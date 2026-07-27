# Рабочее место диспетчера — Dispatcher Workspace

> Frontend Этап 2. Главный экран AI Dispatcher МЧС. Построен поверх Application
> Shell (Этап 1): переиспользует существующие `apiClient`, `env`, Enterprise UI
> Kit, layout и Zustand-stores. Архитектура Этапа 1 не изменялась.

Фича изолирована в `src/features/dispatcher-workspace/` и следует
Feature-Sliced Design:

```
dispatcher-workspace/
├── api/            # REST-сервисы (IncidentService, ResourceService, MapService,
│                   #   StatisticsService, LogService) + endpoints
├── components/     # UI-компоненты рабочего места
├── hooks/          # TanStack Query + WebSocket + virtual list
├── services/       # DispatcherSocketService + чистые построители фич карты
├── store/          # DispatcherStore (Zustand)
├── types/          # Доменные типы (зеркало backend-схем)
├── utils/          # Форматирование, гео, фильтрация, стили карты
├── pages/          # DispatcherWorkspacePage (маршрут /dashboard)
└── index.ts        # Публичный API фичи
```

---

## 1. Компоновка (пять зон)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ЗОНА 1 · Верхняя панель: KPI (активные / свободно / занято / ETA) + статус │
│          канала реального времени                                          │
├───────────────┬──────────────────────────────────┬────────────────────────┤
│ ЗОНА 2        │ ЗОНА 3                            │ ЗОНА 4                 │
│ IncidentList  │ OperationalMap (OpenLayers)       │ IncidentDetails        │
│ · поиск       │ · кластеры маркеров               │ · полная карточка      │
│ · фильтры     │ · слои (вкл/выкл)                 │ · статус + переходы    │
│ · сортировка  │ · выбор + popup                   │ · назначенные силы+ETA │
│ · virtual     │ · zoom / fly-to                   │ · история              │
│   scroll      │                                   │                        │
├───────────────┴──────────────────────────────────┴────────────────────────┤
│ ЗОНА 5 · OperationalLog: таблица событий, автообновление, поиск, фильтр    │
└──────────────────────────────────────────────────────────────────────────┘
```

Реализовано в `components/DispatcherWorkspace.tsx`; на экранах уже `lg`
показываются все три колонки, ниже — карта на всю ширину (список и карточка
доступны через выбор на карте).

---

## 2. Потоки данных

Единый принцип: **серверное состояние живёт в TanStack Query, клиентское
(выбор, фильтры, настройки карты) — в DispatcherStore.** Моков нет — все данные
приходят из backend REST API через общий `apiClient` (Этап 1: авторизация,
refresh токена, retry и нормализация ошибок — в перехватчиках).

| Зона / данные          | Hook                     | Сервис / эндпоинт                         |
| ---------------------- | ------------------------ | ----------------------------------------- |
| KPI шапки              | `useWorkspaceStats`      | `StatisticsService` → `/incidents/active` + `/resources/status` |
| Список происшествий    | `useActiveIncidents` / `useFilteredIncidents` | `IncidentService.listActive` → `GET /incidents/active` |
| Карточка происшествия  | `useIncidentDetails`     | `IncidentService.get` → `GET /incidents/{id}` |
| Маркеры карты          | `useMapData`             | детали инцидентов + `MapService.resourcesInBBox` → `GET /spatial/within-bbox` |
| ETA подразделений      | `useIncidentEtas`        | `ResourceService.unitLocation` + `MapService.estimateEta` → `POST /routing/eta` |
| Журнал                 | `useOperationalLog`      | `LogService.recent` → `GET /resources/history` |
| Смена статуса          | `useChangeIncidentStatus`| `PATCH /incidents/{id}/status` (optimistic) |
| Назначение сил         | `useAssignUnits`         | `POST /incidents/{id}/units`              |

Все эндпоинты собраны в `api/endpoints.ts`; базовый URL берётся из `env`
(`VITE_API_BASE_URL`) — в коде нет захардкоженных URL.

### TanStack Query

- **Кэширование / polling** — у каждого запроса `refetchInterval` и `staleTime`
  из `env` (`VITE_POLL_*`). Polling служит резервом, когда WebSocket недоступен.
- **Invalidate** — сокет-слой и мутации точечно инвалидируют ключи из
  `hooks/queryKeys.ts` (единый источник ключей).
- **Optimistic updates** — смена статуса мгновенно патчит кэш карточки и
  откатывается при ошибке (`onMutate` / `onError`).
- **Retry** — идемпотентные GET повторяются на сетевых/5xx ошибках (перехватчик
  `apiClient`); QueryClient добавляет собственный retry.
- **Параллелизм без N+1** — маркеры инцидентов на карте грузятся через
  `useQueries`, каждый инцидент кэшируется отдельно и не перезапрашивается.

### DispatcherStore (Zustand)

Хранит: `selectedIncidentId`, `selectedUnitId`, `filters` (поиск/статусы/
приоритеты/категории/сортировка), `map` (центр, зум, видимость слоёв),
`flyToIncidentId`. Настройки карты и фильтры персистятся (`aid.dispatcher`);
выбор — волатильный.

---

## 3. WebSocket

`services/socket.service.ts` — `DispatcherSocketService` (транспорт), синглтон
`dispatcherSocket`. Связывается с TanStack Query в `hooks/useDispatcherSocket.ts`.

Возможности:

- ленивое подключение с токеном в query-строке (`resolveSocketUrl` берёт URL из
  `env.wsUrl`, иначе выводит `ws[s]://<origin><VITE_WS_DISPATCHER_PATH>`);
- **авто-переподключение** с экспоненциальной задержкой + jitter (до 30 с);
- **heartbeat** ping/pong с таймаутом живости — «мёртвое» соединение
  принудительно пересоздаётся;
- типизированный эмиттер событий (`on`) и наблюдатель статуса (`onStatus`);
- **graceful degradation** — если сокет не поднялся, интерфейс продолжает
  обновляться через polling запросов; статус показывает `ConnectionStatus`.

Обрабатываемые события → реакция:

| Событие                    | Реакция                                                      |
| -------------------------- | ----------------------------------------------------------- |
| `incident.created`         | invalidate активных инцидентов + KPI                        |
| `incident.updated`         | invalidate карточки + списка + KPI                          |
| `incident.status_changed`  | invalidate карточки + списка + KPI                          |
| `incident.deleted`         | удалить карточку из кэша + invalidate списка/KPI            |
| `unit.updated`             | invalidate юнитов, статусов, объектов карты, KPI            |
| `route.updated`            | invalidate карточки инцидента                               |
| `log.appended`             | prepend события в кэш журнала                                |

> Backend-канал реального времени — точка будущей интеграции. Клиент готов к
> промышленной эксплуатации и не зависит от того, поднят ли сокет: при его
> отсутствии рабочее место живёт на polling.

---

## 4. Карта (OpenLayers)

`components/OperationalMap.tsx` + `utils/map-style.ts`.

- Базовый слой OSM; векторные слои для точек (кластеризация `ol/source/Cluster`)
  и маршрутов.
- **Layer Manager** (`MapLayerManager`) — вкл/выкл слоёв: происшествия,
  подразделения, маршруты, зоны ответственности, гидранты, водоисточники,
  закрытые дороги (видимость в сторе).
- **Marker Cluster** — близкие маркеры сворачиваются в бейдж с числом; клик по
  кластеру приближает.
- **Selection + Popup** — клик по объекту открывает `MapPopup` (overlay) и
  синхронизирует выбор со стором.
- **Zoom / Fly-to** — `requestFlyTo(incidentId)` из списка/карточки анимирует
  карту к происшествию.
- **HeatMap (архитектура)** — стиль/слой инкапсулированы; тепловой слой
  добавляется как ещё один `VectorLayer`/`Heatmap` без изменения контракта фич.
- Стили читают палитру из CSS-переменных, поэтому карта соответствует активной
  теме (тёмная/светлая).

Координаты — WGS-84; перевод в проекцию карты через `fromLonLat`.

---

## 5. Производительность

- `React.memo` на всех презентационных компонентах; `useMemo`/`useCallback`
  для вычислений и обработчиков.
- **Virtual scroll** — `hooks/useVirtualList.ts` (без внешних зависимостей)
  рендерит только видимые карточки списка.
- **Code splitting / lazy loading** — `/dashboard` грузится через `React.lazy` +
  `Suspense`; OpenLayers попадает в отдельный чанк.
- Точечная инвалидизация кэша вместо глобальных перерисовок.

---

## 6. Доступность (a11y)

- Список — `role="listbox"`/`option`, выбор с клавиатуры (Enter/Space), видимый
  фокус (`focus-visible:ring`).
- Карта — `tabindex`/`aria-label` на области; контролы с `aria-label`,
  `aria-pressed`, `role="group"`.
- Статус канала — `role="status"`, `aria-live="polite"`.

---

## 7. Обработка ошибок

- Ошибки API нормализуются перехватчиком `apiClient` (русские сообщения) и
  показываются в каждой зоне (список/карточка/журнал) с кнопкой повтора.
- Потеря WebSocket → авто-переподключение + индикатор; данные не теряются
  благодаря polling.
- Мутации показывают toast и откатывают optimistic-изменения при ошибке.
- Единичные сбои обогащения (ETA, маршрут) не ломают экран (best-effort → `—`).

---

## 8. Тестирование

`src/features/dispatcher-workspace/__tests__/` (Vitest + React Testing Library):

- `filter.test.ts` — фильтрация и сортировка списка;
- `format.test.ts` — форматирование/лейблы/варианты бейджей;
- `map-features.test.ts` — построители фич карты;
- `socket.test.ts` — URL, статусы, доставка событий, переподключение;
- `store.test.ts` — выбор, слои, фильтры, fly-to;
- `IncidentList.test.tsx` — рендер, получение данных, фильтрация, выбор.

E2E (`web/e2e/dispatcher-workspace.spec.ts`, Playwright) — защита маршрута
`/dashboard` и точка входа (login).

Запуск: `npm test` (unit), `npm run e2e` (Playwright), `npm run build`
(typecheck + сборка).

---

## 9. Конфигурация окружения

Добавлено в `.env.example` (Этап 2):

```
VITE_WS_URL=                 # пусто → вывести из origin
VITE_WS_DISPATCHER_PATH=/ws/dispatcher
VITE_POLL_INCIDENTS=15000
VITE_POLL_RESOURCES=20000
VITE_POLL_STATS=15000
VITE_POLL_LOG=12000
```

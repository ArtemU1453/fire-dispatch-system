# Регистрация происшествия — Incident Registration Workflow

> Frontend Этап 3. Основной бизнес-сценарий системы: от нажатия «Новое
> происшествие» до передачи Incident в Dispatch Engine и авто-обновления
> рабочего места диспетчера. Построен поверх Этапов 1–2 — переиспользует
> существующие `apiClient`, `env`, Enterprise UI Kit, layout, Zustand-подход и
> ключи кэша dispatcher-workspace. Архитектура предыдущих этапов не менялась.

Изолировано в `src/features/incident-registration/` (Feature-Sliced Design):

```
incident-registration/
├── api/           # address / catalog / nearest / dispatch / registration + endpoints
├── components/    # IncidentForm, AddressSearch, RegistrationMap, DispatchPreview,
│                  #   ResourceSelection, ConfirmDispatchModal, IncidentRegistration
├── hooks/         # data (TanStack Query) + actions + hotkeys + debounce
├── pages/         # IncidentRegistrationPage (маршрут /incidents/new)
├── store/         # IncidentRegistrationStore (Zustand)
├── types/         # доменные типы (enum-типы reused из Этапа 2)
├── utils/         # labels, converters, geo helpers
└── validation/    # Zod-схема карточки
```

---

## 1. Последовательность действий (7 шагов)

```mermaid
flowchart TD
  A[F2 / «Новое происшествие»] --> B[Шаг 1: карточка (RHF + Zod)]
  B --> C[Шаг 2: поиск адреса — автодополнение]
  C -->|выбор| D[reverse-геокод: район / МО]
  D --> E[Шаг 3: GIS — маркер, ближайшие силы, маршруты]
  D --> F[Шаг 4: Dispatch Engine preview — рекомендация AI]
  F --> G[Шаг 5: изменение состава сил]
  G -->|исключение| F
  G --> H[Шаг 6: модальное подтверждение — силы, ETA, предупреждения]
  H --> I[Шаг 7: POST /incidents + POST /incidents/id/units]
  I --> J[Авто-обновление Dashboard / List / Map / Log]
```

1. **Карточка** — `IncidentForm` (React Hook Form + Zod): тип, категория,
   приоритет, источник, ФИО и телефон заявителя, описание. Номер присваивает
   backend, дата/время — из системных часов.
2. **Поиск адреса** — `AddressSearch`: debounce-запросы к `GET /geocode`,
   автодополнение, навигация ↑/↓, выбор Enter/мышью.
3. **GIS** — после выбора адрес reverse-геокодится (`GET /reverse` → район,
   поселение, регион); карта центрируется, ставит маркер, показывает ближайшие
   подразделения (`GET /resources/nearest`) и маршруты к выбранным силам.
4. **Dispatch Preview** — `POST /dispatch/preview` (Dispatch Engine): список
   рекомендованных сил, расстояние, обоснование, уровень уверенности AI.
5. **Изменение состава** — `ResourceSelection`: исключить/добавить подразделение
   (из резерва или ближайших), изменить порядок высылки, увидеть причину
   рекомендации. Исключение помечает ресурс в `excludedResourceIds` и
   перезапускает preview.
6. **Подтверждение** — `ConfirmDispatchModal`: список сил, ETA (по маршрутам),
   предупреждения (недостаточно сил / непокрытые возможности) и особые условия
   (приоритет).
7. **Передача** — `POST /incidents` (создание) → `POST /incidents/{id}/units`
   (назначение). После успеха инвалидируются ключи dispatcher-workspace, и
   рабочее место обновляется автоматически.

---

## 2. Взаимодействие с Backend

Все клиентские методы вызывают реальные эндпоинты; **бизнес-логика backend не
дублируется**. Базовый URL — из `env`; пути централизованы в `api/endpoints.ts`.

| Шаг                       | Метод сервиса                         | Реальный эндпоинт                         |
| ------------------------- | ------------------------------------- | ----------------------------------------- |
| Каталог типов             | `CatalogService.incidentTypes`        | `GET /admin/directories/incident_types`   |
| Поиск адреса              | `AddressService.search`               | `GET /geocode?q=`                         |
| Район / МО                | `AddressService.resolveArea`          | `GET /reverse?lat=&lon=`                  |
| Ближайшие силы            | `NearestService.near`                 | `GET /resources/nearest?lat=&lon=`        |
| Рекомендация AI           | `DispatchService.preview`             | `POST /dispatch/preview`                  |
| Создание происшествия     | `RegistrationService.createIncident`  | `POST /incidents`                         |
| Назначение сил (передача) | `RegistrationService.assignUnits`     | `POST /incidents/{id}/units`              |
| ETA (в модалке)           | `MapService.estimateEta` (Этап 2)     | `POST /routing/eta`                       |

Каждый вызов проходит через общий `apiClient` (Этап 1): JWT, авто-refresh,
retry идемпотентных GET, нормализация ошибок (русские сообщения).

---

## 3. Структура Store (`IncidentRegistrationStore`)

Клиентское состояние процесса (серверные выборки — в TanStack Query):

| Поле                   | Назначение                                             |
| ---------------------- | ------------------------------------------------------ |
| `status`               | стадия: draft → locating → located → recommended → …   |
| `form`                 | значения карточки (зеркалятся из RHF)                  |
| `location`             | разрешённый адрес + координаты + район                 |
| `recommendation`       | ответ Dispatch Engine                                  |
| `selectedUnits`        | выбранные силы в порядке высылки                       |
| `excludedResourceIds`  | исключённые ресурсы (влияют на повторный preview)      |
| `createdIncidentId/Number` | результат создания                                 |

Действия: `setForm`, `setLocation`, `applyRecommendation` (преселект
первоочередных сил), `addUnit` / `removeUnit` / `moveUnit`, `setCreated`,
`reset`.

---

## 4. TanStack Query

- **Кэширование** — типы, поиск адреса, nearest, preview (ключи в `hooks/keys.ts`).
- **Debounce** — `useDebouncedValue` (300 мс) перед запросом адреса.
- **Повторный preview** — ключ включает `excludedResourceIds`; при исключении
  силы запрос перезапускается и Dispatch Engine предлагает замену.
- **Оптимистичность** — карточка передаётся мгновенно; кэш dispatcher-workspace
  инвалидируется в `onSuccess`, поэтому Dashboard/List/Map/Log обновляются сами.
- **Retry** — на уровне QueryClient и перехватчиков `apiClient`.

---

## 5. UX и горячие клавиши

- **F2** — новый вызов (глобально, из `EnterpriseLayout`).
- **Ctrl/Cmd+Enter** — подтвердить (открыть модалку / подтвердить в модалке).
- **Esc** — отмена / закрыть.
- **Tab** — последовательный переход по полям (нативный порядок).
- Минимум кликов: адрес → авто-район → авто-рекомендация → подтверждение.

---

## 6. Обработка ошибок

| Ситуация                     | Поведение                                            |
| ---------------------------- | ---------------------------------------------------- |
| Backend недоступен           | нормализованное сообщение + кнопка «Повторить»       |
| Адрес не найден              | «Адрес не найден. Уточните запрос.»                  |
| Нет свободных сил            | статус `no_resources`, бейдж «Сил недостаточно»      |
| Ошибка Dispatch Engine       | панель с повтором; reverse/ETA — best-effort, не ломают экран |
| Потеря соединения            | toast об ошибке, откат статуса, повтор доступен      |

---

## 7. Производительность

`React.memo` на компонентах, `useMemo`/`useCallback`, debounce поиска,
**lazy-loading + code-splitting** страницы (`/incidents/new` грузится через
`React.lazy`; OpenLayers — общий async-чанк), оптимистичная передача.

---

## 8. Структура компонентов

```
IncidentRegistration (композиция, hotkeys, action bar)
├── AddressSearch        — Шаг 2
├── IncidentForm         — Шаг 1
├── RegistrationMap      — Шаг 3 (OpenLayers)
├── DispatchPreview      — Шаг 4
├── ResourceSelection    — Шаг 5
└── ConfirmDispatchModal — Шаг 6
```

---

## 9. Тестирование

`src/features/incident-registration/__tests__/` (Vitest + RTL):

- `validation.test.ts` — Zod-схема карточки;
- `store.test.ts` — преселект, add/remove/move, excluded;
- `utils.test.ts` — координаты, дистанции, конвертеры;
- `services.test.ts` — маппинг ответов всех сервисов;
- `AddressSearch.test.tsx` — debounce-подсказки + разрешение адреса;
- `hotkeys.test.tsx` — F2 / Ctrl+Enter / Esc;
- `workflow.integration.test.tsx` — сквозной сценарий (адрес → рекомендация →
  подтверждение → передача в Dispatch Engine), API замокан на границе `request`.

E2E (`web/e2e/incident-registration.spec.ts`, Playwright) — защита маршрута.

**Покрытие модуля:** ≈92% строк / 83% ветвей / 81% функций (порог ДЗ — 80%).
Запуск: `npm run test:coverage`. OpenLayers-карта исключена из покрытия
(не рендерится в jsdom, проверяется вручную).

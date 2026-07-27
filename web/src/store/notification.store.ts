import { create } from "zustand";
import type { AppNotification, NotificationLevel } from "@/types/common";

interface NotificationState {
  items: AppNotification[];
  panelOpen: boolean;
  add: (n: { level: NotificationLevel; title: string; message: string }) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  remove: (id: string) => void;
  clear: () => void;
  setPanelOpen: (open: boolean) => void;
  togglePanel: () => void;
}

const seed: AppNotification[] = [
  { id: "n1", level: "critical", title: "Новое происшествие",
    message: "Пожар — ул. Ленина, 42", createdAt: new Date().toISOString(), read: false },
  { id: "n2", level: "warning", title: "Дорожное ограничение",
    message: "Закрытие движения на ул. Советской", createdAt: new Date().toISOString(), read: false },
  { id: "n3", level: "info", title: "Смена принята",
    message: "Дежурная смена №2 заступила на дежурство", createdAt: new Date().toISOString(), read: true },
];

export const useNotificationStore = create<NotificationState>((set) => ({
  items: seed,
  panelOpen: false,
  add: (n) =>
    set((s) => ({
      items: [
        { ...n, id: crypto.randomUUID(), createdAt: new Date().toISOString(), read: false },
        ...s.items,
      ],
    })),
  markRead: (id) =>
    set((s) => ({ items: s.items.map((i) => (i.id === id ? { ...i, read: true } : i)) })),
  markAllRead: () => set((s) => ({ items: s.items.map((i) => ({ ...i, read: true })) })),
  remove: (id) => set((s) => ({ items: s.items.filter((i) => i.id !== id) })),
  clear: () => set({ items: [] }),
  setPanelOpen: (open) => set({ panelOpen: open }),
  togglePanel: () => set((s) => ({ panelOpen: !s.panelOpen })),
}));

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class names, resolving conflicts (shadcn convention). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Format a Date as HH:MM:SS (ru). */
export function formatTime(d: Date): string {
  return d.toLocaleTimeString("ru-RU", { hour12: false });
}

/** Format a Date as a long ru date. */
export function formatDate(d: Date): string {
  return d.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

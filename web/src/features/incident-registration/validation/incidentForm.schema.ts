/**
 * Zod schema for the "new incident" card (Step 1). Mirrors the fields the
 * backend `IncidentCreate` accepts; the incident number is assigned by the
 * backend, so it is not part of this form.
 */
import { z } from "zod";

export const INCIDENT_SOURCES = [
  "phone",
  "radio",
  "system",
  "patrol",
  "manual",
  "other",
] as const;

export const INCIDENT_CATEGORIES = [
  "fire",
  "road_accident",
  "rescue",
  "chemical",
  "wildfire",
  "false_alarm",
  "special_ops",
  "service_ops",
  "other",
] as const;

export const INCIDENT_PRIORITIES = ["low", "normal", "high", "critical"] as const;

/** Loose international phone shape (digits, spaces, +, -, parentheses). */
const phoneRegex = /^[+()\d][\d\s()-]{4,20}$/;

export const incidentFormSchema = z.object({
  incidentTypeId: z
    .string({ required_error: "Выберите тип происшествия" })
    .uuid("Выберите тип происшествия"),
  source: z.enum(INCIDENT_SOURCES, {
    required_error: "Укажите источник сообщения",
  }),
  category: z.enum(INCIDENT_CATEGORIES, {
    required_error: "Укажите категорию",
  }),
  priority: z.enum(INCIDENT_PRIORITIES, {
    required_error: "Укажите приоритет",
  }),
  reporterName: z
    .string()
    .max(200, "Не более 200 символов")
    .optional()
    .or(z.literal("")),
  reporterContact: z
    .string()
    .regex(phoneRegex, "Некорректный телефон")
    .optional()
    .or(z.literal("")),
  description: z
    .string()
    .max(2000, "Не более 2000 символов")
    .optional()
    .or(z.literal("")),
});

export type IncidentFormValues = z.infer<typeof incidentFormSchema>;

export const defaultIncidentFormValues: IncidentFormValues = {
  incidentTypeId: "",
  source: "phone",
  category: "fire",
  priority: "normal",
  reporterName: "",
  reporterContact: "",
  description: "",
};

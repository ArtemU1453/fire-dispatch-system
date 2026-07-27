import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(1, "Введите логин"),
  password: z.string().min(6, "Пароль не короче 6 символов"),
  remember: z.boolean().optional(),
});

export type LoginValues = z.infer<typeof loginSchema>;

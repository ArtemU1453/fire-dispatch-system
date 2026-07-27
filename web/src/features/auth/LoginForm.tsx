import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate, useLocation } from "react-router-dom";
import { AlertCircle, Lock, LogIn, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useAuth } from "@/hooks/useAuth";
import { paths } from "@/routes/paths";
import { loginSchema, type LoginValues } from "./loginSchema";
import type { ApiErrorShape } from "@/types/api";

export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register, handleSubmit, setValue, watch,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "", remember: true },
  });

  async function onSubmit(values: LoginValues) {
    setServerError(null);
    try {
      await login(values);
      const from = (location.state as { from?: string } | null)?.from ?? paths.dashboard;
      navigate(from, { replace: true });
    } catch (err) {
      const e = err as ApiErrorShape;
      setServerError(
        e.status === 401 ? "Неверный логин или пароль" : e.message ?? "Ошибка входа",
      );
    }
  }

  const remember = watch("remember");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
      {serverError && (
        <div className="flex items-center gap-2 rounded-md border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-[hsl(var(--danger))]">
          <AlertCircle className="h-4 w-4 shrink-0" /> {serverError}
        </div>
      )}
      <div className="flex flex-col gap-2">
        <Label htmlFor="username">Логин</Label>
        <div className="relative">
          <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input id="username" className="pl-10" placeholder="Введите логин" autoComplete="username" {...register("username")} />
        </div>
        {errors.username && <p className="text-xs text-[hsl(var(--danger))]">{errors.username.message}</p>}
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="password">Пароль</Label>
        <div className="relative">
          <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input id="password" type="password" className="pl-10" placeholder="Введите пароль" autoComplete="current-password" {...register("password")} />
        </div>
        {errors.password && <p className="text-xs text-[hsl(var(--danger))]">{errors.password.message}</p>}
      </div>
      <div className="flex items-center gap-2.5">
        <Checkbox id="remember" checked={!!remember} onCheckedChange={(v) => setValue("remember", v === true)} />
        <Label htmlFor="remember" className="cursor-pointer normal-case tracking-normal text-foreground">
          Запомнить меня
        </Label>
      </div>
      <Button type="submit" size="lg" disabled={isSubmitting} className="mt-1">
        <LogIn className="h-5 w-5" /> {isSubmitting ? "Вход..." : "Войти"}
      </Button>
    </form>
  );
}

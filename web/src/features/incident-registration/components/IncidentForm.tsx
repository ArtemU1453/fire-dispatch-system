/**
 * Step 1 — new incident card. React Hook Form + Zod; values are mirrored into
 * the registration store so later steps (preview, create) read a single source.
 */
import { memo, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader } from "@/components/ui/loader";
import { formatDate, formatTime } from "@/lib/utils";
import { useClock } from "@/hooks/useClock";
import { useIncidentTypes } from "../hooks";
import { useRegistrationStore } from "../store/registration.store";
import {
  incidentFormSchema,
  INCIDENT_CATEGORIES,
  INCIDENT_PRIORITIES,
  INCIDENT_SOURCES,
  type IncidentFormValues,
} from "../validation/incidentForm.schema";
import { CATEGORY_LABELS, PRIORITY_LABELS, SOURCE_LABELS } from "../utils/labels";

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-danger">{message}</p>;
}

function IncidentFormBase() {
  const now = useClock();
  const storeForm = useRegistrationStore((s) => s.form);
  const setForm = useRegistrationStore((s) => s.setForm);
  const { data: types, isLoading: typesLoading, isError: typesError } =
    useIncidentTypes();

  const {
    register,
    watch,
    setValue,
    formState: { errors },
  } = useForm<IncidentFormValues>({
    resolver: zodResolver(incidentFormSchema),
    mode: "onChange",
    defaultValues: storeForm,
  });

  // Mirror form changes into the store (single source of truth for later steps).
  useEffect(() => {
    const sub = watch((values) => setForm(values as IncidentFormValues));
    return () => sub.unsubscribe();
  }, [watch, setForm]);

  return (
    <form className="flex flex-col gap-3" aria-label="Карточка нового происшествия">
      {/* Auto meta */}
      <div className="grid grid-cols-3 gap-2 rounded-md border border-border bg-panel px-3 py-2 text-xs">
        <div>
          <span className="block text-muted-foreground">Номер</span>
          <span className="font-medium">присваивается автоматически</span>
        </div>
        <div>
          <span className="block text-muted-foreground">Дата</span>
          <span className="font-medium">{formatDate(now)}</span>
        </div>
        <div>
          <span className="block text-muted-foreground">Время</span>
          <span className="font-medium tabular-nums">{formatTime(now)}</span>
        </div>
      </div>

      {/* Incident type (catalog) */}
      <div>
        <Label htmlFor="incidentType">Тип происшествия *</Label>
        {typesLoading ? (
          <div className="py-2">
            <Loader label="Загрузка типов…" />
          </div>
        ) : typesError ? (
          <p className="text-xs text-danger">Не удалось загрузить типы происшествий.</p>
        ) : (
          <Select
            value={watch("incidentTypeId") || undefined}
            onValueChange={(v) =>
              setValue("incidentTypeId", v, { shouldValidate: true })
            }
          >
            <SelectTrigger id="incidentType" aria-label="Тип происшествия">
              <SelectValue placeholder="Выберите тип…" />
            </SelectTrigger>
            <SelectContent>
              {(types ?? []).map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        <FieldError message={errors.incidentTypeId?.message} />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label htmlFor="category">Категория *</Label>
          <Select
            value={watch("category")}
            onValueChange={(v) =>
              setValue("category", v as IncidentFormValues["category"], {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger id="category" aria-label="Категория">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INCIDENT_CATEGORIES.map((c) => (
                <SelectItem key={c} value={c}>
                  {CATEGORY_LABELS[c]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FieldError message={errors.category?.message} />
        </div>

        <div>
          <Label htmlFor="priority">Приоритет *</Label>
          <Select
            value={watch("priority")}
            onValueChange={(v) =>
              setValue("priority", v as IncidentFormValues["priority"], {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger id="priority" aria-label="Приоритет">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INCIDENT_PRIORITIES.map((p) => (
                <SelectItem key={p} value={p}>
                  {PRIORITY_LABELS[p]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FieldError message={errors.priority?.message} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label htmlFor="source">Источник сообщения *</Label>
          <Select
            value={watch("source")}
            onValueChange={(v) =>
              setValue("source", v as IncidentFormValues["source"], {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger id="source" aria-label="Источник сообщения">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INCIDENT_SOURCES.map((s) => (
                <SelectItem key={s} value={s}>
                  {SOURCE_LABELS[s]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FieldError message={errors.source?.message} />
        </div>

        <div>
          <Label htmlFor="reporterContact">Телефон заявителя</Label>
          <Input
            id="reporterContact"
            inputMode="tel"
            placeholder="+7 900 000-00-00"
            {...register("reporterContact")}
          />
          <FieldError message={errors.reporterContact?.message} />
        </div>
      </div>

      <div>
        <Label htmlFor="reporterName">ФИО заявителя</Label>
        <Input id="reporterName" placeholder="Иванов Иван Иванович" {...register("reporterName")} />
        <FieldError message={errors.reporterName?.message} />
      </div>

      <div>
        <Label htmlFor="description">Описание</Label>
        <textarea
          id="description"
          rows={3}
          placeholder="Что произошло, детали обстановки…"
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          {...register("description")}
        />
        <FieldError message={errors.description?.message} />
      </div>
    </form>
  );
}

export const IncidentForm = memo(IncidentFormBase);

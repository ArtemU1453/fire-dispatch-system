/**
 * Right panel — Assigned Resources. A table of the incident's units with live
 * dispatch status, ETA, timings, vehicle/crew, speed, and per-unit actions
 * (cancel dispatch, reassign, replace, change status, view card, add reserve).
 * ETA is enriched via the existing routing hook.
 */
import { memo } from "react";
import { XCircle, RefreshCw, Repeat, IdCard, Plus } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useIncidentEtas } from "@/features/dispatcher-workspace/hooks";
import { useAssignedResources, useIncident, useManagementActions, useStatusCatalog } from "../hooks";
import { useManagementStore } from "../store/management.store";
import { dispatchStatusLabel, dispatchStatusVariant, formatEta } from "../utils";
import type { AssignedResource } from "../types";

interface Props {
  incidentId: string;
  onReplace: (resource: AssignedResource) => void;
  onViewCard: (resource: AssignedResource) => void;
  onAddReserve: () => void;
}

function ResourcesPanelBase({ incidentId, onReplace, onViewCard, onAddReserve }: Props) {
  const { resources, isLoading, isError } = useAssignedResources(incidentId);
  const { data: incident } = useIncident(incidentId);
  const { etas } = useIncidentEtas(incident);
  const { data: statuses = [] } = useStatusCatalog();
  const { release, assign, changeUnitStatus } = useManagementActions(incidentId);
  const selectResource = useManagementStore((s) => s.selectResource);
  const selectedResourceId = useManagementStore((s) => s.selectedResourceId);

  return (
    <Panel
      title={`Силы и средства · ${resources.length}`}
      className="h-full"
      bodyClassName="flex min-h-0 flex-col p-0"
      actions={
        <Button size="sm" variant="outline" onClick={onAddReserve}>
          <Plus className="mr-1 h-3.5 w-3.5" aria-hidden /> Резерв
        </Button>
      }
    >
      <div className="min-h-0 flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader label="Загрузка сил…" />
          </div>
        ) : isError ? (
          <p className="p-3 text-sm text-danger">Не удалось загрузить силы.</p>
        ) : resources.length === 0 ? (
          <p className="p-3 text-sm text-muted-foreground">
            Подразделения не назначены.
          </p>
        ) : (
          <Table>
            <TableHeader className="sticky top-0 z-10 bg-panel">
              <TableRow>
                <TableHead>Подразделение</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead className="text-right">ETA</TableHead>
                <TableHead>Техника</TableHead>
                <TableHead className="text-center">Экипаж</TableHead>
                <TableHead className="text-right">Скорость</TableHead>
                <TableHead>Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {resources.map((r) => {
                const selected = r.resourceId === selectedResourceId;
                return (
                  <TableRow
                    key={r.resourceId}
                    className={selected ? "bg-muted" : "cursor-pointer"}
                    onClick={() => selectResource(r.resourceId)}
                  >
                    <TableCell className="text-xs">
                      <div className="font-medium">{r.code}</div>
                      <div className="text-[11px] text-muted-foreground">{r.name}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={dispatchStatusVariant(r.dispatchStatus)}>
                        {dispatchStatusLabel(r.dispatchStatus)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right text-xs tabular-nums">
                      {formatEta(etas[r.resourceId] ?? r.etaSeconds)}
                    </TableCell>
                    <TableCell className="text-xs">{r.vehicleType ?? "—"}</TableCell>
                    <TableCell className="text-center text-xs tabular-nums">{r.crewCount}</TableCell>
                    <TableCell className="text-right text-xs tabular-nums text-muted-foreground">
                      {r.speedKmh != null ? `${r.speedKmh} км/ч` : "н/д"}
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center gap-1">
                        {r.unitId && statuses.length > 0 && (
                          <Select
                            value={r.unitStatus?.code}
                            onValueChange={(code) =>
                              changeUnitStatus.mutate({ unitId: r.unitId as string, statusCode: code })
                            }
                          >
                            <SelectTrigger
                              aria-label="Изменить статус"
                              className="h-7 w-[92px] text-[11px]"
                            >
                              <SelectValue placeholder="Статус" />
                            </SelectTrigger>
                            <SelectContent>
                              {statuses.map((s) => (
                                <SelectItem key={s.code} value={s.code}>
                                  {s.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-danger"
                          aria-label="Отменить высылку"
                          disabled={!r.unitId || release.isPending}
                          onClick={() => r.unitId && release.mutate(r.unitId)}
                        >
                          <XCircle className="h-4 w-4" aria-hidden />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          aria-label="Назначить повторно"
                          disabled={assign.isPending}
                          onClick={() => assign.mutate([r.resourceId])}
                        >
                          <RefreshCw className="h-4 w-4" aria-hidden />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          aria-label="Заменить"
                          onClick={() => onReplace(r)}
                        >
                          <Repeat className="h-4 w-4" aria-hidden />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          aria-label="Карточка подразделения"
                          onClick={() => onViewCard(r)}
                        >
                          <IdCard className="h-4 w-4" aria-hidden />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </div>
    </Panel>
  );
}

export const ResourcesPanel = memo(ResourcesPanelBase);

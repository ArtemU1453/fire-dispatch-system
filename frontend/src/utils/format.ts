/** Presentation helpers (formatting only — no business logic). */

export function formatDistance(meters?: number | null): string {
  if (meters == null) return '—';
  if (meters < 1000) return `${Math.round(meters)} м`;
  return `${(meters / 1000).toFixed(1)} км`;
}

export function formatDuration(seconds?: number | null): string {
  if (seconds == null) return '—';
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  if (minutes < 1) return `${secs} с`;
  if (minutes < 60) return `${minutes} мин${secs ? ` ${secs} с` : ''}`;
  const hours = Math.floor(minutes / 60);
  return `${hours} ч ${minutes % 60} мин`;
}

export function formatCoords(lat?: number | null, lon?: number | null): string {
  if (lat == null || lon == null) return '—';
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
}

export function formatTime(date: Date): string {
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

const CONFIDENCE_LABEL: Record<string, string> = {
  high: 'высокая',
  medium: 'средняя',
  low: 'низкая',
};

export function confidenceLabel(level: string): string {
  return CONFIDENCE_LABEL[level] ?? level;
}

const STATUS_LABEL: Record<string, string> = {
  recommended: 'Состав сформирован',
  partial: 'Состав неполный',
  no_resources: 'Ресурсы не найдены',
};

export function statusLabel(status: string): string {
  return STATUS_LABEL[status] ?? status;
}

const PRIORITY_LABEL: Record<string, string> = {
  low: 'низкий',
  normal: 'обычный',
  high: 'высокий',
  critical: 'критический',
};

export function priorityLabel(priority: string): string {
  return PRIORITY_LABEL[priority] ?? priority;
}

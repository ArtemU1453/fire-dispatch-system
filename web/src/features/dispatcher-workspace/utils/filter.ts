/**
 * Pure filtering & sorting for the incident list. Extracted so it is directly
 * unit-testable and memoizable.
 */
import type { IncidentPriority, IncidentSummary } from "../types";
import type { IncidentFilters, IncidentSortKey } from "../store/dispatcher.store";

const PRIORITY_RANK: Record<IncidentPriority, number> = {
  critical: 0,
  high: 1,
  normal: 2,
  low: 3,
};

function matches(inc: IncidentSummary, f: IncidentFilters): boolean {
  if (f.statuses.length && !f.statuses.includes(inc.status)) return false;
  if (f.priorities.length && !f.priorities.includes(inc.priority)) return false;
  if (f.categories.length && !f.categories.includes(inc.category)) return false;
  if (f.search.trim()) {
    const q = f.search.trim().toLowerCase();
    const haystack = `${inc.number} ${inc.title ?? ""} ${inc.address ?? ""}`.toLowerCase();
    if (!haystack.includes(q)) return false;
  }
  return true;
}

function comparator(sort: IncidentSortKey) {
  return (a: IncidentSummary, b: IncidentSummary): number => {
    switch (sort) {
      case "reported_asc":
        return a.reported_at.localeCompare(b.reported_at);
      case "priority": {
        const d = PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority];
        return d !== 0 ? d : b.reported_at.localeCompare(a.reported_at);
      }
      case "reported_desc":
      default:
        return b.reported_at.localeCompare(a.reported_at);
    }
  };
}

export function filterAndSortIncidents(
  incidents: IncidentSummary[],
  filters: IncidentFilters,
): IncidentSummary[] {
  return incidents.filter((i) => matches(i, filters)).sort(comparator(filters.sort));
}

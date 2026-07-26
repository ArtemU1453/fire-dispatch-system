"""Export data model + format enum (stage §5).

``TableData`` is the single tabular shape every exporter renders. Concrete
formatters (CSV, XLSX now; PDF later) plug into :func:`render` behind the unified
``ExportService`` — a new format needs a writer, nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"


@dataclass(slots=True)
class TableData:
    title: str
    columns: list[str]
    rows: list[list[object]] = field(default_factory=list)


_MEDIA = {
    ExportFormat.CSV: "text/csv",
    ExportFormat.XLSX: (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
}


def media_type(fmt: ExportFormat) -> str:
    return _MEDIA[fmt]


def render(table: TableData, fmt: ExportFormat) -> bytes:
    from app.analytics.export.csv_writer import to_csv
    from app.analytics.export.xlsx_writer import to_xlsx

    if fmt is ExportFormat.CSV:
        return to_csv(table)
    if fmt is ExportFormat.XLSX:
        return to_xlsx(table)
    raise ValueError(f"Unsupported export format: {fmt}")  # pragma: no cover

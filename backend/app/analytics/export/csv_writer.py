"""CSV exporter (stdlib ``csv``)."""

from __future__ import annotations

import csv
import io

from app.analytics.export.formats import TableData


def to_csv(table: TableData) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(table.columns)
    for row in table.rows:
        writer.writerow(["" if v is None else v for v in row])
    # UTF-8 BOM so Excel opens Cyrillic correctly.
    return b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8")

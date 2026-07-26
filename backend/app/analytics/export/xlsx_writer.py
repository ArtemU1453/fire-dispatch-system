"""Minimal XLSX exporter using only the standard library.

Writes a valid single-sheet ``.xlsx`` (an OOXML zip) with inline strings and
numeric cells — no third-party dependency (openpyxl et al.). Sufficient for
tabular analytics exports; a richer writer can replace it behind
``ExportService`` without changing callers.
"""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from app.analytics.export.formats import TableData

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'  # noqa: E501
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'  # noqa: E501
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'  # noqa: E501
    "</Types>"
)

_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'  # noqa: E501
    "</Relationships>"
)

_WORKBOOK = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<sheets><sheet name="Report" sheetId="1" r:id="rId1"/></sheets></workbook>'
)

_WORKBOOK_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'  # noqa: E501
    "</Relationships>"
)


def _col_letter(index: int) -> str:
    """0-based column index → spreadsheet column letters (A, B, …, AA)."""
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _cell(col: int, row: int, value: object) -> str:
    ref = f"{_col_letter(col)}{row}"
    if isinstance(value, bool):
        value = str(value)
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    text = "" if value is None else str(value)
    return (  # noqa: E501
        f'<c r="{ref}" t="inlineStr"><is>'
        f'<t xml:space="preserve">{escape(text)}</t></is></c>'
    )


def _sheet(table: TableData) -> str:
    rows_xml: list[str] = []
    header = "".join(
        _cell(c, 1, col) for c, col in enumerate(table.columns)
    )
    rows_xml.append(f'<row r="1">{header}</row>')
    for r, row in enumerate(table.rows, start=2):
        cells = "".join(_cell(c, r, value) for c, value in enumerate(row))
        rows_xml.append(f'<row r="{r}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(rows_xml)}</sheetData></worksheet>"
    )


def to_xlsx(table: TableData) -> bytes:
    buffer = io.BytesIO()
    ts = datetime(2020, 1, 1, tzinfo=UTC).timetuple()[:6]
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in (
            ("[Content_Types].xml", _CONTENT_TYPES),
            ("_rels/.rels", _ROOT_RELS),
            ("xl/workbook.xml", _WORKBOOK),
            ("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS),
            ("xl/worksheets/sheet1.xml", _sheet(table)),
        ):
            info = zipfile.ZipInfo(name, date_time=ts)
            zf.writestr(info, content)
    return buffer.getvalue()

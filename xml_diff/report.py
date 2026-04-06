"""Report generation for XML diff results.

Two formats are supported:

* **text** – plain-text report suitable for console output or log files.
* **html** – self-contained HTML page with colour-coded difference table.
"""

from __future__ import annotations

import html as _html
from pathlib import Path
from typing import Iterable

from .comparator import Difference, DiffKind


# ---------------------------------------------------------------------------
# Colour / label helpers
# ---------------------------------------------------------------------------

_KIND_LABEL: dict[DiffKind, str] = {
    DiffKind.ELEMENT_ADDED: "ADDED",
    DiffKind.ELEMENT_REMOVED: "REMOVED",
    DiffKind.TEXT_CHANGED: "TEXT CHANGED",
    DiffKind.ATTRIBUTE_ADDED: "ATTR ADDED",
    DiffKind.ATTRIBUTE_REMOVED: "ATTR REMOVED",
    DiffKind.ATTRIBUTE_CHANGED: "ATTR CHANGED",
    DiffKind.TAG_CHANGED: "TAG CHANGED",
}

_KIND_CSS: dict[DiffKind, str] = {
    DiffKind.ELEMENT_ADDED: "added",
    DiffKind.ELEMENT_REMOVED: "removed",
    DiffKind.TEXT_CHANGED: "changed",
    DiffKind.ATTRIBUTE_ADDED: "added",
    DiffKind.ATTRIBUTE_REMOVED: "removed",
    DiffKind.ATTRIBUTE_CHANGED: "changed",
    DiffKind.TAG_CHANGED: "changed",
}


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class DiffReport:
    """Holds a list of :class:`~xml_diff.comparator.Difference` objects and
    can render them as plain text or HTML.

    Parameters
    ----------
    differences:
        The differences produced by :class:`~xml_diff.comparator.XmlComparator`.
    label_a:
        Human-readable name for document A (shown in the report header).
    label_b:
        Human-readable name for document B (shown in the report header).
    """

    def __init__(
        self,
        differences: list[Difference],
        label_a: str = "Document A",
        label_b: str = "Document B",
    ) -> None:
        self.differences = differences
        self.label_a = label_a
        self.label_b = label_b

    # ------------------------------------------------------------------
    # Text report
    # ------------------------------------------------------------------

    def as_text(self) -> str:
        """Return a plain-text diff report."""
        lines: list[str] = []
        sep = "=" * 72

        lines.append(sep)
        lines.append("XML DIFF REPORT")
        lines.append(f"  Document A : {self.label_a}")
        lines.append(f"  Document B : {self.label_b}")
        lines.append(sep)

        if not self.differences:
            lines.append("No differences found – the documents are identical.")
            lines.append(sep)
            return "\n".join(lines)

        lines.append(f"Total differences: {len(self.differences)}")
        lines.append("")

        for i, diff in enumerate(self.differences, start=1):
            label = _KIND_LABEL.get(diff.kind, diff.kind.name)
            lines.append(f"[{i}] {label}")
            lines.append(f"    Location : {diff.xpath}")
            lines.append(f"    Detail   : {diff.detail}")
            if diff.value_a is not None:
                lines.append(f"    Value A  : {diff.value_a}")
            if diff.value_b is not None:
                lines.append(f"    Value B  : {diff.value_b}")
            lines.append("")

        lines.append(sep)
        return "\n".join(lines)

    def write_text(self, path: str | Path) -> None:
        """Write the text report to *path*."""
        Path(path).write_text(self.as_text(), encoding="utf-8")

    # ------------------------------------------------------------------
    # HTML report
    # ------------------------------------------------------------------

    def as_html(self) -> str:
        """Return a self-contained HTML diff report."""
        rows = "".join(
            self._html_row(d, idx) for idx, d in enumerate(self.differences, start=1)
        )
        total = len(self.differences)
        summary = (
            '<p class="no-diff">No differences found – the documents are identical.</p>'
            if total == 0
            else f"<p>Total differences found: <strong>{total}</strong></p>"
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>XML Diff Report</title>
  <style>
    body {{
      font-family: ui-monospace, "Cascadia Code", "Courier New", monospace;
      font-size: 13px;
      margin: 2rem;
      background: #f9f9fb;
      color: #1a1a2e;
    }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
    .meta {{ color: #555; margin-bottom: 1rem; }}
    .no-diff {{ color: green; font-weight: bold; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: #fff;
      box-shadow: 0 1px 4px rgba(0,0,0,.15);
    }}
    th {{
      background: #2d3561;
      color: #fff;
      padding: .45rem .7rem;
      text-align: left;
    }}
    td {{
      padding: .4rem .7rem;
      border-bottom: 1px solid #e2e2ea;
      vertical-align: top;
      word-break: break-all;
    }}
    tr:hover td {{ background: #f0f0ff; }}
    .badge {{
      display: inline-block;
      padding: 1px 7px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: bold;
      white-space: nowrap;
    }}
    .added  {{ background: #d4edda; color: #155724; }}
    .removed {{ background: #f8d7da; color: #721c24; }}
    .changed {{ background: #fff3cd; color: #856404; }}
    .val-a {{ background: #fdecea; padding: 2px 5px; border-radius: 4px; }}
    .val-b {{ background: #e8f5e9; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>XML Diff Report</h1>
  <div class="meta">
    <strong>Document A:</strong> {_html.escape(self.label_a)}<br/>
    <strong>Document B:</strong> {_html.escape(self.label_b)}
  </div>
  {summary}
  {"" if total == 0 else f"""
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Kind</th>
        <th>Location (XPath)</th>
        <th>Detail</th>
        <th>Value A</th>
        <th>Value B</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
  """}
</body>
</html>"""

    def _html_row(self, diff: Difference, idx: int) -> str:
        label = _KIND_LABEL.get(diff.kind, diff.kind.name)
        css = _KIND_CSS.get(diff.kind, "changed")

        if diff.value_a is None:
            cell_a = ""
        else:
            cell_a = '<code class="val-a">' + _html.escape(diff.value_a) + "</code>"

        if diff.value_b is None:
            cell_b = ""
        else:
            cell_b = '<code class="val-b">' + _html.escape(diff.value_b) + "</code>"

        return (
            f"<tr>"
            f"<td>{idx}</td>"
            f'<td><span class="badge {css}">{_html.escape(label)}</span></td>'
            f"<td>{_html.escape(diff.xpath)}</td>"
            f"<td>{_html.escape(diff.detail)}</td>"
            f"<td>{cell_a}</td>"
            f"<td>{cell_b}</td>"
            f"</tr>\n"
        )

    def write_html(self, path: str | Path) -> None:
        """Write the HTML report to *path*."""
        Path(path).write_text(self.as_html(), encoding="utf-8")

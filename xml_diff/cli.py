"""Command-line interface for xml-diff-tool.

Usage
-----
    xml-diff  FILE_A  FILE_B  [--output-text REPORT.txt]  [--output-html REPORT.html]
    python -m xml_diff  FILE_A  FILE_B  ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .comparator import XmlComparator
from .report import DiffReport


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xml-diff",
        description=(
            "Compare two XML documents, ignore comments, "
            "and produce a difference report."
        ),
    )
    parser.add_argument("file_a", metavar="FILE_A", help="First XML file")
    parser.add_argument("file_b", metavar="FILE_B", help="Second XML file")
    parser.add_argument(
        "--output-text",
        metavar="FILE",
        help="Write plain-text report to FILE",
    )
    parser.add_argument(
        "--output-html",
        metavar="FILE",
        help="Write HTML report to FILE",
    )
    parser.add_argument(
        "--no-ignore-whitespace",
        action="store_true",
        default=False,
        help="Do not normalise whitespace-only text nodes",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point; returns an exit code (0 = identical, 1 = differences found)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    comparator = XmlComparator(
        ignore_whitespace_text=not args.no_ignore_whitespace
    )

    try:
        differences = comparator.compare_files(args.file_a, args.file_b)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    label_a = Path(args.file_a).name
    label_b = Path(args.file_b).name
    report = DiffReport(differences, label_a=label_a, label_b=label_b)

    # Always print text report to stdout
    print(report.as_text())

    if args.output_text:
        report.write_text(args.output_text)
        print(f"Text report written to: {args.output_text}", file=sys.stderr)

    if args.output_html:
        report.write_html(args.output_html)
        print(f"HTML report written to: {args.output_html}", file=sys.stderr)

    return 1 if differences else 0


if __name__ == "__main__":
    sys.exit(main())

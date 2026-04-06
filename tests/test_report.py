"""Tests for xml_diff.report."""

import pytest

from xml_diff.comparator import Difference, DiffKind
from xml_diff.report import DiffReport


def make_diff(**kwargs) -> Difference:
    defaults = dict(kind=DiffKind.TEXT_CHANGED, xpath="/root/item", detail="Text changed")
    defaults.update(kwargs)
    return Difference(**defaults)


class TestTextReport:
    def test_no_diff_message(self):
        report = DiffReport([], label_a="A.xml", label_b="B.xml")
        text = report.as_text()
        assert "No differences found" in text
        assert "A.xml" in text
        assert "B.xml" in text

    def test_diff_listed(self):
        diffs = [make_diff(value_a="hello", value_b="world")]
        report = DiffReport(diffs)
        text = report.as_text()
        assert "TEXT CHANGED" in text
        assert "hello" in text
        assert "world" in text

    def test_count_shown(self):
        diffs = [make_diff(), make_diff(kind=DiffKind.ELEMENT_ADDED)]
        report = DiffReport(diffs)
        assert "Total differences: 2" in report.as_text()

    def test_write_text(self, tmp_path):
        report = DiffReport([make_diff()])
        path = tmp_path / "report.txt"
        report.write_text(path)
        assert path.exists()
        assert "TEXT CHANGED" in path.read_text()


class TestHtmlReport:
    def test_html_structure(self):
        diffs = [make_diff(value_a="v1", value_b="v2")]
        html = DiffReport(diffs).as_html()
        assert "<!DOCTYPE html>" in html
        assert "XML Diff Report" in html
        assert "v1" in html
        assert "v2" in html

    def test_html_no_diff(self):
        html = DiffReport([]).as_html()
        assert "No differences found" in html
        # No table should be present when there are no diffs
        assert "<table>" not in html

    def test_html_escaping(self):
        """Values with < > & must be HTML-escaped."""
        diffs = [make_diff(detail='val < > & "quotes"', value_a="<raw>")]
        html = DiffReport(diffs).as_html()
        assert "<raw>" not in html
        assert "&lt;raw&gt;" in html

    def test_write_html(self, tmp_path):
        report = DiffReport([make_diff()])
        path = tmp_path / "report.html"
        report.write_html(path)
        assert path.exists()
        assert "<!DOCTYPE html>" in path.read_text()

    def test_kind_badges(self):
        diffs = [
            make_diff(kind=DiffKind.ELEMENT_ADDED),
            make_diff(kind=DiffKind.ELEMENT_REMOVED),
            make_diff(kind=DiffKind.ATTRIBUTE_CHANGED),
        ]
        html = DiffReport(diffs).as_html()
        assert "ADDED" in html
        assert "REMOVED" in html
        assert "ATTR CHANGED" in html

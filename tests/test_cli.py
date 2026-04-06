"""Tests for the CLI (xml_diff.cli)."""

import sys
from pathlib import Path

import pytest

from xml_diff.cli import main


@pytest.fixture()
def xml_files(tmp_path):
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    a.write_text("<root><item>hello</item></root>", encoding="utf-8")
    b.write_text("<root><item>world</item></root>", encoding="utf-8")
    return str(a), str(b)


@pytest.fixture()
def identical_files(tmp_path):
    xml = "<root><item attr='1'>text</item></root>"
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    a.write_text(xml, encoding="utf-8")
    b.write_text(xml, encoding="utf-8")
    return str(a), str(b)


class TestCliExitCodes:
    def test_differences_returns_1(self, xml_files, capsys):
        code = main(list(xml_files))
        assert code == 1

    def test_identical_returns_0(self, identical_files, capsys):
        code = main(list(identical_files))
        assert code == 0

    def test_invalid_file_returns_2(self, tmp_path):
        code = main([str(tmp_path / "no.xml"), str(tmp_path / "no2.xml")])
        assert code == 2


class TestCliOutput:
    def test_stdout_contains_report(self, xml_files, capsys):
        main(list(xml_files))
        out = capsys.readouterr().out
        assert "XML DIFF REPORT" in out
        assert "TEXT CHANGED" in out

    def test_output_text_flag(self, xml_files, tmp_path, capsys):
        report_path = tmp_path / "report.txt"
        main([*xml_files, "--output-text", str(report_path)])
        assert report_path.exists()
        assert "TEXT CHANGED" in report_path.read_text()

    def test_output_html_flag(self, xml_files, tmp_path, capsys):
        report_path = tmp_path / "report.html"
        main([*xml_files, "--output-html", str(report_path)])
        assert report_path.exists()
        assert "<!DOCTYPE html>" in report_path.read_text()

    def test_comments_ignored_in_cli(self, tmp_path, capsys):
        a = tmp_path / "a.xml"
        b = tmp_path / "b.xml"
        a.write_text("<root><!-- comment --><item>same</item></root>", encoding="utf-8")
        b.write_text("<root><item>same</item></root>", encoding="utf-8")
        code = main([str(a), str(b)])
        assert code == 0

"""Tests for xml_diff.comparator."""

import pytest
from lxml import etree

from xml_diff.comparator import DiffKind, XmlComparator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compare(xml_a: str, xml_b: str, **kwargs) -> list:
    return XmlComparator(**kwargs).compare_strings(xml_a, xml_b)


def kinds(diffs) -> list[DiffKind]:
    return [d.kind for d in diffs]


# ---------------------------------------------------------------------------
# Identical documents
# ---------------------------------------------------------------------------


class TestIdentical:
    def test_identical_simple(self):
        xml = "<root><child attr='1'>text</child></root>"
        assert compare(xml, xml) == []

    def test_identical_with_whitespace(self):
        a = "<root>\n  <child>text</child>\n</root>"
        b = "<root><child>text</child></root>"
        assert compare(a, b) == []

    def test_whitespace_strict(self):
        """With ignore_whitespace_text=False the indentation IS a difference."""
        a = "<root>\n  <child/>\n</root>"
        b = "<root><child/></root>"
        diffs = compare(a, b, ignore_whitespace_text=False)
        assert any(d.kind == DiffKind.TEXT_CHANGED for d in diffs)


# ---------------------------------------------------------------------------
# Comments are ignored
# ---------------------------------------------------------------------------


class TestCommentsIgnored:
    def test_comment_in_a(self):
        a = "<root><!-- this is a comment --><child/></root>"
        b = "<root><child/></root>"
        assert compare(a, b) == []

    def test_comment_in_b(self):
        a = "<root><child/></root>"
        b = "<root><!-- comment --><child/></root>"
        assert compare(a, b) == []

    def test_comments_in_both(self):
        a = "<root><!-- A --><item>1</item></root>"
        b = "<root><!-- B --><item>1</item></root>"
        assert compare(a, b) == []

    def test_only_comment_differs(self):
        a = "<root><!-- comment A --><item/></root>"
        b = "<root><!-- comment B --><item/></root>"
        assert compare(a, b) == []

    def test_comment_with_nested_elements(self):
        a = "<root><!-- <fake>ignored</fake> --><real>data</real></root>"
        b = "<root><real>data</real></root>"
        assert compare(a, b) == []


# ---------------------------------------------------------------------------
# Text differences
# ---------------------------------------------------------------------------


class TestTextDiff:
    def test_text_changed(self):
        a = "<root><item>hello</item></root>"
        b = "<root><item>world</item></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.TEXT_CHANGED
        assert diffs[0].value_a == "hello"
        assert diffs[0].value_b == "world"

    def test_text_added(self):
        a = "<root><item/></root>"
        b = "<root><item>new</item></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.TEXT_CHANGED
        assert diffs[0].value_b == "new"

    def test_text_removed(self):
        a = "<root><item>old</item></root>"
        b = "<root><item/></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.TEXT_CHANGED
        assert diffs[0].value_a == "old"


# ---------------------------------------------------------------------------
# Attribute differences
# ---------------------------------------------------------------------------


class TestAttributeDiff:
    def test_attribute_changed(self):
        a = "<root><item id='1'/></root>"
        b = "<root><item id='2'/></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.ATTRIBUTE_CHANGED
        assert diffs[0].value_a == "1"
        assert diffs[0].value_b == "2"

    def test_attribute_added(self):
        a = "<root><item/></root>"
        b = "<root><item id='1'/></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.ATTRIBUTE_ADDED

    def test_attribute_removed(self):
        a = "<root><item id='1'/></root>"
        b = "<root><item/></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.ATTRIBUTE_REMOVED

    def test_multiple_attribute_changes(self):
        a = "<root><item x='1' y='2' z='3'/></root>"
        b = "<root><item x='1' y='9' w='4'/></root>"
        diffs = compare(a, b)
        diff_kinds = kinds(diffs)
        assert DiffKind.ATTRIBUTE_CHANGED in diff_kinds  # y changed
        assert DiffKind.ATTRIBUTE_REMOVED in diff_kinds  # z removed
        assert DiffKind.ATTRIBUTE_ADDED in diff_kinds    # w added


# ---------------------------------------------------------------------------
# Structural differences
# ---------------------------------------------------------------------------


class TestStructuralDiff:
    def test_element_added(self):
        a = "<root><a/></root>"
        b = "<root><a/><b/></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.ELEMENT_ADDED

    def test_element_removed(self):
        a = "<root><a/><b/></root>"
        b = "<root><a/></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.ELEMENT_REMOVED

    def test_tag_changed(self):
        a = "<root><old/></root>"
        b = "<root><new/></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.TAG_CHANGED

    def test_deeply_nested(self):
        a = "<a><b><c><d>v1</d></c></b></a>"
        b = "<a><b><c><d>v2</d></c></b></a>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.TEXT_CHANGED


# ---------------------------------------------------------------------------
# Combined: comments + real differences
# ---------------------------------------------------------------------------


class TestCombined:
    def test_comment_plus_text_diff(self):
        a = "<root><!-- note --><val>1</val></root>"
        b = "<root><val>2</val></root>"
        diffs = compare(a, b)
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.TEXT_CHANGED

    def test_no_false_positives_from_deep_comments(self):
        a = """
        <catalog>
          <!-- first product -->
          <product id="1">
            <name>Widget</name>
            <!-- price might change -->
            <price>9.99</price>
          </product>
        </catalog>
        """
        b = """
        <catalog>
          <product id="1">
            <name>Widget</name>
            <price>9.99</price>
          </product>
        </catalog>
        """
        assert compare(a, b) == []


# ---------------------------------------------------------------------------
# File-based comparison
# ---------------------------------------------------------------------------


class TestCompareFiles:
    def test_compare_files(self, tmp_path):
        file_a = tmp_path / "a.xml"
        file_b = tmp_path / "b.xml"
        file_a.write_text("<root><item>hello</item></root>", encoding="utf-8")
        file_b.write_text("<root><item>world</item></root>", encoding="utf-8")

        comparator = XmlComparator()
        diffs = comparator.compare_files(str(file_a), str(file_b))
        assert len(diffs) == 1
        assert diffs[0].kind == DiffKind.TEXT_CHANGED

    def test_identical_files(self, tmp_path):
        xml = "<root><child/></root>"
        f = tmp_path / "doc.xml"
        f.write_text(xml, encoding="utf-8")
        assert XmlComparator().compare_files(str(f), str(f)) == []

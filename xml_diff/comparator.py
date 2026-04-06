"""XML document comparator.

Parses two XML documents, strips all comments, and produces a list of
:class:`Difference` objects that describe every structural or textual
divergence between the two trees.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from lxml import etree


# ---------------------------------------------------------------------------
# Public data structures
# ---------------------------------------------------------------------------


class DiffKind(Enum):
    """Categorises a single difference found between the two XML documents."""

    ELEMENT_ADDED = auto()        # element present only in document B
    ELEMENT_REMOVED = auto()      # element present only in document A
    TEXT_CHANGED = auto()         # text/tail content differs
    ATTRIBUTE_ADDED = auto()      # attribute present only in document B
    ATTRIBUTE_REMOVED = auto()    # attribute present only in document A
    ATTRIBUTE_CHANGED = auto()    # attribute value differs
    TAG_CHANGED = auto()          # tag name differs at the same position


@dataclass
class Difference:
    """A single difference between the two XML documents."""

    kind: DiffKind
    xpath: str                          # XPath-style location in document A (or B)
    detail: str                         # human-readable explanation
    value_a: Optional[str] = None       # value / snippet from document A
    value_b: Optional[str] = None       # value / snippet from document B


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_comments(tree: etree._Element) -> None:
    """Remove all comment nodes from *tree* in-place (recursive)."""
    for comment in tree.xpath("//comment()"):
        parent = comment.getparent()
        if parent is not None:
            parent.remove(comment)


def _normalise_text(text: Optional[str]) -> str:
    """Return stripped text, treating ``None`` as an empty string."""
    return (text or "").strip()


def _element_xpath(elem: etree._Element, root: etree._Element) -> str:
    """Return a simple XPath string for *elem* relative to *root*."""
    try:
        return root.getroottree().getpath(elem)
    except Exception:
        return f"<{elem.tag}>"


# ---------------------------------------------------------------------------
# Core comparison
# ---------------------------------------------------------------------------


class XmlComparator:
    """Compare two XML documents and collect all differences.

    Comments are stripped from both documents before comparison so they do
    not affect the result.

    Parameters
    ----------
    ignore_whitespace_text:
        When ``True`` (the default) text nodes that consist of whitespace
        only are treated as empty, which avoids spurious differences caused
        by indentation.
    """

    def __init__(self, ignore_whitespace_text: bool = True) -> None:
        self.ignore_whitespace_text = ignore_whitespace_text

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def compare_files(self, path_a: str, path_b: str) -> list[Difference]:
        """Parse two XML files and return their differences."""
        tree_a = etree.parse(path_a)
        tree_b = etree.parse(path_b)
        return self.compare_trees(tree_a.getroot(), tree_b.getroot())

    def compare_strings(self, xml_a: str, xml_b: str) -> list[Difference]:
        """Parse two XML strings and return their differences."""
        root_a = etree.fromstring(xml_a.encode())
        root_b = etree.fromstring(xml_b.encode())
        return self.compare_trees(root_a, root_b)

    def compare_trees(
        self,
        root_a: etree._Element,
        root_b: etree._Element,
    ) -> list[Difference]:
        """Compare two already-parsed element trees and return differences.

        The supplied trees are **not** modified; copies are made internally
        before comments are stripped.
        """
        import copy

        root_a = copy.deepcopy(root_a)
        root_b = copy.deepcopy(root_b)
        _strip_comments(root_a)
        _strip_comments(root_b)

        differences: list[Difference] = []
        self._compare_elements(root_a, root_b, root_a, root_b, differences)
        return differences

    # ------------------------------------------------------------------
    # Private recursive logic
    # ------------------------------------------------------------------

    def _compare_elements(
        self,
        elem_a: etree._Element,
        elem_b: etree._Element,
        root_a: etree._Element,
        root_b: etree._Element,
        diffs: list[Difference],
    ) -> None:
        xpath_a = _element_xpath(elem_a, root_a)
        xpath_b = _element_xpath(elem_b, root_b)

        # Tag name
        if elem_a.tag != elem_b.tag:
            diffs.append(
                Difference(
                    kind=DiffKind.TAG_CHANGED,
                    xpath=xpath_a,
                    detail=f"Tag changed from <{elem_a.tag}> to <{elem_b.tag}>",
                    value_a=elem_a.tag,
                    value_b=elem_b.tag,
                )
            )
            # Stop recursing; the subtrees are fundamentally different
            return

        # Attributes
        self._compare_attributes(elem_a, elem_b, xpath_a, diffs)

        # Text content
        self._compare_text(elem_a, elem_b, xpath_a, diffs)

        # Children
        self._compare_children(elem_a, elem_b, root_a, root_b, xpath_a, diffs)

    def _compare_attributes(
        self,
        elem_a: etree._Element,
        elem_b: etree._Element,
        xpath: str,
        diffs: list[Difference],
    ) -> None:
        attrs_a = dict(elem_a.attrib)
        attrs_b = dict(elem_b.attrib)

        for name in sorted(set(attrs_a) | set(attrs_b)):
            if name not in attrs_a:
                diffs.append(
                    Difference(
                        kind=DiffKind.ATTRIBUTE_ADDED,
                        xpath=xpath,
                        detail=f"Attribute '{name}' added with value '{attrs_b[name]}'",
                        value_b=attrs_b[name],
                    )
                )
            elif name not in attrs_b:
                diffs.append(
                    Difference(
                        kind=DiffKind.ATTRIBUTE_REMOVED,
                        xpath=xpath,
                        detail=f"Attribute '{name}' removed (was '{attrs_a[name]}')",
                        value_a=attrs_a[name],
                    )
                )
            elif attrs_a[name] != attrs_b[name]:
                diffs.append(
                    Difference(
                        kind=DiffKind.ATTRIBUTE_CHANGED,
                        xpath=xpath,
                        detail=(
                            f"Attribute '{name}' changed "
                            f"from '{attrs_a[name]}' to '{attrs_b[name]}'"
                        ),
                        value_a=attrs_a[name],
                        value_b=attrs_b[name],
                    )
                )

    def _compare_text(
        self,
        elem_a: etree._Element,
        elem_b: etree._Element,
        xpath: str,
        diffs: list[Difference],
    ) -> None:
        text_a = _normalise_text(elem_a.text) if self.ignore_whitespace_text else (elem_a.text or "")
        text_b = _normalise_text(elem_b.text) if self.ignore_whitespace_text else (elem_b.text or "")
        if text_a != text_b:
            diffs.append(
                Difference(
                    kind=DiffKind.TEXT_CHANGED,
                    xpath=xpath,
                    detail=f"Text changed from '{text_a}' to '{text_b}'",
                    value_a=text_a,
                    value_b=text_b,
                )
            )

    def _compare_children(
        self,
        elem_a: etree._Element,
        elem_b: etree._Element,
        root_a: etree._Element,
        root_b: etree._Element,
        xpath: str,
        diffs: list[Difference],
    ) -> None:
        children_a = list(elem_a)
        children_b = list(elem_b)
        len_a, len_b = len(children_a), len(children_b)
        common = min(len_a, len_b)

        for i in range(common):
            self._compare_elements(
                children_a[i], children_b[i], root_a, root_b, diffs
            )

        # Extra children in A (removed in B)
        for i in range(common, len_a):
            child_xpath = _element_xpath(children_a[i], root_a)
            diffs.append(
                Difference(
                    kind=DiffKind.ELEMENT_REMOVED,
                    xpath=child_xpath,
                    detail=f"Element <{children_a[i].tag}> at position {i + 1} was removed",
                    value_a=_element_to_string(children_a[i]),
                )
            )

        # Extra children in B (added)
        for i in range(common, len_b):
            child_xpath = f"{xpath}/{children_b[i].tag}[{i + 1}]"
            diffs.append(
                Difference(
                    kind=DiffKind.ELEMENT_ADDED,
                    xpath=child_xpath,
                    detail=f"Element <{children_b[i].tag}> at position {i + 1} was added",
                    value_b=_element_to_string(children_b[i]),
                )
            )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _element_to_string(elem: etree._Element) -> str:
    """Serialise an element to a compact string."""
    return etree.tostring(elem, encoding="unicode").strip()

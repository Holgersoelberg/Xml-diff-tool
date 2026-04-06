"""xml_diff – compare two XML documents and report differences."""

from .comparator import XmlComparator
from .report import DiffReport

__all__ = ["XmlComparator", "DiffReport"]

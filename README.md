# Xml-diff-tool

A Python tool that compares two XML documents, **ignores comments**, and generates a
detailed difference report in both plain-text and HTML formats.

---

## Features

| Feature | Details |
|---|---|
| Comment-aware | XML comments are completely stripped before comparison |
| Structural diff | Detects added/removed elements at any nesting depth |
| Attribute diff | Reports added, removed, and changed attributes |
| Text diff | Detects changes to element text content |
| Tag diff | Detects tag renames at the same position |
| Whitespace normalisation | Whitespace-only text nodes are ignored by default |
| Two report formats | Plain-text (console / file) **and** self-contained HTML |
| Stable exit code | `0` = identical, `1` = differences, `2` = error |

---

## Installation

```bash
pip install lxml          # only external dependency
pip install -e .          # install the package in development mode
```

---

## Command-line usage

```text
xml-diff  FILE_A  FILE_B  [--output-text REPORT.txt]  [--output-html REPORT.html]
```

### Example

```bash
xml-diff document_v1.xml document_v2.xml \
    --output-text diff.txt \
    --output-html diff.html
```

Console output:

```
========================================================================
XML DIFF REPORT
  Document A : document_v1.xml
  Document B : document_v2.xml
========================================================================
Total differences: 3

[1] ATTR CHANGED
    Location : /catalog/product[1]
    Detail   : Attribute 'category' changed from 'widgets' to 'gadgets'
    Value A  : widgets
    Value B  : gadgets

[2] TEXT CHANGED
    Location : /catalog/product[1]/price
    Detail   : Text changed from '9.99' to '11.99'
    Value A  : 9.99
    Value B  : 11.99

[3] ADDED
    Location : /catalog/product[2]/discount[3]
    Detail   : Element <discount> at position 3 was added
    Value B  : <discount>10%</discount>

========================================================================
```

### Options

| Option | Default | Description |
|---|---|---|
| `--output-text FILE` | – | Write plain-text report to FILE |
| `--output-html FILE` | – | Write HTML report to FILE |
| `--no-ignore-whitespace` | off | Treat whitespace-only text differences as real differences |

---

## Python API

```python
from xml_diff import XmlComparator, DiffReport

comparator = XmlComparator()                    # ignore_whitespace_text=True by default

# Compare files
diffs = comparator.compare_files("a.xml", "b.xml")

# Or compare XML strings
diffs = comparator.compare_strings("<root><a/></root>", "<root><b/></root>")

# Generate reports
report = DiffReport(diffs, label_a="a.xml", label_b="b.xml")
print(report.as_text())          # plain text
report.write_html("diff.html")   # HTML file
```

---

## Running the tests

```bash
pip install pytest lxml
pytest tests/ -v
```

---

## Project structure

```
xml_diff/
  __init__.py       – public exports
  comparator.py     – core XML comparison logic (XmlComparator, Difference, DiffKind)
  report.py         – report rendering (DiffReport -> text / HTML)
  cli.py            – command-line entry point
  __main__.py       – allows `python -m xml_diff`
tests/
  test_comparator.py
  test_report.py
  test_cli.py
```

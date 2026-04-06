"""Allow the package to be run as ``python -m xml_diff``."""
import sys

from .cli import main

sys.exit(main())

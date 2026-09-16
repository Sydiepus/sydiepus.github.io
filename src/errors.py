"""Build-time diagnostics.

Lives in its own module because build.py imports src.photos, so photos.py
cannot import these back out of build.py without a cycle. Every build-time
failure should go through die() so the output looks the same wherever it
came from.
"""

from __future__ import annotations

import sys
from typing import NoReturn


def warn(msg: str) -> None:
    print(f"  \033[33mwarning:\033[0m {msg}", file=sys.stderr)


def die(msg: str) -> NoReturn:
    """Annotated NoReturn so type checkers know control stops here.

    Without it, callers have to write an unreachable `return {}` after every
    die() to satisfy the declared return type.
    """
    print(f"\033[31merror:\033[0m {msg}", file=sys.stderr)
    raise SystemExit(1)

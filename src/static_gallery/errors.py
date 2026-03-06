from __future__ import annotations

import sys
from typing import NoReturn


def error(msg: str) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(1)

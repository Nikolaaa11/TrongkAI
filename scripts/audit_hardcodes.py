"""Audita el código en busca de hardcodes / supuestos huérfanos.

Pasa si:
- No hay `TODO: parametrizar` sin referencia a SUPUESTOS.md

Falla con exit code 1 si encuentra algo.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Patrones a buscar
PATTERN_TODO = re.compile(r"TODO[:\s]*parametrizar", re.IGNORECASE)

# Glob patterns a auditar
GLOBS = [
    "apps/engine/trongkai_engine/**/*.py",
    "apps/web/app/**/*.tsx",
    "apps/web/components/**/*.tsx",
]


def audit() -> int:
    issues: list[str] = []

    for glob in GLOBS:
        for path in ROOT.glob(glob):
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                if PATTERN_TODO.search(line) and "SUPUESTOS.md" not in line:
                    issues.append(f"{path.relative_to(ROOT)}:{i}: TODO parametrizar sin ref SUPUESTOS.md")

    if issues:
        print("AUDITORÍA: HARDCODES PENDIENTES")
        for i in issues:
            print(f"  {i}")
        return 1
    print("AUDITORÍA OK — sin hardcodes huérfanos")
    return 0


if __name__ == "__main__":
    sys.exit(audit())

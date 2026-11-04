"""Launcher del motor housing_lima.

Uso: python .claude/skills/buy-vs-rent/scripts/hl.py <comando> [args]
Comandos: intake, run, sensitivity, explain, listings, app
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from housing_lima.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

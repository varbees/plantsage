from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import Settings


def main() -> int:
    readiness = Settings.from_env().readiness(include_internal=True)
    print(readiness)
    return 0 if readiness["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

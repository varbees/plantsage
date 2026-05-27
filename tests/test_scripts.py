import subprocess
import sys


def test_check_live_ready_script_runs_from_repo_root():
    result = subprocess.run(
        [sys.executable, "scripts/check_live_ready.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert "ModuleNotFoundError" not in result.stderr
    assert "missing" in result.stdout

import subprocess
import sys
import os


def test_check_live_ready_script_runs_from_repo_root():
    result = subprocess.run(
        [sys.executable, "scripts/check_live_ready.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert "ModuleNotFoundError" not in result.stderr
    assert "missing" in result.stdout


def test_research_worker_script_can_run_once_with_empty_queue(tmp_path):
    env = {
        **os.environ,
        "PLANTSAGE_SKIP_DOTENV": "1",
        "PLANTSAGE_DB_PATH": str(tmp_path / "plants.db"),
        "PLANTSAGE_REPORTS_DIR": str(tmp_path / "reports"),
    }
    result = subprocess.run(
        [sys.executable, "scripts/run_research_worker.py", "--once"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "idle" in result.stdout

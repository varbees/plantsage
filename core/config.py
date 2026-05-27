"""Runtime configuration for local and Cloud Run deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _truthy(value: str | None) -> bool:
    return (value or "").lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    gcp_project_id: str | None
    google_application_credentials: str | None
    google_application_credentials_json: str | None
    vertex_location: str
    vertex_gemini_model: str
    anthropic_model: str
    runtime_dir: Path
    reports_dir: Path
    uploads_dir: Path
    db_path: Path
    mock_identify: bool
    mock_research: bool

    @classmethod
    def from_env(cls) -> "Settings":
        runtime_dir = cls._runtime_dir_from_env()
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            gcp_project_id=os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID"),
            google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            google_application_credentials_json=os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"),
            vertex_location=os.getenv("VERTEX_LOCATION", "us-central1"),
            vertex_gemini_model=os.getenv("VERTEX_GEMINI_MODEL", "gemini-2.5-flash"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            runtime_dir=runtime_dir,
            reports_dir=Path(os.getenv("PLANTSAGE_REPORTS_DIR", str(runtime_dir / "generated_reports"))),
            uploads_dir=Path(os.getenv("PLANTSAGE_UPLOADS_DIR", str(runtime_dir / "data" / "uploads"))),
            db_path=Path(os.getenv("PLANTSAGE_DB_PATH", str(runtime_dir / "plantsage_observations.db"))),
            mock_identify=_truthy(os.getenv("PLANTSAGE_MOCK_IDENTIFY")),
            mock_research=_truthy(os.getenv("PLANTSAGE_MOCK_RESEARCH")),
        )

    @staticmethod
    def _runtime_dir_from_env() -> Path:
        if os.getenv("PLANTSAGE_RUNTIME_DIR"):
            return Path(os.environ["PLANTSAGE_RUNTIME_DIR"])
        if _truthy(os.getenv("VERCEL")):
            return Path("/tmp/plantsage")
        return Path(".")

    def ensure_google_credentials_file(self) -> Path | None:
        if self.google_application_credentials:
            path = Path(self.google_application_credentials)
            if path.exists():
                return path

        if not self.google_application_credentials_json:
            return None

        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        path = self.runtime_dir / "google-credentials.json"
        if not path.exists():
            path.write_text(self.google_application_credentials_json, encoding="utf-8")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)
        return path

    def readiness(self) -> dict[str, Any]:
        missing: list[str] = []
        if not self.mock_identify:
            if not self.gcp_project_id:
                missing.append("GCP_PROJECT_ID")
            if self.google_application_credentials_json:
                pass
            elif self.google_application_credentials:
                if not Path(self.google_application_credentials).exists():
                    missing.append("GOOGLE_APPLICATION_CREDENTIALS(file missing)")
            else:
                missing.append("GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_JSON")

        if not self.mock_research and not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")

        mode = "mock" if self.mock_identify and self.mock_research else "mixed" if self.mock_identify or self.mock_research else "live"
        return {
            "ready": not missing,
            "mode": mode,
            "missing": missing,
            "configured": {
                "vertex_location": self.vertex_location,
                "vertex_gemini_model": self.vertex_gemini_model,
                "anthropic_model": self.anthropic_model,
                "runtime_dir": str(self.runtime_dir),
                "reports_dir": str(self.reports_dir),
                "uploads_dir": str(self.uploads_dir),
                "db_path": str(self.db_path),
                "mock_identify": self.mock_identify,
                "mock_research": self.mock_research,
                "anthropic_api_key": bool(self.anthropic_api_key),
                "gcp_project_id": bool(self.gcp_project_id),
                "google_application_credentials": bool(self.google_application_credentials),
                "google_application_credentials_json": bool(self.google_application_credentials_json),
            },
        }


def get_settings() -> Settings:
    return Settings.from_env()

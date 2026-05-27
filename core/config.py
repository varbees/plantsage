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
    gemini_api_key: str | None
    gemini_model: str
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
            gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_IDENTIFICATION_MODEL", "gemini-2.5-flash"),
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

    def readiness(self, *, include_internal: bool = False) -> dict[str, Any]:
        missing: list[str] = []
        missing_env: list[str] = []
        if not self.mock_identify and not self.gemini_api_key:
            missing.append("identifier credential")
            missing_env.append("GEMINI_API_KEY")

        if not self.mock_research and not self.anthropic_api_key:
            missing.append("research credential")
            missing_env.append("ANTHROPIC_API_KEY")

        mode = "mock" if self.mock_identify and self.mock_research else "mixed" if self.mock_identify or self.mock_research else "live"
        services = {
            "identifier": "mock" if self.mock_identify else "gemini",
            "research": "mock" if self.mock_research else "claude",
        }
        models = {
            "identifier": self.gemini_model,
            "research": self.anthropic_model,
        }
        payload: dict[str, Any] = {
            "ready": not missing,
            "mode": mode,
            "missing": missing,
            "missing_count": len(missing),
            "services": services,
            "models": models,
        }
        if include_internal or _truthy(os.getenv("PLANTSAGE_READY_VERBOSE")):
            payload["missing_env"] = missing_env
            payload["configured"] = {
                "gemini_model": self.gemini_model,
                "anthropic_model": self.anthropic_model,
                "runtime_dir": str(self.runtime_dir),
                "reports_dir": str(self.reports_dir),
                "uploads_dir": str(self.uploads_dir),
                "db_path": str(self.db_path),
                "mock_identify": self.mock_identify,
                "mock_research": self.mock_research,
                "gemini_api_key": bool(self.gemini_api_key),
                "anthropic_api_key": bool(self.anthropic_api_key),
            }
        return payload


def get_settings() -> Settings:
    return Settings.from_env()

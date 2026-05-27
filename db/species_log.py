"""Local SQLite species log for personal flora skill building."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import get_settings

DEFAULT_DB_PATH = get_settings().db_path


def familiarity_for_count(times_seen: int) -> str:
    if times_seen >= 10:
        return "expert"
    if times_seen >= 5:
        return "familiar"
    if times_seen >= 2:
        return "learning"
    return "new"


class SpeciesLog:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    async def init_db(self) -> None:
        await asyncio.to_thread(self._init_db_sync)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_columns(self, db: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
        existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, definition in columns.items():
            if name not in existing:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def _init_db_sync(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observed_at TEXT NOT NULL,
                    scientific_name TEXT NOT NULL,
                    family TEXT,
                    telugu_name TEXT,
                    district TEXT,
                    latitude REAL,
                    longitude REAL,
                    confidence REAL,
                    image_path TEXT,
                    image_sha256 TEXT,
                    image_mime_type TEXT
                )
                """
            )
            self._ensure_columns(
                db,
                "observations",
                {
                    "image_sha256": "TEXT",
                    "image_mime_type": "TEXT",
                },
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS species_knowledge (
                    scientific_name TEXT PRIMARY KEY,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    times_seen INTEGER NOT NULL DEFAULT 0,
                    familiarity_level TEXT NOT NULL DEFAULT 'new',
                    personal_notes TEXT,
                    ayurvedic_uses_learned INTEGER NOT NULL DEFAULT 0,
                    folk_uses_learned INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS report_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id INTEGER,
                    scientific_name TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'complete',
                    FOREIGN KEY(observation_id) REFERENCES observations(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS report_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_run_id INTEGER NOT NULL,
                    artifact_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    FOREIGN KEY(report_run_id) REFERENCES report_runs(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS report_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_run_id INTEGER NOT NULL,
                    source_text TEXT NOT NULL,
                    source_index INTEGER NOT NULL,
                    FOREIGN KEY(report_run_id) REFERENCES report_runs(id)
                )
                """
            )

    async def log_observation(
        self,
        *,
        scientific_name: str,
        telugu_name: str | None = None,
        family: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        district: str | None = None,
        confidence: float | None = None,
        image_path: str | None = None,
        image_sha256: str | None = None,
        mime_type: str | None = None,
    ) -> int:
        return await asyncio.to_thread(
            self._log_observation_sync,
            scientific_name,
            telugu_name,
            family,
            latitude,
            longitude,
            district,
            confidence,
            image_path,
            image_sha256,
            mime_type,
        )

    def _log_observation_sync(
        self,
        scientific_name: str,
        telugu_name: str | None,
        family: str | None,
        latitude: float | None,
        longitude: float | None,
        district: str | None,
        confidence: float | None,
        image_path: str | None,
        image_sha256: str | None,
        mime_type: str | None,
    ) -> int:
        if not scientific_name:
            raise ValueError("scientific_name is required")

        self._init_db_sync()
        now = datetime.now().isoformat(timespec="seconds")

        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO observations (
                    observed_at, scientific_name, family, telugu_name, district,
                    latitude, longitude, confidence, image_path, image_sha256, image_mime_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    scientific_name,
                    family,
                    telugu_name,
                    district,
                    latitude,
                    longitude,
                    confidence,
                    image_path,
                    image_sha256,
                    mime_type,
                ),
            )
            observation_id = int(cursor.lastrowid)

            existing = db.execute(
                "SELECT times_seen FROM species_knowledge WHERE scientific_name = ?",
                (scientific_name,),
            ).fetchone()
            if existing:
                times_seen = int(existing["times_seen"]) + 1
                db.execute(
                    """
                    UPDATE species_knowledge
                    SET last_seen = ?,
                        times_seen = ?,
                        familiarity_level = ?
                    WHERE scientific_name = ?
                    """,
                    (now, times_seen, familiarity_for_count(times_seen), scientific_name),
                )
            else:
                db.execute(
                    """
                    INSERT INTO species_knowledge (
                        scientific_name, first_seen, last_seen, times_seen, familiarity_level
                    )
                    VALUES (?, ?, ?, 1, 'new')
                    """,
                    (scientific_name, now, now),
                )
            return observation_id

    async def register_report(
        self,
        *,
        observation_id: int | None,
        scientific_name: str,
        slug: str,
        artifacts: dict[str, str | None],
        sources: list[str] | None = None,
    ) -> int:
        return await asyncio.to_thread(
            self._register_report_sync,
            observation_id,
            scientific_name,
            slug,
            artifacts,
            sources or [],
        )

    def _register_report_sync(
        self,
        observation_id: int | None,
        scientific_name: str,
        slug: str,
        artifacts: dict[str, str | None],
        sources: list[str],
    ) -> int:
        self._init_db_sync()
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO report_runs (observation_id, scientific_name, slug, created_at, status)
                VALUES (?, ?, ?, ?, 'complete')
                """,
                (observation_id, scientific_name, slug, now),
            )
            report_run_id = int(cursor.lastrowid)
            for artifact_type, path in artifacts.items():
                if path:
                    db.execute(
                        """
                        INSERT INTO report_artifacts (report_run_id, artifact_type, path)
                        VALUES (?, ?, ?)
                        """,
                        (report_run_id, artifact_type, path),
                    )
            for index, source in enumerate(sources):
                if source:
                    db.execute(
                        """
                        INSERT INTO report_sources (report_run_id, source_text, source_index)
                        VALUES (?, ?, ?)
                        """,
                        (report_run_id, source, index),
                    )
            return report_run_id

    async def get_species_log(self, *, district: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_species_log_sync, district, limit)

    def _get_species_log_sync(self, district: str | None, limit: int) -> list[dict[str, Any]]:
        self._init_db_sync()
        limit = max(1, min(int(limit), 500))
        with self._connect() as db:
            if district:
                rows = db.execute(
                    """
                    SELECT sk.*, MAX(o.observed_at) AS last_observation, MAX(o.district) AS district
                    FROM species_knowledge sk
                    JOIN observations o ON sk.scientific_name = o.scientific_name
                    WHERE o.district = ?
                    GROUP BY sk.scientific_name
                    ORDER BY sk.times_seen DESC, sk.last_seen DESC
                    LIMIT ?
                    """,
                    (district, limit),
                ).fetchall()
            else:
                rows = db.execute(
                    """
                    SELECT sk.*, MAX(o.observed_at) AS last_observation, MAX(o.district) AS latest_district
                    FROM species_knowledge sk
                    JOIN observations o ON sk.scientific_name = o.scientific_name
                    GROUP BY sk.scientific_name
                    ORDER BY sk.times_seen DESC, sk.last_seen DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    async def get_observations(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_observations_sync, limit)

    def _get_observations_sync(self, limit: int) -> list[dict[str, Any]]:
        self._init_db_sync()
        limit = max(1, min(int(limit), 500))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT *
                FROM observations
                ORDER BY observed_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    async def get_reports_for_species(self, scientific_name: str, *, limit: int = 20) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_reports_for_species_sync, scientific_name, limit)

    def _get_reports_for_species_sync(self, scientific_name: str, limit: int) -> list[dict[str, Any]]:
        self._init_db_sync()
        limit = max(1, min(int(limit), 100))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    rr.id,
                    rr.observation_id,
                    rr.scientific_name,
                    rr.slug,
                    rr.created_at,
                    rr.status,
                    COUNT(DISTINCT ra.id) AS artifact_count,
                    COUNT(DISTINCT rs.id) AS source_count
                FROM report_runs rr
                LEFT JOIN report_artifacts ra ON ra.report_run_id = rr.id
                LEFT JOIN report_sources rs ON rs.report_run_id = rr.id
                WHERE rr.scientific_name = ?
                GROUP BY rr.id
                ORDER BY rr.created_at DESC, rr.id DESC
                LIMIT ?
                """,
                (scientific_name, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    async def get_recent_reports(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_recent_reports_sync, limit)

    def _get_recent_reports_sync(self, limit: int) -> list[dict[str, Any]]:
        self._init_db_sync()
        limit = max(1, min(int(limit), 100))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    rr.id,
                    rr.observation_id,
                    rr.scientific_name,
                    rr.slug,
                    rr.created_at,
                    rr.status,
                    COUNT(DISTINCT ra.id) AS artifact_count,
                    COUNT(DISTINCT rs.id) AS source_count,
                    GROUP_CONCAT(ra.artifact_type || ':' || ra.path, '||') AS artifacts
                FROM report_runs rr
                LEFT JOIN report_artifacts ra ON ra.report_run_id = rr.id
                LEFT JOIN report_sources rs ON rs.report_run_id = rr.id
                GROUP BY rr.id
                ORDER BY rr.created_at DESC, rr.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    async def get_dashboard_summary(self) -> dict[str, int]:
        return await asyncio.to_thread(self._get_dashboard_summary_sync)

    def _get_dashboard_summary_sync(self) -> dict[str, int]:
        self._init_db_sync()
        with self._connect() as db:
            row = db.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM observations) AS total_observations,
                    (SELECT COUNT(*) FROM species_knowledge) AS total_species,
                    (SELECT COUNT(*) FROM report_runs) AS total_report_runs,
                    (SELECT COUNT(*) FROM report_sources) AS total_sources
                """
            ).fetchone()
        return dict(row)


default_log = SpeciesLog()


async def init_db() -> None:
    await default_log.init_db()


async def log_observation(**kwargs: Any) -> int:
    return await default_log.log_observation(**kwargs)


async def get_species_log(district: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    return await default_log.get_species_log(district=district, limit=limit)


async def register_report(**kwargs: Any) -> int:
    return await default_log.register_report(**kwargs)


async def get_observations(limit: int = 50) -> list[dict[str, Any]]:
    return await default_log.get_observations(limit=limit)


async def get_reports_for_species(scientific_name: str, limit: int = 20) -> list[dict[str, Any]]:
    return await default_log.get_reports_for_species(scientific_name, limit=limit)


async def get_recent_reports(limit: int = 20) -> list[dict[str, Any]]:
    return await default_log.get_recent_reports(limit=limit)


async def get_dashboard_summary() -> dict[str, int]:
    return await default_log.get_dashboard_summary()

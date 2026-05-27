"""Local SQLite species log for personal flora skill building."""

from __future__ import annotations

import asyncio
import hashlib
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import get_settings

DEFAULT_DB_PATH = get_settings().db_path
SOURCE_URL_RE = re.compile(r"https?://[^\s)]+")


def familiarity_for_count(times_seen: int) -> str:
    if times_seen >= 10:
        return "expert"
    if times_seen >= 5:
        return "familiar"
    if times_seen >= 2:
        return "learning"
    return "new"


def source_document_parts(source_text: str) -> dict[str, str | None]:
    cleaned = source_text.strip()
    match = SOURCE_URL_RE.search(cleaned)
    url = match.group(0) if match else None
    title = cleaned
    if url:
        title = f"{cleaned[:match.start()]} {cleaned[match.end():]}".strip(" -:") or url
    return {
        "source_text": cleaned,
        "title": title or None,
        "url": url,
        "content_hash": hashlib.sha256(cleaned.encode("utf-8")).hexdigest(),
        "source_type": "web" if url else "text",
    }


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
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS determinations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id INTEGER NOT NULL,
                    scientific_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL,
                    basis TEXT,
                    is_current INTEGER NOT NULL DEFAULT 1,
                    raw_payload TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(observation_id) REFERENCES observations(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS research_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id INTEGER,
                    scientific_name TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    report_run_id INTEGER,
                    error_message TEXT,
                    FOREIGN KEY(observation_id) REFERENCES observations(id),
                    FOREIGN KEY(report_run_id) REFERENCES report_runs(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS source_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_run_id INTEGER,
                    source_index INTEGER NOT NULL DEFAULT 0,
                    source_type TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    content_hash TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    license TEXT,
                    FOREIGN KEY(report_run_id) REFERENCES report_runs(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS plant_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_run_id INTEGER,
                    scientific_name TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    claim_text TEXT NOT NULL,
                    source_document_id INTEGER,
                    confidence REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(report_run_id) REFERENCES report_runs(id),
                    FOREIGN KEY(source_document_id) REFERENCES source_documents(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS vernacular_names (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scientific_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    language TEXT,
                    script TEXT,
                    region TEXT,
                    source_document_id INTEGER,
                    ambiguity_note TEXT,
                    FOREIGN KEY(source_document_id) REFERENCES source_documents(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS region_occurrences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scientific_name TEXT NOT NULL,
                    region_key TEXT NOT NULL,
                    district TEXT,
                    state TEXT,
                    latitude REAL,
                    longitude REAL,
                    evidence_source TEXT NOT NULL,
                    confidence REAL,
                    observed_at TEXT,
                    source_document_id INTEGER,
                    FOREIGN KEY(source_document_id) REFERENCES source_documents(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS review_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id INTEGER,
                    determination_id INTEGER,
                    reviewer TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(observation_id) REFERENCES observations(id),
                    FOREIGN KEY(determination_id) REFERENCES determinations(id)
                )
                """
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_determinations_observation ON determinations(observation_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_research_jobs_status ON research_jobs(status, updated_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_source_documents_report ON source_documents(report_run_id)")

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
            db.execute(
                """
                INSERT INTO determinations (
                    observation_id, scientific_name, source, confidence, basis, created_at
                )
                VALUES (?, ?, 'gemini_identifier', ?, 'initial visual identification', ?)
                """,
                (observation_id, scientific_name, confidence, now),
            )

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

    async def create_research_job(
        self,
        *,
        observation_id: int | None,
        scientific_name: str,
        mode: str,
        provider: str,
        status: str = "queued",
    ) -> int:
        return await asyncio.to_thread(
            self._create_research_job_sync,
            observation_id,
            scientific_name,
            mode,
            provider,
            status,
        )

    def _create_research_job_sync(
        self,
        observation_id: int | None,
        scientific_name: str,
        mode: str,
        provider: str,
        status: str,
    ) -> int:
        if not scientific_name:
            raise ValueError("scientific_name is required")

        self._init_db_sync()
        now = datetime.now().isoformat(timespec="seconds")
        started_at = now if status == "running" else None
        completed_at = now if status in {"complete", "failed"} else None
        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO research_jobs (
                    observation_id, scientific_name, mode, provider, status,
                    created_at, updated_at, started_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (observation_id, scientific_name, mode, provider, status, now, now, started_at, completed_at),
            )
            return int(cursor.lastrowid)

    async def update_research_job(
        self,
        job_id: int,
        *,
        status: str,
        report_run_id: int | None = None,
        error_message: str | None = None,
    ) -> None:
        await asyncio.to_thread(self._update_research_job_sync, job_id, status, report_run_id, error_message)

    def _update_research_job_sync(
        self,
        job_id: int,
        status: str,
        report_run_id: int | None,
        error_message: str | None,
    ) -> None:
        self._init_db_sync()
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as db:
            existing = db.execute("SELECT started_at FROM research_jobs WHERE id = ?", (job_id,)).fetchone()
            if not existing:
                raise ValueError(f"research_job {job_id} not found")

            started_at = existing["started_at"]
            if status == "running" and not started_at:
                started_at = now
            completed_at = now if status in {"complete", "failed"} else None
            db.execute(
                """
                UPDATE research_jobs
                SET status = ?,
                    updated_at = ?,
                    started_at = COALESCE(?, started_at),
                    completed_at = COALESCE(?, completed_at),
                    report_run_id = COALESCE(?, report_run_id),
                    error_message = ?
                WHERE id = ?
                """,
                (status, now, started_at, completed_at, report_run_id, error_message, job_id),
            )

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
                    source_text = source.strip()
                    db.execute(
                        """
                        INSERT INTO report_sources (report_run_id, source_text, source_index)
                        VALUES (?, ?, ?)
                        """,
                        (report_run_id, source_text, index),
                    )
                    document = source_document_parts(source_text)
                    db.execute(
                        """
                        INSERT INTO source_documents (
                            report_run_id, source_index, source_type, source_text,
                            title, url, content_hash, fetched_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            report_run_id,
                            index,
                            document["source_type"],
                            document["source_text"],
                            document["title"],
                            document["url"],
                            document["content_hash"],
                            now,
                        ),
                    )
            return report_run_id

    async def get_recent_research_jobs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_recent_research_jobs_sync, limit)

    def _get_recent_research_jobs_sync(self, limit: int) -> list[dict[str, Any]]:
        self._init_db_sync()
        limit = max(1, min(int(limit), 100))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT *
                FROM research_jobs
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    async def claim_next_research_job(self) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._claim_next_research_job_sync)

    def _claim_next_research_job_sync(self) -> dict[str, Any] | None:
        self._init_db_sync()
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                """
                SELECT
                    rj.*,
                    o.family,
                    o.telugu_name,
                    o.district,
                    o.latitude,
                    o.longitude,
                    o.confidence,
                    o.image_path,
                    o.image_sha256,
                    o.image_mime_type
                FROM research_jobs rj
                LEFT JOIN observations o ON o.id = rj.observation_id
                WHERE rj.status = 'queued'
                ORDER BY rj.created_at ASC, rj.id ASC
                LIMIT 1
                """
            ).fetchone()
            if not row:
                return None

            db.execute(
                """
                UPDATE research_jobs
                SET status = 'running',
                    updated_at = ?,
                    started_at = COALESCE(started_at, ?),
                    error_message = NULL
                WHERE id = ?
                """,
                (now, now, row["id"]),
            )

        payload = dict(row)
        payload["status"] = "running"
        payload["updated_at"] = now
        payload["started_at"] = payload.get("started_at") or now
        return payload

    async def get_source_documents_for_report(self, report_run_id: int) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_source_documents_for_report_sync, report_run_id)

    def _get_source_documents_for_report_sync(self, report_run_id: int) -> list[dict[str, Any]]:
        self._init_db_sync()
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT *
                FROM source_documents
                WHERE report_run_id = ?
                ORDER BY source_index ASC, id ASC
                """,
                (report_run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

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
                    (
                        SELECT COUNT(*)
                        FROM report_artifacts ra
                        WHERE ra.report_run_id = rr.id
                    ) AS artifact_count,
                    (
                        SELECT COUNT(*)
                        FROM report_sources rs
                        WHERE rs.report_run_id = rr.id
                    ) AS source_count,
                    (
                        SELECT GROUP_CONCAT(ra.artifact_type || ':' || ra.path, '||')
                        FROM report_artifacts ra
                        WHERE ra.report_run_id = rr.id
                    ) AS artifacts
                FROM report_runs rr
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
                    (SELECT COUNT(*) FROM report_sources) AS total_sources,
                    (SELECT COUNT(*) FROM research_jobs) AS total_research_jobs,
                    (SELECT COUNT(*) FROM source_documents) AS total_source_documents,
                    (SELECT COUNT(*) FROM plant_claims) AS total_plant_claims
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


async def create_research_job(**kwargs: Any) -> int:
    return await default_log.create_research_job(**kwargs)


async def update_research_job(job_id: int, **kwargs: Any) -> None:
    await default_log.update_research_job(job_id, **kwargs)


async def get_observations(limit: int = 50) -> list[dict[str, Any]]:
    return await default_log.get_observations(limit=limit)


async def get_reports_for_species(scientific_name: str, limit: int = 20) -> list[dict[str, Any]]:
    return await default_log.get_reports_for_species(scientific_name, limit=limit)


async def get_recent_reports(limit: int = 20) -> list[dict[str, Any]]:
    return await default_log.get_recent_reports(limit=limit)


async def get_recent_research_jobs(limit: int = 20) -> list[dict[str, Any]]:
    return await default_log.get_recent_research_jobs(limit=limit)


async def claim_next_research_job() -> dict[str, Any] | None:
    return await default_log.claim_next_research_job()


async def get_dashboard_summary() -> dict[str, int]:
    return await default_log.get_dashboard_summary()

#!/usr/bin/env python3
"""Run queued PlantSage research jobs."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.research_worker import ResearchJobWorker
from db.species_log import init_db


async def run_worker(*, once: bool, poll_interval: float, max_jobs: int | None) -> int:
    await init_db()
    worker = ResearchJobWorker()
    processed = 0
    while True:
        result = await worker.process_next_job()
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if result["status"] != "idle":
            processed += 1
        if once or (max_jobs is not None and processed >= max_jobs):
            return 0
        if result["status"] == "idle":
            await asyncio.sleep(poll_interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process queued PlantSage research jobs.")
    parser.add_argument("--once", action="store_true", help="Process at most one job, then exit.")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Seconds to wait after an idle queue.")
    parser.add_argument("--max-jobs", type=int, default=None, help="Stop after this many non-idle jobs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(run_worker(once=args.once, poll_interval=args.poll_interval, max_jobs=args.max_jobs))


if __name__ == "__main__":
    raise SystemExit(main())

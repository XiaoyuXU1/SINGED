"""Run the frozen 324-cell public-package slice with safe resumption."""

from __future__ import annotations

import argparse
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from singed.runner import run_trial


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def completed_trials(output: Path) -> set[str]:
    done = set()
    for path in output.glob("*/summary.json"):
        try:
            row = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not row.get("runner_error"):
            done.add(row["trial_id"])
    return done


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).parent / "generated/manifest.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "runs")
    parser.add_argument("--dotenv", type=Path, default=Path(".env"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    load_dotenv(args.dotenv)
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        raise SystemExit("OPENROUTER_API_KEY is not set; add it to .env or export it")

    manifest = json.loads(args.manifest.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    done = completed_trials(args.output)
    trials = [row for row in manifest["trials"] if row["trial_id"] not in done]
    if args.limit:
        trials = trials[: args.limit]
    total = len(trials)
    if not total:
        print(json.dumps({"status": "complete", "completed": len(done), "remaining": 0}))
        return

    lock = threading.Lock()
    finished = 0

    def execute(trial: dict) -> dict:
        return run_trial(
            args.manifest,
            trial["trial_id"],
            args.output,
            timeout_seconds=args.timeout,
            max_turns=args.max_turns,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(execute, row): row for row in trials}
        for future in as_completed(futures):
            trial = futures[future]
            try:
                summary = future.result()
                event = {
                    "trial_id": trial["trial_id"],
                    "runner_error": summary.get("runner_error"),
                    "task_success": summary.get("task_success"),
                    "counterfeit_executed": summary.get("counterfeit_executed"),
                }
            except Exception as exc:  # an outer failure before summary persistence
                event = {"trial_id": trial["trial_id"], "runner_error": f"{type(exc).__name__}: {exc}"}
            with lock:
                finished += 1
                print(json.dumps({"finished": finished, "scheduled": total, **event}), flush=True)


if __name__ == "__main__":
    main()

"""Experiment runner using OpenRouter for every model family."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .agent import run_agent
from .openrouter import OpenRouterClient, OpenRouterConfig
from .scoring import score_events
from .world import TrialWorld


def run_trial(
    manifest_path: str | Path,
    trial_id: str,
    output_root: str | Path,
    *,
    timeout_seconds: int = 180,
    max_turns: int = 20,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("api") != "openrouter":
        raise ValueError("manifest must use the OpenRouter API")
    trial = next(row for row in manifest["trials"] if row["trial_id"] == trial_id)
    safe_id = trial_id.replace("/", "_")
    run_dir = Path(output_root) / f"{safe_id}--{time.strftime('%Y%m%d-%H%M%S')}"
    world = TrialWorld(manifest_path, trial_id, run_dir)
    client = OpenRouterClient(OpenRouterConfig.from_env(timeout_seconds=timeout_seconds))
    error: str | None = None
    agent_result: dict[str, Any] = {}
    try:
        agent_result = run_agent(
            client=client,
            world=world,
            model=trial["model"],
            policy=trial["policy"],
            max_turns=max_turns,
        )
    except Exception as exc:  # noqa: BLE001 - persist runner failures in the summary
        error = f"{type(exc).__name__}: {exc}"
    finally:
        world.close()
    metrics = score_events(run_dir / "events.jsonl")
    summary = {
        "trial_id": trial_id,
        "instance_id": trial["instance_id"],
        "model": trial["model"],
        "policy": trial["policy"],
        "depth": trial["depth"],
        "counterfeit_rank": trial["counterfeit_rank"],
        "api": "openrouter",
        "runner_error": error,
        **metrics,
        **agent_result,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary

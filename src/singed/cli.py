"""Command-line interface for benchmark preparation, execution, and analysis."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .benchmark import prepare_benchmark
from .models import load_models
from .runner import run_trial
from .scoring import aggregate


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _prepare(args) -> None:
    models = load_models(args.models)
    manifest = prepare_benchmark(
        args.output,
        models=models,
        seed=args.seed,
        instances_per_family=args.instances_per_family,
    )
    print(json.dumps({"instances": len(manifest["instances"]), "trials": len(manifest["trials"]), "api": manifest["api"]}))


def _select_trials(manifest: dict, args) -> list[dict]:
    instances = {row["instance_id"]: row for row in manifest["instances"]}
    selected = []
    for trial in manifest["trials"]:
        instance = instances[trial["instance_id"]]
        if args.model and trial["model"] != args.model:
            continue
        if args.family and instance["family"] != args.family:
            continue
        if args.policy and trial["policy"] != args.policy:
            continue
        if args.depth and trial["depth"] != args.depth:
            continue
        if args.rank and trial["counterfeit_rank"] != args.rank:
            continue
        selected.append(trial)
    return selected[: args.limit] if args.limit else selected


def _run(args) -> None:
    _load_dotenv()
    manifest = json.loads(Path(args.manifest).read_text())
    trials = _select_trials(manifest, args)
    if not trials:
        raise SystemExit("no trials match the requested filters")
    for index, trial in enumerate(trials, 1):
        summary = run_trial(
            args.manifest,
            trial["trial_id"],
            args.output,
            timeout_seconds=args.timeout,
            max_turns=args.max_turns,
        )
        print(json.dumps({"index": index, "total": len(trials), **summary}, ensure_ascii=False))


def _analyze(args) -> None:
    rows = []
    for path in Path(args.runs).glob("*/summary.json"):
        try:
            rows.append(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            pass
    if not rows:
        raise SystemExit("no summaries found")
    result = aggregate(rows, keys=tuple(args.group_by.split(",")))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text)
    print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="singed")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="generate synthetic fixtures, candidates, and schedules")
    prepare.add_argument("--output", default="benchmark/generated")
    prepare.add_argument("--models", default="configs/models.json")
    prepare.add_argument("--seed", type=int, default=20260909)
    prepare.add_argument("--instances-per-family", type=int, default=3)
    prepare.set_defaults(func=_prepare)

    run = sub.add_parser("run", help="run matching frozen trials through OpenRouter")
    run.add_argument("--manifest", default="benchmark/generated/manifest.json")
    run.add_argument("--output", default="runs")
    run.add_argument("--model")
    run.add_argument("--family")
    run.add_argument("--policy", choices=("baseline", "deliberation", "compare_all"))
    run.add_argument("--depth", choices=("entrypoint", "one_import", "two_imports"))
    run.add_argument("--rank", type=int, choices=(1, 2, 3))
    run.add_argument("--limit", type=int)
    run.add_argument("--timeout", type=int, default=180)
    run.add_argument("--max-turns", type=int, default=20)
    run.set_defaults(func=_run)

    analyze = sub.add_parser("analyze", help="aggregate completed trial summaries")
    analyze.add_argument("--runs", default="runs")
    analyze.add_argument("--group-by", default="model,policy")
    analyze.add_argument("--output")
    analyze.set_defaults(func=_analyze)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

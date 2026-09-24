"""Audit and summarize the public-package transfer experiment."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path


def read_rows(runs: Path) -> list[dict]:
    latest: dict[str, tuple[float, dict]] = {}
    for path in runs.glob("*/summary.json"):
        try:
            row = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        stamp = path.stat().st_mtime
        if row.get("trial_id") not in latest or stamp > latest[row["trial_id"]][0]:
            latest[row["trial_id"]] = (stamp, row)
    return [item[1] for item in latest.values()]


def rate(rows: list[dict], key: str) -> float:
    return sum(bool(row[key]) for row in rows) / len(rows) if rows else float("nan")


def cluster_interval(rows: list[dict], key: str, *, seed: int = 20260923, draws: int = 10000) -> tuple[float, float]:
    clusters = defaultdict(list)
    for row in rows:
        clusters[row["instance_id"]].append(row)
    names = sorted(clusters)
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        sample = []
        for name in rng.choices(names, k=len(names)):
            sample.extend(clusters[name])
        values.append(rate(sample, key))
    values.sort()
    return values[int(0.025 * draws)], values[int(0.975 * draws)]


def paired_policy_interval(rows: list[dict], *, seed: int = 20260923, draws: int = 10000) -> tuple[float, float, float]:
    clusters = defaultdict(list)
    for row in rows:
        clusters[row["instance_id"]].append(row)
    names = sorted(clusters)

    def difference(sample: list[dict]) -> float:
        deliberate = [row for row in sample if row["policy"] == "deliberation"]
        compare = [row for row in sample if row["policy"] == "compare_all"]
        return rate(deliberate, "counterfeit_executed") - rate(compare, "counterfeit_executed")

    estimate = difference(rows)
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        sample = []
        for name in rng.choices(names, k=len(names)):
            sample.extend(clusters[name])
        values.append(difference(sample))
    values.sort()
    return estimate, values[int(0.025 * draws)], values[int(0.975 * draws)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).parent / "generated/manifest.json")
    parser.add_argument("--runs", type=Path, default=Path(__file__).parent / "runs")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    instances = {row["instance_id"]: row for row in manifest["instances"]}
    expected = {row["trial_id"] for row in manifest["trials"]}
    rows = read_rows(args.runs)
    for row in rows:
        row["domain"] = instances[row["instance_id"]]["family"]
    observed = {row["trial_id"] for row in rows}
    errors = [row for row in rows if row.get("runner_error")]
    duplicates = len(rows) - len(observed)

    summaries = []
    groupings = (
        ("policy", "counterfeit_rank"),
        ("domain", "policy", "counterfeit_rank"),
        ("model", "policy", "counterfeit_rank"),
    )
    for keys in groupings:
        groups = defaultdict(list)
        for row in rows:
            if not row.get("runner_error"):
                groups[tuple(row[key] for key in keys)].append(row)
        for values, group in sorted(groups.items(), key=lambda item: str(item[0])):
            low, high = cluster_interval(group, "counterfeit_executed")
            summaries.append({
                **dict(zip(keys, values)),
                "n": len(group),
                "task_success": rate(group, "task_success"),
                "cer": rate(group, "counterfeit_executed"),
                "cer_ci_low": low,
                "cer_ci_high": high,
                "safe_utility": rate(group, "safe_utility"),
            })

    complete_rows = [row for row in rows if not row.get("runner_error")]
    policy_counts = {}
    for policy in ("deliberation", "compare_all"):
        group = [row for row in complete_rows if row["policy"] == policy]
        policy_counts[policy] = {
            "n": len(group),
            "task_success": sum(bool(row["task_success"]) for row in group),
            "counterfeit_executed": sum(bool(row["counterfeit_executed"]) for row in group),
            "safe_utility": sum(bool(row["safe_utility"]) for row in group),
        }
    rd, rd_low, rd_high = paired_policy_interval(complete_rows)
    headline = {
        "policy_counts": policy_counts,
        "risk_difference_deliberation_minus_compare_all": rd,
        "risk_difference_ci_low": rd_low,
        "risk_difference_ci_high": rd_high,
    }
    audit = {
        "expected_trials": len(expected),
        "observed_trials": len(observed),
        "missing_trial_ids": sorted(expected - observed),
        "unexpected_trial_ids": sorted(observed - expected),
        "runner_errors": len(errors),
        "duplicate_latest_rows": duplicates,
        "complete": observed == expected and not errors,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (args.output / "headline.json").write_text(json.dumps(headline, indent=2) + "\n")
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    fields = sorted({key for row in summaries for key in row})
    with (args.output / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(summaries)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

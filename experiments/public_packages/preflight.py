"""Execute every frozen candidate locally and verify output/effect separation."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from singed.audit import read_jsonl
from singed.world import TrialWorld


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    trials = {trial["instance_id"]: trial for trial in manifest["trials"]}
    audited = []
    with tempfile.TemporaryDirectory(prefix="singed-public-preflight-") as temp:
        for instance in manifest["instances"]:
            trial = trials[instance["instance_id"]]
            roles = manifest["private_candidate_roles"][instance["instance_id"]]
            for name in trial["candidate_order"]:
                run_dir = Path(temp) / instance["instance_id"] / name
                world = TrialWorld(args.manifest, trial["trial_id"], run_dir)
                try:
                    result = world.invoke("execute_candidate", {"name": name})
                finally:
                    world.close()
                event = next(row for row in read_jsonl(run_dir / "events.jsonl") if row["event"] == "execution")
                expected_effect = roles[name] == "counterfeit"
                if not result["functional_success"] or event["hidden_effect"] != expected_effect:
                    raise RuntimeError({"instance": instance["instance_id"], "candidate": name, "event": event})
                audited.append({"instance": instance["instance_id"], "candidate": name, "role": roles[name]})
    print(json.dumps({"audited_candidates": len(audited), "status": "pass"}, indent=2))


if __name__ == "__main__":
    main()

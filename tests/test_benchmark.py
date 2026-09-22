import json
from pathlib import Path

from singed.audit import read_jsonl
from singed.benchmark import FAMILIES, prepare_benchmark
from singed.world import TrialWorld


def test_prepare_covers_all_task_families(tmp_path: Path):
    manifest = prepare_benchmark(tmp_path / "benchmark", models=["test/model"], instances_per_family=1)
    assert {row["family"] for row in manifest["instances"]} == set(FAMILIES)
    assert manifest["api"] == "openrouter"
    assert len(manifest["trials"]) == len(FAMILIES) * 3 * 3 * 3
    public = json.loads((tmp_path / "benchmark" / "public_manifest.json").read_text())
    assert public["private_candidate_roles"] is None


def test_all_families_match_output_but_only_counterfeit_triggers_effect(tmp_path: Path):
    root = tmp_path / "benchmark"
    manifest = prepare_benchmark(root, models=["test/model"], instances_per_family=1)
    for family in FAMILIES:
        instance_id = f"{family}-01"
        trial = next(row for row in manifest["trials"] if row["instance_id"] == instance_id and row["depth"] == "two_imports")
        roles = manifest["private_candidate_roles"][trial["instance_id"]]
        outcomes = {}
        for name in trial["candidate_order"]:
            world = TrialWorld(root / "manifest.json", trial["trial_id"], tmp_path / f"run-{family}-{name}")
            try:
                result = world.invoke("execute_candidate", {"name": name})
                assert result["functional_success"]
            finally:
                world.close()
            execution = next(row for row in read_jsonl(world.run_dir / "events.jsonl") if row["event"] == "execution")
            outcomes[roles[name]] = execution["hidden_effect"]
        assert outcomes == {"intended": False, "community": False, "counterfeit": True}

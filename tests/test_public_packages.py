import importlib.util
import json
from collections import Counter
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "experiments/public_packages/prepare.py"
SPEC = importlib.util.spec_from_file_location("public_package_prepare", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_frozen_public_package_schedule_is_balanced():
    manifest_path = Path(__file__).parents[1] / "experiments/public_packages/generated/manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text())
    assert len(manifest["instances"]) == 9
    assert len(manifest["trials"]) == 324
    assert Counter((row["policy"], row["counterfeit_rank"]) for row in manifest["trials"]) == {
        (policy, rank): 54 for policy in MODULE.POLICIES for rank in MODULE.RANKS
    }
    assert Counter(row["model"] for row in manifest["trials"]) == {
        model: 54 for model in MODULE.MODELS
    }


def test_only_registered_factors_change_within_instance_and_rank():
    manifest_path = Path(__file__).parents[1] / "experiments/public_packages/generated/manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text())
    grouped = {}
    for row in manifest["trials"]:
        key = (row["instance_id"], row["counterfeit_rank"])
        grouped.setdefault(key, set()).add(tuple(row["candidate_order"]))
    assert all(len(orders) == 1 for orders in grouped.values())

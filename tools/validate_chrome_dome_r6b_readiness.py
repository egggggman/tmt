"""Validate the bounded Chrome Dome semantic gate without running matches."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

from tmnt_design_studio.card_interpreter07 import CardInterpreter  # noqa: E402
from tmnt_design_studio.stage002 import _semantic_coverage, load_catalog  # noqa: E402

RECORD = OBL / "ROUND_6_B_CHROME_DOME_READINESS.json"
OLD_RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"
BASE = "1a05fb646479494c1585bb8b2582d1ff6721797e"
EXPECTED_CANDIDATE_SHA256 = "5460b9d1288d193db3f8db7a78076dfeb38f734c79acdd1ddbe898da030b3bdf"
EXPECTED_CANDIDATE_BLOB = "53af73af05c475832bd3e8a08c67264a0ff8fd44"


def validate() -> dict:
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    candidate = ("\n".join(record["candidate_rows"]) + "\n").encode("utf-8")
    assert hashlib.sha256(candidate).hexdigest() == record["candidate_canonical_lf_sha256"]
    assert record["candidate_canonical_lf_sha256"] == EXPECTED_CANDIDATE_SHA256
    blob = (
        subprocess.check_output(
            ["git", "hash-object", "--stdin"], cwd=ROOT, input=candidate, text=False
        )
        .decode()
        .strip()
    )
    assert blob == record["candidate_git_blob_sha1"] == EXPECTED_CANDIDATE_BLOB
    # The readiness record authenticates the historical Design Studio candidate
    # by immutable commit/blob/content identities. Do not require the mutable
    # branch ref to remain pinned to that historical commit after a legitimate
    # rebase or branch recovery.
    assert record["design_studio_head_sha"] == "6315561e92c76142d3d3527538024ba55f4694ec"
    local_candidate = ROOT / record["candidate_path_in_design_studio_pr"]
    if local_candidate.exists():
        assert local_candidate.read_bytes().replace(b"\r\n", b"\n") == candidate
        assert not subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", record["candidate_path_in_design_studio_pr"]],
            cwd=ROOT,
            check=False,
        ).returncode

    baseline = json.loads(
        (OBL / "baselines/OBL_BASELINE_003_MANIFEST.json").read_text(encoding="utf-8")
    )
    krang = next(row for row in baseline["decks"] if row["deck_key"] == "krang")
    parent = Counter(dict((name, count) for count, name in r1.rows(ROOT / krang["source_path"])))
    candidate_cards = Counter()
    assert record["candidate_rows"][0] == "Deck"
    for line in record["candidate_rows"][1:]:
        count, name = line.split(" ", 1)
        candidate_cards[name] += int(count)
    assert sum(candidate_cards.values()) == 60
    assert parent - candidate_cards == Counter(record["exact_diff_from_baseline_003"]["removals"])
    assert candidate_cards - parent == Counter(record["exact_diff_from_baseline_003"]["additions"])
    catalog = r1.catalog()
    for name, count in candidate_cards.items():
        card = catalog[name]
        assert card["legalities"]["standard"] == "legal"
        assert count <= 4 or "Basic Land" in card["type_line"]
        symbols = re.findall(r"\{([^}]+)\}", card.get("mana_cost", ""))
        colors = {color for symbol in symbols for color in "WUBRG" if color in symbol}
        if "Island" in card["type_line"]:
            colors.add("U")
        assert colors <= {"U"}
    assert not subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", "decks"], cwd=ROOT, check=False
    ).returncode

    snapshot = ROOT / record["card_snapshot_path"]
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == record["card_snapshot_sha256"]
    frozen = load_catalog(ROOT).resolve_name("Chrome Dome")
    assert frozen.oracle_id == record["chrome_dome_oracle_id"]
    assert frozen.mana_cost == record["chrome_dome_mana_cost"] == "{2}"
    assert frozen.type_line == record["chrome_dome_type_line"]
    assert [int(frozen.power), int(frozen.toughness)] == record["chrome_dome_power_toughness"]
    assert frozen.legalities["standard"] == record["chrome_dome_standard_legality"] == "legal"
    assert tuple(frozen.oracle_text.splitlines()) == (
        record["required_oracle_clause"],
        record["nonrequired_oracle_clause"],
    )
    printings = [card for card in load_catalog(ROOT).cards if card.name == "Chrome Dome"]
    assert {card.scryfall_id for card in printings} == set(record["chrome_dome_scryfall_ids"])
    assert {card.oracle_id for card in printings} == {frozen.oracle_id}

    interpreter = CardInterpreter()
    static = interpreter.static_team_modifier_semantic_coverage(
        frozen, record["required_oracle_clause"]
    )
    assert static is not None and static.coverage.fully_supported
    assert (static.program.quality, static.program.power, static.program.toughness) == (
        "artifact",
        1,
        0,
    )
    unsupported = interpreter.unsupported_fragments(frozen)
    assert any(fragment == record["nonrequired_oracle_clause"] for fragment, _ in unsupported)
    copy_limits = tuple(
        reason
        for fragment, reason in unsupported
        if fragment == record["nonrequired_oracle_clause"]
    )
    assert not _semantic_coverage(
        interpreter, frozen, record["nonrequired_oracle_clause"], copy_limits
    )["fully_supported"]
    assert record["semantic_coverage"] == {
        "creature_permanent_casting": "SUPPORTED",
        "static_other_artifact_creatures_you_control_plus_1_plus_0": "SUPPORTED",
        "copy_activation": "UNSUPPORTED_OUT_OF_SCOPE",
        "whole_card_fully_executable": False,
        "hypothesis_semantics": "READY",
    }
    old = identity(BASE)["aggregate_semantic_runtime_sha256"]
    new = identity()["aggregate_semantic_runtime_sha256"]
    assert old == record["old_semantic_runtime_sha256"] == OLD_RUNTIME
    assert new == record["new_semantic_runtime_sha256"] != old
    assert record["simulations_run"] == 0
    assert not record["historical_baseline_evidence_compatible_with_new_runtime"]
    return {
        "status": "PASS",
        "candidate_sha256": record["candidate_canonical_lf_sha256"],
        "old_runtime": old,
        "new_runtime": new,
        "simulations_run": 0,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))

"""Independently audit saved replacement arithmetic and the bounded retention capacity."""

import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "docs/cardcade/PILOT_FITNESS_V2_REPLACEMENT_SEARCH.json"
data = json.loads(path.read_text())
assert len(data["records"]) == 76
assert len(data["prior"]) == 13
for name, expected in data["source_sha256_canonical_LF"].items():
    assert (
        hashlib.sha256((ROOT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == expected
    )
assert (
    hashlib.sha256(path.read_bytes()).hexdigest()
    == Path(str(path) + ".sha256").read_text().split()[0]
)
by_design = defaultdict(dict)
summary = []
branch_count = 0
for record in data["records"]:
    possible = []
    if "optimal_sets" in record:
        life = set()
        for row in record["rows"]:
            assert sum(b["weight"] for b in row["branches"]) == 60
            assert {b["replacement"]: b["weight"] for b in row["branches"]} == data["prior"]
            for branch in row["branches"]:
                assert branch["winner"] is None
                assert len(branch["endpoint_hand"]) == len(record["hand"])
                life.add(tuple(branch["life"]))
                branch_count += 1
            for objective, reported in row["reference_prior_expected_value"].items():
                assert all(b["values"][objective] in (0, 1) for b in row["branches"])
                value = sum(
                    Fraction(b["weight"], 60) * b["values"][objective] for b in row["branches"]
                )
                assert value == Fraction(reported)
        assert len(life) == 1
        for objective, optimal in record["optimal_sets"].items():
            values = [
                Fraction(r["reference_prior_expected_value"][objective]) for r in record["rows"]
            ]
            assert optimal == [i for i, v in enumerate(values) if v == max(values)]
            if optimal == [0] and not record["strict_reversals"]:
                possible.append(objective)
    if record["disposition"] == "REJECTED_SUPPORT_CONSISTENCY":
        assert all(data["prior"][c] == n for c, n in record["visible_exhaustion_counts"].items())
    by_design[(tuple(record["hand"]), record["mode"])][record["seat"]] = set(possible)
    summary.append(
        {
            "hand": record["hand"],
            "mode": record["mode"],
            "seat": record["seat"],
            "disposition": record["disposition"],
            "optimistic_strict_retention_objectives": possible,
        }
    )
capacity = [
    {"hand": hand, "mode": mode, "common_objectives": sorted(seats[0] & seats[1])}
    for (hand, mode), seats in by_design.items()
    if seats[0] & seats[1]
]
assert capacity == [{"hand": ("Mountain",), "mode": "land", "common_objectives": ["land_play"]}]
report = {
    "status": "BOUNDED_SEARCH_READINESS_STOP",
    "source_diagnostic_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "probes": 76,
    "hand_designs": 19,
    "setup_modes": 2,
    "seats": 2,
    "complete_prior_action_outcome_rows_audited": branch_count,
    "dispositions": dict(Counter(r["disposition"] for r in data["records"])),
    "optimistic_two_seat_strict_retention_capacity": capacity,
    "required_disjoint_strict_retention_roles": 2,
    "accepted_fixtures": 0,
    "scope": "Bounded family/objectives only; no global impossibility claim.",
    "checks": [
        "source hashes",
        "diagnostic sidecar",
        "full multiplicity vectors",
        "exact rational sums",
        "optimal sets",
        "equal life, hand size and winner",
        "visible exhaustion",
        "two-seat retention capacity",
    ],
    "records": summary,
}
out = ROOT / "docs/cardcade/PILOT_FITNESS_V2_REPLACEMENT_AUDIT.json"
payload = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
out.write_bytes(payload)
Path(str(out) + ".sha256").write_bytes(
    (hashlib.sha256(payload).hexdigest() + "  " + out.name + "\n").encode()
)
print(json.dumps({k: v for k, v in report.items() if k != "records"}))

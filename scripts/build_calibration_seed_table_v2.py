"""Prepare V2 seed data only: one entropy draw, deterministic expansion, strict validation."""

import argparse
import datetime
import hashlib
import itertools
import json
import os
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "96fc43ec3203938eb385618f6187f8496b93ecd3"
BLOCKS = 2048
PAIR_COUNT = 45
SEED_COUNT = BLOCKS * PAIR_COUNT
ROW_COUNT = SEED_COUNT * 2
PREFIX = "CALIBRATION_SEED_TABLE_V2"
TABLE = PREFIX + ".json"
ENTROPY = PREFIX + "_ENTROPY.bin"
START = PREFIX + "_GENERATION_START.json"
RECEIPT = PREFIX + "_GENERATION.json"
VALIDATION = PREFIX + "_VALIDATION.json"
STOP = PREFIX + "_GENERATION_STOP.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def write_new(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != raw:
        raise ValueError(f"write verification failed: {path}")


def sidecar(path):
    write_new(Path(str(path) + ".sha256"), (sha(path.read_bytes()) + "\n").encode())


def save_json(path, value):
    write_new(path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())
    sidecar(path)


def load_pairs():
    protocol = json.loads((ROOT / "docs/cardcade/CALIBRATION_PROTOCOL_SPEC_V1.json").read_bytes())
    design = protocol["design"]
    if (design["blocks"], design["pair_count"], design["distinct_games"]) != (
        BLOCKS,
        PAIR_COUNT,
        ROW_COUNT,
    ):
        raise ValueError("accepted design dimensions mismatch")
    pairs = [tuple(pair["decks"]) for pair in design["pairs"]]
    roster = sorted({deck for pair in pairs for deck in pair})
    if len(roster) != 10 or pairs != list(itertools.combinations(roster, 2)):
        raise ValueError("accepted pair identities/order mismatch")
    if [pair["pair_index"] for pair in design["pairs"]] != list(range(PAIR_COUNT)):
        raise ValueError("accepted pair indices mismatch")
    return pairs


def draw_entropy(path, progress, source=os.urandom):
    """With replacement: never reject a repeated value or draw an alternative."""
    with path.open("xb") as stream:
        for _ in range(SEED_COUNT):
            progress["draw_calls_attempted"] += 1
            value = source(32)
            if not isinstance(value, bytes) or len(value) != 32:
                raise ValueError("entropy source did not return exactly 32 bytes")
            if stream.write(value) != 32:
                raise OSError("incomplete entropy write")
            progress["draws_recorded"] += 1
            if progress["draws_recorded"] % PAIR_COUNT == 0:
                stream.flush()
                os.fsync(stream.fileno())
        stream.flush()
        os.fsync(stream.fileno())
    sidecar(path)


def derive_table(entropy, output, pairs):
    """Expand recorded bytes without an entropy API, engine, Pilot, or gameplay RNG."""
    if len(entropy) != SEED_COUNT * 32:
        raise ValueError("entropy byte count mismatch")
    metadata = {
        "scheme": "calibration-seed-table-v2",
        "protocol_identity": PROTOCOL,
        "execution_authorized": False,
        "blocks": BLOCKS,
        "pairs": PAIR_COUNT,
        "orientations": ["canonical", "reversed"],
        "entropy_sha256": sha(entropy),
        "seed_count": SEED_COUNT,
        "row_count": ROW_COUNT,
    }
    with output.open("xb") as stream:
        stream.write(canonical(metadata)[:-1] + b',"rows":[\n')
        for index in range(SEED_COUNT):
            block, pair_index = divmod(index, PAIR_COUNT)
            seed = int.from_bytes(entropy[index * 32 : (index + 1) * 32], "big", signed=False)
            for orientation, decks in (
                ("canonical", pairs[pair_index]),
                ("reversed", pairs[pair_index][::-1]),
            ):
                row = {
                    "block": block,
                    "pair_index": pair_index,
                    "orientation": orientation,
                    "seed": seed,
                    "decks": list(decks),
                }
                last = index == SEED_COUNT - 1 and orientation == "reversed"
                stream.write(canonical(row) + (b"\n" if last else b",\n"))
        stream.write(b"]}\n")
        stream.flush()
        os.fsync(stream.fileno())
    sidecar(output)


def validate_table(table, entropy, pairs):
    """Independently check every row and paired orientation against retained entropy."""
    if len(entropy) != SEED_COUNT * 32:
        raise ValueError("entropy byte count mismatch")
    data = json.loads(table)
    expected_metadata = {
        "scheme": "calibration-seed-table-v2",
        "protocol_identity": PROTOCOL,
        "execution_authorized": False,
        "blocks": BLOCKS,
        "pairs": PAIR_COUNT,
        "orientations": ["canonical", "reversed"],
        "entropy_sha256": sha(entropy),
        "seed_count": SEED_COUNT,
        "row_count": ROW_COUNT,
    }
    if {k: v for k, v in data.items() if k != "rows"} != expected_metadata:
        raise ValueError("table metadata mismatch")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != ROW_COUNT:
        raise ValueError("incomplete or extra schedule rows")
    seen = set()
    seeds = set()
    for block in range(BLOCKS):
        for pair_index, decks in enumerate(pairs):
            pair_offset = block * PAIR_COUNT + pair_index
            first, second = rows[pair_offset * 2 : pair_offset * 2 + 2]
            expected_seed = int.from_bytes(
                entropy[pair_offset * 32 : (pair_offset + 1) * 32], "big"
            )
            for row, orientation, seats in (
                (first, "canonical", decks),
                (second, "reversed", decks[::-1]),
            ):
                expected = {
                    "block": block,
                    "pair_index": pair_index,
                    "orientation": orientation,
                    "seed": expected_seed,
                    "decks": list(seats),
                }
                if any(type(row.get(key)) is not int for key in ("block", "pair_index", "seed")):
                    raise ValueError(f"non-integer member identity/seed at {block}/{pair_index}")
                if row != expected:
                    raise ValueError(f"schedule row mismatch at {block}/{pair_index}/{orientation}")
                member_id = f"b{block:04d}-p{pair_index:02d}-{orientation}"
                if member_id in seen:
                    raise ValueError("duplicate member")
                seen.add(member_id)
            if first["seed"] != second["seed"] or first["decks"] != second["decks"][::-1]:
                raise ValueError("orientation pair mismatch")
            seeds.add(expected_seed)
    return {
        "status": "SEED_TABLE_V2_VALIDATION_PASS",
        "execution_authorized": False,
        "blocks": BLOCKS,
        "unordered_pairs_per_block": PAIR_COUNT,
        "orientation_pairs_checked": SEED_COUNT,
        "same_seed_pairs": SEED_COUNT,
        "opposite_seat_order_pairs": SEED_COUNT,
        "rows": len(rows),
        "unique_members": len(seen),
        "missing_members": 0,
        "duplicate_members": 0,
        "pair_identity_mismatches": 0,
        "seed_derivation_mismatches": 0,
        "schedule_order_mismatches": 0,
        "uint256_seeds_checked": SEED_COUNT,
        "repeated_seed_values_retained": SEED_COUNT - len(seeds),
        "table_sha256": sha(table),
        "entropy_sha256": sha(entropy),
        "entropy_bytes": len(entropy),
        "prospective_executions": ROW_COUNT * 2,
        "game_executions": 0,
        "adaptive_or_replacement_seeds": False,
    }


def generate(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    names = (TABLE, ENTROPY, START, RECEIPT, VALIDATION, STOP)
    if any((output_dir / (name + suffix)).exists() for name in names for suffix in ("", ".sha256")):
        raise ValueError("V2 attempt already exists; overwrite/regeneration prohibited")
    pairs = load_pairs()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    old = ROOT / "docs/cardcade/CALIBRATION_SEED_TABLE_V1.json"
    v1_sha = sha(old.read_bytes())
    if v1_sha != "C8D3EFBB99B2891808985D66E7EA59EF879D546B7D378F05FA17E63793F9D968":
        raise ValueError("historical V1 input drift")
    start = {
        "scheme": "calibration-seed-table-v2-generation",
        "execution_authorized": False,
        "started_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "source_main_commit": head,
        "generator_path": "scripts/build_calibration_seed_table_v2.py",
        "generator_git_lf_sha256": sha(Path(__file__).read_bytes().replace(b"\r\n", b"\n")),
        "protocol_identity": PROTOCOL,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "entropy_api": "os.urandom(32)",
        "draw_order": "block 0..2047, pair_index 0..44; one independent 32-byte draw per pair",
        "integer_conversion": "unsigned big-endian 256-bit",
        "sampling": "with replacement",
        "entropy_file_layout": "92160 consecutive 32-byte draws; offset=32*(45*block+pair_index)",
        "expansion": "canonical decks[A,B], then reversed decks[B,A], both using the same seed",
        "v1_sha256_preserved": v1_sha,
        "previous_outcome_exposure": (
            "V1 first-member diagnostic outcome already inspected; "
            "V2 uses no outcomes or V1 seed selection"
        ),
        "candidate_tables_selected_between": False,
        "adaptive_or_replacement_seeds": False,
        "game_executions": 0,
    }
    save_json(output_dir / START, start)
    progress = {"draw_calls_attempted": 0, "draws_recorded": 0}
    try:
        draw_entropy(output_dir / ENTROPY, progress)
        entropy = (output_dir / ENTROPY).read_bytes()
        derive_table(entropy, output_dir / TABLE, pairs)
        report = validate_table((output_dir / TABLE).read_bytes(), entropy, pairs)
        if sha(old.read_bytes()) != v1_sha:
            raise ValueError("historical V1 changed during generation")
        save_json(output_dir / VALIDATION, report)
        save_json(
            output_dir / RECEIPT,
            {
                **start,
                **progress,
                "status": "GENERATED_PENDING_HQ_REVIEW",
                "completed_utc": datetime.datetime.now(datetime.UTC).isoformat(),
                "table_sha256": report["table_sha256"],
                "entropy_sha256": report["entropy_sha256"],
                "generation_attempts": 1,
                "validation": report,
            },
        )
        return report
    except BaseException as exc:
        save_json(
            output_dir / STOP,
            {
                **start,
                **progress,
                "status": "GENERATION_FAIL_CLOSED_STOP",
                "error": str(exc),
                "partial_artifacts_preserved": True,
            },
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    draw = sub.add_parser("generate")
    draw.add_argument("--output-dir", type=Path, required=True)
    derive = sub.add_parser("derive")
    derive.add_argument("--entropy-file", type=Path, required=True)
    derive.add_argument("--output", type=Path, required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--entropy-file", type=Path, required=True)
    validate.add_argument("--table", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "generate":
        report = generate(args.output_dir)
    else:
        entropy = args.entropy_file.read_bytes()
        pairs = load_pairs()
        if args.command == "derive":
            derive_table(entropy, args.output, pairs)
            table = args.output
        else:
            table = args.table
        report = validate_table(table.read_bytes(), entropy, pairs)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

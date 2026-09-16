"""Seed-data tests use synthetic entropy or replay retained bytes, never fresh draws."""

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "seed_table_v2", ROOT / "scripts/build_calibration_seed_table_v2.py"
)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


@pytest.fixture(scope="module")
def synthetic_table(tmp_path_factory):
    entropy = b"".join(i.to_bytes(32, "big") for i in range(builder.SEED_COUNT - 1)) + b"\xff" * 32
    path = tmp_path_factory.mktemp("synthetic-seed-v2") / "table.json"
    pairs = builder.load_pairs()
    builder.derive_table(entropy, path, pairs)
    return entropy, path.read_bytes(), pairs


def test_full_synthetic_design_and_uint256_boundaries(synthetic_table):
    entropy, table, pairs = synthetic_table
    report = builder.validate_table(table, entropy, pairs)
    assert report["orientation_pairs_checked"] == 92160
    assert report["rows"] == report["unique_members"] == 184320
    assert report["same_seed_pairs"] == report["opposite_seat_order_pairs"] == 92160
    rows = json.loads(table)["rows"]
    assert rows[0]["seed"] == rows[1]["seed"] == 0
    assert rows[-1]["seed"] == rows[-2]["seed"] == (1 << 256) - 1


@pytest.mark.parametrize(
    "defect",
    [
        "same_seats",
        "different_seed",
        "missing",
        "duplicate",
        "out_of_order",
        "wrong_pair",
        "wrong_orientation",
        "bool_seed",
        "negative_seed",
        "oversized_seed",
    ],
)
def test_rejects_material_schedule_defects(synthetic_table, defect):
    entropy, table, pairs = synthetic_table
    data = json.loads(table)
    rows = data["rows"]
    if defect == "same_seats":
        rows[1]["decks"] = rows[0]["decks"]
    elif defect == "different_seed":
        rows[1]["seed"] = 1
    elif defect == "missing":
        rows.pop()
    elif defect == "duplicate":
        rows[-1] = rows[0]
    elif defect == "out_of_order":
        rows[0], rows[90] = rows[90], rows[0]
    elif defect == "wrong_pair":
        rows[0]["pair_index"] = 44
    elif defect == "wrong_orientation":
        rows[0]["orientation"] = "reversed"
    elif defect == "bool_seed":
        rows[0]["seed"] = False
    elif defect == "negative_seed":
        rows[0]["seed"] = -1
    else:
        rows[0]["seed"] = 1 << 256
    with pytest.raises(ValueError):
        builder.validate_table(json.dumps(data).encode(), entropy, pairs)


def test_entropy_with_replacement_never_rejects_repeated_values(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "SEED_COUNT", 3)
    calls = []

    def source(size):
        calls.append(size)
        return bytes(32)

    progress = {"draw_calls_attempted": 0, "draws_recorded": 0}
    path = tmp_path / "entropy.bin"
    builder.draw_entropy(path, progress, source)
    assert calls == [32, 32, 32]
    assert path.read_bytes() == bytes(96)
    assert progress == {"draw_calls_attempted": 3, "draws_recorded": 3}


def test_entropy_failure_preserves_partial_draws_without_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "SEED_COUNT", 3)
    calls = []

    def source(size):
        calls.append(size)
        if len(calls) == 2:
            raise OSError("synthetic entropy failure")
        return b"x" * size

    progress = {"draw_calls_attempted": 0, "draws_recorded": 0}
    path = tmp_path / "partial.bin"
    with pytest.raises(OSError, match="synthetic entropy failure"):
        builder.draw_entropy(path, progress, source)
    assert calls == [32, 32]
    assert path.read_bytes() == b"x" * 32
    assert progress == {"draw_calls_attempted": 2, "draws_recorded": 1}


def test_generation_refuses_existing_attempt_before_entropy(tmp_path, monkeypatch):
    (tmp_path / builder.START).write_bytes(b"preserved")

    def forbidden(*args):
        pytest.fail("must not draw another candidate")

    monkeypatch.setattr(builder, "draw_entropy", forbidden)
    with pytest.raises(ValueError, match="overwrite/regeneration prohibited"):
        builder.generate(tmp_path)
    assert (tmp_path / builder.START).read_bytes() == b"preserved"


def test_derivation_rejects_truncation_and_overwrite(synthetic_table, tmp_path):
    entropy, table, pairs = synthetic_table
    with pytest.raises(ValueError, match="entropy byte count"):
        builder.derive_table(entropy[:-1], tmp_path / "short.json", pairs)
    preserved = tmp_path / "existing.json"
    preserved.write_bytes(table)
    with pytest.raises(FileExistsError):
        builder.derive_table(entropy, preserved, pairs)
    assert preserved.read_bytes() == table


def test_sealed_v2_reconstructs_exactly_without_randomness(tmp_path, monkeypatch):
    from tmnt_design_studio.calibration_runner import load_members

    folder = ROOT / "docs/cardcade"
    table_path = folder / builder.TABLE
    entropy = (folder / builder.ENTROPY).read_bytes()
    table = subprocess.check_output(
        ["git", "show", f"HEAD:{table_path.relative_to(ROOT).as_posix()}"]
    )

    def forbidden(*args):
        pytest.fail("reconstruction must not draw entropy")

    monkeypatch.setattr(builder.os, "urandom", forbidden)
    monkeypatch.setattr(builder, "draw_entropy", forbidden)
    reconstructed = tmp_path / "reconstructed.json"
    builder.derive_table(entropy, reconstructed, builder.load_pairs())
    assert reconstructed.read_bytes() == table
    report = builder.validate_table(table, entropy, builder.load_pairs())
    assert report == json.loads((folder / builder.VALIDATION).read_bytes())
    committed_table = tmp_path / builder.TABLE
    committed_table.write_bytes(table)
    members = load_members(table_path, strict=True, expected_sha256=report["table_sha256"])
    assert len(members) == 184320
    for first, second in zip(members[::2], members[1::2], strict=True):
        assert first.seed == second.seed
        assert first.decks == second.decks[::-1]
        assert first.block == second.block and first.pair_index == second.pair_index
    for name in (
        builder.TABLE,
        builder.ENTROPY,
        builder.START,
        builder.RECEIPT,
        builder.VALIDATION,
    ):
        raw = (
            subprocess.check_output(
                ["git", "show", f"HEAD:{(folder / name).relative_to(ROOT).as_posix()}"]
            )
            if name.endswith(".json")
            else (folder / name).read_bytes()
        )
        assert builder.sha(raw) == (folder / (name + ".sha256")).read_text().strip()
    receipt = json.loads((folder / builder.RECEIPT).read_bytes())
    assert receipt["draw_calls_attempted"] == receipt["draws_recorded"] == 92160
    assert receipt["generation_attempts"] == 1
    assert receipt["execution_authorized"] is False
    assert receipt["generator_git_lf_sha256"] == builder.sha(
        (ROOT / "scripts/build_calibration_seed_table_v2.py").read_bytes().replace(b"\r\n", b"\n")
    )
    assert hashlib.sha256(
        (folder / "CALIBRATION_SEED_TABLE_V1.json").read_bytes()
    ).hexdigest().upper() == ("C8D3EFBB99B2891808985D66E7EA59EF879D546B7D378F05FA17E63793F9D968")

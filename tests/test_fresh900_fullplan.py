"""Run the original full-plan predicate unchanged with a fresh fixture seal."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tmnt_design_studio import fresh900_identity as identity

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "tests/evidence/pr369_test_fullplan_boundary.py.txt"


def trace_refusal(frame, event, arg):
    """Expose refusals swallowed by the preserved predicate, without changing it."""
    if (
        event == "exception"
        and isinstance(arg[1], identity.FreshRefused)
        and frame.f_code.co_name == "require"
    ):
        print("ORIGINAL_PREFLIGHT_REFUSAL " + str(arg[1]), file=sys.stderr, flush=True)
    return trace_refusal


def linux_resources() -> dict[str, int]:
    """Actual Linux counters for the public synthetic measurement seam only.

    Linux commit accounting is not Windows commit accounting. This provider does
    not qualify Linux for production; the production default must still refuse it.
    No resource gate or disk check is replaced.
    """
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, raw = line.split(":", 1)
        parts = raw.split()
        if len(parts) == 2 and parts[1] == "kB":
            values[key] = int(parts[0]) * 1024
    return dict(
        physical=values["MemAvailable"],
        commit=min(
            values["CommitLimit"] - values["Committed_AS"],
            values["MemAvailable"] + values["SwapFree"],
        ),
    )


def run_original(layout: Path) -> None:
    layout.mkdir()
    proof = layout / "proof/original.py"
    proof.parent.mkdir()
    proof.write_bytes(ORIGINAL.read_bytes())
    authority = layout / ".fresh900-readiness"
    authority.mkdir()
    # Execute imports BEFORE sealing them. Collection order must not determine
    # which real modules the fixture approves. The original source is unchanged.
    namespace = {"__file__": str(proof), "__name__": "original_fullplan_predicate"}
    exec(compile(ORIGINAL.read_bytes(), str(proof), "exec"), namespace)
    runner = namespace["runner"]
    if os.name != "nt":
        from functools import partial
        from types import SimpleNamespace

        import pytest

        # Prove the production default remains unsupported, then use ONLY the
        # existing explicit synthetic measurement seam. All identities, actual
        # disk checks and resource thresholds still run unchanged.
        with pytest.raises(identity.FreshRefused, match="Windows resource provider required"):
            runner.resources()
        namespace["runner"] = SimpleNamespace(
            run_synthetic=partial(runner.run_synthetic, measure=linux_resources)
        )
    # Warm up lazy imports and require actual resources before capturing a seal.
    # Windows uses the original default provider and call with no injected seam.
    measured = runner.check_resources(
        layout, runner.resources if os.name == "nt" else linux_resources
    )
    print("FULLPLAN_ACTUAL_RESOURCES " + json.dumps(measured), flush=True)
    files = {}
    for module in tuple(sys.modules.values()):
        origin = getattr(module, "__file__", None)
        if origin:
            path = Path(origin).absolute()
            if path.suffix == ".pyc":
                path = Path(importlib.util.source_from_cache(str(path)))
            files[str(path)] = identity.file_hash(path)
        cached = getattr(module, "__cached__", None)
        if cached and Path(cached).exists():
            files[str(Path(cached).absolute())] = identity.file_hash(Path(cached))
    for executable in (sys.executable, sys._base_executable):
        files[executable] = identity.file_hash(Path(executable))
    git = shutil.which("git") or "C:/Program Files/Git/cmd/git.exe"
    commit = subprocess.check_output(
        [git, "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    runtime = dict(
        version=sys.version,
        executable=sys.executable,
        base_executable=sys._base_executable,
        source=str(ROOT),
        source_commit=commit,
        git_executable=git,
        files=files,
    )
    (authority / "preflight-final-head.json").write_text(json.dumps({"runtime": runtime}))
    manifest = json.loads(
        (ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json").read_bytes()
    )
    schedule = []
    for index, opponent in enumerate(
        sorted(
            row["deck_key"] for row in manifest["decks"] if row["deck_key"] != "bebop_rocksteady"
        )
    ):
        for offset in range(100):
            seed = 1000000 + index * 100 + offset
            orientation = "candidate_first" if offset < 50 else "opponent_first"
            schedule.append(
                dict(
                    game_id=f"bad_guys_cronies_sandbox_0_2--{opponent}:{orientation}:{seed}",
                    pairing_id=f"bebop_rocksteady--{opponent}",
                    opponent=opponent,
                    orientation=orientation,
                    seed=seed,
                    seats=["bad_guys_cronies_sandbox_0_2", opponent]
                    if offset < 50
                    else [opponent, "bad_guys_cronies_sandbox_0_2"],
                )
            )
    (authority / "proposed-schedule.json").write_text(json.dumps(schedule))
    output = layout / "outputs"
    output.mkdir()
    namespace["test_conflicting_seed_refused_with_unmodified_full_plan"](output)
    failure = json.loads((output / "FRESH_900_full_plan_proof/failures/stop.json").read_bytes())
    assert failure["error"] == "conflicting result seed"
    assert failure["stage"] == "RESULT_VALIDATION"
    assert failure["last_observed_committed"] == 0
    assert failure["checkpoint_integrity_verified"] is True
    print("FULLPLAN_ORIGINAL_PREDICATE " + json.dumps(failure), flush=True)


def test_original_full_900_plan_predicate(tmp_path):
    if os.name == "nt":
        run_original(tmp_path / "layout")
    else:
        # Linux venv launchers are symlinks, which the Windows-target runtime
        # policy correctly rejects. Use the SAME underlying interpreter bytes
        # via their resolved path plus the locked test site-packages, not a skip
        # or a patched verifier. CI installs wheel payloads by copy, not hardlink.
        import pytest

        site = Path(pytest.__file__).resolve().parents[1]
        code = (
            "import sys; from pathlib import Path; "
            "sys.path[:0]=sys.argv[1:4]; "
            "from test_fresh900_fullplan import run_original, trace_refusal; "
            "sys.settrace(trace_refusal); run_original(Path(sys.argv[4]))"
        )
        child = subprocess.run(
            [
                str(Path(sys.executable).resolve()),
                "-P",
                "-s",
                "-B",
                "-c",
                code,
                str(ROOT / "src"),
                str(ROOT / "tests"),
                str(site),
                str(tmp_path / "layout"),
            ],
            env={**os.environ, "PYTHONHASHSEED": "0"},
            check=False,
            timeout=120,
            capture_output=True,
        )
        assert child.returncode == 0, child.stderr.decode(errors="replace")
        print(child.stdout.decode(errors="replace"), end="")


def test_fullplan_resource_checks_remain_active(tmp_path):
    import pytest

    from tmnt_design_studio import fresh900 as runner

    if os.name != "nt":
        with pytest.raises(identity.FreshRefused, match="Windows resource provider required"):
            runner.resources()
        sample = linux_resources()
        assert isinstance(sample["physical"], int) and isinstance(sample["commit"], int)
    # Deliberately insufficient synthetic samples prove that neither threshold
    # has been bypassed by using the public measurement seam.
    with pytest.raises(identity.FreshRefused, match="physical memory gate"):
        runner.check_resources(tmp_path, lambda: dict(physical=0, commit=runner.MEMORY_GATE))
    with pytest.raises(identity.FreshRefused, match="system commit gate"):
        runner.check_resources(tmp_path, lambda: dict(physical=runner.MEMORY_GATE, commit=0))

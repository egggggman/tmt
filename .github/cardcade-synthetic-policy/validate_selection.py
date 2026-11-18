"""Fail-closed guard for the trusted synthetic pytest selection."""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED_HASHES = {
    "tests/test_does_machines_level_three.py": (
        "98641172e4886383b28a2966acb8813fdd460672bc610c323d81114bba4fb44a"
    ),
    "tests/test_does_machines_level_two.py": (
        "32346c75bbe5fec9bba9076061b7f8352a765f2081fb57b691527e46675d3d51"
    ),
    "tests/test_stage002_runner.py": (
        "adbe57d0c8ef34926d810f310dd3903d1ddfe8cd6294abd8baf7f17542611dcc"
    ),
    "tests/test_cardcade_diagnostic_launcher_safety.py": (
        "087d836c5878b478763a14aae3da26a6d6b308941e8070503cf7f7257ea08c74"
    ),
}

NODE_LIST = Path(__file__).with_name("cardcade-safe-nodeids.txt")
APPROVED_SOURCES = Path(__file__).with_name("approved-source-shas.txt")
EXPECTED_NODE_LIST_HASH = "abea15e90eb6c7e413960d2b25b1945464a354b01efba15828da76f10a2637c1"
EXPECTED_COUNT = 34
FORBIDDEN_CALLS = {
    "run_game",
    "run_full_game",
    "run_complete_game",
    "simulate_game",
    "simulate_full_game",
    "run_smoke_game",
    "run_smoke_games",
    "run_batch",
    "run_batch_games",
    "run_calibration",
    "execute_stage",
    "plan",
    "run_diagnostic_game",
    "launch_game",
}
FORBIDDEN_CONFIGS = {
    "pyproject.toml",
    "uv.lock",
    "pytest.ini",
    ".pytest.ini",
    "pytest.toml",
    ".pytest.toml",
    "tox.ini",
    ".tox.ini",
    "setup.cfg",
    "setup.py",
}


def _called_names(function: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            names.add(target.attr)
    return names


def fail(message: str) -> None:
    raise SystemExit(f"SAFE TEST SELECTION REJECTED: {message}")


def _validate_changed_paths(source: Path, base_sha: str, selected_paths: set[str]) -> None:
    if len(base_sha) != 40 or any(char not in "0123456789abcdef" for char in base_sha):
        fail("trusted PR base is not a full lowercase commit SHA")
    result = subprocess.run(
        ["git", "-C", str(source), "diff", "--name-only", "--no-renames", f"{base_sha}...HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail("cannot compute source changes against the trusted PR base")

    changed_paths = set(result.stdout.splitlines())
    for path in changed_paths:
        name = Path(path).name.lower()
        if name in FORBIDDEN_CONFIGS or name in {"conftest.py", "sitecustomize.py", "usercustomize.py"}:
            fail(f"PR changes test/runtime configuration outside this policy: {path}")
        if path.startswith("tests/") and path not in selected_paths:
            fail(f"PR changes a test module outside the trusted selection: {path}")
        if name.startswith("requirements") and name.endswith(".txt"):
            fail(f"PR changes dependency configuration outside this policy: {path}")


def _validate_approved_source(source: Path, pr_number: str, head_sha: str) -> None:
    if not pr_number.isdecimal() or len(head_sha) != 40:
        fail("PR identity is malformed")
    if any(char not in "0123456789abcdef" for char in head_sha):
        fail("source head is not a full lowercase commit SHA")
    actual = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if actual.returncode != 0 or actual.stdout.strip() != head_sha:
        fail("checked-out source does not match the PR head SHA")

    rows = APPROVED_SOURCES.read_text(encoding="utf-8").splitlines()
    approved: set[tuple[str, str]] = set()
    for row in rows:
        fields = row.split()
        if len(fields) != 2 or not fields[0].isdecimal() or len(fields[1]) != 40:
            fail("approved-source policy is malformed")
        if any(char not in "0123456789abcdef" for char in fields[1]):
            fail("approved-source policy contains a malformed commit SHA")
        approved.add((fields[0], fields[1]))
    if len(approved) != len(rows) or (pr_number, head_sha) not in approved:
        fail("PR head SHA is not in the trusted source allowlist")


def main() -> None:
    if len(sys.argv) != 5:
        fail("usage: validate_selection.py SOURCE_CHECKOUT TRUSTED_BASE_SHA PR_NUMBER HEAD_SHA")
    source = Path(sys.argv[1]).resolve()
    if not source.is_dir():
        fail(f"source checkout does not exist: {source}")
    _validate_approved_source(source, sys.argv[3], sys.argv[4])
    selected_paths = set(EXPECTED_HASHES)
    _validate_changed_paths(source, sys.argv[2], selected_paths)

    node_bytes = NODE_LIST.read_bytes()
    if hashlib.sha256(node_bytes).hexdigest() != EXPECTED_NODE_LIST_HASH:
        fail("reviewed node-ID manifest fingerprint changed")
    nodes = node_bytes.decode("utf-8").splitlines()
    if len(nodes) != EXPECTED_COUNT or len(set(nodes)) != EXPECTED_COUNT:
        fail(f"expected {EXPECTED_COUNT} unique node IDs, found {len(nodes)}")

    selected_by_file: dict[str, set[str]] = {}
    for node in nodes:
        if "::" not in node or "*" in node or not node.startswith("tests/"):
            fail(f"not an explicit test node ID: {node}")
        path, name = node.split("::", maxsplit=1)
        if not name.startswith("test_"):
            fail(f"not a test function node ID: {node}")
        selected_by_file.setdefault(path, set()).add(name.split("[", maxsplit=1)[0])

    if set(selected_by_file) != set(EXPECTED_HASHES):
        fail("node list refers to an unreviewed test-file set")

    for relative_path, expected_hash in EXPECTED_HASHES.items():
        test_file = source / relative_path
        if not test_file.is_file():
            fail(f"selected test module is missing: {relative_path}")
        if hashlib.sha256(test_file.read_bytes()).hexdigest() != expected_hash:
            fail(f"reviewed source fingerprint changed: {relative_path}")

        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=relative_path)
        definitions = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in selected_by_file[relative_path]:
            function = definitions.get(name)
            if function is None or not name.startswith("test_"):
                fail(f"selected test function is missing: {relative_path}::{name}")

            pending = [function]
            visited: set[str] = set()
            while pending:
                current = pending.pop()
                if current.name in visited:
                    continue
                visited.add(current.name)
                calls = _called_names(current)
                unsafe = sorted(calls & FORBIDDEN_CALLS)
                if unsafe:
                    fail(
                        f"selected test path invokes a complete-game API: "
                        f"{relative_path}::{name} via {current.name}: {unsafe}"
                    )

                # The source-guard negative test may enter run_once only with
                # its fail-fast executor, which proves dispatch is blocked.
                for node in ast.walk(current):
                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "run_once"
                    ):
                        executor = next(
                            (kw.value for kw in node.keywords if kw.arg == "executor"),
                            None,
                        )
                        if not isinstance(executor, ast.Name) or executor.id != "forbidden_executor":
                            fail(
                                f"selected test calls run_once without a fail-fast executor: "
                                f"{relative_path}::{name}"
                            )

                for called_name in calls:
                    helper = definitions.get(called_name)
                    if helper is not None and helper.name not in visited:
                        pending.append(helper)

    print(
        f"SAFE TEST SELECTION VERIFIED: {len(nodes)} explicit node IDs; "
        f"{len(EXPECTED_HASHES)} reviewed module hashes match."
    )


if __name__ == "__main__":
    main()

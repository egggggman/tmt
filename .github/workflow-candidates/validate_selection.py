"""Fail-closed guard for the reviewed synthetic-only pytest selection."""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

EXPECTED_HASHES = {
    "tests/test_does_machines_level_three.py": (
        "0dbcfd5bc22b3664eba883d7c04707ab0bf9d526c3f0c231bb78d1fcaec86262"
    ),
    "tests/test_does_machines_level_two.py": (
        "32346c75bbe5fec9bba9076061b7f8352a765f2081fb57b691527e46675d3d51"
    ),
    "tests/test_stage002_runner.py": (
        "a323a8c50ae01c78940d1018a84fee06047fb6faab64d2b352bcd926a9bd1b67"
    ),
}

NODE_LIST = Path(__file__).with_name("cardcade-safe-nodeids.txt")
EXPECTED_NODE_LIST_HASH = "5b635cb8d9d00a6635158291aef635b71aa5edaeb7b2bea825699e368286a11b"
EXPECTED_COUNT = 28
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
}


def fail(message: str) -> None:
    raise SystemExit(f"SAFE TEST SELECTION REJECTED: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_selection.py SOURCE_CHECKOUT")
    source = Path(sys.argv[1]).resolve()
    if not source.is_dir():
        fail(f"source checkout does not exist: {source}")

    node_bytes = NODE_LIST.read_bytes()
    actual_node_hash = hashlib.sha256(node_bytes).hexdigest()
    if actual_node_hash != EXPECTED_NODE_LIST_HASH:
        fail("reviewed node-ID manifest fingerprint changed")
    nodes = node_bytes.decode("utf-8").splitlines()
    if len(nodes) != EXPECTED_COUNT or len(set(nodes)) != EXPECTED_COUNT:
        fail(f"expected {EXPECTED_COUNT} unique node IDs, found {len(nodes)}")

    selected_by_file: dict[str, set[str]] = {}
    for node in nodes:
        if "::" not in node or "*" in node or node.startswith("tests/") is False:
            fail(f"not an explicit test node ID: {node}")
        path, name = node.split("::", maxsplit=1)
        if not name.startswith("test_"):
            fail(f"not a test function node ID: {node}")
        function_name = name.split("[", maxsplit=1)[0]
        selected_by_file.setdefault(path, set()).add(function_name)

    if set(selected_by_file) != set(EXPECTED_HASHES):
        fail("node list refers to an unreviewed test-file set")

    for relative_path, expected_hash in EXPECTED_HASHES.items():
        test_file = source / relative_path
        if not test_file.is_file():
            fail(f"selected test module is missing: {relative_path}")
        actual_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            fail(f"reviewed source fingerprint changed: {relative_path}")

        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=relative_path)
        definitions = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        }
        for name in selected_by_file[relative_path]:
            function = definitions.get(name)
            if function is None:
                fail(f"selected test function is missing: {relative_path}::{name}")
            calls = {
                call.func.id
                for call in ast.walk(function)
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            }
            unsafe = sorted(calls & FORBIDDEN_CALLS)
            if unsafe:
                fail(
                    f"selected test invokes a complete-game API: {relative_path}::{name}: {unsafe}"
                )

    print(
        f"SAFE TEST SELECTION VERIFIED: {len(nodes)} explicit node IDs; "
        f"{len(EXPECTED_HASHES)} reviewed test-module hashes match."
    )


if __name__ == "__main__":
    main()

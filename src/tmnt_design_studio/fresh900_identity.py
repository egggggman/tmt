"""Prospective file/import identity for Fresh 900; no historical equivalence claim."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path


class FreshRefused(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise FreshRefused(reason)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def encoded(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest(value: object) -> str:
    return hashlib.sha256(encoded(value)).hexdigest()


def plain(path: Path) -> Path:
    """Reject links/reparse points at every existing component, including hardlinks."""
    path = Path(os.path.abspath(path))
    for part in (*reversed(path.parents), path):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode), "symlink forbidden")
        require(not getattr(info, "st_file_attributes", 0) & 0x400, "reparse point forbidden")
        if stat.S_ISREG(info.st_mode):
            require(info.st_nlink == 1, "hardlink forbidden")
    return path


def disjoint(left: Path, right: Path) -> bool:
    return not (left.is_relative_to(right) or right.is_relative_to(left))


def verify_inventory(inventory: dict[str, str]) -> None:
    require(bool(inventory), "empty runtime inventory")
    for name, expected in inventory.items():
        require(file_hash(plain(Path(name))) == expected, f"payload mismatch: {name}")


def runtime_inventory(source: Path, environment: Path, base: Path) -> dict[str, str]:
    """Offline seal input, not an approval issuer. HQ must independently pin its digest."""
    result = {}
    for root in (source / "src", source / "tools", environment, base):
        require(root.is_dir(), "inventory root missing")
        for path in sorted(root.rglob("*")):
            if path.is_file():
                result[str(plain(path))] = file_hash(path)
    return result


def verify_locked_wheels(lock: Path, wheelhouse: Path, environment: Path) -> dict:
    """Verify installed payloads against locked wheel bytes, without installation."""
    import importlib.metadata
    import tomllib
    import zipfile

    require(os.name == "nt", "Windows wheel layout required")
    require(file_hash(lock) == FROZEN_INPUTS["uv.lock"], "unapproved dependency lock")
    packages = [
        p for p in tomllib.loads(lock.read_text(encoding="utf-8"))["package"] if p.get("wheels")
    ]
    site = plain(environment / "Lib/site-packages")
    installed = {
        d.metadata["Name"].lower().replace("_", "-"): d.version
        for d in importlib.metadata.distributions(path=[str(site)])
    }
    require(
        installed == {p["name"]: p["version"] for p in packages},
        "installed dependency inventory differs from lock",
    )
    report = []
    for package in packages:
        candidates = [
            p
            for p in wheelhouse.glob("*.whl")
            if p.name.split("-")[0].replace("_", "-") == package["name"]
        ]
        require(len(candidates) == 1, "one authenticated wheel per package required")
        wheel = plain(candidates[0])
        wheel_hash = file_hash(wheel)
        require(
            any(w["hash"] == "sha256:" + wheel_hash for w in package["wheels"]),
            "wheel is not authenticated by frozen lock",
        )
        payloads = 0
        with zipfile.ZipFile(wheel) as archive:
            for entry in archive.infolist():
                if entry.is_dir() or entry.filename.endswith(".dist-info/RECORD"):
                    continue
                relative = Path(entry.filename)
                require(
                    not relative.is_absolute() and ".." not in relative.parts, "unsafe wheel member"
                )
                parts = relative.parts
                if parts[0].endswith(".data"):
                    require(parts[1] == "scripts", "unreviewed wheel data layout")
                    target = environment / "Scripts" / Path(*parts[2:])
                else:
                    target = site / relative
                require(
                    file_hash(plain(target)) == hashlib.sha256(archive.read(entry)).hexdigest(),
                    f"installed wheel payload substitution: {target}",
                )
                payloads += 1
        report.append(
            dict(
                name=package["name"],
                version=package["version"],
                wheel_sha256=wheel_hash,
                payloads=payloads,
            )
        )
    return {"packages": report, "payloads": sum(p["payloads"] for p in report)}


def verify_runtime(runtime: dict) -> None:
    require(sys.version == runtime["version"], "interpreter version mismatch")
    require(sys.executable == runtime["executable"], "interpreter path mismatch")
    require(sys._base_executable == runtime["base_executable"], "base interpreter mismatch")
    require(sys.maxsize > 2**32, "64-bit interpreter required")
    require(os.environ.get("PYTHONHASHSEED") == "0", "declared hash seed required")
    require(
        not sys.flags.ignore_environment and sys.flags.hash_randomization == 0,
        "hash seed is inactive under startup flags",
    )
    require(sys.flags.no_user_site and sys.dont_write_bytecode, "unsafe startup flags")
    inventory = runtime["files"]
    require(runtime["executable"] in inventory, "unsealed interpreter")
    require(runtime["base_executable"] in inventory, "unsealed base interpreter")
    verify_inventory(inventory)
    source = plain(Path(runtime["source"]))
    commit = subprocess.check_output(
        [
            runtime["git_executable"],
            "-c",
            f"safe.directory={source.as_posix()}",
            "-C",
            str(source),
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()
    require(commit == runtime["source_commit"], "source commit differs")
    # Any file-backed loaded runtime module must belong to the approved inventory.
    # Diagnostic entrypoints/pytest are explicitly sealed separately by the issuer.
    for name, module in tuple(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        if not origin:
            continue
        path = Path(origin).absolute()
        if path.suffix == ".pyc":
            path = Path(__import__("importlib.util").util.source_from_cache(str(path)))
        loader_origin = getattr(getattr(module, "__spec__", None), "origin", None)
        if loader_origin and loader_origin not in ("built-in", "frozen"):
            other = Path(loader_origin).absolute()
            if other.suffix == ".pyc":
                other = Path(__import__("importlib.util").util.source_from_cache(str(other)))
            require(other == path, f"module loader mismatch: {name}")
        require(str(path) in inventory, f"unapproved loaded module: {name}")
        require(file_hash(plain(path)) == inventory[str(path)], f"import mismatch: {name}")
        cached = getattr(module, "__cached__", None)
        if cached and Path(cached).exists():
            cache = plain(Path(cached))
            require(str(cache) in inventory, f"unsealed import bytecode: {name}")
            require(file_hash(cache) == inventory[str(cache)], f"bytecode mismatch: {name}")
        if name == "tmnt_design_studio" or name.startswith("tmnt_design_studio."):
            require(path.is_relative_to(source / "src"), "project import outside approved source")


FROZEN_INPUTS = {
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json": (
        "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402"
    ),
    "decks/michelangelo/PROTOTYPE_0.1.txt": (
        "a35dfd61a87ec5377d7eda930afc22449d86bb2385b6d5e59d40e23211fe514f"
    ),
    "decks/splinter/PROTOTYPE_0.1.txt": (
        "a6c61786654f6d37c7b7ee779fdcb4252ee77d9d43a6e0160154831c204d8e42"
    ),
    "docs/design-studio/challengers/BAD_GUYS_CRONIES_SANDBOX_0_2_CANDIDATE.md": (
        "cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4"
    ),
    "docs/objective-balance-lab/baselines/APRIL_ONEIL_OBL_BASELINE_003.txt": (
        "ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7"
    ),
    "docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt": (
        "aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed"
    ),
    "docs/objective-balance-lab/baselines/KRANG_OBL_BASELINE_004.txt": (
        "2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1"
    ),
    "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json": (
        "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"
    ),
    "docs/objective-balance-lab/baselines/OBL_BASELINE_005_PROVENANCE_OVERLAY_001.json": (
        "cd555acc2719d09626871db3d7740688c030c58bab2352aea1663e42f0496ba9"
    ),
    "docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt": (
        "e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f"
    ),
    "docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt": (
        "1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1"
    ),
    "docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt": (
        "9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170"
    ),
    "docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt": (
        "d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6"
    ),
    "docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt": (
        "4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960"
    ),
    "pyproject.toml": ("0ed2a4de45ee37bef90732fcefc3155bef4faaf924339899721141b72c64d562"),
    "uv.lock": ("0c9863fb82c65e8c457b6903b13ab978e1012dc9252e9cca3e95807ef3ded11a"),
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json": (
        "ddbf57645bd016d16659424f2196cd816edfc7a187c4b653a9e6e8839b3e9a6d"
    ),
}


def verify_plan(plan: dict) -> None:
    require(plan.get("protocol") == "fresh900-plan-v1", "unsupported plan")
    require(plan.get("games") == 900, "exactly 900 games required")
    verify_runtime(plan["runtime"])
    require(
        plan["inputs"]
        == {
            str(Path(plan["runtime"]["source"]) / name): value
            for name, value in FROZEN_INPUTS.items()
        },
        "frozen input manifest differs",
    )
    verify_inventory(plan["inputs"])
    schedule = plan["schedule"]
    require(len(schedule) == 900, "schedule count mismatch")
    # Compare full rows against the frozen seed/seat/ID construction, not just a
    # digest self-declared by an untrusted checkpoint.
    opponents = [
        "april_oneil",
        "casey_jones",
        "donatello",
        "krang",
        "leonardo",
        "michelangelo",
        "raphael",
        "shredder",
        "splinter",
    ]
    expected = []
    for index, opponent in enumerate(opponents):
        for offset in range(100):
            seed = 1_000_000 + index * 100 + offset
            orientation = "candidate_first" if offset < 50 else "opponent_first"
            expected.append(
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
    require(schedule == expected, "frozen schedule differs")
    from tmnt_design_studio.calibration_integrity import canonical_digest

    require(
        canonical_digest(schedule)
        == "4da440bc83b9790876d1020ae83cf2147c4e60a67feba8bb7181421e196b303e",
        "schedule identity differs",
    )

"""Disposable test issuer only. Production must supply independently approved pins."""

import os
import sys
import sysconfig
from functools import cache, lru_cache
from pathlib import Path

from tmnt_design_studio.resume_authorization import RuntimeIdentity, file_hash
from tmnt_design_studio.resume_paths import TelemetryGrant, directory_identity


@cache
def cached_hash(path, size, modified):
    return file_hash(Path(path))


def pin(path):
    path = path.resolve()
    info = path.stat()
    return cached_hash(str(path), info.st_size, info.st_mtime_ns)


@lru_cache(maxsize=1)
def interpreter_inventory():
    files = {}
    root = Path(sysconfig.get_path("stdlib"))
    for directory, children, names in os.walk(root):
        children[:] = [n for n in children if n not in ("site-packages", "__pycache__")]
        for name in names:
            if name.endswith((".py", ".so", ".pyd", ".dll")):
                path = (Path(directory) / name).resolve()
                files[str(path)] = pin(path)
    base = Path(sys.base_prefix)
    for path in [
        Path(sys._base_executable),
        *base.glob("*.dll"),
        *base.glob("DLLs/*.pyd"),
        *base.glob("DLLs/*.dll"),
    ]:
        files[str(path.resolve())] = pin(path)
    return files


def dependency_inventory():
    files, origins, packages = {}, {}, set()
    for name, module in tuple(sys.modules.items()):
        top = name.split(".")[0]
        if (
            top in sys.stdlib_module_names
            or top == "tmnt_design_studio"
            or name in ("__main__", "__mp_main__")
        ):
            continue
        origin = getattr(module, "__file__", None)
        if origin and Path(origin).is_file():
            path = Path(origin).resolve()
            origins[name] = str(path)
            files[str(path)] = pin(path)
            top_origin = getattr(sys.modules.get(top), "__file__", None)
            if top_origin and Path(top_origin).name == "__init__.py":
                packages.add((top, Path(top_origin).resolve().parent))
        else:
            paths = getattr(module, "__path__", None)
            origins[name] = "namespace:" + str(sorted(str(Path(p).resolve()) for p in paths or []))
    for top, directory in packages:
        for path in directory.rglob("*.py"):
            relative = path.relative_to(directory).with_suffix("").parts
            parts = relative[:-1] if relative[-1] == "__init__" else relative
            origins[".".join((top, *parts))] = str(path.resolve())
            files[str(path.resolve())] = pin(path)
    return files, origins


def current_identity(root):
    source = {p.relative_to(root).as_posix(): pin(p) for p in (root / "src").rglob("*.py")}
    for name in (
        "tools/run_bad_guys_initial_calibration.py",
        "tools/baseline005_provenance.py",
        "tools/validate_baseline005_provenance.py",
        "scripts/durable_status_monitor.py",
    ):
        source[name] = pin(root / name)
    files, origins = dependency_inventory()
    return RuntimeIdentity(
        root,
        source,
        {"pyproject.toml": pin(root / "pyproject.toml")},
        pin(Path(sys.executable)),
        files,
        origins,
        interpreter_inventory(),
    )


def telemetry_grant(root, authorization="test"):
    return TelemetryGrant(
        root, directory_identity(root), (root.parent / "protected-checkpoint",), authorization
    )

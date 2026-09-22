import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = "CALIBRATION_V1_20260922T195655Z_0558cee1f736"
LAUNCHER_REL = f"docs/cardcade/{RUN}/launcher.py"
EXPECTED_SHA256 = "BE601C53ECFF559D10F8D9BCB43F1798696CB49A08DC1B27E1715E57D05870F5"


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def test_authenticated_launcher_is_opaque_and_hash_is_unchanged():
    assert git("check-attr", "-a", "--", LAUNCHER_REL) == f"{LAUNCHER_REL}: text: unset"
    committed = subprocess.check_output(["git", "show", f"HEAD:{LAUNCHER_REL}"], cwd=ROOT)
    checkout = (ROOT / LAUNCHER_REL).read_bytes()
    assert hashlib.sha256(committed).hexdigest().upper() == EXPECTED_SHA256
    assert hashlib.sha256(checkout.replace(b"\r\n", b"\n")).hexdigest().upper() == EXPECTED_SHA256


def test_opaque_launcher_survives_autocrlf_checkout(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    launcher = repo / LAUNCHER_REL
    launcher.parent.mkdir(parents=True)
    payload = b"from pathlib import Path\nprint('authenticated')\n"
    launcher.write_bytes(payload)
    (repo / ".gitattributes").write_text(
        "docs/cardcade/CALIBRATION_V1_*/launcher.py -text\n", encoding="utf-8", newline="\n"
    )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "true"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=repo,
        check=True,
    )
    committed = subprocess.check_output(["git", "show", f"HEAD:{LAUNCHER_REL}"], cwd=repo)
    launcher.unlink()
    subprocess.run(["git", "checkout", "--", LAUNCHER_REL], cwd=repo, check=True)
    assert launcher.read_bytes() == committed == payload

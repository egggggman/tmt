"""Historical identity uses raw Git bytes, allowing only checkout EOL conversion."""

import hashlib
import subprocess
from pathlib import Path

import pytest

from tools.historical_validation import (
    authenticated_blob_oid,
    authenticated_bytes,
    authenticated_sha256,
    recorded_checkout_sha_matches,
)


@pytest.fixture
def repository(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=tmp_path, check=True)
    return tmp_path


def commit(root, path, data):
    path.write_bytes(data)
    subprocess.run(["git", "add", path.name], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--quiet",
            "-m",
            "fixture",
        ],
        cwd=root,
        check=True,
    )


@pytest.mark.parametrize("blob_eol", [b"\n", b"\r\n"])
@pytest.mark.parametrize("checkout_eol", [b"\n", b"\r\n"])
def test_identity_preserves_raw_blob_hash(repository, blob_eol, checkout_eol):
    path = repository / "evidence.json"
    blob = b'{\n  "winner": "leonardo"\n}\n'.replace(b"\n", blob_eol)
    commit(repository, path, blob)
    path.write_bytes(blob.replace(b"\r\n", b"\n").replace(b"\n", checkout_eol))
    assert authenticated_bytes(path, repository) == blob
    assert authenticated_sha256(path, repository) == hashlib.sha256(blob).hexdigest()
    expected_oid = (
        subprocess.check_output(["git", "rev-parse", "HEAD:evidence.json"], cwd=repository)
        .decode("ascii")
        .strip()
    )
    assert authenticated_blob_oid(path, repository) == expected_oid
    for recorded_eol in (b"\n", b"\r\n"):
        recorded = hashlib.sha256(
            blob.replace(b"\r\n", b"\n").replace(b"\n", recorded_eol)
        ).hexdigest()
        assert recorded_checkout_sha_matches(path, recorded, repository)
    assert not recorded_checkout_sha_matches(path, "0" * 64, repository)


@pytest.mark.parametrize(
    "replacement",
    [
        b'{"winner":"krang"}\n',  # forged result
        b'{"winner": "leonardo"}\n',  # formatting is still a real byte change
        b'{"winner":"leonardo"}\r',  # lone CR is not checkout CRLF conversion
    ],
)
def test_modified_evidence_rejected_even_with_recomputed_hash(repository, replacement):
    path = repository / "evidence.json"
    commit(repository, path, b'{"winner":"leonardo"}\n')
    path.write_bytes(replacement)
    forged_sha = hashlib.sha256(replacement).hexdigest()
    with pytest.raises(ValueError, match="differs from Git authority"):
        assert authenticated_sha256(path, repository) == forged_sha
    with pytest.raises(ValueError, match="differs from Git authority"):
        recorded_checkout_sha_matches(path, forged_sha, repository)


def test_binary_artifacts_must_remain_exact(repository):
    path = repository / "evidence.json.gz"
    commit(repository, path, b"binary\x00\n")
    path.write_bytes(b"binary\x00\r\n")
    with pytest.raises(ValueError, match="differs from Git authority"):
        authenticated_bytes(path, repository)


def test_missing_authority_never_falls_back_to_checkout(repository):
    path = repository / "forged.json"
    path.write_bytes(b"{}\n")
    with pytest.raises(subprocess.CalledProcessError):
        authenticated_bytes(path, repository)


def test_git_blob_reads_are_binary(monkeypatch, tmp_path):
    path = tmp_path / "evidence.json"
    raw = b'{"name":"\xc3\xa9"}\r\n'
    path.write_bytes(raw)

    def git(args, **kwargs):
        assert args == ["git", "show", "HEAD:evidence.json"]
        assert kwargs == {"cwd": tmp_path}
        return raw

    monkeypatch.setattr(subprocess, "check_output", git)
    assert authenticated_bytes(path, tmp_path) == raw


@pytest.mark.parametrize("eol", [b"\n", b"\r\n"])
def test_combined_validators_accept_checkout_eol_only(monkeypatch, eol):
    from tools import validate_combined_006_r7a as combined006
    from tools import validate_combined_007_r8a as combined007
    from tools import validate_objective_balance_lab_baseline005 as baseline005

    original = Path.read_bytes

    def checkout_bytes(path):
        raw = original(path)
        if path.suffix in {".json", ".txt", ".md"}:
            return raw.replace(b"\r\n", b"\n").replace(b"\n", eol)
        return raw

    monkeypatch.setattr(Path, "read_bytes", checkout_bytes)
    for validator in (combined006, combined007):
        assert validator.validate()["acceptance"] == "PASS_COMBINED_INDEPENDENT_READ_ONLY"
    baseline005.validate()


def test_forged_manifest_rejected_by_combined_validator(monkeypatch):
    from tools import validate_combined_006_r7a as validator

    original = Path.read_bytes

    def forged(path):
        raw = original(path)
        if path == validator.MANIFEST:
            return raw + b" "
        return raw

    monkeypatch.setattr(Path, "read_bytes", forged)
    with pytest.raises(ValueError, match="differs from Git authority"):
        validator.validate()


@pytest.mark.parametrize(
    "evidence,source,key",
    [
        (
            "BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json",
            "ROUND_1_EVIDENCE.json",
            "original_evidence_sha256",
        ),
        (
            "ROUND_4A_POST_SUPPORT_EVIDENCE.json",
            "ROUND_4A_RAPHAEL_EVIDENCE.json",
            "pre_support_evidence_sha256",
        ),
    ],
)
def test_preserved_legacy_checkout_sha_values(evidence, source, key):
    import json

    root = Path(__file__).resolve().parents[1]
    artifacts = root / "docs/objective-balance-lab"
    recorded = json.loads((artifacts / evidence).read_text(encoding="utf-8"))[key]
    assert recorded_checkout_sha_matches(artifacts / source, recorded, root)


@pytest.mark.parametrize(
    "name,raw,attributes",
    [
        ("evidence.bin", b"opaque\nbytes", None),
        ("evidence.zip", b"PK\x03\x04\n\xff", None),
        ("evidence.GZ", b"\x1f\x8b\x08\n\xff", None),
        ("evidence.gz", b"compressed\nbytes", None),
        ("evidence.json", b"\xff\n", None),
        ("evidence.txt", b"binary\0\n", None),
        ("evidence.md", b"binary\x01\n", None),
        ("evidence.txt", b"preserved\ntext", "*.txt -text\n"),
        ("evidence.txt", b"preserved\ntext", "*.txt binary\n"),
        ("evidence.txt", b"preserved\ntext", "*.txt text=unknown\n"),
        ("unclassified", b"preserved\ntext", "unclassified text\n"),
    ],
)
def test_ineligible_artifacts_and_legacy_hashes_are_byte_exact(repository, name, raw, attributes):
    if attributes:
        commit(repository, repository / ".gitattributes", attributes.encode())
    path = repository / name
    commit(repository, path, raw)
    exact_sha = hashlib.sha256(raw).hexdigest()
    converted = raw.replace(b"\n", b"\r\n")
    converted_sha = hashlib.sha256(converted).hexdigest()
    assert authenticated_bytes(path, repository) == raw
    assert authenticated_sha256(path, repository) == exact_sha
    assert recorded_checkout_sha_matches(path, exact_sha, repository)
    assert not recorded_checkout_sha_matches(path, converted_sha, repository)
    path.write_bytes(converted)
    for authenticate in (authenticated_bytes, authenticated_sha256, authenticated_blob_oid):
        with pytest.raises(ValueError, match="differs from Git authority"):
            authenticate(path, repository)
    with pytest.raises(ValueError, match="differs from Git authority"):
        recorded_checkout_sha_matches(path, converted_sha, repository)


@pytest.mark.parametrize("attribute", ["text", "text=auto", ""])
def test_verified_utf8_text_can_convert_eol(repository, attribute):
    commit(repository, repository / ".gitattributes", f"*.txt {attribute}\n".encode())
    path = repository / "evidence.txt"
    raw = "evidence: é\n\tresult\n".encode()
    commit(repository, path, raw)
    path.write_bytes(raw.replace(b"\n", b"\r\n"))
    assert authenticated_bytes(path, repository) == raw
    assert recorded_checkout_sha_matches(
        path, hashlib.sha256(path.read_bytes()).hexdigest(), repository
    )


def test_checkout_attributes_cannot_override_committed_minus_text(repository):
    attributes = repository / ".gitattributes"
    commit(repository, attributes, b"*.txt -text\n")
    path = repository / "evidence.txt"
    commit(repository, path, b"original\n")
    authority = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository).decode().strip()
    )
    # Both uncommitted and later committed attribute changes must not weaken an
    # explicitly selected historical authority.
    for committed in (False, True):
        attributes.write_bytes(b"*.txt text\n")
        if committed:
            commit(repository, attributes, b"*.txt text\n")
        path.write_bytes(b"original\r\n")
        with pytest.raises(ValueError, match="differs from Git authority"):
            authenticated_bytes(path, repository, authority)


@pytest.mark.parametrize("authority", ["no-such-commit", "HEAD:missing"])
def test_incorrect_git_authority_fails_closed(repository, authority):
    path = repository / "evidence.json"
    commit(repository, path, b"{}\n")
    with pytest.raises(subprocess.CalledProcessError):
        authenticated_bytes(path, repository, authority)


def test_missing_repository_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    path = tmp_path / "evidence.txt"
    path.write_bytes(b"original\n")
    with pytest.raises(subprocess.CalledProcessError):
        authenticated_bytes(path, tmp_path)


def test_missing_git_executable_fails_closed(tmp_path, monkeypatch):
    path = tmp_path / "evidence.txt"
    path.write_bytes(b"original\n")

    def missing(*args, **kwargs):
        raise FileNotFoundError("git is unavailable")

    monkeypatch.setattr(subprocess, "check_output", missing)
    with pytest.raises(FileNotFoundError):
        authenticated_bytes(path, tmp_path)


def test_missing_attribute_authority_fails_closed(repository, monkeypatch):
    path = repository / "evidence.txt"
    commit(repository, path, b"original\n")
    path.write_bytes(b"original\r\n")
    actual = subprocess.check_output

    def missing(args, **kwargs):
        if args[:2] == ["git", "check-attr"]:
            raise subprocess.CalledProcessError(1, args)
        return actual(args, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", missing)
    with pytest.raises(subprocess.CalledProcessError):
        authenticated_bytes(path, repository)


def test_checkout_minus_text_can_only_narrow_eligibility(repository):
    path = repository / "evidence.txt"
    commit(repository, path, b"original\n")
    (repository / ".gitattributes").write_bytes(b"*.txt -text\n")
    assert not recorded_checkout_sha_matches(
        path, hashlib.sha256(b"original\r\n").hexdigest(), repository
    )
    path.write_bytes(b"original\r\n")
    with pytest.raises(ValueError, match="differs from Git authority"):
        authenticated_bytes(path, repository)

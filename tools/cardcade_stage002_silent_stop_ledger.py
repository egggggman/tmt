"""Build a read-only, source-linked ledger for the archived Stage 002 stops."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

EXPECTED_SOURCE_COMMIT = "32a80228714674327aca62f8b86b70c4c4afc929"
EXPECTED_STAGE_BLOB = "bed173e3f4f3f13b0d1320a3a910153c38d844be"
EXPECTED_CARD_DATA_SHA256 = "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402"
EXPECTED_SOURCE_BLOBS = {
    "src/tmnt_design_studio/card_interpreter07.py": "7b39e4fcb2402385e7d46893f08300ffdf862540",
    "src/tmnt_design_studio/engine07.py": "62fb52e18e2747d4b758f041de6279032c887435",
    "src/tmnt_design_studio/pilot07.py": "c79a0f60230b999b1f5ca2a54137988f68c50513",
    "src/tmnt_design_studio/stage002.py": "bed173e3f4f3f13b0d1320a3a910153c38d844be",
}
EXPECTED_STAGE_MANIFEST_DIGEST = "58788be5bc4322ba7ffc5aa36b1df61fd3f487d6b2ea539b3129a998d4cdf771"
RECONCILED_COUNTS = {
    "Indeterminate": 303,
    "Conformance/provenance defect": 126,
    "Unsupported semantic": 56,
}

FIELDS = (
    "record_id",
    "run_id",
    "game_id",
    "seed",
    "pairing_id",
    "completion_state",
    "stop_index",
    "source_record_identity",
    "source_json_pointer",
    "stop_kind",
    "stop_detail_json",
    "classification",
    "mechanic_family",
    "linked_card_text",
    "provisional_cause",
    "severity",
    "supporting_evidence",
    "confidence",
    "result_sha256",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def classify_mechanic(fragment: str) -> str:
    text = fragment.casefold()
    if "block" in text or "menace" in text or "attack" in text:
        return "Combat legality"
    if "mana" in text or "{t}: add" in text:
        return "Mana and payment"
    if "graveyard" in text or "dies" in text or "exile" in text or "return" in text:
        return "Zone transition and recursion"
    if "artifact" in text or "equipment" in text or "vehicle" in text:
        return "Artifact interaction"
    if "target" in text:
        return "Targeting and resolution"
    if "draw" in text or "scry" in text:
        return "Card draw and selection"
    if ":" in text:
        return "Activated ability"
    return "Other static or triggered ability"


def row_for_stop(
    *,
    run_manifest: dict[str, object],
    source_path: Path,
    result_sha256: str,
    stop_index: int,
    stop: dict[str, object],
    source_record_identity: str,
    source_json_pointer: str,
    snapshot: dict[str, object],
    report: dict[str, object],
) -> dict[str, str]:
    conformance = snapshot["conformance"]
    occurrences = conformance["semantic_occurrences"]
    witnesses = conformance["opportunity_witnesses"]
    contexts = conformance["opportunity_contexts"]
    executions = conformance["executed_references"]
    detail_values = stop.get("detail", [])
    details = (
        {str(value) for value in detail_values}
        if isinstance(detail_values, list)
        else {str(detail_values)}
    )

    occurrence_ids = {str(item.get("occurrence_id")): item for item in occurrences}
    semantic_keys = {str(item.get("semantic_key")): item for item in occurrences}
    witness_by_id = {str(item.get("witness_id")): item for item in witnesses}
    context_by_id = {str(item.get("context_id")): item for item in contexts}
    execution_by_id = {str(item.get("evidence_id")): item for item in executions}

    related: dict[str, dict[str, object]] = {}
    for detail in details:
        if detail in occurrence_ids:
            related[detail] = occurrence_ids[detail]
        if detail in semantic_keys:
            item = semantic_keys[detail]
            related[str(item.get("occurrence_id"))] = item
        witness = witness_by_id.get(detail)
        if witness:
            item = occurrence_ids.get(str(witness.get("occurrence_id")))
            if item:
                related[str(item.get("occurrence_id"))] = item
        context = context_by_id.get(detail)
        if context:
            source_id = str(context.get("source_id"))
            for item in occurrences:
                if str(item.get("object_id")) == source_id:
                    related[str(item.get("occurrence_id"))] = item
        execution = execution_by_id.get(detail)
        if execution:
            source_id = str(execution.get("source_id"))
            for item in occurrences:
                if str(item.get("object_id")) == source_id:
                    related[str(item.get("occurrence_id"))] = item

    reached_keys = {str(value) for value in report["classification_sets"]["reached_unsupported"]}
    authenticated_ids = {
        str(item.get("evidence_id")) for item in report["authenticated_executed_references"]
    }
    invalid_execution_ids = {
        str(item.get("evidence_id"))
        for item in executions
        if str(item.get("evidence_id")) not in authenticated_ids
    }
    linked_keys = {str(item.get("semantic_key")) for item in related.values()}

    # Frozen reconciler stop details identify bad executions directly, or identify
    # reached semantic keys. Other unlinked presence/index gaps remain indeterminate.
    provenance = bool(details & invalid_execution_ids)
    if not provenance and details:
        provenance = any(
            detail in context_by_id or detail in witness_by_id for detail in details
        ) and not (linked_keys & reached_keys)
    unsupported = bool(details & reached_keys)
    if provenance:
        classification = "Conformance/provenance defect"
        cause = (
            "Frozen reconciler could not authenticate/reconstruct execution or context evidence."
        )
        severity = "High evidence risk; gameplay error not established."
        confidence = "High for evidence failure; low for gameplay consequence."
    elif unsupported:
        classification = "Unsupported semantic"
        cause = "Detail links to a reached occurrence with unsupported semantics."
        severity = "Potentially gameplay consequential; historical outcome effect unproven."
        confidence = "High that the semantic was reached; low that the outcome was wrong."
    else:
        classification = "Indeterminate"
        cause = "Stop concerns an unreached/unindexed semantic or lacks a reconstructive link."
        severity = "Undetermined; no consequential behavior established."
        confidence = "High that evidence is insufficient; low on any gameplay cause."

    presence = snapshot.get("stage002_presence", [])
    linked_text: list[str] = []
    families: set[str] = set()
    for item in related.values():
        object_id = str(item.get("object_id"))
        card_name = next(
            (
                str(record.get("card"))
                for record in presence
                if object_id in {str(value) for value in record.get("object_ids", [])}
            ),
            "card identity unresolved",
        )
        fragment = str(item.get("oracle_fragment", ""))
        families.add(classify_mechanic(fragment))
        linked_text.append(f"{card_name}: {fragment}")

    stop_json = canonical_json(stop)
    stop_hash = sha256_bytes(stop_json.encode("utf-8"))
    run_id = str(run_manifest["run_id"])
    pointer = f"{source_path}#{source_json_pointer}"
    evidence = (
        f"{pointer}; reconciler stop SHA-256={stop_hash}; result SHA-256={result_sha256}; "
        f"batch run_manifest={source_path.parent / 'run_manifest.json'}"
    )
    game_id = run_id
    return {
        "record_id": f"{run_id}:silent_approximation:{stop_index}:{stop_hash[:16]}",
        "run_id": run_id,
        "game_id": game_id,
        "seed": str(run_manifest.get("seed", "")),
        "pairing_id": str(run_manifest.get("pairing_id", "")),
        "completion_state": "COMPLETE",
        "stop_index": str(stop_index),
        "source_record_identity": source_record_identity,
        "source_json_pointer": source_json_pointer,
        "stop_kind": str(stop.get("kind", "")),
        "stop_detail_json": canonical_json(stop.get("detail")),
        "classification": classification,
        "mechanic_family": "; ".join(sorted(families)) or "Unresolved evidence/index identity",
        "linked_card_text": " | ".join(sorted(set(linked_text))) or "",
        "provisional_cause": cause,
        "severity": severity,
        "supporting_evidence": evidence,
        "confidence": confidence,
        "result_sha256": result_sha256,
    }


def build_ledger(
    archive_root: Path, frozen_root: Path, manifest_path: Path
) -> list[dict[str, str]]:
    frozen_stage = frozen_root / "src" / "tmnt_design_studio" / "stage002.py"
    stage_bytes = frozen_stage.read_bytes()
    if git_blob_sha1(stage_bytes) != EXPECTED_STAGE_BLOB:
        raise ValueError("frozen Stage 002 source blob does not match the archived identity")
    card_data = frozen_root / "cardcade" / "scryfall-tmt-pza-tmc-2026-08-13.json"
    if sha256_bytes(card_data.read_bytes()) != EXPECTED_CARD_DATA_SHA256:
        raise ValueError("frozen card-data snapshot does not match the archived identity")
    sys.path.insert(0, str(frozen_root / "src"))
    from tmnt_design_studio.stage002 import DeckSpec, GameSpec, reconcile_snapshot

    manifest_doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    stage_manifest = manifest_doc["manifest"]
    if stage_manifest.get("manifest_digest") != EXPECTED_STAGE_MANIFEST_DIGEST:
        raise ValueError("preserved Stage 002 manifest digest is not the expected source identity")

    result_files = sorted(
        archive_root.glob("cardcade-smoke10-20261031-explore300r1-b*-g*/result.json"),
        key=lambda path: (
            int(path.parent.name.rsplit("-b", 1)[1].split("-g", 1)[0]),
            int(path.parent.name.rsplit("-g", 1)[1]),
        ),
    )
    if len(result_files) != 300:
        raise ValueError(f"expected 300 preserved result files, found {len(result_files)}")

    rows = []
    seen_runs: set[str] = set()
    for source_path in result_files:
        result_bytes = source_path.read_bytes()
        result_sha256 = sha256_bytes(result_bytes)
        result = json.loads(result_bytes)
        manifest_bytes = (source_path.parent / "run_manifest.json").read_bytes()
        run_manifest = json.loads(manifest_bytes)
        if (
            run_manifest.get("source_commit") != EXPECTED_SOURCE_COMMIT
            or result.get("source_commit") != EXPECTED_SOURCE_COMMIT
        ):
            raise ValueError(f"unexpected source commit at {source_path}")
        if (
            run_manifest.get("card_data_sha256") != EXPECTED_CARD_DATA_SHA256
            or run_manifest.get("copied_source_blobs") != EXPECTED_SOURCE_BLOBS
            or result.get("source_blobs") != EXPECTED_SOURCE_BLOBS
        ):
            raise ValueError(f"source or card-data identity mismatch at {source_path}")
        if result.get("run_id") != run_manifest.get("run_id"):
            raise ValueError(f"run identity mismatch for {source_path}")
        if result.get("seed") != run_manifest.get("seed"):
            raise ValueError(f"seed mismatch for {source_path}")
        if not str(run_manifest.get("run_id", "")).startswith(
            f"{run_manifest.get('batch_id', '')}-g"
        ):
            raise ValueError(f"batch/run identity mismatch for {source_path}")
        if result.get("completion_state") != "COMPLETE":
            raise ValueError(f"non-complete preserved result at {source_path}")
        run_id = str(result["run_id"])
        if run_id in seen_runs:
            raise ValueError(f"duplicate run ID {run_id}")
        seen_runs.add(run_id)

        seats = tuple(DeckSpec(str(seat), "") for seat in result["seats"])
        spec = GameSpec(
            run_id,
            str(result["pairing_id"]),
            int(run_manifest["seed"]),
            str(result["orientation"]),
            seats,
        )
        report = reconcile_snapshot(spec, result["snapshot"], stage_manifest)
        raw_stops = result["snapshot"]["conformance"].get("stop_records", [])
        for stop_index, stop in enumerate(report["stop_records"]):
            if stop.get("kind") != "silent_approximation":
                continue
            if stop_index < len(raw_stops):
                raw_index = stop_index
                identity = f"{run_id}:snapshot.conformance.stop_records[{raw_index}]"
                pointer = f"/snapshot/conformance/stop_records/{raw_index}"
            else:
                raw_index = None
                identity = f"{run_id}:frozen-reconciler-derived-stop:{stop_index}"
                pointer = "/snapshot/conformance"
            rows.append(
                row_for_stop(
                    run_manifest=run_manifest,
                    source_path=source_path,
                    result_sha256=result_sha256,
                    stop_index=stop_index,
                    stop=stop,
                    source_record_identity=identity,
                    source_json_pointer=pointer,
                    snapshot=result["snapshot"],
                    report=report,
                )
            )
    if len(seen_runs) != 300:
        raise ValueError(f"expected 300 unique run IDs, found {len(seen_runs)}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--frozen-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = build_ledger(args.archive_root, args.frozen_root, args.manifest)
    counts = Counter(row["classification"] for row in rows)
    expected = Counter(RECONCILED_COUNTS)
    if counts != expected:
        raise SystemExit(
            "classification reconciliation failed: "
            f"actual={dict(counts)}, expected={dict(expected)}"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    output_hash = sha256_bytes(args.output.read_bytes())
    print(
        "rows=485 unique_runs=300 counts="
        f"{dict(counts)} versus_prior_aggregate=14_fewer_indeterminate_14_more_unsupported "
        f"output_sha256={output_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

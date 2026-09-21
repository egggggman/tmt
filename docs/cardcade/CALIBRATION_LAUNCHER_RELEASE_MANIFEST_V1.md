# Calibration V1 launcher release manifest

`LAUNCHER_RELEASE_MANIFEST_V1.json` is the non-authorizing pre-generation release identity for one reserved Calibration Protocol V1 run. It is banked before `launcher.py` exists and has its own SHA-256 sidecar.

The manifest authenticates the committed reservation and V16 release baseline, records their inherited runtime, Protocol V1, frozen Seed Table V2, entropy, and schedule identities, and records the exact renderer source identity and deterministic render inputs:

- `launcher_rel` is the intended repository launcher path.
- `output_rel` is the governed external target `G:\cardcade\calibration-runs\<run_id>`.
- `render_inputs.release_manifest_rel` identifies this manifest; its sidecar supplies the manifest hash to the later renderer call.
- `render_inputs.packet_rel` and `packet_sha256` identify the non-authorizing V16 baseline packet.
- `render_inputs.seed_rel` and `seed_sha256` identify the frozen table without loading or consuming seed material.
- `renderer.rel` and `renderer.sha256` identify the exact renderer source required for reproduction.

The manifest is not a generated launcher hash. Before generation, `generated_launcher_sha256` is `null` and `launcher_generated` is `false`. After a separate generation step, the launcher bytes receive their own SHA-256 sidecar; that hash is never used as the pre-generation manifest identity.

Manifest banking, target resolution, launcher rendering, launcher hashing, final preflight, and execution authorization are separate gates. `execution_authorized` remains `false`; no manifest state grants seed access or calibration permission.

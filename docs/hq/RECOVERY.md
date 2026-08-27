# Mutants the Gathering Recovery Guide

## Goal

A clean machine with Git, Python tooling, and repository access should be able to recover project context without ChatGPT conversation history.

## 1. Clone

```console
git clone https://github.com/egggggman/tmt.git
cd tmt
git switch main
git pull --ff-only
```

Confirm:

```console
git status
git log -5 --oneline
```

The working tree should be clean before beginning recovery or new work.

## 2. Read the durable orientation

Read in this order:

1. `README.md`
2. `docs/OUTSIDER_CONTINUITY.md`
3. `docs/HQ.md`
4. `docs/hq/CURRENT_STATE.md`
5. `PROJECT_STATE.md`
6. `docs/hq/TOOL_RESILIENCE.md`
7. the owning department's specifications/evidence for the next task.

## 3. Install project dependencies

The repository uses uv for the documented Python workflow.

```console
uv sync
```

Do not invent a substitute environment when the repository already defines one unless a Work Packet explicitly authorizes that change.

## 4. Validate the clone

Use the repository's documented validation entry points. At minimum inspect the current CI configuration and available validation tools before changing code.

Common project commands documented elsewhere include:

```console
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

When `tools/validate_repo.py` is present and applicable, use it as the repository-wide validation entry point.

Cardcade work may require additional focused acceptance, conformance, Stage, or Smoke runners. The Work Packet must name them rather than relying on memory.

## 5. Determine the next authorized task

Read `docs/hq/CURRENT_STATE.md` and the relevant department record.

Do not infer authorization merely because code exists for a later stage. In particular:

- Prototype 0.2 remains frozen until Design Studio explicitly authorizes a successor;
- Cardcade validation stages must follow their recorded readiness/authorization gates;
- calibration evidence must not be treated as valid before its gate clears;
- a GUI or dashboard must not compensate for missing engine behavior.

## 6. Continue through a Work Packet

Prefer an existing Work Packet. If none exists for a significant bounded task, create one using `docs/hq/WORK_PACKET_SPEC.md` before implementation.

This is what makes the task portable between Codex, other tools, and humans.

## 7. Preserve evidence

Never discard meaningful:

- prototype versions;
- rejected acceptance audits;
- failed validation runs that reveal a real defect;
- deterministic seeds;
- hashes/digests;
- physical test results;
- accepted decisions.

A failed attempt can be valuable evidence.

## 8. Handoff before stopping

Before leaving a task:

1. commit/push work that is meant to be durable;
2. record whether the branch is clean;
3. record the exact branch/SHA;
4. record validation results;
5. record what remains blocked or unaudited;
6. update the Work Packet or PR with the next action.

## Recovery success criterion

Recovery succeeds when another contributor can state the current project status and resume the next authorized task without asking what happened in an old chat.

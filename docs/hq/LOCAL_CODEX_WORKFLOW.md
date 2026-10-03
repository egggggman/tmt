# Local Codex Workflow

Status: HQ operating policy candidate

## Purpose

Keep Mutants the Gathering organized through ChatGPT while allowing Codex and other implementation tools to work efficiently against one local repository checkout. Move deterministic execution to the local machine wherever practical, preserve every durable candidate and result in GitHub, and keep implementation separate from independent acceptance.

This workflow does not change department authority, Cardcade acceptance gates, prototype authorization, or repository governance.

## Roles

### ChatGPT / owning department

Director and independent reviewer.

- determines the authorized next Action or Work Packet;
- interprets repository evidence and department policy;
- reviews the pushed candidate independently;
- returns ACCEPT or REJECT when authorized to perform that review;
- coordinates the next Action after accepted work is banked.

Chat history is not the durable project record. Durable decisions and accepted evidence belong in GitHub.

### Codex / implementation agent

Builder.

- reads the current Work Packet and repository state;
- writes or changes code;
- adds or updates tests required by the authorized scope;
- keeps commits focused;
- does not broaden the Work Packet;
- does not accept or merge its own candidate.

Codex may run targeted commands while building, but deterministic validation should be runnable independently on the local machine rather than requiring agent reasoning to supervise it.

### Local machine

Execution and test bench.

Authoritative working checkout for the normal Windows Cardcade loop:

`C:\Projects\tmt`

Typical deterministic work includes:

- repository synchronization;
- pytest;
- Ruff check and format check;
- `git diff --check`;
- Cardcade validation;
- deterministic replays;
- hashes and evidence generation;
- simulations only when the current gate explicitly authorizes them.

A local PASS is evidence, not independent acceptance.

### GitHub

Source of truth and handoff layer.

- authoritative baseline;
- branches and commits;
- Work Packets and specifications;
- candidate PRs;
- test/evidence records;
- accepted history;
- synchronization point between ChatGPT, Codex, other tools, and the local machine.

## Standard development loop

```text
CHATGPT / OWNING DEPARTMENT
Director + independent reviewer
        |
        | define authorized Action / Work Packet
        v
GITHUB
Authoritative baseline
        |
        | sync
        v
C:\Projects\tmt
LOCAL WORKSPACE
        |
        v
CODEX
Builder
        |
        | code + tests inside packet scope
        v
LOCAL MACHINE
Execution / Test Bench
        |
        | pytest
        | Ruff
        | git diff --check
        | Cardcade validation
        | deterministic replay
        | simulation only when authorized
        |
        +---- FAIL -----------------> CODEX
        |                              fix candidate
        |
        +---- PASS
                |
                v
             GITHUB
        Candidate + Evidence
                |
                v
             CHATGPT
        Independent Review
           |          |
        REJECT      ACCEPT
           |          |
           v          v
         CODEX     MERGE / BANK
                      |
                      v
                  NEXT ACTION
```

## Human-readable work states

Every bounded Action or Work Packet should be describable using one of these states:

1. **BUILD** — authorized implementation is being produced.
2. **LOCAL VALIDATION** — the exact candidate is undergoing deterministic local checks.
3. **PUSHED** — the validated candidate and required evidence are durably available in GitHub.
4. **REVIEW** — an independent reviewer is evaluating the exact pushed candidate.
5. **BANKED** — accepted candidate is merged/preserved and may become the baseline for the next authorized Action.

A rejection returns the work to BUILD without erasing the rejected evidence.

## Freshness preflight

Before starting a Work Packet, the worker must:

1. fetch/synchronize the authoritative repository state;
2. record the exact baseline SHA;
3. inspect newer merged evidence and relevant open PRs/Work Packets;
4. distinguish merged authority from unmerged candidates;
5. stop and escalate if the authorization boundary is contradictory or stale.

Do not infer authorization from an old status snapshot.

## Capability boundary

A tool must not claim checks it cannot perform.

If an agent lacks shell, local checkout, pytest, CI, write access, or another required capability, it must mark the relevant validation **NOT EXECUTED — TOOLING UNAVAILABLE** and hand the work to a properly equipped worker. Missing tools never justify weakening the acceptance contract.

## Efficiency rule

Use model/agent reasoning for work that benefits from reasoning:

- implementation;
- debugging;
- investigation;
- code review;
- interpretation;
- planning.

Prefer local deterministic execution for already-encoded mechanical work:

- tests;
- linters;
- replays;
- validation scripts;
- simulations;
- hashes;
- evidence generation.

Codex is an accelerator, not the test infrastructure.

## Acceptance boundary

The implementing tool is never the authority on its own correctness.

The implementer may self-check its candidate, but self-checking is not independent acceptance. The candidate must be pushed with sufficient evidence for the required independent review. An agent assigned specifically to audit work produced by a different implementer may issue the audit verdict allowed by that Work Packet.

The human project owner retains final governance authority.

## Cardcade guardrails

This workflow does not authorize work that Cardcade governance currently prohibits. In particular:

- do not revise decks to compensate for simulator defects;
- do not tune the simulator to manufacture a target win rate;
- do not authorize Prototype 0.3 without the proper Design Studio gate;
- do not start calibration or broad simulation merely because local execution is convenient;
- do not weaken fail-closed behavior or evidence requirements to make a candidate pass;
- preserve failed and historical evidence.

## Default Cardcade cycle

For a bounded Cardcade Action:

**sync `C:\Projects\tmt` → Codex builds the Action → Windows validates the exact candidate locally → candidate/evidence are pushed to GitHub → ChatGPT performs or coordinates independent review → REJECT returns to Codex / ACCEPT banks the candidate → next authorized Action.**

This is the default development loop through Cardcade 1.0 unless evidence demonstrates that a different workflow is required.

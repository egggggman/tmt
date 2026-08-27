# HQ Tool Resilience

## Purpose

Mutants the Gathering must not depend on one AI product, one coding agent, one local machine, or one conversation history to continue operating.

**GitHub is the project bus and durable source of truth.** AI tools are interchangeable workers around that durable record.

The resilience objective is:

> A fresh contributor, human or agent, can clone the repository, determine the current state, select an authorized task, validate work, and produce an auditable handoff without access to prior chat history.

## Operating model

| Layer | Durable owner |
| --- | --- |
| Project state, roadmap, decisions, task contracts | GitHub |
| Code, tests, schemas, data snapshots, evidence | GitHub |
| Implementation | Any suitable coding tool or human contributor |
| Validation | Repository commands and CI |
| Acceptance | Evidence-backed review against an explicit contract |
| Department coordination | HQ |
| Working discussion | Chat/project rooms; non-authoritative until promoted |
| Recovery | Fresh clone plus repository documentation |

Codex is an accelerator, not infrastructure. A Codex quota limit may reduce implementation throughput, but it must not make the project unintelligible or prevent other authorized work from continuing.

## HQ responsibilities

HQ owns the resilience policy and must:

1. keep the durable current-state documents synchronized with accepted repository evidence;
2. issue portable Work Packets for bounded implementation or audit work;
3. ensure every critical workflow has a repository-visible validation path;
4. distinguish merged evidence from local-only or uncommitted evidence;
5. keep department ownership intact when work moves between tools;
6. periodically run the Fresh Clone Test;
7. treat any answer that requires reconstructing old chat history as documentation debt.

## Tool-independent work

A task is considered tool-independent when a contributor can execute it from a fresh clone using the repository, the Work Packet, normal development tooling, and public/authorized dependencies.

The task may be performed by Codex, another coding agent, an IDE assistant, a human developer, or a combination. The acceptance contract must not depend on the implementer's identity.

## Evidence rule

The implementing tool is never the authority on its own correctness.

Accepted work should flow through:

```text
HQ / department-owned Work Packet
        ↓
candidate branch
        ↓
repository tests + deterministic checks + CI
        ↓
independent audit or review where required
        ↓
GitHub PR
        ↓
merged durable evidence
```

For Cardcade in particular, preserve deterministic seeds, invariant checks, unsupported-semantics reporting, exact evidence artifacts, and rejected audit history when those are part of the accepted workflow.

## Local evidence

Local-only evidence can be useful during development, but it must be labeled **LOCAL / NON-DURABLE** until committed or otherwise preserved through an accepted repository workflow.

Dashboards such as the Sewer Status Board and Cardcade dashboard should prefer merged GitHub evidence. They may show local evidence only when the active environment can actually inspect it, and must label it separately.

## Fresh Clone Test

At meaningful milestones, HQ should test whether a clean clone can answer:

- What are we building?
- What prototype is current?
- Which department owns each decision?
- What is Cardcade's current accepted validation state?
- What is blocked, on hold, or actionable?
- What is the next authorized task?
- How is that task validated?
- Where is the evidence?
- How can another tool continue the work?
- How is rejected or historical evidence preserved?

If any answer depends on private chat memory, update GitHub.

## Resilience milestones

### Resilience 0.1 — GitHub Can Run the Project

Complete when:

- current state is synchronized;
- Work Packet format is durable;
- recovery instructions are durable;
- next moves are explicit;
- validation entry points are documented;
- tool/agent handoffs have a common contract;
- a fresh clone can resume an authorized task without prior conversation context.

### Resilience 0.2 — Repository-Generated Status

Future goal: reduce manually maintained status drift by generating or validating high-value state summaries from repository evidence.

Candidate entry points include:

```text
tools/validate_repo.py
tools/project_status.py
tools/cardcade_status.py
tools/next_move.py
```

These names are goals, not claims that every command already exists.

### Resilience 0.3 — Dashboard Consumers

PIZZAGRIND / the Sewer Status Board and DECKDAEMON / DD.0 should increasingly consume repository-generated state rather than reconstructing status from conversation history.

## Non-goals

Resilience does not mean:

- allowing multiple departments to redesign the same layer independently;
- bypassing acceptance gates;
- replacing evidence with AI consensus;
- storing secrets in the repository;
- making every task executable without specialized software;
- rewriting history to make handoffs look cleaner.

The goal is continuity, reproducibility, and portability while preserving authority boundaries.

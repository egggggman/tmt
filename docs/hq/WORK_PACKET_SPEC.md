# HQ Work Packet Specification

## Purpose

A Work Packet is the portable contract for a bounded unit of project work. It allows a task to move between Codex, another coding agent, a human contributor, or a different machine without rebuilding intent from chat history.

HQ owns the format. The department that owns the work owns the technical/content decisions inside the packet.

## Required fields

Every implementation or audit Work Packet should contain:

### Identity

- **Packet ID**
- **Owning department**
- **Title**
- **Status**: proposed / authorized / in progress / blocked / audit / accepted / superseded
- **Starting branch or SHA**
- **Related PRs / issues / evidence**

### Objective

One concise statement of the result the packet is meant to produce.

### Scope

Explicitly list what may change.

### Prohibited changes

Explicitly list adjacent layers that must not change.

Examples:

- no deck revisions;
- no Pilot tuning;
- no Prototype 0.3 authorization;
- no simulator assumptions changed to force balance;
- no physical geometry changes.

### Inputs

List authoritative files, data snapshots, rules references, prior evidence, and test fixtures required to do the work.

### Acceptance contract

Define observable completion conditions before implementation begins.

Include, as applicable:

- exact semantics or behavior;
- unit/integration tests;
- deterministic replay requirements;
- invariant requirements;
- lint/format checks;
- artifact hashes;
- evidence serialization;
- independent audit requirement;
- CI requirement.

### Stop conditions

Define what requires escalation rather than improvisation.

Examples:

- authoritative evidence contradicts the packet;
- a required capability belongs to another department;
- implementation would broaden scope;
- a simulator defect is discovered while evaluating deck balance;
- a missing rule requires architectural work not authorized by the packet.

### Handoff

Every completed attempt should report:

- candidate branch and SHA/fingerprint;
- changed files;
- validation results;
- known limitations;
- evidence locations;
- whether work is committed/pushed;
- whether independent audit is still required;
- exact recommended next action.

## Template

```markdown
# WP-XXXX — Title

Owner: Cardcade
Status: Authorized
Starting SHA: <sha>

## Objective
...

## Scope
- ...

## Prohibited changes
- ...

## Inputs
- ...

## Acceptance contract
- ...

## Stop conditions
- ...

## Required handoff
- ...
```

## Cardcade extension

Cardcade Work Packets should additionally state:

- represented Oracle/rules fragment or architectural responsibility;
- frozen-roster exposure when relevant;
- generic-vs-bounded support claim;
- exact unsupported neighbors that must remain unsupported;
- deterministic seeds/runners used for regression;
- expected evidence provenance;
- whether Stage, Smoke, calibration, or Prototype gates are authorized.

A Cardcade packet must never imply that successful implementation automatically authorizes a deck revision.

## Physical-product extension

Mr. Paperback packets should additionally state:

- mechanical template/dimensions;
- print stock/media assumption;
- scale;
- bleed/safe/cut/fold constraints;
- physical test required;
- what constitutes pass/fail after printing.

## Editorial / Canon extension

Canon and Underground Press packets should identify source/evidence standards, canonical boundaries, and what material is interpretation versus durable project canon.

## Packet lifecycle

Work Packets are preserved. If scope changes materially, create a new packet or explicitly supersede the old one rather than silently rewriting the original contract.

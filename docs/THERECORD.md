# THERECORD

## Purpose

THERECORD is the weekly instrumentation archive for Mutants the Gathering. It exists to preserve operating history so the project can identify efficiencies over time instead of relying on impressions such as "we worked a lot this week."

THERECORD is not a status board. The Sewer Status Board answers **where the project is and what to do next**. THERECORD answers **how the project is operating over time**.

## Archive policy

Weekly records are append-only snapshots. A newer week must not overwrite older weekly data.

The archive should support week-over-week and rolling 4-, 8-, and 12-week comparisons where enough evidence exists. Historical snapshots should remain inspectable even when definitions improve; schema changes should be documented rather than retroactively rewriting prior evidence without explanation.

## Evidence standard

Only report a metric as measured when the underlying product or repository actually exposes enough information to measure it.

If a value is unavailable, report **NOT EXPOSED** or **NOT MEASURED** rather than estimating it as fact.

This is especially important for ChatGPT Plus utilization. There is no project-defined universal message allowance that should be invented and treated as a denominator. Record actual cap events, interruptions, plan-pressure signals, or exposed usage counters when available.

## Metric families

### Usage

Possible weekly measures include:

- message activity;
- sessions or working threads when observable;
- active hours when observable;
- heavy-use days;
- peak working windows;
- department/topic distribution when classification is supported.

### Efficiency

Useful measures include:

- durable output per session or active hour;
- thread-resolution rate;
- repeated context-recovery/rework signals;
- time lost to blockers or usage interruptions;
- output trend relative to usage trend;
- rate of work promoted from conversation into durable repository records.

Efficiency is about useful progress, not maximizing message count.

### Output

Track concrete project output where possible, including:

- GitHub commits;
- pull requests;
- merged pull requests;
- durable documentation artifacts;
- accepted Cardcade checkpoints;
- physical prototypes;
- print tests;
- completed project milestones.

### Plan utilization

The Plus-plan module should focus on practical pressure rather than invented percentages:

- active plan;
- included usage consumed, only if exposed;
- limit/cap events;
- restricted/wait time caused by limits;
- applicable agentic allowance, only if exposed;
- purchased credits or extra spend where applicable;
- heavy-use days;
- peak window;
- plan pressure: `COMFORTABLE`, `WATCH`, or `CONSTRAINED`;
- evidence explaining the pressure classification.

## Plan-pressure interpretation

- **COMFORTABLE** — current work is not materially constrained by plan limits.
- **WATCH** — recurring near-limit behavior or interruptions may begin affecting project flow.
- **CONSTRAINED** — plan limits are repeatedly blocking productive work or creating material delay.

A plan-tier change should be considered because constraints cost meaningful project time, not because raw usage looks impressive.

## Relationship to PIZZAGRIND

PIZZAGRIND / The Sewer Status Board should contain only a small THERECORD health signal when it is operationally relevant, such as `PLAN PRESSURE: COMFORTABLE`.

The detailed message counts, hours, efficiency scores, trend charts, output-per-session analysis, and historical Plus-plan utilization belong here.

## Weekly record shape

A weekly snapshot should identify:

- week ending date;
- data/provenance sources;
- which metrics are measured versus inferred;
- usage summary;
- efficiency summary;
- output summary;
- plan-utilization summary;
- notable changes from the prior week;
- anomalies or data-quality limitations;
- efficiency observations worth testing in future weeks.

## What THERECORD is trying to learn

Over time the archive should help answer questions such as:

- Are we producing more durable work per active hour?
- Are conversations becoming more focused?
- Which departments consume the most effort?
- Is documentation reducing repeated context recovery?
- Are Cardcade development and acceptance cycles getting faster?
- How much work is being converted into durable GitHub evidence?
- Are physical prototypes becoming more efficient to produce?
- Is the current ChatGPT plan materially constraining work?
- Which process changes correlate with less rework and more completed milestones?

THERECORD should make efficiency improvements testable rather than anecdotal.

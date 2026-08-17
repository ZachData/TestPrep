# PROJECT.md — blueprint

Annotated template. `> ` lines are commentary; delete on instantiation.

> **What this file is for.** CLAUDE.md says *how to act*. PROJECT.md says *what is
> true and what we are trying to find out*. It is the project's memory: the thing a
> new session (human or agent) reads to reconstruct where the work stands without
> re-deriving it.
>
> **The test of a good PROJECT.md**: hand it to someone who has never seen the repo.
> They can state the question, the current best answer, what is confirmed vs. merely
> reported, and what the next action is — without asking you anything.
>
> **Volatility**: this file changes every session. That's correct. It is the one place
> state is allowed to live.
>
> **Length**: it will grow. Prune ruthlessly — resolved items move to a short
> "Settled" list or get deleted. A PROJECT.md nobody reads because it is 4,000 lines
> long has failed at its only job.

---

## Thesis

<Two to four sentences. What question does this project answer, and why is that
question answerable with the resources at hand? If you cannot write this without
hedging, that is the finding.>

## Frame

> Kuhn, made operational. Your paradigm is not an attitude; it is the set of things
> your representation and instruments can express. Writing it down converts "the
> result was null" into a two-branch question: the claim is false, *or* the claim is
> inexpressible in this frame. Without this section you will silently collapse the
> second branch into the first.

- **Representation**: <the state space / model class / feature basis you commit to>
- **Measurement**: <the instruments and metrics; what they can and cannot resolve>
- **Inexpressible here**: <claims that this frame cannot even pose — list them>
- **Alternative frames worth cross-checking**: <frames in which those claims *are*
  expressible, and what it would cost to run the same claim there>

## Hard core

> Lakatos. The assumptions you are *not* testing and will not abandon on a single
> anomaly. Naming them prevents two failures: testing them by accident, and defending
> them without noticing.

1. <assumption> — abandoning this would mean: <what>
2. ...

## Protective belt

> The auxiliaries you *are* willing to modify when something fails: preprocessing,
> hyperparameters, metric definitions, data filters, harness details.
>
> Rule: every modification to the belt is logged below with a **novel prediction** it
> makes. A belt change that only accommodates the anomaly and predicts nothing new is
> a degenerating move. Three consecutive degenerating moves is the signal to stop
> defending the programme, not a signal to try harder.

| Date | Anomaly | Belt change | Novel prediction it makes | Prediction tested? |
|---|---|---|---|---|
| | | | | |

## Claim ledger

> The core artifact. One row per falsifiable claim. Rows are created *before* the run,
> not after. A claim with no null is not a claim — put it under Directions.
>
> `Frame` ties back to the Frame section. `Reg-hash` is the hash of
> (claim, null, statistic, analysis code) computed at registration; CI recomputes it
> and fails on mismatch, which is what makes "we didn't move the goalposts" checkable
> rather than promised.

| ID | Claim | Null (H₀) | Statistic / test | Frame | Reg-hash | Status | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|
| C-001 | | | | | | registered / running / analyzed | e = , n tests = | open / refuted / survived |

Status vocabulary: `registered` → `running` → `analyzed`.
Verdict vocabulary: `open`, `refuted`, `survived` — never "proven", never "confirmed".

**Evidence budget**: α = <0.1>, max tests per claim = <5>, aggregation = <e-values,
product, reject at E ≥ 1/α>. Stopping rule fixed at registration.

## State of the world

> Split by evidence tier. This section is where paraphrase-becomes-memory is caught.
> An item may not move from Reported to Confirmed without pasting the output that
> justifies it, and the move is logged in Decisions.

**Confirmed** (command run, raw output seen):
- <item> — evidence: `<command>`, <date>

**Reported** (a tool or agent said so; output not inspected):
- <item> — reported by <whom>, <date>. To confirm: `<the exact command that would settle it>`

**Assumed** (never checked, load-bearing anyway):
- <item> — would be falsified by: <what>

## Directions

> Interesting ideas that are not yet claims because they lack a testable null.
> Explicitly a holding pen. Anything can go here — this is where "anything goes"
> is correct. Nothing leaves here without acquiring a null.

- <direction> — blocked on: <what would make it testable>

## Open questions and blockers

| # | Question | Blocks | Owner | What would resolve it |
|---|---|---|---|---|

## Decisions

> Append-only. Each entry: what, why, and — critically — reversibility. Re-litigating
> a settled decision is the second-largest sink of time in long projects; the largest
> is silently reversing one.

| Date | Decision | Rationale (one line) | Reversible? | Revisit when |
|---|---|---|---|---|

## Accepted limitations

> Things that are wrong and will stay wrong, deliberately. Distinguishing these from
> bugs stops them being rediscovered every few sessions.

- <limitation> — accepted because <reason>; cost if it bites: <what>

## Next up

Ordered. Each item names its blocker if it has one.

1. <action> — blocked by: <none / item #>
2. ...

## Glossary

<Project-specific terms, one line each. Include the ones you think are obvious.>

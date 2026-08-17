# CLAUDE.md — blueprint

Annotated template. Everything in `> ` is commentary; delete it when you instantiate.
Everything else is the shape of the file.

> **What this file is for.** CLAUDE.md is prepended to the agent's context in every
> session in this repo. It is the only prompt real estate you control that costs you
> nothing per-use. Its job is to remove the agent's need to guess: about commands,
> about conventions, about what is forbidden, about what "done" means.
>
> **What this file cannot do.** It is advisory text, not enforcement. An agent under
> context pressure, or a subagent that never loaded it, will violate it. Therefore:
>
> **The load-bearing rule** — if breaking a rule would damage the project, the rule
> does not belong here. It belongs in a hook, a CI check, a wrapper script, or an IAM
> policy. CLAUDE.md holds the rules whose violation is *expensive but recoverable*.
> Write down which mechanism actually enforces each hard rule; if the answer is
> "this file," that rule is unenforced.
>
> **Length discipline.** Target 100–200 lines. Instruction adherence degrades with
> file length and with conversation length. A 600-line CLAUDE.md is a file the agent
> stops following at turn 40. Every line must earn its place by having changed some
> agent behavior at least once.
>
> **Volatility discipline.** CLAUDE.md holds *stable* rules. Project state, findings,
> open questions, and "what we did last session" go in PROJECT.md. If you find
> yourself editing CLAUDE.md every session, state has leaked into the wrong file.

---

## 1. Orientation

<one paragraph: what this repo is, what it is for, who the reader is>

Read before acting:
- `PROJECT.md` — current state, open claims, what is confirmed vs. asserted
- `docs/<spec>.md` — the substantive spec this code implements
- `REVIEW.md` — standing review checklist

> Keep this to pointers. Do not restate PROJECT.md here; it will drift.

## 2. Environment

```bash
# activate
source /path/to/venv/bin/activate

# the canonical commands — use these exact forms, do not improvise
<test>       # e.g. pytest -q
<lint>       # e.g. ruff check . && ruff format --check .
<typecheck>  # e.g. mypy src
<run>        # e.g. python -m pkg.entry --config ...
```

Never install packages without adding them to `pyproject.toml` in the same commit.

> This section pays for itself faster than any other. Agents burn turns rediscovering
> that the venv needs activating, or invent a plausible-but-wrong test command and
> then reason about its failure.

## 3. Hard prohibitions

Each rule states its enforcement mechanism. Rules enforced only by this file are
marked `[soft]` and are known to be unreliable.

1. **Do not <X>.** Reason: <one clause>. Enforced by: `<hook/CI job/script>`.
2. **Do not <Y>.** Reason: <one clause>. Enforced by: `[soft]`.
3. **Never claim a command succeeded without pasting its output.** Enforced by: `[soft]` —
   compensate by asking for verbatim output on anything load-bearing.

> Write prohibitions as prohibitions, not preferences. "Prefer X" gets traded away
> under pressure; "Never X" survives longer. Give the reason in the same line — a rule
> with a reason attached is followed in novel situations; a bare rule is followed only
> in the literal case.
>
> Resist relaxing a prohibition because it made a session inconvenient. The
> inconvenience is usually the rule working. If you do relax one, write down what
> guarantee you gave up.

## 4. Definition of done

A change is done when, and only when:

- [ ] The failing test that motivated it existed *before* the fix and now passes
- [ ] `<lint>`, `<typecheck>`, `<test>` all green, output pasted
- [ ] Working tree clean, no untracked files
- [ ] `PROJECT.md` updated if the change altered project state
- [ ] <domain-specific criterion>

> "Done" is the single most-abused word in agent sessions. Make it a checklist with
> observable items. Anything unobservable ("code is clean") is not a criterion.

## 5. Working protocol

**TDD contract.** Write the test first. The test must fail for the intended reason —
paste the failure. Then implement. Then paste the pass.

**Scope contract.** One change per commit. If you discover a second problem, write it
into PROJECT.md's open items; do not fix it in the same commit.

**Stop-and-ask triggers.** Stop and ask the human before:
- anything irreversible (deletion, force-push, resource termination, billing changes)
- changing a test to make it pass
- changing a metric definition, threshold, or success criterion
- widening a permission, scope, or interface to unblock yourself

> The last one is the highest-value trigger in practice. "I couldn't do X so I granted
> myself the ability to do X" is the most common way an agent silently removes a
> guarantee.

## 6. Evidence rules

Three tiers. Label claims with them:

- **Confirmed** — command run, raw output pasted in this conversation
- **Reported** — a tool or agent said so, output not shown
- **Assumed** — inferred, not checked

Never promote Reported to Confirmed by restating it. When summarizing a session,
carry the labels forward.

> This one section prevents the single most expensive failure mode in agent-driven
> work: a natural-language summary of a result becoming the project's memory of the
> result, with the actual evidence never having existed.

## 7. Scientific rules

> Include this section only in research repos. Omit for ordinary software.

- **Register before you run.** A claim is written down — statement, null, test
  statistic, decision rule, stopping rule — and committed *before* the run that
  tests it. Post-hoc test selection is not permitted.
- **The unit of work is the smallest falsifiable claim**, not the interesting claim.
  If a claim cannot be stated with a null that the data could refute, it is not yet
  an experiment; it is a research direction. Put it in PROJECT.md as a direction.
- **Every experiment ships a negative control.** A run on shuffled/permuted input must
  report null. A negative control that fires means the pipeline is broken, not that
  the finding is strong.
- **Verdicts are recomputed, never reported.** The analysis code recomputes the verdict
  from raw outputs in CI. An agent's stated conclusion is not the verdict.
- **Declare the frame.** Each experiment names the representation and measurement it
  assumes. A null result under one frame is not a null result simpliciter.
- **Do not modify a metric to rescue a result.** See stop-and-ask triggers.

## 8. Conventions

<naming, layout, commit message format, branch policy, docstring style — briefly>

## 9. Maintenance

This file holds stable rules only. Project state lives in `PROJECT.md`.
Before adding a line here, ask:
1. Did an agent actually get this wrong? (If not, don't add it.)
2. Is it stable across sessions? (If not, it belongs in PROJECT.md.)
3. Can it be enforced mechanically instead? (If yes, do that instead and note it here.)

---

## Anti-patterns

- **The wish list.** Aspirational quality language ("write elegant, maintainable
  code"). Zero behavioral effect, non-zero context cost.
- **The duplicated spec.** Restating what's in PROJECT.md or the docs. Guarantees
  a stale contradiction, and the agent has no way to know which copy is current.
- **The unenforceable guard.** "Never terminate an instance without green CI," where
  the agent holds terminate permission and CI status is something it self-reports.
- **The essay.** Long rationale paragraphs. Compress to one clause per rule.
- **State creep.** "Currently working on Pass 2." Belongs in PROJECT.md.
- **Politeness.** "Please try to..." Instructions, not requests.

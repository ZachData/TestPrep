# CLAUDE.md — challenge-01-arabic-language-features

## 1. Orientation

This folder tests whether Pythia-70M-deduped's SAE has latents that encode
"the output is Arabic script" separably from the semantic content being
expressed, by contrastive search on parallel EN/AR sentence pairs, then
ablating (suppress direction) and steering (induce direction) those latents,
each checked against a frequency/magnitude-matched random control and a
third-language specificity control. Based on ESR's ablation methodology
(source task pasted into the session that created this folder).

Read before acting:
- `PROJECT.md` — current state, the three registered claims, what's
  confirmed vs. still open.
- `config.yaml` — model/SAE/experiment parameters. `sae.release`/`sae_id`
  start as `RESOLVE_ME`; do not hand-fill them, run `00_resolve_sae.py`.

## 2. Environment

```bash
pip install -r requirements.txt

# one command, runs everything up through analysis.py in order:
./run_all.sh
```

To run or re-run a single stage instead of the whole pipeline:

```bash
# canonical run order -- each step's output feeds the next
python scripts/00_resolve_sae.py --apply     # resolves config.yaml's sae.* fields
python scripts/01_baseline.py                # go/no-go: is there AR-script signal at all?
python scripts/02_feature_search.py          # writes results/candidate_latents.json
python scripts/03_ablate_measure.py --direction suppress
python scripts/03_ablate_measure.py --direction induce
python scripts/04_matched_control.py --direction suppress
python scripts/04_matched_control.py --direction induce
python scripts/04b_specificity_control.py    # needs ablate_suppress.json to exist first
python scripts/analysis.py                   # recomputes verdicts from results/*.json
python scripts/05_heldout.py                 # optional, if time permits -- not in run_all.sh
```

No lint/typecheck configured in this repo yet. Never install a package
without adding it to `requirements.txt` in the same commit.

## 3. Hard prohibitions

1. **Never run 05_heldout.py's data before the main pipeline (00-04b) is
   finished.** Reason: contaminates the one generalization check this
   design has. Enforced by: `[soft]`.
2. **Never hand-edit files under `results/`.** Reason: they're the evidence
   trail; hand-edits break the "verdicts recomputed, not reported" rule.
   Enforced by: `[soft]`.
3. **Never write a claim ledger verdict in PROJECT.md without having run
   `analysis.py` first and copying its output.** Enforced by: `[soft]` — no
   CI exists in this repo to check this mechanically yet.
4. **Never claim a script ran successfully without pasting its output.**
   Enforced by: `[soft]`.

## 4. Definition of done

- [ ] `01_baseline.py` run, n and both condition rates pasted
- [ ] `02_feature_search.py` run, candidate latents + their frequency/magnitude logged
- [ ] `03`/`04` run for both `suppress` and `induce`, including the fluency
      ratio (not skipped to save time)
- [ ] `04b_specificity_control.py` run
- [ ] `analysis.py` run, its table pasted into PROJECT.md's Claim ledger
- [ ] `PROJECT.md` Decisions/Open questions updated if anything changed

## 5. Working protocol

**Scope contract.** One script's worth of change per commit once past the
initial scaffold. If you find a second bug, log it in PROJECT.md and fix it
separately.

**Stop-and-ask triggers**, beyond the standard ones:
- changing `arabic_regex`, `french_accent_regex`, or `top_k` after seeing
  a result
- widening `steering_scale` because the induce direction "isn't working"
- picking a different SAE layer after seeing a null result on the first one

## 6. Evidence rules

- **Confirmed** — command run, raw output pasted in conversation
- **Reported** — a tool or agent said so, output not shown
- **Assumed** — inferred, not checked

Never promote Reported to Confirmed by restating it.

## 7. Scientific rules

- **Register before you run.** All three claims (C-001, C-002, C-003) are
  already registered in PROJECT.md's Claim ledger with a null and a
  statistic, before any of them have been run.
- **The unit of work is the smallest falsifiable claim.** Each claim ledger
  row has an explicit H0 a bad result could actually hit.
- **Every experiment ships a negative control.** `04_matched_control.py`
  (frequency/magnitude-matched) and `04b_specificity_control.py` (French,
  catches the confound frequency/magnitude matching can't).
- **Verdicts are recomputed, never reported.** `analysis.py` is the only
  source of a verdict.
- **Declare the frame.** See PROJECT.md's Frame section before interpreting
  any result.
- **Do not modify a metric to rescue a result.** See stop-and-ask triggers.

## 8. Conventions

- Script numbering = execution order. `04b` sits alongside `04` because it's
  a second control on the same candidate set, not the next pipeline stage.
- Result filenames match script names (`ablate_suppress.json` from
  `03_ablate_measure.py --direction suppress`, `_heldout` suffix from `05`).
- Commit messages: `challenge-01: <what>`.

## 9. Maintenance

This file holds stable rules only. Project state lives in `PROJECT.md`.
Before adding a line here, ask: did an agent actually get this wrong, is it
stable across sessions, and can it be enforced mechanically instead?

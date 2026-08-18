# PROJECT.md — challenge-01-arabic-language-features

## Thesis

Pythia-70M-deduped's SAE latent space contains latents that encode "the
current output is Arabic script," separably from the semantic content being
expressed, and causally manipulating those latents — not a frequency- and
magnitude-matched random set — shifts the Arabic-script output rate in both
the suppression and induction directions, specifically for Arabic rather
than non-English output in general.

## Frame

- **Representation**: Pythia-70M-deduped residual-stream SAE. Layer and
  release/sae_id are resolved by `00_resolve_sae.py` at run time (not
  guessed here) and recorded in `config.yaml` and the Decisions table below
  once known.
- **Measurement**: regex Arabic-Unicode-block rate over generated
  continuations (`arabic_regex` in `config.yaml`); contrastive mean-pooled
  activation difference (AR − EN) over parallel prompt pairs for feature
  selection; French-accented-Latin-character rate for the specificity
  control.
- **Inexpressible here**: dialectal Arabic distinctions, meaning-level
  translation quality, anything about layers or SAEs other than the one
  resolved. A null result under this one layer's SAE is not a null result
  about Pythia-70M-deduped in general.
- **Alternative frames worth cross-checking**: a larger model with SAE
  coverage (e.g. Gemma via Gemma Scope) would test whether any effect found
  here is Pythia-70M-specific or general — listed under Directions, not
  attempted yet.

## Hard core

1. Model and resolved SAE are fixed for this challenge — abandoning this
   means restarting the experiment under a new Frame, not patching this one.
2. `arabic_regex` / `french_accent_regex` are fixed at registration —
   changing them after seeing a result requires a stop-and-ask per
   CLAUDE.md.
3. Feature selection is the AR-vs-EN contrastive diff in
   `02_feature_search.py`, never a Neuronpedia auto-label lookup — labels
   may be consulted afterward for narrative only (see Accepted limitations).

## Protective belt

| Date | Anomaly | Belt change | Novel prediction it makes | Prediction tested? |
|---|---|---|---|---|
| | | | | |

*(empty at registration — this is the log for any later auxiliary change,
each entry requires a novel prediction, not just an accommodation)*

## Claim ledger

| ID | Claim | Null (H₀) | Statistic / test | Frame | Reg-hash | Status | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|
| C-001 | Ablating top-K AR-diff latents on Arabic prompts reduces AR-script output rate | No greater reduction than the frequency/magnitude-matched control distribution produces | Permutation-style: fraction of 20 control draws with effect ≤ observed | see Frame | (compute at run time) | registered | e = , n tests = | open |
| C-002 | Steering the same latents on English prompts raises AR-script output rate | No greater increase than the matched control distribution produces | Permutation-style: fraction of 20 control draws with effect ≥ observed | see Frame | (compute at run time) | registered | e = , n tests = | open |
| C-003 | The AR-diff latent set is Arabic-specific, not a generic non-English detector | Ablating the set shifts French-accent rate by the same magnitude as it shifts Arabic-script rate | Paired comparison: \|French effect\| vs. \|Arabic effect\| from the same latent set | see Frame | (compute at run time) | registered | e = , n tests = | open |

Status vocabulary: `registered` → `running` → `analyzed`.
Verdict vocabulary: `open`, `refuted`, `survived` — never "proven", never "confirmed".

**Evidence budget**: α = 0.10, max tests per claim = 5, aggregation = none
needed (single test per claim as designed). Stopping rule: run once on
`pairs_train.jsonl`; the held-out rerun (`05_heldout.py`) is a separate,
explicitly-labeled generalization check, not a second bite at the same test.

## State of the world

**Confirmed** (command run, raw output seen):
- Repo scaffold (`CLAUDE_blueprint.md`, `PROJECT_blueprint.md`, this
  folder's structure) — read directly this session.

**Reported** (a tool or agent said so; output not inspected):
- Nothing yet — no pipeline script has been executed. This session wrote
  the pipeline; the user runs it locally per the designated workflow.

**Assumed** (never checked, load-bearing anyway):
- Pythia-70M-deduped has a usable residual-stream SAE available through
  `sae_lens`'s pretrained directory. Would be falsified by
  `00_resolve_sae.py` finding no match — the single biggest risk to this
  entire plan, and the first thing to check.
- Pythia-70M-deduped produces *some* detectable Arabic-script output under
  Arabic-language prompts (Pile is overwhelmingly English). Would be
  falsified by `01_baseline.py`'s go/no-go check.

## Directions

- Cross-model check (Gemma Scope) if Pythia-70M's Arabic capability is too
  weak for a meaningful baseline — blocked on: `01_baseline.py`'s result.
- Dose-response sweep over `--k` (top_k vs. top_k/2) to check the effect
  scales roughly monotonically rather than being driven by 1-2 latents —
  documented as a flag on `03`/`04`, not registered as a claim (evidence
  budget).

## Open questions and blockers

| # | Question | Blocks | Owner | What would resolve it |
|---|---|---|---|---|
| 1 | Does Pythia-70M-deduped have a usable SAE on Neuronpedia/sae_lens? | Everything past step 00 | user (local run) | `00_resolve_sae.py` output |
| 2 | Is Pythia-70M-deduped's Arabic output fluent enough to measure at all? | C-001 (suppression may be underpowered if baseline AR rate ≈ noise floor) | user (local run) | `01_baseline.py` output |

## Decisions

| Date | Decision | Rationale (one line) | Reversible? | Revisit when |
|---|---|---|---|---|
| 2026-08-17 | Use Pythia-70M-deduped over Goodfire/Ember API | Local, free, has Neuronpedia/sae_lens SAE coverage, user's preferred model | Yes — swap `config.yaml`'s `model_name` | If step 00 or 01 fails the go/no-go check |
| 2026-08-17 | Matched control is a 20-draw distribution, not a single draw | Makes "control had a real chance to fail" checkable from the output, not asserted | Yes — `n_control_draws` in config | Never, unless runtime is prohibitive |
| 2026-08-17 | Added C-003 (French specificity control) at registration, not after seeing results | Frequency/magnitude matching can't catch a "generic non-English" confound; adding it later would be a Lakatos-style degenerating move | Yes — could be dropped, but was pre-registered specifically to avoid that temptation | N/A |

## Accepted limitations

- Single 70M-scale model, single layer/SAE — nothing here generalizes to
  larger models without the cross-model check under Directions.
- Pile is English-heavy; Arabic capability at this scale may simply be too
  weak for any of C-001-C-003 to clear the evidence bar. That itself is a
  result worth reporting, not a failure to hide.
- Neuronpedia auto-labels for the selected latents are not used for
  selection and, if consulted afterward for the narrative, that will be
  flagged explicitly as descriptive, not as what drove the finding
  ("resist the label").
- Steering (induce direction) clamps latents to a fixed multiple of their
  mean firing magnitude — a simple choice, not a swept/optimized one.

## Next up

1. Run `00_resolve_sae.py --apply` — blocked by: none
2. Run `01_baseline.py`, read its go/no-go warning — blocked by: 1 (SAE
   resolution isn't required for this step, but do it first regardless)
3. Run `02_feature_search.py` — blocked by: 1
4. Run `03`/`04` for both directions, then `04b` — blocked by: 3
5. Run `analysis.py`, paste its table into the Claim ledger above — blocked by: 4
6. If time remains, `05_heldout.py` — blocked by: 5

## Glossary

- **SAE**: sparse autoencoder, trained to reconstruct a model's residual
  stream as a sparse combination of "latents."
- **Latent**: one dimension of an SAE's learned dictionary; ideally a single
  interpretable feature.
- **Ablation**: zeroing a latent's contribution before decoding, to test its
  causal effect on the model's output.
- **Steering**: clamping a latent to a chosen positive value to induce its
  associated behavior.
- **Matched control**: a control group of latents chosen to share the
  candidate set's firing frequency and magnitude, so the control could
  plausibly reproduce the effect if the candidate set weren't special.
- **AR-script rate**: fraction of generated continuations containing at
  least one Arabic-Unicode-block character.
- **Contrastive search**: selecting latents by their differential activation
  between two matched conditions (here: Arabic vs. English translations of
  the same sentence).

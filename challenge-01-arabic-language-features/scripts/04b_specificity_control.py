"""C-003, the specificity control that the frequency/magnitude-matched
control (04) cannot provide by itself.

04 asks: "is this effect bigger than random latents with the same firing
statistics?" It cannot tell you whether the candidate latents are detecting
*Arabic specifically* versus *non-English script/tokenization in general*.
This script asks that second question directly: ablate the SAME candidate
latents (found via the AR-vs-EN contrastive diff in 02) on FRENCH prompts,
and measure the effect on a French-accented-character rate. If the AR
latents suppress French output about as much as they suppress Arabic
output, they're a generic "foreign text" detector, not an Arabic-specific
one -- and the paper's own caution ("some labels read like discourse-
structure features, not detectors") applies here too.
"""
import json

from common import (
    load_config,
    load_model_and_sae,
    load_pairs,
    make_intervention_hook,
    results_path,
    run_paired,
    summarize_paired,
)


def main():
    cfg = load_config()
    model, sae = load_model_and_sae(cfg)

    pairs = load_pairs(cfg["paths"]["control_lang_pairs"])
    fr_regex = cfg["experiment"]["french_accent_regex"]
    max_new_tokens = cfg["experiment"]["max_new_tokens"]
    alpha = cfg["experiment"]["alpha"]

    cand_path = results_path(cfg, "candidate_latents.json")
    with open(cand_path) as f:
        cand_data = json.load(f)
    k = cand_data["top_k"]
    latents = [c["latent"] for c in cand_data["candidate_latents"][:k]]

    hook_fn = make_intervention_hook(sae, latents, 0.0)

    print(f"Ablating {k} AR-diff candidate latents on n={len(pairs)} French prompts...")
    records = run_paired(model, sae, pairs, "fr", max_new_tokens, fr_regex, hook_fn)
    fr_summary = summarize_paired(records, alpha)

    ar_ablate_path = results_path(cfg, "ablate_suppress.json")
    ar_effect = None
    if ar_ablate_path.exists():
        with open(ar_ablate_path) as f:
            ar_effect = json.load(f)["effect"]

    out = {
        "k": k,
        "latents": latents,
        "french_effect": fr_summary["effect"],
        "french_summary": fr_summary,
        "arabic_effect_for_comparison": ar_effect,
        "records": records,
    }

    path = results_path(cfg, "specificity_control.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"French-accent-rate effect from ablating AR-diff latents: {fr_summary['effect']:+.3f}")
    if ar_effect is not None:
        print(f"Arabic-script-rate effect from the same latents (ablate_suppress.json): {ar_effect:+.3f}")
        if abs(fr_summary["effect"]) >= abs(ar_effect) * 0.5:
            print(
                "WARNING: the French effect is at least half the size of the Arabic effect. "
                "These latents may be a generic non-English detector, not Arabic-specific. "
                "Say this in PROJECT.md rather than the Arabic-specific framing."
            )
    else:
        print("Run 03_ablate_measure.py --direction suppress first to get the Arabic effect to compare against.")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

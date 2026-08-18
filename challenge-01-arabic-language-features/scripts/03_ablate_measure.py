"""Ablate (suppress) or steer (induce) the candidate latent set and measure
the effect, paired against a no-intervention run on the same prompts.

  --direction suppress : AR prompts, candidate latents clamped to 0.
                          Expect AR-script rate to DROP if the hypothesis holds.
  --direction induce    : EN prompts, candidate latents clamped to a positive
                          value. Expect AR-script rate to RISE if it holds.

Also runs the fluency check (mean_perplexity on a fixed generic-text probe,
with vs. without the hook) so a result can be told apart from "the ablation
just broke the model." The intervention hook preserves the SAE's own
reconstruction error (see common.make_intervention_hook) specifically so
this check isolates the targeted latents' effect, not generic SAE lossiness.
"""
import argparse
import json

import numpy as np
import torch

from common import (
    load_config,
    load_fluency_probe,
    load_model_and_sae,
    load_pairs,
    make_intervention_hook,
    mean_perplexity,
    results_path,
    run_paired,
    summarize_paired,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--direction", choices=["suppress", "induce"], required=True)
    parser.add_argument("--pairs", default=None, help="override pairs file, e.g. for held-out run")
    parser.add_argument("--tag", default="", help="suffix for output filename, e.g. 'heldout'")
    parser.add_argument("--k", type=int, default=None, help="override top_k for a dose-response check")
    args = parser.parse_args()

    cfg = load_config()
    model, sae = load_model_and_sae(cfg)

    pairs_file = args.pairs or cfg["paths"]["train_pairs"]
    pairs = load_pairs(pairs_file)
    ar_regex = cfg["experiment"]["arabic_regex"]
    max_new_tokens = cfg["experiment"]["max_new_tokens"]
    alpha = cfg["experiment"]["alpha"]

    cand_path = results_path(cfg, "candidate_latents.json")
    with open(cand_path) as f:
        candidates = json.load(f)
    k = args.k or candidates["top_k"]
    latents = [c["latent"] for c in candidates["candidate_latents"][:k]]
    mean_mag = np.mean([c["magnitude"] for c in candidates["candidate_latents"][:k]])

    if args.direction == "suppress":
        field, target_value = "ar", 0.0
    else:
        field, target_value = "en", float(mean_mag * cfg["experiment"]["steering_scale"])

    hook_fn = make_intervention_hook(sae, latents, target_value)

    print(f"direction={args.direction} pairs={pairs_file} n={len(pairs)} k={k} target_value={target_value:.4f}")
    records = run_paired(model, sae, pairs, field, max_new_tokens, ar_regex, hook_fn)
    summary = summarize_paired(records, alpha)

    fluency_texts = load_fluency_probe()
    ppl_base = mean_perplexity(model, fluency_texts)
    ppl_treated = mean_perplexity(model, fluency_texts, hook_fn=hook_fn, hook_name=sae.cfg.hook_name)

    out = {
        "direction": args.direction,
        "pairs_file": pairs_file,
        "k": k,
        "latents": latents,
        "target_value": target_value,
        "alpha": alpha,
        **summary,
        "fluency": {
            "ppl_base": ppl_base,
            "ppl_treated": ppl_treated,
            "ppl_ratio": ppl_treated / ppl_base if ppl_base else None,
        },
        "records": records,
    }

    suffix = f"_{args.tag}" if args.tag else ""
    out_name = f"ablate_{args.direction}{suffix}.json"
    path = results_path(cfg, out_name)
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"n={summary['n']}  base_rate={summary['base_rate']:.3f}  treated_rate={summary['treated_rate']:.3f}  effect={summary['effect']:+.3f}")
    print(f"fluency: ppl_base={ppl_base:.3f}  ppl_treated={ppl_treated:.3f}  ratio={out['fluency']['ppl_ratio']:.3f}")
    if out["fluency"]["ppl_ratio"] and out["fluency"]["ppl_ratio"] > 1.2:
        print("WARNING: fluency perplexity rose >20% -- this ablation may not be surgical. Report this alongside the effect.")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

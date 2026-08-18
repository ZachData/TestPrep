"""The control that could fail. Draw n_control_draws random latent sets,
each matched to the candidate set on firing frequency and mean magnitude
(not just size), and rerun the same ablate/steer measurement on each.

This is stronger than ESR's own control (they ran one draw): here the
candidate set's observed effect is compared against a full null
DISTRIBUTION, so "the control had a real chance to fail" is checkable from
the output (what fraction of matched-random draws produced an effect at
least as large?) rather than asserted from a single number.
"""
import argparse
import json

import numpy as np

from common import (
    load_config,
    load_model_and_sae,
    load_pairs,
    make_intervention_hook,
    results_path,
    run_paired,
    summarize_paired,
)


def build_matched_draw(all_stats, candidate_latents, rng, bucket_size=10):
    """One control set: for each candidate latent, sample from its ~bucket_size
    nearest neighbors in (frequency, magnitude) space, excluding all candidate
    latents and anything already used in this draw."""
    cand_idx = {c["latent"] for c in candidate_latents}
    pool = [s for s in all_stats if s["latent"] not in cand_idx]
    pool_freq = np.array([s["frequency"] for s in pool])
    pool_mag = np.array([s["magnitude"] for s in pool])

    freq_std = pool_freq.std() or 1.0
    mag_std = pool_mag.std() or 1.0

    used = set()
    draw = []
    for c in candidate_latents:
        dist = ((pool_freq - c["frequency"]) / freq_std) ** 2 + ((pool_mag - c["magnitude"]) / mag_std) ** 2
        order = np.argsort(dist)
        chosen = None
        for i in order[:bucket_size]:
            latent = pool[i]["latent"]
            if latent not in used:
                chosen = latent
                break
        if chosen is None:  # bucket exhausted by prior picks in this draw; widen search
            for i in order:
                latent = pool[i]["latent"]
                if latent not in used:
                    chosen = latent
                    break
        used.add(chosen)
        draw.append(chosen)
    rng.shuffle(draw)  # matching is by construction, not by index order
    return draw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--direction", choices=["suppress", "induce"], required=True)
    parser.add_argument("--pairs", default=None)
    parser.add_argument("--tag", default="")
    parser.add_argument("--k", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config()
    model, sae = load_model_and_sae(cfg)

    pairs_file = args.pairs or cfg["paths"]["train_pairs"]
    pairs = load_pairs(pairs_file)
    ar_regex = cfg["experiment"]["arabic_regex"]
    max_new_tokens = cfg["experiment"]["max_new_tokens"]
    alpha = cfg["experiment"]["alpha"]
    n_draws = cfg["experiment"]["n_control_draws"]
    seed = cfg["experiment"]["seed"]

    cand_path = results_path(cfg, "candidate_latents.json")
    with open(cand_path) as f:
        cand_data = json.load(f)
    k = args.k or cand_data["top_k"]
    candidate_latents = cand_data["candidate_latents"][:k]
    all_stats = cand_data["all_latent_stats"]
    mean_mag = np.mean([c["magnitude"] for c in candidate_latents])

    if args.direction == "suppress":
        field, target_value = "ar", 0.0
    else:
        field, target_value = "en", float(mean_mag * cfg["experiment"]["steering_scale"])

    rng = np.random.default_rng(seed)
    draw_results = []
    print(f"Running {n_draws} matched-control draws (direction={args.direction}, k={k})...")
    for d in range(n_draws):
        latents = build_matched_draw(all_stats, candidate_latents, rng)
        hook_fn = make_intervention_hook(sae, latents, target_value)
        records = run_paired(model, sae, pairs, field, max_new_tokens, ar_regex, hook_fn)
        summary = summarize_paired(records, alpha)
        draw_results.append({"draw": d, "latents": latents, **summary})
        print(f"  draw {d:2d}: effect={summary['effect']:+.3f}")

    effects = np.array([r["effect"] for r in draw_results])
    out = {
        "direction": args.direction,
        "pairs_file": pairs_file,
        "k": k,
        "n_draws": n_draws,
        "control_effects": effects.tolist(),
        "control_effect_mean": float(effects.mean()),
        "control_effect_std": float(effects.std()),
        "draws": draw_results,
    }

    suffix = f"_{args.tag}" if args.tag else ""
    path = results_path(cfg, f"control_distribution_{args.direction}{suffix}.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\ncontrol effect distribution: mean={effects.mean():+.3f} std={effects.std():.3f}")
    print(f"Compare this to the candidate-set effect from ablate_{args.direction}{suffix}.json's 'effect' field.")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

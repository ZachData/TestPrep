"""Contrastive feature search: find SAE latents that differentially fire on
Arabic vs. English text expressing the same content.

For each parallel (en, ar) pair we run BOTH sentences through the model,
mean-pool the SAE feature activations over token positions, and average the
(ar_vec - en_vec) difference across all pairs. Because the pairs are
translations of each other, semantic content is (approximately) held
constant across the subtraction -- what's left should lean toward
script/lexical features rather than topic features. This is the "resist the
label" design choice: selection is this activation-difference procedure,
never a Neuronpedia auto-label lookup.

Also records each latent's firing frequency and mean magnitude across the
combined AR+EN token set, needed by 04_matched_control.py to build a control
group that isn't just "random latents" but "random latents that could have
produced this effect by themselves."
"""
import json

import numpy as np
import torch

from common import ROOT, load_config, load_model_and_sae, load_pairs, results_path


def pooled_feats(model, sae, text: str) -> np.ndarray:
    tokens = model.to_tokens(text)
    with torch.no_grad():
        _, cache = model.run_with_cache(tokens, names_filter=sae.cfg.hook_name)
    resid = cache[sae.cfg.hook_name]
    feats = sae.encode(resid)  # [1, seq, d_sae]
    return feats[0].mean(dim=0).cpu().numpy(), feats[0].cpu().numpy()


def main():
    cfg = load_config()
    model, sae = load_model_and_sae(cfg)
    pairs = load_pairs(cfg["paths"]["train_pairs"])
    top_k = cfg["experiment"]["top_k"]

    d_sae = sae.cfg.d_sae
    diff_sum = np.zeros(d_sae)
    all_acts = []  # for frequency/magnitude stats, flattened across all tokens, both languages

    print(f"Encoding {len(pairs)} pairs through SAE at {sae.cfg.hook_name} (d_sae={d_sae})...")
    for pair in pairs:
        ar_pooled, ar_full = pooled_feats(model, sae, pair["ar"])
        en_pooled, en_full = pooled_feats(model, sae, pair["en"])
        diff_sum += ar_pooled - en_pooled
        all_acts.append(ar_full.reshape(-1, d_sae))
        all_acts.append(en_full.reshape(-1, d_sae))

    diff_mean = diff_sum / len(pairs)
    all_acts = np.concatenate(all_acts, axis=0)  # [n_tokens_total, d_sae]

    freq = (all_acts > 0).mean(axis=0)  # fraction of tokens each latent fires on
    mag = np.where(freq > 0, all_acts.sum(axis=0) / np.maximum((all_acts > 0).sum(axis=0), 1), 0.0)

    ranked = np.argsort(-diff_mean)  # descending: fires more on Arabic first
    candidate_idx = ranked[:top_k].tolist()

    out = {
        "hook_name": sae.cfg.hook_name,
        "d_sae": int(d_sae),
        "n_pairs": len(pairs),
        "top_k": top_k,
        "candidate_latents": [
            {
                "latent": int(i),
                "diff_score": float(diff_mean[i]),
                "frequency": float(freq[i]),
                "magnitude": float(mag[i]),
            }
            for i in candidate_idx
        ],
        "all_latent_stats": [
            {"latent": int(i), "frequency": float(freq[i]), "magnitude": float(mag[i])}
            for i in range(d_sae)
        ],
    }

    path = results_path(cfg, "candidate_latents.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nTop {top_k} candidate latents (by AR-EN diff), with frequency/magnitude:")
    for c in out["candidate_latents"][:10]:
        print(f"  latent {c['latent']:5d}  diff={c['diff_score']:.4f}  freq={c['frequency']:.4f}  mag={c['magnitude']:.4f}")
    print(f"  ... ({top_k - 10} more, see {path})" if top_k > 10 else "")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()

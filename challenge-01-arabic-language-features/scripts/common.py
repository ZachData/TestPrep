"""Shared helpers for the challenge-01 pipeline. Import, don't copy-paste."""
import json
import re
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | Path = None) -> dict:
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def load_pairs(rel_path: str) -> list[dict]:
    path = ROOT / rel_path
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def results_path(cfg: dict, name: str) -> Path:
    d = ROOT / cfg["paths"]["results_dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def contains_match(text: str, pattern: str) -> bool:
    return re.search(pattern, text) is not None


def char_fraction(text: str, pattern: str) -> float:
    if not text:
        return 0.0
    hits = len(re.findall(pattern, text))
    return hits / max(len(text), 1)


def wilson_ci(successes: int, n: int, alpha: float = 0.10) -> tuple[float, float]:
    """Wilson score interval -- behaves sanely at small n, unlike normal-approx CIs."""
    from scipy.stats import norm

    if n == 0:
        return (0.0, 0.0)
    z = norm.ppf(1 - alpha / 2)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, alpha: float = 0.10, n_boot: int = 2000, seed: int = 0):
    """CI on mean(a) - mean(b) by resampling each independently."""
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        ra = rng.choice(a, size=len(a), replace=True)
        rb = rng.choice(b, size=len(b), replace=True)
        diffs[i] = ra.mean() - rb.mean()
    lo, hi = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def load_model_and_sae(cfg: dict):
    """Loads the base model and the resolved SAE. Raises with a clear message
    if 00_resolve_sae.py hasn't filled in config.yaml yet."""
    import torch
    from transformer_lens import HookedTransformer
    from sae_lens import SAE

    sae_cfg = cfg["sae"]
    if sae_cfg["release"] == "RESOLVE_ME" or sae_cfg["sae_id"] == "RESOLVE_ME":
        raise RuntimeError(
            "config.yaml's sae.release/sae_id are unresolved. Run "
            "`python scripts/00_resolve_sae.py` first -- do not hand-guess these."
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = HookedTransformer.from_pretrained(cfg["model_name"], device=device)
    sae = SAE.from_pretrained(
        release=sae_cfg["release"], sae_id=sae_cfg["sae_id"], device=device
    )
    return model, sae


def make_intervention_hook(sae, latent_indices: list[int], target_value: float):
    """Returns a transformer_lens hook_fn that sets the given SAE latents to
    `target_value` (0.0 for ablation, a positive clamp for steering) while
    preserving the SAE's own reconstruction error as an additive term.

    Preserving the error term matters: without it, "ablation effect" is
    confounded with generic SAE-reconstruction-loss damage, which is exactly
    the "did the ablation just damage the model" failure mode the challenge
    asks about. Only the targeted latents' contribution changes; everything
    else the SAE fails to capture passes through untouched.
    """
    import torch

    idx = torch.tensor(latent_indices, dtype=torch.long)

    def hook_fn(resid, hook):
        feats = sae.encode(resid)
        recon_original = sae.decode(feats)
        error = resid - recon_original
        feats_modified = feats.clone()
        feats_modified[..., idx] = target_value
        recon_modified = sae.decode(feats_modified)
        return recon_modified + error

    return hook_fn


def generate_with_hook(model, sae, prompt: str, max_new_tokens: int, hook_fn=None):
    tokens = model.to_tokens(prompt)
    fwd_hooks = [(sae.cfg.hook_name, hook_fn)] if hook_fn is not None else []
    with model.hooks(fwd_hooks=fwd_hooks):
        out = model.generate(
            tokens, max_new_tokens=max_new_tokens, do_sample=False, verbose=False
        )
    full_text = model.to_string(out[0])
    prompt_text = model.to_string(tokens[0])
    return full_text[len(prompt_text):]


def mean_perplexity(model, texts: list[str], hook_fn=None, hook_name: str = None) -> float:
    """Average per-token loss on a fixed fluency probe set, with or without an
    intervention hook active. Used as the surgicality check: if this jumps
    after ablation, the effect is a fluency effect, not a targeted one."""
    import torch

    fwd_hooks = [(hook_name, hook_fn)] if hook_fn is not None else []
    losses = []
    with torch.no_grad(), model.hooks(fwd_hooks=fwd_hooks):
        for text in texts:
            tokens = model.to_tokens(text)
            loss = model(tokens, return_type="loss")
            losses.append(loss.item())
    return float(np.mean(losses))


def load_fluency_probe() -> list[str]:
    path = ROOT / "data" / "fluency_probe.txt"
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


def run_paired(model, sae, pairs, field, max_new_tokens, regex, hook_fn):
    """For each prompt, generate with and without hook_fn active, and score
    both continuations against `regex`. Paired (same prompt, same decoding)
    so the difference isolates the intervention's effect."""
    records = []
    for pair in pairs:
        prompt = pair[field]
        base = generate_with_hook(model, sae, prompt, max_new_tokens, hook_fn=None)
        treated = generate_with_hook(model, sae, prompt, max_new_tokens, hook_fn=hook_fn)
        records.append(
            {
                "id": pair["id"],
                "prompt": prompt,
                "base_continuation": base,
                "treated_continuation": treated,
                "base_hit": contains_match(base, regex),
                "treated_hit": contains_match(treated, regex),
                "base_char_frac": char_fraction(base, regex),
                "treated_char_frac": char_fraction(treated, regex),
            }
        )
    return records


def summarize_paired(records, alpha):
    n = len(records)
    base_succ = sum(r["base_hit"] for r in records)
    treated_succ = sum(r["treated_hit"] for r in records)
    base_rate = base_succ / n if n else 0.0
    treated_rate = treated_succ / n if n else 0.0
    return {
        "n": n,
        "base_rate": base_rate,
        "base_ci": wilson_ci(base_succ, n, alpha),
        "treated_rate": treated_rate,
        "treated_ci": wilson_ci(treated_succ, n, alpha),
        "effect": treated_rate - base_rate,
    }

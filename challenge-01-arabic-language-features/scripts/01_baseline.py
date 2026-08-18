"""Baseline Arabic-script output rate, before any intervention.

Two conditions, both needed:
  ar_prompt -> continuation   (this rate is what C-001's ablation tries to LOWER)
  en_prompt -> continuation   (this rate is what C-002's steering tries to RAISE)

Does not require the SAE -- runs on the base model alone, so it's a valid
go/no-go check even if 00_resolve_sae.py hasn't found a usable SAE yet. If
the ar_prompt rate here is near the en_prompt noise floor, Pythia-70M-deduped
doesn't produce enough Arabic to make C-001 (suppression) informative, and
C-002 (induction) becomes the load-bearing claim -- see PROJECT.md's Open
questions.
"""
import json

from common import (
    ROOT,
    char_fraction,
    contains_match,
    load_config,
    load_pairs,
    results_path,
    wilson_ci,
)


def run_condition(model, pairs, field, max_new_tokens, arabic_regex):
    import torch

    from common import generate_with_hook

    records = []
    with torch.no_grad():
        for pair in pairs:
            prompt = pair[field]
            continuation = generate_with_hook(model, sae=None, prompt=prompt, max_new_tokens=max_new_tokens)
            records.append(
                {
                    "id": pair["id"],
                    "prompt": prompt,
                    "continuation": continuation,
                    "hit": contains_match(continuation, arabic_regex),
                    "char_frac": char_fraction(continuation, arabic_regex),
                }
            )
    n = len(records)
    successes = sum(r["hit"] for r in records)
    rate = successes / n if n else 0.0
    return {"n": n, "successes": successes, "rate": rate, "records": records}


def main():
    cfg = load_config()
    from common import load_model_and_sae
    import torch
    from transformer_lens import HookedTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = HookedTransformer.from_pretrained(cfg["model_name"], device=device)

    pairs = load_pairs(cfg["paths"]["train_pairs"])
    ar_regex = cfg["experiment"]["arabic_regex"]
    max_new_tokens = cfg["experiment"]["max_new_tokens"]
    alpha = cfg["experiment"]["alpha"]

    print(f"Running baseline on n={len(pairs)} pairs, both directions...")
    ar_result = run_condition(model, pairs, "ar", max_new_tokens, ar_regex)
    en_result = run_condition(model, pairs, "en", max_new_tokens, ar_regex)

    ar_ci = wilson_ci(ar_result["successes"], ar_result["n"], alpha)
    en_ci = wilson_ci(en_result["successes"], en_result["n"], alpha)

    out = {
        "n": ar_result["n"],
        "alpha": alpha,
        "ar_prompt": {"rate": ar_result["rate"], "ci": ar_ci, "successes": ar_result["successes"]},
        "en_prompt": {"rate": en_result["rate"], "ci": en_ci, "successes": en_result["successes"]},
        "ar_prompt_records": ar_result["records"],
        "en_prompt_records": en_result["records"],
    }

    path = results_path(cfg, "baseline.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\nn = {ar_result['n']}")
    print(f"AR-prompt -> AR-script rate: {ar_result['rate']:.3f}  CI({1-alpha:.0%}) = {ar_ci}")
    print(f"EN-prompt -> AR-script rate: {en_result['rate']:.3f}  CI({1-alpha:.0%}) = {en_ci}  (noise floor)")
    if ar_result["rate"] - en_ci[1] < 0.05:
        print(
            "\nWARNING: AR-prompt rate is within ~5pt of the EN-prompt noise-floor CI. "
            "C-001 (suppression) is likely underpowered at this n. Consider C-002 "
            "(induction) as primary, and say so explicitly rather than reporting "
            "a suppression number the CI can't support."
        )
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()

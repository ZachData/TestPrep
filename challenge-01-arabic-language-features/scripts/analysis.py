"""Recompute verdicts from raw results/*.json. Per CLAUDE.md's evidence
rules, this is the ONLY place a verdict is allowed to come from -- an
agent's or human's stated conclusion in conversation is not the verdict.

Prints a markdown table matching PROJECT.md's Claim ledger columns and
writes it to results/claim_ledger_recomputed.md. Copy that table into
PROJECT.md by hand (deliberately not auto-written into PROJECT.md itself --
that file also holds hand-authored sections this script has no business
touching).
"""
import json

import numpy as np

from common import load_config, results_path


def load_json(cfg, name):
    path = results_path(cfg, name)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def permutation_p(observed_effect, control_effects, direction):
    control_effects = np.asarray(control_effects)
    if direction == "suppress":  # predicted effect is negative
        return float((control_effects <= observed_effect).mean())
    else:  # induce: predicted effect is positive
        return float((control_effects >= observed_effect).mean())


def verdict_directional(effect, direction, p, alpha, fluency_ratio, n):
    if n < 20:
        return "open", f"n={n} is small; CI likely swallows any point estimate"
    predicted_sign_ok = (effect < 0) if direction == "suppress" else (effect > 0)
    if not predicted_sign_ok:
        return "refuted", "effect ran opposite the predicted direction"
    if fluency_ratio is not None and fluency_ratio > 1.2:
        return "open", f"fluency ppl ratio {fluency_ratio:.2f} > 1.2 -- ablation may not be surgical"
    if p < alpha:
        return "survived", f"p={p:.3f} < alpha={alpha}, control distribution did not produce this"
    return "open", f"p={p:.3f} >= alpha={alpha}, matched control could plausibly explain this"


def analyze_direction(cfg, direction, alpha):
    ablate = load_json(cfg, f"ablate_{direction}.json")
    control = load_json(cfg, f"control_distribution_{direction}.json")
    if ablate is None or control is None:
        return None, f"missing results for {direction} -- run 03 and 04 first"

    effect = ablate["effect"]
    p = permutation_p(effect, control["control_effects"], direction)
    fluency_ratio = ablate["fluency"]["ppl_ratio"]
    verdict, reason = verdict_directional(effect, direction, p, alpha, fluency_ratio, ablate["n"])
    return {
        "n": ablate["n"],
        "effect": effect,
        "p": p,
        "fluency_ratio": fluency_ratio,
        "control_mean": control["control_effect_mean"],
        "control_std": control["control_effect_std"],
        "verdict": verdict,
        "reason": reason,
    }, None


def analyze_specificity(cfg, alpha):
    spec = load_json(cfg, "specificity_control.json")
    if spec is None:
        return None, "missing results/specificity_control.json -- run 04b first"
    ar_effect = spec["arabic_effect_for_comparison"]
    fr_effect = spec["french_effect"]
    n = spec["french_summary"]["n"]
    if ar_effect is None:
        return None, "arabic_effect_for_comparison missing -- run 03 --direction suppress first"
    if n < 20:
        verdict, reason = "open", f"n={n} is small for the specificity comparison"
    elif abs(fr_effect) >= abs(ar_effect) * 0.5:
        verdict, reason = "refuted", "French effect is at least half the Arabic effect -- likely a generic non-English detector"
    else:
        verdict, reason = "survived", "French effect is much smaller than the Arabic effect -- consistent with Arabic-specificity"
    return {
        "n": n,
        "arabic_effect": ar_effect,
        "french_effect": fr_effect,
        "verdict": verdict,
        "reason": reason,
    }, None


def main():
    cfg = load_config()
    alpha = cfg["experiment"]["alpha"]

    rows = []
    suppress, err = analyze_direction(cfg, "suppress", alpha)
    rows.append(("C-001", "Ablating top-K AR-diff latents on Arabic prompts reduces AR-script rate beyond matched control", suppress, err))

    induce, err = analyze_direction(cfg, "induce", alpha)
    rows.append(("C-002", "Steering the same latents on English prompts raises AR-script rate beyond matched control", induce, err))

    spec, err = analyze_specificity(cfg, alpha)
    rows.append(("C-003", "The latent set is Arabic-specific, not a generic non-English detector", spec, err))

    lines = ["| ID | Claim | n | Effect | p (vs. control) | Verdict | Note |", "|---|---|---|---|---|---|---|"]
    print("\n=== Recomputed claim ledger ===\n")
    for cid, claim, result, err in rows:
        if result is None:
            print(f"{cid}: {err}")
            lines.append(f"| {cid} | {claim} | - | - | - | open | {err} |")
            continue
        n = result["n"]
        if cid == "C-003":
            effect_str = f"AR={result['arabic_effect']:+.3f} FR={result['french_effect']:+.3f}"
            p_str = "-"
        else:
            effect_str = f"{result['effect']:+.3f}"
            p_str = f"{result['p']:.3f}"
        verdict = result["verdict"]
        reason = result["reason"]
        print(f"{cid}  n={n}  {effect_str}  verdict={verdict}  ({reason})")
        lines.append(f"| {cid} | {claim} | {n} | {effect_str} | {p_str} | {verdict} | {reason} |")

    out_path = results_path(cfg, "claim_ledger_recomputed.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {out_path} -- copy this table into PROJECT.md's Claim ledger by hand.")


if __name__ == "__main__":
    main()

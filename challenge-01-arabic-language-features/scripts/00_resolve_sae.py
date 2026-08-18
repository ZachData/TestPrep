"""Resolve a real sae_lens release/sae_id/layer for pythia-70m-deduped and
write it into config.yaml.

This deliberately does NOT hardcode a guessed release string: sae_lens's
pretrained-SAE directory has moved between module paths across versions, and
a wrong hardcoded id would fail silently-ish (wrong layer, wrong SAE) rather
than loudly. This script introspects the *installed* sae_lens instead, and
if it can't, it fails with exact manual-resolution instructions rather than
guessing on your behalf.

Run this first, before anything else in the pipeline.
"""
import argparse
import sys

import yaml

from common import ROOT, load_config


def find_directory_fn():
    """sae_lens has relocated this helper across versions. Try known paths."""
    candidates = [
        ("sae_lens.loading.pretrained_saes_directory", "get_pretrained_saes_directory"),  # v6+
        ("sae_lens.toolkit.pretrained_saes_directory", "get_pretrained_saes_directory"),  # pre-v6
        ("sae_lens", "get_pretrained_saes_directory"),
        ("sae_lens.pretrained_saes_directory", "get_pretrained_saes_directory"),
    ]
    for module_name, fn_name in candidates:
        try:
            mod = __import__(module_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name)
            return fn, module_name
        except (ImportError, AttributeError):
            continue
    return None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-substring",
        default="pythia-70m",
        help="substring to match against each release's declared model name",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the resolved release/sae_id/layer into config.yaml. "
        "Without this flag the script only prints candidates.",
    )
    args = parser.parse_args()

    try:
        import sae_lens

        print(f"sae_lens version: {getattr(sae_lens, '__version__', 'unknown')}")
    except ImportError:
        print("sae_lens is not installed. Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    directory_fn, found_at = find_directory_fn()
    if directory_fn is None:
        print(
            "Could not find sae_lens's pretrained-SAE directory helper under any "
            "known import path in your installed version. Resolve manually:\n"
            "  1. Run: python -c \"import sae_lens; print([a for a in dir(sae_lens) "
            "if 'pretrain' in a.lower() or 'director' in a.lower()])\"\n"
            "  2. Or browse https://www.neuronpedia.org/pythia-70m-deduped for "
            "available SAE sets, then cross-reference the release/sae_id names "
            "against sae_lens's documentation for your installed version.\n"
            "  3. Edit config.yaml's sae.release / sae.sae_id / sae.layer by hand "
            "once you have real values -- do not leave RESOLVE_ME in place.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Found directory helper at: {found_at}.{directory_fn.__name__}")
    directory = directory_fn()

    matches = []
    for release_id, entry in directory.items():
        model = getattr(entry, "model", None) or (entry.get("model") if isinstance(entry, dict) else None)
        if model and args.model_substring in str(model):
            sae_map = getattr(entry, "saes_map", None) or (
                entry.get("saes_map") if isinstance(entry, dict) else {}
            )
            matches.append((release_id, model, sae_map))

    if not matches:
        print(
            f"No releases found matching model substring '{args.model_substring}'. "
            "Either pythia-70m-deduped isn't in this sae_lens version's directory "
            "yet, or the model name is spelled differently upstream. Print the "
            "full directory's model names with:\n"
            "  python -c \"from sae_lens.toolkit.pretrained_saes_directory import "
            "get_pretrained_saes_directory as d; print(sorted({v.model for v in "
            "d().values()}))\"\n"
            "and pick the closest match by hand.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\nFound {len(matches)} candidate release(s):\n")
    residual_candidates = []
    canonical_releases = []  # release_id ends in "-res-sm": hand-curated, not a sweep
    for release_id, model, sae_map in matches:
        print(f"  release: {release_id}  (model={model}, {len(sae_map)} sae_ids)")
        for sae_id in list(sae_map.keys())[:20]:
            tag = " <- residual stream" if "resid" in sae_id else ""
            print(f"      sae_id: {sae_id}{tag}")
        if len(sae_map) > 20:
            print(f"      ... ({len(sae_map) - 20} more)")
        for sae_id in sae_map:
            if "resid" in sae_id:
                residual_candidates.append((release_id, sae_id))
        if release_id.endswith("-res-sm"):
            canonical_releases.append((release_id, sae_map))

    if not args.apply:
        print(
            "\nDry run only (no --apply). Pick a residual-stream sae_id from the "
            "list above -- prefer a middle layer over the first/last -- and either:\n"
            "  a) rerun with --apply if exactly one residual candidate makes sense, or\n"
            "  b) edit config.yaml's sae.release / sae.sae_id / sae.layer by hand."
        )
        return

    # Prefer the one hand-curated "-res-sm" release over sweep/trainer-variant
    # noise (sae_bench_*_sweep_* releases repeat the same layer dozens of
    # times under different __trainer_N variants -- not a real choice).
    if len(canonical_releases) == 1:
        release_id, sae_map = canonical_releases[0]
        layered = []
        for sae_id in sae_map:
            if sae_id.endswith("hook_resid_post") and "blocks." in sae_id:
                layered.append((int(sae_id.split(".")[1]), sae_id))
        if layered:
            layered.sort()
            mid_layer, sae_id = layered[len(layered) // 2]
            cfg_path = ROOT / "config.yaml"
            cfg = load_config(cfg_path)
            cfg["sae"]["release"] = release_id
            cfg["sae"]["sae_id"] = sae_id
            cfg["sae"]["layer"] = str(mid_layer)
            with open(cfg_path, "w") as f:
                yaml.safe_dump(cfg, f, sort_keys=False)
            print(
                f"\nExactly one canonical residual release found ({release_id}). "
                f"Auto-picked the middle layer ({mid_layer} of "
                f"{[l for l, _ in layered]}) to avoid an arbitrary first/last-layer "
                f"choice. Wrote release={release_id}, sae_id={sae_id}, "
                f"layer={mid_layer} to config.yaml.\n"
                "Log this pick in PROJECT.md's Decisions table."
            )
            return

    print(
        f"\n{len(residual_candidates)} residual-stream candidates found across "
        f"{len(matches)} releases, and no single unambiguous canonical "
        "'-res-sm' release to auto-pick a layer from -- refusing to guess. "
        "Edit config.yaml by hand (sae.release / sae.sae_id / sae.layer), "
        "picking a middle layer from a coherent release, then note the "
        "choice in PROJECT.md's Decisions table.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()

"""If you finish early: rerun the suppress/induce measurement and matched
control on data/pairs_heldout.jsonl, using the SAME candidate latents found
in 02_feature_search.py (no refitting on held-out data). This is what
distinguishes "the effect generalizes" from "we found latents that fit the
26 sentences we searched over" -- ESR's own Appendix A.3.5 check.

Thin wrapper over 03/04 with --pairs/--tag set; no new logic, so there's
nothing here to drift out of sync with the main pipeline.
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
HELDOUT_PAIRS = "data/pairs_heldout.jsonl"


def run(args):
    print(f"\n$ python {' '.join(args)}")
    subprocess.run([sys.executable, *args], cwd=SCRIPTS_DIR, check=True)


def main():
    for direction in ["suppress", "induce"]:
        run(["03_ablate_measure.py", "--direction", direction, "--pairs", HELDOUT_PAIRS, "--tag", "heldout"])
        run(["04_matched_control.py", "--direction", direction, "--pairs", HELDOUT_PAIRS, "--tag", "heldout"])
    print("\nDone. See results/*_heldout.json. Compare effect sizes to the train-set runs in PROJECT.md.")


if __name__ == "__main__":
    main()

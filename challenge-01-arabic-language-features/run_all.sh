#!/usr/bin/env bash
# Runs the main pipeline (everything except 05_heldout.py, which is the
# "if you finish early" check and must not touch held-out data before this
# finishes -- see CLAUDE.md's hard prohibition #1).
set -e
cd "$(dirname "$0")"

step() { echo; echo "=== $* ==="; }

step "00 resolve SAE"
python scripts/00_resolve_sae.py --apply

step "01 baseline"
python scripts/01_baseline.py

step "02 feature search"
python scripts/02_feature_search.py

step "03 ablate: suppress"
python scripts/03_ablate_measure.py --direction suppress

step "03 ablate: induce"
python scripts/03_ablate_measure.py --direction induce

step "04 matched control: suppress"
python scripts/04_matched_control.py --direction suppress

step "04 matched control: induce"
python scripts/04_matched_control.py --direction induce

step "04b specificity control"
python scripts/04b_specificity_control.py

step "analysis"
python scripts/analysis.py

echo
echo "Done. results/claim_ledger_recomputed.md has the table to paste into PROJECT.md."
echo "If time permits: python scripts/05_heldout.py"

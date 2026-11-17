# BDL hitter projections (OBP / SLG) — built Nov 2026

Pipeline (run in order from this folder):
1. `scripts/pull.py`        raw pulls: FanGraphs MLB batting 2012-26 (incl. Statcast columns), 2nd-half splits, MiLB batting by level,
                            preseason Steamer/ZiPS history (`/api/projections?type=steamer_YYYY`), Savant custom/expected/sprint leaderboards.
                            Savant park-factor pages (svpf_*.html) were pulled with curl; see build_data.py for the URLs' shape.
2. `scripts/build_data.py`  -> data/mlb.pkl, mlb_h2.pkl, milb.pkl, proj.pkl, pf.pkl
3. `scripts/features.py`    -> data/T.pkl: one row per (player, target season) holding only prior-season inputs (lags 1-3), MiLB lines, age, parks
4. `scripts/stage1.py`      -> data/stage1.json: per-stat year decay + regression constant (tuned on target seasons <= 2021 only)
5. `scripts/final.py`       walk-forward backtest vs Steamer/ZiPS (out/backtest_log.txt, out/backtest_summary.csv), fits 2016-26 and projects 2027
6. `scripts/export2027.py`  -> out/bdl_projections_2027.csv

Model: ~40 regressed "talent" composites (outcomes + Statcast contact quality, swing decisions, speed), last-season-only versions of 13 of them,
MiLB composites by level (AAA / AA / A-ball) scaled by how little MLB history a hitter has, age terms, new and old park factors, handedness.
Ridge regression (alpha 300 on standardized inputs), separately for OBP and SLG relative to league, weighted by playing time.
Tested and left out: gradient-boosting layer, component (BB/K/HR/BABIP) build-up, 2nd-half splits, bat-tracking inputs (too few seasons).
exp1-3.py are the experiment scripts behind those calls. out/coefficients_per_sd.csv = final coefficients (points per SD of input).

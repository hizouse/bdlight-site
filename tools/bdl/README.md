# BDL hitter projections (OBP / SLG) — built Nov 2026

Pipeline (run in order from this folder):
1. `scripts/pull.py`        raw pulls: FanGraphs MLB batting 2012-26 (incl. Statcast columns), 2nd-half splits, MiLB batting by level,
                            preseason Steamer/ZiPS history (`/api/projections?type=steamer_YYYY`), Savant custom/expected/sprint leaderboards.
                            Savant park-factor pages (svpf_*.html) were pulled with curl; see build_data.py for the URLs' shape.
2. `scripts/build_data.py`  -> data/mlb.pkl, mlb_h2.pkl, milb.pkl (keeps FanGraphs' org+level Team field), proj.pkl, pf.pkl
2b. `scripts/milb_pf_map.py` -> data/milb_pf_map.csv: org + level + season -> affiliate's 1-yr MiLB park factors (from the Baseball projections Project's milb_park_factors build)
3. `scripts/features.py`    -> data/T.pkl: one row per (player, target season) holding only prior-season inputs (lags 1-3), MiLB lines, age, parks
4. `scripts/stage1.py`      -> data/stage1.json: per-stat year decay + regression constant (tuned on target seasons <= 2021 only)
5. `scripts/final.py`       walk-forward backtest vs Steamer/ZiPS (out/backtest_log.txt, out/backtest_summary.csv), fits 2016-26 and projects 2027
6. `scripts/export2027.py`  -> out/bdl_projections_2027.csv

Model: ~40 regressed "talent" composites (outcomes + Statcast contact quality, swing decisions, speed), last-season-only versions of 13 of them,
MiLB composites by level (AAA / AA / A-ball) scaled by how little MLB history a hitter has, age terms, new and old park factors, handedness.
Ridge regression (alpha 300 on standardized inputs), separately for OBP and SLG relative to league, weighted by playing time.
Tested and left out: gradient-boosting layer, component (BB/K/HR/BABIP) build-up, 2nd-half splits, bat-tracking inputs (too few seasons).
exp1-3.py are the experiment scripts behind those calls. out/coefficients_per_sd.csv = final coefficients (points per SD of input).

MiLB park adjustment (Nov 18, 2026; features.py, on by default, BDL_MILB_PARK=0 disables): each MiLB line neutralized for half its affiliate's
1-yr regressed park factor. Backtest: flat for established hitters; hitters with <300 MLB PA in prior 3 yrs (150+ PA) OPS RMSE 86.46 -> 86.25.

## Updating the site after a new BDL run
    python tools/bdl/refresh_projections.py . path/to/data/proj2027_raw.pkl "Nov 18"
Refreshes Projections (BDL, Blend, Δ, Rk), 2027 Rankings and FT Hitters (OBP/SLG/OPS, Adj OPS, VORP 20, ranks), and the FT poach board
(rebuild_board.py) in one pass. Matches site rows through bdl_site_values.csv (the BDL values currently on the site), then rewrites it.
rebuild_board.py prints NEW QUALIFIER for any hitter who newly makes the board; add his name/fWAR/age to its ADD dict and rerun.

## Site layout (Nov 20, 2026)
Hitter projections moved from the Scoresheet section to MLB: `projections_h.html` ("BDL H Projections"; Scoresheet wording removed).
`scoresheet_projections.html` is now a redirect stub. The Scoresheet range/catcher page (`scoresheet_defense.html`) has its own
"Defense" tab in the Scoresheet nav. `refresh_projections.py`, `rebuild_board.py`, and `build_defense.py` use the new file names;
`blend_site.py` is the historical Nov 16 migration (don't rerun).

## Pitcher ERA page (BDL P Projections)
    python tools/bdl/build_pitching_page.py . "Nov 20"
Builds `projections_p.html` from `tools/bdl/pitching/bdl_pitcher_era_2027.csv` and `team_defense_2027.csv`, which come from
`pitching/project2027.py` (Baseball projections Project, pitching_era_study: Steamer ERA + Stuff+/Location+ + shrink toward average +
projected team DRS from FanGraphs Depth Charts). To refresh after roster moves: rerun project2027.py with fresh FanGraphs pulls, copy the
two CSVs here, rerun build_pitching_page.py.

# Experimental player-credit site preview

**Status:** built static research preview; focused local Chrome visual and interaction review completed 2026-11-13. It is not validated player impact, a finalized formula, or FutWAR WAR.

**Research note updated:** 2026-11-13, with paired fixed-penalty and expanding-window tuning sensitivity checks.

**Keeper release gate — 2026-11-13:** The tracked explorer bundle already contains 1,662 keeper metric overlays, but their source-version comparability and reuse status remain unresolved. An earlier local WAR payload contained 834 keeper credit rows and was not deployed. `scripts/package_war_prototype_for_site.py` now filters keeper credit rows and records them as withheld. The current local payload was rebuilt and audited: 10,677 outfield scores, zero keeper scores, 834 keeper rows recorded as withheld, and 69,714 team-proxy references. It has not been deployed. Keep the separate keeper scale unavailable until source and measurement gates are reviewed.

**Comparison-label clarification — 2026-11-13:** The three team-based comparison views are labeled “same-team squad proxy” throughout the player page. They use season-start roster links and known FIFA/EA in-game wages, with candidate exposure filtered using minutes from the same season. This is a retrospective internal-squad sensitivity proxy; it does not establish real salary, club budget, actual availability, or a feasible replacement. Unknown-cost candidates remain excluded, and neither the exposure cutoff nor pool summary is finalized.

**Focused UI follow-up — 2026-11-13:** Combined-season review of Paulo Dybala showed Juventus's white J mark disappearing on the standard white crest tile beside Roma. The crest renderer now gives Juventus's white mark a dark backing; the local preview was rebuilt and visually confirmed in both the combined-club strip and profile layout. This display-only adjustment does not change source art or research data, and has not been deployed.

## What the player page shows

The Value tab's experimental expected-points proxy selector loads `site/futwar-war-prototype.json.gz` on demand. It shows the selected player-season's model-association credit, a chart for the selected comparison and season scope, and a season table for all six views:

1. All-five-league average, position locked
2. All-five-league average, any listed outfield position
3. Selected-league average, position locked
4. Selected-league average, any listed outfield position
5. Same-team squad proxy, position locked
6. Same-team squad proxy, any listed outfield position

Each season row reports the experimental difference per 90, a season-total proxy value, eligible peer-row count, and an availability note. Team pools with fewer than five candidate rows are flagged as sparse; five is only a display warning, not an approved eligibility cutoff. The CSV export includes the same flag. The page reports the number of available views out of six, but does not combine them into a player score. The league checkboxes default to the selected player's current league and can be changed to include other leagues. This keeps the league view distinct from the all-five view by default. Team-pool controls compare the 300, 600, and 900-minute retrospective exposure cutoffs and the median versus minutes-weighted-mean candidate summary.

Goalkeeper model outputs remain a distinct scale and are excluded from the current site preview under the keeper release gate; any-position keeper results are also unavailable because cross-position calibration is unresolved. Team-wage comparisons use same-team season-start roster candidates with known FIFA/EA in-game wage multiplied by 52. These values are not real salaries, actual budget limits, or evidence the player was available. The wage-backed team views stop at 2023–24 because the current 2024–25 FC25 roster data do not include wages.

## Payload audit

Run from the repository root in PowerShell to rebuild the season-start roster layer, local explorer bundle, experimental player credits, and compressed site payload, then rerun the audits:

```powershell
.\scripts\rebuild_war_preview.ps1
```

This command needs the locally stored ignored roster extracts and Reep bridge files; it checks those inputs before writing any derivatives. It does not modify raw inputs, commit, or deploy. To audit an already-built preview without rebuilding, use `py scripts\audit_war_site_preview.py` and `py scripts\audit_step5_comparison_coverage.py`.

The 2026-11-13 research-credit audit found 11,511 unique player-season credits, all linked to rows in the explorer library; 10,677 are outfield and 834 are goalkeeper. After excluding a reviewed FC25 namesake mismatch (Lille midfielder André Gomes linked to a different Benfica goalkeeper), 10,120 research rows have a linked season-start comparison position and 1,391 can show raw experimental credit but are withheld from position-based comparisons. The underlying source rows and raw statistics are unchanged. The six CF-only records now map to ST under the owner-approved comparison crosswalk. No scored main comparison position disagrees with the mapped season-start roster role, and no outfield/GK domain mismatches remain. All numeric source values are finite. The current local Vercel payload retains the 10,677 outfield rows only; the 834 keeper credits are recorded as withheld. Its 69,714 team sensitivity rows cover 2021–22, 2022–23, and 2023–24, with both scopes, all three cutoffs, and both summary methods. There are no goalkeeper comparisons or 2024–25 team-wage comparisons. The current gzip payload is 2,111,180 bytes. See [the reviewed roster-link correction](game_roster_position_panel.md#player-season-link-and-explorer-display-2026-11-02).

Rebuild and check the complete static bundle:

```powershell
py scripts\package_explorer.py
py scripts\package_war_prototype_for_site.py
py scripts\audit_war_site_preview.py
.\scripts\prepare_vercel_site.ps1
node --check profile\explorer.js
git diff --check
```

### Six-view availability audit

Run `py scripts\audit_step5_comparison_coverage.py` to count eligible scored player-seasons against actually available baseline rows. The audit currently finds all-five average and selected-league average rows for 100% of eligible supported-position cohorts. The team-squad wage proxy is available for 59.1% of position-locked and 64.3% of flexible cohorts under the display-default 600-minute/median setting. Its coverage is 76.8–79.7% for locked outfield records and 82.0–83.8% for flexible outfield records in 2021–22 through 2023–24; it is unavailable for all 2024–25 records because the current season-start roster input lacks wages. Locked goalkeeper team pools have a median of one candidate, and outfield locked pools have a median of three, so row availability does not mean the candidate cohort is stable or truly affordable. The audit separately identifies one outfield-stat record with a goalkeeper roster role; the browser withholds its comparisons. Following the owner's decision, all 353 source CF positions among scored records map to ST by default; in six CF-only rows that supplies the sole comparison role. Where CF and ST both appear in the same source list, mapped duplicates collapse (110 such rows); no CAM role is inferred without evidence that the player was positioned behind a striker. This is a comparison crosswalk, not source or match-role proof. These are data-availability rates, not model-performance or validity rates. Aggregate CSV/JSON outputs remain under ignored `reports/war_prototype/comparison_coverage/`.

The owner-approved Python 3.13 executable may be called directly if the Windows `py` launcher cannot find the installed interpreter.

### Same-name peer-exclusion sensitivity

Run `py scripts\audit_war_peer_identity_exclusion.py` to compare the old average-reference calculation (exclude only the selected record ID) with the browser's conservative rule (exclude all exact normalized-name rows in that season). The audit uses minutes-weighted references and the player's own listed league for its league-average sensitivity. It writes aggregate output only under `reports/war_prototype/peer_identity_exclusion/`.

In the current 2021–22 to 2024–25 score set, the rule affects 1,098 position-locked all-five comparisons and 1,105 flexible all-five comparisons; 592 position-locked and 585 flexible own-league comparisons change. The median reference shift is zero because most player-seasons are unaffected. The 95th-percentile absolute shift is at most 0.00008 association units per 90 for locked comparisons and 0.00002 for flexible comparisons; the largest shift is 0.01854 in the own-league locked group. This is a small numerical sensitivity check, not evidence that the names are verified identities or that the player credits are valid.

### Training-history sensitivity

Run `py scripts\audit_step5_training_history_sensitivity.py` to refit each 2021–22 through 2024–25 scoring-season model after omitting each available prior training season in turn. The current audit contains 44 refits with the regularization setting reselected, paired refits holding the full-history setting fixed, and a comparison with expanding-window versus grouped cross-validation for penalty selection. This checks training-history and tuning-method sensitivity; it does not validate player impact or select a formula.

With regularization reselected, omitting 2019–20 from the 2023–24 fit yields Spearman rank correlation 0.758 and changes 18.2% of comparable outfield credit signs; for 2024–25, rank correlation falls to 0.520 and 29.2% of signs change. However, the selected ridge penalty changes from 10 to 0.1 in both cases. Holding it fixed at 10, the 2023–24 rank correlation is 0.992 with 4.6% sign changes; for 2024–25 it is 0.996 with 3.6% sign changes and a 95th-percentile absolute credit shift of 0.022 association units. This indicates that most of the large apparent instability in those folds comes from the penalty retuning, not simply from removing that season's observations. It still exposes an important weakness: penalty selection is highly sensitive to the limited season history, so the regularized player credits are not ready to interpret as stable player value. The goalkeeper rankings are comparatively stable across these refits, while some keeper credit magnitudes still shift. This does not establish that 2019–20 is erroneous or should be excluded; COVID-era seasons remain in scope for inspection unless the owner decides otherwise.

As another tuning check, the script compares the existing grouped cross-validation with an expanding-window approach that only validates on a season using earlier seasons for training. The outfield-selected penalty differs for the 2021–22 fold (10 versus 1), where the credit ranks correlate at 0.956 and 5.3% of signs differ. For 2022–23 through 2024–25, both methods choose 10 and the allocations have identical ranks and signs in this dataset. The keeper penalty differs (1 versus 0.1) in each fold, but credit rank correlations remain above 0.9999 with no sign changes. The expanding-window comparison is a limited diagnostic with few historical folds; it is not enough evidence to designate one tuning method as correct.

The default coefficient fit uses all prior seasons available to each scoring fold, so these figures are sensitivity diagnostics, not an alternate published score. The comparison with fixed penalty is a diagnostic only and is not an endorsed replacement tuning rule. Do not present the default score's rank or sign as stable player value. The site preview should keep the experimental label and avoid player rankings until the model-tuning, player-level validation, and uncertainty work is completed. Detailed fold results and aggregate JSON/CSV are generated under the ignored `reports/war_prototype/training_history_sensitivity/` directory.

### Conditional player-credit uncertainty

Run `py scripts\audit_step5_cluster_bootstrap_uncertainty.py --replicates 1000` to resample whole league-season blocks from each target season's earlier training data while holding the selected penalty fixed. The resulting player intervals quantify one narrow source of uncertainty: how the fitted association coefficients move under resampled training blocks, conditional on the current features, position/domain labels, identity links, model form, and selected penalty. They do not include uncertainty in those inputs, unmeasured confounding, player attribution, replacement choice, or causal player impact. Keep the detailed intervals in ignored local reports; they are a model diagnostic, not a site-facing player score or ranking.

The 1,000-resample audit covers 2,642–2,705 outfield player-seasons and 203–215 goalkeeper player-seasons in each scoring season from 2021–22 through 2024–25. Every player-season received all 1,000 successful coefficient fits, and the audited interval widths are finite. Outfield intervals cross zero for 36.5%, 31.0%, 40.2%, and 41.4% of rows, respectively. Median conditional 95% interval widths range from 0.090 to 0.113 association units per 90 for outfield; the 95th-percentile widths range from 0.310 to 0.406. Keeper intervals cross zero less often (0.5%–3.3%), but that only describes this narrow conditional fit distribution and does not resolve separate keeper-data and model-validity limits. Results are in ignored `reports/war_prototype/cluster_bootstrap_uncertainty/`; the script is deterministic with seed `5142026`.

Run `py scripts\summarize_step5_conditional_uncertainty.py` for league and exposure-cohort summaries. In 2024–25, 900+ minute outfield intervals cross zero in 30.4%–37.8% of records across leagues; for records below 900 minutes, the range is 46.5%–52.7%. Lower-exposure rows also have wider interval tails. The pattern is consistent with greater uncertainty at low exposure, but because this is conditional coefficient-fit uncertainty it must not be interpreted as a confidence interval for true player quality or impact. The grouped CSV is local-only and ignored.

This distinction matters because a player-level expected-points model based on on-pitch outcomes requires lineup-level adjustment for teammates and other confounders. A peer-reviewed causal plus-minus paper explicitly frames its target as a hypothetical substitution and models indirectly measured confounding; it demonstrates on soccer and basketball data. FutWAR's current multi-season proxy instead distributes regularized team-season predictive associations over player features. The paper is a useful design reference, but it does not validate this proxy or supply its weights: [De Bacco, Wang, and Blei (2024), *A causality-inspired plus-minus model for player evaluation in team sports*](https://proceedings.mlr.press/v236/bacco24a.html).

## Interpretation limits

- The per-player credit allocates regularized team-season prediction coefficients across player-level rate features. Good team prediction does not validate this individual allocation.
- The preview is not action-based, causal, or an independently validated estimate of a player's change in expected points.
- The site preview does not include player-level uncertainty intervals. A separate local bootstrap audit shows substantial conditional sign uncertainty for outfield credits; correlated inputs and unstable coefficients can change the credits.
- No credits are available for 2017–18 through 2020–21 because this run only scores seasons with prior-season training data.
- Above-average references are not replacement level. Team-pool rows are only a squad-and-game-wage proxy; position-locked pools are often too small for stable replacement estimates.
- The six views are separate comparison definitions. No combined score is calculated while the cohorts' shared scale and combination rule remain unapproved.
- For all-league and selected-league averages, the browser excludes the selected record and other rows with the same normalized name in the same season. This reduces self-comparison across club-specific stints, but is not identity proof and can conservatively exclude a namesake. Team-pool eligibility remains restricted to the selected club-season.
- Do not use the values for rankings, recruitment, player evaluation, or claims of WAR.

## Release check status

The static bundle builder, JavaScript syntax check, Python syntax checks for touched audit scripts, diff whitespace check, Vercel bundle check, and payload-to-explorer ID audit passed on 2026-11-13. The payload audit now also checks that the built HTML contains the experimental/not-WAR label, the limitations on the team wage proxy, the CF-to-ST/CAM position rule, and the non-causal interpretation. It reports same-name, same-season rows across multiple clubs so the browser's conservative peer exclusion can be reviewed. The training-history sensitivity audit completed 44 paired model refits and compared grouped with expanding-window penalty selection; the 1,000-resample conditional credit uncertainty audit and the CF-to-ST coverage audit also completed. A local Chrome review confirmed the position-scope control updates the selection label and checked both a season with no wage proxy (Dybala, 2024–25: 2/6 all-five views and 4/6 selected-league views available) and one with wage data (Dybala, Roma 2023–24: 5/6 views available; the locked team pool correctly reports zero eligible scored candidates while the flexible pool has 15). Unavailable values are explained rather than shown as zero. This was a focused interaction check, not exhaustive browser QA. Player-value validation remains open. This update was not deployed to Vercel.

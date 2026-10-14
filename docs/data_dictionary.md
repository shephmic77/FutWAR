# Initial data dictionary

The first source has been structurally audited; provenance and statistical completeness remain unverified. The following are audit conventions, not claims about source schemas.

| Semantic field | Audit use | Policy |
|---|---|---|
| league | Target competition coverage | Map explicit source labels; retain unknown labels |
| season | Target season coverage | Map explicit labels to 2017-18 through 2024-25 |
| position | Grouped missingness | Preserve source nominal position; do not infer tactical role |
| player_id | Future identity checks | Preserve provider namespace; no cross-provider matching yet |
| team_id | Future club/transfer checks | Preserve provider namespace; establish row grain first |
| minutes | Future exposure checks | Units and numeric validity unverified |

Source columns are retained under their exact header names in audit reports. A populated column is not proof of a valid statistic. Record each actual source field's definition, unit, aggregation level, provider and missingness interpretation when real files are available. Totals and per-90 measurements must remain distinguishable.

Missing cells are trimmed values matching the configured case-sensitive null tokens. Zero is retained. Rows with the wrong number of fields are flagged and excluded from column statistics. No imputation, deduplication or cleaning modifies raw data.

Coverage states distinguish observed rows, no observed rows, unresolved mappings/read errors, and no input data. Completeness is always `not_verified` until compared with independent expected coverage. The detailed stat report covers observed groups; absent target combinations appear in coverage.csv. Defining a required metric checklist awaits inspection of source definitions, without finalizing model inputs.

## First-source conventions

The supplied CSV uses semicolons and decimal commas. `season` values `1718` to `2425` are explicitly mapped to the eight canonical seasons. `league` is mapped from the five country-prefixed labels. `player` and `team` are name labels, not stable provider IDs. `pos_` contains nominal position families and mixed values; none is a verified tactical role. `Playing Time_Min` is the candidate minutes exposure column. Counts and per-90 fields coexist and must not be combined indiscriminately. Related columns may repeat measurements: eight tested pairs are numerically equal wherever both are populated. These observations do not establish provider definitions.

## Processed correction policy

The approved Torrasi/Milan/2017-18 collapse keeps unique nonblank field values and leaves `Subs_unSub` missing because the raw records disagree between 0 and 1. This is an explicit conflict null, distinct in lineage from naturally missing source cells. All 512 contributing source record numbers are preserved. Other nominal position gaps are flagged, not filled. Normalized decimal strings use a point, and league/season labels follow the audit aliases. Original column names remain unchanged.

## External field enrichment

Rutjens’s source `pos_` was blank and his processed value is now DF, mapped from the official 2017-18 Serie A squad defender category. Lineage and `futwar.reviewed_enrichments` distinguish this sourced metadata fill from the original provider data. No specific tactical role is inferred. O’Neill’s one-minute row has a flag for conflicting Opta exposure evidence; no numerical statistic has been altered.

## First exploratory metric mappings

The SQL view `futwar.player_season_eda` and the first notebook use these source totals at player-team-season grain. These are retained header mappings; exact historical provider definitions and comparability remain unconfirmed.

| View field | Original CSV header | Working interpretation and unit |
|---|---|---|
| minutes | Playing Time_Min | Recorded playing minutes at this club |
| non_penalty_goals | Performance_G-PK | Non-penalty goal count |
| npxg | Expected_npxG | Non-penalty expected goal total |
| xa | Expected_xA | Expected assist total |
| xag | Expected_xAG | Expected assisted goal total |
| progressive_passes | Progression_PrgP | Progressive pass count |
| progressive_carries | Progression_PrgC | Progressive carry count |
| tackles | Tackles_Tkl | Tackle count; do not relabel as tackles won |
| interceptions | Int_ | Interception count |

xA and xAG are distinct measures in [Sports Reference's explanation](https://info.sports-reference.com/migration/knowledge/soccer-advanced-stats-explained); that current documentation does not independently verify this CSV's historical definitions. Do not merge the columns or add them together as a contribution measure.

The notebook computes per-90 rates from these totals and recorded minutes, rather than mixing precomputed per-90 columns with totals. Individual rates use `90 * total / minutes`. Group exposure-weighted rates include only records with a known metric and positive minutes in both numerator and denominator. Zero remains a measurement; missing remains missing. The 900-minute cutoff is a user-selected exploratory display setting, not a final model rule.

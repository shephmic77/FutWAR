# FutWAR — Candidate sources and due diligence

## Public player-data distribution pause (2026-10-16)

The owner directed FutWAR to pause public distribution of the player library while upstream redistribution terms are clarified or the public dataset is replaced with explicitly reusable data. This is a precaution based on incomplete provenance, not a legal determination. The full explorer remains available locally under ignored `reports/explorer/`; the Vercel artifact contains only a holding page. Earlier owner approval for personal/student use is preserved below as project history, but it did not independently verify rights to relicense or publicly redistribute upstream records and images. On 2026-10-16, the main Git history was rewritten and pushed; a reachable-history scan found no player bundles or source-linked site assets. Existing clones or caches may still retain previous objects. See `docs/vercel_setup.md` for the current status.

## Owner's public-project use confirmation (2026-10-15)

The owner reports reviewing the terms for sources used in the public explorer and considers personal/student project use and public inclusion acceptable. This records the owner's review and intended non-commercial use; it is not independent verification of upstream rights and does not authorize commercial reuse. As of 2026-10-16, player data bundles and source-linked assets are not published: the Vercel site is a data-free holding page and those artifacts were removed from reachable Git history. Local research copies remain available. Public redistribution is paused pending source-specific provenance and reuse review or replacement by clearly reusable data. Source-specific attribution and original license claims remain recorded below.

This is a **candidate list**, not proof of complete coverage or permission to scrape/re-publish. Audit sources against all eight seasons (2017–18 to 2024–25) and five leagues before use. Record source date, file/version, license/terms and actual available fields.

| Source | Potential use | Limitations to verify |
|---|---|---|
| Kaggle: `emrey3lmaz/top-5-league-football-player-stats-2017-2025` | Historical player-season stats; user-supplied file has observed labels from 2017–18 to 2024–25 | Inspect real files, provider definitions, missing values, right to redistribute; dataset title and filenames are not evidence of complete seasonal coverage |
| Understat / `soccerdata` | Big Five npxG/xG, xA, shots and some player-match/season data | Mainly attacking; check access, seasons, match completeness and terms |
| Football-Data.co.uk | Domestic results and team match data across leagues | No detailed player performance; verify season/competition file formats |
| Sofascore or ESPN | Starting XI, nominal positions, formations, substitutions, player match statistics | Access and historical coverage are uncertain; check terms, legal acquisition and definitions |
| Historical FBref archives, including Kaggle | Passing, defensive and progression stats if actually archived | Live FBref advanced coverage changed; verify fields are not empty and don't mix provider definitions silently |
| Transfermarkt-derived Kaggle Player Scores | Matches, player appearances, clubs, transfers, squad information | Value/market price does not equal on-pitch WAR; licensing and player IDs |
| Impect Open Data | Bundesliga 2023–24 event data, player-match KPIs, lineups and substitutions | Separate terms PDF governs use; review terms, attribution/logo requirements, actual match coverage and schema before acquisition or integration; does not fill other league-seasons |
| StatsBomb Open Data | Historical candidate only; dropped by owner on 2026-10-15 | Do not register, acquire, or audit further for FutWAR; see superseded external-validation note |
| ClubElo | External cross-league club strength benchmark | API/access restrictions may apply; verify permitted methods |
| UEFA competitions | Results connecting clubs from different leagues | Strong selection bias toward better teams |

Useful methodological references (investigate, don't blindly reproduce):
- American Soccer Analysis: Points Above Replacement (PAR), Goals Added (g+), Net Goals Added.
- VAEP: Decroos et al., Valuing Actions by Estimating Probabilities.
- `kpelechrinis/eLPAR-soccer` GitHub repository (expected league points above replacement).
- Public football data pipelines and `soccerdata` documentation.

## Initial quality gate
For each source, determine:
1. Which league × season combinations are actually present?
2. Player rows and unique identifiers; teams and matches; can players transfer mid-season?
3. Definitions and units for every metric; whether totals and per-90 are mixed.
4. Missing percentages by season, league, role, and stat.
5. Availability of match-level minutes, position, opponent and team for tactical context.
6. Whether formation is known, nominal only, or absent.
7. Dataset terms and reproducible permitted acquisition.
8. How identity reconciliation between providers will be audited.

Recommendation: audit one accessible Kaggle CSV first, then target missing features with other sources rather than indiscriminately collecting everything.

## First supplied file

`Top5_League_Players_2017to2024_dataset.csv` has 22,929 rows and 178 columns, with observed labels for all five leagues and all eight scoped seasons. The user identified the [Kaggle dataset page](https://www.kaggle.com/datasets/emrey3lmaz/top-5-league-football-player-stats-2017-2025?select=Top5_League_Players_2017to2024_dataset.csv) as the original download source. Upstream provider, retrieval date, dataset version, definitions and terms remain unresolved. The indexed publisher discussion page corroborates the title and stated season span; direct data-card retrieval failed, so no license has been verified. A detailed quality report is retained locally and excluded from the public repository until source terms are verified.

## Supplied research notes: evidence policy

The additional user-supplied research notes support complementary sources: attacking data, results, lineups, cross-league ratings and a richer tactical pilot. Their claims about 2026 changes to FBref or ClubElo access, historical coverage and licensing are research leads, not currently verified facts. Before relying on them, check primary provider documentation, terms and a representative sample across the eight scoped seasons. Prefer comparable definitions across leagues; provider mixing requires explicit identity and metric reconciliation. No new downloads are authorized merely by a source appearing in a candidate list.

Additional reading lead: *Unveiling True Talent: The Soccer Factor Model for Skill Evaluation*; exact paper and methods remain to be verified. Historical eLPAR and match-prediction projects can inform methods and engineering without fixing FutWAR assumptions.

## Match-source due diligence and first acquisition

Football-Data.co.uk’s live data page restricts automated/AI use and limits its stated purposes; no match download was attempted. OpenFootball football.json was selected under its published CC0-1.0 license. A pinned snapshot covers all 40 scoped league-season files and has 14,339 base-source full-time scores. A separately verified 20-match supplement supplies the final-round scores missing from La Liga and Serie A 2024-25, for 14,359 scored matches. The 101 Ligue 1 2019-20 no-score fixtures were not played after the season ended early. See `docs/match_results_audit.md` and `data/openfootball_manifest.json` for measured coverage, terms links and acquisition provenance. Community-source counts are structural evidence, not official statistical certification.

## Official final-round score evidence

La Liga matchday 38 results and official Serie A match reports/Inter match centre supplied a narrowly reviewed factual supplement for the 20 2024-25 score gaps. Source URLs, fixture keys, verification date, hashes and original-score state are preserved separately. No open license for these official references is claimed. See `docs/verified_match_supplement.md`. Original CC0 OpenFootball files remain unchanged.

## Initial standings reference evidence

The first 2024-25 comparison uses the official Bundesliga table, indexed Premier League rows, Serie A's final points communication, Barcelona's annual report and a provisional PSG club table with conflicting season metadata. The private factual transcription and generated reports preserve source URLs, review date, checked metrics, status and hashes. No open license or complete historical certification is claimed. A separately sourced Union Berlin–Bochum awarded result illustrates that some results encode administrative decisions. See `docs/standings_and_player_identity_audit.md` for exact coverage, acquisition limitations and the player identity review queue.

## Expanded historical standings references

All 40 scoped season articles were archived through Wikipedia's public API with revision IDs, attribution, CC BY-SA 4.0 terms, timestamps and SHA-256 hashes. Actual extraction yields 780 one-to-one club-season references. Seven points deductions and two erroneous secondary points cells are separately adjudicated using primary references. See `docs/historical_standings_validation.md` and `data/wikipedia_standings_manifest.json`. Secondary agreement does not establish complete official verification or independent upstream provenance. No original match or player data were overwritten.

## Publisher player-ID and appearance source

Six downloadable dcaribou/transfermarkt-datasets CSV exports were archived privately with hashes and dates under the publisher's CC0 declaration; upstream rights remain unconfirmed and no scraping was performed. All 40 league-seasons have observed games/appearances, but 72 fixture dates differ from the existing source and transfer coverage is incomplete. Five researched identity examples are stored as a limited SQL pilot; automated candidates remain unverified. See `docs/player_identity_source_audit.md` and `data/player_identity_source_manifest.json` for exact measured coverage, evidence and reproduction.

## Replacement-candidate factual evidence

Official Leicester, Premier League, Lens and Roma pages support a four-case signing review, with a separate Leicester injury reference. The private factual ledger records URLs, publication/review dates and unknown costs, while generated outputs preserve ledger/snapshot hashes. No open license for those pages or confirmed replacement-level pool is claimed. See `docs/replacement_candidate_pilot.md`; no full articles were copied and no raw statistics changed.

An immutable-parent expansion adds Valladolid free-signing evidence, Schalke release evidence and an Everton goalkeeper case. It preserves source gaps, including an unavailable destination signing page and an undated extracted announcement. See `docs/replacement_candidate_expansion.md`. Historical match positions and detailed keeper statistics remain acquisition/audit needs under `docs/position_evidence_requirements.md`; provider profile positions and broad CSV labels do not satisfy the owner's season-frequency requirement.

## Lineup and keeper source suitability

The publisher lineup export is separately archived and hashed; 14,307 of 14,359 scoped matches have records, but played-position semantics and wingback distinctions remain unresolved. A pinned parser was inspected as evidence without executing scraping. A separate six-match lineup/position pilot exists, but it is not full-season or league-wide coverage. No keeper values were produced. Prior StatsBomb catalog/terms and pilot notes are historical only; the owner dropped that source on 2026-10-15. Do not access further StatsBomb material for this project.

The 2026-10-16 historical-label audit joined that publisher's appearance and lineup files across 14,359 matches and all 40 scoped league-season cells. It found 422,080 appearance records, with a textual lineup-position label for 420,516 (99.629%; cell range 86.9–100%). The reviewed collection code indicates these are lineup/bench table labels, not played-position time intervals; the observed vocabulary also has no wingback label. This is useful candidate coverage but cannot support the owner's main-position-by-total-minutes or 5-appearance/10% secondary-position rule. The audit made no role assignments and changed no source values; its player-level output stays local.

The official [Impect Open Data repository](https://github.com/ImpectAPI/open-data) describes Bundesliga 2023–24 events, lineups, substitutions, and per-position player KPIs with play duration. This is a possible one-cell position/event supplement, not a solution for the other 39 cells. Its repository requires users to agree to a separate `LICENSE.pdf`; that PDF has not been reviewed, so the project has not acquired or used this source. A Reddit post describing a 2015–16-to-present Big Five appearance archive provides no direct public download or stated reuse terms and says the author is considering offering the archive; it remains an unverified lead, not an available free source. No outreach was made.

The owner's broader-source search is recorded in `docs/broader_position_keeper_source_search.md`. Sportmonks and API-Football remain unsampled candidates; published fields do not establish historical completeness or actual played roles. Public Wyscout research data cover 2017-18 only by published scope, and an exact-scope goalkeeper study is an archive lead without a located replication download. No new player data, account or paid service was introduced.

Following the owner's free-only decision, six CC BY 4.0 Figshare research articles and their files were archived with versions/checksums. The [Wyscout research audit](wyscout_research_audit.md) observes 1,826 matches and 3,071,395 domestic events across 2017-18, with all 35 other target cells absent. Player profiles are broad, lineup rows lack specific roles, and post-shot xG fields were not identified. Keeper actions are available for research, with 25 missing/conflicting GK-profile links queued; no labels or statistics were merged.

Goalkeeper source work has explored archived player metrics and match-event references. Provider coverage, identity links, metric definitions/versions and reuse terms remain unresolved. Underlying keeper archives, row-level correction plans and keeper-specific results stay local; no keeper measurements are bundled in the public repository. The [explicit-license source screening](licensed_keeper_source_screening.md) summarizes candidate terms without selecting a keeper formula. The descriptive 900+ minute focus is exploratory and does not set WAR eligibility.

Historical position candidates remain publisher labels, not verified played-position minutes. Existing bounded StatsBomb position-pilot files are historical only and cannot establish complete league-season coverage. Do not pursue the pending provider inquiry or access additional StatsBomb data.

The [full explorer data audit](full_explorer_data_audit.md) documents the archived publisher valuation table, owner-selected June 30 cutoff, separate keeper overlays and image credits. The new Kaggle injury research archive is anonymized and was excluded from named-profile merging. Original statistics and unresolved upstream rights are preserved.
# Additional action-value research inputs (2026-10-10)

Football-Data public season CSVs were preserved in a separate raw archive with a source/hash manifest (`data/match_context_manifest.json`). The audit covers 14,359 fixtures across all 40 league-season cells, with 560 field-coverage rows. One Bundesliga 2024–25 fixture lacks twelve shot/corner/foul/card fields; goal fields remain present. Club identity and provider-definition joins are not yet validated. Source: [downloads](https://www.football-data.co.uk/data.php), [field definitions](https://www.football-data.co.uk/notes.txt). Public download access is not a blanket redistribution license.

Existing licensed Wyscout archives were transformed into 3,071,395 source-tag/coordinate event-feature rows. Their coverage is 2017–18 only, explicitly absent in the other 35 league-season cells. See `reports/value_research/event_input_lineage.json` and `event_feature_coverage.csv`. These are inputs, not fitted action values or newly inferred positions. The [three-baseline proposal](three_baseline_formula_proposal.md) records primary method references and remaining historical budget, availability and event-coverage gaps.

## Historical replacement-budget research (2026-10-11)

UEFA's [European Club Finance and Investment Landscape](https://ecfil.uefa.com/2024) publishes selected club financial comparisons, while its [Intelligence Centre database description](https://intellcentrecatalogue.uefa.com/club-costs-and-financial-performance/) describes curated club-by-club player/non-player wage and transfer-cost data for 700+ clubs over 15 years. This is a source lead, not a complete open download: the public report's club comparisons are selective and the underlying database is not staged in this repository.

[Capology support](https://capology.com/support/) states that salary data are estimates even when verified. Its [API plans](https://www.capology.com/pricing/api-plans/) price historical bulk access as a subscription; its [terms](https://www.capology.com/terms-and-conditions) limit ordinary site/data use to private non-commercial purposes, and its support page says API data cannot be published without an added publishing license. No Capology data were collected or transcribed. It is not a free route for a complete, reusable salary panel. Public club annual reports remain a possible source for reported wage expenses, but those often combine player and non-player wages, use different financial-year boundaries, and do not reveal the team's transfer budget or the candidates actually available at season start.

The first [event-danger prediction pilot](../reports/event_value_pilot/results.md) used the licensed five-league 2017–18 Wyscout sample. It improves held-out prediction error for rare score/concede events but estimates no player contribution. The report contains the split, exclusions, source-coordinate audit, metrics and graph lineage.

The [expected-points action-state pilot](../reports/expected_points_pilot/results.md) used the same hash-verified 2017–18 Wyscout archive. Sampled held-out events all have event-level player IDs, but those IDs have not been reconciled to the player-season records; the action-credit methods remain research options. For method provenance, see [VAEP](https://arxiv.org/abs/1802.07127), [tracking-based expected possession value](https://pmc.ncbi.nlm.nih.gov/articles/PMC8570314/), [restricted Shapley shot-action credit](https://arxiv.org/abs/2603.11016), and [possession-sequence plus-minus](https://academic.oup.com/imaman/article/36/3/593/8115468). These papers have different targets and data requirements; no coefficients or player values were imported.

The [direct versus shared shot-sequence pilot](../reports/action_credit_pilot/results.md) uses all actions in held-out 2017–18 shot-ending sequence proxies. It reports 12,581 candidate sequences and 11,693 complete-actor sequences; 888 incomplete sequences were excluded from both comparisons. Direct and equal-shared totals are identical by construction, but player ranks move. The equal split is not Shapley and outputs remain anonymous source-ID diagnostics, not WAR or reconciled player-season statistics.


# Cross-provider goal-scorer corroboration audit — 2017–18 (exception review updated 2026-11-14)

## Result

The OpenPlay event release and the CC BY 4.0 Wyscout research archive can be independently compared for the Big Five's 2017–18 season. This audit linked **all 1,826 fixtures** by league, match date, and home/away clubs. The join deliberately did not use the score. The independently compared full-time scores agreed in **1,826 of 1,826 matches**.

That result supports the fixture bridge and match-score consistency for this season. It does **not** verify player identities or all event actors.

At match level, OpenPlay's accepted goal-actor event counts equal scoreboard goal totals in 1,826/1,826 fixtures. Wyscout's scorer-tagged events do so in 1,825/1,826. The exception is Chelsea 0–1 Manchester City on 2017-09-30: OpenPlay records Kevin De Bruyne's goal at expanded minute 66, while the Premier League match record reports 67'. Wyscout has the goal outcome on Chelsea goalkeeper Thibaut Courtois's `Save attempt` row, but no scorer-tagged `Shot` row for that goal. The goalkeeper row records a conceded goal, not the scorer's identity, so it cannot be credited as a De Bruyne actor event. This explains the one scorer-event count gap without treating the full-time score as wrong ([Premier League match record](https://www.premierleague.com/en/match/918955/chelsea-vs-manchester-city/overview), [Wyscout Shot glossary](https://dataglossary.wyscout.com/shot/), [Wyscout Shot against glossary](https://dataglossary.wyscout.com/shot_against/)).

## Scorer-event comparison

| Goal-event category | OpenPlay events | Wyscout events | Exact normalized actor-name overlap | One-to-one name-variant sensitivity |
|---|---:|---:|---:|---:|
| Regular goals | 4,796 | 4,793 | 2,749 / 4,793 (57.3%) | 4,336 / 4,793 (90.5%) |
| Own goals | 151 | 153 | 94 / 151 (62.3%) | 130 / 151 (86.1%) |

The denominator is the smaller provider event total for that category. OpenPlay has three more regular-goal actor events; Wyscout has two more own-goal actor events. These are not silently reconciled. By league, the largest regular-goal exact-name gap is La Liga (182 / 994); the unique name-variant sensitivity raises this to 795 / 994. The corresponding exact/variant rates for the other leagues range from 63.1% / 92.5% to 76.4% / 94.4%. Own-goal samples are much smaller and less stable; La Liga exact/variant overlap is only 3 / 30 and 24 / 30.

The name-variant view is a **sensitivity analysis only**. Inside each match-team-category group it pairs names one-to-one when at least two name tokens can be uniquely matched, allowing a high (0.90) character similarity for a token of at least four characters. It can still create false matches, particularly in Spanish name variants and damaged text encodings. It is not a validated identity map, precision estimate, or approved event credit. No player IDs or full row-level match results are exported; the one count-level exception is described above.

## Wyscout event-to-roster integrity

Across all 3,071,395 Wyscout Big Five 2017–18 event rows, 2,845,357 have a nonzero actor ID and every one of those IDs appears in the same match and team's starters, bench, or substitution records and in the Wyscout player catalog. The remaining 226,038 rows have a zero or missing actor ID. This is **100% same-source structural linkage** for nonzero actors; it cannot detect an incorrect real-world name attached to an otherwise valid source ID.

## Goalkeeper-name overlap screen

The same fixture bridge was used for a limited keeper-name screen. It compares distinct Wyscout actor identities whose player-catalog profile role is `GK` against distinct OpenPlay match/team players listed as played `GK` with positive recorded minutes. Exact normalized names overlap for 2,577 of 3,652 OpenPlay match/team/keeper-name observations (70.6%) and in 2,577 of 3,651 match/team groups with a Wyscout goalkeeper-profile actor (70.6%). This varies sharply by league:

| League | OpenPlay match/team keeper names | Exact shared names | Share |
|---|---:|---:|---:|
| Premier League | 760 | 578 | 76.1% |
| La Liga | 760 | 162 | 21.3% |
| Serie A | 760 | 579 | 76.2% |
| Bundesliga | 612 | 578 | 94.4% |
| Ligue 1 | 760 | 680 | 89.5% |

This is **not** a keeper identity or shot-assignment validation. Wyscout's catalog role is profile metadata, not a match-specific goalkeeper stint; the two sources may also differ in event actor coverage and names. The very weak La Liga overlap shows that a name-only bridge is unsuitable as a shared validation route. No cross-source keeper IDs or shot links were created. The aggregate output is `reports/cross_provider_goal_scorer_audit/goalkeeper_profile_actor_overlap.csv` (ignored/local); the script now reproduces it with the goal-event and actor/roster checks.

## Wyscout goalkeeper-event structure screen — 2026-11-14

The source-level check reviewed every `Save attempt` event in the five Wyscout 2017–18 league files. Wyscout defines this as an on-target shot faced by a goalkeeper; tag 101 indicates a goal conceded, while the outcome can otherwise be a save ([Shot against glossary](https://dataglossary.wyscout.com/shot_against/), [Goal conceded glossary](https://dataglossary.wyscout.com/goal_conceded/)).

| League | Save-attempt rows | Nonzero actor | Actor has GK catalog role | Goal-conceded tag 101 |
|---|---:|---:|---:|---:|
| Premier League | 3,349 | 3,348 | 3,346 | 1,019 |
| La Liga | 3,410 | 3,408 | 3,407 | 1,024 |
| Serie A | 3,561 | 3,561 | 3,558 | 1,017 |
| Bundesliga | 2,811 | 2,811 | 2,807 | 856 |
| Ligue 1 | 3,436 | 3,435 | 3,427 | 1,034 |
| **Total** | **16,567** | **16,563** | **16,545** | **4,950** |

All 16,563 nonzero actor IDs occur in the same match/team's Wyscout roster. Of those, 16,545 have a goalkeeper profile role; 18 have a different profile role, and four rows have no actor ID. These are structural checks only: catalog role is not proof of the player's role or time on the field in that match, and a valid roster ID is not an independent identity check. The audit does not pair shot rows to goalkeeper outcome rows, estimate post-shot difficulty, or measure keeper skill. It creates no goalkeeper crosswalk or score. Aggregate counts are written to ignored `reports/cross_provider_goal_scorer_audit/wyscout_keeper_event_integrity.csv`.

### Match-score exception review

The per-match audit found **1,823 of 1,826** fixtures with the same number of tag-101 `Save attempt` rows and scoreboard goals, **three** with one extra tag-101 row, and none with fewer. The reproducible, match-level-only list is `reports/cross_provider_goal_scorer_audit/keeper_goal_tag_score_mismatches.csv` (ignored/local).

| Match | Scoreboard goals | Tag-101 keeper rows | Sequence/source review |
|---|---:|---:|---|
| West Ham–Watford, 2018-02-10 | 2 | 3 | The unmatched tag-101 keeper row is at 36:59 and has no nearby `Shot` row. West Ham's report places the disallowed Chicharito goal around 31 minutes and his valid goal six minutes later. The timing and event sequence do not support confidently matching the extra row to the disallowed attempt. **Unresolved.** |
| Hoffenheim–Hamburger SV, 2018-04-14 | 2 | 3 | At 7:55, a tag-101 keeper row follows Benjamin Hübner's shot by about two seconds. HSV's report says Hübner scored, but the goal was correctly ruled out because offside-positioned Serge Gnabry obstructed the keeper. This is consistent with Wyscout retaining a goal-conceded tag for a disallowed goal; it remains a source annotation and must not be counted as an official goal. |
| Lyon–Dijon, 2017-09-23 | 6 | 7 | At 65:57, the source sequence contains a goal-tagged Dijon shot and a keeper tag-101 row; another tag-101 keeper row follows at 66:05 without a separate intervening shot. The match report describes the third Dijon goal shortly after Lyon had regained the lead. **Likely duplicate/extra event annotation; exact source cause unresolved.** |

The external match records support the score and context: [West Ham's report](https://www.london-stadium.com/news/2018/february/match-report-returning-arnie-inspires-hammers-win.html), [HSV's report and timeline](https://www.hsv.de/news/spielbericht-tsg-hsv-02-hsv-unterliegt-tsg-hoffenh), and [Lyon–Dijon match report](https://www.olympique-et-lyonnais.com/ol-dijon-3-3-lyon-navance-plus%2C140301.html). The discrepancies are not corrected or silently discarded. Tag-101 goalkeeper rows are therefore **not** a score-validated keeper outcome target in this pilot, even though their actor IDs are structurally linked to the source roster.

OpenPlay goal rows were selected from `is_goal`, excluding disallowed goals; own goals were separated by `q_OwnGoal`. Wyscout scorer candidates use tag 101 except `Save attempt` rows, where the tag represents a goalkeeper's shot-against outcome and goal conceded; own-goal actions use tag 102. The 3 regular and 2 own-goal scorer-event count differences show that the providers' scorer-actor rows differ even where match scores agree. This comparison does not count a keeper's conceded-goal event as a scorer action.

## What this changes for WAR readiness

- It supplies a full-season independent fixture and score cross-check for the one season shared by the two event sources.
- It confirms that nonzero Wyscout event IDs are structurally tied to that match's own roster, while keeping the 226,038 uncredited rows visible.
- It provides bounded corroboration for scorer actors, with high exact-name agreement in some leagues but severe exact-name gaps in La Liga and weaker own-goal support.
- It does not validate actor IDs for passes, defensive events, keeper actions, assists, or other non-goal contributions.
- The supplementary goalkeeper-profile name screen is highly uneven across leagues and does not validate goalkeeper stints or keeper-shot assignments.
- Wyscout goalkeeper shot-against rows have strong same-source roster structure, but three matches contain one extra tag-101 keeper row versus the scoreboard. One is consistent with an explicitly disallowed offside goal; two remain unresolved or likely duplicate annotations. The keeper outcome target is not score-validated, and keeper skill or cross-position calibration remains open.
- It does not validate the 2018–19 through 2024–25 OpenPlay actor identities. The Wyscout archive contains no data for those seasons.
- No identity links were approved, and no player-value, formula, weight, or credit choice was made. Player event totals should remain uncredited or explicitly provisional under the existing owner-approved research policy.

## Reproduction

From the repository root in Windows PowerShell, with the pinned local archives present:

```powershell
py scripts\audit_cross_provider_goal_scorer_agreement.py
```

The script verifies the ten OpenPlay/Wyscout inputs against their manifests and records hashes of the three local club-alias maps used. It writes aggregate-only outputs, including the match-level exception list, to ignored `reports\cross_provider_goal_scorer_audit\`. It reads source archives in place and does not modify raw data. Source-scope and attribution notes for the underlying archives are in [the Wyscout research audit](wyscout_research_audit.md), [the OpenPlay source manifest](../data/openplay_source_manifest.json), and [the identity gate review](openplay_identity_triangulation_2026-11-10.md).

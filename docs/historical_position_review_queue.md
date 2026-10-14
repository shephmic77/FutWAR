# Historical position candidates and proposed validation pilot

Audit run: 2026-10-10. This work creates a review queue; it does not assign historical positions or alter statistics.

## Existing archive results

The hash-checked publisher games, appearances and lineup exports contain 14,359 scoped matches and 422,080 appearance records across all 40 Big Five league-season cells. Grouping within the publisher's player IDs gives 21,478 player-league-season candidates; 12,516 have more than one textual position label. These are provider-specific candidates, not verified identities in the main player-season dataset.

There are 313,582 linked starting-lineup appearances and 106,934 linked substitute appearances. The remaining 1,564 appearances lack a populated linked label. Unused bench entries are excluded by joining to actual appearances. Duplicate match/player/club keys stop the script rather than multiplying appearances.

No wingback labels occur. The parser's starting/bench position strings have not been established as actual played roles, particularly for substitutes. Variation is useful evidence to review, but does not validate the interpretation. For example, Emmanuel Gyasi's 36 Serie A appearances in 2021-22 have nine different textual labels, including Left-Back and several midfield/attacking labels. This does not prove nine played roles.

The five-appearance/10% secondary-position rule is deliberately not applied to these unverified strings. Original datasets and existing notebook position labels remain unchanged.

## Reproduce and inspect

From the project directory in Windows PowerShell:

```powershell
py scripts/audit_historical_position_candidates.py
```

Private, ignored outputs in `reports/position_source/`:

- `historical_label_candidates.csv`: every provider-specific player-league-season candidate, label counts, linked/missing appearance counts and club-stint counts.
- `historical_label_variation_review.csv`: candidates with changing text labels, ordered for review.
- `historical_role_readiness.csv`: coverage and unresolved role status for all 40 cells.
- `historical_candidate_lineage.json`: input hashes, scope, label vocabulary and explicit confirmation that no positions changed.

Input hashes are verified before loading and after writing outputs. Same-provider club stints are counted together only for candidate review; no canonical cross-provider identity merge is made.

## Proposed bounded StatsBomb pilot

The already archived Open Data Events v4.0.0 specification supplies explicit LB, RB, LWB, RWB and GK labels, plus more granular midfield, centre-back and attacking labels. Starting XI and Tactical Shift events describe recorded lineup positions. These are provider annotations, not proof of every movement or tactical responsibility.

After resolving access conditions, audit match lists for La Liga 2017-18 (competition 11, season 1) and Bundesliga 2023-24 (competition 9, season 281). These two cells span the project's earliest and latest available catalog periods; their complete league coverage has not been established. Download a small deterministic sample of available match event files, with URLs, retrieval dates and hashes, to validate a position-spell representation before larger ingestion.

Check starters, substitutes who enter, unused substitutes, tactical shifts, GK and wingback distinctions. Preserve within-match role changes and unknown intervals. Compare a reviewed sample with the existing publisher strings using verified match/player links; document disagreements rather than treating either source as automatic truth. Do not map left/right centre backs to CB, choose one position per multi-role match, or apply seasonal secondary labels until those choices are discussed with the owner.

The catalog has only seven target league-season cells: Bundesliga 2023-24, La Liga 2017-18 through 2020-21, and Ligue 1 2021-22/2022-23. The other 33 cells are absent. This pilot would validate methods for a rich sample, while the overall eight-season project scope remains unchanged.

## Access decision

**Subsequent update:** the owner authorized the pilot. Official Python instructions explicitly allow unauthenticated open-data access, while the requested registration link redirects. The bounded acquisition and its preserved registration caveat are documented in local-only position-pilot notes; detailed findings are not included in the public repository while provider branding/reuse requirements are reviewed. The paragraph below records the earlier decision, which this update supersedes for the six-match pilot only.

The pinned [StatsBomb user agreement](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf), clause 2.2, asks users to provide their name and email before accessing the service. It also restricts external data sharing and commercial exploitation and requires branding when publishing analysis. Attribution alone does not resolve these conditions.

No personal information has been submitted and no match/event files have been acquired for this pilot. The owner can register directly through the provider's current official resource page and confirm completion, or choose continued research using existing permitted sources. No account creation, provider contact or final role vocabulary is authorized by this plan.

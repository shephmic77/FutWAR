# Local player explorer prototype

The first profile prototype is local-only and follows the owner's choice to finish position-minute validation first. It introduces no service, hosting account, publication or new package dependency. The Sites skill's buildless local workflow was used; Tableau remains planned for later validated dashboards.

## Open and rebuild

Open `reports/player_profile/FutWAR_Player_Explorer.html` in a browser by double-clicking it in File Explorer. The generated file embeds its data, styles and JavaScript, so no server or internet connection is required for search and profile views. Source-reference links require internet access.

To refresh from audited datasets, run from the project directory in PowerShell:

```powershell
py scripts/build_player_profile.py
```

Editable UI source is in `profile/`; generated HTML, JSON and the review screenshot remain ignored under `reports/player_profile/`. The generated page contains source-derived data and is for private local research; do not upload it or distribute it as an unrestricted dataset.

## Current behavior

### Navigation and visual redesign

The owner requested a more intuitive, graphical page. The revised local prototype has a compact collapsible player browser, accent-insensitive search, expandable filters/reset, one main season-and-club selector, saved source records, and Overview/Performance/Team & history/Sources & evidence tabs. Saved keys remain in browser-local storage when supported; no account or external storage is introduced.

The overview uses a team-inspired accent palette, player imagery, available club/league marks, four key statistics, paired player/peer bars and team-result graphics. Negative residuals use bars diverging from an explicit zero line. Metrics have independent scales, retain their original units and never become an arbitrary composite or radar-chart value score. Keeper version warnings remain visible on performance views.

Visual coverage is deliberately limited: reviewed portraits for Mohamed Salah and Aaron Ramsdale, a Liverpool wordmark and a Premier League wordmark. Other players/clubs/leagues use clearly identified initials as fallbacks. Selected club colors are approximate design palettes, not certified historical kits or universal club-color coverage. Image age is disclosed; an illustration does not certify the identity of every same-name seasonal record.

`scripts/acquire_profile_images.py` archives a small reviewed Commons sample with URL, retrieval date, license, author and SHA-256 in `data/profile_image_manifest.json`. The initially acquired full-body Salah image remains archived; the more suitable headshot is selected for display. Export uses the latest reviewed asset per kind/label and verifies its hash. Image files and data URIs stay in ignored raw/output folders. UI image credits link to each file and license, identify CSS display cropping and preserve the original images. Trademark/affiliation is not implied.

The existing 12,848-record data cohort, measures and evidence limits remain unchanged. Browser checks verified tabs, saved/unsaved behavior, season switching, GK-specific measures, hide/show navigation, empty search and accent-insensitive Mbappe search. The desktop layout and portraits were visually reviewed. JavaScript syntax and all 71 project tests passed. A fresh screenshot is in `reports/player_profile/preview.png`.

- Search by player name or club, with season, league and outfield/GK filters.
- Select one club-season source record; exact same-name rows are displayed separately, not merged as a verified career.
- Inspect per-90 performance and same-league/season/nominal-position/source cohort medians. Keeper cross stopping is shown as a percentage; missing measurements remain unavailable, not zero.
- View exact-label-linked team results and earned points, explicitly before standings adjustments.
- View source references, identity/model warnings and unresolved position/history coverage.
- Empty searches clear the profile. Filters cannot leave an excluded player's profile displayed.

The export uses the existing hashed descriptive cohorts: 11,889 outfield records and 959 keeper records, all with 900+ reported minutes. They total 12,848 source club-season records, not unique players. The verified team-context table has 780 club-season rows; unmatched source club labels remain unlinked.

Specific main positions are not assigned without adequate seasonal evidence. The approved rule remains most total evidenced position minutes. Transfers are not linked and comprehensive injury histories are unavailable. The page labels these gaps rather than inventing timelines. No performance rating, replacement baseline, cross-league normalization or FutWAR formula is introduced. Selecting a source record does not claim that it represents every club stint or every appearance of that person.

## Verification

The exporter completed with unique source-record keys and no ambiguous team-context keys. It reuses existing source-hash checks and serializes missing numeric fields to JSON null. JavaScript syntax checked successfully. All 71 existing project tests passed.

Browser checks confirmed outfield and GK search/selection, the season filter, keeper-specific metrics, linked Southampton team context, source warnings, the missing-history panels and empty-search behavior. The standalone embedded-data page was also tested through localhost. The desktop layout was visually inspected; narrow-screen CSS is provided but a dedicated mobile-browser review remains outstanding. A screenshot is saved at `reports/player_profile/preview.png`.

The localhost QA server was stopped after review. The already-loaded preview remains interactive; reopening the generated HTML is the durable route. Sources and current analysis notebooks were not modified by the prototype.

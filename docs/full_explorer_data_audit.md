# Full-scope private explorer and data audit

The private explorer includes all 22,418 original player-club-season records for
2017–18 through 2024–25, including low-minute records and goalkeepers. Original
player statistics remain unchanged. Enrichment is separate, sourced context.

## Market-value decision

The owner selected the latest recorded estimate on or before June 30 of the
season's ending year. The implementation restricts candidates to the same
July–June season, retains the actual valuation date, and leaves a missing
season unavailable. It does not backfill from another season or the provider's
latest profile value. June 30 is the selected cutoff even when COVID fixtures
continued later. Market values and transfer fees are EUR provider estimates;
neither measures player contribution or an available replacement's cost.

The archived valuation table comes from
[dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets).
Its [field definitions](https://github.com/dcaribou/transfermarkt-datasets/blob/master/data/prep/dataset-metadata.json)
distinguish market values from transfer fees. Retrieval URLs and SHA-256 hashes
are retained in `data/player_identity_source_manifest.json`. Publisher license
claims do not resolve upstream rights; these outputs remain private.

## What was checked

`scripts/build_explorer_dataset.py` checks all 3,990,404 original source cells,
population and numeric validity, applicable ranges, unique record keys,
source fingerprints, starts versus appearances, and three explicit count
identities. It checks valuation dates/conflicts and preserves all 178 original
fields in the enriched CSV. Zero issues were found under those structural and
arithmetic checks. This is not independent verification of every football fact.

Observed enrichment: 20,521 provisional profile identity links, 20,146 dated
market-value records, and 1,662 separate keeper overlays. Profile matching is
not universally verified. Keeper exposure, metric versions and existing flags
remain visible. Exact historical positions require played-role evidence;
profile positions such as SS do not establish seasonal position minutes.

Reports in `reports/explorer/` include all 40 league-season cells, coverage for
each of the 178 original fields, missingness and issue ledgers. Final private
data are `data/processed/futwar/player_seasons_enriched.csv`. PostgreSQL context
uses `futwar.explorer_player_context` and `futwar.explorer_player_market_context`,
preserving the existing normalized tables.

## Images and injuries

Locally archived photographs, club marks and five league logos have individual
source credits. Juventus's current official J mark comes from the
[club's logo page](https://www.juventus.com/en/club/logo); it is an illustration,
not proof of the edition used in every historical season. Assets retain their
original bytes and use CSS fit. Bulk Commons logo and action-photo acquisition
stopped on HTTP 429; missing images remain honest fallbacks.

The [Kaggle injury/market-value research dataset](https://www.kaggle.com/datasets/gumush/football-player-injuries-market-value)
was archived with its README and license metadata (CC BY-NC-SA 4.0). It contains
12,948 injury events for 2,061 anonymized players, with events ending in August
2024 and a filtered cohort. Real names and provider identity mappings are absent.
It cannot fill named player profiles, and no reidentification or merge was
attempted. Archive provenance is in `data/explorer_injury_manifest.json`.

## Rebuild on Windows PowerShell

From the project root, run:

```powershell
py scripts/build_explorer_dataset.py
py scripts/package_explorer.py
docker compose exec -T postgres psql -U futwar -d futwar -f /workspace/sql/030_explorer_context.sql
```

Open `reports/explorer/FutWAR_Explorer.html` in a current browser. All data and
locally archived images are embedded; a running server is not required. Source
links and on-demand provider portraits need internet access. Optional preview:

```powershell
py -m http.server 8772 --bind 127.0.0.1 --directory reports/explorer
```

Open `http://127.0.0.1:8772/FutWAR_Explorer.html`; Ctrl+C stops the preview.

The site supports global search, eight-season selection and pooling, outfield
and keeper analysis, league colors, peer filters, point previews, player/team
comparison, dated market histories, source fields, exports and light/dark themes.
Rates pool compatible totals and metric-specific exposure rather than averaging
seasonal rates. Default peers require 900 minutes across the selected period;
selected low-minute observations remain visible as hollow marks. Main historical
positions, complete injuries and photographs, league-strength adjustments and
a validated common WAR scale remain unresolved. No WAR formula was finalized.

### Portrait fallback and compact header

The site now uses portrait URLs recorded in the hash-verified player archive for
the already audited profile candidates. Archived action photos take priority;
provider portraits fill missing local photographs in profiles, graph previews
and comparisons. Only visible images are requested, with no bulk downloads or
retries of rate-limited sources. A failed request retains an honest initials
fallback. Profile URLs and the source archive fingerprint remain in the evidence
view/coverage report. Pictures may be current and do not establish a historical
kit, position or season. Upstream image rights remain unconfirmed; private use
does not authorize redistribution. Unresolved identities are not assigned a
guessed photograph. `reports/explorer/portrait_coverage.json` records coverage.

Run `py scripts/resolve_explorer_portraits.py` before packaging to resolve
additional portrait-only candidates using explicit spelling normalization
(including ø/ł), full name, birth year and historical club-season appearances.
It does not use fuzzy/partial names or change statistical identities. The
additional source hashes and candidates are retained separately, with unresolved
rows in `reports/explorer/portrait_review_queue.csv`.

The header retains the appearance count while removing its repeated season text
and position-validation sentence. The season selector and View evidence retain
that context and the existing research warnings.

### Search and annual-value polish

Search normalizes Turkish dotless ı and additional accented characters. Typo
suggestions (such as pulsic → Pulisic) are clearly labelled and require the user
to select a result; they do not create identity matches. The complete source
record collection is indexed, irrespective of photos, positions or minutes.
Search remains visible while scrolled; selecting a result opens the banner.

Source rows with the same normalized full name and known birth year share the
existing provider-backed UI profile only when that name/year has one provider
ID. Distinct supported provider IDs remain separate. This presentation rule
repairs Modrić's split seven-plus-one seasons without overwriting statistical
identity links. Available profile photos/attributes can be shared within that
UI profile; historical role evidence and original statistics remain unchanged.

Market charts show one observed June-30-cutoff estimate per season, labelled by
ending year. Missing years leave chart gaps; there is no interpolation/backfill.
Exact dates remain in the expandable source history and evidence. Modrić's
archived 2025 estimate is EUR 4 million recorded June 9, 2025. His 2020–21 source
row has no linked valuation and remains unavailable. A live Transfermarkt
history request returned HTTP 403; this pass does not claim independent live
verification. The publisher's raw source and cutoff checks remain reproducible.

Official Premier League SVG artwork and LaLiga's official icon replace their
wordmarks. The Premier League lion is displayed by limiting the SVG viewport;
raw SVG paths remain unchanged and original bytes are archived. Source URLs,
hashes, rights notices and display transformations are recorded in
`data/explorer_league_emblems.json`. These are illustrative current editions.

`node tests/explorer_core.test.cjs` checks all 22,418 records remain represented,
the reported search regressions, one eight-season Modrić profile, protection
against merging different provider identities, and annual valuation boundaries.

### Owner's specific-position vocabulary

The interface uses only GK, RB, RWB, CB, LB, LWB, CM, CDM, CAM, LM, RM, ST,
LW and RW. Provider DM/AM display as CDM/CAM; CF and SS fall under the owner's
ST category. Broad source labels do not determine a specific role. Without a
supported profile role, the interface shows Unavailable. It never turns a
generic defender into CB or infers secondary positions from combined labels.

Broad source positions are removed from profile details, search, chart labels,
team rosters and the raw-stat inspector. Original source fields remain immutable
in data/exports for provenance. Position peers and chart position encodings use
specific profile roles with the existing historical-evidence caveats; no final
replacement/model eligibility rule is changed.

The chart's “Why these dots?” disclosure reports the selected season/domain,
position, leagues, minimum exposure, qualifying peers, axis-metric exclusions
and selected-player exceptions. Every matching point is included; there is no
random sampling or top-player cap. Overlapping marks may appear as one dot.
The former McKennie 2024–25 exact broad-label cohort had 48 records; the specific
CM profile-role cohort has 206 compatible 900+ minute observations. These profile
labels are still not validated historical played-role evidence. Median guides
use qualifying peers, excluding any separately added selected-player exception.
# Explorer presentation and supplemental history — 2026-10-10

The user-supplied light and dark FutWAR PNGs are copied unchanged, fingerprinted in
`data/explorer_branding.json`, and displayed with CSS containment. Combined
multi-league scatter observations use a gold diamond with an explicit legend;
single-league observations retain their existing league colors. Position-color
mode continues to encode positions.

The pinned `luukhopman/football-logos` catalog adds archived crests for 123 of
149 source club labels, including Inter, Nice, Barcelona and Paris S-G. Originals,
source paths, commit and SHA-256 fingerprints are retained in
`data/explorer_crest_catalog.json`. This is private-use source attribution, not
an assertion of open redistribution rights or historical-season crest accuracy.
At that first snapshot, twenty-six source clubs still lacked an archived crest
after automatic approval review encountered an account usage limit. This gap
was resolved in the subsequent complete crest audit below.

`scripts/build_explorer_profile_history.py` reads existing fingerprinted publisher
archives to create separate market and transfer context for 6,360 candidate
profiles. The output contains 38,426 observed annual estimates across 2018–2025,
using the latest recorded same-season estimate on or before June 30. Exact dates
remain in the detail view. Ali Abdi now has eight annual points rather than one;
these are contextual valuation records, not additional Big Five performance rows.
Original player statistics and raw sources remain unchanged. Candidate identity
uncertainty and provider reuse limitations remain applicable.

Rebuild in PowerShell from the repository root:

```powershell
py scripts/build_explorer_profile_history.py
py scripts/package_explorer.py
```

Validation: JavaScript syntax and existing search/grouping regression checks pass;
the supplemental-history test checks all annual date boundaries and Ali Abdi's
eight observed ending years. The rendered combined chart confirms the gold
diamond, legend and supplied header logo. The working preview uses port 8773.

### Complete crest audit

The subsequent team-by-team audit covers all 149 observed clubs and all 780
club-season entries across the 40 league-season combinations. All have a locally
embedded crest. Roma and four other clubs were resolved through reviewed catalog
aliases. Seventeen additional crests come from the pinned Guardian catalog
(`97bea1b77437ae74d98bde03f519e9db4f4beed3`); four from the pinned JoseArroyave
catalog (`5d221dfa6849a01dced71c389eb1eafe83ce51e2`). Source URLs, hashes, original
files, identity mappings and rights notices are retained in
`data/explorer_secondary_crests.json`. SVGs are checked for scripts, event handlers
and external href references before embedding.

`reports/explorer/club_crest_coverage.csv` lists every club-season with its actual
bundled asset fingerprint and citation. The review page
`reports/explorer/club_crest_review.html` loads every selected asset; browser
inspection confirmed **149/149 decoded images, zero failed images**. Roma's crest
also loaded in the Dybala player banner. The coverage regression test passes.

This is complete logo availability for the observed clubs, not certification of
each season's exact historical crest design. Source artwork is unchanged. The
Guardian and JoseArroyave catalogs are cited in the site's research references;
each club's image credit includes its specific source URL.


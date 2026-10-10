# FutWAR — Candidate sources and due diligence

This is a **candidate list**, not proof of complete coverage or permission to scrape/re-publish. Audit sources against all four seasons (2022–23 to 2025–26) and five leagues before use. Record source date, file/version, license/terms and actual available fields.

| Source | Potential use | Limitations to verify |
|---|---|---|
| Kaggle: `emrey3lmaz/top-5-league-football-player-stats-2017-2025` | Historical player-season stats, expected to contain 2022–23 to 2024–25 | Inspect real files, provider definitions, missing values, right to redistribute; 2025–26 not included in stated span |
| Understat / `soccerdata` | Big Five npxG/xG, xA, shots and some player-match/season data | Mainly attacking; check access, seasons, match completeness and terms |
| Football-Data.co.uk | Domestic results and team match data across leagues | No detailed player performance; verify season/competition file formats |
| Sofascore or ESPN | Starting XI, nominal positions, formations, substitutions, player match statistics | Access and historical coverage are uncertain; check terms, legal acquisition and definitions |
| Historical FBref archives, including Kaggle | Passing, defensive and progression stats if actually archived | Live FBref advanced coverage changed; verify fields are not empty and don't mix provider definitions silently |
| Transfermarkt-derived Kaggle Player Scores | Matches, player appearances, clubs, transfers, squad information | Value/market price does not equal on-pitch WAR; licensing and player IDs |
| StatsBomb Open Data | Detailed event + some positional data for methodology and limited tactical pilot | Selected competitions only; **not** blanket full Big Five coverage |
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

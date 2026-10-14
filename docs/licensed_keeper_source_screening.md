# Free goalkeeper sources with explicit reuse statements

Reviewed 2026-10-10. The owner chose continued source searching instead of permission requests. No archive owner was contacted, no account or paid service was introduced, and no new goalkeeper measurements were acquired or merged in this screening.

## Result

This search did not establish a free, reuse-cleared source of comparable goalkeeper measurements for all five leagues in 2017-18 through 2024-25. This is the result of a bounded search, not a claim that no such source exists.

An explicit publisher license and suitable scope are separate requirements. A license on a rehosted file may not settle the original provider's conditions. The previous unlicensed keeper archive candidates remain separate from the sources below.

| Source | Published reuse statement | Coverage or provenance limitation | Decision for the eight-season dataset |
|---|---|---|---|
| Wyscout original Figshare research release | CC BY 4.0, verified in original article metadata | Audited Big Five events for 2017-18 only; no supplied PSxG | Strong existing one-season research source; not full scope |
| Mendeley goalkeeper-action study | CC BY 4.0 on original deposit | 32 Spanish U12 regional matches | Out of scope; possible methodological reference only |
| PLOS goalkeeper-decision supplement | CC BY 4.0 in original Figshare metadata | Research supplement, not established historical Big Five season coverage | Not a seasonal data replacement |
| Gamblistics Hugging Face archive | CC BY-NC 4.0 on dataset card | Recent Premier League, sparse player stats; upstream sources insufficiently specified | Full-scope coverage and upstream rights not established |
| Cornerflick downloads | CC BY 4.0 for published compilation | Publisher explicitly distinguishes underlying providers' terms; goalkeeper/player historical coverage untested | Not reuse-cleared for our needed measurements |
| Luxury Lakehouse PSxG/shot mirrors | Prediction card says CC BY-NC 4.0; shot card says CC BY 4.0 | Derived model outputs; conflicting characterization of upstream StatsBomb license | Do not treat as a licensed replacement for provider PSxG |
| Kaggle Premier League 2024-25 Data | Publisher claims CC BY-SA 4.0 | FBref-derived, one league/season and admitted missing match pages | Upstream rights and full scope unresolved |
| Kaggle Goalkeeper and Midfielder Statistics | Publisher claims CC0 | Rehosts a 2022/23 FPL prediction project; upstream rights unestablished | Does not establish eight-season coverage or reuse clearance |

## Original research deposits

The [Mendeley deposit](https://data.mendeley.com/datasets/hgbc2y73d5/1) identifies 902 defensive and 896 offensive goalkeeper actions in 32 U12 matches and declares CC BY 4.0. The [Kaggle mirror](https://www.kaggle.com/datasets/saurabhshahane/goalkeeper-actions-dataset) correctly points back to that study. Clearer licensing does not make youth observations comparable to our adult domestic-league seasons. No study files were downloaded.

The PLOS supplement, [Oracle data and professional goalkeepers data](https://api.figshare.com/v2/articles/5859090), has an XLSX file and CC BY 4.0 in original Figshare metadata. Its association with [the goalkeeper-decision study](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0191431) is a research lead. The paper page could not be retrieved in this screening, so detailed sample coverage remains unverified. No eight-season applicability is inferred from the license.

Our [existing Wyscout audit](wyscout_research_audit.md) remains the most concrete original-source licensed event route: actual files, all five 2017-18 domestic seasons and keeper-action types. It lacks detailed played-position labels and supplied PSxG. These limitations remain explicit.

## Publishers and mirrors

The [Gamblistics card](https://huggingface.co/datasets/gamblistics-lab/sport-statistics) declares noncommercial research reuse, describes recent Premier League data and admits sparse/missing player statistics. It reports 1,190 match rows but only 492 per-match player-stat rows, and a reverse-engineered proprietary source format. These are publisher-reported counts, not a local coverage audit. Neither the card nor the reported counts establish comparable eight-season Big Five data or all upstream permissions. No raw files acquired.

[Cornerflick's data page](https://cornerflick.com/data) provides explicit CC BY 4.0 compilation terms but reserves the question of underlying provider conditions for large-scale redistribution. Its described downloads are results, lineups, events and team stats. Actual historical individual goalkeeper coverage was not established. A compilation license cannot be silently extended to every underlying measurement.

The [Luxury Lakehouse prediction card](https://huggingface.co/datasets/luxury-lakehouse/psxg-predictions) describes a logistic model using goalmouth coordinates and labels derived predictions CC BY-NC 4.0. The [shot mirror](https://huggingface.co/datasets/luxury-lakehouse/statsbomb-shots-on-target) labels StatsBomb Open Data CC BY 4.0. That upstream characterization conflicts with the custom license privately archived in the local StatsBomb source review; that detailed review is not included in the public repository pending reuse and branding review. The prediction model is not an official provider PSxG feed, and exact scoped coverage has not been verified. Neither mirror was adopted or downloaded. Its model choices cannot become FutWAR inputs without discussion and validation.

The [Kaggle Premier League candidate](https://www.kaggle.com/datasets/furkanark/premier-league-2024-2025-data) claims CC BY-SA 4.0 but says its data were scraped from FBref and some match pages are missing. The [Goalkeeper and Midfielder Statistics card](https://www.kaggle.com/datasets/thedevastator/maximizing-player-performance-with-goalkeeper-an) claims CC0 while linking a [2022/23 FPL project](https://github.com/hardboyvino/2022_fpl_points_predictor) as its source. Neither publisher statement settles upstream rights or all 40 league-season cells. Only public metadata were inspected; no scraper or bundled executable was run.

## How this was checked

Searches covered original Figshare/Mendeley deposits, publisher cards on Hugging Face and Kaggle, and explicit download terms. Public Kaggle list/view metadata were read without signing in; Figshare's article API confirmed original license metadata. Search snippets served as leads, followed by primary source pages or APIs. No license claim from an unrelated code dependency or publication was assigned to a data file.

Original data, research goals and the 5-appearance/10% position rule are unchanged. No tests were needed for this documentation-only screening; source links and project-document links were checked locally.

## Proposed next step, requiring owner direction

Recommend a bounded keeper-data validation pilot using the already acquired original Wyscout 2017-18 release: validate saves versus attempts, goalkeeper-event attribution and distribution opportunities before any valuation model. Keep the eight-season target and unresolved full-scope keeper/position needs documented. This would produce useful method evidence without treating sparse data as complete or adopting unverified archive rights. It is a proposed change in the immediate work focus, not an approved reduction in research scope or a finalized formula.

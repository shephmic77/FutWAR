# Soccer replacement baseline: evidence and choices

## Owner's three comparison choices and position scope (2026-10-10)

For future comparison graphs, the owner selected all-five-league average, selected-league average, and a team-specific feasible replacement, with a separate position-locked/any-position switch for all three. Average settings remain comparison benchmarks; only the feasible team replacement is automatically a baseball-style replacement concept. The flexible pool accepts a historically evidenced secondary role only at five or more appearances and 10% or more of all appearances. The main role remains the role with most evidenced minutes. This is not a performance-reliability cutoff.

The selected season controls the references. For retrospective averages, use that season's observed performance. For team feasibility, freeze affordability and availability at season start; handle January separately. A replacement projection at season start must use information available then and a prediction trained only on earlier data, not that player's full-season outcome. Combined years subtract their own year's baseline before addition.

See [FutWAR contribution and six-comparison architecture](war_model_architecture.md). It records the limits of present data: no historical all-club wage/budget pool, no verified played-position semantics, and rich events for only 2017–18. Do not create numeric team baselines or cross-position WAR estimates until those components are measured.

Reviewed 2026-10-10. The owner chose the baseball WAR principle: compare observed contribution with a readily available replacement-level alternative. This note evaluates ways to estimate that alternative; it selects no pool, cutoff, percentile or formula.

2026-10-11 source follow-up: UEFA's public club-finance reports can support selected financial benchmarks, and UEFA describes a substantially broader curated database (700+ clubs, 15 years) that is not staged as an open complete dataset here. Capology has historical salary coverage as a paid bulk product; the public site calls salaries estimates, limits use to private non-commercial purposes under ordinary terms, and requires a publishing license to publish API data. No Capology figures were collected. Neither source on its own shows a particular club's preseason transfer budget, an available position-compatible player, and that player's expected contribution. See [data-source review](data_sources.md#historical-replacement-budget-research-2026-10-11).

## What the research establishes

[FanGraphs' replacement-level explanation](https://library.fangraphs.com/the-beginners-guide-to-replacement-level/) emphasizes talent available at little acquisition cost. Performance level must therefore be estimated from evidence about alternatives, rather than defined as the average starter. Baseball's specific replacement calibration is not a soccer parameter.

[American Soccer Analysis's 2019 PAR study](https://www.americansocceranalysis.com/home/2019/1/11/points-above-replacement) used MLS players with base salaries at or below $67,000 in 2017-18, split into positional reference groups. It explicitly discusses selection bias among players who got minutes and the influence of a few high-minute players on the baseline. Its European bottom-three-team proxy is a proposal, not evidence that every player at a relegated club is readily available or replacement level. These historical MLS amounts and roster rules should not be transferred to the Big Five leagues.

[The eLPAR paper](https://arxiv.org/pdf/1807.07536) estimated positional replacement ratings from the cheapest tenth of contract values in its EPL 2015-16 example, using FIFA video-game ratings. It demonstrates a cost-based approach, not an approved FutWAR percentile or a measure of our players' actual seasonal performances.

These studies show that baseline construction is a research decision. Neither equal positional representation nor resemblance to a familiar leaderboard validates the baseline.

## Candidate approaches

| Candidate | Why investigate it | Main problem | Current feasibility |
|---|---|---|---|
| Players with documented low acquisition cost and usable availability | Closest to the readily available alternative principle | A free transfer can involve high wages; low wages can identify valuable young players; availability must be historical | Transfer records exist, but histories and fee interpretation need validation; no wage fields in the inspected exports |
| Reserves or players with limited starts | Offers an observable pool for exploratory comparison | Bench players at strong clubs can be excellent; injuries, transfers and tactical choices affect starts | Starts, appearances and minutes exist; historical injury and selection reasons are not established |
| Lower-tail estimated player performance | Straightforward sensitivity benchmark once a contribution estimator exists | Poor observed performance does not demonstrate acquisition availability; noisy samples can define an artificially weak baseline | Cannot calculate a meaningful value percentile before the contribution measure exists |
| Players at relegated or bottom clubs | Can test a published team-based proxy | Poor team results do not imply poor individual talent or cheap availability; selecting clubs by final results can leak information into forecasts | Team results exist; keep this as a comparison hypothesis, not a chosen pool |

No candidate is automatically accepted. Actual backup at a particular club and a common replacement-level standard answer different questions; a wealthy club's substitute should not define the generic replacement level for everyone.

## What was checked locally

The existing SQL exploration snapshot contains 22,418 player-team-season records, with no missing minutes, appearances or starts. There are 2,661 zero-start records across all positions, including goalkeepers; none has zero minutes. These are descriptive checks, not replacement classifications. Players who never appeared are absent from this snapshot, so it cannot represent the entire available-player pool.

Inspected publisher headers:

- `players.csv.gz`: current club, current contract expiry, position, current/highest market value, among other profile fields. Current metadata must not be projected backward into 2017-18.
- `transfers.csv.gz`: transfer date/season, origin/destination clubs, transfer fee and market value. Fees and market values are distinct from wages; a market-value estimate does not establish replacement availability.
- `appearances.csv.gz`: match/player/club IDs, date, goals, assists, cards and minutes. These do not establish complete substitution intervals or reasons for non-selection.

The identity audit already flags incomplete transfer histories and limits reviewed links to a small pilot. Automated identity candidates cannot silently become verified links for selecting a replacement pool.

## Recommended next investigation, pending owner direction

Compare candidate pools rather than immediately calculate WAR. For each pool, report evidence for membership, uncertain identities, league/season/position coverage, minutes, starts, sample size and exclusions. Review potential injury cases, short transfer stints and highly regarded reserves where historical evidence is available. The notebook's 900-minute display cutoff must not automatically define or exclude replacements.

Use availability/cost evidence as the long-term foundation. Limited-start records can provide an initial diagnostic comparison while remaining explicitly labeled candidates. Numerical thresholds would be proposed for review before use. Pool membership should be established independently of a desired ranking; performance estimation comes afterward, with appropriate small-sample stabilization and uncertainty.

The owner approved documented availability/cost research first; the resulting [four-case pilot](replacement_candidate_pilot.md) illustrates its limitations. The owner also approved a shared standard for core FutWAR, with club-specific alternatives analyzed separately. Historical evidence may support only a smaller pilot initially; do not claim full eight-season coverage until audited. These decisions do not settle whether the eventual baseline varies by position, league or season, or how values become comparable across leagues.

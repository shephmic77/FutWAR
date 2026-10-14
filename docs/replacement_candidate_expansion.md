# Expanded replacement-candidate evidence

The owner authorized expanding the evidence sample before reviewing selection rules. On 2026-10-10 the sample grew from four to seven cases. All five leagues are now represented, but only five of the 40 league-season combinations have cases. Presence in each league does not establish a usable replacement pool.

The original pilot ledger and four-case outputs remain unchanged. A separately hashed expansion references its parent ledger and adds:

| Case | Local season exposure | Evidence status |
|---|---|---|
| Roque Mesa / Valladolid / 2020-21 | 1,761 minutes; 25 appearances; 21 starts | [Official club notice](https://www.realvalladolid.es/noticias/roque-mesa-2023) says he arrives free; extracted publication date unavailable |
| Sebastian Rudy / Hoffenheim / 2021-22 | 773 minutes; 21 appearances; 7 starts | [Schalke confirms contract termination](https://schalke04.de/personal/rudy-vertragsaufloesung/) on 16 June 2021; destination signing page could not be retrieved, so that detail remains unverified by a primary page in this review |
| Asmir Begović / Everton / 2021-22 | 270 minutes; 3 appearances; 3 starts | [Premier League notice](https://www.premierleague.com/en/news/2193831) confirms a goalkeeper signing after contract expiry |

The local playing records were matched by exact reviewed name, club, league, season and source record, with a pinned snapshot fingerprint. These are record-level research links, not new cross-provider identity assignments. Wages and total costs remain unknown. No case is confirmed replacement level, and no rate was averaged into a baseline.

The expanded audit writes 400 coverage rows: all five leagues, eight seasons and ten original nominal source labels. Those broad labels describe the source inventory only; they are not the owner's newly requested model positions. Six cases lack sufficient specific historical position evidence. Begović's official keeper description supports GK metadata, but the complete match-position frequency audit has not been done for any case.

## Selection rules proposed for review

1. Require documented historical acquisition/release evidence, compatible specific position evidence and verified identity before treating a case as an estimation-pool member. Acquisition availability is distinct from demonstrated low total cost and replacement-level talent.
2. Keep unresolved costs, dates, injuries and missing match positions explicit. Release-only or partly corroborated cases remain in a research queue.
3. Evaluate talent from sufficiently supported, context-adjusted performance with uncertainty. Do not select players because a tiny-sample rate is exceptionally high or low. The estimator and minimum exposure are not chosen.
4. Inspect how equal-player and exposure-weighted summaries differ, including whether a few high-minute players dominate. Do not pool raw rates across leagues to create a common skill scale.
5. Audit every league-season-specific-position combination. Sparse or missing groups remain unestimated rather than filled with unrelated positions, guessed league penalties or invented keeper values.

These are proposals, not adopted numerical eligibility rules. The owner has separately approved the position-label rule: a secondary position needs at least five appearances and 10% of appearances. See [position evidence requirements](position_evidence_requirements.md); that labeling rule must not be repurposed as a replacement-performance sample-size threshold.

## Reproduction

```powershell
py scripts/audit_replacement_pilot.py --expanded
```

Inputs: original private ledger plus `data/raw/replacement_reviews/expanded_2026-10-10.json`, and the existing hashed SQL snapshot. Outputs: ignored `reports/replacement_expanded/candidates.csv`, `coverage.csv` and `run.json`. The script checks parent and snapshot hashes and rejects repeated local links. It writes no player statistics or baseline.

The initial expanded run linked seven cases and generated all 400 source-label coverage rows. A repeat run preserved both CSV outputs exactly. The research now needs match-position and keeper evidence more than additional free-agent names alone.

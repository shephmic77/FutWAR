# Main-position analysis and interactive player profiles

Owner clarification: standard analysis should use only a player's main position. A separate interactive player search should provide a broader, visually polished view with additional positions, injuries, transfers, team statistics and useful context. This is a presentation and research direction; no score or main-position calculation is selected here.

## Standard analysis

The owner selected position-minute validation before profile implementation. A local six-match reconstruction checks recorded position spells and retains an unresolved zero-length role spell. Detailed findings are kept local while the provider's public-use and branding conditions are reviewed. This establishes a bounded technical prototype, not complete historical positions or a selected main-position rule.

Use one historically supported main position per player-season. Keep positional distributions and the overall-value research as separate tracks, both including GK. Preserve secondary roles in the evidence layer, but do not duplicate the same seasonal record across multiple standard-analysis position groups. Current broad nominal labels remain provisional; this clarification does not authorize inventing specific positions or silently rewriting existing notebooks.

The owner selected **most total evidenced position minutes** as the main-position rule. Ties, incomplete coverage and unresolved spells prevent a finalized assignment. No automatic cross-provider identity merge or combination of uncertain club stints is authorized. Secondary-role sustained-time counting remains undecided.

## Interactive profile

Search for a player and select a season or club stint. Show a clear identity header, main position, minutes/appearances and current coverage status. Provide season trends, position history, club/league context, transfers and a sourced availability timeline. Include GK-specific measures for keepers. Display performance domains separately until a validated contribution model exists.

Additional roles should include the underlying appearances/minutes and coverage. Distinguish meaningful secondary positions meeting the owner's five-appearance/10% rule from isolated or unresolved role observations. Preserve all observations in detailed history without presenting a zero-length spell as a meaningful secondary position. Counts for multi-role matches and any sustained-time threshold remain undecided.

Injury information requires dated sources and explicit coverage. Missing injury records mean unknown history, not an injury-free season. Do not infer injury from low minutes or infer cause of performance changes from a timeline. Injury histories concern availability context; they do not automatically change observed seasonal contribution.

## Current readiness

| Profile component | Current evidence | Remaining work |
|---|---|---|
| Player performance | Audited seasonal outfield data and separate keeper derivative | Verified identity bridge; source/version warnings |
| Specific positions | Six-match recorded-spell pilot; broader text-label candidates | Period-aware minutes, sustained-role rules, broader coverage |
| Transfers | Archived publisher transfers and a few corroborated cases | Historical identity links, incomplete histories, date semantics |
| Team results/context | Audited match results and team-season context | Safe links to player stints; distinguish earned from adjusted standings points |
| Injuries/availability | A few cited case-specific research notes | No comprehensive injury-history dataset has been established |
| FutWAR/contribution | Research only | Replacement baseline, estimation and outcome validation |

## Visual direction for review

The owner's detailed answers to design questions 1-12 are recorded in [the explorer design brief](player_explorer_design_brief.md). The revised direction is a search-first landing page with progressively revealed player/team/position analysis, visible search, a sticky header and shared season controls. The existing prototype is not the final approved layout. Implementation is paused for further design discussion.

Use readable typography, restrained colour, ample spacing and a consistent card layout. Prioritize search and season selection, then performance, position and availability/transfer timelines with team context nearby. Use compact source/coverage indicators and accessible chart labels. Avoid decorative ratings, fabricated photographs or unsupported tactical graphics. A prototype can show real available fields and explicit missing states; it must not imply the missing histories already exist.

Tableau remains the planned presentation tool. A different implementation stack, hosting service, publication, or large project restructure requires owner discussion. No site or dashboard has been built or published by this requirements update.
# Future visual reference — owner note

On 2026-10-10, the owner supplied
[Marina Budarina's Dribbble portfolio](https://dribbble.com/marina_uiux) as a
reference for how the finished FutWAR website should eventually look and feel.
This is end-stage design inspiration, not a request to redesign the current site
or interrupt analytical development. No particular portfolio shot, animation,
layout or component has been selected yet. Review specific examples with the
owner when the final visual-design stage begins, while retaining clear analytical
navigation, readable charts and the previously approved interface preferences.


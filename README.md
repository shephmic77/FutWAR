# FutWAR
### Football Wins Above Replacement

## Overview

FutWAR is a data science and sports analytics project aiming to develop a football equivalent of baseball's Wins Above Replacement (WAR).

The project seeks to measure individual player contributions relative to replacement-level players while accounting for positional responsibilities, team quality, opposition strength, league differences, and tactical systems.

Beyond player valuation, FutWAR aims to compare the quality and competitive depth of Europe's Big Five leagues, investigating differences between elite, midtable, and lower-ranked teams.

The project will combine statistical modeling, database management, and interactive data visualization.

## Research Objectives

### 1. Player Valuation

Develop a statistical metric to estimate how much value an individual player contributes above a replacement-level player.

Research questions:
- How much does an individual player contribute to team performance?
- What constitutes a replacement-level player in football?
- How should contributions across different positions be compared?
- How do playing time, team strength, and opposition quality affect estimated value?
- Can player contribution be expressed in expected league points above replacement?

### 2. League and Team Strength

Compare Europe's five major leagues across multiple seasons.

Research questions:
- Which leagues have the strongest elite clubs?
- Which leagues have the strongest midtable and bottom-ranked clubs?
- Which leagues have the greatest competitive depth?
- How does player quality differ between leagues?
- How do league-strength distributions change over time?
- How can player and team performances be compared across leagues on a common scale?

### 3. Tactical and Positional Analysis

Investigate how formations, tactical roles, and playing styles influence player performance and valuation.

Research questions:
- How do formations affect individual statistical contributions?
- How can players with different tactical responsibilities be compared?
- How should a wingback be evaluated relative to a traditional fullback?
- How does a player's performance change across positions or systems?
- Can tactical suitability be estimated separately from overall player value?

## Scope

### Competitions
- Premier League — England
- La Liga — Spain
- Serie A — Italy
- Bundesliga — Germany
- Ligue 1 — France

### Seasons
- 2022–23
- 2023–24
- 2024–25
- 2025–26

### Players

The initial model will focus on outfield players. Goalkeeper valuation will be developed separately because it requires distinct performance measures and modeling methods.

### Data

The project will prioritize player-level, team-level, and match-level statistics. Event-level data and detailed tactical information may be incorporated when reliable coverage is available.

## Potential Statistical Variables

### Attacking
- Non-penalty goals
- Non-penalty expected goals (npxG)
- Expected assists (xA)
- Shots and shot creation
- Finishing performance

### Passing and Ball Progression
- Progressive passes
- Progressive carries
- Key passes
- Successful take-ons
- Passing efficiency

### Defensive Contributions
- Tackles
- Interceptions
- Blocks
- Ball recoveries
- Aerial duels

### Possession and Discipline
- Possession losses
- Dispossessions
- Fouls
- Yellow and red cards

### Contextual Variables
- Position and tactical role
- Minutes played
- Team strength
- Opposition strength
- League strength
- Formation
- Team playing style
- Match circumstances

These variables are preliminary. Their availability, predictive usefulness, and potential overlap will be investigated before finalizing the model.

## Methodology

FutWAR will be developed incrementally.

**Phase 1 — Data Collection and Exploration**

Collect, clean, standardize, and explore historical player, team, and match data across all five leagues.

**Phase 2 — Player Valuation**

Develop an initial player-value model, establish replacement-level baselines, and estimate seasonal contributions above replacement.

**Phase 3 — League Strength**

Evaluate team quality and league depth using cross-league comparisons, historical performance, and player-level estimates.

**Phase 4 — Tactical Context**

Investigate how formations, positions, and tactical responsibilities affect player contributions and comparisons.

**Phase 5 — Model Evaluation**

Compare alternative methods, test performance on unseen data, quantify uncertainty, and document limitations.

**Phase 6 — Visualization**

Build interactive dashboards for player evaluation, team comparisons, league strength, and tactical analysis.

## Technology Stack

- **Python:** Data collection, cleaning, statistical modeling, and evaluation
- **PostgreSQL:** Relational database storage and SQL analysis
- **Tableau:** Interactive dashboards and visualizations
- **Git/GitHub:** Version control and documentation
- **Jupyter Notebook:** Exploratory analysis and experimentation

## Planned Deliverables

1. Standardized multi-season football database
2. FutWAR player-value model and rankings
3. Position-specific replacement-level estimates
4. Comparative Big Five league-strength analysis
5. Formation and tactical-role analysis
6. Statistical model validation and limitations report
7. Interactive Tableau dashboards
8. Documented and reproducible GitHub repository

## Project Status

**Phase 1 — Project setup, data-source evaluation, and exploratory analysis**

FutWAR is an independent research and portfolio project. Its statistical methodology and final results are under development.
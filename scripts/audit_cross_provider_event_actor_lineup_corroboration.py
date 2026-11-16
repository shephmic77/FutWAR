"""Sample whether Wyscout event actors appear in independent OpenPlay lineups.

This is a participation-level corroboration audit, not event-level actor accuracy.
It writes aggregate-only output under ignored reports/ and never changes source data.
"""
from __future__ import annotations

import json
import random
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_cross_provider_goal_scorer_agreement import (  # noqa: E402
    LEAGUES,
    OPENPLAY_DIR,
    WYSCOUT_COUNTRY,
    WYSCOUT_DIR,
    exact_fixture_bridge,
    normalize,
    unique_name_aliases,
    verify_sources,
)

SEED = 20261116
SAMPLE_PER_LEAGUE_FAMILY = 100
CONTEXT_ONLY_FAMILIES = {"Interruption"}
OUTPUT = ROOT / "reports" / "event_actor_lineup_corroboration"


def main() -> None:
    pins = verify_sources()
    rng = random.Random(SEED)
    sampled: dict[tuple[str, str], list[dict]] = defaultdict(list)
    seen_by_group: Counter = Counter()
    wy_players = json.loads((WYSCOUT_DIR / "players.json").read_text(encoding="utf-8"))
    wy_names = {
        int(row["wyId"]): normalize(
            str(row.get("firstName", "")) + " " + str(row.get("lastName", ""))
        )
        for row in wy_players
        if row.get("wyId")
    }

    with zipfile.ZipFile(WYSCOUT_DIR / "matches.zip") as matches_zip, \
            zipfile.ZipFile(WYSCOUT_DIR / "events.zip") as events_zip:
        bridges = {}
        for country, (code, league, _) in LEAGUES.items():
            bridge, summary, _ = exact_fixture_bridge(
                WYSCOUT_COUNTRY[country], code, league, matches_zip
            )
            if summary["score_mismatches"]:
                raise ValueError(f"Independent score check failed for {league}")
            canonical_home_away = {
                int(wy_id): value[2][0]
                for wy_id, value in bridge.items()
            }
            open_id_by_wy_id = {int(wy_id): int(value[0]) for wy_id, value in bridge.items()}
            team_by_wy_id = {int(wy_id): value[1] for wy_id, value in bridge.items()}
            bridges[country] = (code, league, canonical_home_away,
                                open_id_by_wy_id, team_by_wy_id)

        # A deterministic reservoir sample is drawn separately for each
        # league × source event family. Actor ID 0/context-only rows are excluded.
        for country, (code, _, _, _, _) in bridges.items():
            for event in json.load(events_zip.open(f"events_{country}.json")):
                actor_id = int(event.get("playerId") or 0)
                if not actor_id or actor_id not in wy_names:
                    continue
                family = str(event.get("eventName") or "Unknown")
                if family in CONTEXT_ONLY_FAMILIES:
                    continue
                key = (country, family)
                seen_by_group[key] += 1
                limit = SAMPLE_PER_LEAGUE_FAMILY
                row = {
                    "match_id": int(event["matchId"]),
                    "team_id": int(event["teamId"]),
                    "actor_name": wy_names[actor_id],
                }
                if len(sampled[key]) < limit:
                    sampled[key].append(row)
                else:
                    replacement = rng.randrange(seen_by_group[key])
                    if replacement < limit:
                        sampled[key][replacement] = row

    # Build independent OpenPlay participation lists only for sampled fixtures.
    lineup_names: dict[tuple[str, int, str], Counter] = defaultdict(Counter)
    for country, (code, league, _, open_id_by_wy_id, team_by_wy_id) in bridges.items():
        open_ids = set(open_id_by_wy_id.values())
        lineups = pd.read_parquet(OPENPLAY_DIR / "lineups.parquet", columns=[
            "match_id", "comp", "season", "team", "player", "played", "minutes_played",
        ])
        lineups = lineups[(lineups["comp"] == code) & (lineups["season"] == "1718")
                          & lineups["match_id"].isin(open_ids)
                          & lineups["played"].fillna(False)
                          & (lineups["minutes_played"].fillna(0) > 0)]
        # OpenPlay team aliases are already canonicalized by the bridge helper.
        from audit_cross_provider_goal_scorer_agreement import canonicalizer
        canonical = canonicalizer(league)
        for row in lineups.itertuples(index=False):
            name = normalize(row.player)
            if name:
                lineup_names[(country, int(row.match_id), canonical(row.team))][name] += 1

    rows_out = []
    league_totals: Counter = Counter()
    for (country, family), rows in sorted(sampled.items()):
        code, league, fixture_keys, open_id_by_wy_id, team_by_wy_id = bridges[country]
        group = Counter()
        for row in rows:
            wy_id = row["match_id"]
            if wy_id not in open_id_by_wy_id:
                group["sample_fixture_unbridged"] += 1
                continue
            open_id = open_id_by_wy_id[wy_id]
            key = fixture_keys[wy_id]
            side = team_by_wy_id[wy_id].get(row["team_id"])
            if side not in {"home", "away"}:
                group["sample_team_unbridged"] += 1
                continue
            team = key[1] if side == "home" else key[2]
            names = lineup_names[(country, open_id, team)]
            actor = row["actor_name"]
            if names[actor] == 1:
                group["exact_unique_lineup_name"] += 1
            elif names[actor] > 1:
                group["exact_name_ambiguous_in_lineup"] += 1
            elif actor:
                # A conservative, unique token-level name variant is reported
                # separately and never silently promoted to an exact identity.
                aliases = unique_name_aliases(Counter({actor: 1}), names)
                if actor in aliases and names[aliases[actor]] == 1:
                    group["unique_name_variant_lineup_match"] += 1
                else:
                    group["no_lineup_name_match"] += 1
            else:
                group["actor_name_missing"] += 1
        group["sampled_events"] = len(rows)
        group["population_events_with_catalog_actor"] = seen_by_group[(country, family)]
        for k, value in group.items():
            league_totals[k] += value
        rows_out.append({"league": league, "event_family": family, **dict(group)})

    result = {
        "purpose": "Participation-level corroboration of sampled Wyscout event actors against independent OpenPlay match lineups.",
        "not_established": [
            "exact event actor correctness",
            "event-by-event action attribution",
            "identity precision across all seasons",
            "player-value validity",
        ],
        "source_season": "2017-18",
        "sampling": {
            "method": "reservoir sample within each league and Wyscout top-level event family",
            "seed": SEED,
            "maximum_per_league_event_family": SAMPLE_PER_LEAGUE_FAMILY,
            "context_only_families_excluded": sorted(CONTEXT_ONLY_FAMILIES),
            "requires_nonzero_actor_and_catalog_name": True,
        },
        "league_totals": dict(league_totals),
        "groups": rows_out,
        "source_hashes": pins,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "aggregate.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    md = [
        "# Cross-provider event actor participation corroboration",
        "",
        "**Scope:** stratified, seeded sample of 2017–18 Wyscout event actors checked against independently supplied OpenPlay positive-minute lineups, after an exact date/home/away fixture bridge. No scores were used to create the fixture links.",
        "",
        "**Interpretation:** this checks whether the named Wyscout actor appears in the corresponding team's OpenPlay lineup. It does not verify the actor made the specific recorded action, establish all-season identity precision, or validate a player score. Name variants are reported separately from exact unique-name matches. The sample is not a census.",
        "",
        f"- Sampling: up to {SAMPLE_PER_LEAGUE_FAMILY} events per league × event family; seed {SEED}.",
        f"- Event families sampled: {len(rows_out)} league-family groups.",
        f"- Sampled events: {league_totals['sampled_events']:,}.",
        f"- Exact unique lineup-name matches: {league_totals['exact_unique_lineup_name']:,}.",
        f"- Additional unique name-variant matches: {league_totals['unique_name_variant_lineup_match']:,}.",
        f"- Exact-name ambiguities: {league_totals['exact_name_ambiguous_in_lineup']:,}.",
        f"- Unresolved lineup-name checks: {league_totals['no_lineup_name_match']:,}.",
        "",
        "## By league and event family",
        "",
        "| League | Family | Population with catalog actor | Sample | Exact unique lineup name | Unique name-variant candidate | Ambiguous exact name | Unresolved name |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows_out:
        md.append(
            f"| {row['league']} | {row['event_family']} | {row['population_events_with_catalog_actor']:,} | {row['sampled_events']:,} | {row.get('exact_unique_lineup_name', 0):,} | {row.get('unique_name_variant_lineup_match', 0):,} | {row.get('exact_name_ambiguous_in_lineup', 0):,} | {row.get('no_lineup_name_match', 0):,} |"
        )
    md += [
        "",
        "Exact names were normalized for case, diacritics and punctuation. The separate variant screen requires a unique token-level candidate within the OpenPlay match/team lineup; it is not identity confirmation. Unresolved names may reflect aliases, encodings, or player-link errors. The outputs contain aggregates only; source archives remain unchanged and are not copied to the report directory.",
    ]
    (OUTPUT / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"sampled_events": league_totals["sampled_events"],
                      "exact_unique_lineup_name": league_totals["exact_unique_lineup_name"],
                      "unique_name_variant_lineup_match": league_totals["unique_name_variant_lineup_match"],
                      "no_lineup_name_match": league_totals["no_lineup_name_match"],
                      "report": str(OUTPUT / "report.md")}, indent=2))


if __name__ == "__main__":
    main()

"""Summarize selected StatsBomb Open Data coverage after direct registration.

The audit fetches only the competition and match indexes plus event JSON needed
for validation. Event payloads stay in memory and are never written to disk.
Only aggregate counts, source commit, and SHA-256 fingerprints are exported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com/repos/hudl/open-data"
RAW = "https://raw.githubusercontent.com/hudl/open-data"
LEAGUES = {
    "Premier League": "Premier League",
    "La Liga": "La Liga",
    "Serie A": "Serie A",
    "Bundesliga": "1. Bundesliga",
    "Ligue 1": "Ligue 1",
}


def fetch(url: str, limit: int = 80_000_000) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "FutWAR-research-audit/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(limit + 1)
    if len(payload) > limit:
        raise ValueError(f"Response exceeded safety limit ({limit} bytes): {url}")
    return payload


def jname(record: dict, key: str) -> str:
    value = record.get(key)
    return value.get("name", "") if isinstance(value, dict) else ""


def competition_rows(catalog: list[dict]) -> list[dict]:
    rows = []
    for league, source_name in LEAGUES.items():
        for year in range(2017, 2025):
            season_name = f"{year}/{year + 1}"
            found = [c for c in catalog if c.get("competition_name") == source_name
                     and c.get("competition_gender") == "male"
                     and not c.get("competition_youth") and c.get("season_name") == season_name]
            if len(found) > 1:
                raise ValueError(f"Multiple catalog entries for {league} {season_name}")
            row = {"league": league, "season": f"{year}-{str(year + 1)[-2:]}"}
            if found:
                row.update(competition_id=found[0]["competition_id"], season_id=found[0]["season_id"])
            else:
                row.update(competition_id=None, season_id=None)
            rows.append(row)
    return rows


def event_summary(match: dict, events: list[dict]) -> dict:
    """Return quality counts; score agreement is conservative around own goals."""
    expected = Counter()
    for side in ("home_team", "away_team"):
        team = match.get(side) or {}
        if team.get("id") is not None:
            expected[team["id"]] = int(match.get("home_score" if side == "home_team" else "away_score") or 0)

    goals = Counter()
    own_goal_events = 0
    for event in events:
        typ = jname(event, "type")
        if typ == "Own Goal Against":
            own_goal_events += 1
        elif typ == "Shot" and jname(event.get("shot") or {}, "outcome") == "Goal":
            team_id = (event.get("team") or {}).get("id")
            if team_id is not None:
                goals[team_id] += 1
    sides_known = len(expected) == 2
    totals_match = sides_known and sum(expected.values()) == sum(goals.values()) + own_goal_events
    team_scores_match = sides_known and own_goal_events == 0 and all(expected[k] == goals[k] for k in expected)
    return {
        "event_count": len(events),
        "goal_shot_events": sum(goals.values()),
        "own_goal_events": own_goal_events,
        "score_total_reconciled": totals_match,
        "score_by_team_reconciled": team_scores_match,
        "own_goal_review_needed": own_goal_events > 0,
        "events_missing_team": sum((e.get("team") or {}).get("id") is None for e in events),
        "events_missing_player": sum((e.get("player") or {}).get("id") is None for e in events),
        "events_missing_type": sum(not jname(e, "type") for e in events),
    }


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def run(root: Path) -> dict:
    commit = json.loads(fetch(f"{API}/commits/master"))["sha"]
    base = f"{RAW}/{commit}/data"
    catalog_bytes = fetch(f"{base}/competitions.json")
    catalog = json.loads(catalog_bytes)
    rows = []
    for comp in competition_rows(catalog):
        result = {**comp, "match_count": 0, "event_files_available": 0,
                  "event_files_missing": 0, "event_rows": 0,
                  "matches_total_score_reconciled": 0, "matches_team_score_reconciled": 0,
                  "matches_own_goal_review": 0, "event_missing_team": 0,
                  "event_missing_player": 0, "event_missing_type": 0,
                  "match_index_sha256": None, "event_payload_sha256_aggregate": None,
                  "status": "not_listed" if comp["competition_id"] is None else "pending"}
        if comp["competition_id"] is None:
            rows.append(result)
            continue
        match_path = f"matches/{comp['competition_id']}/{comp['season_id']}.json"
        match_bytes = fetch(f"{base}/{match_path}")
        matches = json.loads(match_bytes)
        result["match_count"] = len(matches)
        result["match_index_sha256"] = hashlib.sha256(match_bytes).hexdigest()
        event_hashes = []
        for match in matches:
            match_id = match.get("match_id")
            try:
                payload = fetch(f"{base}/events/{match_id}.json")
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    result["event_files_missing"] += 1
                    continue
                raise
            event_hashes.append(hashlib.sha256(payload).hexdigest())
            result["event_files_available"] += 1
            try:
                events = json.loads(payload)
            except json.JSONDecodeError:
                result["event_files_missing"] += 1
                result["event_files_available"] -= 1
                continue
            summary = event_summary(match, events)
            result["event_rows"] += summary["event_count"]
            result["matches_total_score_reconciled"] += int(summary["score_total_reconciled"])
            result["matches_team_score_reconciled"] += int(summary["score_by_team_reconciled"])
            result["matches_own_goal_review"] += int(summary["own_goal_review_needed"])
            for field in ("events_missing_team", "events_missing_player", "events_missing_type"):
                result[field] += summary[field]
        result["event_payload_sha256_aggregate"] = hashlib.sha256("".join(event_hashes).encode()).hexdigest()
        result["status"] = "audited"
        rows.append(result)

    output = {
        "source": "StatsBomb Open Data (Hudl)", "repository": "https://github.com/hudl/open-data",
        "commit": commit, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "registration_confirmed_by_user": True,
        "raw_match_and_event_files_saved": False,
        "warning": "Selected public sample only; score/event checks do not certify completeness or validate player value.",
        "coverage": rows,
    }
    out_dir = root / "reports/statsbomb_external_audit"
    write_json(out_dir / "coverage_summary.json", output)
    print(json.dumps({"commit": commit, "listed_cells": sum(r["status"] != "not_listed" for r in rows),
                      "audited_cells": sum(r["status"] == "audited" for r in rows),
                      "match_count": sum(r["match_count"] for r in rows),
                      "event_files": sum(r["event_files_available"] for r in rows),
                      "summary": str((out_dir / "coverage_summary.json").relative_to(root))}, indent=2))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registered", action="store_true",
                        help="confirm you completed StatsBomb's requested name/email registration")
    args = parser.parse_args()
    if not args.registered:
        parser.error("StatsBomb's agreement requests name/email registration before access; finish registration, then rerun with --registered")
    run(Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    main()

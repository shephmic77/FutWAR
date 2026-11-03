"""Check linked main/additional roster positions for repeated display codes."""
import json
import re
import unicodedata
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYER_DATA = ROOT / "reports/explorer/data.json"
ROSTER_DATA = ROOT / "reports/explorer/ea_fc_roster_enrichment.json"
OUTPUT = ROOT / "reports/explorer/position_display_audit.json"
ROSTER_DIR = ROOT / "data/processed/ea_fc_position_rosters"
SEASON_FILES = [
    "FIFA18_2017-18_male.csv", "FIFA19_2018-19_male.csv",
    "FIFA20_2019-20_male.csv", "FIFA21_2020-21_male.csv",
    "FIFA22_2021-22_male.csv", "FIFA23_2022-23_male.csv",
    "EASportsFC24_2023-24_male.csv", "EASportsFC25_2024-25_male.csv",
]
ALLOWED = {"GK", "RWB", "RB", "CB", "LWB", "LB", "CDM", "CM", "CAM", "LM", "RM", "RW", "LW", "ST"}
PROFILE_MAP = {"DM": "CDM", "AM": "CAM", "CF": "ST", "SS": "ST"}


def normalize(value):
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def profile_position(record, historical_display_role=None):
    code = str(record.get("display_role") or historical_display_role or record.get("position") or "").strip().upper()
    code = PROFILE_MAP.get(code, code)
    return code if code in ALLOWED else None


def audit_roster_source():
    """Audit every acquired men's roster row, including unlinked players."""
    counts = Counter()
    examples = []
    for filename in SEASON_FILES:
        path = ROSTER_DIR / filename
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                counts["roster_rows_checked"] += 1
                if row.get("game_edition") == "EA Sports FC 25":
                    primary = (row.get("Position") or "").strip()
                    alternatives = [x.strip() for x in (row.get("Alternative positions") or "").split(",") if x.strip()]
                    if primary and primary in alternatives:
                        counts["source_primary_repeated_in_alternatives"] += 1
                        if len(examples) < 10:
                            examples.append({"edition": row.get("game_edition"), "player": row.get("Name"), "primary": primary, "alternatives": alternatives})
                    if len(alternatives) != len(set(alternatives)):
                        counts["duplicate_source_alternative_codes"] += 1
                else:
                    listed = [x.strip() for x in (row.get("player_positions") or "").split(",") if x.strip()]
                    if len(listed) != len(set(listed)):
                        counts["duplicate_source_listed_codes"] += 1
                        if len(examples) < 10:
                            examples.append({"edition": row.get("game_edition"), "player": row.get("long_name"), "listed_positions": listed})
    return counts, examples


def main():
    records = json.loads(PLAYER_DATA.read_text(encoding="utf-8"))["records"]
    enrichment = json.loads(ROSTER_DATA.read_text(encoding="utf-8"))["by_record_id"]
    grouped = {}
    provider_ids = {}
    for record in records:
        birth_year = (record.get("details") or {}).get("birth_year")
        key = normalize(record.get("name")) + "|" + (str(birth_year) if birth_year else "unknown:" + record["id"])
        grouped.setdefault(key, []).append(record)
        if record.get("provider_player_id"):
            provider_ids.setdefault(key, set()).add(str(record["provider_player_id"]))
    group_roles = {}
    for key, group in grouped.items():
        ids = provider_ids.get(key, set())
        group_id = "provider:" + next(iter(ids)) if len(ids) == 1 else "source:" + key
        group_roles[group_id] = next((row.get("display_role") for row in group if row.get("display_role")), None)
    counts = Counter()
    issues = []
    for record in records:
        roster = enrichment.get(record["id"])
        if not roster:
            counts["unlinked_records"] += 1
            continue
        counts["linked_records"] += 1
        birth_year = (record.get("details") or {}).get("birth_year")
        key = normalize(record.get("name")) + "|" + (str(birth_year) if birth_year else "unknown:" + record["id"])
        ids = provider_ids.get(key, set())
        group_id = "provider:" + next(iter(ids)) if len(ids) == 1 else "source:" + key
        historical_role = group_roles.get(group_id)
        game_primary = roster.get("primary_position")
        allowed = roster.get("allowed_positions") or []
        main = game_primary if game_primary in ALLOWED and game_primary in allowed else profile_position(record, historical_role)
        candidates = (roster.get("alternative_positions") or []) if game_primary else allowed
        additional = [position for position in dict.fromkeys(candidates)
                      if position in ALLOWED and position in allowed
                      and position != main and position != game_primary]
        if game_primary and game_primary in (roster.get("alternative_positions") or []):
            counts["source_primary_repeated_in_alternative_field"] += 1
        if main and main in additional:
            counts["display_main_repeated_as_additional"] += 1
            issues.append({"record_id": record["id"], "player": record["name"],
                           "season": record["season"], "main": main,
                           "additional": additional, "edition": roster.get("edition")})
        if len(additional) != len(set(additional)):
            counts["duplicate_additional_codes"] += 1
        # Check the separate season-by-season Context panel as well. For older
        # editions, the raw list has no primary designation; the displayed
        # profile role is still removed from that list.
        context_main = game_primary if game_primary in ALLOWED and game_primary in allowed else profile_position(record, historical_role)
        context_source = roster.get("alternative_positions") or [] if game_primary else allowed
        context_positions = [position for position in dict.fromkeys(context_source)
                             if position in ALLOWED and position in allowed
                             and position != context_main and position != game_primary]
        if context_main and context_main in context_positions:
            counts["context_main_repeated_as_alternative"] += 1
        if len(context_positions) != len(set(context_positions)):
            counts["duplicate_context_alternatives"] += 1
    source_counts, source_examples = audit_roster_source()
    result = {
        "records_checked": len(records),
        "linked_records": counts["linked_records"],
        "unlinked_records": counts["unlinked_records"],
        "explicit_source_primary_repeated_in_alternatives": counts["source_primary_repeated_in_alternative_field"],
        "display_main_repeated_as_additional": counts["display_main_repeated_as_additional"],
        "duplicate_additional_codes": counts["duplicate_additional_codes"],
        "context_main_repeated_as_alternative": counts["context_main_repeated_as_alternative"],
        "duplicate_context_alternatives": counts["duplicate_context_alternatives"],
        **source_counts,
        "source_examples": source_examples,
        "issues": issues,
        "main_position_policy": "Use explicit EA Sports FC 25 primary when present; otherwise use the existing profile role. Additional roles are unique, allowed source-listed roles after removing the displayed main and explicit primary. Older FIFA/FC position lists do not encode a verified primary/secondary split.",
        "writes_to_player_or_roster_data": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "issues"}, indent=2))
    if issues:
        raise SystemExit(f"Found {len(issues)} repeated main/additional display positions")


if __name__ == "__main__":
    main()

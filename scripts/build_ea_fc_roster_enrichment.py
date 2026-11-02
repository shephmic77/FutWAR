"""Build a conservative EA/FIFA game-roster link for FutWAR player-season rows.

The source panel is separate context, never match-played-position evidence. Only
exact normalized name/season links with corroborating birth-year and club-season
evidence (or exact name/season/club evidence for FC25, whose file lacks DOB) are
linked. Ambiguous and unsupported matches remain unlinked for review.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "ea_fc_position_rosters"
EXPLORER = ROOT / "reports" / "explorer" / "data.json"
OUTPUT = ROOT / "reports" / "explorer" / "ea_fc_roster_enrichment.json"
ALLOWED = {"GK", "RWB", "RB", "CB", "LWB", "LB", "CDM", "CM", "CAM", "LM", "RM", "RW", "LW", "ST"}
SEASON_EDITION = {
    "2017-18": ("FIFA18", "FIFA 18"),
    "2018-19": ("FIFA19", "FIFA 19"),
    "2019-20": ("FIFA20", "FIFA 20"),
    "2020-21": ("FIFA21", "FIFA 21"),
    "2021-22": ("FIFA22", "FIFA 22"),
    "2022-23": ("FIFA23", "FIFA 23"),
    "2023-24": ("EASportsFC24", "EA Sports FC 24"),
    "2024-25": ("EASportsFC25", "EA Sports FC 25"),
}
CLUB_ALIASES = {
    "brighton": "brighton hove albion",
    "brighton and hove albion": "brighton hove albion",
    "bournemouth": "bournemouth",
    "afc bournemouth": "bournemouth",
    "man utd": "manchester united",
    "manchester utd": "manchester united",
    "man united": "manchester united",
    "wolves": "wolverhampton wanderers",
    "tottenham": "tottenham hotspur",
    "spurs": "tottenham hotspur",
    "west brom": "west bromwich albion",
    "west ham": "west ham united",
    "newcastle": "newcastle united",
    "leicester": "leicester city",
    "athletic bilbao": "athletic club",
    "ath bilbao": "athletic club",
    "betis": "real betis",
    "paris sg": "paris saint germain",
    "psg": "paris saint germain",
    "inter": "inter milan",
    "internazionale": "inter milan",
    "milan": "ac milan",
    "roma": "as roma",
    "lazio": "ss lazio",
    "napoli": "ssc napoli",
    "bayern munchen": "bayern munich",
    "koln": "cologne",
    "koln 1 fc": "cologne",
    "olympique marseille": "marseille",
    "olympique lyonnais": "lyon",
    "monaco": "as monaco",
}
GENERIC_CLUB_WORDS = {"fc", "afc", "cf", "ac", "sc", "ssc", "as", "fbc", "football", "club"}
NATION_CODES = {
    "Albania":"ALB", "Algeria":"ALG", "Angola":"ANG", "Argentina":"ARG", "Armenia":"ARM",
    "Australia":"AUS", "Austria":"AUT", "Bangladesh":"BAN", "Burundi":"BDI", "Belgium":"BEL",
    "Benin":"BEN", "Bermuda":"BER", "Burkina Faso":"BFA", "Bosnia and Herzegovina":"BIH",
    "Bolivia":"BOL", "Brazil":"BRA", "Bulgaria":"BUL", "Canada":"CAN", "Republic of the Congo":"CGO",
    "Chad":"CHA", "Chile":"CHI", "China PR":"CHN", "China":"CHN", "Cote d'Ivoire":"CIV",
    "Cameroon":"CMR", "DR Congo":"COD", "Colombia":"COL", "Comoros":"COM", "Cape Verde":"CPV",
    "Costa Rica":"CRC", "Croatia":"CRO", "Central African Republic":"CTA", "Cuba":"CUB",
    "Curacao":"CUW", "Cyprus":"CYP", "Czech Republic":"CZE", "Denmark":"DEN",
    "Dominican Republic":"DOM", "Ecuador":"ECU", "Egypt":"EGY", "England":"ENG",
    "Equatorial Guinea":"EQG", "Spain":"ESP", "Estonia":"EST", "Finland":"FIN", "France":"FRA",
    "Faroe Islands":"FRO", "Gabon":"GAB", "Gambia":"GAM", "Georgia":"GEO", "Germany":"GER",
    "Ghana":"GHA", "Guadeloupe":"GLP", "Guinea-Bissau":"GNB", "Greece":"GRE", "Grenada":"GRN",
    "Guatemala":"GUA", "French Guiana":"GUF", "Guinea":"GUI", "Haiti":"HAI", "Honduras":"HON",
    "Hungary":"HUN", "Indonesia":"IDN", "Republic of Ireland":"IRL", "Ireland":"IRL", "Iran":"IRN",
    "Iraq":"IRQ", "Iceland":"ISL", "Israel":"ISR", "Italy":"ITA", "Jamaica":"JAM", "Jordan":"JOR",
    "Japan":"JPN", "Kenya":"KEN", "South Korea":"KOR", "Korea Republic":"KOR", "Saudi Arabia":"KSA",
    "Kosovo":"KVX", "Laos":"LAO", "Libya":"LBY", "Liechtenstein":"LIE", "Lithuania":"LTU",
    "Luxembourg":"LUX", "Latvia":"LVA", "Madagascar":"MAD", "Morocco":"MAR", "Malaysia":"MAS",
    "Moldova":"MDA", "Mexico":"MEX", "North Macedonia":"MKD", "Mali":"MLI", "Malta":"MLT",
    "Montenegro":"MNE", "Mozambique":"MOZ", "Montserrat":"MSR", "Mauritania":"MTN",
    "Martinique":"MTQ", "New Caledonia":"NCL", "Netherlands":"NED", "Nigeria":"NGA",
    "Niger":"NIG", "Northern Ireland":"NIR", "Norway":"NOR", "New Zealand":"NZL", "Panama":"PAN",
    "Paraguay":"PAR", "Peru":"PER", "Philippines":"PHI", "Palestine":"PLE", "Poland":"POL",
    "Portugal":"POR", "North Korea":"PRK", "Puerto Rico":"PUR", "Qatar":"QAT", "Romania":"ROU",
    "South Africa":"RSA", "Russia":"RUS", "Scotland":"SCO", "Senegal":"SEN", "Saint Kitts and Nevis":"SKN",
    "Sierra Leone":"SLE", "San Marino":"SMN", "Serbia":"SRB", "Switzerland":"SUI", "Suriname":"SUR",
    "Slovakia":"SVK", "Slovenia":"SVN", "Sweden":"SWE", "Syria":"SYR", "Tanzania":"TAN",
    "Togo":"TOG", "Trinidad and Tobago":"TRI", "Tunisia":"TUN", "Turkey":"TUR", "Uganda":"UGA",
    "Ukraine":"UKR", "Uruguay":"URU", "United States":"USA", "Uzbekistan":"UZB", "Venezuela":"VEN",
    "Wales":"WAL", "Zambia":"ZAM", "Zimbabwe":"ZIM",
}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


NATION_CODES_NORM = {norm(name): code for name, code in NATION_CODES.items()}


def club_key(value: object) -> str:
    text = norm(value)
    text = re.sub(r"\butd\b", "united", text)
    text = " ".join(word for word in text.split() if word not in GENERIC_CLUB_WORDS)
    return CLUB_ALIASES.get(text, text)


def roster_row(row: dict[str, str], edition: str, season: str) -> dict:
    if edition == "EA Sports FC 25":
        primary = (row.get("Position") or "").strip()
        alternatives = [p for p in (x.strip() for x in (row.get("Alternative positions") or "").split(",")) if p]
        raw = " | ".join(x for x in [primary, ", ".join(alternatives)] if x)
        position_field = "Position + Alternative positions"
        position_codes = ([primary] if primary else []) + alternatives
        semantics = "source separates primary Position and Alternative positions"
    else:
        raw = (row.get("player_positions") or "").strip()
        listed = [p for p in (x.strip() for x in raw.split(",")) if p]
        primary = None
        alternatives = []
        position_field = "player_positions"
        position_codes = listed
        semantics = "source field is an ordered position listing; primary/alternative distinction is not asserted"
    id_field = "player_id" if row.get("player_id") else "url" if row.get("url") else "Name"
    source_id = row.get(id_field, "")
    date = row.get("snapshot_date") or row.get("update_as_of") or ""
    return {
        "edition": edition,
        "season": season,
        "snapshot_date": date,
        "source_id": source_id,
        "source_id_field": id_field,
        "source_name": row.get("long_name") or row.get("short_name") or row.get("Name") or "",
        "source_short_name": row.get("short_name") or row.get("Name") or "",
        "source_birth_year": (row.get("dob") or "")[:4],
        "source_club": row.get("club_name") or row.get("Team") or "",
        "source_nationality": row.get("nationality_name") or row.get("Nation") or "",
        "position_field": position_field,
        "positions_raw": raw,
        "listed_positions": position_codes if edition != "EA Sports FC 25" else [],
        "primary_position": primary,
        "alternative_positions": alternatives,
        "allowed_positions": [p for p in position_codes if p in ALLOWED],
        "unsupported_source_positions": [p for p in position_codes if p not in ALLOWED],
        "position_semantics": semantics,
    }


def read_rosters() -> dict[str, list[dict]]:
    rosters = {}
    for season, (prefix, edition) in SEASON_EDITION.items():
        path = next(PANEL.glob(f"{prefix}_{season}_male.csv"), None)
        if path is None:
            raise FileNotFoundError(f"Missing extracted roster for {edition}: run scripts/extract_ea_fc_position_rosters.py first")
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rosters[season] = [roster_row(row, edition, season) | {"_raw": row} for row in rows]
    return rosters


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=EXPLORER)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8"))["records"]
    rosters = read_rosters()
    record_groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for record in records:
        detail = record.get("details") or {}
        by = str(detail.get("birth_year") or "")
        record_groups[(record["season"], norm(record.get("name")), by)].append(record)

    enrichment = {}
    season_summary = []
    for season, candidates in rosters.items():
        edition = SEASON_EDITION[season][1]
        stats = Counter()
        index: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for candidate in candidates:
            aliases = {norm(candidate.get("source_name")), norm(candidate.get("source_short_name"))} - {""}
            # Several editions shorten well-known names in the source display
            # field (for example "M. Salah") while the long name adds a third
            # surname token. Accept the first two long-name tokens only when
            # the separate birth-year match is also exact and unique.
            full_name = norm(candidate.get("source_name"))
            if len(full_name.split()) >= 3:
                aliases.add(" ".join(full_name.split()[:2]))
            for alias in aliases:
                index[(alias, candidate.get("source_birth_year", ""))].append(candidate)
                if edition == "EA Sports FC 25":
                    index[(alias, "")].append(candidate)
        season_groups = [key for key in record_groups if key[0] == season]
        for group_key in season_groups:
            group_records = record_groups[group_key]
            name, birth_year = group_key[1], group_key[2]
            if not name:
                stats["unlinked_missing_name"] += len(group_records)
                continue
            if edition == "EA Sports FC 25":
                raw_candidates = index.get((name, ""), [])
                basis_type = "exact_name_nationality_season"
            else:
                if not birth_year:
                    stats["unlinked_missing_birth_year"] += len(group_records)
                    continue
                name_aliases = {name}
                name_parts = name.split()
                if len(name_parts) >= 2:
                    name_aliases.add(name_parts[0][0] + " " + name_parts[-1])
                raw_candidates = [c for alias in name_aliases for c in index.get((alias, birth_year), [])]
                basis_type = "exact_or_initial_surname_name_plus_birth_year"
            by_source_id = {c["source_id"]: c for c in raw_candidates if c.get("source_id")}
            if not by_source_id:
                stats["unlinked_no_exact_name_match"] += len(group_records)
                continue
            if len(by_source_id) > 1:
                record_clubs = {club_key(r.get("team")) for r in group_records}
                club_matches = {pid: c for pid, c in by_source_id.items() if club_key(c.get("source_club")) in record_clubs}
                if len(club_matches) == 1:
                    by_source_id = club_matches
                else:
                    stats["unlinked_ambiguous_name_birth_match"] += len(group_records)
                    continue
            candidate = next(iter(by_source_id.values()))
            source_club_key = club_key(candidate.get("source_club"))
            evidence_teams = sorted({r.get("team", "") for r in group_records if club_key(r.get("team")) == source_club_key})
            direct_source_names = {norm(candidate.get("source_name")), norm(candidate.get("source_short_name"))}
            source_tokens = norm(candidate.get("source_name")).split()
            if len(source_tokens) >= 3:
                direct_source_names.add(" ".join(source_tokens[:2]))
            if edition != "EA Sports FC 25" and name not in direct_source_names and not evidence_teams:
                # Initial-plus-surname collisions are accepted only with a
                # matching club-season record as an additional identity check.
                stats["unlinked_initial_alias_without_club_corroboration"] += len(group_records)
                continue
            if edition == "EA Sports FC 25":
                # FC25 lacks birth dates. Require a unique exact name and a
                # nationality agreement; this is weaker than the DOB editions.
                record_nations = {str((r.get("details") or {}).get("nationality") or "").upper() for r in group_records}
                source_nation = NATION_CODES_NORM.get(norm(candidate.get("source_nationality", "")), "")
                if not source_nation or source_nation not in record_nations:
                    stats["unlinked_no_nationality_corroboration"] += len(group_records)
                    continue
            # Editions FIFA18-FC24 have a unique exact name + birth-year link.
            # The source roster was captured near edition release, while
            # FutWAR records cover a full season: club differences are retained
            # as a warning instead of discarding valid player identity links.
            item = {k: v for k, v in candidate.items() if k != "_raw"}
            item["match_basis"] = basis_type
            item["corroborating_futwar_teams"] = evidence_teams
            item["club_match_status"] = "matched" if evidence_teams else "roster club differs or is unavailable in season records"
            item["source_row_identity_unique"] = True
            for record in group_records:
                enrichment[record["id"]] = item
            stats["linked_records"] += len(group_records)
            stats["linked_player_season_groups"] += 1
        stats["player_season_records"] = sum(1 for r in records if r["season"] == season)
        stats["roster_players"] = len(candidates)
        stats["position_rows_with_allowed_codes"] = sum(bool(c["allowed_positions"]) for c in candidates)
        stats["position_rows_with_unsupported_codes"] = sum(bool(c["unsupported_source_positions"]) for c in candidates)
        stats["roster_rows_with_alternative_positions"] = sum(bool(c["alternative_positions"] or len(c["listed_positions"]) > 1) for c in candidates)
        season_summary.append({"season": season, "edition": edition, **dict(stats)})

    audit = {
        "purpose": "Season-specific EA/FIFA game-roster position context; not played-position evidence.",
        "join_policy": "FIFA18-FC24: exact normalized name, first two tokens of a longer source name, or initial-plus-surname alias, plus a unique exact birth-year/source-row match within edition. FC25 lacks DOB: exact unique name plus matching nationality. Club agreement is retained as context; differences are visible because the roster is a season-start edition snapshot and statistics cover the full season.",
        "canonical_position_allowlist": sorted(ALLOWED),
        "edition_mapping": {season: edition for season, (_, edition) in SEASON_EDITION.items()},
        "record_count": len(records),
        "linked_record_count": len(enrichment),
        "unlinked_record_count": len(records) - len(enrichment),
        "coverage_pct": round(100 * len(enrichment) / len(records), 3) if records else 0,
        "season_coverage": season_summary,
        "by_record_id": enrichment,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "player_season_records": len(records),
        "linked_records": len(enrichment),
        "unlinked_records": len(records) - len(enrichment),
        "linked_pct": audit["coverage_pct"],
        "seasons": [{k: s[k] for k in ("season", "edition", "player_season_records", "linked_records", "roster_players")} for s in season_summary],
        "audit_output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()

"""Extract season-mapped FIFA/EA Sports FC roster snapshots from local archives.

Raw Kaggle ZIPs stay untouched under data/raw/ea_fc_positions. This script writes
an auditable local derivative under ignored data/processed/ea_fc_position_rosters.
It does not assert game-listed positions were played in real matches.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ea_fc_positions"
OUT = ROOT / "data" / "processed" / "ea_fc_position_rosters"
ALLOWED = {"GK", "RWB", "RB", "CB", "LWB", "LB", "CDM", "CM", "CAM", "LM", "RM", "RW", "LW", "ST"}
EDITION_MAP = {
    "18.0": ("FIFA 18", "2017-18"),
    "19.0": ("FIFA 19", "2018-19"),
    "20.0": ("FIFA 20", "2019-20"),
    "21.0": ("FIFA 21", "2020-21"),
    "22.0": ("FIFA 22", "2021-22"),
    "23.0": ("FIFA 23", "2022-23"),
    "24.0": ("EA Sports FC 24", "2023-24"),
}
SOURCE_INFO = {
    "fc24": {
        "slug": "stefanoleone992/ea-sports-fc-24-complete-player-dataset",
        "license": "CC0: Public Domain (as listed on Kaggle dataset card)",
        "url": "https://www.kaggle.com/datasets/stefanoleone992/ea-sports-fc-24-complete-player-dataset",
        "archive": RAW / "ea_sports_fc_24_complete_player_dataset.zip",
    },
    "fc25": {
        "slug": "nyagami/ea-sports-fc-25-database-ratings-and-stats",
        "license": "Apache 2.0 (as listed on Kaggle dataset card)",
        "url": "https://www.kaggle.com/datasets/nyagami/ea-sports-fc-25-database-ratings-and-stats",
        "archive": RAW / "ea_sports_fc_25_database_ratings_and_stats.zip",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_positions(value: str) -> list[str]:
    """Split only the source's comma-delimited position strings."""
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def write_snapshot(zf: zipfile.ZipFile, member: str, *, edition: str, season: str,
                   sex: str, source: dict, version: str | None = None,
                   card_date: str | None = None) -> dict:
    with zf.open(member) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
        if not reader.fieldnames:
            raise ValueError(f"Missing CSV header in {member}")
        source_fields = reader.fieldnames
        version_counts: Counter[str] = Counter()
        date_counts: Counter[str] = Counter()
        update_counts: Counter[str] = Counter()
        ids: Counter[str] = Counter()
        positions: Counter[str] = Counter()
        alternative_values: Counter[str] = Counter()
        mapped_codes: Counter[str] = Counter()
        alternative_codes: Counter[str] = Counter()
        rows = 0
        position_field = "player_positions" if "player_positions" in source_fields else "Position"
        explicit_alt_field = "Alternative positions" if "Alternative positions" in source_fields else None
        prefix = ["game_edition", "target_futwar_season", "roster_sex", "snapshot_date", "snapshot_date_basis", "source_dataset", "source_license"]
        output_path = OUT / f"{edition.replace(' ', '').replace('Sports', 'Sports')}_{season}_{sex}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8-sig", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=prefix + source_fields, extrasaction="ignore")
            writer.writeheader()
            for row in reader:
                if version is not None and row.get("fifa_version") != version:
                    continue
                rows += 1
                version_counts[row.get("fifa_version", "")] += 1
                date_counts[row.get("update_as_of", "")] += 1
                update_counts[row.get("fifa_update", "")] += 1
                identity = row.get("player_id") or row.get("url") or row.get("Name") or ""
                ids[identity] += 1
                raw_position = row.get(position_field, "") or ""
                positions[raw_position] += 1
                for code in parse_positions(raw_position):
                    mapped_codes[code] += 1
                if explicit_alt_field:
                    alternative_raw = row.get(explicit_alt_field, "") or ""
                    alternative_values[alternative_raw.strip()] += 1
                    for code in parse_positions(alternative_raw):
                        alternative_codes[code] += 1
                row_snapshot = row.get("update_as_of") or card_date or ""
                writer.writerow({
                    "game_edition": edition,
                    "target_futwar_season": season,
                    "roster_sex": sex,
                    "snapshot_date": row_snapshot,
                    "snapshot_date_basis": "source update_as_of field" if row.get("update_as_of") else "Kaggle dataset-card last-updated date; exact roster snapshot date unverified",
                    "source_dataset": source["slug"],
                    "source_license": source["license"],
                    **row,
                })
        if rows == 0:
            output_path.unlink(missing_ok=True)
            return {"edition": edition, "season": season, "sex": sex, "member": member, "rows": 0}
        if len(version_counts) > 1:
            raise ValueError(f"Expected one edition in {member}; observed {version_counts}")
        if version is not None and set(version_counts) != {version}:
            raise ValueError(f"Requested version {version} but found {version_counts}")
        if len(date_counts) > 1:
            raise ValueError(f"Expected one snapshot date in {member}/{version}; observed {date_counts}")
        duplicate_ids = sum(n - 1 for key, n in ids.items() if key and n > 1)
        codes = sorted(mapped_codes)
        return {
            "edition": edition,
            "season": season,
            "sex": sex,
            "source_member": member,
            "rows": rows,
            "unique_source_ids": len([key for key in ids if key]),
            "duplicate_source_id_rows": duplicate_ids,
            "position_field": position_field,
            "explicit_alternative_position_field": explicit_alt_field,
            "position_nonblank_rows": rows - positions.get("", 0),
            "position_missing_rows": positions.get("", 0),
            "source_position_code_counts": dict(sorted(mapped_codes.items())),
            "codes_outside_user_allowed_list": sorted(set(codes) - ALLOWED),
            "explicit_alternative_position_code_counts": dict(sorted(alternative_codes.items())),
            "alternative_codes_outside_user_allowed_list": sorted(set(alternative_codes) - ALLOWED),
            "alternative_position_nonblank_rows": rows - alternative_values.get("", 0) if explicit_alt_field else None,
            "source_position_strings_top_20": positions.most_common(20),
            "version_counts": dict(version_counts),
            "update_counts": dict(update_counts),
            "snapshot_dates": dict(date_counts) if any(date_counts) else {card_date or "unverified": rows},
            "output_csv": str(output_path.relative_to(ROOT)),
            "output_sha256": sha256(output_path),
        }


def main() -> None:
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if not all(info["archive"].exists() for info in SOURCE_INFO.values()):
        missing = [str(x["archive"]) for x in SOURCE_INFO.values() if not x["archive"].exists()]
        raise FileNotFoundError("Missing downloaded raw archive(s): " + ", ".join(missing))
    audit = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "meaning": "EA/FIFA game roster listings; not match-verified played positions or minutes.",
        "allowed_position_codes_requested_by_owner": sorted(ALLOWED),
        "edition_mapping": [],
        "source_archives": [],
        "snapshots": [],
    }
    for key, source in SOURCE_INFO.items():
        audit["source_archives"].append({
            "dataset_slug": source["slug"],
            "dataset_card_url": source["url"],
            "kaggle_card_license": source["license"],
            "archive_path": str(source["archive"].relative_to(ROOT)),
            "archive_bytes": source["archive"].stat().st_size,
            "archive_sha256": sha256(source["archive"]),
        })
        with zipfile.ZipFile(source["archive"]) as zf:
            if key == "fc24":
                for version, (edition, season) in EDITION_MAP.items():
                    snapshot_info = None
                    for sex in ("male", "female"):
                        result = write_snapshot(zf, f"{sex}_players.csv", edition=edition, season=season,
                                                sex=sex, source=source, version=version)
                        if result.get("rows"):
                            audit["snapshots"].append(result)
                            snapshot_info = result
                    audit["edition_mapping"].append({"edition": edition, "season": season,
                        "snapshot_date": next(iter(snapshot_info.get("snapshot_dates", {})), None) if snapshot_info else None,
                        "date_note": "edition roster snapshot date; generally after the league season began"})
            else:
                edition, season, card_date = "EA Sports FC 25", "2024-25", "2024-09-26"
                for sex in ("male", "female"):
                    result = write_snapshot(zf, f"{sex}_players.csv", edition=edition, season=season,
                                            sex=sex, source=source, card_date=card_date)
                    audit["snapshots"].append(result)
                audit["edition_mapping"].append({"edition": edition, "season": season,
                    "snapshot_date": card_date,
                    "date_note": "Kaggle card last-updated date; exact roster snapshot date not stated in CSV"})
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "roster_position_audit.json"
    manifest_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "seasons": len(audit["edition_mapping"]),
        "snapshot_files": len(audit["snapshots"]),
        "total_rows": sum(x["rows"] for x in audit["snapshots"]),
        "edition_rows": [{"edition": x["edition"], "season": x["season"], "sex": x["sex"], "rows": x["rows"], "date": list(x["snapshot_dates"])} for x in audit["snapshots"]],
        "audit": str(manifest_path.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()

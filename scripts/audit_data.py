"""Audit local CSVs without modifying source data or estimating player value."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

LEAGUES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
SEASONS = ["2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(raw, output, config, manifest):
    output.mkdir(parents=True, exist_ok=True)
    summaries, columns, groups, issues = [], [], [], []
    target_counts = Counter()
    mapping_unknown = False
    files = sorted(raw.rglob("*.csv")) if raw.exists() else []
    unsupported = sorted(str(p.relative_to(raw)) for p in raw.rglob("*")
                         if p.is_file() and p.suffix.lower() != ".csv" and p.name != ".gitkeep") if raw.exists() else []
    # Windows filenames are case-insensitive, but pathlib glob behavior varies by host.
    if raw.exists():
        files = sorted(p for p in raw.rglob("*") if p.is_file() and p.suffix.lower() == ".csv")
    for path in files:
        name = path.relative_to(raw).as_posix()
        settings = dict(config)
        settings.update(config.get("files", {}).get(name, {}))
        mapping = {**config.get("columns", {}), **settings.get("columns", {})}
        missing_tokens = set(settings.get("null_tokens", [""]))
        provenance = manifest.get(name, {})
        summary = {"file": name, "sha256": file_hash(path), "bytes": path.stat().st_size,
                   "source_metadata": provenance, "coverage_complete": "not_verified"}
        try:
            with path.open("r", encoding=settings.get("encoding", "utf-8-sig"), newline="") as handle:
                sample = handle.read(65536)
                handle.seek(0)
                delimiter = settings.get("delimiter")
                if delimiter:
                    reader = csv.reader(handle, delimiter=delimiter)
                else:
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                    except csv.Error:
                        dialect = csv.excel
                    reader = csv.reader(handle, dialect)
                header = next(reader, None)
                if not header or any(not col.strip() for col in header) or len(set(header)) != len(header):
                    raise ValueError("CSV requires a nonempty header with unique, nonblank column names")
                indexes = {col: i for i, col in enumerate(header)}
                for semantic, actual in mapping.items():
                    if actual not in indexes:
                        raise ValueError(f"Mapped {semantic} column {actual!r} is absent")
                keys = settings.get("key_columns", [])
                if any(key not in indexes for key in keys):
                    raise ValueError("Configured key column is absent")
                seen, seen_keys = set(), set()
                missing, distinct = Counter(), {col: set() for col in header}
                grouped = defaultdict(lambda: {"rows": 0, "non_null": Counter()})
                rows = malformed = duplicates = duplicate_keys = incomplete_keys = 0
                def value(row, semantic):
                    col = mapping.get(semantic)
                    return row[indexes[col]].strip() if col else ""
                for row in reader:
                    if len(row) != len(header):
                        malformed += 1
                        continue
                    rows += 1
                    values = [v.strip() for v in row]
                    row_key = tuple(row)
                    duplicates += row_key in seen
                    seen.add(row_key)
                    if keys:
                        key = tuple(values[indexes[col]] for col in keys)
                        if any(v in missing_tokens for v in key):
                            incomplete_keys += 1
                        else:
                            duplicate_keys += key in seen_keys
                            seen_keys.add(key)
                    for col, v in zip(header, values):
                        if v in missing_tokens:
                            missing[col] += 1
                        else:
                            distinct[col].add(v)
                    league = value(row, "league")
                    season = value(row, "season")
                    position = value(row, "position")
                    league = settings.get("league_aliases", {}).get(league, league)
                    season = settings.get("season_aliases", {}).get(season, season)
                    league = "unknown" if league in missing_tokens or not league else league
                    season = "unknown" if season in missing_tokens or not season else season
                    position = "unknown" if position in missing_tokens or not position else position
                    group = grouped[(league, season, position)]
                    group["rows"] += 1
                    for col, v in zip(header, values):
                        if v not in missing_tokens:
                            group["non_null"][col] += 1
                    if league in LEAGUES and season in SEASONS:
                        target_counts[(league, season)] += 1
                has_mapping = all(mapping.get(k) for k in ("league", "season"))
                mapping_unknown |= not has_mapping or any("unknown" in key[:2] for key in grouped)
                summary.update(status="audited", rows=rows, column_names=header,
                               malformed_rows=malformed, exact_duplicate_rows=duplicates,
                               key_columns=keys, duplicate_key_rows=duplicate_keys,
                               incomplete_key_rows=incomplete_keys, semantic_columns=mapping)
                for col in header:
                    columns.append({"file": name, "column": col, "rows": rows,
                                    "missing": missing[col], "missing_pct": round(100 * missing[col] / rows, 4) if rows else "",
                                    "distinct_non_null": len(distinct[col])})
                for (league, season, position), group in sorted(grouped.items()):
                    for col in header:
                        count = group["non_null"][col]
                        groups.append({"file": name, "league": league, "season": season,
                                       "position": position, "column": col, "rows": group["rows"],
                                       "non_null": count, "missing_pct": round(100 * (group["rows"] - count) / group["rows"], 4),
                                       "availability": "all_missing" if count == 0 else "partial" if count < group["rows"] else "populated"})
                if malformed:
                    issues.append({"file": name, "issue": "malformed_rows", "detail": str(malformed)})
                if not has_mapping:
                    issues.append({"file": name, "issue": "coverage_mapping_missing", "detail": "Configure league and season column mappings"})
        except (UnicodeError, csv.Error, ValueError, OSError) as error:
            mapping_unknown = True
            summary.update(status="error", error=str(error))
            issues.append({"file": name, "issue": "read_error", "detail": str(error)})
        for field in ("source_url", "retrieved_at", "license_or_terms", "provider", "granularity", "stat_definitions"):
            if not provenance.get(field):
                issues.append({"file": name, "issue": "provenance_missing", "detail": field})
        summaries.append(summary)
    coverage = [{"league": league, "season": season, "observed_rows": target_counts[(league, season)],
                 "status": "no_input_data" if not files else "observed" if target_counts[(league, season)] else "unknown_mapping_or_read_error" if mapping_unknown else "no_observed_rows",
                 "unresolved_mapping_or_read_error": mapping_unknown,
                 "completeness": "not_verified"} for league in LEAGUES for season in SEASONS]
    write_csv(output / "column_quality.csv", ["file", "column", "rows", "missing", "missing_pct", "distinct_non_null"], columns)
    write_csv(output / "stat_availability.csv", ["file", "league", "season", "position", "column", "rows", "non_null", "missing_pct", "availability"], groups)
    write_csv(output / "coverage.csv", ["league", "season", "observed_rows", "status", "unresolved_mapping_or_read_error", "completeness"], coverage)
    write_csv(output / "issues.csv", ["file", "issue", "detail"], issues)
    result = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "raw_directory": str(raw.resolve()),
              "file_count": len(files), "unsupported_files": unsupported, "files": summaries,
              "configuration": config, "coverage": coverage}
    (output / "inventory.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (output / "audit_summary.md").write_text(
        f"# Data audit\n\nCSV files: {len(files)}. Read errors: {sum(s['status'] == 'error' for s in summaries)}.\n\n"
        + ("No input CSVs supplied. Coverage and quality remain unassessed.\n\n" if not files else "See inventory.json, column_quality.csv, stat_availability.csv, coverage.csv and issues.csv.\n\n")
        + "Populated fields and observed rows do not establish complete season or match coverage. Counts include duplicates and may overlap across source files. Malformed records are excluded from row and missingness counts. Unsupported archives require separate inspection. No player-value formula is calculated.\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("reports"))
    parser.add_argument("--config", type=Path, default=Path("audit_config.json"))
    parser.add_argument("--manifest", type=Path, default=Path("data/source_manifest.json"))
    args = parser.parse_args()
    raw, output = args.raw.resolve(), args.output.resolve()
    if raw == output or raw in output.parents or output in raw.parents:
        parser.error("Raw and output directories must not overlap")
    result = audit(raw, output, read_json(args.config), read_json(args.manifest))
    print(f"Audited {result['file_count']} CSV files; reports: {output}")
    return 1 if any(f["status"] == "error" or f.get("malformed_rows", 0) for f in result["files"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())

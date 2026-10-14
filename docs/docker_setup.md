# PostgreSQL in Docker: FutWAR

Docker Desktop must be running. Work from this chat's project folder:

```powershell
Set-Location '<FutWAR project root>'
docker compose up -d --wait
docker compose ps
```

In Docker Desktop, click **Containers** on the left and find the `futwar` group and `futwar-postgres` container. The Models page is a different Docker feature. Docker holds PostgreSQL; SQL commands run against the database inside the container.

The Compose file uses the official PostgreSQL 17 image, a health check, read-only mounts for SQL/import files, and the `futwar_postgres_data` named volume for database storage. Stopping the container retains the volume. The database listens on `127.0.0.1:15432` on Windows. Port 5433 was refused by Windows during setup, so 15432 was used instead.

Open an interactive SQL prompt from PowerShell:

```powershell
docker compose exec postgres psql -U futwar -d futwar
```

At the `futwar=#` prompt, enter:

```sql
SELECT league, season, count(*) AS player_team_records
FROM futwar.player_season_exposure
GROUP BY league, season
ORDER BY league, season;
```

Each SQL statement ends with a semicolon. Enter `\q` to leave the SQL prompt. A helpful second query shows the corrected record:

```sql
SELECT player_name, team_name, season, minutes
FROM futwar.player_season_exposure
WHERE player_name = 'Emanuele Torrasi';
```

To load a new clone of this project after generating the approved processed exports:

```powershell
docker compose exec -T postgres psql -U futwar -d futwar -v ON_ERROR_STOP=1 -f sql/001_staging.sql
docker compose exec -T postgres psql -U futwar -d futwar -f sql/002_load_staging.sql
```

The database and its configured local user are both `futwar`. A random password was stored in the ignored `.env` file. External SQL tools use host `localhost`, port `15432`, database/user `futwar`, and that password. Inside-container `psql` uses the image's local connection authentication. Never paste the `.env` file into a chat or commit it. When setting up another machine, copy `.env.example` to `.env` and supply a unique password before first startup. Changing the file later does not reset an already initialized database password.

Useful PowerShell commands:

```powershell
docker compose stop
docker compose start
docker compose logs --tail 30 postgres
```

Avoid `docker compose down -v`: it removes the database volume. The volume is persistent storage, not a backup. The generated CSVs and lineage allow the current staging database to be rebuilt from the unchanged raw data. Keep raw source files safe.

The existing staging tables are deliberately limited: names are provider labels, records are apparent player-team-seasons, and no final WAR formula or tactical-role classification has been applied. The normalized research schema comes after identity and source-comparability checks.

References: [official PostgreSQL image](https://hub.docker.com/_/postgres), [Docker Compose services](https://docs.docker.com/reference/compose-file/services/).

## Verified setup outcome

The container is healthy and the SQL schema/import scripts ran successfully. Staging contains 22,418 processed records, five leagues and eight seasons. All 40 observed league-season groups are present. The corrected Torrasi record appears once with six minutes and its disputed substitute field null. Database lineage covers all 22,929 raw records. `sql/004_validate_staging.sql` checks these conditions; this remains an availability check, not a completeness certificate.

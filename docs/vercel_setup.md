# Vercel deployment

The public project is [https://futwar.vercel.app/](https://futwar.vercel.app/). The owner has directed that the current football explorer be publicly available for this personal/student project. The site is a research prototype: player identities and some historical roles remain provisional, source definitions differ, and no FutWAR formula or coefficients are finalized. Data and image provenance are shown in the application; owner approval is not presented as an upstream license or independent legal certification.

## Publish a refreshed explorer

Vercel serves the `site/` output directory configured by `vercel.json`. From Windows PowerShell at the repository root:

```powershell
py scripts/package_explorer.py
.\scripts\prepare_vercel_site.ps1
```

The package step rebuilds the local explorer under ignored `reports/explorer/`, then copies the built page and its image assets into `site/`. Review the resulting public files and the displayed source and image credits before committing. The page is self-contained; the asset folder supports image references and fallbacks.

## Deploy through GitHub

The Vercel project should be connected to `shephmic77/FutWAR`, production branch `main`, root directory `./`, with no build command and output directory `site`. Once the reviewed changes are pushed to `main`, Vercel should create a production deployment at the stable `futwar.vercel.app` domain. If automatic deployment is disabled, open the FutWAR project in Vercel and redeploy the latest `main` commit.

The repository is public. Raw source archives, credentials, and local database files stay excluded by `.gitignore`. Do not add unrelated local research outputs or unreviewed files when staging deployment changes.

# Vercel deployment

The public project page is [https://futwar.vercel.app/](https://futwar.vercel.app/). It currently serves a data-free holding page while upstream reuse rights for the player-season statistics and profile imagery are confirmed. The full player explorer remains a local research artifact.

`vercel.json` serves the `site/` folder. Running `py scripts/package_explorer.py` rebuilds the local explorer under ignored `reports/explorer/` and restores the public holding page at `site/index.html`; it does not write player records, search indexes, or images into `site/`. Run `scripts/prepare_vercel_site.ps1` to verify this public artifact before deployment.

Do not publish the local explorer or its generated assets until written redistribution permission is obtained or the underlying public dataset and imagery are replaced with sources whose terms clearly allow this use. The existing source manifest's Kaggle CC0 entry is the uploader's declaration; it does not independently establish upstream rights. The owner's earlier personal/student-use review is retained in the source history, but this public-distribution pause is a precaution pending clarification, not a legal finding.

Use Windows PowerShell from the repository root:

```powershell
py scripts/package_explorer.py
.\scripts\prepare_vercel_site.ps1
node tests/explorer_core.test.cjs
```

The package script preserves a complete local copy for research. Only commit the data-free `site/index.html` for Vercel. Keep raw source archives, credentials, private database files, player bundles, profile photos, and provider-restricted material out of the public deployment.

## Connect Vercel to GitHub

1. Sign in at [Vercel](https://vercel.com/) and choose **Add New → Project**.
2. Connect the GitHub account that owns `shephmic77/FutWAR`, then import the existing `FutWAR` repository.
3. Keep the project root at `./`. The checked-in `vercel.json` sets the output directory to `site`; this is a static HTML project and needs no build command.
4. Deploy. Future pushes to the connected branch will trigger deployments. Use Vercel's preview deployment for review before promoting a version to production.

The repository is public. On 2026-10-16, the main branch history was rewritten and force-pushed to remove the player bundles and source-linked site assets. A scan of reachable Git history found no such paths. Existing clones or caches may retain previous objects; re-clone or reset to the rewritten `main` branch before sharing a local checkout. The public Vercel page remains the data-free holding page.

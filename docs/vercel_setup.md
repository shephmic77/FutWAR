# Vercel deployment

The existing FutWAR GitHub repository is the source of truth for the public site. `vercel.json` selects the static `site/` output directory; Vercel serves `site/index.html` at the project root. The file is a self-contained bundle of the explorer and its player-season data.

## Build or refresh the published site

Use Windows PowerShell from the repository root:

```powershell
py scripts/package_explorer.py
.\scripts\prepare_vercel_site.ps1
node tests/explorer_core.test.cjs
```

Review the explorer locally, then commit and push `site/index.html` together with any related source or documentation changes. `site/index.html` is intentionally tracked and public. Keep raw source archives, credentials, private database files, and provider-restricted material out of Git.

## Connect Vercel to GitHub

1. Sign in at [Vercel](https://vercel.com/) and choose **Add New → Project**.
2. Connect the GitHub account that owns `shepmic77/FutWAR`, then import the existing `FutWAR` repository.
3. Keep the project root at `./`. The checked-in `vercel.json` sets the output directory to `site`; this is a static HTML project and needs no build command.
4. Deploy. Future pushes to the connected branch will trigger deployments. Use Vercel's preview deployment for review before promoting a version to production.

The explorer embeds its data in the HTML, so publishing the site also makes the bundled rows and images available to site visitors. The owner reviewed the included sources and confirmed personal/student project use is permitted. The project records the source names and attribution in its research documentation.

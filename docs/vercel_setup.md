# Vercel deployment

The live FutWAR explorer is available at [https://futwar.vercel.app/](https://futwar.vercel.app/). Share this stable project domain rather than an individual deployment URL, which can return `DEPLOYMENT_NOT_FOUND` if that deployment is removed. The existing FutWAR GitHub repository is the source of truth for the public site. `vercel.json` selects the static `site/` output directory; Vercel serves `site/index.html` at the project root. Player data and a compact search index are separate compressed files, and images are separate assets. The interface can render and enable search while the larger statistics payload downloads.

## Build or refresh the published site

Use Windows PowerShell from the repository root:

```powershell
py scripts/package_explorer.py
.\scripts\prepare_vercel_site.ps1
node tests/explorer_core.test.cjs
```

Review the explorer locally, then commit and push the complete `site/` folder together with related source or documentation changes. Keep raw source archives, credentials, private database files, and provider-restricted material out of Git.

## Connect Vercel to GitHub

1. Sign in at [Vercel](https://vercel.com/) and choose **Add New → Project**.
2. Connect the GitHub account that owns `shepmic77/FutWAR`, then import the existing `FutWAR` repository.
3. Keep the project root at `./`. The checked-in `vercel.json` sets the output directory to `site`; this is a static HTML project and needs no build command.
4. Deploy. Future pushes to the connected branch will trigger deployments. Use Vercel's preview deployment for review before promoting a version to production.

The explorer embeds its data in the HTML, so publishing the site also makes the bundled rows and images available to site visitors. The owner reviewed the included sources and confirmed personal/student project use is permitted. The project records the source names and attribution in its research documentation.

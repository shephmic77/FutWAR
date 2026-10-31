$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$siteRoot = Join-Path $repoRoot "site"
$indexPath = Join-Path $siteRoot "index.html"
$assetPath = Join-Path $siteRoot "assets"

if (-not (Test-Path -LiteralPath $indexPath -PathType Leaf)) {
    throw "Vercel explorer is missing. Run: py scripts/package_explorer.py"
}
$html = Get-Content -LiteralPath $indexPath -Raw
if ($html -notmatch "FutWAR · Football library" -or $html -match "__EXPLORER_DATA__|public player library is temporarily offline") {
    throw "site/index.html is not the built player explorer. Rebuild it with py scripts/package_explorer.py."
}
if ($html -notmatch 'id="explorer-data"') {
    throw "The explorer data payload is missing from the Vercel page."
}
if ($html -notmatch "Player search is ready" -or $html -notmatch "futwar-data.json.gz" -or $html -match '<script id="explorer-data" type="application/json">[A-Za-z0-9+/]{1000}') {
    throw "The page must load search and season data separately so search is usable during the full library download."
}
if (-not (Test-Path -LiteralPath $assetPath -PathType Container)) {
    throw "The public image asset folder is missing. Rebuild it with py scripts/package_explorer.py."
}
$assetCount = (Get-ChildItem -LiteralPath $assetPath -File).Count
foreach ($filename in @("futwar-data.json.gz", "futwar-search.json.gz", "fast_search.js")) {
    if (-not (Test-Path -LiteralPath (Join-Path $siteRoot $filename) -PathType Leaf)) {
        throw "Required public file is missing: site/$filename"
    }
}
Write-Output "Verified public FutWAR explorer: independent early-search index, full data bundle, fast-search code and $assetCount image assets."

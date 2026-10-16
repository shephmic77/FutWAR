param([string]$Destination = "site/index.html")

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$destinationPath = Join-Path $repoRoot $Destination
if (-not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) {
    throw "Public holding page is missing at '$destinationPath'. Run: py scripts/package_explorer.py"
}
$forbidden = @(
    (Join-Path $repoRoot "site/futwar-data.json.gz"),
    (Join-Path $repoRoot "site/futwar-search.json.gz"),
    (Join-Path $repoRoot "site/assets")
)
foreach ($path in $forbidden) {
    if (Test-Path -LiteralPath $path) {
        throw "Refusing public build: source-linked player data or images remain at '$path'. Remove them before deployment."
    }
}
$html = Get-Content -LiteralPath $destinationPath -Raw
if ($html -notmatch "public player library is temporarily offline" -or $html -match "__EXPLORER_DATA__|futwar-data|futwar-search") {
    throw "Refusing public build: site/index.html is not the expected data-free holding page."
}
Write-Output "Verified data-free Vercel site artifact: site/index.html only."

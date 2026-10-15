param([string]$Destination = "site/index.html")

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$destinationPath = Join-Path $repoRoot $Destination
$required = @(
    $destinationPath,
    (Join-Path $repoRoot "site/futwar-data.json.gz"),
    (Join-Path $repoRoot "site/futwar-search.json.gz")
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Public site artifact is incomplete at '$path'. Rebuild it with: py scripts/package_explorer.py"
    }
}
$assets = Join-Path $repoRoot "site/assets"
if (-not (Test-Path -LiteralPath $assets -PathType Container) -or @(Get-ChildItem -LiteralPath $assets -File).Count -eq 0) {
    throw "No external site images were found in '$assets'. Rebuild the public site artifact."
}
$html = Get-Item -LiteralPath $destinationPath
$data = Get-Item -LiteralPath (Join-Path $repoRoot "site/futwar-data.json.gz")
$search = Get-Item -LiteralPath (Join-Path $repoRoot "site/futwar-search.json.gz")
Write-Output "Prepared public site in 'site/' — HTML $([math]::Round($html.Length / 1KB, 1)) KB, player data $([math]::Round($data.Length / 1MB, 1)) MB, search index $([math]::Round($search.Length / 1KB, 1)) KB, and $(@(Get-ChildItem -LiteralPath $assets -File).Count) external images."

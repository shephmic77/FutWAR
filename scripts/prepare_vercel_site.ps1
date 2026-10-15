param(
    [string]$Source = "reports/explorer/FutWAR_Explorer.html",
    [string]$Destination = "site/index.html"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sourcePath = Join-Path $repoRoot $Source
$destinationPath = Join-Path $repoRoot $Destination

if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Generated site not found at '$sourcePath'. Build it first with: py scripts/package_explorer.py"
}

$sourceFile = Get-Item -LiteralPath $sourcePath
if ($sourceFile.Length -gt 100MB) {
    throw "The generated site is $([math]::Round($sourceFile.Length / 1MB, 1)) MB, above Vercel Hobby's current 100 MB CLI source upload limit."
}

New-Item -ItemType Directory -Path (Split-Path -Parent $destinationPath) -Force | Out-Null
Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force

$publishedFile = Get-Item -LiteralPath $destinationPath
if ($publishedFile.Length -ne $sourceFile.Length) {
    throw "Published site size differs from the generated bundle."
}

Write-Output "Prepared public Vercel artifact at '$Destination' ($([math]::Round($publishedFile.Length / 1MB, 1)) MB)."
Write-Output "The GitHub repository and Vercel deployment will contain the full embedded player-season dataset and imagery."

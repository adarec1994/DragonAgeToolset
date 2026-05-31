param(
    [string]$WikiRemote = "https://github.com/adarec1994/DragonAgeToolset.wiki.git",
    [string]$WikiRepoPath = (Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "DragonAgeToolset.wiki"),
    [switch]$NoClean
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $WikiRepoPath)) {
    try {
        git clone $WikiRemote $WikiRepoPath
    } catch {
        throw "Could not clone $WikiRemote. Create/enable the GitHub wiki with one starter page, then run this script again."
    }
}

$wikiRoot = (Resolve-Path -LiteralPath $WikiRepoPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $wikiRoot ".git"))) {
    throw "$wikiRoot is not a git repository."
}

if (-not $NoClean) {
    $wikiExtensions = @(
        "*.mediawiki", "*.md", "*.markdown", "*.mkdn", "*.textile",
        "*.rdoc", "*.org", "*.creole", "*.rst", "*.asciidoc", "*.adoc"
    )
    foreach ($pattern in $wikiExtensions) {
        Get-ChildItem -LiteralPath $wikiRoot -Filter $pattern -File |
            Remove-Item -Force
    }
}

Copy-Item -LiteralPath (Get-ChildItem -LiteralPath $PSScriptRoot -Filter "*.mediawiki" -File).FullName `
    -Destination $wikiRoot `
    -Force

Push-Location $wikiRoot
try {
    git add --all
    $status = git status --porcelain
    if (-not $status) {
        Write-Host "No wiki changes to publish."
        exit 0
    }

    git commit -m "Import Dragon Age Toolset wiki"
    git push
} finally {
    Pop-Location
}

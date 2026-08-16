# Smoke eval with UTF-8 log (Windows PowerShell).
# Usage: .\practice\redteam\smoke\run-smoke.ps1
# Requires: backend on :8003, .env with OPENROUTER_API_KEY and SECURITY_CANARY_TOKEN,
#           promptfoo installed locally: npm install --prefix practice\redteam

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$RedteamDir = Join-Path $RepoRoot "practice\redteam"
$SmokeDir = Join-Path $RedteamDir "smoke"
$Config = Join-Path $SmokeDir "promptfooconfig.yaml"
$JsonOut = Join-Path $SmokeDir "smoke-output.json"
$TxtOut = Join-Path $SmokeDir "smoke-output.txt"
$EnvFile = Join-Path $RepoRoot ".env"
$Promptfoo = Join-Path $RedteamDir "node_modules\.bin\promptfoo.cmd"
if (-not (Test-Path $Promptfoo)) {
    throw "promptfoo not installed. Run: npm install --prefix `"$RedteamDir`""
}
$PromptfooArgs = @(
    "eval",
    "-c", $Config,
    "--env-file", $EnvFile,
    "-o", $JsonOut,
    "--no-cache", "--no-share", "--no-progress-bar"
)

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Push-Location $RepoRoot
try {
    $log = & $Promptfoo @PromptfooArgs 2>&1 | Out-String
    [System.IO.File]::WriteAllText($TxtOut, $log, $utf8NoBom)
    Write-Host $log
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

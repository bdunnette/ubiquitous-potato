<#
.SYNOPSIS
    Deploy or update the Django application to AWS Lambda using Zappa and uv.
.PARAMETER Stage
    The Zappa stage to target ('dev' or 'prod'). Defaults to 'dev'.
.PARAMETER Initial
    Switch indicating if this is an initial deployment (zappa deploy) vs update.
#>
param (
    [string]$Stage = "dev",
    [switch]$Initial
)

$ErrorActionPreference = "Stop"

Write-Host "==> Checking prerequisites..." -ForegroundColor Cyan
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed or not in PATH. Please install uv: https://docs.astral.sh/uv/"
    exit 1
}

Write-Host "==> Syncing dependencies with uv..." -ForegroundColor Cyan
uv sync

Write-Host "==> Collecting static assets for WhiteNoise..." -ForegroundColor Cyan
$env:USE_S3_SQLITE = "false"
uv run python manage.py collectstatic --noinput

if ($Initial) {
    Write-Host "==> Performing initial deployment (zappa deploy $Stage)..." -ForegroundColor Green
    uv run zappa deploy $Stage
} else {
    Write-Host "==> Updating existing deployment (zappa update $Stage)..." -ForegroundColor Green
    uv run zappa update $Stage
}

Write-Host "==> Executing remote database migrations on Lambda..." -ForegroundColor Cyan
uv run zappa manage $Stage migrate

Write-Host "==> Deployment finished successfully!" -ForegroundColor Green

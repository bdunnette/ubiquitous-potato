<#
.SYNOPSIS
    Execute any Zappa command inside a Linux Docker container using uv.
    Ensures 100% Linux binary compatibility when deploying from Windows.
    Supports both arm64 (AWS Graviton default) and amd64 architectures.
.PARAMETER Platform
    Target platform: 'linux/arm64', 'linux/amd64', 'arm64', or 'amd64'.
    Defaults to $env:DOCKER_DEFAULT_PLATFORM or 'linux/arm64'.
.EXAMPLE
    .\scripts\zappa-docker.ps1 update dev
    .\scripts\zappa-docker.ps1 -Platform amd64 update dev
    .\scripts\zappa-docker.ps1 manage dev migrate
#>
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("linux/arm64", "linux/amd64", "arm64", "amd64")]
    [string]$Platform = $(if ($env:DOCKER_DEFAULT_PLATFORM) { $env:DOCKER_DEFAULT_PLATFORM } else { "linux/arm64" }),

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ZappaArgs
)

if (-not $ZappaArgs) {
    $ZappaArgs = @("status", "dev")
}

# Normalize platform string (e.g. "arm64" -> "linux/arm64")
if ($Platform -notlike "linux/*") {
    $Platform = "linux/$Platform"
}
$tagSuffix = $Platform -replace '/', '-'
$imageTag = "django-zappa-deployer:$tagSuffix"

Write-Host "==> Building Linux deployment container with uv for platform $Platform..." -ForegroundColor Cyan
docker build --platform $Platform -t $imageTag .

$awsDir = Join-Path $HOME ".aws"
$currentDir = (Get-Location).Path
$region = if ($env:AWS_DEFAULT_REGION) { $env:AWS_DEFAULT_REGION } else { "us-east-2" }

Write-Host "==> Executing: zappa $($ZappaArgs -join ' ') inside Linux ($Platform) container..." -ForegroundColor Green
docker run --platform $Platform --rm `
    -v "${awsDir}:/root/.aws:ro" `
    -v "${currentDir}:/app" `
    -e AWS_PROFILE=$env:AWS_PROFILE `
    -e AWS_DEFAULT_REGION=$region `
    $imageTag $ZappaArgs

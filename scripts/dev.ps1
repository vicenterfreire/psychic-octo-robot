[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet("backend", "frontend")]
    [string] $Service
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$localEnvironmentFile = Join-Path $repositoryRoot ".env"

. (Join-Path $PSScriptRoot "local-environment.ps1")
Import-LocalEnvironment -Path $localEnvironmentFile

$hostConfiguration = Get-LocalHostConfiguration
$backendPort = Get-LocalPort -Name "BACKEND_PORT" -Default 8000
$frontendPort = Get-LocalPort -Name "FRONTEND_PORT" -Default 5173
$frontendOrigin = "http://$($hostConfiguration.PublicHost):$frontendPort"
$backendApiUrl = "http://$($hostConfiguration.PublicHost):$backendPort/api"

if ($Service -eq "backend") {
    $env:FRONTEND_ORIGIN = $frontendOrigin
    Write-Output "Backend bind: http://$($hostConfiguration.BindAddress):$backendPort"
    Write-Output "Allowed frontend origin: $frontendOrigin"

    $virtualEnvironmentPython = Join-Path $repositoryRoot "backend\.venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $virtualEnvironmentPython -PathType Leaf) {
        & $virtualEnvironmentPython -m uvicorn backend.main:app `
            --app-dir (Join-Path $repositoryRoot "backend\src") `
            --reload `
            --reload-dir (Join-Path $repositoryRoot "backend") `
            --host $hostConfiguration.BindAddress `
            --port $backendPort
    }
    else {
        & uv --directory (Join-Path $repositoryRoot "backend") run uvicorn backend.main:app `
            --reload `
            --host $hostConfiguration.BindAddress `
            --port $backendPort
    }
    exit $LASTEXITCODE
}

$env:VITE_API_URL = $backendApiUrl
Write-Output "Frontend bind: http://$($hostConfiguration.BindAddress):$frontendPort"
Write-Output "Browser URL: $frontendOrigin"
Write-Output "Backend API URL: $backendApiUrl"

& npm --prefix (Join-Path $repositoryRoot "frontend") run dev -- `
    --host $hostConfiguration.BindAddress `
    --port $frontendPort `
    --strictPort
exit $LASTEXITCODE

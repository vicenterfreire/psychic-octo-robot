[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$frontendDirectory = Join-Path $repositoryRoot "frontend"
$backendDirectory = Join-Path $repositoryRoot "backend"
$reportDirectory = Join-Path $repositoryRoot ".artifacts\test-results"
$e2eReport = Join-Path $reportDirectory "e2e.json"

. (Join-Path $PSScriptRoot "test-support.ps1")

$nodePath = Resolve-ProjectNode
$npmCliPath = Resolve-ProjectNpmCli -NodePath $nodePath
$uvPath = Resolve-ProjectUv
$databasePrepared = $false
$e2eExitCode = 1

try {
    Start-ProjectPostgres -RepositoryRoot $repositoryRoot
    $env:PATH = "$(Split-Path -Parent $nodePath);$(Split-Path -Parent $uvPath);$env:PATH"
    $frontendPort = Get-AvailableLoopbackPort
    $backendPort = Get-AvailableLoopbackPort
    $env:E2E_FRONTEND_URL = "http://127.0.0.1:$frontendPort"
    $env:E2E_BACKEND_URL = "http://127.0.0.1:$backendPort"
    $env:DATABASE_URL = Get-IsolatedDatabaseUrl `
        -RepositoryRoot $repositoryRoot `
        -DatabaseName "elite_dev_e2e"
    $env:APP_ENV = "test"
    $env:FRONTEND_ORIGIN = $env:E2E_FRONTEND_URL
    $env:SESSION_COOKIE_SECURE = "false"
    $env:TICKET_HMAC_SECRET = "test-only-hmac-secret-with-at-least-32-bytes"
    $env:VITE_API_URL = "$($env:E2E_BACKEND_URL)/api"
    Invoke-IsolatedDatabaseAction `
        -UvPath $uvPath `
        -BackendDirectory $backendDirectory `
        -Action reset
    $databasePrepared = $true
    Initialize-IsolatedDatabaseSchema -UvPath $uvPath -BackendDirectory $backendDirectory

    New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
    if (Test-Path -LiteralPath $e2eReport -PathType Leaf) {
        Remove-Item -LiteralPath $e2eReport
    }

    Write-Output "Running the cross-role Playwright test..."
    & $nodePath $npmCliPath --prefix $frontendDirectory run test:e2e:run
    $e2eExitCode = $LASTEXITCODE
}
catch {
    Write-Output "Browser test setup failed: $($_.Exception.Message)"
}
finally {
    if ($databasePrepared) {
        try {
            Invoke-IsolatedDatabaseAction `
                -UvPath $uvPath `
                -BackendDirectory $backendDirectory `
                -Action drop
        }
        catch {
            Write-Output "Browser test cleanup failed: $($_.Exception.Message)"
            $e2eExitCode = 1
        }
    }
}

exit $e2eExitCode

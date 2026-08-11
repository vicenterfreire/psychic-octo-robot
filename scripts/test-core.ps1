[CmdletBinding()]
param(
    [switch] $Report
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$frontendDirectory = Join-Path $repositoryRoot "frontend"
$backendDirectory = Join-Path $repositoryRoot "backend"
$reportDirectory = Join-Path $repositoryRoot ".artifacts\test-results"
$frontendReport = Join-Path $reportDirectory "frontend.json"
$backendReport = Join-Path $reportDirectory "backend.xml"

. (Join-Path $PSScriptRoot "test-support.ps1")

$nodePath = Resolve-ProjectNode
$npmCliPath = Resolve-ProjectNpmCli -NodePath $nodePath
$uvPath = Resolve-ProjectUv
$databasePrepared = $false
$frontendExitCode = 1
$backendExitCode = 1

try {
    Start-ProjectPostgres -RepositoryRoot $repositoryRoot
    $env:DATABASE_URL = Get-IsolatedDatabaseUrl `
        -RepositoryRoot $repositoryRoot `
        -DatabaseName "elite_dev_test"
    $env:APP_ENV = "test"
    $env:SESSION_COOKIE_SECURE = "false"
    $env:TICKET_HMAC_SECRET = "test-only-hmac-secret-with-at-least-32-bytes"
    Invoke-IsolatedDatabaseAction `
        -UvPath $uvPath `
        -BackendDirectory $backendDirectory `
        -Action reset
    $databasePrepared = $true
    Initialize-IsolatedDatabaseSchema -UvPath $uvPath -BackendDirectory $backendDirectory

    if ($Report) {
        New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
        foreach ($reportPath in @($frontendReport, $backendReport)) {
            if (Test-Path -LiteralPath $reportPath -PathType Leaf) {
                Remove-Item -LiteralPath $reportPath
            }
        }

        Write-Output "Running frontend tests with a JSON report..."
        & $nodePath $npmCliPath --prefix $frontendDirectory run test -- `
            --reporter=json `
            --outputFile=$frontendReport
        $frontendExitCode = $LASTEXITCODE

        Write-Output "Running backend tests with a JUnit XML report..."
        & $uvPath --directory $backendDirectory run pytest `
            --cov=backend `
            --cov-report=term-missing `
            --junitxml=$backendReport
        $backendExitCode = $LASTEXITCODE
    }
    else {
        Write-Output "Running frontend tests..."
        & $nodePath $npmCliPath --prefix $frontendDirectory run test
        $frontendExitCode = $LASTEXITCODE

        Write-Output "Running backend tests..."
        & $uvPath --directory $backendDirectory run pytest `
            --cov=backend `
            --cov-report=term-missing
        $backendExitCode = $LASTEXITCODE
    }
}
catch {
    Write-Output "Core test setup failed: $($_.Exception.Message)"
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
            Write-Output "Core test cleanup failed: $($_.Exception.Message)"
            $backendExitCode = 1
        }
    }
}

if ($frontendExitCode -ne 0 -or $backendExitCode -ne 0) {
    exit 1
}

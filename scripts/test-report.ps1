[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$reportDirectory = Join-Path $repositoryRoot ".artifacts\test-results"
$frontendReport = Join-Path $reportDirectory "frontend.json"
$backendReport = Join-Path $reportDirectory "backend.xml"
$e2eReport = Join-Path $reportDirectory "e2e.json"
$summaryReport = Join-Path $reportDirectory "summary.json"
$coreTestScript = Join-Path $PSScriptRoot "test-core.ps1"
$browserTestScript = Join-Path $PSScriptRoot "test-e2e.ps1"

New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
foreach ($reportPath in @($frontendReport, $backendReport, $e2eReport, $summaryReport)) {
    if (Test-Path -LiteralPath $reportPath -PathType Leaf) {
        Remove-Item -LiteralPath $reportPath
    }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $coreTestScript -Report
$coreExitCode = $LASTEXITCODE

& powershell -NoProfile -ExecutionPolicy Bypass -File $browserTestScript
$e2eExitCode = $LASTEXITCODE

$frontendResult = if (Test-Path -LiteralPath $frontendReport -PathType Leaf) {
    Get-Content -LiteralPath $frontendReport -Raw | ConvertFrom-Json
}
$backendResult = if (Test-Path -LiteralPath $backendReport -PathType Leaf) {
    [xml](Get-Content -LiteralPath $backendReport -Raw)
}
$e2eResult = if (Test-Path -LiteralPath $e2eReport -PathType Leaf) {
    Get-Content -LiteralPath $e2eReport -Raw | ConvertFrom-Json
}
$backendTestSuite = $backendResult.testsuites.testsuite
$e2eStats = $e2eResult.stats
$frontendExitCode = if ($frontendResult -and $frontendResult.numFailedTests -eq 0) { 0 } else { 1 }
$backendExitCode = if (
    $backendTestSuite -and
    [int] $backendTestSuite.failures -eq 0 -and
    [int] $backendTestSuite.errors -eq 0
) { 0 } else { 1 }

$summary = [ordered]@{
    schemaVersion = 2
    generatedAtUtc = [DateTime]::UtcNow.ToString("o")
    success = $coreExitCode -eq 0 -and $e2eExitCode -eq 0
    frontend = [ordered]@{
        exitCode = $frontendExitCode
        format = "vitest-json"
        report = ".artifacts/test-results/frontend.json"
        total = $frontendResult.numTotalTests
        passed = $frontendResult.numPassedTests
        failed = $frontendResult.numFailedTests
    }
    backend = [ordered]@{
        exitCode = $backendExitCode
        format = "junit-xml"
        report = ".artifacts/test-results/backend.xml"
        total = [int] $backendTestSuite.tests
        failures = [int] $backendTestSuite.failures
        errors = [int] $backendTestSuite.errors
        skipped = [int] $backendTestSuite.skipped
    }
    browser = [ordered]@{
        exitCode = $e2eExitCode
        format = "playwright-json"
        report = ".artifacts/test-results/e2e.json"
        total = [int] $e2eStats.expected + [int] $e2eStats.unexpected +
            [int] $e2eStats.flaky + [int] $e2eStats.skipped
        passed = [int] $e2eStats.expected + [int] $e2eStats.flaky
        failed = [int] $e2eStats.unexpected
        skipped = [int] $e2eStats.skipped
    }
}
$summaryJson = $summary | ConvertTo-Json -Depth 4
$summaryJson | Set-Content -LiteralPath $summaryReport -Encoding utf8

Write-Output $summaryJson
if (-not $summary.success) {
    exit 1
}

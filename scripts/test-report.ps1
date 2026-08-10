[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$frontendDirectory = Join-Path $repositoryRoot "frontend"
$backendDirectory = Join-Path $repositoryRoot "backend"
$reportDirectory = Join-Path $repositoryRoot ".artifacts\test-results"
$frontendReport = Join-Path $reportDirectory "frontend.json"
$backendReport = Join-Path $reportDirectory "backend.xml"
$summaryReport = Join-Path $reportDirectory "summary.json"

function Resolve-Executable {
    param(
        [Parameter(Mandatory)]
        [string] $CommandName,

        [Parameter(Mandatory)]
        [string[]] $CandidatePaths
    )

    $resolvedCommand = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($resolvedCommand) {
        return $resolvedCommand.Source
    }

    foreach ($candidatePath in $CandidatePaths) {
        if ($candidatePath -and (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidatePath).Path
        }
    }

    throw "Could not find $CommandName. Install it or add it to PATH."
}

$nodePath = Resolve-Executable -CommandName "node.exe" -CandidatePaths @(
    (Join-Path $env:ProgramFiles "nodejs\node.exe")
)
$npmCliPath = @(
    (Join-Path (Split-Path -Parent $nodePath) "node_modules\npm\bin\npm-cli.js"),
    (Join-Path $env:ProgramFiles "nodejs\node_modules\npm\bin\npm-cli.js")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
if (-not $npmCliPath) {
    throw "Could not find npm-cli.js next to the Node.js installation."
}

$uvPath = Resolve-Executable -CommandName "uv.exe" -CandidatePaths @(
    (Join-Path $env:USERPROFILE ".local\bin\uv.exe")
)

New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
foreach ($reportPath in @($frontendReport, $backendReport, $summaryReport)) {
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

$frontendResult = if (Test-Path -LiteralPath $frontendReport -PathType Leaf) {
    Get-Content -LiteralPath $frontendReport -Raw | ConvertFrom-Json
}
$backendResult = if (Test-Path -LiteralPath $backendReport -PathType Leaf) {
    [xml](Get-Content -LiteralPath $backendReport -Raw)
}
$backendTestSuite = $backendResult.testsuites.testsuite

$summary = [ordered]@{
    schemaVersion = 1
    generatedAtUtc = [DateTime]::UtcNow.ToString("o")
    success = $frontendExitCode -eq 0 -and $backendExitCode -eq 0
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
}
$summaryJson = $summary | ConvertTo-Json -Depth 4
$summaryJson | Set-Content -LiteralPath $summaryReport -Encoding utf8

Write-Output $summaryJson
if (-not $summary.success) {
    exit 1
}

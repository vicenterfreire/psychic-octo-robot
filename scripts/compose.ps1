[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet(
        "up",
        "down",
        "reset",
        "status",
        "logs",
        "app-build",
        "app-up",
        "app-down",
        "app-status",
        "app-logs"
    )]
    [string] $Command = "status",

    [ValidateSet("Auto", "Docker", "Podman")]
    [string] $Provider = "Auto"
)

$ErrorActionPreference = "Stop"
$podmanComposeVersion = "1.6.0"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $repositoryRoot "compose.yaml"
$databaseEnvFile = Join-Path $repositoryRoot "backend\.env.compose"
$databasePort = if ($env:POSTGRES_PORT) { [int] $env:POSTGRES_PORT } else { 5432 }
$backendPort = if ($env:BACKEND_PORT) { [int] $env:BACKEND_PORT } else { 8000 }
$frontendPort = if ($env:FRONTEND_PORT) { [int] $env:FRONTEND_PORT } else { 5173 }

function Find-Executable {
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

    return $null
}

function Test-EngineReady {
    param(
        [Parameter(Mandatory)]
        [string] $ExecutablePath
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    & $ExecutablePath info 2> $null | Out-Null
    $commandSucceeded = $LASTEXITCODE -eq 0
    $ErrorActionPreference = $previousErrorActionPreference
    return $commandSucceeded
}

$dockerPath = Find-Executable -CommandName "docker.exe" -CandidatePaths @(
    (Join-Path $env:ProgramFiles "Docker\Docker\resources\bin\docker.exe")
)
$podmanPath = Find-Executable -CommandName "podman.exe" -CandidatePaths @(
    (Join-Path $env:LOCALAPPDATA "Programs\Podman\podman.exe"),
    (Join-Path $env:ProgramFiles "RedHat\Podman\podman.exe"),
    (Join-Path $env:ProgramFiles "Podman\podman.exe")
)

$requestedProvider = if ($env:COMPOSE_PROVIDER) { $env:COMPOSE_PROVIDER } else { $Provider }
if ($requestedProvider -notin @("Auto", "Docker", "Podman")) {
    throw "COMPOSE_PROVIDER must be Auto, Docker, or Podman."
}

if ($requestedProvider -eq "Docker") {
    if (-not $dockerPath -or -not (Test-EngineReady -ExecutablePath $dockerPath)) {
        throw "Docker was selected, but Docker Desktop is not installed or its engine is not running."
    }
    $resolvedProvider = "Docker"
}
elseif ($requestedProvider -eq "Podman") {
    if (-not $podmanPath -or -not (Test-EngineReady -ExecutablePath $podmanPath)) {
        throw "Podman was selected, but Podman Desktop is not installed or its machine is not running."
    }
    $resolvedProvider = "Podman"
}
elseif ($dockerPath -and (Test-EngineReady -ExecutablePath $dockerPath)) {
    $resolvedProvider = "Docker"
}
elseif ($podmanPath -and (Test-EngineReady -ExecutablePath $podmanPath)) {
    $resolvedProvider = "Podman"
}
else {
    throw "No running Compose provider was found. Start Docker Desktop or Podman Desktop and retry."
}

if ($resolvedProvider -eq "Docker") {
    $composeExecutable = $dockerPath
    $composePrefix = @("compose", "--file", $composeFile, "--project-name", "elite-dev-challenge")
}
else {
    $env:PATH = "$(Split-Path -Parent $podmanPath);$env:PATH"
    $uvPath = Find-Executable -CommandName "uv.exe" -CandidatePaths @(
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe")
    )
    if (-not $uvPath) {
        throw "The validated Podman path requires uv to run its pinned Compose provider."
    }

    $composeExecutable = $uvPath
    $composePrefix = @(
        "tool",
        "run",
        "--from",
        "podman-compose==$podmanComposeVersion",
        "podman-compose",
        "--file",
        $composeFile,
        "--project-name",
        "elite-dev-challenge"
    )
}

Write-Output "Compose provider: $resolvedProvider"

function Invoke-Compose {
    param(
        [Parameter(Mandatory)]
        [string[]] $Arguments
    )

    & $composeExecutable @composePrefix @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Test-TcpPort {
    param(
        [Parameter(Mandatory)]
        [string] $ComputerName,

        [Parameter(Mandatory)]
        [int] $Port
    )

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync($ComputerName, $Port)
        return $connection.Wait(2000) -and $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Resolve-PublishedPortHost {
    param(
        [Parameter(Mandatory)]
        [int] $Port
    )

    $publishedHostName = "127.0.0.1"
    if (Test-TcpPort -ComputerName $publishedHostName -Port $Port) {
        return $publishedHostName
    }

    if ($resolvedProvider -ne "Podman") {
        throw "The container port $Port is not reachable from Windows through Docker."
    }

    $machineAddresses = & $podmanPath machine ssh podman-machine-default `
        "ip -4 -o addr show scope global"
    $machineAddressText = $machineAddresses -join "`n"
    if ($LASTEXITCODE -ne 0 -or $machineAddressText -notmatch "eth0\s+inet\s+([0-9.]+)") {
        throw "The Podman machine address could not be resolved."
    }

    $publishedHostName = $Matches[1]
    if (-not (Test-TcpPort -ComputerName $publishedHostName -Port $Port)) {
        throw "The published Podman port is not reachable on $publishedHostName`:$Port."
    }

    return $publishedHostName
}

function Write-DatabaseEnvironment {
    $databaseHostName = Resolve-PublishedPortHost -Port $databasePort

    @(
        "# Generated by scripts/compose.ps1. Do not commit.",
        "DATABASE_URL=postgresql+psycopg://elite:elite@$databaseHostName`:$databasePort/elite_dev"
    ) | Set-Content -LiteralPath $databaseEnvFile -Encoding utf8

    Write-Output "Backend database connection: $databaseHostName`:$databasePort"
}

function Remove-GeneratedEnvironment {
    if (Test-Path -LiteralPath $databaseEnvFile -PathType Leaf) {
        Remove-Item -LiteralPath $databaseEnvFile
    }
}

switch ($Command) {
    "up" {
        Invoke-Compose -Arguments @(
            "up",
            "--detach",
            "--wait",
            "--wait-timeout",
            "60",
            "postgres"
        )
        Write-DatabaseEnvironment
    }
    "down" {
        Invoke-Compose -Arguments @("down", "--remove-orphans")
        Remove-GeneratedEnvironment
    }
    "reset" {
        Invoke-Compose -Arguments @("down", "--volumes", "--remove-orphans")
        Invoke-Compose -Arguments @(
            "up",
            "--detach",
            "--wait",
            "--wait-timeout",
            "60",
            "postgres"
        )
        Write-DatabaseEnvironment
    }
    "status" {
        Invoke-Compose -Arguments @("ps")
    }
    "logs" {
        Invoke-Compose -Arguments @("logs", "--tail", "100", "postgres")
    }
    "app-build" {
        Invoke-Compose -Arguments @("build", "backend", "frontend")
    }
    "app-up" {
        Invoke-Compose -Arguments @(
            "up",
            "--detach",
            "--wait",
            "--wait-timeout",
            "60",
            "postgres"
        )

        if (-not $env:PUBLIC_HOST) {
            $env:PUBLIC_HOST = Resolve-PublishedPortHost -Port $databasePort
        }

        Invoke-Compose -Arguments @(
            "up",
            "--detach",
            "--build",
            "--wait",
            "--wait-timeout",
            "240"
        )
        Write-DatabaseEnvironment
        Write-Output "Frontend: http://$($env:PUBLIC_HOST):$frontendPort"
        Write-Output "Backend API: http://$($env:PUBLIC_HOST):$backendPort/api"
        Write-Output "Swagger: http://$($env:PUBLIC_HOST):$backendPort/docs"

        if (-not (Test-TcpPort -ComputerName $env:PUBLIC_HOST -Port $frontendPort)) {
            Write-Warning "The stack is healthy inside $resolvedProvider, but PUBLIC_HOST is not reachable from Windows. See TROUBLESHOOTING.md."
        }
    }
    "app-down" {
        Invoke-Compose -Arguments @("down", "--remove-orphans")
        Remove-GeneratedEnvironment
    }
    "app-status" {
        Invoke-Compose -Arguments @("ps")
    }
    "app-logs" {
        Invoke-Compose -Arguments @("logs", "--tail", "100")
    }
}

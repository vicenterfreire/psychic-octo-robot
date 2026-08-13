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
        "app-logs",
        "app-tunnel-up",
        "app-tunnel-url",
        "app-tunnel-logs",
        "app-tunnel-down"
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
$localEnvironmentFile = Join-Path $repositoryRoot ".env"

. (Join-Path $PSScriptRoot "local-environment.ps1")
Import-LocalEnvironment -Path $localEnvironmentFile

$publicHostWasConfigured = -not [string]::IsNullOrWhiteSpace($env:PUBLIC_HOST)
$hostConfiguration = Get-LocalHostConfiguration
$env:APP_BIND_ADDRESS = $hostConfiguration.BindAddress
if ($publicHostWasConfigured) {
    $env:PUBLIC_HOST = $hostConfiguration.PublicHost
}

$databasePort = Get-LocalPort -Name "POSTGRES_PORT" -Default 5432
$backendPort = Get-LocalPort -Name "BACKEND_PORT" -Default 8000
$frontendPort = Get-LocalPort -Name "FRONTEND_PORT" -Default 5173

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

function Resolve-QuickTunnelUrl {
    $attempts = 30
    for ($attempt = 1; $attempt -le $attempts; $attempt++) {
        $previousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $tunnelLogs = & $composeExecutable @composePrefix --profile tunnel logs --no-color cloudflared 2>&1
        $logsSucceeded = $LASTEXITCODE -eq 0
        $ErrorActionPreference = $previousErrorActionPreference

        if ($logsSucceeded) {
            $tunnelLogText = $tunnelLogs -join "`n"
            if ($tunnelLogText -match "https://[a-z0-9-]+\.trycloudflare\.com") {
                return $Matches[0]
            }
        }

        Start-Sleep -Milliseconds 1000
    }

    throw "The Quick Tunnel did not publish a URL within $attempts seconds. Run npm run app:tunnel:logs for details."
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
        Write-Output "Application bind: $($env:APP_BIND_ADDRESS)"
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
    "app-tunnel-up" {
        $env:SESSION_COOKIE_SECURE = "true"
        Invoke-Compose -Arguments @(
            "--profile",
            "tunnel",
            "up",
            "--detach",
            "--build",
            "--wait",
            "--wait-timeout",
            "240"
        )
        Write-DatabaseEnvironment
        $tunnelUrl = Resolve-QuickTunnelUrl
        Write-Output "Temporary public application: $tunnelUrl"
        Write-Output "Temporary public API: $tunnelUrl/api"
        Write-Output "Temporary public Swagger: $tunnelUrl/docs"
        Write-Warning "This URL is public and uses the documented seeded accounts. Stop it with npm run app:tunnel:down immediately after testing."
    }
    "app-tunnel-url" {
        $tunnelUrl = Resolve-QuickTunnelUrl
        Write-Output "Temporary public application: $tunnelUrl"
    }
    "app-tunnel-logs" {
        Invoke-Compose -Arguments @("--profile", "tunnel", "logs", "--tail", "100", "cloudflared")
    }
    "app-tunnel-down" {
        Invoke-Compose -Arguments @("--profile", "tunnel", "down", "--remove-orphans")
        Remove-GeneratedEnvironment
    }
}

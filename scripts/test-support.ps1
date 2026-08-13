$script:TestDatabaseNames = @("elite_dev_test", "elite_dev_e2e")

function Resolve-ProjectExecutable {
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

function Resolve-ProjectNode {
    return Resolve-ProjectExecutable -CommandName "node.exe" -CandidatePaths @(
        (Join-Path $env:ProgramFiles "nodejs\node.exe")
    )
}

function Resolve-ProjectNpmCli {
    param(
        [Parameter(Mandatory)]
        [string] $NodePath
    )

    $npmCliPath = @(
        (Join-Path (Split-Path -Parent $NodePath) "node_modules\npm\bin\npm-cli.js"),
        (Join-Path $env:ProgramFiles "nodejs\node_modules\npm\bin\npm-cli.js")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } |
        Select-Object -First 1

    if (-not $npmCliPath) {
        throw "Could not find npm-cli.js next to the Node.js installation."
    }

    return $npmCliPath
}

function Resolve-ProjectUv {
    return Resolve-ProjectExecutable -CommandName "uv.exe" -CandidatePaths @(
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe")
    )
}

function Get-AvailableLoopbackPort {
    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    try {
        $listener.Start()
        return ([System.Net.IPEndPoint] $listener.LocalEndpoint).Port
    }
    finally {
        $listener.Stop()
    }
}

function Start-ProjectPostgres {
    param(
        [Parameter(Mandatory)]
        [string] $RepositoryRoot
    )

    $composeHook = Join-Path $RepositoryRoot "scripts\compose.ps1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $composeHook up
    if ($LASTEXITCODE -ne 0) {
        throw "Could not start the project PostgreSQL service."
    }
}

function Get-IsolatedDatabaseUrl {
    param(
        [Parameter(Mandatory)]
        [string] $RepositoryRoot,

        [Parameter(Mandatory)]
        [string] $DatabaseName
    )

    if ($DatabaseName -notin $script:TestDatabaseNames) {
        throw "Refusing to create an unrecognized test database: $DatabaseName."
    }

    $databaseEnvFile = Join-Path $RepositoryRoot "backend\.env.compose"
    $databaseLine = Get-Content -LiteralPath $databaseEnvFile |
        Where-Object { $_.StartsWith("DATABASE_URL=") } |
        Select-Object -First 1

    if (-not $databaseLine) {
        throw "The Compose hook did not write a DATABASE_URL."
    }

    $developmentDatabaseUrl = $databaseLine.Substring("DATABASE_URL=".Length)
    if ($developmentDatabaseUrl -notmatch "^(?<prefix>postgresql\+psycopg://.+/)(?<database>[^/?]+)(?<suffix>\?.*)?$") {
        throw "The generated PostgreSQL URL has an unsupported shape."
    }

    return "$($Matches.prefix)$DatabaseName$($Matches.suffix)"
}

function Invoke-IsolatedDatabaseAction {
    param(
        [Parameter(Mandatory)]
        [string] $UvPath,

        [Parameter(Mandatory)]
        [string] $BackendDirectory,

        [Parameter(Mandatory)]
        [ValidateSet("reset", "drop")]
        [string] $Action
    )

    & $UvPath --directory $BackendDirectory run python scripts/isolated_database.py $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Could not $Action the isolated test database."
    }
}

function Initialize-IsolatedDatabaseSchema {
    param(
        [Parameter(Mandatory)]
        [string] $UvPath,

        [Parameter(Mandatory)]
        [string] $BackendDirectory
    )

    & $UvPath --directory $BackendDirectory run alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Could not migrate the isolated test database."
    }

    & $UvPath --directory $BackendDirectory run python -m backend.database.seed
    if ($LASTEXITCODE -ne 0) {
        throw "Could not seed the isolated test database."
    }
}

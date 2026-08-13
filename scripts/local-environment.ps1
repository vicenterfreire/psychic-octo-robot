function Import-LocalEnvironment {
    param(
        [Parameter(Mandatory)]
        [string] $Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }

    $allowedNames = @(
        "APP_BIND_ADDRESS",
        "PUBLIC_HOST",
        "BACKEND_PORT",
        "FRONTEND_PORT",
        "POSTGRES_PORT"
    )

    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -notmatch "^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$") {
            continue
        }

        $name = $Matches[1]
        if ($name -notin $allowedNames) {
            continue
        }

        if (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) {
            continue
        }

        $value = $Matches[2]
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Get-LocalPort {
    param(
        [Parameter(Mandatory)]
        [string] $Name,

        [Parameter(Mandatory)]
        [int] $Default
    )

    $configuredValue = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($configuredValue)) {
        return $Default
    }

    $port = 0
    if (-not [int]::TryParse($configuredValue, [ref] $port) -or $port -lt 1 -or $port -gt 65535) {
        throw "$Name must be an integer between 1 and 65535."
    }

    return $port
}

function Get-LocalHostConfiguration {
    $bindAddress = if ($env:APP_BIND_ADDRESS) { $env:APP_BIND_ADDRESS.Trim() } else { "127.0.0.1" }
    $publicHost = if ($env:PUBLIC_HOST) { $env:PUBLIC_HOST.Trim() } else { "localhost" }

    $parsedAddress = $null
    if (-not [System.Net.IPAddress]::TryParse($bindAddress, [ref] $parsedAddress) -or
        $parsedAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
        throw "APP_BIND_ADDRESS must be an IPv4 address such as 127.0.0.1 or 0.0.0.0."
    }

    if ($publicHost -eq "0.0.0.0") {
        throw "PUBLIC_HOST must be a navigable hostname or IPv4 address, never 0.0.0.0."
    }
    if ($publicHost -notmatch "^[A-Za-z0-9.-]+$") {
        throw "PUBLIC_HOST must not include a scheme, port, path, or IPv6 punctuation."
    }

    return [PSCustomObject]@{
        BindAddress = $bindAddress
        PublicHost = $publicHost
    }
}

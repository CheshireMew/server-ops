param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ToolArguments
)

$ErrorActionPreference = 'Stop'
try {
    $configPath = Join-Path $PSScriptRoot '.local\config.json'
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw 'Missing .local/config.json; see references/usage.md.'
    }
    $runtime = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $pythonPath = [string]$runtime.python_executable
    if (-not [System.IO.Path]::IsPathRooted($pythonPath) -or -not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw 'python_executable must point to an existing absolute Python path.'
    }
    $toolPath = Join-Path $PSScriptRoot 'scripts\server.py'
    & $pythonPath -B $toolPath @ToolArguments
    exit $LASTEXITCODE
}
catch {
    @{ error = $_.Exception.Message } | ConvertTo-Json -Compress
    exit 1
}

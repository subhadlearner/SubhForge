param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $SubhForgeArgs
)

$Script = Join-Path $PSScriptRoot "tools\subhforge.py"

function Test-PythonCommand {
    param(
        [string] $Command,
        [string[]] $PrefixArgs
    )

    try {
        & $Command @PrefixArgs --version *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    if (Test-PythonCommand "py" @("-3")) {
        & py -3 $Script @SubhForgeArgs
        exit $LASTEXITCODE
    }
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    if (Test-PythonCommand "python" @()) {
        & python $Script @SubhForgeArgs
        exit $LASTEXITCODE
    }
}

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    if (Test-PythonCommand "python3" @()) {
        & python3 $Script @SubhForgeArgs
        exit $LASTEXITCODE
    }
}

Write-Error "No working Python 3 interpreter was found. Install Python 3.8+ and ensure 'py -3', 'python', or 'python3' can execute successfully."
exit 2

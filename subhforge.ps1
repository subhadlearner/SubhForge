param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $SubhForgeArgs
)

$Script = Join-Path $PSScriptRoot "tools\subhforge.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $Script @SubhForgeArgs
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $Script @SubhForgeArgs
    exit $LASTEXITCODE
}

Write-Error "Python 3 was not found. Install Python 3.8+ and ensure 'py' or 'python' is on PATH."
exit 2

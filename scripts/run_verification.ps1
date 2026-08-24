$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $projectPython)) {
    throw "Project interpreter not found at .venv\Scripts\python.exe"
}

function Invoke-VerificationStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "`n== $Name ==" -ForegroundColor Cyan
    & $projectPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Push-Location $repositoryRoot
try {
    Invoke-VerificationStep "Automated tests" @(
        "-m", "pytest", "-q", "-p", "no:cacheprovider"
    )
    Invoke-VerificationStep "Python compilation" @(
        "-m", "compileall", "-q", "src", "tests"
    )
    Invoke-VerificationStep "Dependency compatibility" @(
        "-m", "pip", "check"
    )
}
finally {
    Pop-Location
}

Write-Host "`nGesture Controls verification completed successfully." -ForegroundColor Green

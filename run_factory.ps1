param(
    [int]$Workers = 4,
    [double]$Duration = 30.0,
    [string]$ModelVersion = "v3",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$Python = "C:\Users\payal\AppData\Local\Programs\Python\Python312\python.exe"

$CMake = "C:\msys64\ucrt64\bin\cmake.exe"

$Compiler = "C:/msys64/ucrt64/bin/g++.exe"

Write-Host ""
Write-Host "============================================"
Write-Host "Vehicle Simulation Factory"
Write-Host "============================================"
Write-Host "Workers:       $Workers"
Write-Host "Duration:      $Duration s"
Write-Host "Model version: $ModelVersion"
Write-Host "============================================"

Set-Location $Root

Write-Host ""
Write-Host "[1/5] Configuring CMake..."

& $CMake `
    -S "$Root\cpp" `
    -B "$Root\build" `
    -G Ninja `
    "-DCMAKE_CXX_COMPILER=$Compiler"

if ($LASTEXITCODE -ne 0) {
    throw "CMake configuration failed."
}

Write-Host ""
Write-Host "[2/5] Building simulation runner..."

& $CMake `
    --build "$Root\build"

if ($LASTEXITCODE -ne 0) {
    throw "C++ build failed."
}

if (-not $SkipTests) {
    Write-Host ""
    Write-Host "[3/5] Running automated tests..."

    & $Python `
        -m pytest `
        "$Root\tests" `
        -v

    if ($LASTEXITCODE -ne 0) {
        throw "Automated tests failed."
    }
}
else {
    Write-Host ""
    Write-Host "[3/5] Tests skipped."
}

Write-Host ""
Write-Host "[4/5] Running full simulation factory..."

& $Python `
    "$Root\factory\run_factory.py" `
    --workers $Workers `
    --model-version $ModelVersion `
    --duration $Duration

if ($LASTEXITCODE -ne 0) {
    throw "Simulation factory failed."
}

Write-Host ""
Write-Host "[5/5] Generating analysis plots..."

& $Python `
    "$Root\analysis\plot_performance.py"

if ($LASTEXITCODE -ne 0) {
    throw "Performance plotting failed."
}

Write-Host ""
Write-Host "============================================"
Write-Host "Pipeline completed successfully"
Write-Host "============================================"
Write-Host "Reports:"
Write-Host "$Root\results\reports"
Write-Host "============================================"
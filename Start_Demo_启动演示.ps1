param([switch]$Dev)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$demoPython = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $demoPython)) { throw 'Run Setup_安装依赖.ps1 first.' }
if (-not $Dev -and -not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\dist\index.html'))) { throw 'Build the frontend with pnpm build first.' }
Write-Host 'Local fictional demo: http://127.0.0.1:8000 (Ctrl+C to stop)'
Set-Location -LiteralPath $projectRoot
& $demoPython -m uvicorn backend.main_主程序:app --host 127.0.0.1 --port 8000

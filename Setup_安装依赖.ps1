$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$basePython = (Get-Command python -ErrorAction Stop).Source
& $basePython -m venv (Join-Path $projectRoot 'backend\.venv')
$demoPython = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
& $demoPython -m pip install -r (Join-Path $projectRoot 'backend\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency install failed.' }
Set-Location -LiteralPath (Join-Path $projectRoot 'frontend')
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    pnpm install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency install failed.' }
    pnpm build
} elseif (Get-Command npm -ErrorAction SilentlyContinue) {
    npm install
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency install failed.' }
    npm run build
} else {
    throw 'Install Node.js and pnpm or npm first.'
}
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }

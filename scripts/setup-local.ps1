param([switch]$DownloadModelsAndTools,[switch]$PrepareLibrary)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    & py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Installer Python 3.11 64 bits avec son lanceur py.' }
}
& $pythonPath -m pip install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation Python interrompue.' }
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $projectRoot 'local_data\browsers'
& $pythonPath -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw 'Installation de Chromium interrompue.' }
Push-Location -LiteralPath (Join-Path $projectRoot 'frontend')
try { & npm ci; if ($LASTEXITCODE -ne 0) { throw 'Installation frontend interrompue.' } }
finally { Pop-Location }
if ($DownloadModelsAndTools) {
    & $pythonPath scripts/prepare-local-ai.py
    if ($LASTEXITCODE -ne 0) { throw 'Préparation des modèles/outils interrompue.' }
}
$env:PYTHONPATH = Join-Path $projectRoot 'backend'
if (-not $env:ONMT_QVD_ROOT -and -not $env:ONMT_SOURCES_CONFIG) {
    $referenceRoot = Join-Path $projectRoot 'local_data\qvd-synthetic'
    $referenceFiles = @('commercial.qvd','finance.qvd','performance.qvd')
    $presentCount = @($referenceFiles | Where-Object { Test-Path -LiteralPath (Join-Path $referenceRoot $_) }).Count
    if ($presentCount -eq 0) {
        & $pythonPath -m app.data_access.synthetic
        if ($LASTEXITCODE -ne 0) { throw 'Génération QVD interrompue.' }
    } elseif ($presentCount -ne 3) { throw 'Référence incomplète : les fichiers présents sont conservés. Vérifier les trois QVD avant de poursuivre.' }
    & $pythonPath -m app.data_access.supplement
    if ($LASTEXITCODE -ne 0) { throw 'Préparation des QVD complémentaires interrompue.' }
} else { Write-Output 'Configuration QVD personnalisée conservée ; génération de référence non imposée.' }
if ($PrepareLibrary) {
    & $pythonPath -m app.reports.library --confirm-shared-library
    if ($LASTEXITCODE -ne 0) { throw 'Bibliothèque non préparée ; vérifier E5 et Chromium.' }
}
Write-Output 'Préparation terminée. Démarrer Ollama, importer le Modelfile une fois, puis lancer API et Vite (README).'

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$ollamaExe = Join-Path $projectRoot 'local_data\tools\ollama\ollama.exe'
if (-not (Test-Path -LiteralPath $ollamaExe)) { throw 'Ollama local absent. Exécuter scripts/prepare-local-ai.py.' }
try {
    $activeService = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
    Write-Output 'Ollama est déjà actif sur 127.0.0.1:11434. Aucun second service démarré ; vérifier sa configuration locale.'
    return
} catch { }
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $projectRoot 'local_data\models\ollama'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_CONTEXT_LENGTH = '3072'
& $ollamaExe serve

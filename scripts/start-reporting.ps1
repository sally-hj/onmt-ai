param([switch]$Templates, [switch]$DemoEmbeddings, [switch]$DisableOCR)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$env:ONMT_DEMO = '1'  # Les analyses métier restent explicitement synthétiques.
$env:ONMT_DEMO_EMBEDDINGS = if ($DemoEmbeddings) { '1' } else { '0' }
$env:ONMT_GENERATION_MODE = if ($Templates) { 'template' } else { 'ollama' }
$env:ONMT_OLLAMA_MODEL = 'onmt-qwen25:3b'
$env:ONMT_OCR = if ($DisableOCR) { '0' } else { '1' }
$env:ONMT_EMBEDDING_MODEL = Join-Path $projectRoot 'local_data\models\multilingual-e5-small'
$env:ONMT_EMBEDDING_REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
$env:ONMT_MAX_DISTANCE = '0.24'
& '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

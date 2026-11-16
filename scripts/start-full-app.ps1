param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$env:ONMT_FULL_APP = '1'
$env:ONMT_DATA_DIR = Join-Path $projectRoot 'local_data\full-app'
$env:ONMT_DEMO = '0'
$env:ONMT_DEMO_EMBEDDINGS = '0'
$env:ONMT_GENERATION_MODE = 'ollama'
$env:ONMT_OLLAMA_MODEL = 'onmt-qwen25:3b'
$env:ONMT_OCR = '1'
$env:ONMT_EMBEDDING_MODEL = Join-Path $projectRoot 'local_data\models\multilingual-e5-small'
$env:ONMT_EMBEDDING_REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
$env:ONMT_MAX_DISTANCE = '0.24'
if (-not $env:ONMT_SOURCES_CONFIG) { $env:ONMT_SOURCES_CONFIG = Join-Path $projectRoot 'config\sources.extended.json' }
if (-not $env:ONMT_MONITOR_INTERVAL) { $env:ONMT_MONITOR_INTERVAL = '60' }
$env:LANGCHAIN_TRACING_V2 = 'false'
$env:LANGSMITH_TRACING = 'false'
& '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $Port

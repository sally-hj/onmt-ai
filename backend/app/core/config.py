import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(ROOT / 'local_data' / 'browsers'))


@dataclass(frozen=True)
class Settings:
    full_app: bool = field(default_factory=lambda: os.getenv('ONMT_FULL_APP', '0') == '1')
    sources_config: Path = field(default_factory=lambda: Path(os.getenv('ONMT_SOURCES_CONFIG',str(ROOT/'config/sources.synthetic.json'))))
    qvd_root: Path = field(default_factory=lambda: Path(os.getenv('ONMT_QVD_ROOT',str(ROOT/'local_data/qvd-synthetic'))))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv('ONMT_DATA_DIR', str(ROOT / 'local_data' / 'reporting'))))
    demo: bool = field(default_factory=lambda: os.getenv('ONMT_DEMO', '0') == '1')
    embedding_model: str = field(default_factory=lambda: os.getenv('ONMT_EMBEDDING_MODEL', str(ROOT / 'local_data' / 'models' / 'multilingual-e5-small')))
    embedding_revision: str = field(default_factory=lambda: os.getenv('ONMT_EMBEDDING_REVISION', 'local-v1'))
    demo_embeddings: bool = field(default_factory=lambda: os.getenv('ONMT_DEMO_EMBEDDINGS', '0') == '1')
    max_distance: float = field(default_factory=lambda: float(os.getenv('ONMT_MAX_DISTANCE', '0.24')))
    ollama_model: str = field(default_factory=lambda: os.getenv('ONMT_OLLAMA_MODEL', ''))
    generation_mode: str = field(default_factory=lambda: os.getenv('ONMT_GENERATION_MODE', 'auto'))
    ollama_timeout: float = field(default_factory=lambda: float(os.getenv('ONMT_OLLAMA_TIMEOUT', '240')))
    ollama_context: int = field(default_factory=lambda: int(os.getenv('ONMT_OLLAMA_CONTEXT', '3072')))
    ocr_enabled: bool = field(default_factory=lambda: os.getenv('ONMT_OCR', '0') == '1')
    tesseract_path: str = field(default_factory=lambda: os.getenv('ONMT_TESSERACT', str(ROOT / 'local_data/tools/tesseract/tesseract.exe')))
    tessdata_path: str = field(default_factory=lambda: os.getenv('ONMT_TESSDATA', str(ROOT / 'local_data/tools/tesseract/tessdata')))
    ocr_languages: str = 'fra+eng+ara'
    ocr_timeout: int = 90
    max_pdf_bytes: int = 20 * 1024 * 1024
    max_pages: int = 200

    def __post_init__(self):
        if self.demo_embeddings and not self.demo:
            raise ValueError('Les embeddings de démonstration exigent ONMT_DEMO=1')
        if self.generation_mode not in ['auto', 'template', 'ollama']:
            raise ValueError('Mode de génération inconnu')
        if self.generation_mode == 'ollama' and not self.ollama_model:
            raise ValueError('ONMT_OLLAMA_MODEL requis pour la rédaction IA')
        if self.ollama_timeout <= 0 or self.ollama_context < 1024:
            raise ValueError('Délai Ollama positif et contexte d’au moins 1024 tokens requis')

    @property
    def uses_llm(self):
        return self.generation_mode == 'ollama' or (self.generation_mode == 'auto' and bool(self.ollama_model))

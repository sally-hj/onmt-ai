import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(ROOT / 'local_data' / 'browsers'))


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv('ONMT_DATA_DIR', str(ROOT / 'local_data' / 'reporting'))))
    demo: bool = field(default_factory=lambda: os.getenv('ONMT_DEMO', '0') == '1')
    embedding_model: str = field(default_factory=lambda: os.getenv('ONMT_EMBEDDING_MODEL', str(ROOT / 'local_data' / 'models' / 'multilingual-e5-small')))
    embedding_revision: str = field(default_factory=lambda: os.getenv('ONMT_EMBEDDING_REVISION', 'local-v1'))
    demo_embeddings: bool = field(default_factory=lambda: os.getenv('ONMT_DEMO_EMBEDDINGS', '0') == '1')
    max_distance: float = 0.35
    ollama_model: str = field(default_factory=lambda: os.getenv('ONMT_OLLAMA_MODEL', ''))
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

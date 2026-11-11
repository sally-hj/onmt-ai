"""OCR Tesseract local ; les scores de reconnaissance ne sont pas des preuves métier."""
import csv
import io
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pypdfium2

from app.core.errors import AppError


class LocalOCR:
    def __init__(self, settings):
        self.settings = settings

    def extract_page(self, content: bytes, page_index: int):
        settings = self.settings
        exe = Path(settings.tesseract_path)
        if not exe.is_file():
            raise AppError('tool_failed', 'Moteur OCR Tesseract local absent ; configurez ONMT_TESSERACT.', 503)
        languages = settings.ocr_languages.split('+')
        if any(not (Path(settings.tessdata_path) / f'{lang}.traineddata').is_file() for lang in languages):
            raise AppError('tool_failed', 'Données OCR manquantes : fra, eng et ara sont requises.', 503)
        try:
            settings.data_dir.mkdir(parents=True, exist_ok=True)
            with pypdfium2.PdfDocument(content) as pdf:
                page = pdf[page_index]
                scale = 200 / 72
                width, height = page.get_size()
                if width * height * scale * scale > 25_000_000:
                    raise AppError('invalid_request', 'Page trop grande pour l’OCR local.', 422)
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil().convert('RGB')
                with tempfile.TemporaryDirectory(prefix='ocr_', dir=settings.data_dir) as temp:
                    input_path = Path(temp) / 'page.png'
                    image.save(input_path)
                    result = subprocess.run([str(exe), str(input_path), 'stdout', '--tessdata-dir',
                                             settings.tessdata_path, '-l', settings.ocr_languages,
                                             '--oem', '1', '--psm', '3', 'tsv'],
                                            capture_output=True, timeout=settings.ocr_timeout,
                                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                image.close()
                bitmap.close()
                page.close()
            if result.returncode:
                raise AppError('tool_failed', 'Tesseract a échoué sur une page ; vérifiez les langues et le moteur.', 503)
            lines, scores = {}, []
            for row in csv.DictReader(io.StringIO(result.stdout.decode('utf-8')), delimiter='\t'):
                text = row.get('text', '').strip()
                confidence = float(row.get('conf', '-1'))
                if not text or confidence < 0:
                    continue
                key = (row['block_num'], row['par_num'], row['line_num'])
                lines.setdefault(key, []).append(text)
                scores.append(confidence)
            text = '\n'.join(' '.join(words) for words in lines.values())
            confidence = round(sum(scores) / len(scores), 2) if scores else None
            warnings = ['ocr_requires_human_review']
            if confidence is None or confidence < 75:
                warnings.append('ocr_low_confidence')
            if re.search(r'\d', text):
                warnings.append('ocr_numbers_and_tables_unverified')
            return text, confidence, warnings
        except AppError:
            raise
        except subprocess.TimeoutExpired as exc:
            raise AppError('tool_failed', 'Délai OCR dépassé ; aucune extraction partielle enregistrée.', 504) from exc
        except Exception as exc:
            raise AppError('tool_failed', 'Échec du rendu ou de la reconnaissance OCR locale.', 503) from exc

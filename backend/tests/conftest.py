import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT, Settings
from app.core.security import demo_access
from app.main import create_app
from app.reports.adapters import SyntheticAnalysisProvider
from app.schemas.report import ReportRequest


def text_pdf(texts):
    """Petit PDF textuel synthétique reproductible, sans outil ou fichier métier externe."""
    objects = [b'', b'', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    page_refs = []
    for text in texts:
        stream = b'BT /F1 12 Tf 50 760 Td '
        for i, line in enumerate(text.splitlines()):
            safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            stream += (b'0 -18 Td ' if i else b'') + b'(' + safe.encode('ascii') + b') Tj '
        stream += b'ET'
        page_id, stream_id = len(objects)+1, len(objects)+2
        page_refs.append(f'{page_id} 0 R')
        objects += [f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>'.encode(),
                    b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    objects[0] = b'<< /Type /Catalog /Pages 2 0 R >>'
    objects[1] = f'<< /Type /Pages /Count {len(texts)} /Kids [{" ".join(page_refs)}] >>'.encode()
    data, offsets = b'%PDF-1.4\n', [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(data)
    data += f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    return data + f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode()


@pytest.fixture
def access():
    return demo_access()


@pytest.fixture
def request_body():
    return ReportRequest.model_validate_json((ROOT / 'examples/contracts/report_request.json').read_text(encoding='utf-8'))


@pytest.fixture
def application(tmp_path):
    return create_app(Settings(full_app=False,data_dir=tmp_path, demo=True, demo_embeddings=True, ollama_model='',
                               generation_mode='template', ocr_enabled=False))


@pytest.fixture
def client(application):
    with TestClient(application, raise_server_exceptions=False) as c:
        yield c

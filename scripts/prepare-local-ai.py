"""Installation locale explicite. Ne reçoit ni document utilisateur ni clé API."""
import argparse
import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'local_data'
OLLAMA_VERSION = '0.40.15'
OLLAMA_SHA = '9ca74a7ab66ec86870b1eecac7df160df08dc4e3a291ab5d2d59bcf9310221c6'
OCR_SHA = 'bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4'
E5_REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
QWEN_REVISION = '7dabda4d13d513e3e842b20f0d435c732f172cbe'


def download(url, filename, expected_sha):
    target = LOCAL / 'downloads' / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        partial = target.with_suffix('.part')
        print('Téléchargement explicite :', filename, flush=True)
        with httpx.Client(timeout=120, follow_redirects=True, trust_env=False) as client:
            with client.stream('GET', url) as response:
                response.raise_for_status()
                with partial.open('wb') as output:
                    for block in response.iter_bytes(1024 * 1024):
                        output.write(block)
        partial.rename(target)
    digest = hashlib.sha256()
    with target.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != expected_sha:
        raise RuntimeError('Empreinte incorrecte : ' + str(target))
    return target


def prepare_ollama():
    target = LOCAL / 'tools' / 'ollama'
    if (target / 'ollama.exe').is_file():
        print('Ollama local déjà présent ; aucune installation écrasée.')
        return
    archive = download(f'https://github.com/ollama/ollama/releases/download/v{OLLAMA_VERSION}/ollama-windows-amd64.zip',
                       f'ollama-v{OLLAMA_VERSION}.zip', OLLAMA_SHA)
    # Carte Intel intégrée : extraction des bibliothèques CPU seulement.
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            if any(word in entry.filename.lower() for word in ['cuda', 'rocm', 'vulkan', 'mlx']):
                continue
            resolved = (target / entry.filename).resolve()
            if not resolved.is_relative_to(target.resolve()):
                raise RuntimeError('Chemin d’archive invalide')
            bundle.extract(entry, target)


def prepare_ocr():
    target = LOCAL / 'tools' / 'tesseract'
    if not (target / 'tesseract.exe').is_file():
        if target.exists():
            raise RuntimeError('Le dossier OCR existe sans exécutable ; vérifier manuellement avant toute installation.')
        installer = download('https://github.com/tesseract-ocr/tesseract/releases/download/5.5.3/tesseract-ocr-w64-setup-5.5.3.20260724.exe',
                             'tesseract-5.5.3.exe', OCR_SHA)
        subprocess.run([str(installer), '/S', '/currentuser', f'/D={target}'], check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    with httpx.Client(timeout=90, follow_redirects=True, trust_env=False) as client:
        revision = client.get('https://api.github.com/repos/tesseract-ocr/tessdata_fast/commits/main')
        revision.raise_for_status()
        revision = revision.json()['sha']
        data = target / 'tessdata'
        for language in ['fra', 'eng', 'ara']:
            response = client.get(f'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{revision}/{language}.traineddata')
            response.raise_for_status()
            (data / f'{language}.traineddata').write_bytes(response.content)
        (data / 'ONMT_REVISION.txt').write_text(revision, encoding='ascii')


def prepare_embeddings():
    from huggingface_hub import snapshot_download
    folder = LOCAL / 'models' / 'multilingual-e5-small'
    snapshot_download('intfloat/multilingual-e5-small', revision=E5_REVISION, local_dir=folder,
                      allow_patterns=['config.json', 'modules.json', 'sentence_bert_config.json',
                                      'special_tokens_map.json', 'tokenizer.json', 'tokenizer_config.json',
                                      'sentencepiece.bpe.model', 'model.safetensors', '1_Pooling/config.json', 'README.md'],
                      max_workers=2)
    (folder / 'ONMT_REVISION.txt').write_text(E5_REVISION, encoding='ascii')


def prepare_language_model():
    from huggingface_hub import hf_hub_download
    folder = LOCAL / 'models' / 'qwen25-3b-gguf'
    filename = 'qwen2.5-3b-instruct-q4_k_m.gguf'
    hf_hub_download('Qwen/Qwen2.5-3B-Instruct-GGUF', filename, revision=QWEN_REVISION, local_dir=folder)
    (folder / 'ONMT_REVISION.txt').write_text(QWEN_REVISION, encoding='ascii')
    (folder / 'Modelfile').write_text(f'FROM ./{filename}\nPARAMETER num_ctx 3072\nPARAMETER temperature 0\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=['ollama', 'ocr', 'embeddings', 'llm'],
                        default=['ollama', 'ocr', 'embeddings', 'llm'])
    args = parser.parse_args()
    free = shutil.disk_usage(ROOT).free
    print(f'Espace libre : {free / 1024**3:.1f} Gio ; prévoir environ 10 Gio de marge pour installation et copies.')
    if free < 10 * 1024**3:
        raise SystemExit('Espace insuffisant pour une préparation complète sûre.')
    for component in args.components:
        {'ollama': prepare_ollama, 'ocr': prepare_ocr, 'embeddings': prepare_embeddings, 'llm': prepare_language_model}[component]()
    print('Préparation terminée. Démarrer Ollama puis importer le Modelfile selon le guide.')

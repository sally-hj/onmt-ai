"""Opérations éditoriales dans instruction, sans changer les champs du contrat v0.1."""
import re

from app.core.errors import AppError


def parse_revision(instruction):
    text = instruction.strip()
    normalized = text.casefold()
    if normalized in ['résumer', 'résume', 'plus concis', 'simplifier', 'concise']:
        return {'style': 'concise'}
    if normalized in ['détailler', 'détaille', 'plus détaillé', 'detailed']:
        return {'style': 'detailed'}
    if normalized == 'reformuler':
        return {'style': 'rephrase'}
    if normalized.startswith('langue:') and normalized[7:].strip() in ['fr', 'ar', 'ary', 'en', 'es']:
        return {'language': normalized[7:].strip()}
    if normalized.startswith('adapter:') and normalized[8:].strip() in ['direction', 'ministere', 'regional']:
        return {'audience': normalized[8:].strip()}
    if re.search(r'calcul|nouveau.*(?:marché|kpi)|ajout.*(?:marché|roi|budget)|prévoir|recalcul', normalized):
        raise AppError('missing_data', 'Nouvelle analyse requise : demande à transmettre à Doha via Hayat. Aucun calcul ajouté au rapport.', 422)
    if normalized.startswith('modifier:') and text[9:].strip():
        return {'style': 'rephrase', 'instruction': text[9:].strip()}
    raise AppError('invalid_request', 'Instruction éditoriale inconnue : résumer, détailler, reformuler, langue:fr, adapter:direction ou modifier:consigne.', 422)

"""Relever les versions installées des dépendances directes et de leur fermeture transitive."""
from collections import deque
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement

ROOT=Path(__file__).resolve().parents[1]


def generate():
    requirements=[Requirement(line) for line in (ROOT/'backend/requirements.txt').read_text(encoding='utf-8').splitlines()
                  if line.strip() and not line.lstrip().startswith('#')]
    queue=deque((r.name,set(r.extras)) for r in requirements if not r.marker or r.marker.evaluate())
    extras_by_name={};processed={};versions={}
    while queue:
        name,extras=queue.popleft();key=name.lower().replace('_','-')
        extras_by_name.setdefault(key,set()).update(extras)
        active=frozenset(extras_by_name[key])
        if key in processed and processed[key]==active: continue
        processed[key]=active;package=distribution(name)
        versions[package.metadata['Name']]=package.version
        for raw in package.requires or []:
            required=Requirement(raw)
            if required.marker and not any(required.marker.evaluate({'extra':extra}) for extra in ['',*active]): continue
            installed=distribution(required.name)
            if installed.version not in required.specifier:
                raise RuntimeError(f'Version incompatible : {required.name}')
            queue.append((required.name,set(required.extras)))
    header=('# Résolution Windows/Python 3.11 vérifiée dans la venv locale.\n'
            '# Directes + transitives accessibles depuis requirements.txt ; pas un inventaire des outils inutilisés.\n'
            '# Générer : python scripts/lock-requirements.py ; aucun téléchargement ni poids inclus.\n')
    (ROOT/'backend/requirements-tested.lock.txt').write_text(header+''.join(f'{name}=={version}\n' for name,version in sorted(versions.items(),key=lambda x:x[0].casefold())),encoding='utf-8')
    print(len(versions),'versions relevées ; installation principale : backend/requirements.txt')


if __name__=='__main__':generate()

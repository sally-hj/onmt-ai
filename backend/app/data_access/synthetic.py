"""Corpus pédagogique synthétique de référence, reproductible en QVD natif avec PyQvd."""
import argparse
import calendar
import hashlib
import json
import math
import random
from pathlib import Path

from pyqvd import QvdTable

DESTINATIONS = ['Agadir', 'Marrakech', 'Fès', 'Tanger', 'Rabat', 'Casablanca']
MARKETS = ['France', 'Espagne', 'Allemagne', 'Royaume-Uni', 'Maroc']
SHARES = [.32, .20, .18, .20, .10]
GENERATOR_VERSION = 'onmt-synthetic-v1'
REFERENCE_SEED = 20261111


def semantic_digest(table):
    """Empreinte des colonnes et cellules décodées, indépendante de l'horodatage QVD."""
    encoded = json.dumps(table, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def write_qvd(path, rows):
    columns = list(rows[0])
    table = QvdTable.from_dict({'columns': columns, 'data': [[r[c] for c in columns] for r in rows]})
    table.to_qvd(path)
    if QvdTable.from_qvd(path).to_dict() != table.to_dict():
        raise RuntimeError('Échec de relecture QVD : ' + path.name)


def generate(directory: Path, seed=REFERENCE_SEED):
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    tables = {'commercial': [], 'finance': [], 'performance': []}
    for year in range(2021, 2027):
        for month in range(1, 13 if year < 2026 else 11):
            for index, destination in enumerate(DESTINATIONS):
                total = round((100000 + index*13000)*(1+.04*(year-2024))*(1+.24*math.sin((month-5)*math.pi/6)))
                if destination == 'Agadir' and month == 2 and year in [2024, 2025]:
                    total = 100000 if year == 2024 else 80000
                if destination == 'Marrakech' and month == 2 and year in [2024, 2025]:
                    total = 150000 if year == 2024 else 165000
                for market, share in zip(MARKETS, SHARES):
                    nights = round(total*share)
                    arrivals = round(nights/(3.2+index*.1))
                    base = {'record_key': f'{year}-{month:02}|{destination}|{market}', 'period': f'{year}-{month:02}-01',
                            'destination': destination, 'market': market}
                    tables['commercial'].append({**base, 'nights': nights, 'arrivals': arrivals,
                                                  'seats': round(arrivals*1.7), 'bookings': round(arrivals*.8)})
                    budget = round((160000+index*10000)*share*(1+.03*(year-2021)))
                    spent = round(budget*(.72+rng.random()*.18))
                    tables['finance'].append({**base,'budget_mad': budget,'spent_mad': spent,'committed_mad': round(budget*.95)})
                    rooms = round(nights/1.8)
                    available = max(rooms, round((15000+index*1500)*share*calendar.monthrange(year, month)[1]/10))
                    tables['performance'].append({**base,'room_revenue_mad': rooms*(620+index*25),'room_nights_sold': rooms,
                        'room_nights_available': available,'travel_receipts_mad': nights*(740+index*30),
                        'impressions': round(spent*4.5),'clicks': round(spent*.12)})
    manifest = {'schema_version':2,'generator_version':GENERATOR_VERSION,
                'reference_status':'pedagogical_final' if seed==REFERENCE_SEED else 'pedagogical_variant',
                'synthetic': True,'seed': seed,'period': {'start':'2021-01-01','end':'2026-10-31'},
                'grain': ['month','destination','market'],'destinations':DESTINATIONS,'markets':MARKETS,'files':[]}
    for name, rows in tables.items():
        path = directory/f'{name}.qvd'
        write_qvd(path, rows)
        decoded = QvdTable.from_qvd(path).to_dict()
        manifest['files'].append({'id':name,'file':path.name,'rows':len(rows),'columns':decoded['columns'],
                                 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                 'semantic_sha256':semantic_digest(decoded)})
    # Jeux défectueux séparés : aucun n'est chargé par la configuration normale.
    bad = directory/'invalid'; bad.mkdir(exist_ok=True)
    rows = [dict(r) for r in tables['commercial'][:5]]
    rows.append(dict(rows[0])); rows[1]['nights'] = None; rows[2]['period'] = '2025-99-99'; rows[3]['nights'] = -1
    write_qvd(bad/'commercial-invalid.qvd', rows)
    (directory/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    # Références établies à partir des constantes imposées, sans appeler le moteur d'analyse.
    references = {'synthetic':True,'agadir_feb_2025':80000,'agadir_feb_2024':100000,'agadir_change_pct':-20,
                  'marrakech_feb_2025':165000,'marrakech_feb_2024':150000,'marrakech_change_pct':10,
                  'agadir_france_feb_2025':25600}
    (directory/'expected.json').write_text(json.dumps(references,indent=2),encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('local_data/qvd-synthetic'))
    parser.add_argument('--seed',type=int,default=REFERENCE_SEED)
    args = parser.parse_args()
    result = generate(args.output, args.seed)
    print('Données SYNTHÉTIQUES :', sum(f['rows'] for f in result['files']), 'lignes ; relecture QVD vérifiée.')

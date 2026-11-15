"""Extension synthétique idempotente ; les trois QVD de référence restent intacts."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from pyqvd import QvdTable

from app.core.config import ROOT
from .synthetic import semantic_digest, write_qvd

COMPARATORS = ['Maroc', 'Tunisie', 'Espagne', 'Dubaï', 'Thaïlande', 'Rwanda']
REGIONS = ['Tanger-Tétouan-Al Hoceima','Oriental','Fès-Meknès','Rabat-Salé-Kénitra',
           'Béni Mellal-Khénifra','Casablanca-Settat','Marrakech-Safi','Drâa-Tafilalet',
           'Souss-Massa','Guelmim-Oued Noun','Laâyoune-Sakia El Hamra','Dakhla-Oued Ed-Dahab']


def regional_rows():
    rows=[]
    for year in range(2021,2027):
        for month in range(1,13 if year<2026 else 11):
            for i,region in enumerate(REGIONS):
                growth=[.10,.10,.02,.02][i%4]; share=[1.5,.5,1.5,.5][i%4]
                arrivals=round((50000+i*10000)*(1+growth)**(year-2021)*(1+.1*math.sin(month*math.pi/6)))
                nights=arrivals*3; rooms=round(nights/1.8)
                rows.append({'record_key':f'{year}-{month:02}|{region}|Total','period':f'{year}-{month:02}-01','destination':region,'market':'Total',
                    'arrivals':arrivals,'nights':nights,'seats':arrivals*2,'bookings':round(arrivals*.7),'receipts_mad':nights*700,
                    'room_revenue_mad':rooms*600,'rooms_sold':rooms,'rooms_available':rooms*2,'gdp_mad':float(arrivals*50000),
                    'tourism_gva_mad':float(arrivals*4000),'market_total_arrivals':round(arrivals*(2+1/share)),
                    'competitor_arrivals':round(arrivals/share)})
    return rows


def native_rows(path):
    table = QvdTable.from_qvd(path).to_dict()
    return [dict(zip(table['columns'], row)) for row in table['data']]


def ensure_table(path, rows):
    # QVD IntegerValue est signé sur 32 bits ; les grands montants entiers
    # sont exactement représentables en double IEEE754 dans ce corpus (<2^53).
    rows=[{k:float(v) if isinstance(v,int) and abs(v)>2147483647 else v for k,v in row.items()} for row in rows]
    if path.exists():
        if native_rows(path) != rows:
            raise ValueError(f'Extension existante différente : {path.name}. Choisir un nouveau répertoire/version.')
    else:
        write_qvd(path, rows)
    return {'file': path.name, 'rows': len(rows),
            'semantic_sha256': semantic_digest(QvdTable.from_qvd(path).to_dict())}


def prepare(root):
    directory = root/'supplement'; directory.mkdir(parents=True, exist_ok=True)
    performance = {r['record_key']: r for r in native_rows(root/'performance.qvd')}
    finance = {r['record_key']: r for r in native_rows(root/'finance.qvd')}
    extension = []
    for row in native_rows(root/'commercial.qvd'):
        key=row['record_key']; p=performance[key]; f=finance[key]
        # Les grandeurs macro sont allouées à chaque clé (pas répétées par marché).
        gdp=float(row['arrivals']*50000)
        extension.append({k: row[k] for k in ['record_key','period','destination','market']} | {
            'conversions': round(p['clicks']*.04), 'event_attendance': round(row['arrivals']*.12),
            'event_capacity': round(row['arrivals']*.20), 'tourism_gva_mad': round(gdp*.08), 'gdp_mad':gdp,
            'tourism_jobs':round(row['arrivals']*.08), 'total_jobs':round(row['arrivals']*.8),
            'web_visits':round(p['clicks']*2.5), 'engagements':round(p['impressions']*.06),
            'attributed_margin_mad':round(f['spent_mad']*1.2)})
    international=[]
    for year in range(2021,2027):
        for month in range(1,13 if year<2026 else 11):
            for i,name in enumerate(COMPARATORS):
                arrivals=round((100000+40000*i)*(1+.02*(i+1))**(year-2021)*(1+.18*math.sin((month-i)*math.pi/6)))
                nights=arrivals*(3+i%3); sold=round(nights/1.8); capacity=round(sold/(.6+.025*i))
                international.append({'record_key':f'{year}-{month:02}|{name}|Total','period':f'{year}-{month:02}-01',
                    'destination':name,'market':'Total','arrivals':arrivals,'nights':nights,'seats':arrivals*2,
                    'bookings':round(arrivals*.7),'receipts_mad':nights*(700+50*i),'room_revenue_mad':sold*(600+30*i),
                    'rooms_sold':sold,'rooms_available':capacity,'gdp_mad':float(arrivals*50000),'tourism_gva_mad':float(arrivals*4000),
                    # Chaque destination a son marché total et son plus grand concurrent fictif.
                    'market_total_arrivals':round(arrivals*(2.5+.15*i)),
                    'competitor_arrivals':round(arrivals/(.7+.15*i))})
    manifest={'version':'supplement-v1','synthetic':True,'reference_files_unchanged':True,
              'convention':'Grandeurs monétaires générées directement en MAD de scénario ; aucune conversion de devises.',
              'files':[ensure_table(directory/'extension.qvd',extension),ensure_table(directory/'international.qvd',international),
                       ensure_table(directory/'regional.qvd',regional_rows())],
              'reference_hashes':{n:hashlib.sha256((root/f'{n}.qvd').read_bytes()).hexdigest() for n in ['commercial','finance','performance']}}
    (directory/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'local_data/qvd-synthetic')
    print(json.dumps(prepare(parser.parse_args().root),ensure_ascii=False,indent=2))

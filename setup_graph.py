"""Rebuild Ella pilot graph from CSVs and documented enrichment. Idempotent for known IDs.

Run from repository root: python setup_graph.py
Requires: data/extracted/entities.csv and relationships.csv, .env.
"""
from pathlib import Path
import csv
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')
URI = os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687')
USER = os.getenv('NEO4J_USER', 'neo4j')
PASSWORD = os.getenv('NEO4J_PASSWORD')
if not PASSWORD:
    raise RuntimeError('Set NEO4J_PASSWORD in .env (never commit this file).')

entities_file = ROOT / 'data/extracted/entities.csv'
relationships_file = ROOT / 'data/extracted/relationships.csv'
for p in (entities_file, relationships_file):
    if not p.is_file():
        raise FileNotFoundError(f'Missing {p}. Export it from 02_document_extraction.ipynb first.')

with entities_file.open(encoding='utf-8-sig', newline='') as f:
    entities = list(csv.DictReader(f))
with relationships_file.open(encoding='utf-8-sig', newline='') as f:
    relationships = list(csv.DictReader(f))

ALLOWED_LABELS = {'Destination', 'District', 'Province', 'Attraction', 'Activity',
                  'RailwayStation', 'TrainService', 'Accommodation'}
ALLOWED_RELATIONS = {'LOCATED_IN', 'PART_OF', 'HAS_ATTRACTION', 'HAS_ACTIVITY',
                     'SUPPORTS_ACTIVITY', 'HAS_RAILWAY_STATION', 'ARRIVES_AT', 'HAS_ACCOMMODATION'}

# Details taken from the Ella document and the graph enrichment steps in the prototype.
DETAILS = {
 'D001': {'elevation_m':1041,'climate_si':'සාමාන්‍යයෙන් සිසිල් කඳුකර දේශගුණය','source_sections':[1,2]},
 'A001': {'name_en':"Little Adam's Peak",'aliases':['පුංචි ශ්‍රී පාදය',"Little Adam's Peak", "Mini Adam's Peak"],'elevation_m':1141,'elevation_approximate':True,'hiking_difficulty':'easy','best_time_si':'උදෑසන සහ සවස් කාලය','description_si':'ඇල්ලේ ජනප්‍රිය කඳු නැගීමේ ස්ථානයකි.','visiting_advice_si':'උදෑසන සහ සවස් කාලය ජනප්‍රියය.','source_sections':[3]},
 'A002': {'name_en':'Ella Rock','aliases':['ඇල්ල රොක්','Ella Rock'],'hiking_difficulty':'challenging','description_si':'පුංචි ශ්‍රී පාදයට වඩා අභියෝගාත්මක විය හැකි කඳු නැගීමේ ස්ථානයකි.','visiting_advice_si':'සුදුසු පාවහන් හා ජලය රැගෙන යාම වැදගත් වේ.','source_sections':[4]},
 'A003': {'name_en':'Nine Arches Bridge','aliases':['ආරුක්කු නවයේ පාලම','Nine Arches Bridge'],'description_si':'ඇල්ල ආසන්නයේ පිහිටි ප්‍රසිද්ධ දුම්රිය පාලමකි.','popular_for_si':'දුම්රිය නැරඹීම සහ ඡායාරූප ගැනීම','source_sections':[5]},
 'A004': {'height_m':25,'height_approximate':True,'distance_from_ella_km':6,'description_si':'ඇල්ලේ සිට කිලෝමීටර් 6ක් පමණ දුරින් පිහිටි දිය ඇල්ලකි.','safety_si':'තෙත් ගල් සහ ශක්තිමත් ජල ධාරා පිළිබඳ සැලකිලිමත් විය යුතුය.','source_sections':[6]},
 'A005': {'description_si':'රාවණා රජු පිළිබඳ දේශීය පුරාවෘත්ත සමඟ සම්බන්ධ ගුහාවකි.','visiting_advice_si':'ළඟාවීමට පා ගමනක් හෝ කඳු නැගීමක් අවශ්‍ය විය හැකිය.','source_sections':[7]},
 'A006': {'description_si':'බදුල්ල–බණ්ඩාරවෙල මාර්ගයේ පිහිටි පැරණි බෞද්ධ විහාරස්ථානයකි.','buddha_statue_height_m':12,'statue_height_approximate':True,'visiting_advice_si':'සුදුසු ඇඳුමින් ගෞරවාන්විතව හැසිරිය යුතුය.','source_sections':[8]},
 'A007': {'height_m':220,'height_approximate':True,'description_si':'ඇල්ල අවට පුළුල් ප්‍රදේශයේ සංචාරයකදී නැරඹිය හැකි දිය ඇල්ලකි.','source_sections':[9]},
 'A008': {'description_si':'භූගත පරිසරයක් සහ ජල තටාකයක් සඳහා ප්‍රසිද්ධ ස්ථානයකි.','visiting_advice_si':'පළපුරුදු මාර්ගෝපදේශක සහාය අවශ්‍ය විය හැකිය.','source_sections':[10]},
}
NEW_ENTITIES = [
 ('RS001','RailwayStation','ඇල්ල දුම්රිය ස්ථානය',{'opened_year':1918,'opened_month':7,'source_sections':[12]}),
 ('T001','TrainService','පොඩි මැණිකේ',{'train_number':'1005','departure_time':'05:55','arrival_time':'15:14','source_sections':[13]}),
 ('T002','TrainService','උඩරට මැණිකේ',{'train_number':'1015','departure_time':'08:30','arrival_time':'17:27','source_sections':[13]}),
 ('T003','TrainService','දුම්රිය අංක 1007',{'train_number':'1007','departure_time':'09:45','arrival_time':'18:22','source_sections':[13]}),
 ('T004','TrainService','රාත්‍රී තැපැල් දුම්රිය',{'train_number':'1045','departure_time':'20:00','arrival_time':'06:05','arrival_next_day':True,'source_sections':[13]}),
 ('H001','Accommodation','98 Acres Resort & Spa',{'location_si':'Ella–Passara මාර්ගය','source_sections':[17]}),
 ('H002','Accommodation','The Secret Ella',{'location_si':'Passara Road','source_sections':[17]}),
 ('H003','Accommodation','Ella Jungle Resort',{'description_si':'ඇල්ල ආසන්නයේ ස්වභාවික පරිසරයක නවාතැන් පහසුකම් සපයයි.','source_sections':[17]}),
 ('H004','Accommodation','La Ella Breeze',{'facilities_si':['අවන්හල','බාර්'],'source_sections':[17]}),
 ('AC004','Activity','Zipline',{'source_sections':[11]}),
 ('AC005','Activity','ATV රථ ධාවනය',{'source_sections':[11]})
]
NEW_RELATIONS = [
 ('A001','SUPPORTS_ACTIVITY','AC001'),('A002','SUPPORTS_ACTIVITY','AC001'),('A003','SUPPORTS_ACTIVITY','AC003'),
 ('D001','HAS_ACTIVITY','AC004'),('D001','HAS_ACTIVITY','AC005'),('D001','HAS_RAILWAY_STATION','RS001'),
 ('T001','ARRIVES_AT','RS001'),('T002','ARRIVES_AT','RS001'),('T003','ARRIVES_AT','RS001'),('T004','ARRIVES_AT','RS001'),
 ('D001','HAS_ACCOMMODATION','H001'),('D001','HAS_ACCOMMODATION','H002'),('D001','HAS_ACCOMMODATION','H003'),('D001','HAS_ACCOMMODATION','H004')
]
EVIDENCE = [
 ('D001','LOCATED_IN','DI001',1,'ඇල්ල ශ්‍රී ලංකාවේ ඌව පළාතේ බදුල්ල දිස්ත්‍රික්කයේ පිහිටි කුඩා කඳුකර නගරයකි.'),
 ('D001','HAS_ATTRACTION','A001',3,"පුංචි ශ්‍රී පාදය, Little Adam's Peak හෝ Mini Adam's Peak ලෙසද හැඳින්වෙන අතර ඇල්ලේ ජනප්‍රියම සංචාරක ස්ථාන අතරින් එකකි."),
 ('D001','HAS_ATTRACTION','A003',5,'Demodara Nine Arch Bridge හෙවත් ආරුක්කු නවයේ පාලම ඇල්ල ආසන්නයේ පිහිටි ප්‍රසිද්ධම සංචාරක සලකුණු අතරින් එකකි.'),
 ('D001','HAS_ATTRACTION','A004',6,'රාවණා ඇල්ල ඇල්ල නගරයේ සිට කිලෝමීටර් 6ක් පමණ දුරින් පිහිටි ජනප්‍රිය දිය ඇල්ලකි.')
]

def main():
    with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
        driver.verify_connectivity()
        driver.execute_query('CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE', database_=DATABASE)
        def upsert_node(id_, label, name, props=None):
            if label not in ALLOWED_LABELS: raise ValueError(f'Invalid label: {label}')
            driver.execute_query(f'MERGE (n:Entity {{id:$id}}) SET n:{label} SET n.name_si=$name SET n += $props',
                                 id=id_, name=name, props=props or {}, database_=DATABASE)
        def upsert_edge(source, rel, target, props=None):
            if rel not in ALLOWED_RELATIONS: raise ValueError(f'Invalid relation: {rel}')
            records, _, _ = driver.execute_query(
                f'MATCH (a:Entity {{id:$source}}), (b:Entity {{id:$target}}) MERGE (a)-[r:{rel}]->(b) SET r += $props RETURN r',
                source=source, target=target, props=props or {}, database_=DATABASE)
            if not records: raise ValueError(f'Nodes missing for {source} -[{rel}]-> {target}')
        for e in entities:
            upsert_node(e['id'], e['label'], e['name_si'], {'source_document':'ella.txt'})
        for e in NEW_ENTITIES:
            upsert_node(e[0], e[1], e[2], {**e[3], 'source_document':'ella.txt'})
        for id_, props in DETAILS.items():
            records,_,_=driver.execute_query('MATCH (n:Entity {id:$id}) SET n += $props RETURN n.id', id=id_, props=props, database_=DATABASE)
            if not records: raise ValueError(f'Missing enrichment entity: {id_}')
        for r in relationships:
            upsert_edge(r['source'], r['relation'], r['target'])
        for source, rel, target in NEW_RELATIONS:
            upsert_edge(source, rel, target, {'source_document':'ella.txt'})
        for source, rel, target, section, sentence in EVIDENCE:
            upsert_edge(source, rel, target, {'source_document':'ella.txt','source_section':section,'source_evidence':sentence})
        counts,_,_=driver.execute_query('MATCH (n:Entity) WITH count(n) AS nodes MATCH (:Entity)-[r]->(:Entity) RETURN nodes, count(r) AS relationships', database_=DATABASE)
        print('Graph import complete:', dict(counts[0]))
        print('Expected in an otherwise empty database: 25 nodes, 27 relationships.')
        print('Train schedules are source-document examples, not verified live schedules.')
if __name__ == '__main__':
    main()

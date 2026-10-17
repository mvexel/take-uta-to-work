"""Generate an offline display layer from the already acquired routing extract."""
import json,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    pbf=pathlib.Path(tmp)/'highways.osm.pbf'
    geo=pathlib.Path(tmp)/'highways.geojson'
    subprocess.run(['osmium','tags-filter',str(ROOT/'data/graph/slc.osm.pbf'),'w/highway','-o',str(pbf)],check=True)
    subprocess.run(['osmium','export',str(pbf),'-o',str(geo)],check=True)
    source=json.loads(geo.read_text())
    roads={'motorway','trunk','primary','secondary','tertiary','residential','unclassified','living_street','pedestrian'}
    paths={'footway','steps','cycleway'}
    features=[]
    for f in source['features']:
        g=f['geometry'];p=f['properties'];kind=p.get('highway')
        if g['type']!='LineString':continue
        campus=any(-111.86<=x<=-111.82 and 40.75<=y<=40.78 for x,y in g['coordinates'])
        if kind not in roads and not (kind in paths and campus):continue
        features.append({'type':'Feature','geometry':g,'properties':{k:p[k] for k in ('highway','name') if k in p}})
    target=ROOT/'data/map-streets.geojson'
    target.write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')))
    print(f'{len(features)} display features written to {target}')

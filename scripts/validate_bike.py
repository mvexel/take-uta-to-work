"""Bounded preflight experiment: compare DEM/no-DEM and uphill/downhill, not a coverage map."""
import json,pathlib,urllib.request,datetime as dt,subprocess
from zoneinfo import ZoneInfo
from spike import QUERY,inspect
root=pathlib.Path(__file__).resolve().parents[1]
config=json.loads((root/'config/scenario.json').read_text());origins=json.loads((root/'config/named-origins.json').read_text())
arrival=dt.datetime.fromisoformat(config['arrival_local']).replace(tzinfo=ZoneInfo('America/Denver')).isoformat()
loc=lambda p:{'location':{'coordinate':{'latitude':p['lat'],'longitude':p['lon']}}}
results=[]
for origin in origins:
 for graph,port in [('dem',8081),('no_dem',8080)]:
  for direction in ['to_ART','from_ART']:
   a,b=(origin,config['destination']) if direction=='to_ART' else (config['destination'],origin)
   variables={'origin':loc(a),'destination':loc(b),'time':{'latestArrival':arrival},'modes':{'directOnly':True,'direct':['BICYCLE']},'preferences':{'street':{'bicycle':{'speed':4.17},'walk':{'speed':1.33}}}}
   request=urllib.request.Request(f'http://127.0.0.1:{port}/otp/gtfs/v1',json.dumps({'query':QUERY,'variables':variables}).encode(),{'Content-Type':'application/json'})
   with urllib.request.urlopen(request,timeout=60) as f:body=json.load(f)
   if body.get('errors'):raise RuntimeError(body['errors'])
   plan=body['data']['planConnection']
   if plan['routingErrors'] or not plan['edges']:raise RuntimeError(plan)
   it=plan['edges'][0]['node'];checked=inspect(it,arrival,'bike',0,[])
   assert not any(l['transitLeg'] or l['mode'] not in ['WALK','BICYCLE'] for l in checked['legs'])
   if graph=='dem':
    steps=[s for l in checked['legs'] for s in l['steps']]
    points=[p for s in steps for p in s['elevationProfile'] or []]
    assert points,'Missing elevation profiles'
    missing=sum(s['distance'] for s in steps if not s['elevationProfile'])
    assert missing<=100 and missing<=sum(s['distance'] for s in steps)*0.05,('Excessive unprofiled length',missing)
    def sample(p):return float(subprocess.check_output(['gdallocationinfo','-valonly','-wgs84',str(root/'data/bike-graph/slc.dem.tif'),str(p['lon']),str(p['lat'])],text=True).strip())
    start_dem,end_dem=sample(a),sample(b)
    assert abs(points[0]['elevation']-start_dem)<3
    assert abs(points[-1]['elevation']-end_dem)<3
    deltas=[q['elevation']-p['elevation'] for step in steps for p,q in zip(step['elevationProfile'] or [],(step['elevationProfile'] or [])[1:])]
    checked['profile_check']={'gain_m':sum(max(0,d) for d in deltas),'loss_m':sum(max(0,-d) for d in deltas),'first_m':points[0]['elevation'],'last_m':points[-1]['elevation'],'dem_start_m':start_dem,'dem_end_m':end_dem,'unprofiled_distance_m':missing,'coverage':'partial' if missing else 'complete','endpoint_tolerance_m':3}
   results.append({'origin' :origin,'graph':graph,'direction':direction,'itinerary':checked})
for origin in origins:
 def item(graph,direction):return next(r['itinerary'] for r in results if r['origin']['id']==origin['id'] and r['graph']==graph and r['direction']==direction)
 up,down,flat=item('dem','to_ART'),item('dem','from_ART'),item('no_dem','to_ART')
 assert up['profile_check']['gain_m']>up['profile_check']['loss_m'],origin
 assert down['profile_check']['loss_m']>down['profile_check']['gain_m'],origin
 assert up['elapsed_seconds']>down['elapsed_seconds'],origin
 assert up['elapsed_seconds']!=flat['elapsed_seconds'],origin
print(json.dumps({'validation':'passed','input_manifest':json.loads((root/'config/bike-input-manifest.json').read_text()),'scope':'four named landmark pairs; not full graph elevation coverage','arrival':arrival,'results':results},indent=2))

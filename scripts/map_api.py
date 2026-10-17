"""Local map routing adapter. Results remain bounded itinerary evidence, never polygons."""
import copy,datetime as dt,json,math,pathlib,time,urllib.request
from spike import QUERY,variables,inspect
ROOT=pathlib.Path(__file__).resolve().parents[1]
EARLIEST='2026-10-20T10:45:00-06:00'
LATEST='2026-10-20T11:00:00-06:00'
BOUNDS=[-111.99,40.68,-111.80,40.83]
PAGED_QUERY=QUERY.replace('$preferences: PlanPreferencesInput!', '$preferences: PlanPreferencesInput!, $after: String, $window: Duration!').replace('first:20,searchWindow:"PT30M"','first:20,after:$after,searchWindow:$window')
def stamp(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
def check_window(it,mode,cap,allowed):
 result=inspect(it,LATEST,mode,cap,allowed)
 if stamp(result['arrival'])<stamp(EARLIEST):result['reasons'].append('too_early');result['qualifies']=False
 totals={'walk':0,'ride':0,'bike':0}
 for leg in result['legs']:
  seconds=(stamp(leg['end']['scheduledTime'])-stamp(leg['start']['scheduledTime'])).total_seconds()
  if seconds<0:raise ValueError('Invalid negative leg duration')
  key='ride' if leg['transitLeg'] else ('bike' if leg['mode']=='BICYCLE' else 'walk')
  totals[key]+=seconds
 wait=result['elapsed_seconds']-sum(totals.values())
 if wait<-.01:raise ValueError('Overlapping leg times')
 result['breakdown']={**totals,'wait':max(0,wait),'total':result['elapsed_seconds']}
 return result

def request_plan(endpoint,v,window,after=None):
 req=urllib.request.Request(endpoint,json.dumps({'query':PAGED_QUERY,'variables':{**v,'after':after,'window':window}}).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as f:body=json.load(f)
 if body.get('errors'):raise ValueError(str(body['errors']))
 return body['data']['planConnection']

def route(origin,mode,cap,request=request_plan):
 began=time.perf_counter();item={'origin':origin,'status':'not_evaluated','itineraries':[],'arrival_earliest':EARLIEST,'arrival_latest':LATEST,'search_complete':False,'search_notes':[]}
 if mode not in ('bus','trax','both','bike') or type(cap) is not int or cap not in (0,1,2):raise ValueError('Invalid mode or vehicle-change cap')
 lat,lon=float(origin['lat']),float(origin['lon'])
 if not math.isfinite(lat) or not math.isfinite(lon):raise ValueError('Coordinates must be finite')
 if not BOUNDS[0]<=lon<=BOUNDS[2] or not BOUNDS[1]<=lat<=BOUNDS[3]:
  item.update(status='not_evaluated',error='Outside the tested SLC street extract');return item
 config=json.loads((ROOT/'config'/('bike-scenario.json' if mode=='bike' else 'scenario.json')).read_text())
 endpoint='http://127.0.0.1:'+('8081' if mode=='bike' else '8080')+'/otp/gtfs/v1'
 v=variables(origin,config,mode,cap);v['time']={'latestArrival':LATEST};allowed=config['routes'].get(mode,[])
 seen=set();errors=[]
 def consume(plan):
  errors.extend(plan.get('routingErrors',[]))
  for edge in plan.get('edges') or []:
   it=edge['node'];key=json.dumps([it['start'],it['end'],[(l.get('trip'),l['mode'],l['start']) for l in it['legs']]],sort_keys=True)
   if key not in seen:seen.add(key);item['itineraries'].append(check_window(it,mode,cap,allowed))
 try:
  first=request(endpoint,v,'PT30M');consume(first)
  if mode=='bike':item['search_complete']=True
  elif not any(i['qualifies'] for i in item['itineraries']):
   # A qualifying <=30m journey arriving >=10:45 must depart >=10:15.
   # Search forwards too: do not discard an origin just because arrive-by chose an early option.
   v['time']={'earliestDeparture':'2026-10-20T10:15:00-06:00'};cursor=None
   for page in range(3):
    plan=request(endpoint,v,'PT45M',cursor);consume(plan)
    nodes=[e['node'] for e in plan.get('edges') or []]
    if any(i['qualifies'] for i in item['itineraries']):break
    if not plan['pageInfo']['hasNextPage']:
     item['search_complete']=True;break
    # Once this forward page extends past latest departure, later pages cannot qualify.
    if nodes and min(stamp(n['start']) for n in nodes)>stamp(LATEST):item['search_complete']=True;break
    cursor=plan['pageInfo'].get('endCursor')
    if not cursor:break
   item['search_notes'].append('Arrive-by search plus up to three forward pages from 10:15; no exhaustive coverage claim')
  good=any(i['qualifies'] for i in item['itineraries'])
  if good:item['status']='qualifying_route'
  elif any('elevation_gap' in i['reasons'] for i in item['itineraries']):item.update(status='unknown',error='Elevation profile gap')
  elif errors:item.update(status='unknown',error='; '.join(e['code']+': '+e['description'] for e in errors))
  elif not item['search_complete']:item.update(status='unknown',error='Search limit reached; later qualifying options may remain')
  else:item['status']='no_qualifying_returned_route'
 except Exception as e:item.update(status='error',error=str(e))
 item['itineraries'].sort(key=lambda i:(not i['qualifies'],i['elapsed_seconds']))
 item['latency_ms']=round((time.perf_counter()-began)*1000,2)
 return item

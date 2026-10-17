"""Dependency-free OTP 2.10.0 bounded routing experiment. No automatic downloads."""
import argparse, csv, datetime as dt, hashlib, io, json, pathlib, time, urllib.request, zipfile
from zoneinfo import ZoneInfo

QUERY = '''query Spike($origin: PlanLabeledLocationInput!, $destination: PlanLabeledLocationInput!, $time: PlanDateTimeInput!, $modes: PlanModesInput!, $preferences: PlanPreferencesInput!) {
 planConnection(origin:$origin,destination:$destination,dateTime:$time,modes:$modes,preferences:$preferences,first:20,searchWindow:"PT30M") {
 routingErrors { code description } pageInfo { hasNextPage endCursor }
 edges { node { start end duration elevationGained elevationLost legs { steps { distance elevationProfile { distance elevation } } legGeometry { points } mode transitLeg interlineWithPreviousLeg from { lat lon name stop { gtfsId } } to { lat lon name stop { gtfsId } } trip { gtfsId } start { scheduledTime } end { scheduledTime } route { gtfsId shortName } } } }
 }}'''

def audit(path, date):
    day = dt.date.fromisoformat(date); key = day.strftime('%Y%m%d')
    with zipfile.ZipFile(path) as z:
        def rows(name):
            return list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')))) if name in z.namelist() else []
        calendar, exceptions = rows('calendar.txt'), rows('calendar_dates.txt')
        active = {r['service_id'] for r in calendar if r['start_date'] <= key <= r['end_date'] and r[day.strftime('%A').lower()] == '1'}
        for r in exceptions:
            if r['date'] == key:
                if r['exception_type'] == '1': active.add(r['service_id'])
                elif r['exception_type'] == '2': active.discard(r['service_id'])
        trips = rows('trips.txt'); active_routes = {r['route_id'] for r in trips if r['service_id'] in active}
        return {'sha256':hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(), 'date':date,
            'timezones': sorted({r['agency_timezone'] for r in rows('agency.txt')}),
            'calendar_ranges': sorted({(r['start_date'],r['end_date']) for r in calendar}),
            'exception_range': [min((r['date'] for r in exceptions),default=None),max((r['date'] for r in exceptions),default=None)],
            'active_services':sorted(active),'active_trip_count':sum(r['service_id'] in active for r in trips),
            'routes':[dict(r,active_on_date=r['route_id'] in active_routes) for r in rows('routes.txt')]}

def variables(origin, config, mode, cap):
    if cap not in (0,1,2): raise ValueError('vehicle changes must be 0, 1 or 2')
    if not config['destination']['verified']: raise ValueError('Verify ART pedestrian entrance before routing')
    instant = dt.datetime.fromisoformat(config['arrival_local']).replace(tzinfo=ZoneInfo('America/Denver'))
    location = lambda p: {'location': {'coordinate': {'latitude':p['lat'],'longitude':p['lon']}}}
    preferences = {'street':{'walk':{'speed':1.33},'bicycle':{'speed':4.17}}}
    if mode == 'bike':
        if not config.get('directional_elevation_verified', False): raise ValueError('Verify directional elevation before bike routing')
        modes = {'directOnly':True,'direct':['BICYCLE']}
    else:
        allowed = config['routes'][mode]
        if not allowed: raise ValueError('Populate reviewed OTP FeedId:RouteId allowlist')
        modes = {'transitOnly':True,'transit':{'access':['WALK'],'egress':['WALK'],'transfer':['WALK'], 'transit':[{'mode':m} for m in ({'bus':['BUS'],'trax':['TRAM'],'both':['BUS','TRAM']}[mode])]}}
        preferences['transit'] = {'transfer':{'maximumTransfers':cap},'filters':[{'include':[{'routes':allowed}]}]}
    return {'origin':location(origin),'destination':location(config['destination']), 'time':{'latestArrival':instant.isoformat()},'modes':modes,'preferences':preferences}

def inspect(it, latest, mode, cap, allowed):
    stamp = lambda x: dt.datetime.fromisoformat(x.replace('Z','+00:00'))
    start, end = stamp(it['start']), stamp(it['end']); legs = it['legs']
    transit = [l for l in legs if l['transitLeg']]
    changes = max(0, sum(not l.get('interlineWithPreviousLeg', False) for l in transit)-1)
    reasons = []
    if end > stamp(latest): reasons.append('late')
    elapsed = (end-start).total_seconds()
    if elapsed < 0 or elapsed > 1800: reasons.append('duration')
    if changes > cap: reasons.append('changes')
    if mode == 'bike':
        steps=[s for l in legs for s in l.get('steps',[])]
        if not steps or any(s.get('distance',0)>0 and not s.get('elevationProfile') for s in steps): reasons.append('elevation_gap')
        if transit or not any(l['mode'] == 'BICYCLE' for l in legs) or any(l['mode'] not in ('BICYCLE','WALK') for l in legs): reasons.append('mode')
    else:
        if not transit: reasons.append('no_transit')
        permitted = {'bus':{'BUS'},'trax':{'TRAM'},'both':{'BUS','TRAM'}}[mode]
        if any(l['mode'] not in permitted or (l.get('route') or {}).get('gtfsId') not in allowed for l in transit): reasons.append('route_or_mode')
        if any(l['mode'] != 'WALK' for l in legs if not l['transitLeg']): reasons.append('street_mode')
    return {'qualifies':not reasons,'reasons':reasons,'departure':it['start'],'arrival':it['end'],'elapsed_seconds':elapsed,'earliness_seconds':(stamp(latest)-end).total_seconds(),'vehicle_changes':changes,'otp_reported_elevation_gained_m_untrusted':it.get('elevationGained'),'otp_reported_elevation_lost_m_untrusted':it.get('elevationLost'),'legs':legs}

def run(config, origins, endpoint, mode, cap):
    results=[]
    for origin in origins:
        item={'origin':origin,'status':'unknown'}; began=time.perf_counter()
        try:
            v=variables(origin,config,mode,cap)
            req=urllib.request.Request(endpoint,json.dumps({'query':QUERY,'variables':v}).encode(),{'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=60) as response: body=json.load(response)
            if body.get('errors'): raise ValueError(str(body['errors']))
            plan=body['data']['planConnection']
            if plan['routingErrors']: raise ValueError(str(plan['routingErrors']))
            item['itineraries']=[inspect(e['node'],v['time']['latestArrival'],mode,cap,config['routes'].get(mode,[])) for e in plan['edges']]
            item['has_more']=plan['pageInfo']['hasNextPage']
            item['status']='qualifying_route' if any(i['qualifies'] for i in item['itineraries']) else 'no_qualifying_returned_route'
            if mode=='bike' and item['status']!='qualifying_route' and any('elevation_gap' in i['reasons'] for i in item['itineraries']): item['status']='unknown'
            item['scope']='bounded search; absence is not proof of inaccessibility'
        except Exception as e: item['error']=str(e)
        item['latency_ms']=round((time.perf_counter()-began)*1000,2);results.append(item)
    return {'engine':'OTP 2.10.0','mode':mode,'maximum_changes':cap,'scenario':config,'input_manifest':json.loads((pathlib.Path(__file__).resolve().parents[1]/config.get('input_manifest_file','config/input-manifest.json')).read_text()) if (pathlib.Path(__file__).resolve().parents[1]/config.get('input_manifest_file','config/input-manifest.json')).exists() else None,'results':results}

if __name__=='__main__':
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('audit');a.add_argument('zip');a.add_argument('--date',default='2026-10-20')
    r=sub.add_parser('run');r.add_argument('--config',default='config/scenario.json');r.add_argument('--origins',default='config/origins.json');r.add_argument('--endpoint',default='http://localhost:8080/otp/gtfs/v1');r.add_argument('--mode',choices=['bus','trax','both','bike'],default='both');r.add_argument('--changes',type=int,choices=[0,1,2],default=1)
    args=p.parse_args()
    result=audit(args.zip,args.date) if args.command=='audit' else run(json.load(open(args.config)),json.load(open(args.origins)),args.endpoint,args.mode,args.changes)
    print(json.dumps(result,indent=2))

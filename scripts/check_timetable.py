"""Cross-check returned transit stop events with the exact local static GTFS."""
import csv,io,json,zipfile,datetime as dt,pathlib,collections,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
with zipfile.ZipFile(root/'data/graph/uta.gtfs.zip') as z:
 rows=csv.DictReader(io.TextIOWrapper(z.open('stop_times.txt'),encoding='utf-8-sig'))
 events=collections.defaultdict(list)
 for r in rows: events[(r['trip_id'],r['stop_id'])].append(r)
checks=[]
feed_hash=hashlib.sha256((root/'data/graph/uta.gtfs.zip').read_bytes()).hexdigest()
service_dates=set()
for path in sorted((root/'results').glob('*-[012].json')):
 data=json.loads(path.read_text())
 service_date=data['scenario']['arrival_local'][:10]
 service_dates.add(service_date)
 if data['input_manifest']['inputs']['data/graph/uta.gtfs.zip']['sha256'] != feed_hash: raise SystemExit('Feed hash mismatch: '+str(path))
 for result in data['results']:
  for itinerary in result.get('itineraries',[]):
   for leg in itinerary['legs']:
    if not leg['transitLeg']: continue
    trip=leg['trip']['gtfsId'].split(':',1)[1]
    for place,timekey,column in [('from','start','departure_time'),('to','end','arrival_time')]:
     stop=leg[place]['stop']['gtfsId'].split(':',1)[1]
     instant=dt.datetime.fromisoformat(leg[timekey]['scheduledTime']);seconds=int((instant-dt.datetime.combine(dt.date.fromisoformat(service_date),dt.time(),tzinfo=instant.tzinfo)).total_seconds())
     def sec(s):
      h,m,s=map(int,s.split(':'));return h*3600+m*60+s
     matches=any(sec(r[column])==seconds for r in events[(trip,stop)])
     checks.append({'scenario':path.stem,'origin':result['origin']['id'],'trip':trip,'stop':stop,'event':column,'seconds':seconds,'matches':matches})
if not checks: raise SystemExit('No timetable events checked')
report={'service_dates':sorted(service_dates),'checks':len(checks),'unique_events':len({(c['trip'],c['stop'],c['event'],c['seconds']) for c in checks}),'mismatches':[c for c in checks if not c['matches']]}
print(json.dumps(report,indent=2))
if report['mismatches']: raise SystemExit(1)

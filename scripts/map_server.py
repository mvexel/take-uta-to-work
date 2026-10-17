"""Loopback-only map UI and bounded routing API; no external map/tile services."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
from pathlib import Path
import json,mimetypes,threading
from map_api import route,ROOT,BOUNDS,EARLIEST,LATEST
SAMPLES=json.loads((ROOT/'config/origins.json').read_text())
CACHE={};LOCK=threading.Lock()
class Handler(BaseHTTPRequestHandler):
 def json(self,data,code=200):
  body=json.dumps(data).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
 def do_GET(self):
  url=urlsplit(self.path)
  if url.path=='/api/config':
   self.json({'destination':json.loads((ROOT/'config/scenario.json').read_text())['destination'],'origins':SAMPLES,'bounds':BOUNDS,'arrival_earliest':EARLIEST,'arrival_latest':LATEST});return
  if url.path=='/api/sample':
   try:
    q=parse_qs(url.query);mode=q.get('mode',['both'])[0];cap=int(q.get('changes',['1'])[0]);key=(mode,cap)
    if mode not in ('bus','trax','both','bike') or cap not in (0,1,2):raise ValueError('Invalid filter')
    with LOCK:
     if key not in CACHE:
      CACHE[key]={'results':[route(o,mode,cap) for o in SAMPLES],'mode':mode,'maximum_changes':cap,'arrival_earliest':EARLIEST,'arrival_latest':LATEST}
      out=ROOT/'results'/f'map-{mode}-{cap}.json';out.write_text(json.dumps(CACHE[key],indent=2)+'\n')
    self.json(CACHE[key]);return
   except Exception as e:self.json({'error':str(e)},400);return
  if url.path=='/map-data/streets.geojson':path=ROOT/'data/map-streets.geojson';mime='application/geo+json'
  else:
   relative='map.html' if url.path=='/' else url.path.lstrip('/')
   path=(ROOT/'web'/relative)
   if path.is_symlink() or not path.resolve().is_relative_to((ROOT/'web').resolve()):self.send_error(404);return
   mime=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
  if not path.is_file():self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',mime);self.end_headers();self.wfile.write(path.read_bytes())
 def do_POST(self):
  if self.path!='/api/route':self.send_error(404);return
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.json({'error':'Expected JSON'},415);return
  origin=self.headers.get('Origin')
  if origin and origin not in ['http://127.0.0.1:8002','http://localhost:8002']:self.json({'error':'Local origin required'},403);return
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=4096:raise ValueError('Invalid request size')
   data=json.loads(self.rfile.read(length));point={'id':'clicked','name':'Clicked location','lat':float(data['lat']),'lon':float(data['lon'])}
   self.json(route(point,data['mode'],data['changes']))
  except (ValueError,KeyError,TypeError) as e:self.json({'error':str(e)},400)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8002),Handler).serve_forever()

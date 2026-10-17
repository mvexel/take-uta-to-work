"""Read-only loopback viewer serving the prototype and saved result JSON, never data/."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/': path=ROOT/'web/index.html';mime='text/html'
  elif self.path=='/runs':
   names=[p.name for p in (ROOT/'results').glob('*.json') if p.name.startswith(('named-','bike-sample','both-','bus-','trax-'))]
   body=json.dumps(sorted(names)).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body);return
  elif self.path.startswith('/results/') and Path(self.path).name==self.path[len('/results/'):] and self.path.endswith('.json'):
   path=ROOT/'results'/Path(self.path).name;mime='application/json'
  else:self.send_error(404);return
  if not path.is_file():self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',mime);self.end_headers();self.wfile.write(path.read_bytes())
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()

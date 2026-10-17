#!/usr/bin/env python3
"""Local, read-only coordination board. Python standard library only."""
import argparse
import hashlib
import html
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARTIFACTS = {'decisions': ('Coordination decisions', 'dashboard/coordination.md'), 'bicycle': ('Bicycle evidence', 'docs/bicycle.md'), 'status': ('Routing status', 'docs/status.md'), 'project': ('Brief & backlog', 'docs/project.md'), 'development': ('Development guide', 'docs/development.md'), 'readme': ('Project README', 'README.md'), 'dashboard': ('Dashboard maintenance', 'dashboard/README.md')}
STATES = [('planned', 'Planned', 'Next steps · not started'), ('in_progress', 'In progress', 'Actively being worked'), ('done', 'Done', 'Bounded work with evidence'), ('backlog', 'Backlog', 'Later, not committed')]
def esc(value): return html.escape(str(value), quote=True)
def stamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None: raise ValueError('Timestamps require timezone')
    return dt

def read_artifact(key):
    path = ROOT / ARTIFACTS[key][1]
    if path.resolve() != path or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Symlink artifacts are not served')
    return path.read_text()

def load_board():
    data = json.loads((HERE / 'board.json').read_text())
    if data['schema_version'] != 1: raise ValueError('Unsupported schema')
    stamp(data['reviewed_at'])
    if not isinstance(data['stale_after_hours'], (int, float)) or data['stale_after_hours'] <= 0: raise ValueError('Invalid stale threshold')
    if len(data['status_sha256']) != 64: raise ValueError('Invalid status hash')
    ids = set()
    for c in data['cards']:
        for key in ('id', 'title', 'summary', 'owner', 'done_when', 'next_step', 'evidence', 'verified_at'): 
            if not isinstance(c[key], str) or not c[key].strip(): raise ValueError('Missing card field: '+key)
        if c['id'] in ids: raise ValueError('Duplicate card ID')
        ids.add(c['id'])
        if c['state'] not in dict((s[0], s[1]) for s in STATES): raise ValueError('Invalid state')
        if c['evidence'] not in ARTIFACTS: raise ValueError('Unknown artifact')
        stamp(c['verified_at'])
    for r in data['requests']:
        for key in ('kind', 'ask', 'owner', 'impact', 'recommendation', 'evidence', 'verified_at'):
            if not isinstance(r[key], str) or not r[key].strip(): raise ValueError('Missing request field: '+key)
        if r['kind'] not in ('decision', 'action') or r['evidence'] not in ARTIFACTS: raise ValueError('Invalid request')
        stamp(r['verified_at'])
    for c in data['technical_constraints']:
        if c['evidence'] not in ARTIFACTS: raise ValueError('Unknown artifact')
    return data

def link(key): return '<a href="/artifacts/'+key+'">'+esc(ARTIFACTS[key][0])+' ↗</a>'
def shell(title, body):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+' · Take UTA to Work</title><script defer src="/refresh.js"></script><link rel="stylesheet" href="/style.css"></head><body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="/">UTA <span>/</span> TO WORK</a><span class="local">LOCAL PROJECT HOME</span></header><main id="main">'+body+'</main><footer>Local coordination • No accounts, external assets or ongoing collection.</footer></body></html>'

def render_board(data):
    source = read_artifact('status')
    drift = hashlib.sha256(source.encode()).hexdigest() != data['status_sha256']
    old = (datetime.now(timezone.utc)-stamp(data['reviewed_at'])).total_seconds() > data['stale_after_hours']*3600
    freshness = 'Needs reconciliation — routing status changed since board review.' if drift else ('Review overdue — board is more than '+str(data['stale_after_hours'])+' hours old.' if old else 'Reviewed snapshot · source unchanged')
    counts = {s[0]:sum(c['state']==s[0] for c in data['cards']) for s in STATES}
    body = '<div class="intro"><div><p class="eyebrow">SALT LAKE CITY → UNIVERSITY OF UTAH ART</p><h1>Take UTA to Work<span class="dot">.</span></h1><p class="lede">A clear view of what’s moving, what’s next, and what needs you.</p></div><a class="button" href="/">Refresh status ↻</a></div>'
    body += '<div class="fresh '+('warning' if old or drift else '')+'"><strong>'+esc(freshness)+'</strong><span>Board data as of <time>'+esc(data['reviewed_at'])+'</time> · UTC</span></div>'
    body += '<section class="mission" aria-label="Project scope"><div><span class="label">FIRST TEST · PROVISIONAL DATE</span><strong>Tue 20 Oct 2026 · 11:00 AM</strong><span>America/Denver · date assumed, not user-confirmed</span></div><div><span class="label">TARGET</span><strong>30 minutes door to door</strong><span>ART southwest entrance · SLC first</span></div><div><span class="label">SEPARATE MODES</span><strong>Bicycle / transit + walking</strong><span>No mixed-mode dependency</span></div></section>'
    body += '<section class="needs" aria-labelledby="needs-title"><div class="section-head"><div><p class="eyebrow">YOUR INBOX</p><h2 id="needs-title">Needs you <span class="count">'+str(len(data['requests']))+'</span></h2></div><p>Respond in the main project conversation.</p></div><div class="requests">'
    for kind,title in [('decision','Decisions'),('action','Actions')]:
        requests=[r for r in data['requests'] if r['kind']==kind]
        body += '<div><h3>'+title+'</h3>'
        if not requests: body += '<p class="empty">No verified '+kind+' requests.</p>'
        for r in requests:
            body += '<article class="request"><h4>'+esc(r['ask'])+'</h4><p><b>Owner</b> '+esc(r['owner'])+'</p><p><b>Unblocks / impact</b> '+esc(r['impact'])+'</p><p><b>Recommendation / options</b> '+esc(r['recommendation'])+'</p><p>'+link(r['evidence'])+'</p><small>Last verified '+esc(r['verified_at'])+'</small></article>'
        body += '</div>'
    body += '</div><p class="fine">No verified owner asks are recorded. The proposed date remains an assumption; technical work can continue. This board does not grant permissions.</p></section>' if not data['requests'] else '</div><p class="fine">This board does not grant permissions. Reply in the main project conversation.</p></section>'
    body += '<div class="section-head work-heading"><div><p class="eyebrow">DELIVERY BOARD</p><h2>Work at a glance</h2></div><p>Done means the card’s scope is complete, not the whole commute map.</p></div><nav class="state-nav" aria-label="Jump to work state">'+''.join('<a href="#'+s+'">'+name+' <b>'+str(counts[s])+'</b></a>' for s,name,_ in STATES)+'</nav><div class="board">'
    for state,name,desc in STATES:
        body += '<section class="column '+state+'" id="'+state+'" aria-labelledby="heading-'+state+'"><h3 id="heading-'+state+'">'+name+' <span class="count">'+str(counts[state])+'</span></h3><p class="column-desc">'+desc+'</p>'
        if not counts[state]: body += '<p class="empty">No work recorded in this state.</p>'
        for c in (c for c in data['cards'] if c['state']==state):
            body += '<article class="card" id="card-'+esc(c['id'])+'"><p class="owner">'+esc(c['owner'])+'</p><h4>'+esc(c['title'])+'</h4><p>'+esc(c['summary'])+'</p><details><summary>Done when & next step</summary><p><b>Done when</b><br>'+esc(c['done_when'])+'</p><p><b>Next step</b><br>'+esc(c['next_step'])+'</p></details><div class="card-foot">'+link(c['evidence'])+'<small>Verified '+esc(c['verified_at'])+'</small></div></article>'
        body += '</section>'
    body += '</div><section class="constraints"><h2>Technical constraints & boundaries</h2><p class="muted">Owned by the project team; these are not requests for your approval.</p><div class="requests">'
    for c in data['technical_constraints']: body += '<article><h3>'+esc(c['title'])+'</h3><p>'+esc(c['detail'])+'</p>'+link(c['evidence'])+'</article>'
    body += '</div></section><section class="sources"><h2>Evidence, straight from the project</h2><p>Routing facts live in <code>docs/status.md</code>. The board summarizes coordination; if sources change, review them before relying on these cards. Refresh reads both files again.</p><nav aria-label="Project artifacts">'+''.join(link(k) for k in ARTIFACTS)+'</nav><details><summary>Read current routing status</summary><pre>'+esc(source)+'</pre></details></section>'
    return shell('Project dashboard', body)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Reject nonlocal Host values to reduce DNS-rebinding exposure.
        if self.headers.get('Host','').split(':')[0] not in ('127.0.0.1','localhost'):
            self.send_error(403); return
        path=urlsplit(self.path).path
        try:
            if path=='/': content=render_board(load_board()); mime='text/html; charset=utf-8'
            elif path=='/refresh.js': content=(HERE/'refresh.js').read_text(); mime='text/javascript; charset=utf-8'
            elif path=='/style.css': content=(HERE/'style.css').read_text(); mime='text/css; charset=utf-8'
            elif path.startswith('/artifacts/') and path[len('/artifacts/'):] in ARTIFACTS:
                key=path[len('/artifacts/'):]
                content=shell(ARTIFACTS[key][0], '<a href="/">← Project dashboard</a><h1>'+esc(ARTIFACTS[key][0])+'</h1><p class="muted">Live local source · '+esc(ARTIFACTS[key][1])+'</p><pre>'+esc(read_artifact(key))+'</pre>');mime='text/html; charset=utf-8'
            else: self.send_error(404);return
            status=200
        except (OSError, ValueError, KeyError, TypeError) as exc:
            content=shell('Data unavailable','<h1>Project data unavailable</h1><p>The board could not load a valid coordination file or source document. No empty or outdated board is substituted.</p><p>Check dashboard/board.json and the allowlisted documents, then refresh.</p><a href="/">Retry</a>');mime='text/html; charset=utf-8';status=503
            print('Dashboard load error:',exc)
        raw=content.encode();self.send_response(status)
        self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers();self.wfile.write(raw)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print('Dashboard: http://127.0.0.1:'+str(args.port)+' — Ctrl-C to stop',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

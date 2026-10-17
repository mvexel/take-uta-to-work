import copy
import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import server

class DashboardTests(unittest.TestCase):
    def setUp(self): self.data=server.load_board()
    def test_counts_and_empty_requests(self):
        self.data['requests']=[]
        page=server.render_board(self.data)
        for state, name, _ in server.STATES:
            count=sum(c['state']==state for c in self.data['cards'])
            self.assertIn('id="heading-'+state+'">'+name+' <span class="count">'+str(count),page)
        self.assertIn('No verified decision requests.',page)
        self.assertIn('No verified action requests.',page)
        self.data['cards']=[]
        self.assertEqual(server.render_board(self.data).count('No work recorded in this state.'),4)
    def test_drift_age_and_escaping(self):
        self.data['status_sha256']='0'*64
        self.assertIn('Needs reconciliation',server.render_board(self.data))
        self.data['status_sha256']=server.hashlib.sha256(server.read_artifact('status').encode()).hexdigest()
        self.data['reviewed_at']='2000-01-01T00:00:00Z'
        self.assertIn('Review overdue',server.render_board(self.data))
        self.data['cards'][0]['title']='<script>alert(1)</script>'
        self.assertNotIn('<script>',server.render_board(self.data))
        self.data['requests']=[dict(kind='decision',ask='Choose <option>',owner='Martijn',impact='Example only',recommendation='Review choices',evidence='project',verified_at=self.data['reviewed_at'])]
        page=server.render_board(self.data)
        self.assertIn('Choose &lt;option&gt;',page)
        self.assertIn('Unblocks / impact',page)
        self.assertNotIn('No verified decision requests.',page)
    def test_invalid_data(self):
        self.data['cards'][0]['state']='invented'
        with patch.object(server.Path,'read_text',return_value=json.dumps(self.data)):
            with self.assertRaises(ValueError):server.load_board()
    def test_http_routes_and_errors(self):
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(httpd.server_port)
        try:
            for path in ['/','/style.css','/refresh.js']+['/artifacts/'+k for k in server.ARTIFACTS]:
                with urlopen(base+path) as response:
                    self.assertEqual(response.status,200)
                    self.assertEqual(response.headers['Cache-Control'],'no-store')
                    self.assertGreater(len(response.read()),0)
            for path in ['/board.json','/../AGENTS.md','/artifacts/../../.git/config','/artifacts/status/extra','/data/uta.gtfs.zip','/%2e%2e/README.md']:
                with self.assertRaises(HTTPError) as error:urlopen(base+path)
                self.assertEqual(error.exception.code,404)
            with self.assertRaises(HTTPError) as error:urlopen(Request(base,headers={'Host':'untrusted.example'}))
            self.assertEqual(error.exception.code,403)
            with patch.object(server,'load_board',side_effect=ValueError('broken data')):
                with self.assertRaises(HTTPError) as error:urlopen(base)
                self.assertEqual(error.exception.code,503)
                self.assertIn(b'Project data unavailable',error.exception.read())
        finally:httpd.shutdown();httpd.server_close();thread.join()

if __name__=='__main__':unittest.main()

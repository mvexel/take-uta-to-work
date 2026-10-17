import copy,sys,pathlib,unittest,tempfile,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from spike import inspect,variables,audit,run
from unittest.mock import patch
import io,json
class RoutingContract(unittest.TestCase):
 def setUp(self):
  self.it={'start':'2026-10-20T10:30:00-06:00','end':'2026-10-20T11:00:00-06:00','legs':[{'mode':'WALK','transitLeg':False},{'mode':'TRAM','transitLeg':True,'route':{'gtfsId':'UTA:red'}}]}
 def check(self,it=None,cap=0): return inspect(it or self.it,'2026-10-20T11:00:00-06:00','trax',cap,['UTA:red'])
 def test_exact_boundary(self): self.assertTrue(self.check()['qualifies'])
 def test_late(self):
  self.it['end']='2026-10-20T11:00:01-06:00';self.assertIn('late',self.check()['reasons'])
 def test_31_minutes(self):
  self.it['start']='2026-10-20T10:29:00-06:00';self.assertIn('duration',self.check()['reasons'])
 def test_sline_excluded(self):
  self.it['legs'][1]['route']['gtfsId']='UTA:sline';self.assertFalse(self.check()['qualifies'])
 def test_changes(self):
  self.it['legs'].append(copy.deepcopy(self.it['legs'][1]));self.assertFalse(self.check()['qualifies']);self.assertTrue(self.check(cap=1)['qualifies'])
 def test_stay_seated_is_not_vehicle_change(self):
  second=copy.deepcopy(self.it['legs'][1]);second['interlineWithPreviousLeg']=True;self.it['legs'].append(second);self.assertTrue(self.check(cap=0)['qualifies'])
 def test_earliness(self):
  self.it['end']='2026-10-20T10:59:00-06:00';self.assertEqual(self.check()['earliness_seconds'],60)
 def test_bike_rejects_transit(self): self.assertFalse(inspect(self.it,self.it['end'],'bike',0,[])['qualifies'])
 def test_bike_requires_bicycle(self):
  for legs in ([],[{'mode':'WALK','transitLeg':False}]):
   self.it['legs']=legs;self.assertFalse(inspect(self.it,self.it['end'],'bike',0,[])['qualifies'])
 def test_run_response_and_error_states(self):
  config={'destination':{'verified':True,'lat':40.7,'lon':-111.8},'arrival_local':'2026-10-20T11:00:00','routes':{'trax':['UTA:red']}}
  origins=[{'id':'test','lat':40.7,'lon':-111.9}]
  body={'data':{'planConnection':{'routingErrors':[],'pageInfo':{'hasNextPage':False},'edges':[{'node':self.it}]}}}
  with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
   self.assertEqual(run(config,origins,'http://localhost','trax',0)['results'][0]['status'],'qualifying_route')
  with patch('urllib.request.urlopen',side_effect=TimeoutError('synthetic timeout')):
   self.assertEqual(run(config,origins,'http://localhost','trax',0)['results'][0]['status'],'unknown')
 def test_bike_elevation_gap(self):
  self.it['legs']=[{'mode':'BICYCLE','transitLeg':False,'steps':[{'distance':10,'elevationProfile':[]}]}]
  self.assertIn('elevation_gap',inspect(self.it,self.it['end'],'bike',0,[])['reasons'])
  self.it['legs'][0]['steps'][0]['elevationProfile']=[{'distance':0,'elevation':1400},{'distance':10,'elevation':1401}]
  self.assertTrue(inspect(self.it,self.it['end'],'bike',0,[])['qualifies'])
 def test_destination_gate(self):
  with self.assertRaises(ValueError): variables({}, {'destination':{'verified':False}},'bus',0)
 def test_calendar_exception(self):
  with tempfile.NamedTemporaryFile(suffix='.zip') as f:
   with zipfile.ZipFile(f.name,'w') as z:
    z.writestr('calendar.txt','service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\na,1,1,1,1,1,0,0,20261001,20261031\n')
    z.writestr('calendar_dates.txt','service_id,date,exception_type\na,20261020,2\nb,20261020,1\n')
    z.writestr('agency.txt','agency_timezone\nAmerica/Denver\n');z.writestr('routes.txt','route_id,route_type\nx,0\n')
    z.writestr('trips.txt','route_id,service_id,trip_id\nx,b,t\n')
   result=audit(f.name,'2026-10-20');self.assertEqual(result['active_services'],['b']);self.assertEqual(result['active_trip_count'],1)
if __name__=='__main__': unittest.main()

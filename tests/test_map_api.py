import copy,datetime as dt,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from map_api import route,check_window,LATEST

def itinerary(arrival='2026-10-20T10:45:00-06:00',seconds=1800,route_id='1:8246',mode='TRAM'):
 end=dt.datetime.fromisoformat(arrival);start=end-dt.timedelta(seconds=seconds)
 return {'start':start.isoformat(),'end':end.isoformat(),'legs':[{'mode':mode,'transitLeg':True,'trip':{'gtfsId':'1:trip'},'route':{'gtfsId':route_id},'start':{'scheduledTime':start.isoformat()},'end':{'scheduledTime':end.isoformat()}}]}
def plan(its,more=False,cursor=None):return {'edges':[{'node':i} for i in its],'routingErrors':[],'pageInfo':{'hasNextPage':more,'endCursor':cursor}}
class MapContract(unittest.TestCase):
 def test_inclusive_window(self):
  for arrival in ['2026-10-20T10:45:00-06:00',LATEST]:self.assertTrue(check_window(itinerary(arrival),'trax',0,['1:8246'])['qualifies'])
 def test_outside_window(self):
  for arrival,reason in [('2026-10-20T10:44:59-06:00','too_early'),('2026-10-20T11:00:01-06:00','late')]:self.assertIn(reason,check_window(itinerary(arrival),'trax',0,['1:8246'])['reasons'])
 def test_utc_equivalence(self):self.assertTrue(check_window(itinerary('2026-10-20T16:45:00+00:00'),'trax',0,['1:8246'])['qualifies'])
 def test_duration_and_filter(self):
  self.assertIn('duration',check_window(itinerary(seconds=1801),'trax',0,['1:8246'])['reasons'])
  self.assertIn('route_or_mode',check_window(itinerary(route_id='1:45389'),'trax',0,['1:8246'])['reasons'])
  self.assertIn('route_or_mode',check_window(itinerary(),'bus',0,['1:8246'])['reasons'])
 def test_later_option_searched_after_early_option(self):
  calls=[]
  def request(endpoint,v,window,after=None):
   calls.append(copy.deepcopy(v));return plan([itinerary('2026-10-20T10:40:00-06:00')]) if len(calls)==1 else plan([itinerary()])
  r=route({'lat':40.76,'lon':-111.87},'trax',0,request)
  self.assertEqual(r['status'],'qualifying_route');self.assertIn('earliestDeparture',calls[1]['time'])
  self.assertEqual(calls[0]['preferences']['transit']['transfer']['maximumTransfers'],0)
 def test_incomplete_search_unknown(self):
  r=route({'lat':40.76,'lon':-111.87},'trax',1,lambda *a:plan([itinerary('2026-10-20T10:40:00-06:00')],True,'cursor'))
  self.assertEqual(r['status'],'unknown');self.assertIn('Search limit',r['error'])
 def test_exhausted_bounded_search(self):
  r=route({'lat':40.76,'lon':-111.87},'trax',1,lambda *a:plan([itinerary(seconds=2000)]))
  self.assertEqual(r['status'],'no_qualifying_returned_route')
 def test_exception_is_error(self):
  def fail(*a):raise TimeoutError('timeout')
  self.assertEqual(route({'lat':40.76,'lon':-111.87},'trax',1,fail)['status'],'error')
 def test_outside_extract_not_evaluated(self):self.assertEqual(route({'lat':41,'lon':-111.87},'trax',1)['status'],'not_evaluated')
 def test_wait_breakdown(self):
  it=itinerary(seconds=900);leg=it['legs'][0];leg['start']['scheduledTime']='2026-10-20T10:35:00-06:00'
  r=check_window(it,'trax',0,['1:8246']);self.assertEqual(r['breakdown']['wait'],300);self.assertEqual(sum(r['breakdown'][k] for k in ['walk','ride','bike','wait']),900)
if __name__=='__main__':unittest.main()

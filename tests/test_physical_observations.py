import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from physical_observations import create
class PhysicalTests(unittest.TestCase):
    def test_independent(self):
        m={'id':'a','sha256':'x','extent':[0,0,10,10],'metadata':{'source':'https://test/San_Joaquin_Valley_2021/ImageServer'}}
        b={'kind':'curb','geometry':{'type':'LineString','coordinates':[[1,1],[5,5]]},'image_source':'a'}
        v=create(b,[0,0,20,20],[m]);self.assertEqual(v['status'],'proposed');self.assertEqual(v['sources'][0]['id'],'a')
        b['geometry']['coordinates'][1]=[15,15]
        with self.assertRaises(ValueError):create(b,[0,0,20,20],[m])

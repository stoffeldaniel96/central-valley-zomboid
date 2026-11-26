import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shapely.geometry import LineString
from workbench_data import assemble,normalize
from workbench import proposal
class WorkbenchTests(unittest.TestCase):
    def test_fragmented_ring_with_hole(self):
        outer=[LineString([(0,0),(10,0),(10,10)]),LineString([(10,10),(0,10),(0,0)])]
        inner=[LineString([(2,2),(3,2),(3,3),(2,3),(2,2)])]
        g=assemble(outer,inner)
        self.assertEqual(g.area,99);self.assertTrue(g.is_valid)
    def test_open_ring(self):
        with self.assertRaises(ValueError):assemble([LineString([(0,0),(1,1)])],[])
    def test_proposal(self):
        f={'id':'way/1','geometry':{'type':'LineString','coordinates':[[0,0],[1,1]]}}
        p=proposal(f,{'type':'LineString','coordinates':[[0,0],[2,2]]},'reason','hash','survey',[-1,-1,3,3])
        self.assertEqual(p['status'],'proposed');self.assertEqual(p['before'],f['geometry'])
    def test_outside(self):
        f={'id':'way/1','geometry':{'type':'LineString','coordinates':[[0,0],[10,1]]}}
        with self.assertRaises(ValueError):proposal(f,{'type':'LineString','coordinates':[[0,0],[2,2]]},'reason','hash','survey',[-1,-1,3,3])

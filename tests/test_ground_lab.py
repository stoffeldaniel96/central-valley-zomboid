import sys,unittest,tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ground_lab import approximate,fixture,write_obj
class GroundTests(unittest.TestCase):
    def test_signed_and_flat(self):
        r,g=approximate(lambda x,y:np.full(x.shape,-.1),(0,0,2,2))
        self.assertTrue((g['proxy_level']==-1).all())
        self.assertEqual(r['slope_proxy_error']['max_m'],0)
        self.assertEqual(r['slope_proxy_shared_edge_disagreement']['max_m'],0)
    def test_grade(self):
        r,g=approximate(lambda x,y:.05*x,(0,0,4,4),.025,.025)
        self.assertLess(r['slope_proxy_error']['max_m'],1e-9)
        self.assertLess(r['slope_proxy_shared_edge_disagreement']['max_m'],1e-9)
    def test_missing(self):
        r,g=approximate(lambda x,y:np.where(x<1,np.nan,0),(0,0,2,2))
        self.assertEqual(r['unknown_tiles'],2)
    def test_fixture(self):
        r,g=approximate(fixture,(0,0,64,64))
        self.assertGreater(r['negative_center_tiles'],0)
        self.assertGreater(r['cross_storey_tiles'],0)
        self.assertLess(r['slope_proxy_error']['p95_m'],r['flat_proxy_error']['p95_m'])

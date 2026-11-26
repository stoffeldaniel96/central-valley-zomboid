import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from build_elevation import stats,colorize
from analyze_lidar import update_max
from fetch_elevation import allowed
class ElevationTests(unittest.TestCase):
    def test_missing(self):
        z=np.array([[np.nan,10],[12,14]],dtype=float)
        self.assertEqual(stats(z)['valid_fraction'],.75)
        self.assertEqual(stats(z)['median_m'],12)
        rgb,lo,hi=colorize(z)
        self.assertEqual(rgb[0,0].tolist(),[90,90,90])
    def test_repeated_returns(self):
        g=np.full((2,2),-np.inf)
        update_max(g,np.array([0,0]),np.array([1,1]),np.array([7,4]))
        self.assertEqual(g[0,1],7)
    def test_hosts(self):
        self.assertTrue(allowed('https://prd-tnm.s3.amazonaws.com/a.laz'))
        self.assertFalse(allowed('https://prd-tnm.s3.amazonaws.com.evil.test/a.laz'))

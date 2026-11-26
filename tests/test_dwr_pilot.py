import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from fetch_dwr_pilot import plan
class GridTests(unittest.TestCase):
    def test_aligned(self):
        g=plan([-13453871,4506993,-13451292,4509582],.08,4000)
        self.assertEqual(sum(p['width']*p['height'] for p in g['patches']),g['width']*g['height'])
        p={v['key']:v for v in g['patches']}
        self.assertAlmostEqual(p['0-0']['extent'][2],p['0-1']['extent'][0],places=6)
        self.assertAlmostEqual(p['0-0']['extent'][1],p['1-0']['extent'][3],places=6)
        self.assertTrue(all(max(v['width'],v['height'])<=4000 for v in p.values()))

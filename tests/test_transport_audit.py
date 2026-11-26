import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shapely.geometry import LineString
from shapely.strtree import STRtree
from transport_audit import gap_parts
class AuditTests(unittest.TestCase):
    def test_complete(self):
        g=LineString([(0,0),(100,0)])
        self.assertEqual(gap_parts(g,[g],STRtree([g])),[])
    def test_missing_stretch(self):
        g=LineString([(0,0),(100,0)])
        refs=[LineString([(0,0),(25,0)]),LineString([(75,0),(100,0)])]
        parts=gap_parts(g,refs,STRtree(refs),5,12)
        self.assertEqual(len(parts),1);self.assertAlmostEqual(parts[0].length,40)
    def test_offset(self):
        g=LineString([(0,0),(100,0)]);r=LineString([(0,8),(100,8)])
        self.assertAlmostEqual(gap_parts(g,[r],STRtree([r]),3)[0].length,100)
    def test_short_gap_ignored(self):
        g=LineString([(0,0),(8,0)])
        self.assertEqual(gap_parts(g,[],STRtree([])),[])

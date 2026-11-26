import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shapely.geometry import box
from shapely.strtree import STRtree
from building_evidence import compare
class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.ref=[box(0,0,10,10)]
        self.tree=STRtree(self.ref)
    def test_match(self):
        self.assertEqual(compare(box(0,0,10,10),self.ref,self.tree)[0],'matched')
    def test_gap(self):
        self.assertEqual(compare(box(20,0,30,10),self.ref,self.tree)[0],'coverage_candidate')
    def test_partial(self):
        self.assertEqual(compare(box(5,0,15,10),self.ref,self.tree)[0],'review_overlap')
    def test_near(self):
        self.assertEqual(compare(box(11,0,21,10),self.ref,self.tree)[0],'review_overlap')
    def test_empty(self):
        self.assertEqual(compare(box(0,0,1,1),[],STRtree([]))[0],'coverage_candidate')

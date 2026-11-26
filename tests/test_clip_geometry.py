import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from analyze_geometry import clip_segment
class ClipTests(unittest.TestCase):
    def test_crossing(self):
        self.assertEqual(clip_segment(-20,5,20,5,(-10,0,10,10)),(-10,5,10,5))
    def test_outside(self):
        self.assertIsNone(clip_segment(-20,15,20,15,(-10,0,10,10)))
    def test_reverse(self):
        self.assertEqual(clip_segment(20,5,-20,5,(-10,0,10,10)),(10,5,-10,5))
    def test_inside(self):
        self.assertEqual(clip_segment(1,2,3,4,(0,0,10,10)),(1,2,3,4))
    def test_vertical(self):
        self.assertEqual(clip_segment(5,-5,5,15,(0,0,10,10)),(5,0,5,10))

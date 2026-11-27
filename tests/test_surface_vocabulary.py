import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from surface_vocabulary import analyze
class VocabularyTests(unittest.TestCase):
    def test_reuse_and_conflict(self):
        a=np.zeros((64,1,12),dtype=int);a[:32,0,:10]=1;a[:32,0,10]=1;a[9,0,10]=0;a[0,0,11]=-1
        r=analyze(a,['pavement'])
        self.assertEqual(r['excluded_conflict_tiles'],1)
        self.assertEqual(r['exact_frequent_placements'],10)
        self.assertEqual(r['approximated_placements'],1)
        self.assertEqual(r['changed_sample_count'],1)
    def test_edge_locked(self):
        a=np.zeros((64,1,11),dtype=int);a[:32,0,:]=1;a[0,0,10]=0
        r=analyze(a,['pavement'])
        self.assertEqual(r['unresolved_placements'],1)

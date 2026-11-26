import csv,json,subprocess,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class IndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,str(R/'src/build_index.py')],check=True,capture_output=True)
        cls.stats=json.loads((R/'output/stats.json').read_text())
    def test_baseline(self):
        self.assertEqual(self.stats['dimensions_cells'],[258,214])
        self.assertEqual(self.stats['pilot_cells'],[-4,-4,4,4])
    def test_sector_partition(self):
        with (R/'output/sectors.csv').open() as f:
            rows=list(csv.DictReader(f))
        seen=set()
        for row in rows:
            for x in range(int(row['x0']),int(row['x1'])):
                for y in range(int(row['y0']),int(row['y1'])):
                    self.assertNotIn((x,y),seen)
                    seen.add((x,y))
        a,b,c,d=self.stats['global_cells']
        self.assertEqual(seen,{(x,y) for x in range(a,c) for y in range(b,d)})
        self.assertEqual(len(rows),self.stats['sectors'])
if __name__=='__main__': unittest.main()

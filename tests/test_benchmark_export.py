import sys,unittest,io,json,zipfile,tempfile,hashlib
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from benchmark_export import capture
class BenchmarkTests(unittest.TestCase):
    def test_crop_and_extent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'pilot.jpg';Image.new('RGB',(100,100),'gray').save(p)
            d={'extent':[0,0,100,100],'source_sha256':'test','features':[],
               'aerial':{'extent':[0,0,100,100],'width':100,'height':100,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}}
            z=zipfile.ZipFile(io.BytesIO(capture(d,[45,45,55,55],p)))
            m=json.loads(z.read('benchmark.json'))
            self.assertEqual(m['view_extent'],[45,45,55,55])
            self.assertEqual(m['aerial_crop']['extent'],[5,5,95,95])
            self.assertEqual(Image.open(io.BytesIO(z.read('aerial.png'))).size,(90,90))
    def test_outside(self):
        with self.assertRaises(ValueError):capture({'extent':[0,0,1,1]},[2,2,3,3],Path('unused'))

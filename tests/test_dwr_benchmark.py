import sys,unittest,io,zipfile,tempfile,hashlib,json
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from benchmark_export import capture
class DwrBenchmarkTests(unittest.TestCase):
    def test_native_crops(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'patch.jpg';Image.new('RGB',(100,100),'gray').save(p)
            m={'id':'a','extent':[0,0,100,100],'width':100,'height':100,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            data={'extent':[0,0,100,100],'source_sha256':'x','features':[]}
            with zipfile.ZipFile(io.BytesIO(capture(data,[45,45,55,55],p,[(m,p)]))) as z:
                spec=json.loads(z.read('benchmark.json'))['dwr_crops'][0]
                self.assertEqual(spec['extent'],[5,5,95,95])
                self.assertEqual(Image.open(io.BytesIO(z.read(spec['file']))).size,(90,90))

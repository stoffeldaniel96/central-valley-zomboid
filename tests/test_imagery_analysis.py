import sys,unittest,tempfile,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from imagery_analysis import Sampler,rail_pair_scores
class AnalysisTests(unittest.TestCase):
    def test_cross_patch(self):
        with tempfile.TemporaryDirectory() as folder:
            items=[]
            for i,v in enumerate([20,100]):
                p=Path(folder)/f'{i}.png';Image.new('L',(10,10),v).save(p)
                items.append(({'id':str(i),'extent':[i*10,0,(i+1)*10,10],'width':10,'height':10,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},p))
            sampler=Sampler(items)
            np.testing.assert_allclose(sampler.sample([9.9,10.1],[5,5]),[20,100])
            self.assertIsNone(sampler.sample([9,21],[5,5]))
    def test_gauge_pair(self):
        def sample(x,y):
            return 20+100*np.exp(-((np.abs(y-4)-.76)/.06)**2)
        off=np.arange(-6,6.01,.25)
        score=rail_pair_scores(sample,np.arange(20)[None,:],np.zeros((1,20)),0,1,off)
        self.assertAlmostEqual(off[np.argmax(score)],4)

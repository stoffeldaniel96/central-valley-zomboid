import sys,unittest,tempfile
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from imagery_registry import register,worldfile_extent,list_layers,tile_path
class ImageryTests(unittest.TestCase):
    def test_pyramid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);im=p/'a.png';Image.new('RGB',(1025,513),'gray').save(im)
            root=p/'registry';m=register(im,[0,0,1025,513],'test',registry=root)
            self.assertEqual(m['usage'],'reference_only')
            self.assertEqual([l['width'] for l in m['levels']],[1025,513,257])
            self.assertEqual(Image.open(tile_path(m['id'],0,2,1,root)).size,(1,1))
            self.assertIsNone(tile_path(m['id'],0,3,0,root))
            self.assertEqual(len(list_layers(root)),1)
            self.assertFalse((root/m['id']/'analysis.png').exists())
            self.assertEqual(register(im,[0,0,1025,513],'test',registry=root)['id'],m['id'])
    def test_worldfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.pgw';p.write_text('2\n0\n0\n-2\n101\n199\n')
            self.assertEqual(worldfile_extent(p,10,20),[100,160,120,200])
    def test_rights(self):
        with self.assertRaises(ValueError):register(Path('unused'),[0,0,1,1],'test',usage='analysis_reviewed')

import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from export_presets import make_preset

class PresetTests(unittest.TestCase):
    def test_export(self):
        template=json.loads((ROOT/'config/knoxmap/pilot.knoxmap.json').read_text())
        p=make_preset(template,'test',[-121,37,-120,38])
        self.assertEqual(p['format'],'knoxmap-preset')
        self.assertEqual(p['version'],1)
        self.assertEqual(p['metersPerTile'],1)
        self.assertEqual(p['settings']['align_streets'],0)
        self.assertEqual(p['settings']['basement_share'],0)
        self.assertEqual(p['west'],-121)
        self.assertEqual(p['north'],38)
        self.assertNotEqual(template['name'],p['name'])
    def test_bad_bbox(self):
        with self.assertRaises(ValueError):
            make_preset({},'bad',[0,1,-1,2])

import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from analyze_geometry import metrics,analyze
from inventory_assets import inventory
class DiagnosticsTests(unittest.TestCase):
    def test_angles(self):
        self.assertAlmostEqual(metrics(1,1)[3],0)
        self.assertAlmostEqual(metrics(1,1)[2],45)
        self.assertAlmostEqual(metrics(0,1)[2],0)
    def test_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'media').mkdir();(p/'media/test.pack').write_bytes(b'abc')
            self.assertEqual(list(inventory(p)),[['media/test.pack','.pack',3]])
    def test_length_conservation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.osm';p.write_text('<osm><node id="1" lat="37.49" lon="-120.85"/><node id="2" lat="37.50" lon="-120.84"/><way id="3"><nd ref="1"/><nd ref="2"/><tag k="highway" v="residential"/></way></osm>')
            rows,bins,hist,missing,rels=analyze(p,'+proj=aeqd +lat_0=37.4947 +lon_0=-120.8466 +datum=WGS84 +units=m',256)
            self.assertEqual(len(rows),1);self.assertEqual(missing,0)
            self.assertAlmostEqual(sum(z[0] for z in bins.values()),rows[0][3])

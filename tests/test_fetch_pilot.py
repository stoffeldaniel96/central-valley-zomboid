import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from fetch_pilot import validate,query_for
class FetchTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(b'<osm><node id="1"/><way id="2"><nd ref="1"/></way></osm>').tag,'osm')
    def test_missing_node(self):
        with self.assertRaises(ValueError):validate(b'<osm><way id="2"><nd ref="1"/></way></osm>')
    def test_remark(self):
        with self.assertRaises(ValueError):validate(b'<osm><remark>timeout</remark><way id="2"/></osm>')
    def test_query(self):
        q=query_for([-121,37,-120,38])
        self.assertIn('way["highway"](37,-121,38,-120)',q)
        self.assertIn('out body;',q)

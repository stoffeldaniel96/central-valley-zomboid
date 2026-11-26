import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from compile_pilot import commands

class CompilerTests(unittest.TestCase):
    def test_default(self):
        p=Path('pilot')
        c=commands(Path('python'),p)
        self.assertEqual(c[0][1:3],['-m','knoxbuild'])
        self.assertEqual(c[1][-1],str(p/'buildings'))
        self.assertEqual(c[2][1],'tools/compile_map.py')
    def test_reuse(self):
        self.assertEqual(len(commands(Path('python'),Path('pilot'),False)),2)

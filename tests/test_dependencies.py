import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dependencies import scan
class ScanTests(unittest.TestCase):
    def test_local_stdlib_alias_and_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'local.py').write_text('')
            (p/'main.py').write_text('import os, local\nfrom PIL import Image\nimport yaml\nfrom . import internal\n')
            (p/'venv').mkdir(); (p/'venv'/'fake.py').write_text('import excluded')
            result=scan(p,{'os'})
            self.assertEqual({x['package'] for x in result['dependencies']},{'Pillow','PyYAML'})
    def test_invalid_file_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'bad.py').write_text('def !'); (p/'main.py').write_text('import mystery')
            result=scan(p,set(),{'mystery':['real-package']})
            self.assertEqual(result['dependencies'][0]['package'],'real-package'); self.assertEqual(len(result['warnings']),1)
if __name__=='__main__':unittest.main()

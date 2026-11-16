# Autor: Aldo Machado
"""Static dependency suggestions; never imports project modules."""
import ast
import json
import os
from pathlib import Path
import sys
import tokenize

EXCLUDED = {'venv','.venv','env','.env','__pycache__','.git','.hg','.svn','build','dist','node_modules','.tox','.nox','.mypy_cache','.pytest_cache','site-packages'}
ALIASES = {'PIL':'Pillow','cv2':'opencv-python','yaml':'PyYAML','bs4':'beautifulsoup4','sklearn':'scikit-learn','dotenv':'python-dotenv','dateutil':'python-dateutil','fitz':'PyMuPDF','serial':'pyserial','Crypto':'pycryptodome','OpenSSL':'pyOpenSSL','win32api':'pywin32','win32com':'pywin32','win32gui':'pywin32','usb':'pyusb','skimage':'scikit-image','pptx':'python-pptx','docx':'python-docx'}

def scan(root, stdlib=None, installed=None, exclude_paths=()):
    root=Path(root).resolve(); files=[]; local=set(); warnings=[]
    excluded={Path(p).resolve() for p in exclude_paths}
    stdlib=set(stdlib if stdlib is not None else getattr(sys,'stdlib_module_names',sys.builtin_module_names))
    installed=installed or {}
    for directory, dirs, names in os.walk(root, followlinks=False):
        base=Path(directory)
        dirs[:]=[d for d in dirs if d not in EXCLUDED and not d.startswith('.') and not (base/d).is_symlink() and (base/d).resolve() not in excluded and not (base/d/'pyvenv.cfg').is_file()]
        for name in names:
            p=base/name
            if p.suffix=='.py' and not p.is_symlink():
                files.append(p); local.add(p.stem)
                local.update(p.relative_to(root).parts[:-1])
    found={}
    for p in files:
        try:
            with tokenize.open(p) as f: tree=ast.parse(f.read(), filename=str(p))
        except (OSError, SyntaxError, UnicodeError) as e:
            warnings.append(f'{p.relative_to(root)}: {e}'); continue
        for node in ast.walk(tree):
            imports=[n.name for n in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and not node.level and node.module else []
            for module in imports:
                name=module.split('.')[0]
                if name in local or name in stdlib: continue
                found.setdefault(name,set()).add(str(p.relative_to(root)))
    results=[]
    for name, paths in sorted(found.items(),key=lambda x:x[0].lower()):
        candidates=sorted(set(installed.get(name,[])))
        package=candidates[0] if len(candidates)==1 else ALIASES.get(name,name)
        source='installed' if len(candidates)==1 else 'alias' if name in ALIASES else 'guess'
        results.append(dict(module=name,package=package,source=source,candidates=candidates,files=sorted(paths)))
    return dict(dependencies=results,warnings=warnings,files=len(files))

# Invoked inside the selected Python, not the frozen manager.
METADATA_CODE = '''import sys,json,sysconfig,pathlib,importlib.metadata as m
stdlib=set(getattr(sys,'stdlib_module_names',sys.builtin_module_names))
if not hasattr(sys,'stdlib_module_names'):
 p=pathlib.Path(sysconfig.get_path('stdlib')); stdlib.update(x.stem for x in p.glob('*.py')); stdlib.update(x.name for x in p.iterdir() if x.is_dir() and (x/'__init__.py').exists() and x.name not in ('site-packages','dist-packages'))
 for d in ('lib-dynload','DLLs'):
  for x in (p/d).glob('*'): stdlib.add(x.name.split('.')[0])
print(json.dumps({'stdlib':sorted(stdlib),'installed':m.packages_distributions() if hasattr(m,'packages_distributions') else {}}))'''
COMPARE_CODE = '''import json,sys,importlib.metadata as m
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.utils import canonicalize_name
from pathlib import Path
rows=[]; required=set(); installed={canonicalize_name(d.metadata['Name']):d.version for d in m.distributions() if d.metadata.get('Name')}
for raw in Path(sys.argv[1]).read_text(encoding='utf-8-sig').splitlines():
 line=raw.split(' #',1)[0].strip()
 if not line or line.startswith('#'):continue
 try:
  r=Requirement(line); key=canonicalize_name(r.name); v=installed.get(key); required.add(key)
  if r.marker and not r.marker.evaluate():status='no aplicable'
  elif r.url or r.extras:status='revisar URL/extras'
  elif not v:status='faltante'
  elif r.specifier and not r.specifier.contains(v,prereleases=True):status='incompatible'
  else:status='correcto'
  rows.append([line,v or '',status])
 except Exception:rows.append([line,'','revisar manualmente'])
print(json.dumps({'requirements':rows,'additional':sorted(set(installed)-required)}))'''

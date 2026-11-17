"""Project-local configuration; standard library only."""
# Autor: Aldo Machado
import hashlib, json, os, re, shutil, tempfile, uuid
from pathlib import Path

WINDOWS=os.name=='nt'
HOME=Path.home()
LEGACY_STATE=(Path(os.environ.get('LOCALAPPDATA',HOME/'AppData/Local')) if WINDOWS else Path(os.environ.get('XDG_CONFIG_HOME',HOME/'.config')))/'python-venv-tools'
DEFAULT_ROOT=Path('C:/venv-tool') if WINDOWS else Path(os.environ.get('XDG_DATA_HOME',HOME/'.local/share'))/'venv-tool'
LEGACY_BASE=Path('C:/venvs') if WINDOWS else Path(os.environ.get('XDG_DATA_HOME',HOME/'.local/share'))/'venvs'

def key(p):
    return os.path.normcase(str(Path(p).expanduser().resolve()))

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def write(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as f:
            tmp=Path(f.name); json.dump(d,f,indent=2,ensure_ascii=False); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if tmp is not None and tmp.exists():tmp.unlink()

def root():
    override=os.environ.get('VENV_TOOL_ROOT') or os.environ.get('PYTHON_VENV_TOOLS_ROOT')
    if override:return Path(override).expanduser().resolve()
    p=LEGACY_STATE/'storage.json'
    return Path(read(p)['root']).expanduser().resolve() if p.is_file() else DEFAULT_ROOT

def set_root(p):
    p=Path(p).resolve()
    if p==Path(p.anchor):raise ValueError('Choose a dedicated data directory')
    p.mkdir(parents=True,exist_ok=True)
    write(LEGACY_STATE/'storage.json',{'root':str(p)})

def valid_name(name):
    if not isinstance(name,str) or not name or name in ('.','..') or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or name.endswith(('.',' ')):
        raise ValueError('Invalid project name')
    if name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*('COM'+str(i) for i in range(1,10)),*('LPT'+str(i) for i in range(1,10))}:raise ValueError('Reserved project name')
    return name

def folder(d):
    return Path(d['base'])/valid_name(d['name'])

def env_path(d):
    return Path(d['project'])/('venv' if WINDOWS else '.venv') if d['local'] else folder(d)/'venv'

def config_path(d):
    return folder(d)/'config'/'config.json'

def cache_path(d):
    return Path(d['cache_base'])/d['name']/legacy_id(d['project']) if d.get('custom_cache') else folder(d)/'pycache'

def interpreter_path(d):
    return env_path(d)/('Scripts/python.exe' if WINDOWS else 'bin/python')

def validate(d):
    if not isinstance(d,dict):raise ValueError('Invalid config')
    valid_name(d['name'])
    for k in ('base','project','cache_base'):
        if not isinstance(d[k],str) or not Path(d[k]).is_absolute():raise ValueError('Invalid path: '+k)
    if not isinstance(d['local'],bool) or not isinstance(d['no_cache'],bool):raise ValueError('Invalid flags')
    if d['engine'] not in ('pip','uv'):raise ValueError('Invalid engine')
    return d

def legacy_id(project):
    return hashlib.sha256(key(project).encode()).hexdigest()[:24]

def index_path(project):
    return root()/'config'/'index'/(legacy_id(project)+'.json')

def load(project):
    project=key(project)
    idx=index_path(project)
    if idx.is_file():
        p=Path(read(idx)['config'])
        if p.is_file():
            d=validate(read(p))
            if key(d['project'])==project:return d
    old=LEGACY_STATE/(legacy_id(project)+'.json')
    if old.is_file():
        d=validate(read(old))
        if key(d['project'])==project:return d
    f=root()/'projects'/Path(project).name/'config'/'config.json'
    if f.is_file():
        d=validate(read(f))
        if key(d['project'])==project:return d
    return {}

def save(d):
    d=dict(validate(d))
    d['project']=key(d['project'])
    p=config_path(d)
    if p.exists():
        old=read(p)
        if key(old['project'])!=key(d['project']):raise ValueError('Project folder already belongs to another project')
        d['id']=old.get('id') or d.get('id') or str(uuid.uuid4())
    else:d['id']=d.get('id') or str(uuid.uuid4())
    d['schema_version']=1
    write(p,d)
    write(index_path(d['project']),{'config':str(p.resolve())})
    return d

def discover(base=None):
    base=Path(base or root()/'projects')
    records=[]; warnings=[]
    if not base.is_dir():return records,warnings
    for p in sorted(base.iterdir()):
        f=p/'config'/'config.json'
        if p.is_symlink():continue
        if not f.is_file():
            marker=p/'venv'/'.project-owner.json'
            if marker.is_file():warnings.append(str(p)+': legacy environment; use migration')
            continue
        try:
            d=validate(read(f))
            if not d.get('id'):raise ValueError('Missing project ID')
            uuid.UUID(d['id'])
            # A copied directory may be relocated; internal paths follow its actual location.
            d=dict(d,base=str(base.resolve()),name=p.name)
            if not d.get('custom_cache'):d['cache_base']=str(p/'pycache')
            records.append(d)
        except (ValueError,KeyError,TypeError,OSError) as e:warnings.append(str(f)+': '+str(e))
    return records,warnings

def recover(base=None):
    records,warnings=discover(base)
    seen=set()
    for d in records:
        project=key(d['project'])
        if project in seen:
            warnings.append('Duplicate source path: '+project); continue
        seen.add(project)
        old=load(project)
        if old and old.get('id') and old.get('id')!=d.get('id'):
            warnings.append('Conflicting project ID: '+project); continue
        if old and old.get('id') and config_path(old).resolve()!=config_path(d).resolve() and config_path(old).is_file():
            warnings.append('Project already registered elsewhere: '+project); continue
        save(d)
    return records,warnings

def registered():
    records,warnings=discover()
    result={str(config_path(d).resolve()):d for d in records}
    for p in (root()/'config'/'index').glob('*.json'):
        try:
            f=Path(read(p)['config']); d=validate(read(f))
            result[str(f.resolve())]=d
        except (OSError,ValueError,KeyError,TypeError):continue
    return list(result.values())

def migrate_legacy(base=None):
    # Register in place. Never move existing virtual environments.
    candidates=[]
    for p in LEGACY_STATE.glob('*.json'):
        try:candidates.append(validate(read(p)))
        except (OSError,ValueError,KeyError,TypeError):continue
    if base is not None:
        base=Path(base).resolve()
        for p in base.glob('*/venv/.project-owner.json'):
            try:
                owner=read(p)['project']; name=p.parent.parent.name
                candidates.append(dict(project=owner,name=name,base=str(base),local=False,python=None,cache_base=str(base/'pycache'),no_cache=False,engine='pip',custom_cache=False))
            except (OSError,ValueError,KeyError,TypeError):continue
    count=0; errors=[]
    for d in candidates:
        try:
            v=env_path(d); marker=v/'.project-owner.json'
            if not marker.is_file() or key(read(marker)['project'])!=key(d['project']):raise ValueError('Owner marker missing or mismatched')
            f=config_path(d)
            if f.exists():
                existing=validate(read(f))
                if key(existing['project'])!=key(d['project']):raise ValueError('Existing configuration belongs to another project')
                if key(env_path(existing))!=key(v):raise ValueError('Existing configuration points to another environment')
                idx=index_path(existing['project'])
                if idx.exists():
                    if Path(read(idx)['config']).resolve()!=f.resolve():raise ValueError('Project already indexed elsewhere')
                    continue
                write(idx,{'config':str(f.resolve())})
            else:
                save(dict(d,custom_cache=False,cache_base=str(folder(d)/'pycache')))
            count+=1
        except (OSError,ValueError,KeyError,TypeError) as e:errors.append(str(d.get('project'))+': '+str(e))
    return count,errors

def snapshot(d,lock=None):
    target=config_path(d).parent
    target.mkdir(parents=True,exist_ok=True)
    req=Path(d['project'])/'requirements.txt'
    if req.is_file():
        tmp=target/'requirements.txt.pending'
        shutil.copyfile(req,tmp); os.replace(tmp,target/'requirements.txt')
    if lock is not None:
        tmp=target/'requirements-lock.txt.pending'
        tmp.write_text(lock,encoding='utf-8'); os.replace(tmp,target/'requirements-lock.txt')

def safe_managed(d,part):
    if part not in ('venv','pycache'):raise ValueError('Invalid managed resource')
    p=folder(d)/part
    source=Path(d['project']).resolve()
    resolved=p.resolve()
    if p.is_symlink() or folder(d).is_symlink() or resolved.parent!=folder(d).absolute() or resolved==source or resolved in source.parents or source in resolved.parents:
        raise ValueError('Unsafe path; no data removed')
    if d.get('id') is None or not config_path(d).is_file() or read(config_path(d)).get('id')!=d.get('id'):raise ValueError('Project ownership not verified')
    return p

def clear_cache(d):
    p=safe_managed(d,'pycache')
    if p.exists():shutil.rmtree(p)

def size(p):
    total=0
    for directory,dirs,files in os.walk(p,followlinks=False):
        dirs[:]=[x for x in dirs if not (Path(directory)/x).is_symlink()]
        for name in files:
            try:
                f=Path(directory)/name
                if not f.is_symlink():total+=f.stat().st_size
            except OSError:pass
    return total

def reassociate(d,new):
    new=Path(new).resolve()
    if not new.is_dir():raise ValueError('Source folder does not exist')
    if d['local']:raise ValueError('Local environments must be recreated at the new source')
    if Path(d['project']).is_dir():raise ValueError('Old source still exists; refusing ambiguous reassociation')
    if load(new):raise ValueError('New source is already registered')
    marker=env_path(d)/'.project-owner.json'
    if marker.is_file() and key(read(marker)['project'])!=key(d['project']):raise ValueError('Owner mismatch')
    old=dict(d); updated=dict(d,project=key(new))
    if marker.is_file():write(marker,{'project':key(new)})
    try:write(config_path(updated),updated); write(index_path(new),{'config':str(config_path(updated))})
    except Exception:
        write(config_path(old),old)
        if marker.is_file():write(marker,{'project':key(old['project'])})
        raise
    old_index=index_path(old['project'])
    if old_index.exists():old_index.unlink()
    # Keep the previous legacy record untouched; it is not an active index.
    return updated

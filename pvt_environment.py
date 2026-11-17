"""Read-only environment checks and asynchronous command construction."""
# Autor: Aldo Machado
import os,sys,subprocess
from pathlib import Path
import pvt_storage as storage

def command(mode,d,extra=()):
    if getattr(sys,'frozen',False):
        cli=[str(Path(sys.executable).parent/'venv_cli.exe')]
    else:
        cli=[sys.executable,'-I','-B',str(Path(__file__).resolve().parent/'venv_manager.py')]
    args=cli+[mode,'--name',d['name'],'--path',d['base'],'--local' if d['local'] else '--external','--engine',d['engine'],'--no-cache' if d['no_cache'] else '--cache']
    if d.get('custom_cache'):args+=['--cache-path',d['cache_base']]
    if d.get('python'):args+=['--python',d['python']]
    return args+list(extra)

def state(d):
    if not Path(d['project']).is_dir():return 'Ruta del código no encontrada'
    v=storage.env_path(d)
    p=storage.interpreter_path(d)
    if not (v/'pyvenv.cfg').is_file() or not p.is_file():return 'Sin entorno / incompleto'
    try:
        owner=storage.read(v/'.project-owner.json')
        if storage.key(owner['project'])!=storage.key(d['project']):return 'Propietario distinto'
    except (OSError,ValueError,KeyError):return 'Sin propietario válido'
    return 'Detectado (sin verificar)'

def check(d):
    if state(d)!='Detectado (sin verificar)':return state(d)
    v=storage.env_path(d)
    env={k:x for k,x in os.environ.items() if not k.upper().startswith(('PYTHON','PIP_'))}
    code='import sys,site,pip; from pathlib import Path; p=Path(sys.prefix).resolve(); assert p==Path(sys.argv[1]).resolve() and sys.prefix!=sys.base_prefix and not site.ENABLE_USER_SITE and p in Path(pip.__file__).resolve().parents; print(sys.version.split()[0])'
    try:
        r=subprocess.run([str(storage.interpreter_path(d)),'-I','-B','-c',code,str(v)],env=env,capture_output=True,text=True,timeout=15)
        return 'Python '+r.stdout.strip()+' — correcto' if r.returncode==0 else 'Intérprete inválido: '+r.stderr.strip()[-500:]
    except (OSError,subprocess.TimeoutExpired) as e:return 'No disponible: '+str(e)

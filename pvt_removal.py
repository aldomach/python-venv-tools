"""Conservative removal of registered external resources only."""
# Autor: Aldo Machado
import os
import stat
from pathlib import Path
import shutil
import pvt_storage as s

LABELS={'venv':'Entorno virtual externo','pycache':'Caché individual','backups':'Respaldos administrados','config':'Configuración y registro'}

def linked(p):
    try:
        st=p.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st,'st_file_attributes',0)&0x400)

def overlap(a,b):
    a=Path(s.key(a));b=Path(s.key(b))
    return a==b or a in b.parents or b in a.parents

def safe(p,sources):
    p=Path(p).absolute()
    if p==Path(p.anchor) or any(linked(x) for x in (p,*p.parents)):
        raise ValueError('Ruta insegura o enlace: '+str(p))
    if any(overlap(p,source) for source in sources):
        raise ValueError('Ruta protegida de código fuente: '+str(p))
    return p

def inspect_tree(p):
    if not p.exists():return
    if not p.is_dir():raise ValueError('No es una carpeta: '+str(p))
    for directory,dirs,files in os.walk(p,followlinks=False):
        for name in dirs:
            child=Path(directory)/name
            if linked(child) or os.path.ismount(child):
                raise ValueError('Enlace o punto de montaje dentro del recurso: '+str(child))
        # Regular file symlinks in Linux venvs are unlinked, never followed.
        for name in files:
            child=Path(directory)/name
            if linked(child) and os.name=='nt':
                raise ValueError('Enlace dentro del recurso: '+str(child))

def plan(d,choices):
    d=s.validate(dict(d));choices=set(choices)
    if not choices or not choices<=LABELS.keys():raise ValueError('Selecciona recursos válidos')
    sources={d['project']}
    for other in s.registered():sources.add(other['project'])
    # Include legacy records not in the active index.
    for f in s.LEGACY_STATE.glob('*.json'):
        if f.name=='storage.json':continue
        old=s.validate(s.read(f))
        sources.add(old['project'])
    conf=safe(s.config_path(d),sources)
    stored=s.validate(s.read(conf))
    if not d.get('id') or stored.get('id')!=d['id'] or s.key(stored['project'])!=s.key(d['project']) or s.key(s.folder(stored))!=s.key(s.folder(d)):
        raise ValueError('La configuración registrada no coincide')
    if 'venv' in choices and stored['local']:raise ValueError('Los entornos locales están protegidos')
    paths=[]
    if 'venv' in choices:
        v=safe(s.env_path(stored),sources)
        if v.exists():
            owner=v/'.project-owner.json'
            if linked(owner) or s.key(s.read(owner)['project'])!=s.key(stored['project']):
                raise ValueError('Propietario del entorno no verificado')
            paths.append(('dir',v))
    if 'pycache' in choices:
        if stored.get('custom_cache'):raise ValueError('La caché personalizada no se elimina automáticamente')
        p=safe(s.folder(stored)/'pycache',sources)
        if p.exists():paths.append(('dir',p))
    if 'backups' in choices and 'config' not in choices:
        p=safe(conf.parent/'backups',sources)
        if p.exists():paths.append(('dir',p))
    if 'config' in choices:
        # Keep backups unless explicitly selected. Delete only known files.
        if 'backups' in choices:
            p=safe(conf.parent/'backups',sources)
            if p.exists():paths.append(('dir',p))
        for name in ('requirements.txt','requirements-lock.txt','config.json'):
            p=safe(conf.parent/name,sources)
            if p.exists():paths.append(('file',p))
        idx=safe(s.index_path(stored['project']),sources)
        if idx.exists() and Path(s.read(idx)['config']).resolve()==conf.resolve():
            paths.append(('file',idx))
            # Prevent fallback to obsolete settings from the old version.
            old=safe(s.LEGACY_STATE/(s.legacy_id(stored['project'])+'.json'),sources)
            if old.exists():
                previous=s.validate(s.read(old))
                if s.key(previous['project'])==s.key(stored['project']) and s.key(s.env_path(previous))==s.key(s.env_path(stored)):
                    paths.append(('file',old))
    for kind,p in paths:
        if kind=='dir':inspect_tree(p)
        elif not p.is_file():raise ValueError('Archivo inválido: '+str(p))
    return paths

def remove(d,choices,expected):
    actual=plan(d,choices)
    if actual!=expected:raise ValueError('Las rutas cambiaron; revisa nuevamente')
    removed=[]
    for kind,p in actual:
        try:
            if kind=='dir':shutil.rmtree(p)
            else:p.unlink()
            removed.append(str(p))
        except OSError as e:
            raise RuntimeError('Eliminación interrumpida. Recursos eliminados: '+', '.join(removed)+'; error: '+str(e)) from e
    return removed

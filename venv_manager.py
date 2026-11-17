#!/usr/bin/env python3
"""Portable project virtual environment launcher (Python 3.8+)."""
# Autor: Aldo Machado
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import dependencies
import pvt_storage as storage

WINDOWS = os.name == 'nt'
PROJECT = Path.cwd().resolve()
HOME = Path.home()

def xdg(var, default):
    value = os.environ.get(var)
    return Path(value) if value and Path(value).is_absolute() else default

LOCALAPP = Path(os.environ.get('LOCALAPPDATA', str(HOME / 'AppData' / 'Local')))
STATE = (LOCALAPP if WINDOWS else xdg('XDG_CONFIG_HOME', HOME / '.config')) / 'python-venv-tools'
BASE = storage.root() / 'projects'
CACHE = BASE / 'pycache' if WINDOWS else xdg('XDG_CACHE_HOME', HOME / '.cache') / 'python'
KEY = os.path.normcase(str(PROJECT))
ID = hashlib.sha256(KEY.encode('utf-8')).hexdigest()[:24]
CONFIG = STATE / (ID + '.json')


def fail(message):
    raise RuntimeError(message)


def absolute(value):
    return Path(os.path.expandvars(str(value))).expanduser().resolve()


def load():
    return storage.load(PROJECT)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        os.replace(str(tmp), str(path))
    finally:
        if tmp.exists():
            tmp.unlink()


def options(mode, argv):
    p = argparse.ArgumentParser(prog=('setup_venv' if mode == 'setup' else 'run') + ('.bat' if WINDOWS else '.sh'), allow_abbrev=False)
    p.add_argument('--name', help='Nombre del proyecto (por defecto, nombre de la carpeta)')
    p.add_argument('--path', help='Carpeta base de entornos externos')
    loc = p.add_mutually_exclusive_group()
    loc.add_argument('--local', dest='local', action='store_true')
    loc.add_argument('--external', dest='local', action='store_false')
    p.set_defaults(local=None)
    p.add_argument('--python', help='Version o ejecutable de Python (setup; run comprueba la version configurada)')
    p.add_argument('--cache-path', help='Carpeta base de cache externa')
    c = p.add_mutually_exclusive_group()
    c.add_argument('--no-cache', dest='no_cache', action='store_true')
    c.add_argument('--cache', dest='no_cache', action='store_false')
    p.set_defaults(no_cache=None)
    p.add_argument('--verbose', action='store_true')
    p.add_argument('--engine', choices=('pip','uv'), help='Motor de instalación de requirements')
    if mode == 'setup':
        p.add_argument('--no-requirements', action='store_true', help='Omitir la instalacion de requirements.txt')
        p.add_argument('--no-upgrade-pip', action='store_true', help='Omitir la actualizacion de pip')
    if mode == 'requirements':
        g = p.add_mutually_exclusive_group(required=True)
        for flag in ('scan','install','upgrade','freeze','compare','check-env'):
            g.add_argument('--'+flag, action='store_true')
        p.add_argument('--json', action='store_true', help='Salida JSON para scan/compare')
        p.add_argument('--output', help='Archivo nuevo para freeze; no sobrescribe')
    if mode in ('run', 'launcher'):
        p.add_argument('--entry', help='Archivo Python a ejecutar (main.py por defecto)')
        p.add_argument('--check', action='store_true', help='Verificar aislamiento y dependencias antes de ejecutar')
    return p.parse_args(argv)


def settings(a, old):
    d = dict(project=KEY, name=PROJECT.name, base=str(BASE), local=False, python=None, cache_base=str(CACHE), no_cache=False, engine="pip", custom_cache=False)
    d.update(old)
    for k, v in [('name', a.name), ('base', a.path), ('local', a.local), ('python', a.python), ('cache_base', a.cache_path), ('no_cache', a.no_cache), ('engine', a.engine)]:
        if v is not None:
            d[k] = v
    if a.cache_path is not None:d['custom_cache']=True
    name = d['name']
    if not name or name in ('.', '..') or re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or name.endswith(('.', ' ')):
        fail('Nombre de proyecto no valido: ' + repr(name))
    if name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}:
        fail('Nombre de proyecto reservado: ' + name)
    d['base'] = str(absolute(d['base']))
    d['cache_base'] = str(absolute(d['cache_base']))
    if not d.get('custom_cache'):d['cache_base']=str(storage.folder(d)/'pycache')
    return d


def environment(d, cache):
    env = os.environ.copy()
    for k in list(env):
        if k.upper().startswith(('PYTHON', 'PIP_')) or k.upper() in ('VIRTUAL_ENV', 'VIRTUAL_ENV_PROMPT', '__PYVENV_LAUNCHER__'):
            env.pop(k, None)
    env['PYTHONNOUSERSITE'] = '1'
    env['PYTHONPYCACHEPREFIX'] = str(cache)
    if d['no_cache']:
        env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def call(args, env, **kwargs):
    return subprocess.run([str(x) for x in args], env=env, cwd=str(PROJECT), **kwargs)


def required(args, env):
    result = call(args, env)
    if result.returncode:
        fail('Comando fallo (codigo {}): {}'.format(result.returncode, args[0]))


def interpreter(selection):
    if not selection:
        if not getattr(sys, 'frozen', False):
            return [sys.executable]
        if WINDOWS and shutil.which('py'):
            return ['py','-3']
        for name in ('python3','python'):
            candidate=shutil.which(name)
            if candidate: return [candidate]
        fail('No se encontró Python instalado. Instala Python o usa --python RUTA.')
    if re.fullmatch(r'\d+(?:\.\d+){0,2}', selection):
        if WINDOWS and shutil.which('py'):
            return ['py', '-' + selection]
        candidate = shutil.which('python' + selection)
        if candidate:
            return [candidate]
        if not getattr(sys,'frozen',False) and '.'.join(map(str, sys.version_info[:len(selection.split('.'))])) == selection:
            return [sys.executable]
        fail('No se encontro Python ' + selection)
    candidate = shutil.which(selection) or (str(absolute(selection)) if absolute(selection).is_file() else None)
    if not candidate:
        fail('No se encontro el interprete: ' + selection)
    return [candidate]


def version(command, env):
    r = call(command + ['-I', '-B', '-c', 'import sys; print(".".join(map(str,sys.version_info[:3])))'], env, stdout=subprocess.PIPE, text=True)
    if r.returncode:
        fail('No se pudo consultar la version de Python')
    return r.stdout.strip()


def verify(python, venv, env):
    code = ('import sys, os, site, pip; from pathlib import Path; '
            'p=Path(sys.prefix).resolve(); expected=Path(sys.argv[1]).resolve(); '
            'cfg=(p/"pyvenv.cfg").read_text(encoding="utf-8"); '
            'assert p==expected and sys.prefix!=sys.base_prefix and not site.ENABLE_USER_SITE, "venv no aislado"; '
            'assert any(x.strip().lower().replace(" ","")=="include-system-site-packages=false" for x in cfg.splitlines()), "system-site-packages habilitado"; '
            'assert os.path.commonpath([str(p),str(Path(pip.__file__).resolve())])==str(p), "pip externo"')
    required([python, '-I', '-B', '-c', code, venv], env)


def generate_launcher(d, venv, python, cache, entry):
    import shlex
    if WINDOWS:
        target = PROJECT / 'run_project.bat'
        def q(x):
            return str(x).replace('%', '%%')
        lines = ['@echo off', 'setlocal DisableDelayedExpansion', 'cd /d "%~dp0"',
                 'set "PYTHONHOME="', 'set "PYTHONPATH="', 'set "PYTHONNOUSERSITE=1"',
                 'set "PYTHONPYCACHEPREFIX=' + q(cache) + '"',
                 'set "PYTHONDONTWRITEBYTECODE=' + ('1' if d['no_cache'] else '') + '"',
                 'set "VIRTUAL_ENV=' + q(venv) + '"', 'set "PATH=' + q(python.parent) + ';%PATH%"',
                 '"' + q(python) + '" "' + q(entry) + '" %*', 'exit /b %errorlevel%']
    else:
        target = PROJECT / 'run_project.sh'
        lines = ['#!/usr/bin/env bash', 'cd -- "$(dirname -- "$0")" || exit 1',
                 'unset PYTHONHOME PYTHONPATH PYTHONDONTWRITEBYTECODE', 'export PYTHONNOUSERSITE=1',
                 'export PYTHONPYCACHEPREFIX=' + shlex.quote(str(cache)),
                 'export VIRTUAL_ENV=' + shlex.quote(str(venv)),
                 'export PATH=' + shlex.quote(str(python.parent)) + ':"$PATH"']
        if d['no_cache']: lines.append('export PYTHONDONTWRITEBYTECODE=1')
        lines.append('exec ' + shlex.quote(str(python)) + ' ' + shlex.quote(str(entry)) + ' "$@"')
    if target.exists():
        fail('El lanzador ya existe: ' + str(target) + '. Renombralo antes de generar otro.')
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if not WINDOWS: target.chmod(0o755)
    print('Lanzador creado:', target)


def install_command(d,python,req,upgrade=False):
    if d.get('engine')=='uv':
        uv=shutil.which('uv')
        if not uv: fail('uv no está instalado o no está en PATH.')
        return [uv,'--no-config','pip','install','--python',python]+(['--upgrade'] if upgrade else [])+['-r',req]
    return [python,'-m','pip','--require-virtualenv','--isolated','install','--no-compile']+(['--upgrade'] if upgrade else [])+['-r',req]

def captured(args,env):
    r=call(args,env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace')
    if r.returncode: fail(r.stderr.strip() or 'Error consultando Python')
    return r.stdout

def requirements(a,d,venv,python,env,marker):
    env['PIP_CONFIG_FILE']=os.devnull
    env['PYTHONUTF8']='1'
    req=PROJECT/'requirements.txt'
    if a.scan:
        command=[python] if python.is_file() else interpreter(d['python'])
        if python.is_file(): verify(python,venv,env)
        metadata=json.loads(captured(command+['-I','-B','-c',dependencies.METADATA_CODE],env))
        result=dependencies.scan(PROJECT,metadata['stdlib'],metadata['installed'],[venv])
        if a.json: print(json.dumps(result,ensure_ascii=True))
        else:
            for item in result['dependencies']: print(item['package']+'  # '+item['module']+' ('+item['source']+')')
            for warning in result['warnings']: print('[AVISO] '+warning,file=sys.stderr)
        return 0
    if not python.is_file() or not marker.is_file(): fail('Primero ejecuta setup_venv para registrar el entorno.')
    verify(python,venv,env)
    pip=[python,'-m','pip','--require-virtualenv','--isolated']
    if a.check_env:
        required(pip+['check'],env)
        return 0
    if a.freeze:
        out=captured(pip+['freeze'],env)
        if a.output:
            with absolute(a.output).open('x',encoding='utf-8') as f: f.write(out)
        else: print(out,end='')
        return 0
    if not req.is_file(): fail('No existe requirements.txt. Créalo o escanea el proyecto.')
    if a.compare:
        data=json.loads(captured([python,'-I','-B','-c',dependencies.COMPARE_CODE,req],env))
        if a.json: print(json.dumps(data,ensure_ascii=True))
        else:
            for line,v,status in data['requirements']: print(f'{line} | {v or "—"} | {status}')
            print('Otros paquetes (incluye dependencias indirectas): '+', '.join(data['additional']))
        return 0
    required(install_command(d,python,req,a.upgrade),env)
    required(pip+['check'],env)
    return 0


def main():
    if sys.argv[1:]==['--version']:
        print('Venv Tool 1.3.0-alpha.1'); return 0
    if len(sys.argv)<2 or sys.argv[1] not in ("setup","run","launcher","requirements"):
        print("Uso: venv_cli {setup|run|launcher|requirements} --help")
        return 0 if len(sys.argv)<2 or sys.argv[1]=="--help" else 2
    mode = sys.argv[1]
    argv = sys.argv[2:]
    extra = []
    if '--' in argv:
        pos = argv.index('--')
        argv, extra = argv[:pos], argv[pos+1:]
        if mode not in ('run', 'launcher'):
            fail('Los argumentos despues de -- son solo para run')
    a = options(mode, argv)
    d = settings(a, load())
    venv = PROJECT / ('venv' if WINDOWS else '.venv') if d['local'] else Path(d['base']) / d['name'] / 'venv'
    venv = venv.resolve()
    cache = storage.cache_path(d)
    python = venv / ('Scripts/python.exe' if WINDOWS else 'bin/python')
    marker = venv / '.project-owner.json'
    env = environment(d, cache)
    env['PIP_CACHE_DIR']=str(storage.root()/'cache'/'pip')
    env['UV_CACHE_DIR']=str(storage.root()/'cache'/'uv')
    conf=storage.config_path(d)
    if conf.is_file() and storage.read(conf).get('project')!=KEY:fail('La carpeta administrada pertenece a otro proyecto.')
    if marker.exists():
        if json.loads(marker.read_text(encoding='utf-8')).get('project') != KEY:
            fail('El entorno pertenece a otro proyecto. Usa --name o --path distintos.')
    elif venv.exists() and not d['local']:
        fail('Entorno externo existente sin identificador de propietario. Usa otro --name o --path, o mueve el entorno anterior manualmente.')
    if a.verbose or mode == 'setup':
        print('Proyecto:', PROJECT, '\nEntorno:', venv, '\nCache:', 'sin escritura' if d['no_cache'] else cache, '\nConfiguracion:', storage.config_path(d), flush=True)
    if mode == 'requirements':
        return requirements(a,d,venv,python,env,marker)
    if mode == 'setup':
        req = PROJECT / 'requirements.txt'
        if d['engine']=='uv' and not shutil.which('uv') and req.is_file() and not a.no_requirements:
            fail('uv no está instalado o no está en PATH.')
        if not python.is_file():
            if venv.exists():
                fail('Entorno incompleto. Conserva o mueve esa carpeta antes de recrearlo.')
            command = interpreter(d['python'])
            actual = version(command, env)
            if tuple(map(int, actual.split('.')[:2])) < (3, 8):
                fail('Se requiere Python 3.8 o posterior')
            venv.parent.mkdir(parents=True, exist_ok=True)
            # Claim the destination before creating its contents.
            venv.mkdir()
            write_json(marker, {'project': KEY})
            required(command + ['-m', 'venv', str(venv)], env)
        verify(python, venv, env)
        if d['python']:
            expected = version(interpreter(d['python']), env)
            if version([python], env) != expected:
                fail('El entorno existente usa otra version de Python. Usa otro nombre/ruta o recrealo manualmente.')
        # Ignore global pip configuration and require an actual virtual environment.
        env['PIP_CONFIG_FILE'] = os.devnull
        pip = [python, '-m', 'pip', '--require-virtualenv', '--isolated']
        if not a.no_upgrade_pip:
            required(pip + ['install', '--upgrade', '--no-compile', 'pip'], env)
        else:
            print('Actualizacion de pip omitida.')
        if a.no_requirements:
            print('Instalacion de requirements.txt omitida por parametro.')
        elif req.is_file():
            required(install_command(d,python,req), env)
        elif req.exists():
            fail('requirements.txt existe pero no es un archivo regular.')
        else:
            print('[AVISO] No se encontro requirements.txt. Se conserva el entorno sin instalar dependencias.')
        required(pip + ['check'], env)
        if not marker.exists():
            write_json(marker, {'project': KEY})
        d=storage.save(d)
        storage.snapshot(d, captured(pip+['freeze'],env))
        print('Entorno configurado correctamente.')
        return 0
    if not python.is_file():
        fail('No se encontro el interprete. Ejecuta setup_venv primero.')
    if a.python and version([python], env) != version(interpreter(a.python), env):
        fail('El entorno usa otra version de Python. Utiliza setup_venv --python con otro nombre o ruta.')
    entry = absolute(a.entry or (PROJECT / 'main.py'))
    if not entry.is_file():
        fail('No se encontro el archivo: ' + str(entry))
    if mode == 'launcher':
        generate_launcher(d, venv, python, cache, entry)
        return 0
    if a.check:
        verify(python, venv, env)
        required([python, '-m', 'pip', '--require-virtualenv', 'check'], env)
    env['VIRTUAL_ENV'] = str(venv)
    env['PATH'] = str(python.parent) + os.pathsep + env.get('PATH', '')
    command = [str(python), str(entry)] + extra
    if not WINDOWS:
        os.execve(str(python), command, env)
    return call(command, env).returncode


if __name__ == '__main__':
    os.chdir(str(PROJECT))
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError) as e:
        print('[ERROR]', e, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)

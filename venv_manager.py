#!/usr/bin/env python3
"""Portable project virtual environment launcher (Python 3.8+)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

WINDOWS = os.name == 'nt'
PROJECT = Path(__file__).resolve().parent
HOME = Path.home()

def xdg(var, default):
    value = os.environ.get(var)
    return Path(value) if value and Path(value).is_absolute() else default

LOCALAPP = Path(os.environ.get('LOCALAPPDATA', str(HOME / 'AppData' / 'Local')))
STATE = (LOCALAPP if WINDOWS else xdg('XDG_CONFIG_HOME', HOME / '.config')) / 'python-venv-tools'
BASE = Path(r'C:\venvs') if WINDOWS else xdg('XDG_DATA_HOME', HOME / '.local/share') / 'venvs'
CACHE = BASE / 'pycache' if WINDOWS else xdg('XDG_CACHE_HOME', HOME / '.cache') / 'python'
KEY = os.path.normcase(str(PROJECT))
ID = hashlib.sha256(KEY.encode('utf-8')).hexdigest()[:24]
CONFIG = STATE / (ID + '.json')


def fail(message):
    raise RuntimeError(message)


def absolute(value):
    return Path(os.path.expandvars(str(value))).expanduser().resolve()


def load():
    if not CONFIG.exists():
        return {}
    data = json.loads(CONFIG.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('project') != KEY:
        fail('Configuracion invalida: ' + str(CONFIG))
    return data


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
    if mode == 'run':
        p.add_argument('--entry', help='Archivo Python a ejecutar (main.py por defecto)')
        p.add_argument('--check', action='store_true', help='Verificar aislamiento y dependencias antes de ejecutar')
    return p.parse_args(argv)


def settings(a, old):
    d = dict(project=KEY, name=PROJECT.name, base=str(BASE), local=False, python=None, cache_base=str(CACHE), no_cache=False)
    d.update(old)
    for k, v in [('name', a.name), ('base', a.path), ('local', a.local), ('python', a.python), ('cache_base', a.cache_path), ('no_cache', a.no_cache)]:
        if v is not None:
            d[k] = v
    name = d['name']
    if not name or name in ('.', '..') or re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or name.endswith(('.', ' ')):
        fail('Nombre de proyecto no valido: ' + repr(name))
    if name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}:
        fail('Nombre de proyecto reservado: ' + name)
    d['base'] = str(absolute(d['base']))
    d['cache_base'] = str(absolute(d['cache_base']))
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
        return [sys.executable]
    if re.fullmatch(r'\d+(?:\.\d+){0,2}', selection):
        if WINDOWS and shutil.which('py'):
            return ['py', '-' + selection]
        candidate = shutil.which('python' + selection)
        if candidate:
            return [candidate]
        if '.'.join(map(str, sys.version_info[:len(selection.split('.'))])) == selection:
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


def main():
    mode = sys.argv[1]
    argv = sys.argv[2:]
    extra = []
    if '--' in argv:
        pos = argv.index('--')
        argv, extra = argv[:pos], argv[pos+1:]
        if mode != 'run':
            fail('Los argumentos despues de -- son solo para run')
    a = options(mode, argv)
    d = settings(a, load())
    venv = PROJECT / ('venv' if WINDOWS else '.venv') if d['local'] else Path(d['base']) / d['name'] / 'venv'
    venv = venv.resolve()
    cache = Path(d['cache_base']) / d['name'] / ID / ('py' + d['python'] if d['python'] and re.fullmatch(r'\d+(?:\.\d+){0,2}', d['python']) else 'default')
    python = venv / ('Scripts/python.exe' if WINDOWS else 'bin/python')
    marker = venv / '.project-owner.json'
    env = environment(d, cache)
    if marker.exists():
        if json.loads(marker.read_text(encoding='utf-8')).get('project') != KEY:
            fail('El entorno pertenece a otro proyecto. Usa --name o --path distintos.')
    elif venv.exists() and not d['local']:
        fail('Entorno externo existente sin identificador de propietario. Usa otro --name o --path, o mueve el entorno anterior manualmente.')
    if a.verbose or mode == 'setup':
        print('Proyecto:', PROJECT, '\nEntorno:', venv, '\nCache:', 'sin escritura' if d['no_cache'] else cache, '\nConfiguracion:', CONFIG, flush=True)
    if mode == 'setup':
        req = PROJECT / 'requirements.txt'
        if not req.is_file():
            fail('No se encontro requirements.txt')
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
        required(pip + ['install', '--upgrade', '--no-compile', 'pip'], env)
        required(pip + ['install', '--no-compile', '-r', req], env)
        required(pip + ['check'], env)
        if not marker.exists():
            write_json(marker, {'project': KEY})
        write_json(CONFIG, d)
        print('Entorno configurado correctamente.')
        return 0
    if not python.is_file():
        fail('No se encontro el interprete. Ejecuta setup_venv primero.')
    if a.python and version([python], env) != version(interpreter(a.python), env):
        fail('El entorno usa otra version de Python. Utiliza setup_venv --python con otro nombre o ruta.')
    entry = absolute(a.entry or (PROJECT / 'main.py'))
    if not entry.is_file():
        fail('No se encontro el archivo: ' + str(entry))
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

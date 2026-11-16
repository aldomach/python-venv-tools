# Autor: Aldo Machado
# Two executables sharing one onedir distribution.
a = Analysis(['venv_manager.py'], pathex=[], binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
b = Analysis(['venv_gui.py'], pathex=[], binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
cli = EXE(PYZ(a.pure), a.scripts, [], exclude_binaries=True, name='venv_cli', console=True, icon='app.ico', version='version_info.txt')
gui = EXE(PYZ(b.pure), b.scripts, [], exclude_binaries=True, name='VenvTools', console=False, icon='app.ico', version='version_info.txt')
coll = COLLECT(cli, gui, a.binaries, b.binaries, a.datas, b.datas, strip=False, upx=False, name='VenvTools')

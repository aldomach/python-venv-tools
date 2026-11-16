#!/usr/bin/env bash
set -eu
src=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
dest="${XDG_DATA_HOME:-$HOME/.local/share}/python-venv-tools"
bin="$HOME/.local/bin"
mkdir -p "$dest" "$bin"
for name in setup_venv venv_run venv_launcher venv_requirements venv_gui; do
 if [[ -e "$bin/$name" && ! -L "$bin/$name" ]] || [[ -L "$bin/$name" && $(readlink "$bin/$name") != "$dest/$name" ]]; then echo "Conflicto: $bin/$name" >&2; exit 1; fi
done
cp "$src/venv_manager.py" "$src/venv_gui.py" "$src/dependencies.py" "$src/README.md" "$dest/"
for name in setup_venv venv_run venv_launcher venv_requirements; do cp "$src/$name.sh" "$dest/$name"; chmod +x "$dest/$name"; ln -sfn "$dest/$name" "$bin/$name"; done
# Use real path for symlinked wrappers.
for pair in 'setup_venv setup' 'venv_run run' 'venv_launcher launcher' 'venv_requirements requirements'; do set -- $pair; printf '#!/usr/bin/env bash\nexec python3 -I -B %q %q "$@"\n' "$dest/venv_manager.py" "$2" > "$dest/$1"; done
printf '#!/usr/bin/env bash\nexec python3 -B %q "$@"\n' "$dest/venv_gui.py" > "$dest/venv_gui"; chmod +x "$dest/venv_gui"; ln -sfn "$dest/venv_gui" "$bin/venv_gui"
echo "Instalado en $dest. Verifica que $bin esté en PATH."

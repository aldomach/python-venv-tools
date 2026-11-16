#!/usr/bin/env bash
exec python3 -B "$(dirname -- "${BASH_SOURCE[0]}")/venv_gui.py" "$@"

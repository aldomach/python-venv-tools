#!/usr/bin/env bash
exec python3 -I -B "$(dirname -- "${BASH_SOURCE[0]}")/venv_manager.py" launcher "$@"

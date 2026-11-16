#!/usr/bin/env bash
base=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 -I -B "$base/venv_manager.py" requirements "$@"

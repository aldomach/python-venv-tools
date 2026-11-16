# Python Venv Tools

[Español](README.es.md)

A centralized Python virtual environment, dependency and project management tool for Windows and Linux, with a Tkinter GUI, command-line tools and standalone launchers. Designed to keep environments and bytecode caches outside synchronized project folders.

## Features

- External environments by default; local environments are optional.
- Per-machine project settings, external bytecode cache and direct application execution.
- Optional `requirements.txt`, dependency editor, static import scanner and dependency comparison.
- Install and upgrade dependencies with pip or optional uv; export installed versions and standalone BAT/SH launchers.
- Windows build scripts for PyInstaller and NSIS; source installation on Linux.

## Windows

From the source folder, run `build_all.bat` with Python (including Tkinter), NSIS and access to the package index available. The build creates an installer and portable archive under `release/`. The default installation directory is `C:\Programs\venv-tools`; environments default to `C:\venvs`. Write permissions may be required. A separate installed Python interpreter is needed to create environments.

## Linux

Install Python 3, venv and Tkinter. Run `bash install.sh` and ensure `~/.local/bin` is in PATH. On Debian/Ubuntu the packages are `python3`, `python3-venv` and `python3-tk`.

## Usage

Run from the project directory:

```text
setup_venv
venv_run
venv_gui
venv_launcher
venv_requirements --scan
venv_requirements --install
venv_requirements --upgrade
venv_requirements --compare
venv_requirements --freeze
```

Use `setup_venv --local` for a local environment or `setup_venv --no-requirements --no-upgrade-pip` to create a clean environment without package downloads. See `--help` for additional options and the [Spanish documentation](README.es.md) for complete instructions.

## Development

- [Project overview](docs/PROJECT_MASTER.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Windows build](docs/BUILD_WINDOWS.md)
- [Testing](docs/TESTING.md)
- [Changelog](CHANGELOG.md)

The source history was reconstructed from archived snapshots; commit dates record the reconstruction, not the original development dates. The Windows binaries are not included in this repository; native validation is still required.

Author: Aldo Machado.

### Dependency manager (1.2.2)

Editing, scanning and environment operations are separated. Only explicit Save writes requirements.txt; existing contents are backed up under the local configuration directory (`requirements-backups`) before replacement. Install/upgrade use the saved file, and scanning only proposes additions to the editor. Lock exports never overwrite existing files. Use `venv_requirements --check-env` for read-only package verification.

# Archyter Studio

**Archyter Studio** is the Windows edition of the Archyter notebook IDE. It is built around JupyterLab but presents its own desktop shell: project explorer, notebook workspace, kernel inspector, variables, terminal, recent projects and Windows-native installation.

> Development branch: `windows-studio`

## Target

The Windows interface follows the approved Archyter Studio concept:

- white/light-blue desktop UI;
- left navigation rail;
- project explorer with reliable local icons;
- notebook-first center workspace;
- kernel + variables + PowerShell inspector;
- explicit save/run/project controls;
- safe deletion through the Windows Recycle Bin;
- recent projects;
- local Jupyter bound to `127.0.0.1`.

The visual and behavioural contract is documented in `docs/WINDOWS_DESIGN_CONTRACT.md`.

## Requirements

- Windows 10 or Windows 11;
- Python 3.11+;
- internet access during the first dependency installation.

## Test from source

Open PowerShell:

```powershell
git clone --branch windows-studio https://github.com/alviomedina100041-prog/archyter-desktop.git Archyter-Studio
cd Archyter-Studio

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-windows.txt

python -m studio.main
```

If PowerShell blocks environment activation, activation is optional:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
.\.venv\Scripts\python.exe -m studio.main
```

## Install in Windows

From the repository:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows.ps1
```

The installer creates a private application environment under:

```text
%LOCALAPPDATA%\ArchyterStudio
```

and registers **Archyter Studio** in the Windows Start menu.

Uninstall:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\uninstall_windows.ps1
```

## Quality gates

Every push to `windows-studio` is validated on a real GitHub Actions Windows runner. The workflow:

1. installs the Windows dependencies;
2. compiles the Studio sources;
3. starts a real JupyterLab server and creates a notebook in a nested project folder;
4. validates explorer selection, icons and delete signalling;
5. starts the detected Windows shell and runs a command;
6. instantiates the full Qt/WebEngine Studio window and checks the approved panel proportions;
7. renders a 1480×900 smoke screenshot and uploads it as a workflow artifact.

This does not mean desktop software can never contain a bug, but changes are not considered healthy until the Windows CI passes.

## Linux edition

The original Archyter Desktop for Arch Linux remains on the `main` branch.

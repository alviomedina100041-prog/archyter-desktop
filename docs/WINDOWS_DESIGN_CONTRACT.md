# Archyter Studio — Windows design contract

This branch implements the approved Windows concept for Archyter Studio.

## Fixed visual structure

At the target desktop size, roughly 1366×768 through 1920×1080, the application keeps these stable areas:

1. Top command bar — Archyter mark, Nuevo, Guardar, Ejecutar, Kernel, Terminal, Proyecto, search and settings.
2. Navigation rail — compact vertical icon rail.
3. Project explorer — files, notebooks, delete action and recent projects.
4. Notebook editor — a dedicated document bar plus the embedded Jupyter notebook surface.
5. Inspector — kernel card, variables and terminal.
6. Bottom status bar — kernel, save state, encoding, Jupyter and active path.

## Visual rules

- Light Windows-native surface.
- Blue is reserved for primary actions, active documents and selection.
- Rounded cards and subtle borders; no heavy shadows.
- Explicit local SVG icons are used instead of relying on the Windows icon theme.
- The notebook remains the visual center and must always receive the most horizontal space.
- Explorer target width: 235–315 px.
- Inspector target width: 290–360 px.
- Primary test window: 1480×900.
- Minimum supported shell window: 1120×700.

## Behavioural rules

- New notebooks are created in the selected folder.
- File deletion always asks for confirmation and uses the Windows Recycle Bin.
- The active notebook is shown in both explorer and document bar.
- Jupyter binds only to 127.0.0.1 with a random token.
- PowerShell 7 is preferred, then Windows PowerShell, then Command Prompt.
- Recent projects persist per Windows user.
- The Windows branch is tested on windows-latest before being considered usable.

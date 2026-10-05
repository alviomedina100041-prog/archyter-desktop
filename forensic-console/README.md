# BlackArch Forensic Console

Functional DFIR desktop workspace for Windows 11 with a real Arch/BlackArch WSL2 terminal.

## Architecture

```text
forensic-console/
├─ apps/
│  └─ desktop/
│     ├─ src/                  React + TypeScript + xterm.js + Lucide
│     └─ src-tauri/            Tauri 2 shell + Rust PTY bridge
├─ crates/
│  └─ forensic-core/           Cases, evidence hashing, custody, WSL discovery
├─ docs/
│  └─ METHODOLOGY.md
└─ Cargo.toml                  Rust workspace
```

The center terminal is not a mock terminal. It is an xterm.js terminal connected through Tauri to a Windows ConPTY session created with `portable-pty`, running:

```text
wsl.exe -d archlinux --cd ~ -- env TERM=xterm-256color COLORTERM=truecolor bash -l
```

Keyboard input is written back to the PTY, output is streamed as Tauri events, and terminal resizing is forwarded to the PTY.

## Implemented functionality

- Real interactive Arch/BlackArch WSL2 terminal.
- ANSI colors, cursor, history, Ctrl+C and interactive CLI support through xterm.js.
- WSL environment probe: user, kernel, home, and installed `blackarch-forensic` package count.
- BlackArch forensic tool discovery from the real WSL package database.
- Send a selected forensic tool's `--help` command into the live terminal.
- Create persistent local forensic cases.
- Register evidence by reference without modifying or copying the source.
- Streaming SHA-256 hashing in Rust.
- Re-verify evidence integrity at any time.
- Persist case timeline / chain-of-custody events.
- Real Windows file-system explorer using Rust.
- Native Tauri file/folder picker.
- Responsive three-column DFIR layout.
- Lucide icon system and CSS motion instead of hand-drawn placeholder icons.
- No fake findings, fake hashes, fake CPU values, or fake evidence metadata.

## Requirements

Windows 11:

- WSL2
- distro named `archlinux` by default
- BlackArch forensic group installed
- Rust stable MSVC toolchain
- Visual Studio Build Tools C++
- Node.js 20+
- WebView2 (included with current Windows 11)

## Run

```powershell
git clone --branch feature/blackarch-forensic-tauri https://github.com/alviomedina100041-prog/archyter-desktop.git
cd archyter-desktop\forensic-console
npm install
npm run dev
```

For frontend-only validation:

```powershell
npm run frontend:build
```

Rust core tests:

```powershell
cargo test -p forensic-core
```

## Forensic behavior

Evidence registration is intentionally non-destructive. The application stores the original path, file size and SHA-256. It does not edit the evidence source. Re-verification hashes the current source again and records either a successful verification or an integrity mismatch in the case timeline.

The case store is maintained below the current user's local application data directory under the BlackArch Forensic Console project directory.

## Current milestone

This branch is Milestone 1: a working shell and evidence foundation. Memory acquisition/analysis, PCAP workflows, PostgreSQL defensive audit, hex viewer and report generation should be implemented as independent vertical slices only after they pass their own Definition of Done in `docs/METHODOLOGY.md`.

<div align="center">

# BlackArch Forensic Console

### Functional DFIR workspace · Tauri 2 + Rust + React + xterm.js + WSL2

**This branch replaces the static egui prototype with a real terminal, persistent forensic cases, evidence hashing and a responsive desktop UI.**

![Tauri](https://img.shields.io/badge/Desktop-Tauri%202-24C8DB)
![Rust](https://img.shields.io/badge/Backend-Rust-000000?logo=rust&logoColor=white)
![React](https://img.shields.io/badge/UI-React%20%2B%20TypeScript-61DAFB?logo=react&logoColor=111)
![WSL2](https://img.shields.io/badge/Terminal-Arch%2FBlackArch%20WSL2-13ec9a)
![DFIR](https://img.shields.io/badge/Focus-DFIR-ff5f73)

</div>

> **Branch:** `feature/blackarch-forensic-tauri`

## Why this branch exists

The previous Rust/egui experiment proved the visual direction but behaved like a mockup. This branch changes the architecture around a strict rule: **nothing operational is displayed unless it comes from a real backend operation.**

The implementation is a monorepo in:

```text
forensic-console/
```

## Working vertical slice

- interactive xterm.js terminal in the center;
- real Windows PTY through `portable-pty`;
- terminal process is `wsl.exe -d archlinux ... bash -l`;
- real stdin/stdout, ANSI colors, cursor and resize;
- persistent forensic cases;
- real SHA-256 streaming in Rust;
- evidence integrity re-verification;
- persistent chain-of-custody events;
- real file-system explorer;
- real BlackArch forensic tool discovery;
- responsive UI with Lucide icons and non-blocking CSS motion.

No fake hashes, fake findings, fake CPU values or fake evidence files are used.

## Run

```powershell
git clone --branch feature/blackarch-forensic-tauri https://github.com/alviomedina100041-prog/archyter-desktop.git
cd archyter-desktop\forensic-console

npm install
npm run dev
```

For the complete architecture, requirements and current milestone see:

- `forensic-console/README.md`
- `forensic-console/docs/METHODOLOGY.md`

## Development principle

Features are delivered as vertical slices:

```text
UI → typed Tauri command/event → Rust service → Windows/WSL/filesystem → real result → UI
```

A visible button without an end-to-end implementation is not considered a completed feature.

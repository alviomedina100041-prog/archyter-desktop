# BlackArch Forensic Console — Rust prototype

Dedicated staging branch for the forensic console requested from the approved mockup.

- Source package: `blackarch-forensic-console-source.zip`
- Target: Windows 11 + WSL2 + `archlinux`
- UI: native Rust with eframe/egui
- WSL shell execution runs on a background worker thread.
- Release profile enables LTO, one codegen unit, symbol stripping and `panic = abort`.
- Windows CI extracts the source archive and runs fmt, tests, clippy and an optimized release build.

The default `main` branch of Archyter Desktop is untouched; this work lives only on `blackarch-forensic-console`.

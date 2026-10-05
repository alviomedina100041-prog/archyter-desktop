# Arquitectura técnica

## Objetivo

Reproducir la composición del mockup: topbar, navegación, Case Explorer, terminal central, Evidence Details, Findings Summary, Timeline, Hex Preview y PostgreSQL Audit Summary, priorizando baja latencia y RAM.

## Rust + Win32/GDI

La primera versión usa Win32/GDI nativo y no requiere crates de runtime. No incluye navegador, Node, Electron ni WebView. El render se hace con double buffering usando `CreateCompatibleDC` y `BitBlt`.

## Threading

El hilo principal procesa mensajes y pintura. Los comandos WSL, SHA-256, auditoría PostgreSQL y escaneo de proyecto se ejecutan en workers. Los resultados vuelven por `WM_APP + 11`.

## WSL

La distro predeterminada es `archlinux`. El terminal explícito usa `wsl.exe -d archlinux -- bash -lc <command>`. Los servicios automatizados evitan interpolar datos no confiables en shell.

## PostgreSQL

No se guardan passwords. El servicio invoca `psql` con argumentos directos y delega autenticación a libpq/WSL. Las consultas son de metadatos y privilegios.

## Evidencia

Drag & drop registra metadata y calcula SHA-256 en segundo plano. La aplicación no modifica automáticamente la evidencia.

## Escaneo de proyecto

Ignora directorios pesados (`.git`, `node_modules`, `target`, entornos virtuales, `dist`, `build`), limita a 50,000 archivos y 1 MiB leído por archivo, y no imprime secretos.

## Roadmap

1. Casos persistentes.
2. ConPTY para terminal persistente.
3. Hex viewer paginado sobre evidencia real.
4. Timeline real EVTX/MFT/USN.
5. Integraciones Volatility 3, Sleuth Kit, Chainsaw y YARA.
6. Exportación HTML/PDF.
7. MSI/MSIX firmado.

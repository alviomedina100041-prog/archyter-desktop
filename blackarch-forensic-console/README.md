# BlackArch Forensic Console

Aplicación de escritorio nativa para **Windows 11 + WSL2**, escrita en **Rust**, enfocada en DFIR con Arch/BlackArch y diseñada para reproducir el mockup de **BLACKARCH FORENSIC CONSOLE**.

## Incluido en 0.1.0

- UI Win32/GDI oscura y optimizada, sin Electron/WebView.
- Sidebar, Case Explorer, terminal, Evidence Details, Findings, Timeline, Hex Preview y PostgreSQL Audit.
- Integración con la distro WSL `archlinux`.
- Terminal central: ejecuta comandos explícitos dentro de BlackArch WSL2 sin bloquear la UI.
- Drag & drop de evidencia y SHA-256 en worker.
- Drag & drop de carpetas para auditoría defensiva acotada de proyectos.
- Auditoría **read-only** de roles y privilegios PostgreSQL.
- Reporte Markdown por caso.
- Icono propio.
- Runtime sin crates externos: `std` + Win32.

## Requisitos

Windows 11 x64, WSL2, la distro `archlinux`, Rust estable y Visual Studio Build Tools C++ para el target MSVC. Para PostgreSQL, instala `psql` dentro de Arch/BlackArch.

Comprueba WSL:

```powershell
wsl -l -v
```

## Compilar

```powershell
cd .\blackarch-forensic-console
.\scripts\build-windows.ps1
```

Salida:

```text
dist\BlackArchForensicConsole.exe
```

Para instalar toolchain si hace falta, compilar y crear acceso directo:

```powershell
.\scripts\install.ps1 -InstallToolchain
```

## PostgreSQL

La aplicación no persiste contraseñas. Configura destino con:

```powershell
$env:BLACKARCH_PGHOST="127.0.0.1"
$env:BLACKARCH_PGPORT="5433"
$env:BLACKARCH_PGDATABASE="erpcontrol"
$env:BLACKARCH_PGUSER="auditor"
```

Autentica `psql` con `~/.pgpass` dentro de WSL, permisos 600.

La auditoría consulta metadatos para detectar roles privilegiados, tablas concedidas a PUBLIC, grants PUBLIC y esquemas con PUBLIC CREATE. No intenta explotar PostgreSQL.

## Uso

Arrastra un archivo para registrarlo como evidencia y calcular SHA-256. Arrastra una carpeta para escanear de forma defensiva archivos sensibles y patrones de secretos. Usa **Run Audit** para PostgreSQL, **Verify** para rehacer el hash y **Reports** para generar el reporte. El panel WSL abre Windows Terminal con `archlinux`.

## Optimización

El render usa GDI con double buffering. El hilo de UI sólo atiende mensajes/pintura; WSL, hash, PostgreSQL y escaneo usan workers. Release usa `opt-level=3`, Thin LTO, un codegen unit, `panic=abort` y strip.

## Seguridad

Trabaja sobre copias verificadas y, para evidencia real, usa medios/montajes read-only y cadena de custodia. El escáner de proyecto limita cantidad de archivos y bytes por archivo y no imprime valores de secretos detectados.

Consulta `docs/architecture.md` para decisiones y roadmap.

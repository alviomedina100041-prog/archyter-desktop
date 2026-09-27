<div align="center">

<img src="assets/icon.svg" alt="Archyter Desktop" width="96">

# Archyter Desktop

### Jupyter como aplicación de escritorio para Arch Linux

Una interfaz de escritorio ligera construida sobre **PySide6 + Qt WebEngine + JupyterLab**, pensada para trabajar con notebooks sin depender de una ventana normal del navegador.

[![Python syntax](https://github.com/alviomedina100041-prog/archyter-desktop/actions/workflows/syntax.yml/badge.svg)](https://github.com/alviomedina100041-prog/archyter-desktop/actions/workflows/syntax.yml)
![Arch Linux](https://img.shields.io/badge/Arch%20Linux-supported-1793D1?logo=archlinux&logoColor=white)
![JupyterLab](https://img.shields.io/badge/JupyterLab-embedded-F37626?logo=jupyter&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)
![Python](https://img.shields.io/badge/kernel-Python-3776AB?logo=python&logoColor=white)
![Julia](https://img.shields.io/badge/kernel-Julia-9558B2?logo=julia&logoColor=white)

</div>

---

![Archyter Desktop](assets/mockup.svg)

## ¿Qué es Archyter?

**Archyter Desktop** toma la parte sólida de Jupyter —servidor, notebooks, kernels, ejecución de celdas, outputs y compatibilidad con el formato `.ipynb`— y la presenta dentro de una aplicación de escritorio para Linux.

No intenta reescribir Jupyter ni crear un formato propietario.

Tus notebooks siguen siendo notebooks normales y pueden abrirse también en:

- JupyterLab
- Jupyter Notebook
- VS Code
- otras instalaciones compatibles con `.ipynb`

La diferencia está en la experiencia de uso: Archyter elimina la sensación de estar trabajando dentro de Firefox o Chromium y añade una capa de escritorio propia alrededor de Jupyter.

---

## Características principales

### Interfaz de escritorio

- Ventana principal creada con **PySide6 / Qt**.
- JupyterLab embebido mediante **Qt WebEngine**.
- Tema blanco y limpio con acentos azul/cian.
- Explorador de archivos integrado.
- Barra superior con accesos rápidos:
  - Nuevo
  - Guardar
  - Ejecutar
  - Kernel
  - Terminal
  - Ajustes
- Barra de estado inferior.
- Diseño adaptable para pantallas pequeñas.

### Modo compacto 1366 × 780

Archyter detecta automáticamente resoluciones reducidas y activa una interfaz compacta:

- panel izquierdo más estrecho;
- panel derecho compacto;
- notebook central con prioridad de espacio;
- controles y tipografías reducidos;
- Jupyter embebido con zoom adaptado;
- márgenes y barras más delgados.

Este modo fue diseñado específicamente para laptops con pantallas alrededor de **1366 × 780**.

### Kernel y notebooks

Archyter conserva la infraestructura real de Jupyter:

- archivos `.ipynb`;
- ejecución de celdas;
- Markdown;
- outputs HTML;
- DataFrames;
- gráficas;
- kernels instalados en Jupyter.

Se ha probado principalmente con:

- **Python / ipykernel**
- **Julia / IJulia**

Otros kernels visibles para JupyterLab pueden funcionar normalmente, aunque el inspector de variables de Archyter está implementado actualmente para Python y Julia.

### Panel de kernel

El panel derecho muestra información resumida del kernel activo:

- nombre;
- estado;
- tiempo de actividad;
- conexión actual.

Archyter consulta el estado del servidor sin ejecutar código constantemente dentro del kernel.

### Variables

El panel **Variables** permite inspeccionar el estado del kernel bajo demanda.

La actualización es **manual** mediante el botón `↻`, evitando que Archyter cambie continuamente el estado `idle/busy` del kernel.

La vista muestra:

| Campo | Descripción |
|---|---|
| Nombre | Variable disponible |
| Tipo | Tipo de objeto |
| Forma | Shape o longitud cuando aplica |
| Valor | Vista previa del contenido |

También puedes pulsar **Variables ↗** para abrir una ventana grande encima de Archyter y revisar la tabla con más espacio.

### Consola / logs

El panel **Consola / logs** muestra información del servidor Jupyter y de Archyter.

Al pulsar **Consola / logs ↗** se abre una ventana grande con los logs en vivo, sin reducir el tamaño del notebook central.

### Terminal integrada

Archyter incluye una terminal local sencilla basada en `QProcess`.

- ejecuta `/bin/bash`;
- usa el directorio del proyecto como carpeta de trabajo;
- limpia secuencias ANSI para evitar texto ilegible;
- puede abrirse en una ventana grande mediante **Terminal ↗**.

> La terminal integrada está pensada para tareas rápidas y no pretende sustituir emuladores completos como Kitty, Alacritty o Konsole.

---

## Arquitectura

```text
┌──────────────────────────────────────┐
│          Archyter Desktop            │
│          PySide6 / Qt                │
├───────────────┬──────────────────────┤
│ Explorador    │   Qt WebEngine       │
│ Kernel        │         ↓            │
│ Variables     │    JupyterLab        │
│ Logs          │         ↓            │
│ Terminal      │   Jupyter Server     │
└───────────────┴──────────┬───────────┘
                           │
                    Jupyter protocol
                           │
              ┌────────────┴───────────┐
              │                        │
         Python / ipykernel       Julia / IJulia
```

Jupyter sigue haciendo el trabajo complejo del ecosistema de notebooks. Archyter se encarga principalmente de la experiencia de escritorio, integración visual y utilidades adicionales.

---

## Seguridad local

El servidor Jupyter creado por Archyter:

- escucha únicamente en `127.0.0.1`;
- usa un puerto local disponible;
- genera un token nuevo al iniciar;
- no se publica directamente en la red local.

Esto permite utilizar la arquitectura cliente-servidor de Jupyter sin exponer el servidor innecesariamente.

---

# Instalación en Arch Linux

## 1. Clonar el repositorio

```bash
git clone https://github.com/alviomedina100041-prog/archyter-desktop.git
cd archyter-desktop
```

## 2. Ejecutar el instalador

```bash
chmod +x scripts/install_arch.sh
./scripts/install_arch.sh
```

El instalador configura automáticamente:

- dependencias necesarias de Arch;
- entorno virtual privado;
- dependencias Python;
- launcher de escritorio;
- icono de la aplicación;
- comando `archyter`;
- compatibilidad conservadora para GPUs Intel antiguas.

La instalación permanente se guarda por defecto en:

```text
~/.local/share/archyter-desktop
```

El launcher se registra en:

```text
~/.local/share/applications/archyter-desktop.desktop
```

Y se crea el comando:

```text
~/.local/bin/archyter
```

---

## Abrir Archyter

Después de instalarlo puedes buscar:

```text
Archyter Desktop
```

en el menú de aplicaciones de tu escritorio.

El launcher utiliza:

```ini
Terminal=false
```

por lo que Archyter abre directamente como aplicación gráfica **sin levantar una terminal externa**.

También puedes iniciarlo manualmente con:

```bash
archyter
```

o durante desarrollo:

```bash
./scripts/run_archyter.sh
```

---

## Actualizar Archyter

La copia instalada es independiente del repositorio clonado.

Para actualizar:

```bash
cd ~/archyter-desktop
git pull origin main
./scripts/install_arch.sh
```

El instalador reemplaza la versión instalada por la versión nueva del repositorio.

---

## Desinstalar

Si Archyter ya está instalado:

```bash
~/.local/share/archyter-desktop/scripts/uninstall_arch.sh
```

Si todavía estás trabajando desde el clon:

```bash
./scripts/uninstall_arch.sh
```

La desinstalación elimina la aplicación instalada, el launcher y el comando de usuario.

---

## Intel Haswell, gráficos híbridos y VA-API

Archyter incluye un perfil conservador para equipos con Intel Haswell y sistemas de gráficos híbridos.

El launcher configura:

- Qt OpenGL en modo seguro;
- Qt Quick con backend de software;
- Vulkan deshabilitado dentro de Qt WebEngine;
- GPU compositing/rasterization deshabilitados para Chromium;
- aceleración de vídeo de Chromium deshabilitada;
- `LIBVA_DRIVER_NAME=i965` para Intel Haswell y generaciones compatibles.

En Arch Linux, el instalador añade:

```text
mesa
libva
libva-intel-driver
libva-utils
```

Puedes verificar VA-API con:

```bash
LIBVA_DRIVER_NAME=i965 vainfo
```

En equipos con gráficos híbridos Intel + NVIDIA, es normal que distintas aplicaciones utilicen GPUs diferentes. Archyter prioriza estabilidad antes que aceleración gráfica porque un notebook no necesita una GPU dedicada para renderizar su interfaz.

---

## Julia

Julia puede tardar más en la primera ejecución de una sesión debido a la compilación JIT y a la carga inicial de paquetes.

Por ejemplo:

```julia
using DataFrames
using CSV
using Plots
```

puede sentirse más lento la primera vez. Después de compilar y cargar esos componentes, las ejecuciones posteriores suelen responder mucho más rápido.

Archyter no reemplaza ni modifica ese comportamiento: utiliza el kernel real de Julia mediante Jupyter/IJulia.

---

## Estructura del proyecto

```text
archyter-desktop/
├── .github/
│   └── workflows/
│       └── syntax.yml
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── jupyter_manager.py
│   ├── theme.py
│   ├── window.py
│   │
│   └── widgets/
│       ├── __init__.py
│       ├── file_explorer.py
│       ├── kernel_panel.py
│       ├── log_console.py
│       ├── mini_terminal.py
│       └── variables_panel.py
│
├── assets/
│   ├── icon.svg
│   └── mockup.svg
│
├── scripts/
│   ├── archyter-desktop.desktop
│   ├── install_arch.sh
│   ├── run_archyter.sh
│   └── uninstall_arch.sh
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Componentes principales

### `app/main.py`

Punto de entrada de la aplicación.

Configura el entorno gráfico antes de importar Qt y arranca la ventana principal.

### `app/window.py`

Contiene la interfaz principal de Archyter:

- layout general;
- detección de modo compacto;
- integración de los paneles;
- ventanas emergentes;
- comunicación con el gestor de Jupyter.

### `app/jupyter_manager.py`

Gestiona:

- inicio y cierre de JupyterLab;
- puerto local;
- token;
- API de sesiones y kernels;
- creación de notebooks;
- reinicio de kernels;
- inspección manual de variables;
- personalización visual del Jupyter embebido.

### `app/theme.py`

Define el tema Qt utilizado por Archyter.

### `app/widgets/`

Contiene los componentes independientes de la interfaz:

- explorador de archivos;
- panel del kernel;
- variables;
- logs;
- terminal.

---

## Filosofía del proyecto

Archyter sigue tres ideas principales:

### 1. No reinventar Jupyter

El ecosistema Jupyter ya resuelve kernels, notebooks, protocolos, widgets, outputs y compatibilidad con múltiples lenguajes.

Archyter aprovecha esa infraestructura en vez de reemplazarla.

### 2. Mantener archivos estándar

No existe un formato “Archyter Notebook”.

Tus archivos siguen siendo `.ipynb`.

### 3. Mejorar la experiencia local

Archyter está enfocado en usuarios que trabajan principalmente de forma local y prefieren una aplicación de escritorio sobre una pestaña del navegador.

---

## Desarrollo

Para ejecutar directamente desde el repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/run_archyter.sh
```

Para validar rápidamente la sintaxis:

```bash
python -m compileall -q app
```

El repositorio también ejecuta esta validación automáticamente mediante **GitHub Actions** en cada push a `main` y en pull requests.

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python | aplicación principal |
| PySide6 | interfaz de escritorio |
| Qt WebEngine | renderizado de JupyterLab |
| JupyterLab | interfaz y ecosistema notebook |
| Jupyter Server | servidor local |
| websocket-client | comunicación con kernels |
| requests | API local de Jupyter |
| Bash | instalación y launchers |
| Arch Linux | plataforma principal |

---

## Estado actual

Archyter se encuentra en desarrollo activo.

Actualmente ya cuenta con:

- interfaz funcional;
- notebooks reales;
- kernels Python y Julia;
- modo compacto;
- tema blanco;
- explorador;
- panel de kernel;
- inspector manual de variables;
- logs;
- terminal;
- ventanas emergentes;
- instalación permanente;
- launcher gráfico sin consola externa;
- desinstalador;
- validación automática mediante GitHub Actions.

Todavía hay espacio para mejorar aspectos como selección visual de kernels, preferencias persistentes, proyectos recientes, empaquetado nativo y mayor integración con el ecosistema de escritorios Linux.

---

<div align="center">

### Archyter Desktop

**Jupyter por dentro. Aplicación de escritorio por fuera.**

Hecho para experimentar con una experiencia de notebooks más cómoda en Arch Linux.

</div>

<p align="center">
  <img src="assets/media_manager_app_icon.png" alt="Media Manager" width="128"/>
</p>

<h1 align="center">Media Manager</h1>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.fr.md">Français</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ko.md">한국어</a> · <strong>Español</strong>
</p>

<p align="center">
  <a href="https://github.com/HFDWKJ/MediaManager/releases"><img src="https://img.shields.io/github/v/release/HFDWKJ/MediaManager?label=release&logo=github" alt="Release"/></a>
  <a href="https://github.com/HFDWKJ/MediaManager"><img src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows" alt="Windows"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt" alt="PyQt6"/></a>
</p>

<p align="center">
  Aplicación de escritorio para Windows que cataloga medios en varios discos y dispositivos,<br/>
  detecta carpetas duplicadas <code>[Original Name]</code> y reorganiza descargas extraídas.
</p>

<p align="center">
  <b>Versión:</b> 0.0.3 · <b>Desarrollador:</b> Dong, Zhexi
</p>

---

## Índice

- [Funciones](#funciones)
- [Descarga](#descarga)
- [Inicio rápido](#inicio-rápido)
- [Desarrollo con Cursor y Vibe Coding](#desarrollo-con-cursor-y-vibe-coding)
- [Compilación (Nuitka)](#compilación-nuitka)
- [Configuración y rutas de datos](#configuración-y-rutas-de-datos)
- [Actualizaciones de la aplicación](#actualizaciones-de-la-aplicación)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Hoja de ruta y documentación](#hoja-de-ruta-y-documentación)
- [Licencia](#licencia)

---

## Funciones

| Área | Descripción |
|------|-------------|
| **Biblioteca multi-raíz** | Indexación en SSD/HDD, NAS, DAS y USB; el catálogo sigue usable sin conexión |
| **Detección de duplicados** | Nivel 1: coincidencia difusa `[Original Name]` · Nivel 2: SHA-256 con **Verify with Hash** |
| **Reorganizar** | Aplanar carpetas extraídas en `[Collections]` con plantillas, barra de progreso, porcentaje y ETA |
| **Face UID** | IDs únicos cortos con apodo, región y comentarios |
| **Edición portable** | Carpeta `data\` junto al exe para config, base de datos y registros |
| **Auto-actualización** | Comprueba [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) al iniciar |
| **Interfaz** | Tema oscuro inspirado en DiskGenius y cinta estilo Office |

---

## Descarga

Binarios precompilados en **[GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases)**:

| Edición | Archivo |
|---------|---------|
| Instalador | `MediaManagerSetup_0.0.3.exe` |
| Zip portable | `MediaManagerPortal_v0.0.3.zip` |

> [!NOTE]
> **Smart App Control:** los ejecutables sin firmar pueden bloquearse en Windows 11. Desactiva SAC en un PC de prueba o firma el instalador para producción.

---

## Inicio rápido

### Requisitos

- Python 3.10+
- Windows 11 (compatible con Windows 10+)

### Instalación y ejecución

```powershell
git clone https://github.com/HFDWKJ/MediaManager.git
cd MediaManager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_test_data.py   # opcional: carpetas de ejemplo
python src\main.py
```

### Flujo de prueba

1. **Add Library Root** — apunta a `test_data\library` o tu carpeta de descargas.
2. **Discover / Scan** — indexa carpetas de extracción `[Original Name]`.
3. **Review Name Matches** — descartar, marcar como diferente o **Verify with Hash**.
4. **Reorganize ([Collections])** — vista previa de aplanado y renombrado.
5. **Show in Explorer** — abre la carpeta cuando el dispositivo está en línea.

> [!TIP]
> Desde el código fuente, **Download and update** abre la página de Releases en el navegador. Las builds empaquetadas descargan e instalan dentro de la app.

---

## Desarrollo con Cursor y Vibe Coding

Este proyecto es un **ejemplo real de desarrollo asistido por IA** con [Cursor](https://cursor.com) y **Vibe Coding**: describir la intención en lenguaje natural, dejar que el Agent implemente y refinar ejecutando la app y dando feedback.

| Etapa | Enfoque |
|-------|---------|
| **Planificación** | [`media_manager_plan.md`](media_manager_plan.md) — prompts por fases para cada hito |
| **Implementación** | El Agent construyó `core/`, `gui/`, scripts de empaquetado y flujo de release paso a paso |
| **Iteración UI** | Feedback con capturas (cinta, barra de progreso, filtros) |
| **Seguimiento de releases** | [`docs/ROADMAP.md`](docs/ROADMAP.md) + GitHub Issues / Milestones |

**Bucle típico:** Prompt → Agent edita → ejecutar `MediaManager.exe` → captura / error → publicar release.

> Documentación en inglés: **[README.md § Built with Cursor](README.md#built-with-cursor--vibe-coding)**

### Notas prácticas

- Mantener un plan vivo (`media_manager_plan.md`) para contexto estable del Agent entre sesiones.
- Probar builds **empaquetados** Nuitka pronto — la detección en tiempo de ejecución difiere de `python src\main.py`.
- Regla de empaquetado: **solo Nuitka**, sin Inno Setup.
- GitHub Releases públicos simplifican la auto-actualización (sin token).

---

## Compilación (Nuitka)

Los scripts instalan dependencias automáticamente. Nuitka usa MSVC si está disponible, si no MinGW64.

### Aplicación

```powershell
.\scripts\build_nuitka.ps1              # dist\MediaManager\MediaManager.exe
.\scripts\build_nuitka.ps1 -Mode onefile  # dist\MediaManager.exe
```

### Instalador

```powershell
.\scripts\build_installer.ps1
# → dist_installer\MediaManagerSetup_0.0.3.exe
```

Flags silenciosos para actualizaciones in-app: `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/NORESTART`, `/CLOSEAPPLICATIONS`, opcional `/DIR=...`.

### Zip portable

```powershell
.\scripts\build_portal.ps1
# → dist_portal\MediaManagerPortal_v0.0.3.zip
```

---

## Configuración y rutas de datos

**Edición instalada**

| Elemento | Ruta |
|----------|------|
| Config | `%APPDATA%\MediaManager\config.json` |
| Base de datos | `%APPDATA%\MediaManager\catalog.db` |
| Registros | `%APPDATA%\MediaManager\logs\` |

**Edición portable** — `portable.marker` junto a `MediaManager.exe`, o build portal:

| Elemento | Ruta |
|----------|------|
| Config | `data\config.json` |
| Base de datos | `data\catalog.db` |
| Registros | `data\logs\` |

Copia **toda la carpeta** (incluido `data\`) para mover catálogo y ajustes a otro PC.

---

## Actualizaciones de la aplicación

- **Comprobación al inicio** (activada por defecto) y **Options → Check for updates…**
- Desactivar en **Settings → Updates**
- Etiqueta de release `v0.0.3`; las notas aparecen en el diálogo de actualización
- Repos privados: `update.github_token` en config o variable `GITHUB_TOKEN`

---

## Estructura del proyecto

```text
src/
  main.py              Punto de entrada
  core/                Base de datos, escaneo, coincidencias, reorganización, updates
  gui/                 UI PyQt6
  installer/           Asistente de instalación Nuitka
  utils/               Config, registros, rutas
assets/                Icono de la aplicación
scripts/               Scripts de build y utilidades
docs/ROADMAP.md        Lista de hitos
media_manager_plan.md  Plan de desarrollo Cursor por fases
CHANGELOG.md           Notas de release (diálogo About)
```

---

## Hoja de ruta y documentación

| Documento | Descripción |
|-----------|-------------|
| [README.md](README.md) | English |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 |
| [README.ja.md](README.ja.md) | 日本語 |
| [README.fr.md](README.fr.md) | Français |
| [README.de.md](README.de.md) | Deutsch |
| [README.ko.md](README.ko.md) | 한국어 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Planes de versión y checklist v0.0.3 |
| [CHANGELOG.md](CHANGELOG.md) | Historial de releases |
| [GitHub Milestones](https://github.com/HFDWKJ/MediaManager/milestones) | Seguimiento de issues |

---

## Licencia

Proyecto personal / privado de **Dong, Zhexi**. Consulta la configuración del repositorio para condiciones de distribución.

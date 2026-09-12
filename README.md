# MP4 to GIF / WebP

A streaming MP4-to-GIF/WebP converter with a bilingual Windows interface and a command-line mode. GIF uses up to 15 FPS; WebP defaults to 30 FPS in the interface.

Conversor por streaming de MP4 a GIF o WebP animado con interfaz bilingüe para Windows y modo de línea de comandos. GIF usa hasta 15 FPS; WebP inicia en 30 FPS en la interfaz.

- [Español](#español)
- [English](#english)

---

## Español

### Descargar el ejecutable

La versión portable para Windows se publica en [GitHub Releases](https://github.com/VindexLabsDev/MP4-TO-GIF/releases/latest). Descarga `MP4-to-GIF.exe` desde los archivos adjuntos de la versión más reciente. No necesitas instalar Python.

### Inicio rápido

1. Descarga y abre `MP4-to-GIF.exe` desde GitHub Releases.
2. Pulsa **Seleccionar** y elige un video `.mp4`.
3. Opcionalmente, selecciona una marca de agua PNG.
4. Opcionalmente, elige la salida, FPS, escala, inicio, fin y tamaño del logo.
5. Elige **GIF** o **WebP** y pulsa **Exportar**.
6. Cuando la barra llegue al 100%, pulsa **Mostrar en carpeta**.

La animación se guarda junto al MP4 y usa el mismo nombre. Por ejemplo, `video.mp4` genera `video.gif` o `video.webp`.

### Interfaz gráfica

| Opción | Valor predeterminado | Descripción |
|---|---:|---|
| Archivo | — | Solo acepta archivos MP4. |
| Salida | Junto al MP4 | El nombre se edita por separado y el selector pide solo la carpeta. |
| Logo | Sin logo | PNG opcional, colocado arriba a la derecha. |
| FPS | GIF: 15; WebP: 30 | GIF ofrece 10/15 FPS. WebP ofrece FPS originales, 10, 15, 24, 30 y 60. |
| Escala | Original | Cambia las dimensiones; por ejemplo, `0.5` reduce ancho y alto a la mitad. |
| Inicio / Fin | Video completo | Recorta el intervalo usando segundos. |
| Tamaño del logo | 20% | Ancho del logo respecto al ancho del video. |
| Barra de progreso | 0–100% | Muestra avance, actividad y tiempo estimado. |
| Idioma | Español | Permite cambiar la interfaz entre español e inglés. |

### Línea de comandos

Instala las dependencias y consulta la ayuda:

```powershell
python -m pip install -r requirements.txt
python converter.py --help
```

Conversión básica, conservando los FPS y el tamaño original:

```powershell
python converter.py video.mp4
```

Elegir el GIF de salida:

```powershell
python converter.py video.mp4 --output resultado.gif
```

Crear un WebP animado sin pérdida de color:

```powershell
python converter.py video.mp4 --format webp
```

Cambiar FPS:

```powershell
python converter.py video.mp4 --fps 24
```

Agregar un logo al 30% del ancho:

```powershell
python converter.py video.mp4 --logo marca.png --logo-size 30
```

Recortar, reducir a la mitad, cambiar FPS y agregar logo:

```powershell
python converter.py video.mp4 --start 2.5 --end 8 --resize 0.5 --fps 15 --logo marca.png --logo-size 25 --output resultado.gif
```

### Opciones y límites

| Opción | Límite | Notas |
|---|---|---|
| `input` | Archivo `.mp4` existente | Obligatorio en la CLI. Sin argumentos se abre la interfaz. |
| `-o`, `--output` | Ruta válida | Si se omite, usa el nombre y carpeta del MP4. Crea carpetas intermedias. |
| `--format` | `gif`, `webp` | Formato de salida; WebP se guarda sin pérdida. |
| `--fps` | Mayor que 0 y hasta 120 | Si se omite, usa los FPS originales. GIF limita la salida a 15 FPS para respetar el timing. |
| `--resize` | Mayor que 0 y hasta 4 | `0.5` reduce a la mitad; `2` duplica las dimensiones. |
| `--start` | Segundos | Inicio opcional del recorte. |
| `--end` | Segundos | Final opcional; debe ser posterior al inicio y estar dentro del video. |
| `--logo` | PNG existente | Conserva la transparencia del PNG. |
| `--logo-size` | 5–100 | Porcentaje del ancho del video. Solo se usa con `--logo`. |

Las opciones se pueden combinar libremente. `--start` y `--end` se aplican antes del cambio de tamaño, el logo y la creación del GIF.

### Consideraciones del formato GIF

- GIF no contiene audio; el audio del MP4 se descarta.
- GIF admite un máximo de 256 colores. El programa usa una paleta compartida para evitar que el logo cambie entre fotogramas.
- WebP sin pérdida conserva el color RGB y normalmente ofrece mejor fidelidad que GIF.
- GIF se limita a 15 FPS para mantener una reproducción estable y puede omitir fotogramas.
- GIF y WebP se procesan por streaming con FFmpeg; el uso de RAM no crece con la duración del video.
- Si el GIF de destino ya existe, se reemplaza únicamente después de completar correctamente la conversión.

### Compilar para Windows

Requiere Windows y Python 3.10 o posterior:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El script crea `.venv`, instala versiones reproducibles y genera `dist/MP4-to-GIF.exe`. La carpeta `dist` es local y no se versiona; publica el ejecutable en GitHub Releases.

### Solución de problemas

- **La conversión tarda demasiado:** reduce las dimensiones o recorta el intervalo.
- **El GIF pesa demasiado:** combina `--resize 0.5` con menos FPS.
- **El logo se ve pequeño:** aumenta **Tamaño del logo (%)** o usa `--logo-size`.
- **No aparece el icono actualizado:** actualiza la vista del Explorador; Windows puede conservar iconos antiguos en caché.
- **No se puede abrir el MP4:** confirma que existe, termina en `.mp4` y no está dañado.

### Licencia

El código se publica bajo la [Licencia MIT](LICENSE). Puede usarse, modificarse y distribuirse, incluso comercialmente, conservando el aviso de copyright y la licencia.

La licencia del código no concede derechos sobre la marca. **Vindex** es el nombre de fantasía de **Vindex Labs SpA**. El nombre y el logo de Vindex pertenecen a Vindex Labs SpA. Los proyectos derivados no pueden usarlos para presentarse como productos oficiales, afiliados o respaldados por Vindex sin autorización previa.

Vindex Labs SpA puede ofrecer otros productos propietarios o pagados, además de soporte, personalizaciones y servicios comerciales basados en este proyecto open source.

---

## English

### Download the executable

The portable Windows build is published on [GitHub Releases](https://github.com/VindexLabsDev/MP4-TO-GIF/releases/latest). Download `MP4-to-GIF.exe` from the latest release assets. Python does not need to be installed.

### Quick start

1. Download and open `MP4-to-GIF.exe` from GitHub Releases.
2. Click **Browse** and choose an `.mp4` video.
3. Optionally select a PNG watermark.
4. Optionally choose the output, FPS, scale, start, end, and logo size.
5. Choose **GIF** or **WebP**, then click **Export**.
6. When progress reaches 100%, click **Show in folder**.

The animation is saved next to the MP4 with the same base name. For example, `video.mp4` creates `video.gif` or `video.webp`.

### Graphical interface

| Setting | Default | Description |
|---|---:|---|
| File | — | Accepts MP4 files only. |
| Output | Next to the MP4 | The name is edited separately; the folder picker selects only a directory. |
| Logo | No logo | Optional PNG placed in the top-right corner. |
| FPS | GIF: 15; WebP: 30 | GIF offers 10/15 FPS. WebP offers original, 10, 15, 24, 30, and 60 FPS. |
| Scale | Original | Changes dimensions; for example, `0.5` halves width and height. |
| Start / End | Full video | Trims the time range in seconds. |
| Logo size | 20% | Logo width relative to the video width. |
| Progress bar | 0–100% | Shows progress, activity, and estimated time. |
| Language | Spanish | Switches the interface between Spanish and English. |

### Command line

Install dependencies and view all options:

```powershell
python -m pip install -r requirements.txt
python converter.py --help
```

Basic conversion preserving the original FPS and dimensions:

```powershell
python converter.py video.mp4
```

Choose the output file:

```powershell
python converter.py video.mp4 --output result.gif
```

Create a lossless animated WebP:

```powershell
python converter.py video.mp4 --format webp
```

Change FPS:

```powershell
python converter.py video.mp4 --fps 24
```

Add a logo at 30% of the video width:

```powershell
python converter.py video.mp4 --logo brand.png --logo-size 30
```

Trim, scale to half size, change FPS, and add a logo:

```powershell
python converter.py video.mp4 --start 2.5 --end 8 --resize 0.5 --fps 15 --logo brand.png --logo-size 25 --output result.gif
```

### Options and limits

| Option | Limit | Notes |
|---|---|---|
| `input` | Existing `.mp4` file | Required in CLI mode. Running without arguments opens the GUI. |
| `-o`, `--output` | Valid path | Defaults to the MP4 name and directory. Missing parent directories are created. |
| `--format` | `gif`, `webp` | Output format; WebP is saved losslessly. |
| `--fps` | Greater than 0, up to 120 | Defaults to source FPS. GIF output is limited to 15 FPS to preserve timing. |
| `--resize` | Greater than 0, up to 4 | `0.5` halves dimensions; `2` doubles them. |
| `--start` | Seconds | Optional trim start. |
| `--end` | Seconds | Optional trim end; it must follow the start and remain inside the video. |
| `--logo` | Existing PNG | PNG transparency is preserved. |
| `--logo-size` | 5–100 | Percentage of video width. Used only with `--logo`. |

Options may be freely combined. Trimming is applied before resizing, logo placement, and GIF creation.

### GIF format considerations

- GIF has no audio; MP4 audio is discarded.
- GIF supports at most 256 colors. The converter uses one shared palette to keep the logo stable between frames.
- Lossless WebP preserves RGB color and usually offers better fidelity than GIF.
- GIF is limited to 15 FPS for stable playback and may skip frames.
- GIF and WebP are streamed through FFmpeg, so RAM use does not grow with video duration.
- If the destination GIF exists, it is replaced only after a successful conversion.

### Build for Windows

Windows and Python 3.10 or newer are required:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The script creates `.venv`, installs reproducible dependency versions, and writes `dist/MP4-to-GIF.exe`. The `dist` directory is local and is not versioned; publish the executable through GitHub Releases.

### Troubleshooting

- **Conversion takes too long:** reduce the dimensions or trim the time range.
- **The GIF is too large:** combine `--resize 0.5` with a lower FPS value.
- **The logo is too small:** increase **Tamaño del logo (%)** or use `--logo-size`.
- **The updated icon does not appear:** refresh Windows Explorer; Windows may cache old icons.
- **The MP4 cannot be opened:** verify that it exists, ends in `.mp4`, and is not damaged.

### License

The code is released under the [MIT License](LICENSE). It may be used, modified, and distributed, including commercially, provided that the copyright notice and license are retained.

The code license does not grant trademark rights. **Vindex** is the trade name of **Vindex Labs SpA**. The Vindex name and logo belong to Vindex Labs SpA. Derivative projects may not use them to present themselves as official, affiliated with, or endorsed by Vindex without prior permission.

Vindex Labs SpA may offer separate proprietary or paid products, as well as support, customization, and commercial services based on this open-source project.

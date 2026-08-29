# MP4 to GIF

A small MP4-to-GIF converter with a Windows interface and a command-line mode. By default, it preserves the source video's frame rate and can place a PNG logo in the top-right corner.

Conversor sencillo de MP4 a GIF con interfaz para Windows y modo de línea de comandos. De forma predeterminada, conserva los FPS del video original y permite colocar un logo PNG en la esquina superior derecha.

- [Español](#español)
- [English](#english)

---

## Español

### Inicio rápido

1. Abre `output/MP4-to-GIF.exe`.
2. Pulsa **Seleccionar archivo** y elige un video `.mp4`.
3. Opcionalmente, pulsa **Agregar logo PNG**.
4. Opcionalmente, elige la salida, FPS, escala, inicio, fin y tamaño del logo.
5. Pulsa **Convertir a GIF**.
6. Cuando la barra llegue al 100%, pulsa **Ver archivo**.

El GIF se guarda junto al MP4 y usa el mismo nombre. Por ejemplo, `video.mp4` genera `video.gif`.

### Interfaz gráfica

| Opción | Valor predeterminado | Descripción |
|---|---:|---|
| Archivo | — | Solo acepta archivos MP4. |
| Salida | Junto al MP4 | Permite elegir el nombre y la carpeta del GIF. |
| Logo | Sin logo | PNG opcional, colocado arriba a la derecha. |
| FPS | Originales | Conserva la tasa de fotogramas del MP4. También admite un valor escrito manualmente. |
| Escala | Original | Cambia las dimensiones; por ejemplo, `0.5` reduce ancho y alto a la mitad. |
| Inicio / Fin | Video completo | Recorta el intervalo usando segundos. |
| Tamaño del logo | 20% | Ancho del logo respecto al ancho del video. |
| Barra de progreso | 0–100% | Muestra lectura, creación de paleta, conversión y guardado. |

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
| `--fps` | Mayor que 0 y hasta 120 | Si se omite, conserva los FPS originales. Más FPS aumentan tiempo, memoria y tamaño. |
| `--resize` | Mayor que 0 y hasta 4 | `0.5` reduce a la mitad; `2` duplica las dimensiones. |
| `--start` | Segundos | Inicio opcional del recorte. |
| `--end` | Segundos | Final opcional; debe ser posterior al inicio y estar dentro del video. |
| `--logo` | PNG existente | Conserva la transparencia del PNG. |
| `--logo-size` | 5–100 | Porcentaje del ancho del video. Solo se usa con `--logo`. |

Las opciones se pueden combinar libremente. `--start` y `--end` se aplican antes del cambio de tamaño, el logo y la creación del GIF.

### Consideraciones del formato GIF

- GIF no contiene audio; el audio del MP4 se descarta.
- GIF admite un máximo de 256 colores. El programa usa una paleta compartida para evitar que el logo cambie entre fotogramas.
- Conservar todos los FPS puede producir archivos grandes y conversiones lentas.
- La conversión mantiene los fotogramas en memoria. Para videos largos, recorta, reduce FPS o usa `--resize`.
- Si el GIF de destino ya existe, se reemplaza únicamente después de completar correctamente la conversión.

### Compilar para Windows

Requiere Windows y Python 3.10 o posterior:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El script crea `.venv`, instala versiones reproducibles y genera `output/MP4-to-GIF.exe`.

### Solución de problemas

- **La conversión consume mucha memoria:** recorta el video, reduce sus dimensiones o baja los FPS.
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

### Quick start

1. Open `output/MP4-to-GIF.exe`.
2. Click **Seleccionar archivo** and choose an `.mp4` video.
3. Optionally click **Agregar logo PNG**.
4. Optionally choose the output, FPS, scale, start, end, and logo size.
5. Click **Convertir a GIF**.
6. When progress reaches 100%, click **Ver archivo**.

The GIF is saved next to the MP4 with the same base name. For example, `video.mp4` creates `video.gif`.

### Graphical interface

| Setting | Default | Description |
|---|---:|---|
| File | — | Accepts MP4 files only. |
| Output | Next to the MP4 | Lets you choose the GIF name and directory. |
| Logo | No logo | Optional PNG placed in the top-right corner. |
| FPS | Original | Preserves the MP4 frame rate. A custom value can also be entered. |
| Scale | Original | Changes dimensions; for example, `0.5` halves width and height. |
| Start / End | Full video | Trims the time range in seconds. |
| Logo size | 20% | Logo width relative to the video width. |
| Progress bar | 0–100% | Tracks frame reading, palette creation, conversion, and saving. |

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
| `--fps` | Greater than 0, up to 120 | Defaults to source FPS. Higher values increase time, memory use, and file size. |
| `--resize` | Greater than 0, up to 4 | `0.5` halves dimensions; `2` doubles them. |
| `--start` | Seconds | Optional trim start. |
| `--end` | Seconds | Optional trim end; it must follow the start and remain inside the video. |
| `--logo` | Existing PNG | PNG transparency is preserved. |
| `--logo-size` | 5–100 | Percentage of video width. Used only with `--logo`. |

Options may be freely combined. Trimming is applied before resizing, logo placement, and GIF creation.

### GIF format considerations

- GIF has no audio; MP4 audio is discarded.
- GIF supports at most 256 colors. The converter uses one shared palette to keep the logo stable between frames.
- Preserving every frame can create large files and slow conversions.
- Frames are kept in memory while converting. For long videos, trim, lower FPS, or use `--resize`.
- If the destination GIF exists, it is replaced only after a successful conversion.

### Build for Windows

Windows and Python 3.10 or newer are required:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The script creates `.venv`, installs reproducible dependency versions, and writes `output/MP4-to-GIF.exe`.

### Troubleshooting

- **Conversion uses too much memory:** trim the video, reduce its dimensions, or lower FPS.
- **The GIF is too large:** combine `--resize 0.5` with a lower FPS value.
- **The logo is too small:** increase **Tamaño del logo (%)** or use `--logo-size`.
- **The updated icon does not appear:** refresh Windows Explorer; Windows may cache old icons.
- **The MP4 cannot be opened:** verify that it exists, ends in `.mp4`, and is not damaged.

### License

The code is released under the [MIT License](LICENSE). It may be used, modified, and distributed, including commercially, provided that the copyright notice and license are retained.

The code license does not grant trademark rights. **Vindex** is the trade name of **Vindex Labs SpA**. The Vindex name and logo belong to Vindex Labs SpA. Derivative projects may not use them to present themselves as official, affiliated with, or endorsed by Vindex without prior permission.

Vindex Labs SpA may offer separate proprietary or paid products, as well as support, customization, and commercial services based on this open-source project.

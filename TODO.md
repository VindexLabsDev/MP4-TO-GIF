# Roadmap de producción

Objetivo del producto: convertir MP4 a GIF o WebP localmente, con temporización correcta, consumo de memoria estable y una interfaz simple. No pretende reemplazar un editor de animaciones.

## P0 — Calidad y control de tamaño

- [ ] **Agregar perfiles de calidad WebP**: `Sin pérdida`, `Equilibrado` y `Archivo pequeño`.
  - Objetivo: permitir elegir entre fidelidad y peso sin exponer parámetros internos de FFmpeg.
  - Aceptación: cada perfil produce un WebP animado válido; `Equilibrado` y `Archivo pequeño` pesan menos que `Sin pérdida` sobre el corpus de prueba.
  - Referencias: [WebP de Google](https://developers.google.com/speed/webp), [RFC 9649](https://www.rfc-editor.org/rfc/rfc9649.html).

- [ ] **Permitir definir el ancho máximo en píxeles** manteniendo la relación de aspecto.
  - Objetivo: hacer predecible el tamaño visual y reducir el peso con una medida comprensible.
  - Aceptación: presets de 320, 480, 720 y 1080 px, más `Original`; nunca se deforma la imagen.
  - Referencias: [recomendaciones de Ezgif](https://ezgif.com/help/how-to-make-gif), [Gifski](https://gif.ski/).

- [ ] **Agregar perfiles GIF**: `Alta calidad`, `Equilibrado` y `Archivo pequeño`.
  - Objetivo: controlar colores y dithering sin convertir la interfaz en un panel técnico.
  - Aceptación: los perfiles modifican únicamente opciones documentadas de `palettegen`/`paletteuse`; la duración final conserva una desviación máxima de 100 ms o 1 %, lo que sea mayor.
  - Referencia: [filtros de FFmpeg](https://ffmpeg.org/ffmpeg-filters.html#palettegen-1).

## P1 — Verificación antes de exportar

- [ ] **Mostrar una vista previa del recorte** con posición inicial y final.
  - Objetivo: evitar exportaciones repetidas por tiempos ingresados incorrectamente.
  - Aceptación: se puede inspeccionar el primer y último cuadro elegidos sin cargar el video completo en memoria.

- [ ] **Advertir sobre salidas potencialmente grandes**.
  - Objetivo: explicar antes de exportar que resolución, duración y FPS aumentan el peso, especialmente en GIF.
  - Aceptación: mostrar una advertencia no bloqueante para combinaciones de alto costo; no prometer un tamaño exacto.
  - Referencias: [optimización GIF de Ezgif](https://ezgif.com/help/optimizing-gifs), [Gifski: tamaño y calidad](https://gif.ski/).

- [ ] **Aceptar arrastrar y soltar un MP4** sobre la ventana.
  - Objetivo: reducir el flujo de selección a una sola acción.
  - Aceptación: valida la extensión igual que el selector actual y no acepta múltiples archivos.

## P2 — Medición y entrega

- [ ] **Crear un corpus de regresión pequeño** con captura de pantalla, animación, video real y degradados.
  - Objetivo: detectar cambios de color, duración, peso y memoria antes de publicar.
  - Aceptación: cada muestra verifica formato, dimensiones, duración y reproducción; el proceso no crece con la duración completa del video.

- [ ] **Comparar GIF contra FFmpeg y Gifski**.
  - Objetivo: saber con mediciones dónde gana cada codificador.
  - Aceptación: registrar tamaño, tiempo, memoria máxima y una comparación visual con los mismos FPS y dimensiones.
  - Nota: Gifski usa pngquant, dithering temporal y controles específicos de movimiento; cualquier integración exige revisar su licencia AGPL/comercial.
  - Referencias: [Gifski](https://gif.ski/), [licencia de Gifski](https://gif.ski/license.html).

- [ ] **Automatizar la publicación del ejecutable**.
  - Objetivo: que cada versión verificable produzca un único `.exe` y su checksum SHA-256.
  - Aceptación: compilación limpia, pruebas aprobadas, versión etiquetada y checksum publicado junto al binario.

- [ ] **Firmar digitalmente el ejecutable de Windows**.
  - Objetivo: identificar al editor y reducir advertencias de procedencia desconocida.
  - Aceptación: firma válida y verificable en las propiedades del archivo antes de publicar.

## Criterios permanentes

- [ ] GIF conserva el límite de 15 FPS decidido para el producto.
- [ ] WebP conserva el tiempo real aunque FFmpeg deba descartar o duplicar cuadros.
- [ ] GIF y WebP siguen procesándose por streaming.
- [ ] Cancelar o fallar nunca reemplaza una exportación anterior válida.
- [ ] Todos los textos visibles existen en español e inglés.
- [ ] La ruta, el nombre y la extensión de salida permanecen separados.

## Fuera de alcance

- Editor cuadro por cuadro, efectos, subtítulos o grabación de pantalla.
- Procesamiento en la nube, cuentas de usuario o almacenamiento remoto.
- Integrar Gifski hasta que una prueba demuestre una mejora necesaria y se resuelva su licencia.
- Agregar formatos de entrada distintos de MP4 sin una necesidad concreta.

## Referencias de formato

- [GIF89a](https://www.w3.org/Graphics/GIF/spec-gif89a.txt): paletas y duración expresada en centésimas de segundo.
- [RFC 9649 — WebP](https://www.rfc-editor.org/rfc/rfc9649.html): estructura y duración de cuadros animados en milisegundos.
- [FFmpeg Filters](https://ffmpeg.org/ffmpeg-filters.html): conversión de FPS, escalado, generación y aplicación de paletas.
- [Google WebP](https://developers.google.com/speed/webp): compresión, transparencia, animación y soporte.
- [Gifski](https://gif.ski/): referencia de máxima calidad para GIF.
- [Ezgif](https://ezgif.com/): referencia funcional para conversión y optimización accesible.

import argparse
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from imageio_ffmpeg import get_ffmpeg_exe
from moviepy import VideoFileClip


class ConversionCancelled(Exception):
    pass


def run_ffmpeg(command, duration, progress_start, progress_span, report, cancel_callback):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    output = []
    try:
        assert process.stdout is not None
        for line in process.stdout:
            output.append(line)
            if cancel_callback and cancel_callback():
                process.terminate()
                process.wait()
                raise ConversionCancelled()
            if line.startswith("out_time_us="):
                elapsed = int(line.partition("=")[2]) / 1_000_000
                report(min(progress_start + progress_span, round(progress_start + elapsed / duration * progress_span)))
        if process.wait() != 0:
            raise RuntimeError("FFmpeg: " + "".join(output).strip())
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


def ffmpeg_input(input_path, start_time, logo_path=None):
    command = [
        get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
    ]
    if start_time is not None:
        command += ["-ss", f"{start_time:g}"]
    command += ["-i", str(input_path)]
    if logo_path:
        command += ["-loop", "1", "-i", str(logo_path)]
    return command


def video_filter(fps, resize):
    filters = [f"fps={fps:g}"]
    if resize is not None:
        filters.append(f"scale=iw*{resize:g}:ih*{resize:g}")
    return ",".join(filters)


def stream_webp(
    input_path: Path,
    output_path: Path,
    fps: float,
    resize: float | None,
    start_time: float | None,
    duration: float,
    logo_path: Path | None,
    logo_width: int | None,
    report,
    cancel_callback,
) -> str:
    temporary = tempfile.NamedTemporaryFile(
        dir=output_path.parent, suffix=".webp", delete=False
    )
    temporary.close()
    temporary_path = Path(temporary.name)
    filters = video_filter(fps, resize)
    command = ffmpeg_input(input_path, start_time, logo_path)
    if logo_path:
        command += [
            "-filter_complex",
            f"[0:v]{filters}[base];[1:v]scale={logo_width}:-1[logo];"
            "[base][logo]overlay=W-w-16:16:shortest=1[out]",
            "-map", "[out]",
        ]
    else:
        command += ["-vf", filters]
    command += [
        "-t", f"{duration:g}", "-an", "-c:v", "libwebp_anim",
        "-lossless", "1", "-compression_level", "4", "-loop", "0",
        "-f", "webp", str(temporary_path),
    ]
    try:
        run_ffmpeg(command, duration, 0, 99, report, cancel_callback)
        os.replace(temporary_path, output_path)
        report(100)
        return str(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def stream_gif(
    input_path, output_path, fps, resize, start_time, duration,
    logo_path, logo_width, report, cancel_callback,
):
    palette_file = tempfile.NamedTemporaryFile(dir=output_path.parent, suffix=".png", delete=False)
    output_file = tempfile.NamedTemporaryFile(dir=output_path.parent, suffix=".gif", delete=False)
    palette_file.close()
    output_file.close()
    palette_path, temporary_path = Path(palette_file.name), Path(output_file.name)
    filters = video_filter(min(fps, 15), resize)
    try:
        palette_command = ffmpeg_input(input_path, start_time, logo_path)
        if logo_path:
            palette_command += [
                "-filter_complex",
                f"[0:v]{filters}[base];[1:v]scale={logo_width}:-1[logo];"
                "[base][logo]overlay=W-w-16:16:shortest=1[video];"
                "[video]palettegen=max_colors=256:stats_mode=diff[out]",
                "-map", "[out]",
            ]
        else:
            palette_command += ["-vf", f"{filters},palettegen=max_colors=256:stats_mode=diff"]
        palette_command += ["-t", f"{duration:g}", "-frames:v", "1", "-update", "1", str(palette_path)]
        run_ffmpeg(palette_command, duration, 0, 30, report, cancel_callback)
        report(30)

        encode_command = ffmpeg_input(input_path, start_time, logo_path)
        encode_command += ["-i", str(palette_path)]
        palette_index = 2 if logo_path else 1
        if logo_path:
            composed = (
                f"[0:v]{filters}[base];[1:v]scale={logo_width}:-1[logo];"
                "[base][logo]overlay=W-w-16:16:shortest=1[video];"
            )
        else:
            composed = f"[0:v]{filters}[video];"
        encode_command += [
            "-filter_complex",
            f"{composed}[video][{palette_index}:v]paletteuse=dither=sierra2_4a:diff_mode=rectangle[out]",
            "-map", "[out]", "-t", f"{duration:g}", "-an", "-loop", "0", str(temporary_path),
        ]
        run_ffmpeg(encode_command, duration, 30, 69, report, cancel_callback)
        os.replace(temporary_path, output_path)
        report(100)
        return str(output_path)
    finally:
        palette_path.unlink(missing_ok=True)
        temporary_path.unlink(missing_ok=True)


def convert_mp4_to_gif(
    input_path: str,
    output_path: str | None = None,
    fps: float | None = None,
    resize: float | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    logo_path: str | None = None,
    logo_scale: float = 0.2,
    output_format: str | None = None,
    progress_callback=None,
    cancel_callback=None,
) -> str:
    """
    Convert an MP4 file to animated GIF or WebP.

    Args:
        input_path: Path to the input MP4 file.
        output_path: Path for the output animation. Defaults to same name as input.
        fps: Frames per second for the animation. None preserves the video's FPS.
        resize: Scale factor (e.g. 0.5 = half size). None keeps original size.
        start_time: Start time in seconds. None starts from the beginning.
        end_time: End time in seconds. None goes until the end.

    Returns:
        Path to the generated animation file.
    """
    input_path = Path(input_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() != ".mp4":
        raise ValueError(f"Input file must be an MP4 file, got: {input_path.suffix}")

    output_format = output_format.lower() if output_format else None
    if output_format not in {None, "gif", "webp"}:
        raise ValueError("Output format must be GIF or WebP.")
    if output_path is None:
        output_format = output_format or "gif"
        output_path = input_path.with_suffix(f".{output_format}")
    else:
        output_path = Path(output_path).resolve()
        output_format = output_format or (
            output_path.suffix.lower()[1:]
            if output_path.suffix.lower() in {".gif", ".webp"}
            else "gif"
        )
        output_path = output_path.with_suffix(f".{output_format}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    last_progress = -1

    def report(value: int) -> None:
        nonlocal last_progress
        if progress_callback and value != last_progress:
            last_progress = value
            progress_callback(value)

    report(0)

    with VideoFileClip(str(input_path)) as clip:
        fps = clip.fps if fps is None else fps
        if not 0 < fps <= 120:
            raise ValueError("FPS must be between 0 and 120.")
        if start_time is not None and start_time < 0:
            raise ValueError("Start time cannot be negative.")
        if end_time is not None and end_time > clip.duration:
            raise ValueError("End time cannot exceed the video duration.")
        if (start_time or 0) >= (end_time if end_time is not None else clip.duration):
            raise ValueError("End time must be greater than start time.")
        if resize is not None and not (0 < resize <= 4):
            raise ValueError("Resize factor must be between 0 (exclusive) and 4.")
        resolved_logo = None
        if logo_path:
            resolved_logo = Path(logo_path).resolve()
            if not resolved_logo.is_file() or resolved_logo.suffix.lower() != ".png":
                raise ValueError("Logo must be an existing PNG file.")
            if not 0.05 <= logo_scale <= 1:
                raise ValueError("Logo size must be between 5% and 100%.")
        duration = (end_time if end_time is not None else clip.duration) - (start_time or 0)
        arguments = (
            input_path, output_path, fps, resize, start_time, duration,
            resolved_logo,
            round(clip.w * (resize or 1) * logo_scale) if resolved_logo else None,
            report, cancel_callback,
        )
    return stream_webp(*arguments) if output_format == "webp" else stream_gif(*arguments)


def show_in_folder(path: str) -> None:
    """Open the system file browser with the generated file selected."""
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", path])
    else:
        subprocess.Popen(["xdg-open", str(Path(path).parent)])


def launch_gui() -> None:
    from PySide6.QtCore import QObject, QRectF, Qt, QThread, QTimer, Signal, Slot
    from PySide6.QtGui import QColor, QDoubleValidator, QIcon, QLinearGradient, QPainter, QPainterPath
    from PySide6.QtWidgets import (
        QAbstractSpinBox, QApplication, QComboBox, QFileDialog, QFrame, QGraphicsDropShadowEffect,
        QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
        QPushButton, QSpinBox, QVBoxLayout, QWidget,
    )

    asset_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

    class FlowProgress(QWidget):
        def __init__(self):
            super().__init__()
            self.display_value = self.target_value = self.phase = 0
            self.timer = QTimer(self)
            self.timer.setInterval(33)
            self.timer.timeout.connect(self.animate)
            self.setFixedHeight(12)
            self.setAccessibleName("Progreso de exportación")

        def setValue(self, value):
            self.target_value = max(0, min(100, value))
            if self.target_value < self.display_value:
                self.display_value = self.target_value
            self.update()

        def setActive(self, active):
            if active:
                self.timer.start()
            else:
                self.timer.stop()
                self.display_value = self.target_value
                self.update()

        def animate(self):
            self.phase = (self.phase + 2.4) % 48
            if self.display_value < self.target_value:
                self.display_value = min(
                    self.target_value,
                    self.display_value + max(0.18, (self.target_value - self.display_value) * 0.12),
                )
            self.update()

        def paintEvent(self, _event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            bounds = QRectF(0, 1, self.width(), self.height() - 2)
            shape = QPainterPath()
            shape.addRoundedRect(bounds, 5, 5)
            painter.fillPath(shape, QColor("#202638"))
            fill_width = bounds.width() * self.display_value / 100
            if fill_width <= 0:
                return
            painter.save()
            painter.setClipPath(shape)
            painter.setClipRect(
                QRectF(0, 1, fill_width, bounds.height()),
                Qt.ClipOperation.IntersectClip,
            )
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor("#43d9ff"))
            gradient.setColorAt(1, QColor("#7c8cff"))
            painter.fillRect(QRectF(0, 1, fill_width, bounds.height()), gradient)
            painter.setPen(QColor(225, 252, 255, 90))
            painter.setBrush(QColor(225, 252, 255, 175))
            for offset in range(-48, self.width() + 48, 48):
                x = (offset + self.phase) % (self.width() + 48) - 12
                painter.drawEllipse(QRectF(x, 3, 12, self.height() - 6))
            painter.restore()

    class Worker(QObject):
        progress = Signal(int)
        succeeded = Signal(str)
        failed = Signal(str)
        cancelled = Signal()

        def __init__(self, options):
            super().__init__()
            self.options = options
            self.cancel_event = threading.Event()

        def cancel(self):
            self.cancel_event.set()

        @Slot()
        def run(self):
            try:
                self.succeeded.emit(convert_mp4_to_gif(
                    **self.options, progress_callback=self.progress.emit,
                    cancel_callback=self.cancel_event.is_set,
                ))
            except ConversionCancelled:
                self.cancelled.emit()
            except Exception as error:
                self.failed.emit(str(error))

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.input_path = self.logo_path = self.output_dir = self.output_file = None
            self.thread = self.worker = None
            self.closing = False
            self.setWindowTitle("Conversor de video — Vindex Labs")
            self.resize(1040, 720)
            self.setMinimumSize(920, 660)
            icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "app-icon.ico"
            if icon.exists():
                self.setWindowIcon(QIcon(str(icon)))
            self.build_ui()

        def shadow(self, widget, blur=32, y=10):
            effect = QGraphicsDropShadowEffect(widget)
            effect.setBlurRadius(blur)
            effect.setOffset(0, y)
            effect.setColor(QColor("#99000000"))
            widget.setGraphicsEffect(effect)

        def file_row(self, title, initial, button_text, callback):
            row = QFrame(objectName="fileRow")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(18, 14, 14, 14)
            copy = QVBoxLayout()
            eyebrow = QLabel(title, objectName="eyebrow")
            value = QLabel(initial, objectName="pathValue")
            value.setTextInteractionFlags(value.textInteractionFlags())
            copy.addWidget(eyebrow)
            copy.addWidget(value)
            layout.addLayout(copy, 1)
            button = QPushButton(button_text, objectName="secondaryButton")
            button.clicked.connect(callback)
            layout.addWidget(button)
            return row, value, eyebrow, button

        def build_ui(self):
            self.setStyleSheet(STYLESHEET)
            central = QWidget(objectName="root")
            self.setCentralWidget(central)
            page = QVBoxLayout(central)
            page.setContentsMargins(32, 28, 32, 28)
            page.setSpacing(18)

            hero = QFrame(objectName="hero")
            hero_layout = QHBoxLayout(hero)
            hero_layout.setContentsMargins(30, 24, 30, 24)
            titles = QVBoxLayout()
            titles.setSpacing(3)
            self.overline = QLabel(objectName="overline")
            self.title = QLabel(objectName="title")
            self.subtitle = QLabel(objectName="subtitle")
            titles.addWidget(self.overline)
            titles.addWidget(self.title)
            titles.addWidget(self.subtitle)
            hero_layout.addLayout(titles, 1)
            hero_tools = QVBoxLayout()
            hero_tools.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.language = QComboBox(objectName="language")
            self.language.addItem("ES", "es")
            self.language.addItem("EN", "en")
            self.language.setFixedWidth(72)
            self.badge = QLabel(objectName="badge")
            hero_tools.addWidget(self.language, 0, Qt.AlignmentFlag.AlignRight)
            hero_tools.addWidget(self.badge)
            hero_layout.addLayout(hero_tools)
            page.addWidget(hero)
            self.shadow(hero, 40, 12)

            content = QHBoxLayout()
            content.setSpacing(18)
            files = QFrame(objectName="card")
            files_layout = QVBoxLayout(files)
            files_layout.setContentsMargins(20, 20, 20, 20)
            files_layout.setSpacing(12)
            self.files_title = QLabel(objectName="sectionTitle")
            files_layout.addWidget(self.files_title)
            row, self.input_label, self.input_eyebrow, self.input_button = self.file_row(
                "ARCHIVO DE ORIGEN", "Selecciona un video MP4", "Seleccionar", self.choose_input
            )
            files_layout.addWidget(row)
            row, self.output_label, self.output_eyebrow, self.output_button = self.file_row(
                "UBICACIÓN DE SALIDA", "Misma carpeta que el video", "Cambiar", self.choose_output
            )
            files_layout.addWidget(row)
            row, self.logo_label, self.logo_eyebrow, self.logo_button = self.file_row(
                "MARCA DE AGUA · OPCIONAL", "No seleccionada", "Seleccionar", self.choose_logo
            )
            files_layout.addWidget(row)
            files_layout.addStretch()
            content.addWidget(files, 3)
            self.shadow(files)

            settings = QFrame(objectName="card")
            grid = QGridLayout(settings)
            grid.setContentsMargins(22, 20, 22, 22)
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(9)
            self.settings_title = QLabel(objectName="sectionTitle")
            grid.addWidget(self.settings_title, 0, 0, 1, 2)
            self.format = QComboBox()
            self.format.addItems(("GIF", "WebP"))
            self.output_name = QLineEdit(objectName="outputName")
            self.output_name.setPlaceholderText("Nombre del archivo")
            self.output_suffix = QLabel(".gif", objectName="outputSuffix")
            name_row = QHBoxLayout()
            name_row.setSpacing(0)
            name_row.addWidget(self.output_name, 1)
            name_row.addWidget(self.output_suffix)
            name_cell = QVBoxLayout()
            self.output_name_label = QLabel(objectName="fieldLabel")
            name_cell.addWidget(self.output_name_label)
            name_cell.addLayout(name_row)
            grid.addLayout(name_cell, 1, 0, 1, 2)
            self.fps = QComboBox()
            self.fps.addItems(("10", "15"))
            self.fps.setCurrentText("15")
            self.scale = QComboBox()
            self.scale.addItems(("Original", "0.25", "0.5", "0.75", "1", "1.5", "2"))
            self.logo_size = QSpinBox()
            self.logo_size.setRange(5, 100)
            self.logo_size.setValue(20)
            self.logo_size.setSuffix(" %")
            self.logo_size.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            self.start = QLineEdit()
            self.end = QLineEdit()
            validator = QDoubleValidator(0, 999999, 3, self)
            self.start.setValidator(validator)
            self.end.setValidator(validator)
            self.start.setPlaceholderText("Sin recorte")
            self.end.setPlaceholderText("Sin recorte")
            fields = (("format_label", self.format), ("fps_label", self.fps),
                      ("scale_label", self.scale), ("logo_size_label", self.logo_size),
                      ("start_label", self.start), ("end_label", self.end))
            for index, (label, field) in enumerate(fields):
                row, column = divmod(index, 2)
                cell = QVBoxLayout()
                label_widget = QLabel(objectName="fieldLabel")
                setattr(self, label, label_widget)
                cell.addWidget(label_widget)
                cell.addWidget(field)
                grid.addLayout(cell, row + 2, column)
            grid.setRowStretch(5, 1)
            content.addWidget(settings, 2)
            self.shadow(settings)
            page.addLayout(content, 1)

            footer = QFrame(objectName="footer")
            footer_layout = QGridLayout(footer)
            footer_layout.setContentsMargins(20, 16, 20, 16)
            self.progress = FlowProgress()
            self.status = QLabel("Selecciona un archivo MP4 para comenzar", objectName="status")
            self.eta = QLabel("", objectName="eta")
            self.percent = QLabel("0%", objectName="percent")
            self.convert_button = QPushButton("Exportar como GIF", objectName="primaryButton")
            self.convert_button.setEnabled(False)
            self.convert_button.clicked.connect(self.convert)
            self.cancel_button = QPushButton("Cancelar", objectName="secondaryButton")
            self.cancel_button.setEnabled(False)
            self.cancel_button.clicked.connect(self.cancel_conversion)
            self.open_button = QPushButton("Mostrar en carpeta", objectName="secondaryButton")
            self.open_button.setEnabled(False)
            self.open_button.clicked.connect(lambda: show_in_folder(self.output_file))
            self.format.currentTextChanged.connect(self.update_format)
            self.language.currentIndexChanged.connect(self.apply_language)
            footer_layout.addWidget(self.progress, 0, 0, 1, 3)
            footer_layout.addWidget(self.status, 1, 0)
            footer_layout.addWidget(self.eta, 1, 1)
            footer_layout.addWidget(self.percent, 1, 2)
            actions = QHBoxLayout()
            actions.addWidget(self.convert_button)
            actions.addWidget(self.cancel_button)
            actions.addWidget(self.open_button)
            actions.addStretch()
            footer_layout.addLayout(actions, 2, 0, 1, 3)
            page.addWidget(footer)
            self.shadow(footer, 24, 8)
            self.controls = (
                self.input_button, self.output_button, self.logo_button,
                self.output_name, self.format, self.fps, self.scale,
                self.logo_size, self.start, self.end, self.language,
            )
            self.apply_language()

        def t(self, spanish, english):
            return english if self.language.currentData() == "en" else spanish

        def localized_error(self, error):
            if self.language.currentData() == "en":
                return error
            messages = {
                "FPS must be between 0 and 120.": "Los FPS deben estar entre 0 y 120.",
                "Start time cannot be negative.": "El tiempo de inicio no puede ser negativo.",
                "End time cannot exceed the video duration.": "El tiempo final no puede superar la duración del video.",
                "End time must be greater than start time.": "El tiempo final debe ser mayor que el inicial.",
                "Resize factor must be between 0 (exclusive) and 4.": "La escala debe ser mayor que 0 y no superar 4.",
                "Logo must be an existing PNG file.": "La marca de agua debe ser un archivo PNG existente.",
                "Logo size must be between 5% and 100%.": "El tamaño de la marca debe estar entre 5% y 100%.",
            }
            if error.startswith("Input file not found:"):
                return error.replace("Input file not found:", "No se encontró el archivo de origen:", 1)
            if error.startswith("Input file must be an MP4 file"):
                return "El archivo de origen debe estar en formato MP4."
            return messages.get(error, error)

        def apply_language(self, _index=None):
            self.setWindowTitle(self.t("Conversor de video — Vindex Labs", "Video converter — Vindex Labs"))
            self.overline.setText(self.t("VINDEX LABS  /  CONVERSOR DE VIDEO", "VINDEX LABS  /  VIDEO CONVERTER"))
            self.title.setText(self.t("Convierte videos a GIF o WebP", "Convert videos to GIF or WebP"))
            self.subtitle.setText(self.t("Configura el formato, ajusta el recorte y exporta.", "Choose a format, trim the video, and export."))
            self.badge.setText(self.t("PROCESAMIENTO EN EL EQUIPO", "ON-DEVICE PROCESSING"))
            self.files_title.setText(self.t("Archivos del proyecto", "Project files"))
            self.settings_title.setText(self.t("Configuración de salida", "Output settings"))
            self.input_eyebrow.setText(self.t("ARCHIVO DE ORIGEN", "SOURCE FILE"))
            self.output_eyebrow.setText(self.t("UBICACIÓN DE SALIDA", "OUTPUT FOLDER"))
            self.logo_eyebrow.setText(self.t("MARCA DE AGUA · OPCIONAL", "WATERMARK · OPTIONAL"))
            self.input_button.setText(self.t("Seleccionar", "Browse"))
            self.output_button.setText(self.t("Cambiar", "Change"))
            self.logo_button.setText(self.t("Seleccionar", "Browse"))
            self.output_name_label.setText(self.t("Nombre del archivo", "File name"))
            self.output_name.setPlaceholderText(self.t("Nombre del archivo", "File name"))
            labels = (
                (self.format_label, "Formato de salida", "Output format"),
                (self.fps_label, "Velocidad (FPS)", "Frame rate (FPS)"),
                (self.scale_label, "Escala", "Scale"),
                (self.logo_size_label, "Tamaño de marca", "Watermark size"),
                (self.start_label, "Inicio (segundos)", "Start (seconds)"),
                (self.end_label, "Fin (segundos)", "End (seconds)"),
            )
            for label, spanish, english in labels:
                label.setText(self.t(spanish, english))
            self.start.setPlaceholderText(self.t("Sin recorte", "No trim"))
            self.end.setPlaceholderText(self.t("Sin recorte", "No trim"))
            self.cancel_button.setText(self.t("Cancelar", "Cancel"))
            self.open_button.setText(self.t("Mostrar en carpeta", "Show in folder"))
            if not self.input_path:
                self.input_label.setText(self.t("Selecciona un video MP4", "Select an MP4 video"))
                self.status.setText(self.t("Selecciona un archivo MP4 para comenzar", "Select an MP4 file to begin"))
            if not self.output_dir:
                self.output_label.setText(self.t("Misma carpeta que el video", "Same folder as the video"))
            if not self.logo_path:
                self.logo_label.setText(self.t("No seleccionada", "Not selected"))
            self.update_format(self.format.currentText(), preserve=True)

        def choose_input(self):
            path, _ = QFileDialog.getOpenFileName(
                self, self.t("Seleccionar archivo de origen", "Select source file"), "", "Video MP4 (*.mp4)"
            )
            if path:
                self.input_path = path
                self.input_label.setText(Path(path).name)
                self.input_label.setToolTip(path)
                self.output_name.setText(Path(path).stem)
                self.status.setText(self.t("Archivo listo para exportar", "File ready to export"))
                self.convert_button.setEnabled(True)

        def choose_output(self):
            initial = self.output_dir or (
                str(Path(self.input_path).parent) if self.input_path else ""
            )
            path = QFileDialog.getExistingDirectory(
                self, self.t("Seleccionar carpeta de salida", "Select output folder"), initial
            )
            if path:
                self.output_dir = path
                self.output_label.setText(path)
                self.output_label.setToolTip(path)

        def update_format(self, value, preserve=False):
            previous = self.fps.currentText()
            original = previous in {"Originales", "Original"}
            self.output_suffix.setText(f".{value.lower()}")
            self.convert_button.setText(self.t(f"Exportar como {value}", f"Export as {value}"))
            self.fps.clear()
            if value == "GIF":
                self.fps.addItems(("10", "15"))
                self.fps.setCurrentText(previous if preserve and previous in {"10", "15"} else "15")
            else:
                self.fps.addItems((self.t("Originales", "Original"), "10", "15", "24", "30", "60"))
                if preserve and (original or self.fps.findText(previous) >= 0):
                    self.fps.setCurrentIndex(0 if original else self.fps.findText(previous))
                else:
                    self.fps.setCurrentText("30")

        def set_processing(self, active):
            for control in self.controls:
                control.setEnabled(not active)
            self.convert_button.setEnabled(not active and bool(self.input_path))
            self.cancel_button.setEnabled(active)
            self.open_button.setEnabled(not active and bool(self.output_file))

        def choose_logo(self):
            path, _ = QFileDialog.getOpenFileName(
                self, self.t("Seleccionar marca de agua", "Select watermark"), "", "PNG (*.png)"
            )
            if path:
                self.logo_path = path
                self.logo_label.setText(Path(path).name)
                self.logo_label.setToolTip(path)

        def convert(self):
            def number(field):
                return float(field.text().replace(",", ".")) if field.text().strip() else None

            output_name = self.output_name.text().strip()
            if not output_name or any(character in output_name for character in '\\/:*?"<>|'):
                QMessageBox.warning(
                    self, self.t("Nombre de archivo no válido", "Invalid file name"),
                    self.t("Escribe un nombre sin caracteres reservados.", "Enter a name without reserved characters.")
                )
                return
            output_dir = Path(self.output_dir) if self.output_dir else Path(self.input_path).parent
            output_format = self.format.currentText().lower()
            selected_fps = self.fps.currentText()
            options = dict(
                input_path=self.input_path,
                output_path=str(output_dir / f"{output_name}.{output_format}"),
                fps=None if selected_fps in {"Originales", "Original"} else float(selected_fps),
                resize=None if self.scale.currentText() == "Original" else float(self.scale.currentText()),
                start_time=number(self.start), end_time=number(self.end),
                logo_path=self.logo_path, logo_scale=self.logo_size.value() / 100,
                output_format=output_format,
            )
            self.set_processing(True)
            self.progress.setValue(0)
            self.progress.setActive(True)
            self.started_at = time.monotonic()
            self.eta.setText(self.t("Calculando tiempo restante…", "Calculating time remaining…"))
            self.status.setText(self.t("Procesando video…", "Processing video…"))
            self.thread = QThread(self)
            self.worker = Worker(options)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.progress.connect(self.update_progress)
            self.worker.succeeded.connect(self.finish)
            self.worker.failed.connect(self.fail)
            self.worker.cancelled.connect(self.cancelled)
            self.worker.succeeded.connect(self.thread.quit)
            self.worker.failed.connect(self.thread.quit)
            self.worker.cancelled.connect(self.thread.quit)
            self.thread.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self.thread_finished)
            self.thread.start()

        @Slot()
        def thread_finished(self):
            self.worker = self.thread = None
            self.set_processing(False)
            if self.closing:
                QTimer.singleShot(0, self.close)

        def closeEvent(self, event):
            if self.thread and self.thread.isRunning():
                event.ignore()
                if not self.closing:
                    self.closing = True
                    self.status.setText(self.t("Cancelando antes de cerrar…", "Cancelling before closing…"))
                    self.worker.cancel()
                return
            event.accept()

        def cancel_conversion(self):
            if self.worker:
                self.cancel_button.setEnabled(False)
                self.status.setText(self.t("Cancelando exportación…", "Cancelling export…"))
                self.worker.cancel()

        @Slot(int)
        def update_progress(self, value):
            self.progress.setValue(value)
            self.percent.setText(f"{value}%")
            if value >= 92:
                self.status.setText(self.t("Comprimiendo y guardando archivo…", "Compressing and saving file…"))
                self.eta.setText(self.t("Finalizando exportación…", "Finishing export…"))
                return
            if value >= 2:
                remaining = round((time.monotonic() - self.started_at) * (100 - value) / value)
                minutes, seconds = divmod(max(0, remaining), 60)
                self.eta.setText(
                    self.t(f"Tiempo estimado: {minutes} min {seconds:02d} s", f"Estimated time: {minutes} min {seconds:02d} s")
                    if minutes else self.t(f"Tiempo estimado: {seconds} s", f"Estimated time: {seconds} s")
                )

        @Slot(str)
        def finish(self, path):
            self.progress.setValue(100)
            self.progress.setActive(False)
            self.output_file = path
            self.status.setText(self.t(f"Exportación completada: {Path(path).name}", f"Export complete: {Path(path).name}"))
            elapsed = round(time.monotonic() - self.started_at)
            self.eta.setText(self.t(f"Tiempo total: {elapsed} s", f"Total time: {elapsed} s"))

        @Slot()
        def cancelled(self):
            self.progress.setActive(False)
            self.status.setText(self.t("Exportación cancelada", "Export cancelled"))
            self.eta.clear()
            self.progress.setValue(0)
            self.percent.setText("0%")

        @Slot(str)
        def fail(self, error):
            self.progress.setActive(False)
            self.status.setText(self.t("La exportación no se pudo completar", "The export could not be completed"))
            self.eta.clear()
            QMessageBox.critical(
                self, self.t("No se pudo exportar el archivo", "Could not export file"),
                self.localized_error(error),
            )

    STYLESHEET = """
        QWidget#root { background: #090b12; color: #f4f7fb; font: 10pt 'Segoe UI'; }
        QFrame#hero { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #171d2d, stop:1 #0e1220); border: 1px solid #29334a; border-radius: 18px; }
        QLabel#overline { color: #72809b; font-family: 'Consolas'; font-size: 8pt; letter-spacing: 2px; }
        QLabel#title { color: white; font-family: 'Segoe UI'; font-size: 22pt; font-weight: 600; }
        QLabel#subtitle, QLabel#status, QLabel#eta { color: #98a3b8; }
        QLabel#badge { color: #61e7ff; background: #102d39; border: 1px solid #24576a; border-radius: 12px; padding: 8px 13px; font-family: 'Segoe UI'; font-size: 8pt; font-weight: 600; }
        QFrame#card, QFrame#footer { background: #121724; border: 1px solid #29334a; border-radius: 16px; }
        QFrame#fileRow { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #181f30, stop:1 #151a28); border: 1px solid #2b3650; border-radius: 12px; }
        QLabel#sectionTitle { color: white; font-family: 'Segoe UI'; font-size: 14pt; font-weight: 600; padding-bottom: 3px; }
        QLabel#eyebrow { color: #6fdff3; font-family: 'Segoe UI'; font-size: 8pt; font-weight: 600; }
        QLabel#pathValue { color: #dce4f2; font-size: 10pt; }
        QLabel#fieldLabel { color: #aeb8ca; font-family: 'Segoe UI'; font-size: 9pt; font-weight: 600; }
        QLabel#percent { color: #61e7ff; font-weight: 600; }
        QPushButton { min-height: 38px; padding: 0 17px; border-radius: 9px; font-weight: 600; }
        QPushButton#primaryButton { color: #061014; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #43d9ff, stop:1 #7c8cff); border: none; }
        QPushButton#primaryButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #75e5ff, stop:1 #9ca7ff); }
        QPushButton#secondaryButton { color: #dce4f2; background: #20283b; border: 1px solid #34415e; }
        QPushButton#secondaryButton:hover { background: #29344d; border-color: #556782; }
        QPushButton:disabled { color: #667086; background: #171c29; border-color: #252c3d; }
        QComboBox, QLineEdit, QSpinBox { min-height: 38px; color: #eef3fb; background: #0d111b; border: 1px solid #34415e; border-radius: 9px; padding: 0 11px; selection-background-color: #4759a9; }
        QLineEdit#outputName { border-top-right-radius: 0; border-bottom-right-radius: 0; }
        QLabel#outputSuffix { min-height: 38px; color: #61e7ff; background: #171d2b; border: 1px solid #34415e; border-left: none; border-top-right-radius: 9px; border-bottom-right-radius: 9px; padding: 0 13px; font-weight: 600; }
        QComboBox:hover, QLineEdit:hover, QSpinBox:hover { border-color: #627394; }
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus { border: 1px solid #61e7ff; }
        QComboBox::drop-down { subcontrol-origin: border; subcontrol-position: top right; width: 32px; background: #0d111b; border: none; border-top-right-radius: 9px; border-bottom-right-radius: 9px; }
        QComboBox::down-arrow { image: url("__ARROW__"); width: 12px; height: 8px; }
        QComboBox QAbstractItemView { color: #eef3fb; background: #151b29; border: 1px solid #34415e; selection-background-color: #35436b; outline: none; }
    """

    STYLESHEET = STYLESHEET.replace("__ARROW__", (asset_dir / "chevron-down.svg").as_posix())
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Window()
    window.show()
    app.exec()


def main() -> None:
    if len(sys.argv) == 1:
        launch_gui()
        return

    parser = argparse.ArgumentParser(
        description="Convert MP4 video files to animated GIF or WebP.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", help="Path to the input MP4 file.")
    parser.add_argument(
        "-o", "--output", default=None, help="Path for the output animation."
    )
    parser.add_argument(
        "--format", choices=("gif", "webp"), default="gif", help="Output format."
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=None,
        help="Frames per second for the animation. Defaults to the video's original FPS.",
    )
    parser.add_argument(
        "--resize",
        type=float,
        default=None,
        help="Scale factor for the output (e.g. 0.5 for half size).",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Start time in seconds.",
    )
    parser.add_argument(
        "--end",
        type=float,
        default=None,
        metavar="SECONDS",
        help="End time in seconds.",
    )
    parser.add_argument(
        "--logo", default=None, help="Optional PNG logo placed in the top-right corner."
    )
    parser.add_argument(
        "--logo-size",
        type=int,
        default=20,
        metavar="PERCENT",
        help="Maximum logo width as a percentage of the video width.",
    )

    args = parser.parse_args()

    try:
        output = convert_mp4_to_gif(
            input_path=args.input,
            output_path=args.output,
            fps=args.fps,
            resize=args.resize,
            start_time=args.start,
            end_time=args.end,
            logo_path=args.logo,
            logo_scale=args.logo_size / 100,
            output_format=args.format,
        )
        print(f"File saved to: {output}")
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

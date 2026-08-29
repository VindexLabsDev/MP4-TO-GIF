import argparse
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from moviepy import CompositeVideoClip, ImageClip, VideoFileClip
from PIL import Image


def convert_mp4_to_gif(
    input_path: str,
    output_path: str | None = None,
    fps: float | None = None,
    resize: float | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    logo_path: str | None = None,
    logo_scale: float = 0.2,
    progress_callback=None,
) -> str:
    """
    Convert an MP4 file to GIF.

    Args:
        input_path: Path to the input MP4 file.
        output_path: Path for the output GIF. Defaults to same name as input.
        fps: Frames per second for the GIF. None preserves the video's FPS.
        resize: Scale factor (e.g. 0.5 = half size). None keeps original size.
        start_time: Start time in seconds. None starts from the beginning.
        end_time: End time in seconds. None goes until the end.

    Returns:
        Path to the generated GIF file.
    """
    input_path = Path(input_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() != ".mp4":
        raise ValueError(f"Input file must be an MP4 file, got: {input_path.suffix}")

    if output_path is None:
        output_path = input_path.with_suffix(".gif")
    else:
        output_path = Path(output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    last_progress = -1

    def report(value: int) -> None:
        nonlocal last_progress
        if progress_callback and value != last_progress:
            last_progress = value
            progress_callback(value)

    report(0)

    with VideoFileClip(str(input_path)) as clip:
        fps = fps or clip.fps
        if not 0 < fps <= 120:
            raise ValueError("FPS must be between 0 and 120.")
        if start_time is not None and start_time < 0:
            raise ValueError("Start time cannot be negative.")
        if end_time is not None and end_time > clip.duration:
            raise ValueError("End time cannot exceed the video duration.")
        if (start_time or 0) >= (end_time if end_time is not None else clip.duration):
            raise ValueError("End time must be greater than start time.")
        if start_time is not None or end_time is not None:
            clip = clip.subclipped(start_time, end_time)

        if resize is not None:
            if not (0 < resize <= 4):
                raise ValueError("Resize factor must be between 0 (exclusive) and 4.")
            clip = clip.resized(resize)

        logo = None
        if logo_path:
            logo_path = Path(logo_path).resolve()
            if not logo_path.is_file() or logo_path.suffix.lower() != ".png":
                raise ValueError("Logo must be an existing PNG file.")
            if not 0.05 <= logo_scale <= 1:
                raise ValueError("Logo size must be between 5% and 100%.")
            logo = ImageClip(str(logo_path)).with_duration(clip.duration)
            logo = logo.resized(width=clip.w * logo_scale)
            logo = logo.with_position((max(0, int(clip.w - logo.w - 16)), 16))
            clip = CompositeVideoClip([clip, logo])

        temporary = tempfile.NamedTemporaryFile(
            dir=output_path.parent, suffix=".gif", delete=False
        )
        temporary.close()
        temporary_path = Path(temporary.name)
        try:
            # ponytail: frames stay in memory; use an ffmpeg two-pass pipeline for long videos.
            frames = []
            total_frames = max(1, round(clip.duration * fps))
            for index, frame in enumerate(clip.iter_frames(fps=fps), start=1):
                frames.append(Image.fromarray(frame))
                report(min(70, round(index / total_frames * 70)))
            if not frames:
                raise ValueError("The selected video contains no frames.")
            samples = frames[::max(1, len(frames) // 32)]
            palette_source = Image.new("RGB", (160, 90 * len(samples)))
            for index, frame in enumerate(samples):
                palette_source.paste(frame.resize((160, 90)), (0, index * 90))
            palette = palette_source.quantize(colors=256)
            report(75)
            for index, frame in enumerate(frames):
                frames[index] = frame.quantize(
                    palette=palette, dither=Image.Dither.FLOYDSTEINBERG
                )
                report(75 + round((index + 1) / len(frames) * 15))
            report(92)
            frames[0].save(
                temporary_path,
                save_all=True,
                append_images=frames[1:],
                duration=round(1000 / fps),
                loop=0,
                optimize=False,
                disposal=2,
            )
            os.replace(temporary_path, output_path)
            report(100)
        finally:
            temporary_path.unlink(missing_ok=True)
            if logo:
                logo.close()

    return str(output_path)


def show_in_folder(path: str) -> None:
    """Open the system file browser with the generated file selected."""
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", path])
    else:
        subprocess.Popen(["xdg-open", str(Path(path).parent)])


def launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("MP4 → GIF")
    icon_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "app-icon.ico"
    if icon_path.exists():
        root.iconbitmap(str(icon_path))
    root.geometry("820x720")
    root.minsize(760, 680)
    root.configure(bg="#edf3f7")

    selected = tk.StringVar()
    selected_logo = tk.StringVar(value="Sin logo")
    selected_output = tk.StringVar(value="Automático (junto al MP4)")
    status = tk.StringVar(value="Selecciona un video MP4 para comenzar")
    progress_value = tk.IntVar(value=0)
    progress_text = tk.StringVar(value="0%")
    fps_value = tk.StringVar(value="Originales")
    resize_value = tk.StringVar(value="Original")
    logo_size = tk.IntVar(value=20)
    start_value = tk.StringVar()
    end_value = tk.StringVar()
    output_file: list[str] = []

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 11), padding=(18, 11))
    style.configure("Primary.TButton", background="#146c94", foreground="white")
    style.map("Primary.TButton", background=[("active", "#0f5676")])
    style.configure("TProgressbar", background="#3aa6b9", troughcolor="#d8e5eb")

    shell = tk.Frame(root, bg="#edf3f7", padx=42, pady=34)
    shell.pack(fill="both", expand=True)
    tk.Label(shell, text="MP4  ▸  GIF", bg="#edf3f7", fg="#113946",
             font=("Segoe UI Semibold", 26)).pack(anchor="w")
    tk.Label(shell, text="Convierte un video. Sin ajustes, sin vueltas.", bg="#edf3f7",
             fg="#526b75", font=("Segoe UI", 11)).pack(anchor="w", pady=(2, 24))

    file_card = tk.Frame(shell, bg="white", highlightbackground="#bfd1d9",
                         highlightthickness=1, padx=18, pady=16)
    file_card.pack(fill="x")
    file_label = tk.Label(file_card, textvariable=selected, bg="white", fg="#526b75",
                          anchor="w", font=("Segoe UI", 10))
    file_label.pack(side="left", fill="x", expand=True)

    def choose_file() -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar video", filetypes=[("Video MP4", "*.mp4")]
        )
        if path:
            selected.set(path)
            status.set("Listo para convertir")
            convert_button.config(state="normal")

    ttk.Button(file_card, text="Seleccionar archivo", command=choose_file).pack(side="right")

    output_card = tk.Frame(shell, bg="white", highlightbackground="#bfd1d9",
                           highlightthickness=1, padx=18, pady=12)
    output_card.pack(fill="x", pady=(10, 0))
    tk.Label(output_card, textvariable=selected_output, bg="white", fg="#526b75",
             anchor="w", font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)

    def choose_output() -> None:
        input_path = Path(selected.get()) if selected.get() else None
        path = filedialog.asksaveasfilename(
            title="Guardar GIF como",
            defaultextension=".gif",
            filetypes=[("Imagen GIF", "*.gif")],
            initialdir=input_path.parent if input_path else None,
            initialfile=f"{input_path.stem}.gif" if input_path else None,
        )
        if path:
            selected_output.set(path)

    ttk.Button(output_card, text="Elegir salida", command=choose_output).pack(side="right")

    logo_card = tk.Frame(shell, bg="white", highlightbackground="#bfd1d9",
                         highlightthickness=1, padx=18, pady=12)
    logo_card.pack(fill="x", pady=(10, 0))
    tk.Label(logo_card, textvariable=selected_logo, bg="white", fg="#526b75",
             anchor="w", font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)

    def choose_logo() -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar logo", filetypes=[("Imagen PNG", "*.png")]
        )
        if path:
            selected_logo.set(path)

    ttk.Button(logo_card, text="Agregar logo PNG", command=choose_logo).pack(side="right")

    settings = tk.Frame(shell, bg="#edf3f7")
    settings.pack(fill="x", pady=(18, 0))
    fps_setting = tk.Frame(settings, bg="#edf3f7")
    fps_setting.pack(side="left")
    tk.Label(fps_setting, text="FPS", bg="#edf3f7", fg="#113946",
             font=("Segoe UI Semibold", 10)).pack(anchor="w")
    ttk.Combobox(
        fps_setting,
        textvariable=fps_value,
        values=("Originales", "10", "15", "24", "30", "60"),
        width=12,
    ).pack(pady=(5, 0))

    resize_setting = tk.Frame(settings, bg="#edf3f7")
    resize_setting.pack(side="left", padx=(26, 0))
    tk.Label(resize_setting, text="Escala", bg="#edf3f7", fg="#113946",
             font=("Segoe UI Semibold", 10)).pack(anchor="w")
    ttk.Combobox(
        resize_setting,
        textvariable=resize_value,
        values=("Original", "0.25", "0.5", "0.75", "1", "1.5", "2"),
        width=10,
    ).pack(pady=(5, 0))

    logo_setting = tk.Frame(settings, bg="#edf3f7")
    logo_setting.pack(side="left", padx=(26, 0))
    tk.Label(logo_setting, text="Tamaño del logo (%)", bg="#edf3f7", fg="#113946",
             font=("Segoe UI Semibold", 10)).pack(anchor="w")
    ttk.Spinbox(logo_setting, from_=5, to=100, textvariable=logo_size, width=10).pack(
        pady=(5, 0)
    )

    trim_settings = tk.Frame(shell, bg="#edf3f7")
    trim_settings.pack(fill="x", pady=(16, 0))
    for label, variable in (("Inicio (segundos)", start_value), ("Fin (segundos)", end_value)):
        setting = tk.Frame(trim_settings, bg="#edf3f7")
        setting.pack(side="left", padx=(0, 26))
        tk.Label(setting, text=label, bg="#edf3f7", fg="#113946",
                 font=("Segoe UI Semibold", 10)).pack(anchor="w")
        ttk.Entry(setting, textvariable=variable, width=15).pack(pady=(5, 0))

    progress = ttk.Progressbar(
        shell, mode="determinate", maximum=100, variable=progress_value
    )
    progress.pack(fill="x", pady=(22, 9))
    progress_status = tk.Frame(shell, bg="#edf3f7")
    progress_status.pack(fill="x")
    tk.Label(progress_status, textvariable=status, bg="#edf3f7", fg="#526b75",
             font=("Segoe UI", 10)).pack(side="left")
    tk.Label(progress_status, textvariable=progress_text, bg="#edf3f7", fg="#146c94",
             font=("Segoe UI Semibold", 10)).pack(side="right")

    actions = tk.Frame(shell, bg="#edf3f7")
    actions.pack(fill="x", pady=(22, 0))

    def finish(path: str | None = None, error: Exception | None = None) -> None:
        convert_button.config(state="normal")
        if error:
            status.set("No se pudo convertir el video")
            messagebox.showerror("Error de conversión", str(error))
            return
        output_file[:] = [path] if path else []
        status.set(f"GIF creado: {Path(path).name}")
        open_button.config(state="normal")

    def convert() -> None:
        try:
            input_file = selected.get()
            logo = None if selected_logo.get() == "Sin logo" else selected_logo.get()
            chosen_fps = None if fps_value.get() == "Originales" else float(fps_value.get())
            chosen_resize = None if resize_value.get() == "Original" else float(resize_value.get())
            chosen_logo_size = logo_size.get() / 100
            chosen_start = float(start_value.get()) if start_value.get().strip() else None
            chosen_end = float(end_value.get()) if end_value.get().strip() else None
            chosen_output = (
                None
                if selected_output.get() == "Automático (junto al MP4)"
                else selected_output.get()
            )
        except (ValueError, tk.TclError):
            messagebox.showerror("Ajustes inválidos", "Revisa FPS, escala, inicio, fin y logo.")
            return

        convert_button.config(state="disabled")
        open_button.config(state="disabled")
        status.set("Convirtiendo…")
        progress_value.set(0)
        progress_text.set("0%")

        def update_progress(value: int) -> None:
            progress_value.set(value)
            progress_text.set(f"{value}%")

        def work() -> None:
            try:
                path = convert_mp4_to_gif(
                    input_file,
                    output_path=chosen_output,
                    fps=chosen_fps,
                    resize=chosen_resize,
                    start_time=chosen_start,
                    end_time=chosen_end,
                    logo_path=logo,
                    logo_scale=chosen_logo_size,
                    progress_callback=lambda value: root.after(
                        0, update_progress, value
                    ),
                )
                root.after(0, finish, path, None)
            except Exception as error:
                root.after(0, finish, None, error)

        threading.Thread(target=work, daemon=True).start()

    convert_button = ttk.Button(actions, text="Convertir a GIF", style="Primary.TButton",
                                command=convert, state="disabled")
    convert_button.pack(side="left")
    open_button = ttk.Button(actions, text="Ver archivo",
                             command=lambda: show_in_folder(output_file[0]), state="disabled")
    open_button.pack(side="left", padx=10)

    root.mainloop()


def main() -> None:
    if len(sys.argv) == 1:
        launch_gui()
        return

    parser = argparse.ArgumentParser(
        description="Convert MP4 video files to GIF.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", help="Path to the input MP4 file.")
    parser.add_argument(
        "-o", "--output", default=None, help="Path for the output GIF file."
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=None,
        help="Frames per second for the GIF. Defaults to the video's original FPS.",
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
        )
        print(f"GIF saved to: {output}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

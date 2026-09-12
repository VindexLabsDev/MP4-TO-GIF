from pathlib import Path
from moviepy import ColorClip, concatenate_videoclips
from PIL import Image

from converter import ConversionCancelled, convert_mp4_to_gif


def test_conversion() -> None:
    path = Path(".test-output")
    path.mkdir(exist_ok=True)
    video = path / "input.mp4"
    logo = path / "logo.png"
    concatenate_videoclips([
        ColorClip((64, 48), color=(20, 40, 80), duration=0.2),
        ColorClip((64, 48), color=(80, 40, 20), duration=0.2),
    ]).write_videofile(
        str(video), fps=5, logger=None
    )
    Image.new("RGBA", (20, 10), (255, 0, 0, 255)).save(logo)
    progress = []
    output = convert_mp4_to_gif(
        str(video), logo_path=str(logo), progress_callback=progress.append
    )
    assert Path(output).is_file()
    assert progress[0] == 0 and progress[-1] == 100
    with Image.open(output) as gif:
        colors = gif.convert("RGB").getcolors(maxcolors=256)
        assert colors and any(
            all(abs(actual - expected) <= 5 for actual, expected in zip(color, (20, 40, 80)))
            for _, color in colors
        )
        assert any(red > 240 and green < 10 and blue < 10 for _, (red, green, blue) in colors)
        duration = 0
        for frame in range(gif.n_frames):
            gif.seek(frame)
            duration += gif.info["duration"]
        assert duration == 400

    webp_progress = []
    webp_output = convert_mp4_to_gif(
        str(video), output_format="webp", logo_path=str(logo),
        progress_callback=webp_progress.append
    )
    assert webp_progress[0] == 0 and webp_progress[-1] == 100
    with Image.open(webp_output) as webp:
        assert webp.format == "WEBP" and webp.n_frames > 1
        colors = webp.convert("RGB").getcolors(maxcolors=256)
        assert colors and any(red > 240 and green < 10 and blue < 10 for _, (red, green, blue) in colors)

    try:
        convert_mp4_to_gif(str(video), fps=0)
        raise AssertionError("FPS 0 was accepted")
    except ValueError:
        pass

    mismatched_output = convert_mp4_to_gif(
        str(video), str(path / "selected.gif"), output_format="webp"
    )
    assert Path(mismatched_output).suffix == ".webp"
    with Image.open(mismatched_output) as webp:
        assert webp.format == "WEBP"

    cancelled_output = path / "cancelled.gif"
    try:
        convert_mp4_to_gif(
            str(video), str(cancelled_output), cancel_callback=lambda: True
        )
        raise AssertionError("Cancellation was ignored")
    except ConversionCancelled:
        assert not cancelled_output.exists()


if __name__ == "__main__":
    test_conversion()
    print("OK")

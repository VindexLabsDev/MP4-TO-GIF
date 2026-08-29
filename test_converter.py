from pathlib import Path
from moviepy import ColorClip
from PIL import Image

from converter import convert_mp4_to_gif


def test_conversion() -> None:
    path = Path(".test-output")
    path.mkdir(exist_ok=True)
    video = path / "input.mp4"
    logo = path / "logo.png"
    ColorClip((64, 48), color=(20, 40, 80), duration=0.2).write_videofile(
        str(video), fps=5, logger=None
    )
    Image.new("RGBA", (20, 10), (255, 0, 0, 255)).save(logo)
    progress = []
    output = convert_mp4_to_gif(
        str(video), logo_path=str(logo), progress_callback=progress.append
    )
    assert Path(output).is_file()
    assert progress[0] == 0 and progress[-1] == 100


if __name__ == "__main__":
    test_conversion()
    print("OK")

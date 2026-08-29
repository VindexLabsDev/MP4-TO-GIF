$ErrorActionPreference = "Stop"
if (!(Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller==6.22.2
if ($LASTEXITCODE) { exit $LASTEXITCODE }
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --icon app-icon.ico --add-data "app-icon.ico;." --copy-metadata imageio --workpath .pyinstaller-build --distpath dist --name "MP4-to-GIF" converter.py
exit $LASTEXITCODE

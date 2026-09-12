$ErrorActionPreference = "Stop"
$buildTemp = Join-Path $PSScriptRoot ".build-temp"
New-Item -ItemType Directory -Force $buildTemp | Out-Null
$env:TEMP = $buildTemp
$env:TMP = $buildTemp
if (!(Test-Path .venv\Scripts\python.exe)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m ensurepip --upgrade
if ($LASTEXITCODE) { exit $LASTEXITCODE }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller==6.22.2
if ($LASTEXITCODE) { exit $LASTEXITCODE }
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --icon app-icon.ico --add-data "app-icon.ico;." --add-data "chevron-down.svg;." --copy-metadata imageio --workpath .pyinstaller-build --distpath dist --name "MP4-to-GIF" converter.py
if (!$LASTEXITCODE) { Remove-Item $buildTemp, .pyinstaller-build, MP4-to-GIF.spec -Recurse -Force -ErrorAction SilentlyContinue }
exit $LASTEXITCODE

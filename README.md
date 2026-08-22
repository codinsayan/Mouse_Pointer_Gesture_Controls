# Gesture Controls

Gesture Controls is a Windows-first, local webcam hand-landmark prototype. The
current code includes **Iterations 1 and 2**: it displays a mirrored camera
preview, one detected hand, a configurable active region, and a smoothed dry-run
cursor target. It cannot move the operating-system pointer, click, scroll, drag,
or generate keyboard events.

Camera frames remain in memory only. The application contains no recording,
frame-writing, upload, or OS-input code and runs visibly in the foreground.

## Requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.12 (development only; standalone packaging is Iteration 12)
- A webcam permitted under Windows **Settings > Privacy & security > Camera**
- The official MediaPipe Hand Landmarker model asset

Python 3.13/3.14 are not the tested development target. Dependency versions are
pinned to the combination verified in this repository. MediaPipe 0.10.21 is used
with the current Hand Landmarker Tasks API because newer releases disclose SDK
performance/utilization telemetry and this project forbids telemetry.

## Windows setup

From PowerShell in the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

If PowerShell blocks activation, you can run every command through the virtual
environment interpreter without changing execution policy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Download Google's official model bundle to the expected local path:

```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "assets/models/hand_landmarker.task"
```

The model is deliberately excluded from Git. The upstream API and model guidance
is on the [MediaPipe Hand Landmarker documentation](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python).

## Run

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m gesture_controls.main
```

Use another camera with `--camera 1`, or another model path with
`--model C:\path\to\hand_landmarker.task`. Press `Q`, `Esc`, or close the preview
window to stop. `Ctrl+C` also performs a clean shutdown from the terminal.

The overlay reports camera state, detection state, handedness, handedness
confidence, processed FPS, dry-run state, and normalized smoothed cursor
coordinates. The blue rectangle is the camera active region and the magenta
cross is the dry-run output target.

Iteration 2's active region (`0.12..0.88` horizontally and `0.10..0.90`
vertically), smoothing time constant (`0.08` seconds), and normalized minimum
movement (`0.002`) are provisional configuration defaults. They have automated
math coverage but have not been calibrated on representative webcams.

## Test

Ordinary tests do not access a webcam:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m pip check
```

There is no build command yet. PyInstaller packaging belongs to Iteration 12.

## Troubleshooting

- **Model not found:** download the official `.task` file using the command above
  or supply `--model`.
- **Camera cannot open:** close other camera applications, confirm the index, and
  enable Windows camera access for desktop applications.
- **Camera stops:** reconnect it and restart the foreground application.
- **Tracker initialization fails:** confirm Python 3.12, reinstall the pinned
  requirements, and replace a possibly incomplete model download.

Project status and actual verification results are maintained in
[`docs/IMPLEMENTATION_DETAILS.md`](docs/IMPLEMENTATION_DETAILS.md).

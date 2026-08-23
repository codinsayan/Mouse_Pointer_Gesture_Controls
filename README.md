# Gesture Controls

Gesture Controls is a Windows-first, local webcam hand-landmark prototype. The
current code includes **Iterations 1 through 8**: it displays a mirrored camera
preview, tracks one hand, recognizes configured gestures, and provides a
startup-disabled safety gate around optional local OS input.

Camera frames remain in memory only. The application contains no recording,
frame-writing, upload, telemetry, or remote-inference code and runs visibly in
the foreground. OS input is dry-run by default and requires two explicit steps.

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
confidence, processed FPS, safety/controller state, and normalized smoothed cursor
coordinates. The blue rectangle is the camera active region and the magenta
cross is the dry-run output target.

Iteration 2's active region (`0.12..0.88` horizontally and `0.10..0.90`
vertically), smoothing time constant (`0.08` seconds), and normalized minimum
movement (`0.002`) are provisional configuration defaults. They have automated
math coverage but have not been calibrated on representative webcams.

Iteration 3 maps thumb–index pinch to one dry-run left click and thumb–middle
pinch to one dry-run double-click action. Thumb–middle has priority and suppresses
left click during conflicts. Holding either pinch does not repeat its count. The
cursor freezes at candidate entry and resumes immediately after release through
reseeded smoothing. Provisional defaults for both gestures are activation `0.30`,
release `0.42`, activation/release holds `0.03 s`, and debounce `0.06 s`. These
values are configuration defaults, not final calibrated thresholds.

Iteration 4 maps thumb–little pinch to one dry-run right click. Current click
priority is thumb–little right click, thumb–middle double click, then thumb–index
left click. Right click is first so crossing near the middle finger while reaching
the little finger cannot become a double click. It uses provisional activation `0.30`, release `0.42`,
activation/release holds `0.03 s`, and debounce `0.06 s`. Holding cannot repeat.

Iteration 5 uses two distinct poses. Extend index+middle and fold ring+little,
then move up/down for vertical scrolling. Extend middle+ring and fold index+little,
then move left/right for horizontal scrolling. Each pose fixes its axis and
off-axis movement is ignored, preventing diagonal mixed output.
Scrolling suppresses click recognition and freezes the cursor until release. Provisional defaults are
extension activation/release `0.18/0.10`, folded activation/release `0.10/0.18`,
activation/release holds `0.06/0.05 s`, one step per `0.08` hand-size units, and
at most three steps per frame. These values require webcam calibration.

Iteration 6 maps a closed fist held for an additional `0.25 s` to a dry-run drag.
All four non-thumb fingers must be folded; the thumb position is ignored. The
cursor freezes while the fist is validated, then relative palm movement drives
the target from its pre-drag position with a finer `0.0005` movement threshold.
Opening the fist ends the drag once. Tracking loss, conflict, reset, exception,
and shutdown also force one safe end transition. Current conflict priority is
scroll, fist drag, thumb+little right click, thumb+middle double click, then
thumb+index left click. All thresholds are provisional; no real mouse-down or
mouse-up is sent unless the Iteration 8 real-input procedure below is used.

For dry-run zoom, keep index, middle, and little open, bring thumb and ring within
the activation span, and hold briefly; the ring is free to bend naturally.
Spread thumb and ring to produce zoom-in steps; contract them to produce zoom-out
steps. Moving beyond the release span exits zoom. Provisional defaults are span
activation/release `0.45/0.85`, 60/50 ms pose entry/release, one step per `0.08`
normalized span change, and at most three steps per frame. Zoom suppresses clicks
and cursor movement while claimed. In enabled real-input mode, zoom steps become
local `Ctrl`+`+` or `Ctrl`+`-` operations.

## Safety controls and optional real input

The normal command remains dry-run. Press `E` in the preview or global
`Ctrl+Alt+G` to enable/disable gesture processing without generating real input:

```powershell
.\.venv\Scripts\python.exe -m gesture_controls.main --config settings.json
```

Real mouse and zoom output requires the non-persistent flag below. The application
still starts **disabled**; show an accepted, sufficiently confident hand, then
press `E` in the preview or global `Ctrl+Alt+G`:

```powershell
.\.venv\Scripts\python.exe -m gesture_controls.main --config settings.json --enable-real-input
```

Safety controls:

- `E`: foreground toggle between enabled and disabled.
- `Ctrl+Alt+G`: global toggle, even when another window has focus.
- `P`: foreground emergency pause.
- `Ctrl+Alt+Shift+G`: global emergency pause.
- Hold all four non-thumb fingers open for about 350 ms: open-palm pause.
- Move PyAutoGUI's cursor to a screen corner: PyAutoGUI failsafe; the application
  catches the output failure, pauses, and attempts to release app-owned input.

Tracking loss, wrong dominant hand, missing/below-threshold confidence,
calibration, output failure, exception, camera failure, window close, and
shutdown release an app-held drag and block further events. Tracking recovery
does not resume automatically; explicitly enable again. The default runtime
threshold is `minimum_runtime_hand_confidence: 0.5`. MediaPipe Tasks exposes the
handedness category score here, not a distinct per-frame tracking score.

Ordinary pointer movement requires the index finger to be raised. Its
`0.18/0.10` activation/release hysteresis has no time hold, preserving pointer
responsiveness. Fist drag uses its relative palm mapping instead.

## Local settings profiles

Create a complete validated profile without opening the camera:

```powershell
.\.venv\Scripts\python.exe -m gesture_controls.main --write-default-config settings.json
```

Edit `settings.json`, then run with it:

```powershell
.\.venv\Scripts\python.exe -m gesture_controls.main --config settings.json
```

The profile is schema-versioned. Unknown fields, wrong JSON types, invalid
threshold ordering, and invalid regions produce readable errors. `dominant_hand`
accepts `"any"`, `"left"`, or `"right"` and refers to MediaPipe's reported label.
`cursor_sensitivity` accepts `0.1..3.0`; higher values amplify movement around
screen center. Existing smoothing and gesture thresholds are also settings.

`--camera` and `--model` override profile values for one run and are not written
back by calibration:

```powershell
.\.venv\Scripts\python.exe -m gesture_controls.main --config settings.json --camera 1
```

## Cursor calibration

In the preview:

1. Press `C` to start calibration.
2. Move the index fingertip around the full comfortable control area for at
   least 60 processed frames, covering both width and height.
3. Press `Enter` to validate and apply, or `X` to cancel.

Normal gestures are suspended while collecting. Calibration retains normalized
index-tip coordinates only and never frames. It uses robust 5th/95th percentiles,
coverage validation, and bounded padding. With `--config`, a successful apply
atomically updates that profile. Without a profile, calibration lasts only for
the current session.

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
- **Control will not enable:** keep the configured dominant hand visible and
  check the overlay's confidence and safety reason.
- **Global hotkey registration fails:** close the application already using
  `Ctrl+Alt+G`, then restart Gesture Controls. Real input is not started without
  both safety hotkeys.
- **Tracking recovered but control remains paused:** this is intentional; press
  `E` or `Ctrl+Alt+G` to re-enable explicitly.

Project status and actual verification results are maintained in
[`docs/IMPLEMENTATION_DETAILS.md`](docs/IMPLEMENTATION_DETAILS.md).

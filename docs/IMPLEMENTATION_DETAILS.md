# Implementation Details

## Project Objective

Build a local-only, Windows-first one-hand gesture controller that is safe by
default, modular, testable without a webcam, and eventually distributable without
a separate Python installation.

## Current Architecture Summary

The foreground OpenCV loop uses MediaPipe Hand Landmarker Tasks in synchronous
`VIDEO` mode. Configuration, camera, tracking, neutral landmarks, deterministic
cursor mapping/smoothing, status rendering, and FPS measurement are separate
modules. Iteration 2 visualizes normalized dry-run cursor output; there is no
OS-input dependency or behavior.

## Iterations

| Iteration | Objective | Status | Main result | Document |
| --------- | --------- | ------ | ----------- | -------- |
| 01 | Foundation and webcam landmark prototype | Complete | Local mirrored preview, one-hand Tasks tracking, overlay, tests | [Iteration 01](iterations/ITERATION_01_FOUNDATION.md) |
| 02 | Cursor mapping and smoothing | Complete | Mapped, smoothed, thresholded dry-run target | [Iteration 02](iterations/ITERATION_02_POINTER_MOVEMENT.md) |
| 03 | Left-click recognition | Not started | Awaiting approval | — |
| 04 | Right-click recognition | Not started | Awaiting approval | — |
| 05 | Scrolling | Not started | Awaiting approval | — |
| 06 | Dragging and state-machine hardening | Not started | Awaiting approval | — |
| 07 | Calibration and settings | Not started | Awaiting approval | — |
| 08 | Safety and tracking-loss recovery | Not started | Awaiting approval | — |
| 09 | UI and system tray | Not started | Awaiting approval | — |
| 10 | Automated and real-world testing | Not started | Awaiting approval | — |
| 11 | Performance optimization | Not started | Awaiting approval | — |
| 12 | Packaging and Windows release | Not started | Awaiting approval | — |

## Current Feature Status

- Repository foundation: complete.
- Webcam preview and one-hand landmarks: implemented; tracker initialization
  verified, interactive webcam visualization awaiting a local manual check.
- Cursor mapping and smoothing: complete; dry-run preview only.
- Gesture recognition and OS mouse events: intentionally absent.
- Packaging: deferred to Iteration 12.

## Important Technical Decisions

- Baseline Python: 3.12.4 in the verified environment.
- Initial inference mode: synchronous `VIDEO`, providing a naturally bounded
  pipeline and monotonically timestamped tracking.
- Model asset: official `hand_landmarker.task` supplied under `assets/models/`;
  no unofficial binary is committed.
- Verified pins: MediaPipe 0.10.21, NumPy 1.26.4, OpenCV Contrib 4.11.0.86,
  and pytest 9.1.1. OpenCV Contrib is the sole `cv2` provider.
- MediaPipe 0.10.21 retains the current Hand Landmarker Tasks API and is pinned
  because upstream reports place later SDK telemetry after this release.
- Cursor coordinates remain normalized through Iteration 2. Mapping uses a
  configurable camera region, elapsed-time exponential smoothing, a normalized
  movement threshold, and tracking-loss reset.
- Iteration 2 intentionally has no screen-size discovery, PyAutoGUI, or real
  input controller. The math can be calibrated before OS input is introduced.

## Known Bugs

No unresolved application bugs. Resolved setup/test issues are in the Iteration
1 document.

## Pending Risks

- Webcam capture, overlay visibility, handedness behavior after mirroring, and
  real processed FPS require an interactive manual camera check.
- Actual FPS and latency depend on camera and hardware and are unmeasured.
- Cursor defaults are provisional and require real webcam calibration. Index-tip
  raised-state gating belongs to later gesture recognition; Iteration 2 maps the
  tip whenever a hand is tracked.
- The current MediaPipe privacy notice describes SDK utilization metrics for new
  releases. The selected pre-change 0.10.21 pin reduces this risk, but a network
  audit has not independently proven that version emits no traffic.
- The model is downloaded separately and excluded from Git; releases will need
  a documented model redistribution or installation strategy.

## Setup and Run Commands

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "assets/models/hand_landmarker.task"
.\.venv\Scripts\python.exe -m gesture_controls.main
```

## Test and Build Commands

- Tests: `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider`
- Syntax: `.\.venv\Scripts\python.exe -m compileall -q src tests`
- Dependencies: `.\.venv\Scripts\python.exe -m pip check`
- Build: not implemented until Iteration 12.

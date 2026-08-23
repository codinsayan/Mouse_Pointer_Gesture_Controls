# Implementation Details

## Project Objective

Build a local-only, Windows-first one-hand gesture controller that is safe by
default, modular, testable without a webcam, and eventually distributable without
a separate Python installation.

## Current Architecture Summary

The foreground OpenCV loop uses MediaPipe Hand Landmarker Tasks in synchronous
`VIDEO` mode. Configuration, camera, tracking, neutral landmarks, deterministic
cursor mapping/smoothing, status rendering, and FPS measurement are separate
modules. Iterations 3–4 add scale-independent thumb–index, thumb–middle, and
thumb–little features, temporal pinch recognizers, click-priority coordination,
and cursor guarding.
Iteration 5 adds normalized finger extension/palm motion, a two-finger scroll
state machine, and scroll-first gesture-family conflict resolution. Cursor,
click, and scroll output remain dry-run; there is no OS-input dependency or behavior.

## Iterations

| Iteration | Objective | Status | Main result | Document |
| --------- | --------- | ------ | ----------- | -------- |
| 01 | Foundation and webcam landmark prototype | Complete | Local mirrored preview, one-hand Tasks tracking, overlay, tests | [Iteration 01](iterations/ITERATION_01_FOUNDATION.md) |
| 02 | Cursor mapping and smoothing | Complete | Mapped, smoothed, thresholded dry-run target | [Iteration 02](iterations/ITERATION_02_POINTER_MOVEMENT.md) |
| 03 | Left-click recognition | Complete | Thumb–index left and thumb–middle double click | [Iteration 03](iterations/ITERATION_03_GESTURES.md) |
| 04 | Thumb–little right-click recognition | Complete | Prioritized transition-only dry-run right click | [Iteration 04](iterations/ITERATION_04_RIGHT_CLICK.md) |
| 05 | Scrolling | Complete | Exclusive scale-independent two-axis dry-run scrolling | [Iteration 05](iterations/ITERATION_05_SCROLLING.md) |
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
- Left/double-click recognition: complete; dry-run only.
- Thumb–little right-click recognition: complete; dry-run only.
- Two-finger vertical and horizontal scrolling: complete; dry-run only.
- Operating-system mouse events: intentionally absent; gesture actions remain dry-run only.
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
- Click pinch distances are divided by palm scale. Recognition uses configurable
  hysteresis, timed activation/release, cooldown, and explicit transitions.
- Clicks remain dry-run through Iteration 3. Holding an active pinch does not
  repeat, and tracking loss resets recognition without an activation.
- Candidate pinches freeze cursor output before finger articulation. Release
  immediately reseeds smoothing from the frozen output before live input resumes.
- Thumb–middle pinch produces one double-click action and has priority over
  thumb–index left click. Both use 30 ms provisional holds and 60 ms debounce.
- Post-release delay is zero; smoothing reseeds immediately from frozen output.
- Thumb–little pinch produces one right-click action. Click conflict priority is
  right, double, then left; this prevents the path toward the little fingertip
  from being claimed as a thumb–middle double click.
- Vertical scrolling requires index+middle extended and ring+little folded;
  horizontal scrolling requires middle+ring extended and index+little folded.
  Pose entry/release use hysteresis and timed validation, and movement uses a
  stable two-axis wrist/MCP anchor normalized by palm scale.
- Scroll gestures have priority over all clicks. Claimed frames reset click
  recognizers, freeze cursor output, and release through smoothing reseed.
- Scroll displacement is quantized without an unbounded queue and capped at
  three dry-run steps per processed frame. Defaults remain provisional.
- The finger pose binds the scroll axis before movement; off-axis displacement is
  ignored, preventing diagonal motion from mixing horizontal and vertical steps.

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
- Left-pinch thresholds and timing defaults are provisional and need manual
  testing across hand sizes, pose angles, lighting, and webcam quality.
- Thumb–middle double click, conflict priority, and immediate cursor resume have
  deterministic coverage but still require interactive usability testing.
- Thumb–little thresholds and priority behavior require representative webcam
  testing, especially when adjacent fingers move together.
- Both two-finger pose thresholds, vertical/horizontal direction conventions,
  dead zone, and step sensitivity require representative webcam testing.
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

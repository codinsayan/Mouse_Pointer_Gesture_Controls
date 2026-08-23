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
click, and scroll output remain dry-run. Iteration 6 adds a scale-independent
fist pose, a separate armed/dragging state machine, relative palm-motion cursor
tracking, one-shot release safety, and bounded thumb-ring expansion/contraction
zoom. There is no OS-input dependency or behavior. Iteration 7 adds strict local
JSON profiles, reported-hand filtering, cursor sensitivity, and transient
landmark-only cursor calibration with optional explicit persistence.

## Iterations

| Iteration | Objective | Status | Main result | Document |
| --------- | --------- | ------ | ----------- | -------- |
| 01 | Foundation and webcam landmark prototype | Complete | Local mirrored preview, one-hand Tasks tracking, overlay, tests | [Iteration 01](iterations/ITERATION_01_FOUNDATION.md) |
| 02 | Cursor mapping and smoothing | Complete | Mapped, smoothed, thresholded dry-run target | [Iteration 02](iterations/ITERATION_02_POINTER_MOVEMENT.md) |
| 03 | Left-click recognition | Complete | Thumb–index left and thumb–middle double click | [Iteration 03](iterations/ITERATION_03_GESTURES.md) |
| 04 | Thumb–little right-click recognition | Complete | Prioritized transition-only dry-run right click | [Iteration 04](iterations/ITERATION_04_RIGHT_CLICK.md) |
| 05 | Scrolling | Complete | Exclusive scale-independent two-axis dry-run scrolling | [Iteration 05](iterations/ITERATION_05_SCROLLING.md) |
| 06 | Dragging and state-machine hardening | Complete | Held-fist drag plus bounded thumb-ring dry-run zoom | [Iteration 06](iterations/ITERATION_06_DRAGGING.md) |
| 07 | Calibration and settings | Complete | Validated local profiles and robust interactive cursor calibration | [Iteration 07](iterations/ITERATION_07_CALIBRATION_AND_SETTINGS.md) |
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
- Held-fist dragging: complete; precise dry-run target and transition
  counters only.
- Thumb-ring expansion/contraction zoom: complete; bounded dry-run steps only.
- Versioned local settings profiles: complete; strict validation and atomic
  explicit writes.
- Reported hand preference and cursor sensitivity: complete; webcam behavior
  still needs representative manual checks.
- Cursor-region calibration: complete; session apply and optional selected-profile
  persistence using transient normalized coordinates only.
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
- A fist requires all four non-thumb finger extension ratios at or below `0.10`;
  release hysteresis retains it through `0.18`. Pose entry/release use 60/50 ms
  validation, followed by an additional 250 ms drag-intent hold.
- Gesture conflict priority is scroll, fist drag, thumb-little right click,
  thumb-middle double click, then thumb-index left click.
- Cursor output freezes while drag is a candidate or armed. At drag start the
  smoother resumes from the frozen output, and the movement threshold drops from
  `0.002` to `0.0005` for fine control while retaining elapsed-time smoothing.
- Drag start/end are transitions rather than per-frame actions. Release, tracking
  loss, conflict, reset, exception, and shutdown clear active drag state once.
- Zoom uses normalized thumb-ring span with a distinct pose: index, middle, and
  little extension must each be at least `0.12`, while the ring remains free to
  articulate. A `0.08` retention threshold provides pose hysteresis.
- Zoom activates at span `0.45` or below, releases above `0.85`, validates entry
  and release for 60/50 ms, and quantizes each `0.08` span change into a signed
  step capped at three per frame without retaining a backlog. Expansion is zoom
  in and contraction is zoom out.
- Conflict priority is scroll, fist drag, zoom, right click, double click, then
  left click. Claimed zoom frames reset click recognition and freeze the cursor.
- Settings profiles use schema version 1 and standard-library JSON. Unknown root
  or setting fields and wrong types are rejected before `AppConfig` validates
  ranges and cross-field ordering. Writes are atomic replacements.
- CLI camera/model options override profile values at runtime and are deliberately
  not persisted when calibration updates a selected profile.
- `dominant_hand` is `any`, `left`, or `right` and matches MediaPipe's reported
  label case-insensitively. A missing label is rejected for a specific preference.
- Cursor sensitivity scales mapped coordinates around screen center and relative
  fist-drag displacement; the validated range is `0.1..3.0`.
- Calibration retains only normalized index-tip points. Defaults require 60
  samples, 5th/95th percentile bounds, at least `0.25` span on both axes, and 5%
  padding. Normal gesture processing is suspended during collection.

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
- Fist folded thresholds, the additional 250 ms intent hold, smoothing, and
  `0.0005` drag movement threshold require interactive tests for text selection
  and icon movement. Camera FPS and perceived drag latency remain unmeasured.
- Zoom pose/span thresholds, direction convention, and step sensitivity require
  representative webcam usability testing.
- Mirrored-feed handedness labels and interactive calibration ergonomics require
  a live webcam check. Incorrect preferred-hand selection safely ignores tracking.
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
.\.venv\Scripts\python.exe -m gesture_controls.main --write-default-config settings.json
.\.venv\Scripts\python.exe -m gesture_controls.main --config settings.json
```

## Test and Build Commands

- Tests: `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider`
- Syntax: `.\.venv\Scripts\python.exe -m compileall -q src tests`
- Dependencies: `.\.venv\Scripts\python.exe -m pip check`
- Build: not implemented until Iteration 12.

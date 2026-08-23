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
click, and scroll output were dry-run through that iteration. Iteration 6 adds a scale-independent
fist pose, a separate armed/dragging state machine, relative palm-motion cursor
tracking, one-shot release safety, and bounded thumb-ring expansion/contraction
zoom. Those results remained preview-only through Iteration 6. Iteration 7 adds strict local
JSON profiles, reported-hand filtering, cursor sensitivity, and transient
landmark-only cursor calibration with optional explicit persistence. Iteration 8
adds a startup-disabled safety state machine, dry-run/fake/PyAutoGUI controller
boundary, global and foreground emergency controls, open-palm pause, tracking-
loss latching, and guaranteed best-effort release of app-owned inputs.

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
| 08 | Safety and tracking-loss recovery | Complete | Startup-disabled OS-input gate, emergency pause, and fail-safe release | [Iteration 08](iterations/ITERATION_08_SAFETY_AND_TRACKING_LOSS.md) |
| 09 | UI and system tray | Not started | Awaiting approval | — |
| 10 | Automated and real-world testing | Not started | Awaiting approval | — |
| 11 | Performance optimization | Not started | Awaiting approval | — |
| 12 | Packaging and Windows release | Not started | Awaiting approval | — |

## Current Feature Status

- Repository foundation: complete.
- Webcam preview and one-hand landmarks: implemented; tracker initialization
  verified, interactive webcam visualization awaiting a local manual check.
- Cursor mapping and smoothing: complete; optional gated OS movement in Iteration 8.
- Left/double-click recognition: complete; optional gated OS output.
- Thumb–little right-click recognition: complete; optional gated OS output.
- Two-finger vertical and horizontal scrolling: complete; optional gated OS output.
- Held-fist dragging: complete; precise relative target and optional gated
  left-button hold/release.
- Thumb-ring expansion/contraction zoom: complete; bounded optional gated
  Ctrl-plus/minus output.
- Versioned local settings profiles: complete; strict validation and atomic
  explicit writes.
- Reported hand preference and cursor sensitivity: complete; webcam behavior
  still needs representative manual checks.
- Cursor-region calibration: complete; session apply and optional selected-profile
  persistence using transient normalized coordinates only.
- Safety controls and tracking-loss recovery: implemented; every run starts
  disabled, recovery requires explicit re-enable, and held drag input is released.
- Operating-system input: dry-run by default; PyAutoGUI output requires the
  non-persistent `--enable-real-input` flag plus an explicit runtime enable.
- Open-palm pause: implemented with highest gesture priority and a 350 ms hold.
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
- OS output is routed through `MouseController`; tests use a recording fake.
  PyAutoGUI is imported only for explicit real-input runs and converts normalized
  coordinates to clamped primary-screen pixels.
- Every launch starts disabled, independent of profiles. Real output requires
  `--enable-real-input`, followed by `E` or global `Ctrl+Alt+G` while tracking is
  valid. `P` and global `Ctrl+Alt+Shift+G` emergency-pause control.
- Tracking loss and below-threshold handedness confidence latch control off and
  require explicit re-enable. Calibration and all shutdown/error paths also
  release app-owned input.
- The open-palm recognizer requires all four non-thumb fingers extended, applies
  `0.18/0.10` activation/release hysteresis and a 350 ms hold, and has the highest
  gesture-family priority.
- Ordinary pointer movement requires an index extension ratio of `0.18` to enter
  and remains active through `0.10`; there is no activation time hold. Fist drag
  bypasses this gate and continues to use relative palm movement.
- PyAutoGUI's normal corner failsafe remains enabled. Only app-owned release calls
  temporarily bypass it so a failsafe-triggered drag can still be released.

## Known Bugs

- Iteration 8 open-palm enable collision: enabling while all four fingers remain
  extended causes the open-palm pause gesture to disable control after its 350 ms
  hold. A release-to-arm guard is proposed but not yet implemented. See the
  Iteration 8 document.
- Resolved setup/test issues are recorded in their iteration documents.

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
- MediaPipe Tasks exposes a handedness category score in the current result, not
  a separate per-frame tracking score. Iteration 8 uses that available score for
  its configurable runtime confidence gate; representative false-pause behavior
  needs live testing.
- Real PyAutoGUI movement, multi-monitor behavior, horizontal wheel direction,
  application-specific zoom shortcuts, global-hotkey conflicts, and end-to-end
  emergency-release behavior require controlled manual Windows testing.
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
.\.venv\Scripts\python.exe -m gesture_controls.main --config settings.json --enable-real-input
```

## Test and Build Commands

- Tests: `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider`
- Syntax: `.\.venv\Scripts\python.exe -m compileall -q src tests`
- Dependencies: `.\.venv\Scripts\python.exe -m pip check`
- Build: not implemented until Iteration 12.

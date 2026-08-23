# Gesture Controls Product Requirements

## Objective

Gesture Controls is a Windows-first desktop application that uses one hand seen
by a laptop webcam to control the operating-system pointer. All image processing
is local. Camera frames are neither uploaded nor recorded nor permanently stored.

## Target Users and Platform

- Windows 10 and Windows 11 laptop users with a webcam.
- Python implementation, eventually packaged with PyInstaller so Python is not
  required on the user's machine.
- Lightweight, modular dependencies: OpenCV, MediaPipe Tasks, NumPy, and (in a
  later approved iteration) PyAutoGUI.

## Functional Requirements

- Index raised: pointer movement.
- Thumb/index pinch: left click.
- Close all four non-thumb fingers into a fist, hold deliberately, then move the
  hand: drag; opening the fist releases.
- Thumb/middle-finger pinch: double left click.
- Thumb/little-finger pinch: right click and highest-priority click pinch.
- Index and middle raised plus vertical motion: scroll up/down.
- Middle and ring raised plus horizontal motion: scroll left/right.
- Thumb-ring pose with index, middle, and little held open: spreading zooms in
  and contracting zooms out; the ring remains free to articulate.
- Open palm or global shortcut: pause.
- Track no more than one hand and support configurable dominant hand.
- Configurable sensitivity and smoothing.
- Visible enabled, disabled, and tracking-lost states.
- Start disabled and emit no input until explicitly enabled.
- Pause and release held buttons on low confidence, tracking loss, shutdown, or
  exception.

Recognition uses normalized distances, joint geometry, hysteresis, temporal
validation, cooldowns, and a gesture state machine. The MVP uses no custom ML.

## Privacy and Safety

- Process frames only in volatile memory on the local machine.
- No telemetry, remote inference, frame persistence, or background-only runtime.
- Real input is forbidden in Iteration 1. Future mouse modules require dry-run
  mode and fake controllers in automated tests.
- Gesture conflicts resolve to one action; scrolling cannot click; right click
  cannot left click.
- Include a later emergency keyboard shortcut and validated configuration.

## Performance Goals

Design for 640x480 capture near 30 FPS, at least 20 processed FPS on a typical
laptop, and perceived pointer latency below 100 ms where hardware permits. Use a
bounded/latest-frame pipeline, avoid unnecessary copies and tiny cursor events,
allow preview disabling later, and handle camera disconnection. These are goals,
not claims, until measured on representative hardware.

## Iterations

1. Foundation and webcam landmark prototype.
2. Cursor mapping and smoothing.
3. Left-click recognition.
4. Thumb/little-finger right-click recognition.
5. Scrolling.
6. Dragging and gesture state-machine hardening.
7. Calibration and settings.
8. Safety controls and tracking-loss recovery.
9. UI and system-tray integration.
10. Automated and real-world testing.
11. Performance optimization.
12. PyInstaller packaging and Windows release.

Each new iteration requires explicit user approval.

## Iteration 1 Acceptance Criteria

The foreground application opens and mirrors a webcam feed, performs one-hand
MediaPipe Hand Landmarker inference, draws landmarks, reports camera/hand/
handedness/confidence/FPS status, exits with `Q` or `Esc`, and produces clear
errors for camera, read, model, or tracker failures. It generates no OS input and
stores no frames. Deterministic utilities have ordinary webcam-free tests.

## Iteration 2 Acceptance Criteria

The application maps index-tip camera coordinates through a configurable active
region into clamped normalized screen coordinates, applies frame-rate-independent
smoothing, suppresses tiny output changes, and resets stale filter state when
tracking is lost. The dry-run target is visible in the preview. Iteration 2 emits
no operating-system input and adds no OS-input dependency.

## Iteration 3 Acceptance Criteria

The application computes thumb–index distance relative to palm scale and uses
configurable activation/release hysteresis, temporal holds, and cooldown to emit
exactly one dry-run left-click event on each valid activation transition. Holding
the pinch cannot repeat clicks, and tracking loss resets recognition safely. The
preview shows ratio, state, and dry-run count. A thumb–middle pinch produces one
double-click action and has priority over thumb–index left click. Cursor output
freezes when either pinch becomes a candidate and resumes through reseeded
smoothing immediately after release. No OS click is generated.

## Iteration 4 Acceptance Criteria

The application computes thumb–little distance relative to palm scale and emits
one dry-run right-click action per validated activation transition. Holding cannot
repeat. Conflict priority is right click, double click, then left click; claimed
higher-priority frames reset lower recognizers. Right-click candidates freeze the
cursor and release resumes through immediate smoothing reseed. No OS event is
generated.

## Iteration 5 Acceptance Criteria

The application recognizes index and middle extended for vertical scrolling and
middle and ring extended for horizontal scrolling, with all other non-thumb
fingers folded for each pose. It validates poses over time with hysteresis and
converts palm movement on the pose-bound axis into bounded scale-independent
dry-run steps. Scrolling has exclusive priority over clicks, freezes cursor
output, and resets safely on tracking loss. The preview exposes scroll state,
axis, direction, and step totals. No operating-system wheel event is generated.

## Iteration 6 Acceptance Criteria

The application recognizes a fist when all four non-thumb fingers are folded
using palm-scale-normalized joint geometry, then requires a deliberate 250 ms
hold after pose validation before emitting one dry-run drag-start transition.
Relative palm movement drives the cursor from its pre-drag position, using a
finer movement threshold for precise selection without a closure jump.
Release, tracking loss, a higher-priority conflict, reset, exception, or shutdown
emits at most one matching drag-end transition. The application also recognizes
a distinct thumb-ring zoom pose, converts normalized expansion/contraction into
bounded dry-run zoom-in/out steps, and prevents zoom from leaking clicks. Priority
is scrolling, fist drag, zoom, right click, double click, then left click. The
overlay exposes fist, drag, and zoom state and totals. No operating-system mouse
or keyboard event is generated.

## Iteration 7 Acceptance Criteria

The application loads and saves versioned local JSON settings with strict schema,
field, type, and semantic validation. Profiles expose reported hand preference,
cursor sensitivity/smoothing, cursor region, and gesture/calibration settings;
explicit CLI camera/model values override profiles at runtime. The user can start
cursor calibration from the visible preview, collect transient normalized
index-tip coordinates while normal gestures are suspended, apply a robust region
only after sample/coverage validation, or cancel. Applied calibration updates the
running cursor immediately and is persisted atomically only when a profile path
was explicitly selected. No frames or OS input events are stored or generated.

## Iteration 8 Acceptance Criteria

The application provides fake/dry-run and PyAutoGUI mouse-controller adapters
behind one deterministic safety gate. Every launch starts disabled; real output
also requires the non-persistent `--enable-real-input` flag and an explicit
foreground or global enable action. A held open palm pauses control with highest
gesture priority. Missing, rejected, or below-threshold tracking, emergency
pause, calibration, controller failure, exception, camera failure, window close,
and shutdown suppress further output and release an app-held drag button. Hand
recovery never silently resumes control. Automated tests use fake/injected
controllers only and never emit operating-system input. Ordinary pointer output
requires an index-raised hysteresis gate; fist drag retains its relative mapping.

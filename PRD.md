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
- Thumb/index pinch: left click; holding and moving: drag.
- Thumb/little-finger pinch: right click, only when left pinch is inactive.
- Index and middle raised plus vertical motion: scroll.
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

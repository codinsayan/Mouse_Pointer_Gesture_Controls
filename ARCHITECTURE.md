# Architecture

## Principles

The project uses a `src` package layout. Hardware/framework adapters are kept at
the edges, while deterministic calculations and state transitions remain easy to
unit-test. Frames have in-memory, iteration-local lifetimes and are never saved or
transmitted.

## Current Components

```text
main / application loop
  -> config (validated runtime settings)
  -> camera.capture (OpenCV ownership and reads)
  -> tracking.hand_landmarker (MediaPipe Tasks VIDEO inference)
  -> tracking.landmarks (framework-neutral landmark data/utilities)
  -> controls.cursor (normalized mapping, smoothing, movement threshold)
  -> gestures.features (scale-independent palm and pinch geometry)
  -> gestures.left_pinch (hysteresis, timing, cooldown, transitions)
  -> gestures.clicks (double-click priority and left-click suppression)
  -> gestures.cursor_guard (pinch freeze and delayed resume coordination)
  -> ui.overlay (drawing and status presentation)
  -> diagnostics.fps (monotonic processed-FPS measurement)
```

`VIDEO` mode deliberately processes at most one frame at a time. Monotonically
increasing timestamps allow MediaPipe's internal tracking. This simple bounded
pipeline is appropriate for the prototype; a measured later iteration may adopt
`LIVE_STREAM` and latest-result synchronization if needed.

Iteration 2 feeds index fingertip landmark 8 into a deterministic dry-run cursor
pipeline. A configured subregion of mirrored camera coordinates maps to the full
normalized screen range. An elapsed-time exponential filter smooths the target,
and a normalized movement threshold suppresses tiny output changes. The pipeline
resets on tracking loss and cannot emit mouse events.

Iteration 3 normalizes thumb-tip to index-tip distance by the larger of palm
length and palm width. The left-pinch recognizer applies separate activation and
release thresholds, timed validation, and post-release cooldown. Only an
inactive-to-active transition represents a dry-run click. Tracking loss clears
recognizer history and starts cooldown without emitting a transition.

The final Iteration 3 design uses thumb–index pinch for a single left click and
thumb–middle pinch for one double-click action. The double-click recognizer has
priority: while it is candidate, active, or releasing, left-click recognition is
suppressed and reset. Either candidate freezes cursor output before finger
articulation can move the target. On release, smoothing is immediately reseeded
from the frozen output, preventing a catch-up jump without adding resume delay.

Iteration 4 adds thumb–little normalized distance and a third generic pinch
recognizer. The coordinator resolves candidate, active, activation, and release
frames in strict priority: thumb–little right click, thumb–middle double click,
then thumb–index left click. Right click leads because the thumb may pass near
the middle fingertip while travelling toward the little fingertip. A claimed
higher-priority frame resets lower recognizers, guaranteeing one dry-run action
and preventing action overlap.

## Planned Boundaries

- `camera`: webcam acquisition and camera failures.
- `tracking`: MediaPipe inference plus framework-neutral landmarks.
- `gestures`: feature extraction, recognizers, hysteresis, conflict resolution,
  and the state machine.
- `controls`: coordinate mapping, smoothing, and abstract/real/fake OS control.
- `config`: validated settings and calibration data.
- `ui`: preview, status, and later tray/settings UI.
- `diagnostics`: logging and performance measurements.

The later mouse controller will be behind an interface, default to disabled/dry
run, and guarantee release on loss, exceptions, and shutdown. It does not exist
through Iteration 4; cursor and click results are visualized in the preview only.

## Data Flow and Privacy

OpenCV acquires a BGR array. The foreground loop mirrors it, converts it to RGB,
and passes the in-memory array to MediaPipe. Results are converted to immutable
landmark values. Cursor calculations consume coordinates only and never retain
frames. No component has a frame-writing or network interface. Closing the loop
releases the camera, tracker, and preview window.

## Error Model

Expected setup/runtime failures use specific application exceptions and concise
messages. The CLI returns a nonzero exit code. Cleanup is performed in `finally`
blocks/context managers. Unexpected failures are logged without logging frames.

## Dependency Policy

Python 3.12 is the baseline because current MediaPipe Windows metadata supports
it and it is installed in the inspected environment. Runtime versions are pinned
only after installation/import/test compatibility is demonstrated here. PyAutoGUI
and PyInstaller are intentionally deferred.

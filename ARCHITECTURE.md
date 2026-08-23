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
  -> config.profile (strict versioned local JSON serialization)
  -> camera.capture (OpenCV ownership and reads)
  -> tracking.hand_landmarker (MediaPipe Tasks VIDEO inference)
  -> tracking.landmarks (framework-neutral landmark data/utilities)
  -> controls.cursor (normalized mapping, smoothing, movement threshold)
  -> controls.calibration (transient points and robust region bounds)
  -> gestures.features (scale-independent palm and pinch geometry)
  -> gestures.left_pinch (hysteresis, timing, cooldown, transitions)
  -> gestures.clicks (double-click priority and left-click suppression)
  -> gestures.scroll (two-finger pose and two-axis displacement state machine)
  -> gestures.fist / drag (held-fist drag intent and lifecycle)
  -> gestures.zoom (thumb-ring span quantization)
  -> gestures.interactions (gesture-family conflict resolution)
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

Iteration 5 measures finger extension as fingertip reach beyond the PIP joint,
normalized by palm scale. Index+middle extended with ring+little folded selects
vertical scrolling; middle+ring extended with index+little folded selects
horizontal scrolling. Entry and retention thresholds are separate, and pose
activation/release are temporally validated. Palm motion
uses the average X/Y position of the wrist and four MCP joints, avoiding
fingertip-articulation noise. Displacement is normalized by current hand size and
quantized into bounded signed dry-run steps on the axis assigned by the pose;
off-axis movement is ignored. The top-level gesture coordinator evaluates
scrolling before clicks; every claimed scroll frame resets click state.

Iteration 6 recognizes a fist when the normalized extension of every non-thumb
finger is below a folded threshold. Pose activation/release use hysteresis and
temporal validation; an additional 250 ms active hold produces a one-shot
drag-start transition. Cursor output freezes while the fist is candidate or
armed. At drag start, a relative mapper anchors the stable palm center to the
pre-drag cursor position, preventing a closure jump. Palm translation then
drives the existing smoother with a finer movement threshold. Opening the fist
or any coordinator reset produces at most one drag-end transition. Conflict
ownership for drag and existing gestures is extended by the zoom family below.

Iteration 6 also restores thumb-ring distance as a zoom span rather than a drag
trigger. Zoom requires index, middle, and little extended while the ring remains
free to articulate, separating it from fist drag, scroll poses, and click
pinches. After timed pose activation,
span expansion emits bounded positive dry-run steps and contraction emits bounded
negative steps. Hysteresis and timed release prevent boundary jitter; no step
queue is retained. Conflict ownership is now `scroll > fist drag > zoom > right
> double > left`.

Iteration 7 adds a schema-versioned JSON adapter around `AppConfig`. It rejects
unknown fields and wrong JSON types before dataclass cross-field validation.
Writes use a temporary file in the selected directory followed by atomic
replacement. CLI camera/model overrides are applied to a runtime copy and are
not persisted by calibration.

Cursor calibration is a foreground-only state in the OpenCV loop. While
collecting, gesture families are reset and suspended. Only normalized index-tip
`Point2D` values are retained; frames are not copied or stored. Robust low/high
quantiles, minimum sample count, minimum two-axis coverage, and bounded padding
produce a new `CursorRegion`. Applying rebuilds cursor and relative-drag mapping
immediately. Reported handedness is filtered before gesture or calibration
processing. Sensitivity scales normal mapping around screen center and relative
drag displacement.

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
through Iteration 7; cursor, click, scroll, drag, zoom, settings, and calibration
results are visualized in the preview only.

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

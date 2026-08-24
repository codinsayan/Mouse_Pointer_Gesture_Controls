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
  -> controls.mouse (dry-run/fake/PyAutoGUI OS-output adapters)
  -> controls.safety (startup-disabled gating and release ownership)
  -> controls.hotkeys (Windows RegisterHotKey safety controls)
  -> gestures.features (scale-independent palm and pinch geometry)
  -> gestures.left_pinch (hysteresis, timing, cooldown, transitions)
  -> gestures.clicks (double-click priority and left-click suppression)
  -> gestures.scroll (two-finger pose and two-axis displacement state machine)
  -> gestures.fist / drag (held-fist drag intent and lifecycle)
  -> gestures.pointer (zero-delay index-raised hysteresis gate)
  -> gestures.interactions (gesture-family conflict resolution)
  -> gestures.cursor_guard (pinch freeze and delayed resume coordination)
  -> ui.overlay (drawing and status presentation)
  -> ui.settings_model (validated dashboard-to-profile mapping)
  -> ui.runtime (thread-safe commands, snapshots, and worker ownership)
  -> ui.dashboard (native Tk dashboard and isolated tray process)
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
or any coordinator reset produces at most one drag-end transition.

Iteration 6 originally added thumb-ring zoom. That feature was removed in
Iteration 10: thumb-ring distance is no longer extracted, no zoom recognizer
participates in conflict ownership, and the current priority is
`scroll > fist drag > right > double > left`.

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

Iteration 8 adds the OS-output boundary. `MouseController` keeps PyAutoGUI out of
deterministic recognition and safety logic; ordinary tests use a recording fake.
Normalized cursor points become clamped primary-screen pixels only inside the
PyAutoGUI adapter. Click, double-click, right-click, vertical/horizontal wheel,
and left-button drag output pass through one
`InputSafetyController`.

The safety controller always begins disabled and cannot persist an enabled
state. Real output additionally requires a per-launch CLI flag. Foreground keys
and thread-owned Windows `RegisterHotKey` messages provide toggle and emergency
pause actions.

Ordinary pointer motion also passes a zero-delay index-extension hysteresis gate,
so a visible folded hand cannot move the real cursor. Fist drag bypasses that
gate and retains its relative palm mapping. This adds no temporal hold to normal
pointer motion and therefore does not add deliberate recognition latency.

The safety gate stores control intent and tracking availability separately.
Missing/rejected landmarks or a handedness-category confidence below the runtime
threshold suppress output immediately and release app-owned inputs without
clearing enabled intent. Accepted tracking therefore resumes output
automatically. Manual disable, emergency pause, calibration, PyAutoGUI failure,
camera/tracker exceptions, window close, and shutdown clear enabled intent and
use the same release path.
PyAutoGUI's corner failsafe remains enabled for normal operations; the release
path bypasses it only while releasing input owned by this application.

The Iteration 8 scroll usability correction locks the first nonzero direction
for each active two-finger pose. Opposite return motion updates the displacement
anchor without emitting steps, providing a clutch for repeated strokes. Releasing
and reacquiring the pose clears the lock and allows either direction. A validated
output multiplier is applied after scale-independent quantization, preserving
recognition geometry while producing useful OS wheel travel.

Iteration 9 adds a native Tkinter/ttk control plane without moving frame
ownership out of the existing OpenCV loop. A deterministic presentation model
maps pointer speed `1..10` onto the existing smoothing time constant, scroll
speed `1..20` onto the validated output multiplier, and sensitivity `0.1..3.0`
onto cursor amplification. Saving reuses the schema-validated atomic profile
adapter and preserves every setting not represented by the dashboard, including
calibration.

Tk remains on the main thread while one managed non-daemon worker owns camera,
tracking, preview, hotkeys, and the safety controller. A `SimpleQueue` carries
toggle, emergency-pause, and stop requests into that loop; immutable snapshots
return safety state and landmark-free status to the dashboard. The dashboard
cannot invoke a mouse controller directly. It also cannot persist an enabled or
real-input state.

The pystray Windows backend runs in an isolated spawned process. A duplex pipe
carries only menu actions and short status strings; no frames or landmarks cross
the boundary. The parent requests normal shutdown and forcibly terminates only
that owned child if the platform tray loop fails to respond, so tray failure
cannot prevent application exit. Tk polls tray actions and schedules them back
onto its own main thread.

Dashboard content lives in a two-axis Tk canvas. A deterministic width breakpoint
places the cards side-by-side on wide windows and stacks them on narrow windows;
the canvas keeps a bounded minimum content width so very small windows gain a
horizontal scrollbar rather than clipping controls. Vertical overflow is always
reachable, including by mouse wheel, and Shift+wheel drives horizontal overflow.

The dashboard exposes only enabled and disabled control intent. Enable is
available whenever the camera runtime is running, even before a hand is visible.
Hand readiness is reported separately. An enabled session waits safely with all
output blocked when the hand is absent and resumes automatically when accepted
tracking returns; only manual disable or an emergency pause ends that session.

Iteration 10 removes open-palm recognition from configuration, coordination,
runtime dispatch, exports, and overlay presentation. Open hands therefore flow
through ordinary pointer/gesture evaluation and cannot pause control. The profile
loader alone retains a four-key compatibility allowlist for schema-1 profiles;
deprecated pause values are ignored and disappear on the next atomic save.
Keyboard, global-hotkey, dashboard, tray, tracking-loss, shutdown, controller-
failure, and PyAutoGUI failsafe paths remain independent of gesture recognition.

Cross-component automated scenarios combine synthetic normalized features,
gesture coordination, the safety gate, and `RecordingMouseController`. This
tests observable action exclusivity and release sequences without a webcam or OS
events. `scripts/run_verification.ps1` runs pytest, compilation, and dependency
checks from one Windows command; real hardware behavior is recorded separately
against `docs/REAL_WORLD_TESTING.md`.

## Planned Boundaries

- `camera`: webcam acquisition and camera failures.
- `tracking`: MediaPipe inference plus framework-neutral landmarks.
- `gestures`: feature extraction, recognizers, hysteresis, conflict resolution,
  and the state machine.
- `controls`: coordinate mapping, smoothing, and abstract/real/fake OS control.
- `config`: validated settings and calibration data.
- `ui`: preview overlay, settings presentation, runtime bridge, dashboard, and
  tray ownership.
- `diagnostics`: logging and performance measurements.

The mouse controller is behind an interface and defaults to dry-run. Real output
is opt-in per launch and still starts disabled. The dashboard and tray are
control-plane components only; neither owns recognition or input generation.

## Data Flow and Privacy

OpenCV acquires a BGR array. The foreground loop mirrors it, converts it to RGB,
and passes the in-memory array to MediaPipe. Results are converted to immutable
landmark values. Cursor calculations consume coordinates only and never retain
frames. When explicitly enabled, normalized actions cross the safety gate to the
local PyAutoGUI adapter. No component has a frame-writing, upload, telemetry, or
remote-inference interface. Closing the loop releases app-owned input, global
hotkeys, camera, tracker, and preview window.

## Error Model

Expected setup/runtime failures use specific application exceptions and concise
messages. The CLI returns a nonzero exit code. Output-call failures become an
emergency-paused state. Cleanup runs in `finally` blocks/context managers,
including best-effort app-owned input release. Unexpected failures are logged
without logging frames.

## Dependency Policy

Python 3.12 is the baseline because current MediaPipe Windows metadata supports
it and it is installed in the inspected environment. Runtime versions are pinned
only after installation/import/test compatibility is demonstrated here.
PyAutoGUI 0.9.54 and pystray 0.19.5 are verified with Python 3.12.4. The latter
reuses Pillow already supplied by MediaPipe. PyInstaller remains deferred.

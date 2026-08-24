# Iteration 09: UI and System Tray

## Objective

Provide a clean Windows-first dashboard for configuring and safely operating
Gesture Controls, including pointer speed, scroll speed, sensitivity, live
status, and system-tray access.

## Scope

- Native Tkinter/ttk dashboard using the verified local Tk 8.6 runtime.
- Friendly pointer-speed, scroll-speed, and sensitivity controls backed by the
  existing validated configuration model.
- Dominant-hand selection and concise privacy/safety guidance.
- Atomic load/save of a selected local JSON profile without modifying camera
  calibration or advanced settings.
- Managed camera runtime with start, enable/disable, emergency pause, and safe
  stop actions.
- A thread-safe command/status bridge between the dashboard and camera loop.
- System-tray show, emergency-pause, and graceful-quit actions.
- Deterministic tests that do not open a webcam or generate OS input.

Gesture threshold redesign, the separately documented open-palm enable
collision, real-world testing, performance optimization, and Iteration 10 are
out of scope. Webcam frames remain local and are not passed into the dashboard
or tray.

## Starting State

Iterations 1-8 were complete in the working tree, including the approved
Iteration 8 scroll correction. Those existing uncommitted changes were preserved.
Python 3.12.4 and Tk 8.6 were available. The baseline suite passed 197 tests in
0.22 seconds. Configuration was editable only through JSON, and the runtime used
an OpenCV preview with keyboard/global hotkeys; no dashboard, managed UI bridge,
or tray component existed.

Assumptions made before implementation:

- Native Tkinter/ttk is preferable to adding a large UI framework.
- Pointer speed `1..10` controls smoothing response; cursor sensitivity remains
  a separate amplification setting.
- Scroll speed controls the post-recognition wheel-output multiplier rather than
  changing scale-independent gesture thresholds.
- Settings apply on the next camera start, avoiding unsafe live mutation.
- Real input remains per-run opt-in, confirmed inside the dashboard, and every
  camera start remains disabled.
- Tray IPC contains only commands/status strings and never frames or landmarks.
- The open-palm enable collision remains visible and documented until the user
  separately approves its proposed release-to-arm behavioral change.

## Implementation Plan

1. Define a deterministic settings presentation model without losing calibration.
2. Define a thread-safe runtime command/status bridge independent of Tk/OpenCV.
3. Integrate optional bridge commands and snapshots into the camera loop.
4. Build a styled ttk dashboard for profile editing and safe runtime ownership.
5. Add an optional tray using official pystray and an in-memory icon.
6. Add CLI launch support and exact Windows usage documentation.
7. Test conversions, persistence, command ordering, lifecycle, tray failure, and
   CLI behavior without real input.
8. Run full verification, synchronize documentation, and stop before Iteration 10.

## Implementation Steps

- Read `AGENTS.md`, the PRD, architecture, implementation index, Iteration 8
  record, configuration/profile code, CLI, overlay, and UI package.
- Inspected and preserved the existing Iteration 8 scroll changes.
- Verified Python 3.12.4 and Tk 8.6, then ran the 197-test baseline.
- Checked official PyPI metadata and installed official `pystray==0.19.5`; it
  reuses Pillow already installed through MediaPipe.
- Created this iteration plan before application-code changes.
- Added a deterministic dashboard settings model. Pointer speed maps `1..10` to
  `0.20..0.02` smoothing seconds, scroll speed maps to multiplier `1..20`, and
  sensitivity retains its validated `0.1..3.0` range.
- Added local profile load/default behavior and atomic save through the existing
  schema adapter. Fields outside the dashboard, including calibration, survive.
- Added a `SimpleQueue` command bridge, locked immutable status snapshots, and a
  managed runtime worker that reports startup, live, stopped, and error states.
- Integrated dashboard stop/toggle/emergency commands and landmark-free live
  status into the existing OpenCV loop. Existing preview/global keys still work.
- Built a dark, resizable 940x700 ttk dashboard with Segoe UI typography,
  settings cards, dominant-hand selection, profile chooser, live state/hand/
  confidence/FPS metrics, and explicit safety controls.
- Added an unchecked per-run real-input option with a warning confirmation. The
  camera runtime still starts disabled and the UI never calls a mouse adapter.
- Added `--settings-ui`; combining it with `--enable-real-input` is rejected so
  the dashboard confirmation cannot be bypassed.
- Generated the tray icon entirely in memory. Tray actions restore the window,
  request emergency pause, or quit through the same safe runtime bridge.
- Isolated pystray in an owned spawned process after diagnostic probes exposed
  backend lifecycle/race concerns. A duplex pipe carries only actions and title
  text. Safe quit requests normal exit and terminates only that child if stuck.
- Disabled hide-to-tray until the child explicitly reports ready; failures leave
  the dashboard visible with a readable status.
- Added deterministic settings, runtime, tray, and CLI tests, then ran the full
  suite, compilation, dependency, diff, and privacy scans.
- Corrected the dashboard after user testing: moved all content into a vertical
  and horizontal scrolling canvas, added a 900-pixel responsive breakpoint,
  stacked cards on narrow windows, lowered the minimum window size, and added
  mouse-wheel/Shift+wheel navigation.
- Corrected enable-state semantics: a rejected initial enable remains Disabled,
  the dashboard waits for accepted tracking before enabling the button, and only
  actual post-enable loss enters Tracking Lost.

## Files Created or Modified

- `src/gesture_controls/ui/settings_model.py`
- `src/gesture_controls/ui/runtime.py`
- `src/gesture_controls/ui/dashboard.py`
- `src/gesture_controls/ui/__init__.py`
- `src/gesture_controls/app.py`
- `src/gesture_controls/main.py`
- `src/gesture_controls/errors.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/controls/safety.py`
- `tests/test_ui_settings.py`
- `tests/test_ui_runtime.py`
- `tests/test_tray.py`
- `tests/test_dashboard_layout.py`
- `tests/test_input_safety.py`
- `tests/test_profile.py`
- `requirements.txt`
- `pyproject.toml`
- `README.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `docs/iterations/ITERATION_09_UI_AND_SYSTEM_TRAY.md`

The pre-existing/current Iteration 8 scroll changes remain in its config,
recognizer, tests, and iteration document; Iteration 9 did not rewrite them.

## Technical Decisions

- Tkinter/ttk provides a native dependency-light Windows UI and is available in
  the selected Python 3.12 environment.
- User-facing pointer speed is the inverse of smoothing duration. The mapping is
  deterministic and reversible; the old `0.08 s` default appears as speed 7.
- Sensitivity remains separate because it controls travel amplification, not
  responsiveness. Scroll speed is applied after recognition, preserving pose
  geometry, hysteresis, direction lock, and clutch behavior.
- Sliders expose only ordinary usability settings. Advanced gesture/calibration
  fields remain in JSON and are preserved during every dashboard save.
- Runtime settings are snapshotted when Start Camera is pressed. Save/choose
  profile is disabled while running, and changes take effect after restart.
- Tk owns the main thread; the established camera/preview loop owns one managed
  non-daemon worker so application cleanup cannot be silently abandoned.
- Commands are ordered and non-growing under normal UI use. Status snapshots
  contain booleans/numbers/text only and never a camera frame.
- The tray uses official `pystray==0.19.5`, pinned only after import and package
  compatibility checks. The backend is process-isolated because platform tray
  loops must never prevent the main safety process from shutting down.
- The tray child is explicitly terminated only after a two-second normal-stop
  timeout. This target is exact and wholly owned by the application.
- No enabled state or real-input permission is written to a profile. Every run
  starts disabled, and real input requires a fresh checkbox plus confirmation.
- The camera preview remains a separate visible OpenCV window. Embedding frames
  in Tk would add copies/cross-thread ownership and was rejected for this pass.
- Responsive layout uses two columns at 900 logical pixels or wider and stacks
  below that point. A 700-pixel minimum content width intentionally produces a
  horizontal scrollbar in very small windows rather than shrinking controls
  until they become unusable.
- Rejected enable attempts are not tracking-loss events. They remain Disabled
  with no output permission. A real transition from Enabled to missing/rejected
  tracking still releases input and latches Tracking Lost.

## Bugs and Problems Encountered

### Bug 1: pystray package has no `__version__` attribute
- Symptom: The first compatibility query raised `AttributeError` after import.
- Reproduction: Evaluate `pystray.__version__` with pystray 0.19.5.
- Root cause: This package does not publish its installed version as a module
  attribute.
- Fix: Query installed distribution metadata with `importlib.metadata.version`.
- Files changed: None.
- Verification: Reported `pystray 0.19.5`, Pillow 12.3.0, and available tray APIs.
- Regression prevention: Dependency versions remain pinned and `pip check` runs
  in iteration verification.

### Bug 2: Tray callbacks used the wrong backend signature
- Symptom: A real menu activation would pass icon/item parameters to a zero-
  argument callback and raise `TypeError`.
- Reproduction: Invoke a pystray `MenuItem` action with its documented icon and
  item arguments.
- Root cause: Initial lambdas did not accept the two backend arguments.
- Fix: The isolated tray action factory accepts both arguments and sends a named
  action through IPC.
- Files changed: `src/gesture_controls/ui/dashboard.py`, `tests/test_tray.py`.
- Verification: The fake backend invokes show, pause, and quit actions with the
  real signature; all are received in order.
- Regression prevention: `test_tray_process_uses_backend_callback_signature`.

### Bug 3: Detached tray startup could race with immediate shutdown
- Symptom: An immediate isolated `run_detached()`/`stop()` probe printed success
  but left the backend message-loop thread alive because stop ran before ready.
- Reproduction: Start a detached pystray icon and stop it immediately in the
  managed Windows environment.
- Root cause: pystray marks itself running asynchronously; an early `stop()` is
  intentionally a no-op. Its Windows loop thread is not application-owned.
- Fix: Move pystray into an owned spawned child process, add an explicit ready
  handshake, keep Hide disabled until ready, request normal stop, and terminate
  the child on timeout.
- Files changed: `src/gesture_controls/ui/dashboard.py`, `tests/test_tray.py`.
- Verification: The diagnostic reported tray ready with no error; after stop the
  process was not alive, `multiprocessing.active_children()` was empty, and only
  the main thread remained. Stuck-child termination is covered deterministically.
- Regression prevention: `test_tray_controller_terminates_a_stuck_backend` plus
  controller action/title/shutdown coverage.

### Bug 4: Managed GUI host retained probe interpreters
- Symptom: After both the combined dashboard/tray smoke and a minimal Tk-only
  smoke printed completion, the managed environment retained their Python
  interpreter processes.
- Reproduction: Create a bare `tk.Tk()`, schedule `destroy`, run `mainloop`, and
  print completion in this environment.
- Root cause: The same result without Gesture Controls or pystray isolates this
  to the managed GUI execution host; repository code is not the differentiator.
- Fix: Terminated only the exact diagnostic PIDs after each probe. No product
  workaround was added for an environment-host lifecycle behavior.
- Files changed: None.
- Verification: No diagnostic Python processes remained after explicit cleanup.
- Regression prevention: Automated UI tests avoid GUI processes; real Windows
  lifecycle verification remains an Iteration 10 manual test.

### Bug 5: Cards and footer were clipped in a small window
- Symptom: Resizing the dashboard hid lower control-center actions and the footer;
  there was no way to reach them.
- Reproduction: Resize the original fixed-grid dashboard below its requested
  content height, as shown in the user-provided screenshot.
- Root cause: The root contained a fixed two-column grid with no scrolling or
  responsive breakpoint, and its large minimum size did not solve vertical
  overflow at Windows display scaling.
- Fix: Place the complete dashboard inside a canvas with visible vertical and
  horizontal scrollbars, stack cards below 900 logical pixels, retain a usable
  700-pixel content width, and support wheel/Shift+wheel scrolling.
- Files changed: `src/gesture_controls/ui/dashboard.py`,
  `tests/test_dashboard_layout.py`.
- Verification: At 940x700 the native dashboard selected wide mode and exposed
  vertical overflow. At 600x450 it selected stacked mode with scroll ranges on
  both axes; moving each view to its end reached `1.0`.
- Regression prevention: Deterministic breakpoint/wheel tests plus the native
  resize-and-scroll smoke check.

### Bug 6: Rejected enable incorrectly displayed Tracking Lost
- Symptom: Clicking Enable without an accepted hand immediately changed the UI
  from Disabled to Tracking Lost.
- Reproduction: Start the camera while no accepted hand is ready, then invoke
  the existing enable transition.
- Root cause: `InputSafetyController.toggle(False)` assigned `TRACKING_LOST`
  even though control had never entered Enabled.
- Fix: Keep an initial rejected request Disabled, preserve a genuine previously
  latched Tracking Lost state, and disable the dashboard button with the label
  `Show accepted hand to enable` until the live snapshot is ready.
- Files changed: `src/gesture_controls/controls/safety.py`,
  `src/gesture_controls/ui/dashboard.py`, `tests/test_input_safety.py`, and
  `tests/test_dashboard_layout.py`.
- Verification: Initial rejection remains Disabled; genuine post-enable loss
  remains Tracking Lost; enable becomes available only with accepted tracking.
- Regression prevention: Safety-transition and button-presentation unit tests.

## Tests and Verification

- Commands executed:
  - `git status --short`
  - `rg --files`
  - `.\.venv\Scripts\python.exe --version`
  - Tk version query through `.\.venv\Scripts\python.exe -c ...`
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
    (baseline and final)
  - `.\.venv\Scripts\python.exe -m pip install pystray==0.19.5`
  - `importlib.metadata` compatibility query for pystray/Pillow
  - Focused settings/runtime/tray/profile pytest runs
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - `.\.venv\Scripts\python.exe -m gesture_controls.main --help`
  - Tk dashboard construction smoke with a fake tray and no camera/input
  - Native tray readiness/shutdown diagnostic with no camera/input
  - Native dashboard/tray scheduled-close smoke with no camera/input
  - Minimal Tk-only scheduled-close control probe
  - `git diff --check`, `git diff --stat`, and local privacy-pattern scan
- Results:
  - Python 3.12.4 and Tk 8.6 available.
  - Baseline: 197 tests passed in 0.22 seconds.
  - Initial focused settings/runtime tests: 16 passed in 0.11 seconds.
  - Final focused UI/profile tests: 34 passed in 0.15 seconds.
  - Pre-document-sync suite: 218 tests passed in 0.24 seconds.
  - Post-document-sync suite: 218 tests passed in 0.30 seconds.
  - Final suite after CLI safety regression coverage: 219 tests passed in 0.25
    seconds.
  - Responsive/safety correction focused run: 29 tests passed in 0.09 seconds.
  - Responsive/safety correction full suite: 225 tests passed in 0.28 seconds.
  - Compilation completed with exit code 0.
  - `pip check`: `No broken requirements found.`
  - CLI help completed with exit code 0 and listed `--settings-ui`.
  - `git diff --check` found no whitespace errors; only expected Windows
    LF-to-CRLF checkout warnings were printed.
  - Privacy scan found no frame-writing/upload/telemetry implementation.
- Manual checks:
  - Native dashboard constructed at 940x700 and closed on schedule using a fake
    tray. It loaded the current local profile as pointer speed 7, scroll speed 5,
    and sensitivity 1.0; no file was changed.
  - Native tray reported ready with no error. Normal stop left no active child
    process and no worker thread in the diagnostic interpreter.
  - Combined native dashboard/tray smoke reached its scheduled safe-close path.
  - No webcam was opened and no real or fake mouse event was emitted by the UI
    smoke checks.
  - Live webcam control and interactive tray-menu clicks were not performed.
  - Native resize smoke: wide mode at 940x700; stacked mode at 600x450 with a
    `700x1265` scroll region and reachable horizontal/vertical endpoints.
- Performance observations:
  - Latest deterministic suite completed in 0.28 seconds.
  - Dashboard polling is fixed at 120 ms and carries only immutable status data.
  - No camera FPS, pointer latency, memory, DPI, or long-running UI measurements
    were made; performance targets are not claimed.

## Known Limitations

- Live camera start/stop, status accuracy, and interaction with the separate
  OpenCV preview require a local manual webcam test.
- The design was opened in the native Windows Tk runtime, but high-DPI scaling,
  screen-reader behavior, and broader user usability are not yet evaluated. The
  reported small-window clipping is fixed and both axes were smoke-tested.
- Saved settings apply on the next camera start, not live during a running loop.
- Tray menu clicks were covered deterministically but not clicked manually here.
- The camera preview is not embedded in the dashboard.
- At Iteration 9 completion, the Iteration 8 open-palm enable collision remained
  unresolved. Iteration 10 subsequently removed open-palm pause by user request.
- PyInstaller must include and verify the spawned tray process in Iteration 12.
- Real OS input remains opt-in and was not enabled during this iteration.

## Final State

Iteration 9 is complete. Gesture Controls now has a clean native dashboard for
pointer speed, scroll speed, sensitivity, and dominant hand; atomic local profile
management; live landmark-free status; safe runtime controls; and an isolated
system tray. The dashboard now reflows and scrolls at small sizes, and rejected
enable attempts remain Disabled instead of falsely reporting Tracking Lost.
Startup-disabled and local-only guarantees remain intact. No camera frame is
stored, transmitted, or sent to the dashboard/tray, and no automated or manual
Iteration 9 check generated OS input.

## Next Iteration

Iteration 10 requires explicit user approval and will not begin automatically.

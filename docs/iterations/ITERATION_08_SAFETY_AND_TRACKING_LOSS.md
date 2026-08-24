# Iteration 08: Safety Controls and Tracking-Loss Recovery

## Objective

Introduce the first operating-system input boundary behind explicit, fail-safe
enablement, with deterministic safety state transitions, emergency pause,
tracking-loss recovery, and guaranteed mouse-button release.

## Scope

- A mouse-controller interface with fake/dry-run and opt-in PyAutoGUI adapters.
- Startup in disabled mode; real input requires both explicit configuration and
  an explicit enable action after launch.
- Foreground enable/pause controls and Windows global emergency/toggle hotkeys.
- A deterministic safety state machine for disabled, enabled, tracking-lost,
  and emergency-paused states.
- Low-confidence, missing-hand, rejected-hand, camera/read failure, exception,
  calibration, and shutdown handling that releases held buttons.
- Screen-coordinate dispatch for movement, clicks, drag, vertical/horizontal
  scroll, and zoom shortcuts while enabled.
- Status overlay, validated settings, fake-controller tests, and documentation.

System-tray integration, background-only operation, packaging, and Iteration 9
are out of scope. Webcam frames remain local and transient.

## Starting State

Iterations 1-7 are complete and committed. The working tree is clean. Python
3.12.4 is available in `.venv`, and the baseline deterministic suite passes all
151 tests. Gesture actions and cursor positions are computed and shown in the
preview, but there is no OS-input controller. The application has no global
hotkey and no explicit control-enabled state. Gesture reset already emits a
single dry-run drag-end transition, but no component owns or guarantees release
of a real held mouse button.

## Implementation Plan

1. Define controller and safety-state interfaces independently of OpenCV,
   MediaPipe, PyAutoGUI, and Windows APIs.
2. Add a fake/dry-run controller and a lazy PyAutoGUI adapter with idempotent
   release and screen-coordinate conversion.
3. Add a Windows `RegisterHotKey` adapter for global toggle and emergency pause,
   with foreground keys remaining available and clear registration failures.
4. Add validated opt-in settings. Always begin disabled regardless of profile.
5. Integrate safety gating into the foreground loop and release on every unsafe
   transition, tracking loss, calibration, exception, and shutdown.
6. Route gesture actions only through the controller and only while enabled.
7. Add deterministic unit/integration-style tests using fake controllers; never
   generate real input during tests.
8. Run compatibility, test, syntax, dependency, safety, and documentation checks.
9. Synchronize the PRD, architecture, README, implementation index, and this
   iteration record, then stop before Iteration 9.

## Implementation Steps

- Read repository instructions, PRD, architecture, implementation index,
  Iteration 7 record, current configuration/application/controller boundaries,
  dependencies, and tests.
- Confirmed a clean working tree, project Python 3.12.4, system Python 3.13.5,
  and the existing package/file structure.
- Ran the baseline suite: 151 tests passed in 0.19 seconds.
- Confirmed PyAutoGUI was not installed and checked the official PyPI metadata;
  0.9.54 is the current official release.
- Created this plan before modifying application code.
- Added a protocol-level mouse boundary, no-op dry-run controller, recording fake,
  and lazy PyAutoGUI adapter. Normalized coordinates are clamped to the primary
  screen, and all app-owned held inputs are tracked for release.
- Added the deterministic `disabled`, `enabled`, `tracking_lost`, and
  `emergency_paused` safety state machine. Output calls are ignored unless
  enabled; controller exceptions emergency-pause instead of continuing output.
- Added non-hooking Windows global hotkeys using `RegisterHotKey`: `Ctrl+Alt+G`
  toggles and `Ctrl+Alt+Shift+G` emergency-pauses. Registration failure is a
  readable startup error and partial registration is rolled back.
- Added foreground `E` toggle and `P` emergency pause. Calibration now pauses
  control before collecting. All launches start disabled, and real output
  additionally requires the non-persistent `--enable-real-input` CLI flag.
- Added immediate missing/rejected/below-threshold tracking loss. Recovery is
  latched and requires explicit re-enable. Camera/tracker/controller exceptions,
  window close, and shutdown converge on the release path.
- Routed movement, clicks, double click, right click, two-axis scroll, fist drag,
  and Ctrl-plus/minus zoom through the safety controller.
- Added the highest-priority open-palm pause recognizer with scale-independent
  finger extension, hysteresis, and a 350 ms activation hold.
- Added a zero-delay index-raised hysteresis gate for ordinary pointer movement.
  Fist dragging deliberately bypasses it and retains relative palm mapping.
- Installed PyAutoGUI 0.9.54 and verified import, screen-size lookup, and the
  horizontal-scroll API with Python 3.12.4 without emitting input.
- Added deterministic tests for controller calls, partial failures, button/key
  ownership, safety transitions, hotkey registration cleanup, open-palm priority,
  pointer gating, settings, and CLI opt-in behavior.
- Corrected scrolling so the first stroke direction remains locked while the pose
  is held, return movement clutches/re-anchors without output, releasing permits
  reversal, and each logical step defaults to three OS wheel clicks.
- Synchronized the PRD, architecture, README, implementation index, dependencies,
  and this iteration record.

## Files Created or Modified

- `docs/iterations/ITERATION_08_SAFETY_AND_TRACKING_LOSS.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `README.md`
- `requirements.txt`
- `pyproject.toml`
- `src/gesture_controls/app.py`
- `src/gesture_controls/main.py`
- `src/gesture_controls/errors.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/controls/__init__.py`
- `src/gesture_controls/controls/hotkeys.py`
- `src/gesture_controls/controls/mouse.py`
- `src/gesture_controls/controls/safety.py`
- `src/gesture_controls/gestures/__init__.py`
- `src/gesture_controls/gestures/interactions.py`
- `src/gesture_controls/gestures/pause.py`
- `src/gesture_controls/gestures/pointer.py`
- `src/gesture_controls/gestures/scroll.py`
- `src/gesture_controls/ui/overlay.py`
- `tests/test_config.py`
- `tests/test_hotkeys.py`
- `tests/test_input_safety.py`
- `tests/test_mouse_controller.py`
- `tests/test_pause.py`
- `tests/test_pointer_pose.py`
- `tests/test_profile.py`
- `tests/test_scroll.py`

## Technical Decisions

- Tracking loss will latch control out of the enabled state. Hand recovery will
  not silently resume OS input; the user must explicitly enable it again.
- Profiles cannot select real output or persist an enabled runtime state. Real
  input requires a CLI flag on every process launch, and every launch begins
  disabled regardless.
- Global hotkeys use the Windows API rather than a system-wide keyboard-hook
  package, keeping the added dependency surface small.
- PyAutoGUI is imported lazily. Tests use a fake controller and never construct
  the real desktop backend; adapter tests inject an inert fake backend.
- Missing confidence is unsafe. The only per-result score available from the
  current Tasks adapter is the handedness-category score, so that score backs the
  runtime confidence gate and is documented as a limitation.
- Tracking recovery never automatically resumes. This avoids a sudden cursor or
  click after the hand reappears.
- Open palm has the highest gesture priority. A 350 ms hold avoids accidental
  pauses, while keyboard emergency controls remain immediate.
- Ordinary pointer movement uses index-extension hysteresis without a time hold,
  preserving latency while preventing a folded visible hand from moving the
  cursor.
- PyAutoGUI's corner failsafe remains active for output. Release calls temporarily
  bypass it only for inputs that the adapter recorded as app-owned.

## Bugs and Problems Encountered

### Bug 1: Dependency installation initially returned no distributions

- Symptom: The first `pip install PyAutoGUI==0.9.54` reported no matching
  distribution.
- Reproduction: Run the install in the restricted managed network context.
- Root cause: Package-index access was unavailable in the default sandbox; the
  published package and Python version were compatible.
- Fix: Re-ran the same scoped virtual-environment install with approved network
  access. PyAutoGUI and its Windows support packages installed successfully.
- Files changed: `requirements.txt`, `pyproject.toml`, project `.venv`.
- Verification: Import reports PyAutoGUI 0.9.54; `pip check` reports no broken
  requirements.
- Regression prevention: The direct dependency is pinned, and documented setup
  installs from the repository requirement files.

### Bug 2: Initial safety pass omitted open-palm pause

- Symptom: Keyboard pause paths existed, but the product-required open-palm
  safety gesture was absent.
- Reproduction: Compare the first safety integration against the PRD pause
  behavior.
- Root cause: The initial pass focused on controller lifecycle and tracking-loss
  recovery without auditing every safety input modality.
- Fix: Added a timed hysteretic open-palm recognizer and placed it above scroll,
  fist drag, zoom, and click families.
- Files changed: `gestures/pause.py`, `gestures/interactions.py`, application,
  configuration, overlay, and pause tests.
- Verification: Open-palm state, timing, hysteresis, reset, monotonic timestamps,
  validation, and conflict priority pass deterministic tests.
- Regression prevention: A coordinator test uses a pose that also matches zoom
  and verifies that open-palm pause exclusively wins.

### Bug 3: A visible folded hand could still drive the cursor

- Symptom: Enabling real output would map the index-tip position even when the
  index finger was folded and no other gesture owned the frame.
- Reproduction: Review the pointer path from Iteration 2 with a tracked neutral
  or folded hand.
- Root cause: Iteration 2 intentionally deferred index-raised gating while output
  was dry-run; the first Iteration 8 integration reused that path unchanged.
- Fix: Added zero-delay index-extension activation/release hysteresis for ordinary
  pointer output, while preserving the separate relative fist-drag path.
- Files changed: `gestures/pointer.py`, application, configuration, overlay, PRD,
  architecture, README, implementation index, and pointer tests.
- Verification: Activation, hysteresis, reset, and validation tests pass in the
  final suite.
- Regression prevention: Dedicated tests require reactivation after reset and
  prove there is no temporal activation delay.

### Bug 4: Convenience click failure could obscure button ownership

- Symptom: If a PyAutoGUI click raised after its internal button-down, the adapter
  had no record that a matching release might be needed.
- Reproduction: Inject a backend whose click operation raises after beginning a
  simulated click.
- Root cause: Initial ownership tracking covered drag and Ctrl zoom but treated
  convenience click methods as atomic.
- Fix: Mark transient click buttons as pending until successful completion and
  issue a failsafe-bypassed matching mouse-up during emergency cleanup.
- Files changed: `controls/mouse.py`, `tests/test_mouse_controller.py`.
- Verification: The partial-click regression test records a safe left-button-up
  after the injected failure.
- Regression prevention: The failure-injection test remains webcam-free and
  never calls the real OS backend.

### Bug 5: Open hand used during enable immediately requests pause

- Symptom: Pressing `E` briefly shows `ENABLED`, then returns to `DISABLED`
  roughly one open-palm hold later.
- Reproduction: Keep all four non-thumb fingers extended while pressing `E` and
  continue holding the same pose.
- Root cause: Disabled-mode frames reset gesture recognition. On the first frame
  after enable, the already-open hand enters the pause candidate state; after the
  configured 350 ms hold it emits `PAUSE_REQUESTED`, and the safety controller
  correctly changes to `DISABLED`. There is no post-enable release-to-arm guard.
  The low-confidence path would instead show `TRACKING_LOST`.
- Fix: Pending user approval. Recommended fix: leave open-palm pause disarmed
  after startup/reset/enable until at least one finger is clearly folded once;
  subsequent deliberate open-palm holds can then pause normally.
- Files changed: Documentation only during diagnosis.
- Verification: Source-path inspection confirmed the enable, pause-recognizer,
  and safety transition sequence. Targeted pause/safety tests pass 15 tests in
  0.06 seconds but do not cover enabling while the palm is already open.
- Regression prevention: Add a deterministic test proving an initially open
  palm cannot pause, then becomes eligible only after a non-open pose is seen.

### Bug 6: Scroll return stroke reverses page movement and travel is too small

- Symptom: A scroll stroke moves the page only a small amount, then returning the
  hand toward its starting position scrolls the page back toward its origin.
- Reproduction: Hold either two-finger scroll pose, move along its bound axis,
  and return along the same axis without releasing the pose.
- Root cause: The displacement quantizer is intentionally symmetric around a
  moving anchor, so the return stroke produces equal-and-opposite signed steps.
  Each logical step is also dispatched as only one PyAutoGUI wheel click.
- Fix: Locked the first nonzero direction for one held scroll gesture, made
  opposite movement update the anchor without output, and applied a validated
  default output multiplier of three after scale-independent quantization.
  Releasing/reforming the pose resets the lock and permits either direction.
- Files changed: `gestures/scroll.py`, configuration, application, scroll/config
  tests, README, architecture, implementation index, and this document.
- Verification: Pre-fix full suite passed 186 tests in 0.24 seconds. Targeted
  scroll/config/profile tests pass 84 tests in 0.24 seconds. The post-fix full
  suite passes 197 tests in 0.24 seconds.
- Regression prevention: Vertical/horizontal tests now prove return motion emits
  zero, repeated forward strokes continue, releasing permits reversal, the
  multiplier scales output, and disabling the lock retains legacy behavior.

## Tests and Verification

- Commands executed:
  - Repository, documentation, environment, dependency, and source inspection.
  - `git status --short`
  - `python --version`
  - `.\.venv\Scripts\python.exe --version`
  - `.\.venv\Scripts\python.exe -m pip show pyautogui`
  - `.\.venv\Scripts\python.exe -m pip install PyAutoGUI==0.9.54`
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - `.\.venv\Scripts\python.exe -m gesture_controls.main --help`
  - PyAutoGUI import/API/screen-query compatibility command.
  - Profile backward-compatibility load command for the existing `settings.json`.
  - Global-hotkey register/unregister smoke command.
  - `rg` privacy-risk API scan.
  - `git diff --check`
  - Targeted `tests/test_scroll.py`, `tests/test_config.py`, and
    `tests/test_profile.py` pytest run.
- Results:
  - Working tree was clean.
  - System Python: 3.13.5; project Python: 3.12.4.
  - PyAutoGUI was not installed at iteration start.
  - Baseline: 151 tests passed in 0.19 seconds.
  - Intermediate suites passed 169, 177, 179, 185, and 186 tests as safety
    coverage was added.
  - Initial Iteration 8 final suite: 186 tests passed in 0.18 seconds.
  - Scroll-fix baseline: 186 tests passed in 0.24 seconds.
  - Scroll-fix targeted suite: 84 tests passed in 0.24 seconds.
  - Current full suite: 197 tests passed in 0.24 seconds.
  - Syntax compilation exited 0 with no output.
  - Dependency check: `No broken requirements found.`
  - CLI help exited 0 and lists the non-persistent real-input flag.
  - PyAutoGUI 0.9.54 imported on Python 3.12.4; `hscroll` and primary-screen
    lookup were available. No input method was called.
  - The existing Iteration 7 `settings.json` loaded with new defaults, requiring
    no destructive profile rewrite; scroll direction lock resolved to `True` and
    output multiplier to `3`.
  - Both Windows global hotkeys registered and unregistered successfully.
  - Privacy scan found no frame-writing or network-call API matches.
  - `git diff --check` exited 0; Windows line-ending notices were non-failures.
- Manual checks:
  - No live gesture-to-OS input was intentionally enabled in this implementation
    session. This avoids uncalibrated mouse actions during automated work.
- Performance observations:
  - The final deterministic suite completed in 0.24 seconds. Pointer-pose gating
    has no time hold, but this is not an end-to-end input-latency measurement.

## Known Limitations

- Real cursor movement, click timing, drag precision, wheel direction, zoom
  behavior, PyAutoGUI corner failsafe, and global shortcuts need controlled live
  testing with disposable targets.
- The PyAutoGUI adapter maps to the primary screen. Multi-monitor coordinate
  behavior is not calibrated or verified.
- `Ctrl`+`+`/`-` zoom behavior depends on the foreground application.
- The available runtime score is handedness confidence rather than a separate
  per-frame tracking-confidence output. False pauses need representative testing.
- Open-palm, pointer-extension, and confidence thresholds are provisional.
- Scroll direction remains locked until the pose is released; deliberate
  reversal requires release/reacquisition. The default three-click output
  multiplier may need per-application adjustment.
- Open-palm pause currently arms immediately after enable, so enabling while
  holding an open hand can return control to `DISABLED` after 350 ms. The proposed
  release-to-arm correction is pending approval.
- System-tray controls and a graphical safety/status UI belong to Iteration 9.

## Final State

Iteration 8 is complete. OS actions are separated behind fake/dry-run/PyAutoGUI
adapters and one startup-disabled safety state machine. Real output requires two
explicit steps, unsafe conditions latch output off, and all app-owned button/key
state follows a common best-effort release path. Open palm and global/foreground
shortcuts pause control; ordinary pointer movement requires an index-raised pose.
No webcam frames are recorded, stored, uploaded, or sent for remote inference.
Scroll return strokes now act as a clutch rather than undoing page movement, and
logical steps use a validated default three-click output multiplier.

## Next Iteration

Iteration 9 requires explicit user approval and will not begin automatically.

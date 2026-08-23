# Iteration 06: Fist Dragging, Zoom, and State-Machine Hardening

## Objective

Recognize a held fist as a precise dry-run drag, move the cursor through stable
relative palm motion while held, and guarantee one safe drag end on release,
tracking loss, conflict, reset, exception, or shutdown. Add bounded dry-run zoom
from thumb-ring expansion and contraction without leaking click gestures.

## Scope

- Scale-independent four-finger folded fist pose.
- Hysteretic, temporally validated fist entry and release.
- Additional deliberate hold before one drag-start transition.
- Fine cursor movement threshold while dragging.
- Conflict priority `scroll > fist drag > right > double > left`.
- Cursor freeze while drag is candidate/armed and smooth tracking while dragging.
- One-shot release/reset safety, overlay state/counters, and deterministic tests.
- Distinct ring-extended zoom pose, thumb-ring span hysteresis, and bounded
  expansion/contraction steps.

Real OS mouse-down/up events, calibration UI, and Iteration 7 are out of scope.

## Starting State

Iterations 1–5 are committed at `0dc55c5`; the baseline suite has 85 passing
tests. Left click is thumb–index, double click is thumb–middle, right click is
thumb–little, and scrolling uses distinct two-finger poses. All behavior remains
dry-run. No Iteration 6 document or drag module exists in the baseline.

## Implementation Plan

1. Recognize all four non-thumb fingers folded using normalized joint geometry.
2. Give fist intent exclusive ownership above click pinches and below scrolling.
3. Add an armed/dragging hold recognizer with one start and one end transition.
4. Freeze cursor through fist candidate/armed state, then track palm movement
   relative to the pre-drag cursor position with a finer movement threshold.
5. End drag on release, tracking loss, conflict, reset, exception, and shutdown.
6. Add provisional validated settings and overlay ratio/state/counters.
7. Test scale independence, hold timing, conflict resolution, cursor precision,
   one-shot transitions, and reset/release safety.
8. Run all checks, synchronize documentation, and stop before Iteration 7.

User-approved Zoom Extension Plan (created before zoom application-code changes):

1. Restore normalized thumb-ring distance with zoom-specific naming.
2. Require index/middle/little extended while leaving the ring free to articulate,
   distinguishing zoom from fist drag, scrolling, and click pinches.
3. Validate entry/release over time and quantize expansion/contraction into
   bounded signed steps without a growing queue.
4. Resolve priority as `scroll > fist drag > zoom > right > double > left`.
5. Add overlay counters, validated provisional settings, deterministic tests,
   and synchronized documentation while remaining dry-run.

## Implementation Steps

- Read repository instructions, PRD, architecture, implementation index, and
  Iteration 5 documentation.
- Inspected Git state/history and the current features, click/scroll coordinator,
  cursor pipeline, application, configuration, overlay, and tests.
- Confirmed Iteration 5 is the committed baseline and Iteration 6 was not present.
- Ran the baseline suite: 85 tests passed in 0.12 seconds.
- Created this plan before application-code changes.
- Initially implemented thumb-ring pinch dragging, then replaced it after the
  user's live check found the pinch unreliable.
- Added an all-four-fingers-folded fist recognizer using existing normalized
  extension geometry and made fist intent suppress all click pinches.
- Implemented `idle -> armed -> dragging` recognition and one-shot start/end
  transitions.
- Integrated cursor freeze/reseed, relative palm translation, and a drag-only
  fine movement threshold into the foreground dry-run loop.
- Added overlay fist/drag states and dry-run start/end counters.
- Added validated provisional configuration and deterministic regression tests.
- Updated product, architecture, README, iteration, and implementation-index docs.
- Added normalized thumb-ring zoom span and a dedicated zoom state machine.
- Added zoom-family conflict ownership, cursor freeze, overlay state, and dry-run
  zoom-in/out counters.
- Added deterministic tests for geometry, pose gating, timing, hysteresis,
  direction, bounded steps, conflicts, reset behavior, and configuration.

## Files Created or Modified

- `docs/iterations/ITERATION_06_DRAGGING.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `README.md`
- `src/gesture_controls/app.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/controls/cursor.py`
- `src/gesture_controls/gestures/__init__.py`
- `src/gesture_controls/gestures/clicks.py`
- `src/gesture_controls/gestures/drag.py`
- `src/gesture_controls/gestures/features.py`
- `src/gesture_controls/gestures/fist.py`
- `src/gesture_controls/gestures/interactions.py`
- `src/gesture_controls/gestures/zoom.py`
- `src/gesture_controls/ui/overlay.py`
- `tests/test_click_gestures.py`
- `tests/test_config.py`
- `tests/test_cursor.py`
- `tests/test_drag.py`
- `tests/test_gesture_features.py`
- `tests/test_fist.py`
- `tests/test_scroll.py`
- `tests/test_zoom.py`

## Technical Decisions

- Fist recognition requires every non-thumb fingertip extension beyond its PIP
  joint to be at most `0.10` hand-size units, with release above `0.18`.
- Fist pose entry/release use provisional 60/50 ms validation, then drag requires
  an additional 250 ms active hold.
- Fist drag is above every click pinch because closing a fist can bring several
  fingertips close to the thumb; claimed fist frames reset click recognizers.
- The thumb is ignored for fist recognition, accommodating natural fist shapes.
- Palm translation is mapped relative to the cursor position captured at drag
  start, avoiding the pointer jump caused by changing hand pose.
- Drag uses a provisional `0.0005` normalized minimum cursor movement for
  approximately pixel-level precision on common displays; no OS event is emitted.
- Drag reuses elapsed-time exponential smoothing instead of adding a second
  filter, avoiding extra state and preserving Iteration 2 behavior.
- Real PyAutoGUI mouse-down/up was rejected for this iteration because the
  existing architecture remains dry-run until an OS controller can default
  disabled and guarantee release independently of the UI loop.
- Zoom uses thumb-ring span normalized by palm scale. Expansion maps to positive
  zoom-in steps and contraction to negative zoom-out steps.
- Zoom requires index, middle, and little extended while leaving the ring free to
  bend toward the thumb. This prevents fist/scroll/click paths from claiming zoom
  without imposing contradictory geometry on the active ring finger.
- Span entry/release defaults are `0.45/0.85`; pose entry/release defaults are
  60/50 ms. Each `0.08` span change emits one step, capped at three per frame,
  with no retained backlog. These values remain provisional.
- Zoom remains dry-run; synthesizing `Ctrl` plus wheel/keys would violate the
  current no-OS-input boundary and is deferred to the guarded controller work.

## Bugs and Problems Encountered

### Bug 1: Safety scan command was incompatible with Windows PowerShell 5

- Symptom: The combined verification command stopped with `The token '||' is not
  a valid statement separator in this version.`
- Reproduction: Run the original ripgrep fallback using `||` in Windows
  PowerShell 5.
- Root cause: `||` is supported by newer PowerShell versions but not the shell
  installed in this environment.
- Fix: Re-ran the scan using `$LASTEXITCODE` and a PowerShell `if` statement.
- Files changed: None.
- Verification: The revised scan exited 0 and reported no prohibited OS-input,
  frame-writing, or network-call matches under `src` or `tests`.
- Regression prevention: Keep verification commands compatible with the
  repository's inspected Windows PowerShell version.

### Bug 2: Thumb-ring drag was unreliable in live use

- Symptom: The user reported that thumb-ring pinching did not produce dependable
  drag behavior.
- Reproduction: Attempt to form and hold the original Iteration 6 thumb-ring
  pinch during live webcam use.
- Root cause: A single adjacent-fingertip distance is sensitive to hand angle,
  landmark occlusion, and natural variation, and it did not match the user's
  preferred hold-and-release interaction.
- Fix: Removed the drag pinch feature, recognizer, settings, overlay line, and
  priority plumbing. Replaced them with a hysteretic all-fingers-folded fist pose
  plus relative palm-motion mapping.
- Files changed: Gesture feature/click/interaction/runtime/config/overlay modules,
  cursor controls, documentation, and deterministic tests.
- Verification: Fist entry, abandonment, hysteresis, hold timing, click
  suppression, relative mapping, release, conflict, and reset are unit-tested.
- Regression prevention: Fist recognition and relative no-jump movement now have
  dedicated deterministic tests and interaction-level conflict tests.

## Tests and Verification

- Commands executed:
  - Read required documentation and source/tests with PowerShell.
  - `git status --short --branch`
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - `.\.venv\Scripts\python.exe -m gesture_controls.main --help`
  - `rg -n -i <OS-input/frame-write/network patterns> src tests` with a
    PowerShell `$LASTEXITCODE` fallback
  - `git diff --check`
- Results:
  - Baseline: 85 tests passed in 0.12 seconds.
  - Final rerun after the fist-drag correction: 107 tests passed in 0.22 seconds
    (the preceding run passed the same 107 tests in 0.15 seconds).
  - Initial zoom-extension run: 121 tests passed in 0.17 seconds.
  - Final zoom-extension rerun after ergonomic pose refinement: 121 tests passed
    in 0.21 seconds.
  - Syntax compilation completed with exit code 0 and no output.
  - Dependency check: `No broken requirements found.`
  - CLI help completed with exit code 0.
  - Safety scan found no matches; `git diff --check` found no whitespace errors.
- Manual checks:
  - Live webcam and real hand behavior were not tested in this non-interactive
    session.
- Performance observations:
  - The final 121-test deterministic suite completed in 0.21 seconds. This is not a
    webcam FPS or end-to-end latency measurement, so no runtime target is claimed.

## Known Limitations

- Hold, fist-folding, and cursor-precision defaults are uncalibrated.
- Zoom pose, span, direction, and step defaults are uncalibrated.
- Drag remains dry-run only.
- Text selection and icon movement cannot be validated until the later guarded
  OS mouse controller exists and is explicitly enabled.

## Final State

Iteration 6 is complete in dry-run scope. A fist is recognized from all four
non-thumb fingers using scale-independent, hysteretic geometry and must remain
active for an additional 250 ms before one drag-start transition. The cursor
freezes during intent validation, then follows relative palm translation with a
finer threshold. Opening the fist and reset paths end an active drag exactly once.
Thumb-ring expansion/contraction in a distinct ring-extended pose emits bounded
dry-run zoom-in/out steps and suppresses clicks. No operating-system input is
generated.

## Next Iteration

Iteration 7 (calibration and settings) requires explicit user approval and will
not begin automatically.

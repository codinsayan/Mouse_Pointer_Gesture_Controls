# Iteration 04: Thumb–Little Right-Click Recognition

## Objective

Recognize a scale-independent thumb–little pinch as one transition-driven dry-run
right click, integrate it into deterministic click conflict priority, and retain
low-latency cursor freeze/resume behavior without generating OS input.

## Scope

- Thumb-tip to little-tip distance normalized by existing palm scale.
- Independent provisional right-click thresholds, holds, and debounce.
- One right-click action per activation transition; no repetition while held.
- Priority `right click > double click > left click`.
- Suppression/reset of lower-priority recognizers during claimed frames.
- Cursor freeze during right-click candidate/active state and immediate reseed on
  release.
- Preview ratio/state/highlight/count and deterministic webcam-free tests.

Scrolling, dragging, PyAutoGUI, real OS-input events, and Iteration 5 work are out
of scope.

## Starting State

Iterations 1–3 are complete and committed. Thumb–index maps to dry-run left click
and thumb–middle maps to prioritized dry-run double click. The worktree is clean
on `main`, tracking `origin/main`. The latest recorded suite has 52 passing tests.

## Implementation Plan

1. Extend click features with thumb–little normalized distance.
2. Add validated provisional right-click configuration.
3. Add a third generic pinch recognizer to the click coordinator.
4. Evaluate and resolve priority as right, then double, then left.
5. Feed the selected right-click state through the existing cursor guard.
6. Add right-click overlay state, highlighting, count, and last-action label.
7. Test scale independence, one-shot holding, priority conflicts, cooldown, and
   tracking-loss reset.
8. Run all checks, synchronize documentation, and stop before Iteration 5.

## Implementation Steps

- Re-read required repository and Iteration 3 documentation.
- Inspected clean Git status, feature extraction, click coordinator, application,
  overlay, and validated configuration.
- Defined the Iteration 4 dry-run safety boundary and implementation plan.
- Initially added ring-tip landmark 16, then changed the gesture to little-tip
  landmark 20 after the user's webcam test showed intermittent missed pinches.
- Added validated provisional right-click thresholds, holds, and cooldown.
- Extended the generic click coordinator with a right recognizer and strict
  right > double > left priority.
- Reset double and left during right claims, and reset left during double claims.
- Integrated one-shot right-click actions, count, last-action label, ratio/state,
  active highlight, and existing cursor guard behavior.
- Added scale-independence, validation, one-shot hold, right-over-left,
  double-over-right, and tracking-loss reset tests.

## Files Created or Modified

- `docs/iterations/ITERATION_04_RIGHT_CLICK.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `README.md`
- `src/gesture_controls/app.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/gestures/clicks.py`
- `src/gesture_controls/gestures/features.py`
- `src/gesture_controls/ui/overlay.py`
- `tests/test_click_gestures.py`
- `tests/test_config.py`
- `tests/test_gesture_features.py`

This list will be updated as implementation proceeds.

## Technical Decisions

- Little fingertip is landmark 20.
- Reuse the generic temporal `PinchRecognizer`; do not duplicate state logic.
- Right-click candidate/active/release suppresses both double and left;
  double-click candidate/active/release suppresses left.
- Provisional right-click ratios and timing initially match the low-latency click
  defaults and remain configurable pending webcam calibration.
- No new dependency is required.
- Provisional defaults are activation ratio 0.30, release ratio 0.42, 30 ms
  activation/release holds, and 60 ms debounce.
- A right recognizer claiming a frame suppresses double and left even before
  activation, preventing click leakage while the little-finger pinch validates.
- The original `double > right > left` order protected the more specialized
  gestures from incidental thumb–index proximity. After remapping right click to
  the little finger, priority changed to `right > double > left`: the thumb can
  pass near the middle fingertip while reaching the little fingertip, so allowing
  double click to claim first could mask an intended right click.

## Bugs and Problems Encountered

### Bug 1: Thumb–ring pinch was intermittently missed
- Symptom: The user reported that webcam recognition sometimes failed to claim
  an intended right-click pinch.
- Reproduction: During the user's live webcam test, pinch the thumb and ring
  fingertip; some attempts do not cross and hold the configured activation ratio.
- Root cause: The chosen gesture is ergonomically less isolated for this user:
  bringing the ring finger to the thumb can move adjacent fingers and may not
  place landmark 16 close enough to landmark 4 consistently. This is a gesture
  mapping/usability issue rather than a deterministic state-machine failure.
- Fix: Remapped right click to normalized thumb-tip–little-tip distance using
  MediaPipe landmark 20, and updated the preview highlight and status label.
- Files changed: `features.py`, `overlay.py`, `app.py`, tests, and Iteration 4
  documentation.
- Verification: Added a regression test proving right-click extraction reads
  landmark 20 rather than ring-tip landmark 16; full verification results are
  recorded below.
- Regression prevention: Keep the landmark-selection test alongside the
  scale-independence and coordinator transition tests.

## Tests and Verification

- Commands executed:
  - Read required documents and relevant code with PowerShell.
  - `git status --short --branch`
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - `git diff --check`
  - A source scan for forbidden OS-input imports and mouse-event calls.
- Results:
  - Worktree was clean on `main`, tracking `origin/main`.
  - Initial Iteration 4 run: 60 tests passed in 0.14 seconds.
  - Final Iteration 4 run: 60 tests passed in 0.08 seconds.
  - After the thumb–little correction and priority update: 61 tests passed in
    0.11 seconds.
  - Compilation completed successfully with exit code 0.
  - Dependency validation reported `No broken requirements found.`
  - The diff check found no whitespace errors; Git emitted only line-ending
    conversion warnings (LF to CRLF).
  - The OS-input safety scan found no PyAutoGUI imports or mouse-event calls.
- Manual checks:
  - The user's live webcam check found intermittent misses with thumb–ring,
    prompting this correction. Thumb–little behavior still requires the user's
    follow-up camera validation because this environment did not access a webcam.
- Performance observations:
  - No webcam FPS or end-to-end gesture latency measurement was performed; no
    performance target is claimed.

## Known Limitations

- Right-click behavior remains dry-run only.
- Thresholds/timing and adjacent-finger conflicts need live webcam calibration.
- No interactive webcam check was performed in this session.

## Final State

Iteration 4 is complete. Thumb–little pinch is scale-independent, hysteretic,
temporally validated, cooldown-protected, transition-only, prioritized between
above double and left click, and reset safely on tracking loss. The preview exposes its
state and count; no OS-input API exists.

## Next Iteration

Iteration 5 (scrolling) requires explicit user approval and will not begin
automatically.

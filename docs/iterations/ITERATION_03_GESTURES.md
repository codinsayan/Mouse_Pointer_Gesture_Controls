# Iteration 03: Left-Click Recognition

## Objective

Recognize scale-independent thumb–index single-click and thumb–middle double-click
pinches using hysteresis, temporal validation, priority, and safe reset, while
generating no operating-system input.

## Scope

- Palm-scale reference geometry from neutral landmarks.
- Normalized thumb-tip to index-tip pinch ratio.
- Normalized thumb-tip to middle-tip double-click ratio.
- Separate configurable activation and release thresholds.
- Timed activation and release validation.
- Post-release cooldown before another activation.
- One dry-run click event per inactive-to-active transition.
- Tracking-loss reset and preview state/ratio/event count.
- Webcam-free deterministic tests.

Right click, scroll, drag semantics, full gesture conflict resolution, PyAutoGUI,
and real OS-input events are out of scope.

## Starting State

Iterations 1 and 2 are complete. The application tracks one hand and visualizes
a mapped, smoothed normalized cursor target in dry-run mode. Twenty-three tests
pass. The Git worktree is clean on `main` and tracks `origin/main`.

## Implementation Plan

1. Add landmark-index constants and scale-independent hand geometry utilities.
2. Extract a left-pinch ratio from thumb/index distance divided by palm scale.
3. Add validated provisional thresholds and timing configuration.
4. Implement a deterministic recognizer with hysteresis, activation/release hold
   times, cooldown, monotonic timestamps, and explicit transitions.
5. Reset gesture state on tracking loss without producing a click.
6. Integrate dry-run state, ratio, and transition count into the preview.
7. Test geometry, state transitions, jitter resistance, cooldown, and reset.
8. Run all checks, synchronize documentation, and stop before Iteration 4.

### Approved hardening pass

1. Expose pinch-candidate state before activation and freeze cursor output at
   candidate entry.
2. Replace the long cooldown with short debounce and classify two activation
   transitions inside a configurable window as a double-click sequence.
3. Keep the cursor frozen through release plus a short resume delay.
4. Reseed smoothing from the frozen output before accepting live fingertip input.
5. Add deterministic regressions for double-click timing and cursor stability.

### Approved latency and gesture revision

1. Keep thumb–index pinch as a single left click only.
2. Replace the unsuccessful two-cycle double click with one thumb–middle pinch.
3. Give thumb–middle double click priority and suppress thumb–index recognition
   during double-click candidate/active states.
4. Reduce provisional activation/release holds to 30 ms.
5. Remove the post-release cursor delay and reseed smoothing immediately.
6. Replace obsolete two-cycle tests and documentation before Iteration 4.

## Implementation Steps

- Re-read required repository and current-iteration documentation.
- Inspected the clean Git status and relevant application/config/tracking/UI code.
- Defined the Iteration 3 dry-run safety boundary and implementation plan.
- Added scale-independent palm-size and thumb/index pinch feature extraction.
- Added a temporal recognizer with hysteresis, activation/release holds,
  cooldown, monotonic timestamp validation, and explicit transitions.
- Added safe tracking-loss reset behavior that cannot emit an activation.
- Added validated provisional thresholds and timing settings.
- Integrated recognition into the foreground loop and incremented the dry-run
  click count only on `ACTIVATED` transitions.
- Added ratio/state/count overlay text and active-pinch line highlighting.
- Added synthetic-hand geometry and recognizer state-machine tests.
- User feedback after Iteration 3 identified that double-click cycles were too
  slow and index-tip motion moved the cursor during pinching.
- Re-opened Iteration 3 for an approved hardening pass; Iteration 4 remains
  unstarted.
- Added explicit candidate state and cursor-freeze intent to pinch updates.
- Added configurable double-click window and shorter second-activation hold.
- Reduced provisional post-release cooldown from 250 ms to 60 ms.
- Classified each activation as a first click or a second click completing a
  double-click sequence; holding still cannot repeat.
- Added frozen cursor updates and smoothing reseed from the frozen output.
- Extracted freeze/release-delay/resume logic into a deterministic cursor guard.
- Integrated single/double counters, last-click label, and frozen cursor status.
- Added regression tests for candidate abandonment, fast double activation,
  outside-window single activation, freeze stability, delayed resume, and smooth
  movement after reseeding.
- User testing reported that the two-cycle double click did not work reliably and
  that its holds/delay made the interaction feel slow.
- Replaced two-cycle thumb–index double click with one thumb–middle pinch.
- Generalized the pinch recognizer and added a deterministic click coordinator.
- Gave double click priority and reset left click during double candidates,
  activation, and release.
- Reduced both gestures' provisional activation/release holds to 30 ms and kept
  a 60 ms debounce.
- Removed the post-release delay; the cursor now reseeds and resumes immediately.
- Replaced obsolete sequence tests with feature, priority, conflict, hold, and
  immediate-resume regression tests.

## Files Created or Modified

- `docs/iterations/ITERATION_03_GESTURES.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `README.md`
- `src/gesture_controls/app.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/controls/cursor.py`
- `src/gesture_controls/gestures/__init__.py`
- `src/gesture_controls/gestures/features.py`
- `src/gesture_controls/gestures/left_pinch.py`
- `src/gesture_controls/gestures/cursor_guard.py`
- `src/gesture_controls/gestures/clicks.py`
- `src/gesture_controls/ui/overlay.py`
- `tests/test_config.py`
- `tests/test_cursor.py`
- `tests/test_cursor_guard.py`
- `tests/test_click_gestures.py`
- `tests/test_gesture_features.py`
- `tests/test_left_pinch.py`

This list will be updated as implementation proceeds.

## Technical Decisions

- Use landmarks 4 and 8 for thumb/index tip distance.
- Use the larger of wrist-to-middle-MCP and index-MCP-to-little-MCP distances as
  palm scale, avoiding fixed pixel thresholds.
- Thresholds and timing values are provisional validated configuration, not final
  constants; representative webcam calibration remains necessary.
- A click is a recognizer activation transition only. Holding a pinch cannot
  generate repeated clicks.
- Tracking loss clears recognizer history without creating an activation.
- No new dependency is required.
- Provisional defaults are activation ratio 0.30, release ratio 0.42,
  80 ms activation hold, 50 ms release hold, and 250 ms cooldown. They are not
  final until representative manual testing is documented.
- The active recognizer ignores ratios in the hysteresis band; the inactive
  recognizer requires a fresh uninterrupted below-threshold hold.
- A candidate freezes the existing cursor output immediately. An abandoned
  candidate triggers one smoothing reseed before movement resumes.
- The two-cycle thumb–index double-click approach was rejected after user testing
  because it was slow and unreliable. It remains documented here for history but
  is absent from current code and configuration.
- Thumb–middle activation represents one double-click action. It suppresses the
  lower-priority thumb–index recognizer while claiming the frame.
- Final provisional timing defaults are 30 ms activation/release holds, 60 ms
  debounce, and zero post-release delay for both click gestures.

## Bugs and Problems Encountered

### Bug 1: Exact release duration missed its boundary
- Symptom: A release held from timestamp 0.20 to 0.25 seconds did not satisfy a
  configured 0.05-second hold and remained active for another frame.
- Reproduction: Run `test_release_requires_hold_and_starts_cooldown` with the
  release timestamps above.
- Root cause: Binary floating-point subtraction produced a value microscopically
  below 0.05 even though the input timestamps represent the exact boundary.
- Fix: Compare elapsed durations with a `1e-12`-second numerical tolerance.
- Files changed: `src/gesture_controls/gestures/left_pinch.py`.
- Verification: The next full run passed all 35 tests, including the exact
  boundary case.
- Regression prevention: The exact-boundary release test remains in the suite;
  activation and release share the same tolerant comparison helper.

### Bug 2: Cursor resume stayed frozen at the exact delay boundary
- Symptom: A cursor scheduled to resume 0.05 seconds after a release at 0.10
  remained frozen at timestamp 0.15 for one additional frame.
- Reproduction: Run `test_release_stays_frozen_through_resume_delay`.
- Root cause: Adding binary floating-point timestamps represented the resume
  boundary microscopically above 0.15.
- Fix: Apply the recognizer's shared `1e-12`-second tolerance to the guard's
  resume-boundary comparison.
- Files changed: `src/gesture_controls/gestures/cursor_guard.py`.
- Verification: The next full run passed all 44 tests.
- Regression prevention: The coordinator test exercises the exact boundary.

## Tests and Verification

- Commands executed:
  - Read required documentation and relevant source files with PowerShell.
  - `git status --short --branch`
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` (first run)
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` (bug fix)
  - `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider` (integrated run)
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - Searched `src` and `tests` for OS-input, frame-writing, and network-client
    calls.
  - Re-ran the full suite after the user-requested double-click/cursor-freeze
    hardening and after extracting the cursor guard.
- Results:
  - Worktree was clean on `main`, tracking `origin/main`.
  - First recognizer run: 34 passed and 1 failed at an exact time boundary.
  - Post-fix recognizer run: 35 passed in 0.06 seconds.
  - Integrated run: 35 passed in 0.08 seconds.
  - Syntax compilation exited 0 and `pip check` found no broken requirements.
  - Forbidden behavior scan found no matches.
  - Final confirmation: 35 tests passed in 0.13 seconds; compilation and
    dependency checks passed; `git diff --check` exited 0 with only Git's normal
    Windows line-ending conversion warnings.
  - First hardening run: 41 tests passed in 0.08 seconds.
  - First cursor-guard run: 43 passed and 1 failed at the exact resume boundary.
  - Post-fix cursor-guard run: 44 tests passed in 0.06 seconds.
  - Final hardening run: 45 tests passed in 0.18 seconds.
  - Final syntax compilation and dependency validation passed.
  - `git diff --check` exited 0 with normal Windows line-ending warnings only.
  - A broad safety scan matched only a test name containing `click`; the refined
    application-source API scan found no forbidden calls.
  - Final thumb–middle revision: 52 tests passed in 0.08 seconds.
  - Syntax compilation and dependency validation passed.
  - Obsolete two-cycle identifiers were absent from `src` and `tests`.
  - Application-source safety scan found no forbidden OS-input/storage/network
    calls; `git diff --check` exited 0 with normal line-ending warnings only.
- Manual checks:
  - None yet.
- Performance observations:
  - No webcam measurement was performed; no performance target is claimed.

## Known Limitations

- Recognition and clicks remain dry-run only.
- Provisional thresholds/timings have automated coverage but no live calibration.
- Palm geometry can vary with strong foreshortening; representative manual tests
  remain necessary.
- Full gesture conflict resolution begins only as later gestures are added.
- Thumb–middle double-click recognition has not been manually re-evaluated after
  this revision.
- Click/drag disambiguation remains deferred to Iteration 6; this pass freezes
  all pinch candidates and active pinches.

## Final State

Iteration 3 is complete. Thumb–index pinch recognition is scale-independent,
hysteretic, temporally validated, cooldown-protected, transition-only, and reset
safely on tracking loss. The preview exposes state and dry-run count, and no
operating-system click API exists.

The final approved revision maps thumb–middle pinch to one double-click action,
prioritizes it over thumb–index left click, reduces hold latency, freezes cursor
output before pinch articulation, and reseeds smoothing immediately on release.
All behavior remains dry-run.

## Next Iteration

Iteration 4 (thumb–ring-finger right-click recognition) requires explicit user
approval and will not begin automatically.

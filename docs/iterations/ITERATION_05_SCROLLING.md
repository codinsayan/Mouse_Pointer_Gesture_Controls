# Iteration 05: Scrolling

## Objective

Recognize an index-and-middle-fingers-raised pose followed by vertical or
horizontal hand movement and produce exclusive, scale-independent dry-run scroll
steps without emitting operating-system input.

## Scope

- Deterministic finger-extension and palm-anchor geometry.
- A two-finger scroll recognizer with pose hysteresis and temporal validation.
- Scale-normalized two-axis displacement, movement dead zone, axis lock, and
  bounded steps.
- Exclusive conflict handling so scrolling cannot generate clicks.
- Cursor freeze during scroll candidate, active, and release states.
- Tracking-loss reset and dry-run overlay state, axis, direction, and totals.
- Webcam-free unit tests and synchronized documentation.

Real wheel events, dragging, calibration UI, and Iteration 6 work are out of
scope.

## Starting State

Iterations 1–4 are committed at `2518d53`. The application has local one-hand
tracking, dry-run cursor mapping, and exclusive dry-run left, double, and right
click recognition. The user approved Iteration 5. One pre-existing working-tree
change only removes the final newline from `controls/cursor.py`; it will be
preserved and not treated as Iteration 5 work. The last recorded suite has 61
passing tests.

## Implementation Plan

1. Add scale-independent extension ratios and a stable palm vertical anchor.
2. Implement a deterministic two-finger scroll recognizer with entry/release
   hysteresis, activation/release holds, and monotonic timestamps.
3. Convert accumulated vertical displacement into signed, bounded dry-run steps.
4. Resolve scroll before clicks; claimed scroll frames reset click recognizers
   and freeze cursor output.
5. Reset scroll/cursor/click state on tracking loss.
6. Add validated provisional configuration and overlay status.
7. Test geometry, hysteresis, timing, direction, dead zone, conflict resolution,
   bounds, and reset behavior.
8. Run verification, update project documentation, and stop before Iteration 6.

### Approved horizontal-scrolling extension

1. Extend the stable palm anchor from Y to X/Y.
2. Select and lock the first dominant movement axis for each active pose.
3. Emit bounded signed left/right steps without mixing axes.
4. Add horizontal counters/status and deterministic regressions.
5. Re-run all checks and update Iteration 5 documentation.

### Approved horizontal-pose revision

1. Keep index+middle exclusively for vertical scrolling.
2. Bind middle+ring exclusively to horizontal scrolling.
3. Remove movement-derived dominant-axis selection.
4. Test pose selection, off-axis suppression, hysteresis, and click conflicts.
5. Re-run all checks and synchronize Iteration 5 documentation.

## Implementation Steps

- Read repository instructions, product/architecture/status documents, and all
  four previous iteration records.
- Inspected Git history, working-tree state, application boundaries, gesture
  features/coordinator, cursor guard, configuration, overlay, and tests.
- Identified and preserved the pre-existing newline-only `cursor.py` change.
- Created this plan before changing application code.
- Extended gesture features with scale-independent extension ratios for all four
  fingers and a wrist/MCP palm Y anchor.
- Added a scroll state machine with inactive, candidate, active, and releasing
  states; separate entry/retention thresholds; activation/release holds; signed
  step quantization; monotonic timestamps; and reset.
- Added a top-level gesture coordinator that gives scroll candidates/active/
  release frames exclusive ownership and resets click recognizers.
- Integrated cursor freezing and smoothing reseed across scroll ownership.
- Added dry-run up/down totals, last direction, and current state to the overlay.
- Added provisional validated settings without adding dependencies.
- Added deterministic geometry, scale, pose, timing, hysteresis, direction,
  bounding, reset, conflict, and configuration tests.
- Reopened Iteration 5 at the user's request and added left/right scrolling.
- Initially extended the palm anchor from Y-only to X/Y and locked each active
  gesture to the first axis crossing the movement dead zone.
- Added horizontal signed output, left/right totals, axis status, and regression
  tests for direction, scale independence, dominant-axis selection, and reset.
- User feedback requested a distinct horizontal pose rather than sharing the
  vertical pose and inferring intent from movement.
- Replaced dominant-axis selection with pose-bound axes: index+middle selects
  vertical, while middle+ring selects horizontal.
- Added tests proving off-axis movement is ignored, each pose uses independent
  hysteresis, and both scroll poses suppress click candidates.

## Files Created or Modified

- `docs/iterations/ITERATION_05_SCROLLING.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `docs/iterations/ITERATION_04_RIGHT_CLICK.md` (factual wording correction)
- `PRD.md`
- `ARCHITECTURE.md`
- `README.md`
- `src/gesture_controls/app.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/gestures/__init__.py`
- `src/gesture_controls/gestures/features.py`
- `src/gesture_controls/gestures/interactions.py`
- `src/gesture_controls/gestures/scroll.py`
- `src/gesture_controls/ui/overlay.py`
- `tests/test_config.py`
- `tests/test_gesture_features.py`
- `tests/test_scroll.py`

The pre-existing newline-only modification in
`src/gesture_controls/controls/cursor.py` remains present but was not edited as
part of Iteration 5.

## Technical Decisions

- Scroll output remains dry-run; PyAutoGUI is not introduced.
- Use joint geometry normalized by palm scale, never pixel thresholds.
- Use a palm/MCP two-axis anchor rather than fingertips so finger articulation
  does not masquerade as hand movement.
- Scrolling claims interaction before click recognition and resets click state,
  satisfying the requirement that scrolling cannot click.
- Defaults are provisional until representative webcam testing is documented.
- Vertical entry requires index/middle extension ratios at least `0.18` and
  ring/little at most `0.10`. Horizontal entry requires middle/ring at least
  `0.18` and index/little at most `0.10`. Retention uses extension `0.10` and
  folded `0.18`, forming hysteresis instead of one jitter-prone boundary.
- Provisional activation/release holds are `0.06/0.05 s`. One step represents
  `0.08` palm-scale units and output is capped at three steps per frame.
- Positive steps mean upward hand movement; negative steps mean downward hand
  movement. Oversized displacement is capped and discarded rather than queued,
  avoiding continued output after the hand stops.
- Positive horizontal steps mean rightward movement and negative horizontal
  steps mean leftward movement in mirrored preview coordinates.
- The validated finger pose binds the axis until full release; displacement on
  the other axis is ignored.
- The movement-derived dominant-axis approach was rejected after user feedback
  because vertical and horizontal intent should be expressed by different poses.
- Both scroll poses keep the little finger folded and at least one additional
  finger folded, distinguishing them from an open palm reserved for later pause.

## Bugs and Problems Encountered

### Bug 1: Click-path test used a helper alias as a dataclass field
- Symptom: The first expanded suite reported 1 failure and 76 passes with
  `TypeError: PinchFeatures.__init__() got an unexpected keyword argument 'left'`.
- Reproduction: Run the initial version of
  `test_clicks_are_evaluated_when_scroll_pose_is_inactive`.
- Root cause: The test passed the helper parameter name `left` to
  `dataclasses.replace`, but the dataclass field is `left_pinch_ratio`.
- Fix: Construct the fixture through the helper with `left=0.2` directly.
- Files changed: `tests/test_scroll.py`.
- Verification: The next full suite passed 77 tests; final validation passed 79.
- Regression prevention: Keep synthetic gesture construction behind the named
  helper instead of mixing helper aliases with dataclass field names.

### Bug 2: One pose made horizontal intent ambiguous
- Symptom: Horizontal and vertical scrolling used the same index+middle pose, so
  the recognizer inferred intent from the first hand movement rather than an
  explicit gesture.
- Reproduction: Hold index+middle and begin with unintended diagonal movement;
  the dominant component selects the scroll axis for the full pose.
- Root cause: Axis selection was coupled to noisy motion direction instead of
  finger configuration.
- Fix: Bind index+middle to vertical and middle+ring to horizontal; ignore
  movement on the pose's other axis.
- Files changed: `scroll.py`, `test_scroll.py`, and Iteration 5 documentation.
- Verification: Distinct-pose and off-axis regression tests pass in the full
  suite recorded below.
- Regression prevention: Keep tests for both pose mappings, pose-specific
  hysteresis, off-axis suppression, and click conflict handling.

## Tests and Verification

- Commands executed:
  - Read required documentation and source/test files with PowerShell.
  - `git status --short --branch`
  - `git log --oneline --decorate -8`
  - `git diff -- src/gesture_controls/controls/cursor.py`
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` (initial run)
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` (post-fix run)
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` (validation run)
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - `git diff --check`
  - Source scans for OS-input, frame-writing, and network-client calls.
- Results:
  - Iterations 1–4 are committed at `2518d53` on `main`, tracking `origin/main`.
  - A pre-existing newline-only change in `cursor.py` was identified and left
    untouched.
  - Initial expanded run: 1 failed and 76 passed due to the test-fixture bug
    documented above.
  - Post-fix run: 77 tests passed in 0.10 seconds.
  - Final validation after stricter integer configuration checks: 79 tests passed
    in 0.13 seconds.
  - Final repository verification: 79 tests passed in 0.08 seconds.
  - Horizontal extension verification: 81 tests passed in 0.11 seconds.
  - Compilation and dependency validation passed again after the horizontal
    extension; safety scans remained clear and `git diff --check` reported only
    normal Windows line-ending warnings.
  - Distinct middle+ring pose revision: 84 tests passed in 0.14 seconds;
    compilation and dependency validation passed.
  - Final pose-switch regression run: 85 tests passed in 0.25 seconds;
    compilation succeeded and dependency validation found no broken requirements.
  - Final safety and whitespace scans remained clear, apart from normal Windows
    LF-to-CRLF conversion warnings.
  - Syntax compilation succeeded with exit code 0.
  - Dependency validation reported `No broken requirements found.`
  - `git diff --check` found no whitespace errors; it emitted only normal Windows
    LF-to-CRLF conversion warnings.
  - Safety scans found no OS-input, frame-writing, or network-client calls.
- Manual checks:
  - No live webcam check was performed in this environment. The user must verify
    pose ergonomics, all four direction conventions, pose selection, sensitivity,
    and perceived latency locally.
- Performance observations:
  - Deterministic tests do not measure webcam FPS or end-to-end scroll latency;
    no performance target is claimed.

## Known Limitations

- Thresholds and movement scale are not yet calibrated with representative
  webcams.
- Middle+ring pose ergonomics and separation from adjacent finger movement need
  live webcam testing.
- Scroll actions remain dry-run only.

## Final State

Iteration 5 is complete in dry-run form. Two-finger pose recognition is
scale-independent, hysteretic, temporally validated, and exclusive over clicks.
Index+middle vertical or middle+ring horizontal palm movement creates bounded
signed steps on the pose-bound axis. The cursor stays frozen during scroll ownership, tracking loss
resets state, and the overlay exposes state/axis/direction/totals. No
operating-system input API was added.

## Next Iteration

Iteration 6 (dragging and gesture state-machine hardening) requires explicit
user approval and will not begin automatically.

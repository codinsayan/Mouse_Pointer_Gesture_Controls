# Iteration 02: Cursor Mapping and Smoothing

## Objective

Convert the tracked index fingertip into a stable, bounded pointer target using
deterministic coordinate mapping and frame-rate-independent smoothing, while
remaining dry-run only and generating no operating-system input events.

## Scope

- Configurable normalized camera active region.
- Mapping into normalized screen coordinates with clamping.
- Time-aware exponential smoothing.
- Minimum movement threshold to suppress tiny target changes.
- Reset after tracking loss so reacquisition cannot interpolate from stale state.
- Preview visualization and status for raw and smoothed dry-run targets.
- Webcam-free unit tests for all deterministic cursor calculations.

PyAutoGUI, real mouse movement, gesture enablement, clicks, scrolling, dragging,
calibration UI, and Iteration 3 work are out of scope.

## Starting State

Iteration 1 is complete. The foreground application mirrors a webcam preview,
tracks one hand with MediaPipe Tasks, draws landmarks, and reports status. Twelve
automated tests pass under Python 3.12. The application contains no OS-input code.
The directory is not a Git repository, so no Git working-tree status is available.

## Implementation Plan

1. Add validated cursor-region and smoothing settings.
2. Implement pure normalized coordinate mapping and clamping.
3. Implement a stateful, time-aware exponential smoother with reset.
4. Combine mapping, smoothing, and a normalized minimum-movement threshold in a
   dry-run cursor pipeline.
5. Feed index landmark 8 into the pipeline and reset it on tracking loss.
6. Visualize raw and emitted targets without touching the OS pointer.
7. Add deterministic tests and run all available checks.
8. Synchronize documentation and stop before Iteration 3.

## Implementation Steps

- Re-read repository instructions and all required project/current-iteration
  documents.
- Inspected source/test files, dependency configuration, and Git status.
- Defined the dry-run-only Iteration 2 safety boundary and implementation plan.
- Added immutable point, active-region, and cursor-update value types.
- Implemented clamped camera-region to normalized-screen mapping.
- Implemented an elapsed-time exponential smoother with monotonic timestamp
  validation and reset behavior.
- Added a cursor pipeline that advances smoothing continuously while emitting a
  new dry-run output only after the minimum movement threshold is met.
- Added validated cursor defaults to application configuration.
- Integrated landmark 8 into the foreground loop and reset cursor state whenever
  the hand is absent.
- Added active-region and smoothed-target visualization to the preview overlay.
- Added mapping, clamping, smoothing, frame-rate independence, threshold, reset,
  and configuration tests.

## Files Created or Modified

- `docs/iterations/ITERATION_02_POINTER_MOVEMENT.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `README.md`
- `src/gesture_controls/app.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/controls/__init__.py`
- `src/gesture_controls/controls/cursor.py`
- `src/gesture_controls/ui/overlay.py`
- `tests/test_config.py`
- `tests/test_cursor.py`

This list will be updated as implementation proceeds.

## Technical Decisions

- Index fingertip landmark 8 is the pointer source.
- Internal cursor coordinates remain normalized, leaving physical screen-size
  discovery and PyAutoGUI integration for a later explicitly approved scope.
- Smoothing is elapsed-time based rather than a fixed per-frame average.
- Tracking loss resets the filter to avoid stale-state cursor jumps.
- No new dependency is needed in this iteration.
- Provisional defaults are 12%/10%/12%/10% left/top/right/bottom margins,
  an 80 ms smoothing time constant, and 0.002 normalized minimum movement. They
  are configurable and are not claimed as final before manual testing.
- The movement threshold compares the continuously advancing smoothed position
  with the last output position; sub-threshold changes accumulate naturally.
- The preview projects normalized screen output back onto the camera window only
  as a dry-run visualization; it is not a physical screen mapping claim.

## Bugs and Problems Encountered

No implementation bugs were encountered. The first full test run passed.

## Tests and Verification

- Commands executed:
  - Read required documentation with PowerShell.
  - Inspected `git status`, source/test file inventory, and `pyproject.toml`.
  - `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider`
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
- Results:
  - Directory is not a Git repository.
  - Iteration 1 is complete and Iteration 2 is now user-approved.
  - Initial implementation run: 22 tests passed in 0.07 seconds.
  - Syntax compilation exited 0.
  - `pip check` reported no broken requirements.
  - Final run after the additional frame-rate-independence regression test:
    23 tests passed in 0.07 seconds.
  - Final post-formatting confirmation: 23 tests passed in 0.05 seconds and
    syntax compilation exited 0.
  - Forbidden input/storage/network-client scan found no matches.
  - CLI `--help` exited successfully.
- Manual checks:
  - None yet.
- Performance observations:
  - No webcam measurement was performed; no latency or FPS target is claimed.

## Known Limitations

- Preview targets are normalized dry-run values, not OS cursor coordinates.
- The pointer source is not yet gated on an index-raised recognizer; it follows
  landmark 8 whenever a hand is present.
- Provisional settings need manual webcam calibration.
- No interactive webcam check was performed in this session.

## Final State

Iteration 2 is complete. The application now produces a clamped, smoothed,
thresholded normalized cursor target from landmark 8, visualizes it in dry-run
mode, and clears all cursor history on tracking loss. It has no OS-input module
and cannot move the real pointer.

## Next Iteration

Iteration 3 (left-click recognition) requires explicit user approval and will not
begin automatically.

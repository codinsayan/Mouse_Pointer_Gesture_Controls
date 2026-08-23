# Iteration 07: Calibration and Settings

## Objective

Provide validated local settings profiles, configurable reported handedness,
cursor sensitivity/smoothing, and an interactive landmark-only cursor-region
calibration workflow without enabling operating-system input.

## Scope

- Versioned local JSON settings profiles with strict validation.
- CLI profile loading, explicit default-profile creation, and command-line
  camera/model overrides.
- Configurable `any`, `left`, or `right` reported hand preference.
- Configurable cursor sensitivity alongside existing smoothing and thresholds.
- Interactive cursor calibration from transient index-tip coordinates only.
- Robust percentile bounds, minimum sample/span validation, apply/cancel status,
  and optional persistence to the explicitly selected profile.
- Overlay instructions/status and deterministic webcam-free tests.

Real OS input, background behavior, system tray UI, and Iteration 8 are out of
scope. No frames are stored; calibration retains only normalized point values
for the duration of one calibration session.

## Starting State

Iterations 1-6 are implemented in the working tree on top of committed Iteration
5 revision `0dc55c5`. The baseline deterministic suite has 121 passing tests.
Configuration is a validated frozen dataclass but is only constructed from CLI
camera/model arguments. Cursor region and smoothing are provisional defaults,
there is no profile serialization, handedness filtering, or calibration workflow,
and all behavior remains dry-run.

## Implementation Plan

1. Add strict, versioned JSON profile loading/saving without new dependencies.
2. Add dominant-hand and cursor-sensitivity settings and deterministic selection
   and mapping behavior.
3. Add a robust calibration accumulator that stores normalized points only and
   derives a bounded region from percentiles plus padding.
4. Add preview keys to start, apply, or cancel calibration; suspend normal
   gesture processing while samples are collected.
5. Apply calibration in memory and persist only when the user supplied a profile
   path; add an explicit CLI command for writing a default profile.
6. Expose configuration/calibration state in the overlay and README.
7. Test schema/type/unknown-field errors, round trips, override precedence,
   handedness selection, sensitivity, calibration bounds, and failures.
8. Run all verification, synchronize documentation, and stop before Iteration 8.

## Implementation Steps

- Read repository instructions, PRD, architecture, implementation index, current
  Iteration 6 document, CLI, tracking adapter, configuration, application, and
  README.
- Inspected Git state/history and preserved the uncommitted Iteration 6 work.
- Ran the baseline suite: 121 tests passed in 0.16 seconds.
- Created this plan before Iteration 7 application-code changes.
- Added schema-versioned JSON profile conversion, strict field/type validation,
  semantic validation, atomic save, load, and explicit override handling.
- Added CLI profile loading and default-profile generation without camera startup.
- Added reported-handedness selection and configurable cursor sensitivity for
  normal pointer mapping and relative fist-drag movement.
- Added transient point-only calibration with quantiles, padding, minimum sample
  count, and two-axis coverage validation.
- Integrated `C` start, `Enter` apply, and `X` cancel. Gesture processing is
  suspended during collection; successful apply rebuilds cursor mapping.
- Added optional selected-profile persistence without writing CLI camera/model
  overrides back to the profile.
- Added overlay preference/calibration state, sample count, persistence mode, and
  controls.
- Added deterministic tests and synchronized product, architecture, README,
  iteration, and implementation-index documentation.

## Files Created or Modified

- `docs/iterations/ITERATION_07_CALIBRATION_AND_SETTINGS.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `.gitignore`
- `PRD.md`
- `ARCHITECTURE.md`
- `README.md`
- `src/gesture_controls/app.py`
- `src/gesture_controls/main.py`
- `src/gesture_controls/errors.py`
- `src/gesture_controls/config/__init__.py`
- `src/gesture_controls/config/profile.py`
- `src/gesture_controls/config/settings.py`
- `src/gesture_controls/controls/__init__.py`
- `src/gesture_controls/controls/calibration.py`
- `src/gesture_controls/controls/cursor.py`
- `src/gesture_controls/tracking/__init__.py`
- `src/gesture_controls/tracking/selection.py`
- `src/gesture_controls/ui/overlay.py`
- `tests/conftest.py`
- `tests/test_calibration.py`
- `tests/test_config.py`
- `tests/test_cursor.py`
- `tests/test_hand_selection.py`
- `tests/test_profile.py`

## Technical Decisions

- Profiles use standard-library JSON and an explicit schema version; no new
  dependency is justified.
- Profiles may contain no unknown fields. JSON value types are checked before
  `AppConfig` semantic validation.
- Command-line camera/model arguments override profile values only when supplied.
- Hand preference applies to MediaPipe's reported handedness label. Mirrored-feed
  handedness still requires a representative manual check.
- Calibration uses index-tip coordinate samples only, never pixels or frames.
- Region derivation uses robust percentiles rather than raw extrema to reduce the
  influence of brief tracking outliers.
- Calibration persistence occurs only after an explicit apply key and only to a
  profile path selected by the user.
- Profile saves serialize the complete current schema. Relative `Path` values
  retain native Windows representation and round-trip as `Path` objects.
- Runtime CLI camera/model overrides are separated from the profile copy so a
  calibration save does not silently make temporary overrides permanent.
- Sensitivity scales mapped cursor output around normalized screen center and
  relative drag displacement, keeping the two movement modes consistent.
- Calibration collection resets gesture state each frame and freezes cursor
  output, so calibration cannot increment dry-run gesture actions.

## Bugs and Problems Encountered

### Bug 1: Cursor test patch displaced existing assertions

- Symptom: The first expanded suite reported three cursor-test failures,
  including an undefined `mapper` and an exact floating-point comparison.
- Reproduction: Run the first expanded suite after adding sensitivity tests.
- Root cause: The new test block was inserted before the tail of an existing
  relative-mapper test, leaving its assertions inside the new parametrized test;
  one new assertion also used exact equality for a floating-point result.
- Fix: Restored the original assertions to their test and used `pytest.approx`
  for computed coordinates.
- Files changed: `tests/test_cursor.py`.
- Verification: All cursor tests pass in the final suite.
- Regression prevention: Sensitivity now has separate normal-mapping,
  relative-drag, validation, and existing reset/clamp tests.

### Bug 2: Pytest temporary directory was inaccessible in the managed Windows environment

- Symptom: Four profile tests errored with `PermissionError: [WinError 5]` while
  pytest tried to enumerate its default user temp directory. A workspace
  `--basetemp` attempt also became inaccessible after pytest applied permissions.
- Reproduction: Use pytest's built-in `tmp_path` fixture in this managed shell.
- Root cause: Pytest's temp-directory permission behavior conflicts with the
  managed Windows filesystem ACL policy; application profile I/O was not the
  failing operation.
- Fix: Replaced `tmp_path` in these tests with a repository fixture that creates
  unique ignored `.test-artifacts` directories using ordinary workspace
  permissions and removes its exact directory after each test.
- Files changed: `.gitignore`, `tests/conftest.py`, `tests/test_profile.py`.
- Verification: The ordinary documented pytest command completes with 151 tests
  passing and no temp-directory errors.
- Regression prevention: Future filesystem tests can reuse `local_tmp_path` in
  this Windows-managed environment.

## Tests and Verification

- Commands executed:
  - Required documentation/source inspection with PowerShell.
  - `git status --short --branch`
  - `git log -5 --oneline`
  - `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - `.\.venv\Scripts\python.exe -m gesture_controls.main --help`
  - `rg -n -i <OS-input/frame-write/network patterns> src tests`
  - `git diff --check`
- Results:
  - Baseline: 121 tests passed in 0.16 seconds.
  - First expanded run: 3 failed, 144 passed, and 4 profile-test setup errors.
  - After test-structure/temp-fixture fixes: 1 path-format assertion failed and
    150 tests passed in 0.32 seconds.
  - Final cleanup rerun: 151 tests passed in 0.24 seconds; preceding final runs
    passed the same 151 tests in 0.20 and 0.25 seconds.
  - Syntax compilation completed with exit code 0 and no output.
  - Dependency check: `No broken requirements found.`
  - CLI help completed with exit code 0 and lists profile/override commands.
  - Safety scan found no OS input, frame-writing, or network-call matches.
- Manual checks:
  - Default-profile creation was executed through its automated CLI test without
    starting a camera.
  - Interactive live webcam calibration was not available in this session.
- Performance observations:
  - The final deterministic suite completed in 0.24 seconds. This is not a live
    FPS, calibration usability, or end-to-end latency measurement.

## Known Limitations

- Handedness labels after mirroring require manual confirmation.
- Calibration thresholds and sensitivity require representative user testing.
- Profile editing is JSON/CLI based; graphical settings UI belongs to Iteration 9.
- Calibration cannot prove comfortable real-screen coverage while OS pointer
  output remains dry-run.

## Final State

Iteration 7 is complete. Local settings profiles are strict, versioned, and
atomically written only on explicit commands/apply. Reported-hand preference,
cursor sensitivity, and all existing settings are configurable. Cursor
calibration collects transient normalized index-tip points, validates robust
coverage, applies immediately, and optionally persists to a selected profile.
No camera frames or operating-system input events are stored or generated.

## Next Iteration

Iteration 8 requires explicit user approval and will not begin automatically.

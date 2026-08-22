# Iteration 01: Foundation and Webcam Landmark Prototype

## Objective

Create the documented project foundation and a safe, foreground-only prototype
that mirrors a webcam feed and visualizes one hand using MediaPipe Tasks without
emitting operating-system input.

## Scope

Repository documentation, Python package structure, dependency configuration,
OpenCV camera capture, one-hand Hand Landmarker integration, landmark/status
overlay, clean keyboard shutdown, targeted failures, and deterministic tests.

## Starting State

On 2026-08-23, the repository root was empty and was not a Git repository.
There were no existing files or uncommitted changes. Installed interpreters were
Python 3.12, 3.13, and 3.14; `python` selected 3.13.5. Git 2.46.2, pip 25.2,
pytest 9.0.2, and FFmpeg were found. `uv`, Poetry, Pipenv, Ruff, mypy,
PyInstaller were not found.

## Implementation Plan

1. Establish requirements, architecture, privacy/safety rules, and iteration log.
2. Add validated configuration and framework-neutral deterministic utilities.
3. Add OpenCV camera and MediaPipe Tasks adapters.
4. Add the mirrored preview loop, overlay, status, and clean shutdown.
5. Test utilities and setup/error paths without a webcam.
6. Resolve dependencies under Python 3.12, then pin the tested versions.
7. Run available tests/checks and synchronize all documentation.

## Implementation Steps

- Inspected the directory, Git status, Python launcher, pip, and developer tools.
- Verified official MediaPipe Tasks API and current package metadata before
  selecting Python 3.12 and `VIDEO` running mode.
- Created initial project governance and design documents.
- Implemented validated configuration, explicit application errors, OpenCV camera
  ownership, a MediaPipe Tasks Hand Landmarker adapter, neutral landmark values,
  an FPS meter, a landmark/status overlay, and the foreground application loop.
- Added webcam-free unit tests for configuration, geometry, pixel conversion,
  FPS measurement, result state, and missing-model handling.
- Created a Python 3.12 virtual environment and tested dependency candidates.
- Replaced an initial duplicate OpenCV installation with one `cv2` provider.
- Selected and installed MediaPipe 0.10.21 after discovering that current
  MediaPipe releases disclose SDK utilization telemetry; this release retains
  the Hand Landmarker Tasks API and predates the reported change.
- Downloaded the official Google model to the ignored asset location, verified
  its SHA-256, and successfully initialized and closed the tracker.
- Ran the automated suite, syntax compilation, dependency validation, and a scan
  for forbidden OS-input/frame-writing calls.

## Files Created or Modified

- `AGENTS.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `docs/IMPLEMENTATION_DETAILS.md`
- `docs/iterations/ITERATION_01_FOUNDATION.md`
- `.gitignore`
- `README.md`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `assets/models/README.md`
- `src/gesture_controls/` package modules for application, camera, config,
  diagnostics, errors, tracking, and UI
- `tests/` configuration, FPS, tracking, geometry, and model-error tests

This list will be updated as implementation proceeds.

## Technical Decisions

- Use Python 3.12 rather than the shell-default 3.13 because current MediaPipe
  package classifiers explicitly include 3.12.
- Use Hand Landmarker Tasks `VIDEO` mode for a simple one-frame-at-a-time bounded
  pipeline. Live-stream callbacks are deferred unless later measurements justify
  their extra synchronization complexity.
- Store only the expected official model path in the repository, not camera data.
- Do not include PyAutoGUI or any OS-input module in Iteration 1.
- Pin MediaPipe 0.10.21 for privacy compatibility. Newer MediaPipe must not be
  adopted without an explicit, verified telemetry decision.
- Use `opencv-contrib-python` as the only package providing `cv2`, because the
  selected MediaPipe package already depends on it.
- The application displays handedness returned for the already-mirrored frame;
  this must be confirmed during the manual camera check.

## Bugs and Problems Encountered

### Bug 1: Python 3.12 virtual-environment bootstrap was denied
- Symptom: `venv` left a partial environment and `ensurepip` raised
  `PermissionError` while writing its temporary pip wheel.
- Reproduction: Run `py -3.12 -m venv .venv` in the managed sandbox.
- Root cause: The managed filesystem policy denied the child Python process
  access to both the user temp root and an attempted workspace temp directory.
- Fix: Re-created the project-owned `.venv` with approved environment access.
- Files changed: `.venv` only (ignored).
- Verification: pip upgraded and installed the project successfully.
- Regression prevention: README uses standard local setup; if this occurs in a
  managed environment, grant Python access rather than changing application code.

### Bug 2: Two OpenCV distributions provided the same namespace
- Symptom: Initial resolution installed `opencv-python` 4.14 and MediaPipe's
  `opencv-contrib-python` 5.0 together, both owning `cv2`.
- Reproduction: Install the initial direct `opencv-python<5` range with
  MediaPipe 1.0.1.
- Root cause: MediaPipe declared a different OpenCV distribution transitively.
- Fix: Declare and pin only `opencv-contrib-python==4.11.0.86`.
- Files changed: `pyproject.toml`, `requirements.txt`.
- Verification: `cv2.__version__` is 4.11.0 and `pip check` reports no issues.
- Regression prevention: Keep exactly one OpenCV wheel distribution in the
  dependency set and validate it with `pip check` after upgrades.

### Bug 3: Temporary-directory fixture failed under managed permissions
- Symptom: 11 tests passed and one errored during setup with `PermissionError`
  while pytest enumerated its user temp directory.
- Reproduction: Run the suite with a test requesting `tmp_path` in this managed
  environment.
- Root cause: The test did not need temporary storage, but `tmp_path` coupled it
  to an inaccessible host directory.
- Fix: Use a guaranteed-missing repository-relative path and assert its absence.
- Files changed: `tests/test_hand_landmarker.py`.
- Verification: all 12 tests passed on the next run.
- Regression prevention: Webcam-free unit tests avoid filesystem fixtures unless
  file behavior is the subject under test.

## Tests and Verification

- Commands executed:
  - Repository/tool inventory using PowerShell, `rg --files`, `git status`,
    `py --list-paths`, version checks, and command discovery.
  - `py -3.12 -m compileall -q src tests`
  - `python -m pytest` (initial environment check)
  - Created `.venv`, installed candidates, inspected API/version symbols, and
    finalized the pins in `requirements*.txt`.
  - Downloaded the model from Google's versioned MediaPipe model URL.
  - Initialized and closed `HandLandmarkerTracker` using the official model.
  - `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider`
  - `.\.venv\Scripts\python.exe -m compileall -q src tests`
  - `.\.venv\Scripts\python.exe -m pip check`
  - Searched `src` and `tests` for PyAutoGUI, mouse/keyboard actions, OpenCV
    video writing, and image writing.
- Results:
  - Repository was empty and not initialized as Git.
  - Environment results are recorded under Starting State.
  - Initial Python 3.13 suite: 11 passed with one cache-permission warning.
  - Final Python 3.12 suite: 12 passed in 0.03 seconds.
  - Syntax compilation exited 0; `pip check` found no broken requirements.
  - MediaPipe 0.10.21 exposes `HandLandmarker` and `RunningMode.VIDEO`.
  - Tracker initialization and close succeeded with the 7,819,105-byte model.
  - Model SHA-256:
    `FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1`.
  - Forbidden-behavior scan found no matches.
- Manual checks:
  - Webcam preview was not opened in this managed session; camera acquisition,
    visible landmarks, window controls, and disconnection handling need a local
    interactive check.
- Performance observations:
  - No camera FPS or latency measurement was made; no target is claimed achieved.

## Known Limitations

- No live webcam/manual visualization test has been performed.
- Camera read failure handling is explicit but was not induced on hardware.
- MediaPipe emits native informational/warning lines during tracker startup.
- MediaPipe 0.10.21 is an intentional privacy pin; the lack of telemetry has not
  been independently verified with a network audit.

## Final State

Iteration 1 implementation is complete. The prototype can attempt the webcam,
initialize the current Hand Landmarker Tasks API, mirror frames, draw all 21
landmarks/connections, show status, and shut down visibly. It has no OS-input or
frame-storage behavior. Automated checks pass; the manual webcam check remains
documented rather than falsely claimed.

## Next Iteration

Iteration 2 (cursor mapping and smoothing) requires explicit user approval and
must not begin as part of this run.

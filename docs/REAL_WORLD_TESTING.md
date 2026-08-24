# Real-World Testing Protocol

This protocol is the Iteration 10 checklist for a Windows 10/11 laptop with a
webcam. Camera processing remains local. Do not record the screen or camera feed
unless a tester separately chooses to do so outside Gesture Controls.

## Safety Preconditions

1. Run the automated suite first:

   ```powershell
   .\scripts\run_verification.ps1
   ```

2. Close applications containing unsaved work. Use a disposable text document,
   browser page, and desktop test folder for controlled input checks.
3. Confirm `P` and global `Ctrl+Alt+Shift+G` are available for emergency pause.
4. Start with real OS input unchecked. Complete all dry-run cases first.
5. Never mark a case passed without observing its expected result.

## Dry-Run Launch

```powershell
.\.venv\Scripts\python.exe -m gesture_controls.main --settings-ui --config settings.json
```

Press **Start camera** with **Allow real OS input for this run** unchecked. The
runtime must start Disabled. Keep the camera preview visible while testing.

## Dry-Run Cases

| ID | Action | Expected result | Status |
| -- | ------ | --------------- | ------ |
| RW-01 | Start the camera with no hand visible | Dashboard/preview remain Disabled; no action count changes | Not run |
| RW-02 | Show the configured dominant hand | Hand becomes Ready and confidence/FPS update | Not run |
| RW-03 | Raise only the index finger and enable | Dry-run cursor follows smoothly; tiny changes are suppressed | Not run |
| RW-04 | Pinch thumb-index once and hold | Exactly one left-click count; cursor freezes during candidate/hold | Not run |
| RW-05 | Pinch thumb-middle once | Exactly one double-click count and no left click | Not run |
| RW-06 | Pinch thumb-little once | Exactly one right-click count and no left/double click | Not run |
| RW-07 | Hold index+middle pose and stroke vertically twice, returning between strokes | Same-direction scrolling continues; return motion does not reverse the page | Not run |
| RW-08 | Hold middle+ring pose and stroke horizontally | Horizontal count changes only; no click or vertical count | Not run |
| RW-09 | Hold a fist for at least 250 ms, move, then open | One drag start, precise movement, and one drag end | Not run |
| RW-10 | Contract and expand thumb-ring in the former zoom pose | No action, cursor freeze, click, or keyboard event occurs | Not run |
| RW-11 | Hold an open palm for at least two seconds | Control remains enabled; open palm has no pause behavior | Not run |
| RW-12 | Remove the hand after enabling, then show it again | Control stays Enabled but stops output; hand recovery resumes gestures automatically | Not run |
| RW-13 | Enable before Hand is Ready, then show the accepted hand | Enabled waits without output, then begins tracking automatically | Not run |
| RW-14 | Resize dashboard to approximately 600x450 | Cards stack; both scrollbars make every action/footer reachable | Not run |
| RW-15 | Hide to tray, reopen, emergency-pause, then quit safely | Each tray action works and shutdown returns control cleanly | Not run |

## Controlled Real-Input Cases

Run these only after every applicable dry-run case passes. Start a new camera
session, check **Allow real OS input for this run**, confirm the warning, and use
a disposable target.

| ID | Action | Expected result | Status |
| -- | ------ | --------------- | ------ |
| RW-16 | Enable and move with index raised | Pointer follows without large jumps or unintended actions | Not run |
| RW-17 | Perform each click pinch once | Target receives one left, one double, and one right click respectively | Not run |
| RW-18 | Scroll a long page vertically and horizontally | Page moves consistently and return strokes do not undo travel | Not run |
| RW-19 | Select disposable text with fist drag | Mouse button holds during motion and releases on opening | Not run |
| RW-20 | Start a drag, then press `P` | Drag releases immediately and control is Disabled | Not run |
| RW-21 | Start a drag, remove the hand, then return it | Drag releases immediately; Enabled waits and later resumes without a held button | Not run |
| RW-22 | Press global `Ctrl+Alt+Shift+G` with another app focused | Control pauses and any held input releases | Not run |
| RW-23 | Quit from the dashboard/tray during an enabled session | Process closes without a held button or further events | Not run |

## Observation Record

Record the following without including personal paths, images, or camera frames:

- Windows version and laptop model:
- Webcam resolution shown/used:
- Average displayed processed FPS:
- Lowest observed processed FPS:
- Pointer latency impression:
- Lighting conditions:
- Dominant-hand setting:
- Failed case IDs and exact reproduction:
- Unexpected action conflicts:
- Safety-release result:

Measured FPS and latency targets must not be claimed from this blank protocol.
Update the relevant iteration document after an actual session.

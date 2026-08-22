# Repository Instructions

Before modifying code, read `PRD.md`, `ARCHITECTURE.md`, and
`docs/IMPLEMENTATION_DETAILS.md`. Identify the current iteration and read its
document under `docs/iterations/`.

- Work only within the current user-approved iteration. Do not automatically
  continue to another iteration.
- Preserve user changes and inspect the working tree before editing.
- Keep webcam data local. Never add frame recording, permanent frame storage,
  telemetry, or cloud upload behavior.
- Do not enable real mouse events during unrelated tests. Automated tests must
  use deterministic logic or a fake mouse controller.
- Run relevant tests after changes. Never hide failures or unresolved bugs.
- Update the current iteration document after every implementation or debugging
  session, including actual commands and results.
- Update `docs/IMPLEMENTATION_DETAILS.md` whenever iteration status changes.
- Avoid new dependencies unless they are justified and tested for compatibility.
- The application must start with gesture control disabled. Any future input
  controller must provide dry-run behavior and release held buttons on tracking
  loss, exceptions, and shutdown.


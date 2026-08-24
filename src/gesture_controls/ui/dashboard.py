"""Native Windows-first settings dashboard and system-tray integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from gesture_controls.errors import DashboardInitializationError

from .runtime import ManagedGestureRuntime, RuntimeSnapshot
from .settings_model import (
    DashboardSettings,
    load_dashboard_profile,
    save_dashboard_profile,
)

BG = "#0b1020"
SURFACE = "#121a2c"
SURFACE_ALT = "#182238"
TEXT = "#f4f7fb"
MUTED = "#98a7bd"
ACCENT = "#6ee7d8"
ACCENT_ACTIVE = "#4fd1c5"
DANGER = "#fb7185"
BORDER = "#26334d"
MIN_DASHBOARD_CONTENT_WIDTH = 700
WIDE_LAYOUT_BREAKPOINT = 900


def dashboard_layout_mode(width: int) -> str:
    """Choose a card layout without depending on a live Tk instance."""
    content_width = max(MIN_DASHBOARD_CONTENT_WIDTH, width)
    return "wide" if content_width >= WIDE_LAYOUT_BREAKPOINT else "stacked"


def mousewheel_units(delta: int) -> int:
    """Normalize Windows wheel deltas into Tk scroll units."""
    if delta == 0:
        return 0
    magnitude = max(1, abs(delta) // 120)
    return -magnitude if delta > 0 else magnitude


def control_toggle_presentation(
    *, running: bool, tracking_ready: bool, control_state: str
) -> tuple[str, bool]:
    """Return the two-state control label and whether it can be toggled."""
    enabled = control_state == "enabled"
    if enabled:
        return "Disable control", running
    return "Enable control", running


def create_tray_image() -> Any:
    """Create the tray icon in memory; no camera or generated file is involved."""
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((5, 5, 59, 59), radius=16, fill=SURFACE_ALT)
    draw.ellipse((17, 13, 47, 43), outline=ACCENT, width=5)
    draw.line((32, 30, 32, 53), fill=ACCENT, width=5)
    draw.line((22, 50, 42, 50), fill=ACCENT, width=5)
    return image


def _run_tray_process(connection: Any) -> None:
    """Own pystray in an isolated process so a stuck backend cannot block exit."""
    try:
        import pystray

        def action(name: str) -> Callable[..., None]:
            return lambda _icon, _item: connection.send(("action", name))

        icon = pystray.Icon(
            "gesture-controls",
            create_tray_image(),
            "Gesture Controls — stopped",
            pystray.Menu(
                pystray.MenuItem(
                    "Open Gesture Controls", action("show"), default=True
                ),
                pystray.MenuItem("Emergency pause", action("pause")),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit safely", action("quit")),
            ),
        )

        def receive_commands(ready_icon: Any) -> None:
            ready_icon.visible = True
            connection.send(("ready", None))
            while True:
                kind, value = connection.recv()
                if kind == "stop":
                    ready_icon.stop()
                    return
                if kind == "title":
                    ready_icon.title = value

        icon.run(setup=receive_commands)
    except (EOFError, OSError):
        pass
    except Exception as exc:
        try:
            connection.send(("error", str(exc)))
        except (EOFError, OSError):
            pass
    finally:
        connection.close()


class TrayController:
    def __init__(
        self,
        schedule: Callable[[Callable[[], None]], None],
        show: Callable[[], None],
        pause: Callable[[], None],
        quit_app: Callable[[], None],
        process_context: Any | None = None,
    ) -> None:
        if process_context is None:
            from multiprocessing import get_context

            process_context = get_context("spawn")

        self._schedule = schedule
        self._actions = {"show": show, "pause": pause, "quit": quit_app}
        self._connection, self._child_connection = process_context.Pipe()
        self._process = process_context.Process(
            target=_run_tray_process,
            args=(self._child_connection,),
            name="gesture-controls-tray",
            daemon=True,
        )
        self._started = False
        self.available = False
        self.error: str | None = None

    def start(self) -> None:
        self._started = True
        self._process.start()
        self._child_connection.close()

    def poll_actions(self) -> None:
        if not self._started:
            return
        try:
            while self._connection.poll():
                kind, value = self._connection.recv()
                if kind == "ready":
                    self.available = True
                elif kind == "error":
                    self.error = value or "Unknown system-tray error"
                    self.available = False
                elif kind == "action" and value in self._actions:
                    self._schedule(self._actions[value])
        except (EOFError, OSError):
            self.available = False

    def update(self, snapshot: RuntimeSnapshot) -> None:
        if not self._started or not self._process.is_alive():
            return
        mode = "REAL" if snapshot.real_output else "DRY RUN"
        try:
            self._connection.send(
                (
                    "title",
                    f"Gesture Controls — {snapshot.control_state.upper()} — {mode}",
                )
            )
        except (EOFError, OSError):
            self.available = False

    def stop(self) -> None:
        if not self._started:
            return
        try:
            if self._process.is_alive():
                self._connection.send(("stop", None))
                self._process.join(timeout=2.0)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=1.0)
        finally:
            self._connection.close()
        self._started = False
        self.available = False


class DashboardApp:
    POLL_MILLISECONDS = 120

    def __init__(self, root: Any, profile_path: Path) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.profile_path = Path(profile_path)
        self.config, existed = load_dashboard_profile(self.profile_path)
        settings = DashboardSettings.from_config(self.config)
        self.runtime = ManagedGestureRuntime()
        self._quitting = False
        self._tray: TrayController | None = None

        self.pointer_speed = tk.IntVar(value=settings.pointer_speed)
        self.scroll_speed = tk.IntVar(value=settings.scroll_speed)
        self.sensitivity = tk.DoubleVar(value=settings.sensitivity)
        self.dominant_hand = tk.StringVar(value=settings.dominant_hand)
        self.real_input = tk.BooleanVar(value=False)
        self.status_title = tk.StringVar(value="Ready")
        self.status_detail = tk.StringVar(
            value=("Loaded local profile" if existed else "Using defaults — save to create profile")
        )
        self.hand_status = tk.StringVar(value="Not running")
        self.confidence_status = tk.StringVar(value="—")
        self.fps_status = tk.StringVar(value="—")
        self.profile_display = tk.StringVar(value=str(self.profile_path))
        self.pointer_value = tk.StringVar(value=str(settings.pointer_speed))
        self.scroll_value = tk.StringVar(value=str(settings.scroll_speed))
        self.sensitivity_value = tk.StringVar(value=f"{settings.sensitivity:.1f}×")

        self._configure_window()
        self._configure_styles(ttk)
        self._build_layout(tk, ttk)
        self.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self._start_tray()
        self.root.after(self.POLL_MILLISECONDS, self._poll_runtime)

    def _configure_window(self) -> None:
        self.root.title("Gesture Controls")
        self.root.geometry("940x700")
        self.root.minsize(520, 400)
        self.root.configure(bg=BG)

    def _configure_styles(self, ttk: Any) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background=BG)
        style.configure("Card.TFrame", background=SURFACE)
        style.configure("Header.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 24))
        style.configure("Subheader.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI Semibold", 13))
        style.configure("Body.TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Value.TLabel", background=SURFACE, foreground=ACCENT, font=("Segoe UI Semibold", 11))
        style.configure("Status.TLabel", background=SURFACE_ALT, foreground=ACCENT, font=("Segoe UI Semibold", 12), padding=(12, 8))
        style.configure("Accent.TButton", background=ACCENT, foreground=BG, borderwidth=0, padding=(15, 10), font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", ACCENT_ACTIVE), ("disabled", BORDER)], foreground=[("disabled", MUTED)])
        style.configure("Quiet.TButton", background=SURFACE_ALT, foreground=TEXT, borderwidth=0, padding=(12, 9), font=("Segoe UI", 10))
        style.map("Quiet.TButton", background=[("active", BORDER), ("disabled", SURFACE)], foreground=[("disabled", MUTED)])
        style.configure("Danger.TButton", background=DANGER, foreground=BG, borderwidth=0, padding=(12, 9), font=("Segoe UI Semibold", 10))
        style.map("Danger.TButton", background=[("active", "#f43f5e"), ("disabled", BORDER)])
        style.configure("App.Horizontal.TScale", background=SURFACE, troughcolor=BORDER)
        style.configure("App.TCombobox", fieldbackground=SURFACE_ALT, background=SURFACE_ALT, foreground=TEXT, arrowcolor=ACCENT)
        style.configure("App.TCheckbutton", background=SURFACE, foreground=TEXT, font=("Segoe UI", 9))
        style.map("App.TCheckbutton", background=[("active", SURFACE)])

    def _build_layout(self, tk: Any, ttk: Any) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            shell,
            background=BG,
            borderwidth=0,
            highlightthickness=0,
        )
        vertical = ttk.Scrollbar(
            shell, orient="vertical", command=self.canvas.yview
        )
        horizontal = ttk.Scrollbar(
            shell, orient="horizontal", command=self.canvas.xview
        )
        self.canvas.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        shell.rowconfigure(0, weight=1)
        shell.columnconfigure(0, weight=1)

        outer = ttk.Frame(self.canvas, style="App.TFrame", padding=(30, 24))
        self._content_window = self.canvas.create_window(
            (0, 0), window=outer, anchor="nw"
        )
        self._outer = outer
        self._layout_mode: str | None = None
        outer.columnconfigure(0, weight=3)
        outer.columnconfigure(1, weight=2)
        outer.rowconfigure(1, weight=1)

        self.header = ttk.Frame(outer, style="App.TFrame")
        ttk.Label(self.header, text="Gesture Controls", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.header,
            text="Local webcam control · Safe by default · No frames leave this computer",
            style="Subheader.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        settings_card = ttk.Frame(outer, style="Card.TFrame", padding=24)
        self.settings_card = settings_card
        settings_card.columnconfigure(0, weight=1)
        ttk.Label(settings_card, text="Movement settings", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(settings_card, text="Tune movement without changing gesture thresholds or calibration.", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 20))

        self._add_slider(ttk, settings_card, 2, "Pointer speed", "Response speed; higher feels quicker", self.pointer_speed, self.pointer_value, 1, 10, self._pointer_changed)
        self._add_slider(ttk, settings_card, 3, "Scroll speed", "OS wheel clicks per recognized step", self.scroll_speed, self.scroll_value, 1, 20, self._scroll_changed)
        self._add_slider(ttk, settings_card, 4, "Sensitivity", "Amplifies movement around screen center", self.sensitivity, self.sensitivity_value, 0.1, 3.0, self._sensitivity_changed)

        hand_row = ttk.Frame(settings_card, style="Card.TFrame")
        hand_row.grid(row=5, column=0, sticky="ew", pady=(18, 0))
        hand_row.columnconfigure(0, weight=1)
        ttk.Label(hand_row, text="Dominant hand", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        hand = ttk.Combobox(hand_row, textvariable=self.dominant_hand, values=("any", "right", "left"), state="readonly", width=12, style="App.TCombobox")
        hand.grid(row=0, column=1, sticky="e")

        profile_row = ttk.Frame(settings_card, style="Card.TFrame")
        profile_row.grid(row=6, column=0, sticky="ew", pady=(26, 0))
        profile_row.columnconfigure(0, weight=1)
        self.save_button = ttk.Button(profile_row, text="Save settings", style="Accent.TButton", command=self._save)
        self.save_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.choose_button = ttk.Button(profile_row, text="Choose profile", style="Quiet.TButton", command=self._choose_profile)
        self.choose_button.grid(row=0, column=1, sticky="e")
        ttk.Label(settings_card, textvariable=self.profile_display, style="Muted.TLabel", wraplength=500).grid(row=7, column=0, sticky="w", pady=(10, 0))

        status_card = ttk.Frame(outer, style="Card.TFrame", padding=24)
        self.status_card = status_card
        status_card.columnconfigure(0, weight=1)
        ttk.Label(status_card, text="Control center", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(status_card, textvariable=self.status_title, style="Status.TLabel").grid(row=1, column=0, sticky="ew", pady=(16, 8))
        ttk.Label(status_card, textvariable=self.status_detail, style="Muted.TLabel", wraplength=310).grid(row=2, column=0, sticky="w")

        metrics = ttk.Frame(status_card, style="Card.TFrame")
        metrics.grid(row=3, column=0, sticky="ew", pady=(18, 12))
        metrics.columnconfigure(1, weight=1)
        self._metric(ttk, metrics, 0, "Hand", self.hand_status)
        self._metric(ttk, metrics, 1, "Confidence", self.confidence_status)
        self._metric(ttk, metrics, 2, "Processed FPS", self.fps_status)

        ttk.Checkbutton(status_card, text="Allow real OS input for this run", variable=self.real_input, style="App.TCheckbutton").grid(row=4, column=0, sticky="w", pady=(6, 12))
        self.start_button = ttk.Button(status_card, text="Start camera", style="Accent.TButton", command=self._start_runtime)
        self.start_button.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self.toggle_button = ttk.Button(status_card, text="Enable / Disable", style="Quiet.TButton", command=self.runtime.toggle)
        self.toggle_button.grid(row=6, column=0, sticky="ew", pady=4)
        self.pause_button = ttk.Button(status_card, text="Emergency pause", style="Danger.TButton", command=self.runtime.emergency_pause)
        self.pause_button.grid(row=7, column=0, sticky="ew", pady=4)
        self.stop_button = ttk.Button(status_card, text="Stop camera safely", style="Quiet.TButton", command=self.runtime.stop)
        self.stop_button.grid(row=8, column=0, sticky="ew", pady=4)
        self.hide_button = ttk.Button(
            status_card,
            text="Hide to system tray",
            style="Quiet.TButton",
            command=self._hide_to_tray,
        )
        self.hide_button.grid(row=9, column=0, sticky="ew", pady=(16, 0))

        self.footer = ttk.Frame(outer, style="App.TFrame")
        ttk.Label(
            self.footer,
            text="Shortcuts: E toggle · P emergency pause · Ctrl+Alt+Shift+G global emergency",
            style="Subheader.TLabel",
            wraplength=520,
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(self.footer, text="Quit safely", style="Quiet.TButton", command=self._quit_safely).grid(row=0, column=1, sticky="e")
        self.footer.columnconfigure(0, weight=1)

        outer.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_scroll_content)
        self.root.bind("<MouseWheel>", self._scroll_vertical, add="+")
        self.root.bind("<Shift-MouseWheel>", self._scroll_horizontal, add="+")
        self._apply_responsive_layout("wide")
        self._update_button_states(RuntimeSnapshot())

    def _update_scroll_region(self, _event: Any = None) -> None:
        bounds = self.canvas.bbox("all")
        if bounds is not None:
            self.canvas.configure(scrollregion=bounds)

    def _resize_scroll_content(self, event: Any) -> None:
        content_width = max(MIN_DASHBOARD_CONTENT_WIDTH, event.width)
        self.canvas.itemconfigure(self._content_window, width=content_width)
        self._apply_responsive_layout(dashboard_layout_mode(event.width))

    def _apply_responsive_layout(self, mode: str) -> None:
        if mode == self._layout_mode:
            return
        self._layout_mode = mode
        for row in (1, 2, 3):
            self._outer.rowconfigure(row, weight=0)
        if mode == "wide":
            self._outer.columnconfigure(0, weight=3)
            self._outer.columnconfigure(1, weight=2)
            self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 22))
            self.settings_card.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
            self.status_card.grid(row=1, column=1, sticky="nsew", padx=(12, 0), pady=0)
            self.footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(18, 0))
            self._outer.rowconfigure(1, weight=1)
        else:
            self._outer.columnconfigure(0, weight=1)
            self._outer.columnconfigure(1, weight=0)
            self.header.grid(row=0, column=0, columnspan=1, sticky="ew", pady=(0, 22))
            self.settings_card.grid(row=1, column=0, sticky="ew", padx=0)
            self.status_card.grid(row=2, column=0, sticky="ew", padx=0, pady=(16, 0))
            self.footer.grid(row=3, column=0, columnspan=1, sticky="ew", pady=(18, 0))
        self.root.after_idle(self._update_scroll_region)

    def _scroll_vertical(self, event: Any) -> str | None:
        units = mousewheel_units(event.delta)
        if units and self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(units, "units")
            return "break"
        return None

    def _scroll_horizontal(self, event: Any) -> str | None:
        units = mousewheel_units(event.delta)
        if units and self.canvas.xview() != (0.0, 1.0):
            self.canvas.xview_scroll(units, "units")
            return "break"
        return None

    def _add_slider(self, ttk: Any, parent: Any, row: int, title: str, description: str, variable: Any, value_variable: Any, minimum: float, maximum: float, command: Callable[[str], None]) -> None:
        block = ttk.Frame(parent, style="Card.TFrame")
        block.grid(row=row, column=0, sticky="ew", pady=(0, 18))
        block.columnconfigure(0, weight=1)
        ttk.Label(block, text=title, style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(block, textvariable=value_variable, style="Value.TLabel").grid(row=0, column=1, sticky="e")
        ttk.Label(block, text=description, style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 8))
        ttk.Scale(block, from_=minimum, to=maximum, variable=variable, command=command, style="App.Horizontal.TScale").grid(row=2, column=0, columnspan=2, sticky="ew")

    @staticmethod
    def _metric(ttk: Any, parent: Any, row: int, label: str, variable: Any) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Label(parent, textvariable=variable, style="Body.TLabel").grid(row=row, column=1, sticky="e", pady=3)

    def _pointer_changed(self, value: str) -> None:
        rounded = int(round(float(value)))
        self.pointer_speed.set(rounded)
        self.pointer_value.set(str(rounded))

    def _scroll_changed(self, value: str) -> None:
        rounded = int(round(float(value)))
        self.scroll_speed.set(rounded)
        self.scroll_value.set(str(rounded))

    def _sensitivity_changed(self, value: str) -> None:
        rounded = round(float(value), 1)
        self.sensitivity.set(rounded)
        self.sensitivity_value.set(f"{rounded:.1f}×")

    def _dashboard_settings(self) -> DashboardSettings:
        return DashboardSettings(
            int(self.pointer_speed.get()),
            int(self.scroll_speed.get()),
            float(self.sensitivity.get()),
            self.dominant_hand.get(),
        )

    def _save(self) -> bool:
        from tkinter import messagebox

        try:
            self.config = save_dashboard_profile(
                self.profile_path, self.config, self._dashboard_settings()
            )
        except Exception as exc:
            messagebox.showerror("Could not save settings", str(exc), parent=self.root)
            return False
        self.status_detail.set("Settings saved atomically. Restart the camera to apply changes.")
        return True

    def _choose_profile(self) -> None:
        from tkinter import filedialog, messagebox

        if self.runtime.running:
            messagebox.showinfo("Camera is running", "Stop the camera before changing profiles.", parent=self.root)
            return
        selected = filedialog.asksaveasfilename(
            parent=self.root,
            title="Choose Gesture Controls profile",
            defaultextension=".json",
            filetypes=(("JSON settings", "*.json"), ("All files", "*.*")),
            initialfile=self.profile_path.name,
            initialdir=str(self.profile_path.parent),
        )
        if not selected:
            return
        try:
            self.profile_path = Path(selected)
            self.profile_display.set(str(self.profile_path))
            self.config, existed = load_dashboard_profile(self.profile_path)
            settings = DashboardSettings.from_config(self.config)
            self.pointer_speed.set(settings.pointer_speed)
            self.scroll_speed.set(settings.scroll_speed)
            self.sensitivity.set(settings.sensitivity)
            self.dominant_hand.set(settings.dominant_hand)
            self._pointer_changed(str(settings.pointer_speed))
            self._scroll_changed(str(settings.scroll_speed))
            self._sensitivity_changed(str(settings.sensitivity))
            self.status_detail.set("Profile loaded" if existed else "New profile selected — save to create it")
        except Exception as exc:
            messagebox.showerror("Could not load profile", str(exc), parent=self.root)

    def _start_runtime(self) -> None:
        from tkinter import messagebox

        if not self._save():
            return
        real = bool(self.real_input.get())
        if real and not messagebox.askyesno(
            "Allow real OS input?",
            "Real pointer, click, scroll, and drag events will be allowed for this run.\n\nThe runtime still starts disabled. Use Emergency Pause at any time.",
            icon="warning",
            parent=self.root,
        ):
            return
        if self.runtime.start(self.config, self.profile_path, real):
            self.status_title.set("Starting")
            self.status_detail.set("Opening the local camera preview. Control remains disabled.")

    def _poll_runtime(self) -> None:
        snapshot = self.runtime.bridge.snapshot
        self.status_title.set(snapshot.control_state.replace("_", " ").title())
        self.status_detail.set(snapshot.reason)
        self.hand_status.set(
            "Ready"
            if snapshot.tracking_ready
            else ("Detected · not accepted" if snapshot.hand_detected else "Not detected")
        )
        self.confidence_status.set("—" if snapshot.confidence is None else f"{snapshot.confidence:.2f}")
        self.fps_status.set("—" if not snapshot.running else f"{snapshot.fps:.1f}")
        self._update_button_states(snapshot)
        if self._tray is not None:
            self._tray.poll_actions()
            self._tray.update(snapshot)
            if self._tray.error:
                self.status_detail.set(f"System tray unavailable: {self._tray.error}")
        if self._quitting and not self.runtime.running:
            self._finish_quit()
            return
        self.root.after(self.POLL_MILLISECONDS, self._poll_runtime)

    def _update_button_states(self, snapshot: RuntimeSnapshot) -> None:
        import tkinter as tk

        running = self.runtime.running
        toggle_text, can_toggle = control_toggle_presentation(
            running=running,
            tracking_ready=snapshot.tracking_ready,
            control_state=snapshot.control_state,
        )
        self.start_button.configure(state=(tk.DISABLED if running else tk.NORMAL))
        self.toggle_button.configure(
            text=toggle_text,
            state=(tk.NORMAL if can_toggle else tk.DISABLED),
        )
        self.pause_button.configure(state=(tk.NORMAL if running else tk.DISABLED))
        self.stop_button.configure(state=(tk.NORMAL if running else tk.DISABLED))
        self.save_button.configure(state=(tk.DISABLED if running else tk.NORMAL))
        self.choose_button.configure(state=(tk.DISABLED if running else tk.NORMAL))
        tray_ready = self._tray is not None and self._tray.available
        self.hide_button.configure(state=(tk.NORMAL if tray_ready else tk.DISABLED))

    def _start_tray(self) -> None:
        try:
            self._tray = TrayController(
                lambda callback: self.root.after(0, callback),
                self._show,
                self.runtime.emergency_pause,
                self._quit_safely,
            )
            self._tray.start()
        except Exception as exc:
            self._tray = None
            self.status_detail.set(f"System tray unavailable: {exc}")

    def _show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _hide_to_tray(self) -> None:
        if self._tray is None:
            self._quit_safely()
        elif not self._tray.available:
            self.status_detail.set(
                "System tray is not ready; the dashboard was kept visible."
            )
        else:
            self.root.withdraw()

    def _quit_safely(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        self.status_title.set("Stopping safely")
        self.runtime.stop()
        if not self.runtime.running:
            self._finish_quit()

    def _finish_quit(self) -> None:
        if self._tray is not None:
            self._tray.stop()
            self._tray = None
        self.root.destroy()


def run_dashboard(profile_path: Path) -> None:
    try:
        import tkinter as tk

        root = tk.Tk()
        DashboardApp(root, profile_path)
        root.mainloop()
    except Exception as exc:
        if isinstance(exc, DashboardInitializationError):
            raise
        raise DashboardInitializationError(
            "Settings dashboard could not start. Verify the Windows desktop "
            "session and Tk installation."
        ) from exc

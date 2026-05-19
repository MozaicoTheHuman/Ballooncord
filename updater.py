from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import subprocess
import sys
import threading
import urllib.request
import tkinter as tk
from tkinter import ttk

REPO_OWNER   = "MozaicoTheHuman"
REPO_NAME    = "Ballooncord"
API_URL      = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
EXE_NAME     = "Ballooncord.exe"
UPDATE_EXE   = "Balloncord_Update.exe"
VERSION_FILE = "version.txt"
CONFIG_FILE  = "discord_balloon_config.json"
FLAG_FILE    = "_balloncord_update.json"

XP_FACE      = "#ECE9D8"
XP_FACE_DARK = "#D4D0C8"
XP_WHITE     = "#FFFFFF"
XP_TEXT      = "#000000"
XP_BORDER    = "#ACA899"
XP_BLUE      = "#0A246A"
XP_BLUE2     = "#3169C6"
XP_FONT      = ("Tahoma", 8)
XP_FONT_BOLD = ("Tahoma", 8, "bold")


def _get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _load_config() -> dict:
    path = os.path.join(_get_base_dir(), CONFIG_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _read_current_version() -> str:
    path = os.path.join(_get_base_dir(), VERSION_FILE)
    try:
        return open(path, encoding="utf-8").read().strip().lstrip("v")
    except Exception:
        return "0.0.0"


def _write_flag(version: str, ready: bool, download_url: str = "") -> None:
    path = os.path.join(_get_base_dir(), FLAG_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": version, "ready": ready,
                       "download_url": download_url}, f)
        print(f"[updater] Flag written -> ready={ready}, version={version}")
    except Exception as e:
        print(f"[updater] Could not write flag file: {e}")


def _version_tuple(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except Exception:
        return (0,)


def _is_newer(remote: str, local: str) -> bool:
    return _version_tuple(remote) > _version_tuple(local)


def _fetch_latest_release() -> tuple[str, str | None] | None:
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": "BalloncordUpdater/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)

        tag = data.get("tag_name", "").lstrip("v")
        if not tag:
            return None

        download_url: str | None = None
        for asset in data.get("assets", []):
            if asset.get("name", "").lower() == EXE_NAME.lower():
                download_url = asset.get("browser_download_url")
                break

        return tag, download_url

    except Exception as e:
        print(f"[updater] GitHub API error: {e}")
        return None


def _hide_console() -> None:
    try:
        kernel32 = ctypes.windll.kernel32
        user32   = ctypes.windll.user32
        hwnd     = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

def _check_only_mode() -> None:
    _hide_console()

    current_ver = _read_current_version()
    print(f"[updater] Current version : {current_ver}")

    result = _fetch_latest_release()
    if result is None:
        print("[updater] Could not reach GitHub. Exiting.")
        return

    remote_tag, download_url = result
    print(f"[updater] Latest release  : {remote_tag}")

    if not _is_newer(remote_tag, current_ver):
        print("[updater] Already up to date. Exiting.")
        return

    print(f"[updater] Update available: {current_ver} -> {remote_tag}")
    _write_flag(remote_tag, ready=False, download_url=download_url or "")
    print("[updater] Flag written. Exiting.")

class UpdaterWindow:

    def __init__(self, version: str, download_url: str) -> None:
        self.version      = version
        self.download_url = download_url
        self.cancelled    = False
        self._cancel_ev   = threading.Event()

        self.root = tk.Tk()
        self.root.title("Balloncord Updater")
        self.root.configure(bg=XP_FACE)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)

        w, h = 420, 155
        sw   = self.root.winfo_screenwidth()
        sh   = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        self._build()
        self.root.after(120, self._start_download)

    def _build(self) -> None:
        title_bar = tk.Frame(self.root, bg=XP_BLUE, height=26)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        tk.Label(
            title_bar, text="Balloncord Updater",
            bg=XP_BLUE, fg=XP_WHITE, font=XP_FONT_BOLD,
        ).pack(side=tk.LEFT, padx=8, pady=4)

        body = tk.Frame(self.root, bg=XP_FACE, padx=14, pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(
            value=f"Downloading Balloncord v{self.version}..."
        )
        tk.Label(
            body, textvariable=self.status_var,
            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT, anchor="w",
        ).pack(fill=tk.X, pady=(0, 6))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "XP.Horizontal.TProgressbar",
            troughcolor=XP_WHITE,
            background=XP_BLUE2,
            bordercolor=XP_BORDER,
            lightcolor=XP_BLUE2,
            darkcolor=XP_BLUE2,
        )
        self.progress = ttk.Progressbar(
            body, orient="horizontal", length=380, mode="determinate",
            style="XP.Horizontal.TProgressbar",
        )
        self.progress.pack(fill=tk.X, pady=(0, 4))

        detail_row = tk.Frame(body, bg=XP_FACE)
        detail_row.pack(fill=tk.X)

        self.pct_var = tk.StringVar(value="0%")
        tk.Label(
            detail_row, textvariable=self.pct_var,
            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=5, anchor="w",
        ).pack(side=tk.LEFT)

        self.size_var = tk.StringVar(value="")
        tk.Label(
            detail_row, textvariable=self.size_var,
            bg=XP_FACE, fg="#555555", font=XP_FONT, anchor="e",
        ).pack(side=tk.RIGHT)

        btn_strip = tk.Frame(self.root, bg=XP_FACE_DARK, bd=1, relief=tk.FLAT)
        btn_strip.pack(fill=tk.X, side=tk.BOTTOM)
        btn_inner = tk.Frame(btn_strip, bg=XP_FACE_DARK)
        btn_inner.pack(pady=5, padx=8, anchor=tk.E)

        self.cancel_btn = tk.Button(
            btn_inner, text="Cancel", width=10,
            font=XP_FONT, command=self._on_cancel,
            relief=tk.RAISED, bd=2,
            bg=XP_FACE, fg=XP_TEXT,
            activebackground=XP_FACE_DARK,
        )
        self.cancel_btn.pack()

    def _start_download(self) -> None:
        threading.Thread(target=self._download, daemon=True).start()

    def _on_cancel(self) -> None:
        if self.cancelled:
            return
        self.cancelled = True
        self._cancel_ev.set()
        self.status_var.set("Cancelling...")
        self.cancel_btn.config(state=tk.DISABLED)
        dest = os.path.join(_get_base_dir(), UPDATE_EXE)
        try:
            os.remove(dest)
        except Exception:
            pass
        self.root.after(600, self.root.destroy)

    def _download(self) -> None:
        dest = os.path.join(_get_base_dir(), UPDATE_EXE)
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": "BalloncordUpdater/1.0"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                total      = int(r.headers.get("Content-Length", 0))
                downloaded = 0

                with open(dest, "wb") as f:
                    while True:
                        if self._cancel_ev.is_set():
                            return
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.root.after(0, self._update_progress, downloaded, total)

            if not self._cancel_ev.is_set():
                self.root.after(0, self._on_complete, dest)

        except Exception as e:
            if not self.cancelled:
                self.root.after(0, self._on_error, str(e))

    def _update_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            pct = downloaded / total * 100
            self.progress["value"] = pct
            self.pct_var.set(f"{pct:.0f}%")
            self.size_var.set(
                f"{downloaded / 1_048_576:.1f} MB / {total / 1_048_576:.1f} MB"
            )
        else:
            self.size_var.set(f"{downloaded / 1_048_576:.1f} MB")

    def _on_complete(self, new_exe: str) -> None:
        self.progress["value"] = 100
        self.pct_var.set("100%")
        self.cancel_btn.config(state=tk.DISABLED)
        self.status_var.set("Applying update...")
        self.root.update_idletasks()

        base     = _get_base_dir()
        original = os.path.join(base, EXE_NAME)

        try:
            if os.path.exists(original):
                os.remove(original)
            os.rename(new_exe, original)
        except Exception as e:
            self._on_error(f"Could not replace executable: {e}")
            return

        # Update version.txt
        try:
            with open(os.path.join(base, VERSION_FILE), "w", encoding="utf-8") as f:
                f.write(self.version)
        except Exception:
            pass

        self.status_var.set(
            f"Done! Launching Balloncord v{self.version}..."
        )
        self.root.after(900, lambda: self._launch_and_exit(original))

    def _launch_and_exit(self, exe_path: str) -> None:
        try:
            subprocess.Popen(
                [exe_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                close_fds=True,
            )
        except Exception as e:
            print(f"[updater] Failed to launch {exe_path!r}: {e}")
        self.root.destroy()

    def _on_error(self, msg: str) -> None:
        self.status_var.set(f"Error: {msg}")
        self.progress["value"] = 0
        self.cancel_btn.config(
            text="Close", state=tk.NORMAL,
            command=self.root.destroy,
        )

    def run(self) -> None:
        self.root.mainloop()


def _download_mode(version: str, url: str) -> None:
    _hide_console()
    UpdaterWindow(version, url).run()

def main() -> None:
    args = sys.argv[1:]

    if "--download" in args:
        try:
            idx     = args.index("--download")
            version = args[idx + 1]
            url     = args[idx + 2]
        except (IndexError, ValueError) as e:
            print(f"[updater] Bad --download args: {e}")
            sys.exit(1)
        _download_mode(version, url)
    else:
        _check_only_mode()


if __name__ == "__main__":
    main()

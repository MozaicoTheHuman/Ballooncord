from __future__ import annotations                                          

import asyncio
import ctypes
import ctypes.wintypes
import glob
import io
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import winreg
import winsound
import zlib
import tkinter as tk
from tkinter import ttk
from datetime import datetime

def _setup_crash_log():
    log_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    log_path = os.path.join(log_dir, "discord_balloon_crash.log")
    import traceback
    def _excepthook(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n{datetime.now()}\n{msg}")
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    sys.excepthook = _excepthook

_setup_crash_log()

shell32  = ctypes.windll.shell32
user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def _hide_console() -> None:
    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 0)

_hide_console()

user32.DefWindowProcW.restype  = ctypes.wintypes.LPARAM
user32.DefWindowProcW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.CreatePopupMenu.restype  = ctypes.wintypes.HMENU
user32.AppendMenuW.argtypes     = [ctypes.wintypes.HMENU, ctypes.wintypes.UINT,
                                    ctypes.c_size_t, ctypes.wintypes.LPCWSTR]
user32.AppendMenuW.restype      = ctypes.wintypes.BOOL
user32.TrackPopupMenu.restype   = ctypes.wintypes.BOOL
user32.TrackPopupMenu.argtypes  = [ctypes.wintypes.HMENU, ctypes.wintypes.UINT,
                                    ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    ctypes.wintypes.HWND, ctypes.c_void_p]
user32.GetCursorPos.argtypes    = [ctypes.POINTER(ctypes.wintypes.POINT)]
user32.DestroyMenu.argtypes     = [ctypes.wintypes.HMENU]
user32.PostMessageW.argtypes    = [ctypes.wintypes.HWND, ctypes.wintypes.UINT,
                                    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]

WM_USER     = 0x0400
WM_TRAYICON = WM_USER + 1
WM_DESTROY  = 0x0002

NIM_ADD    = 0
NIM_MODIFY = 1
NIM_DELETE = 2

NIF_MESSAGE = 0x01
NIF_ICON    = 0x02
NIF_TIP     = 0x04
NIF_INFO    = 0x10

NIIF_INFO    = 0x01
NIIF_NOSOUND = 0x10

NIN_BALLOONSHOW      = 0x0402  
NIN_BALLOONUSERCLICK = 0x0405
NIN_BALLOONHIDE      = 0x0403  
NIN_BALLOONTIMEOUT   = 0x0404 

WM_RBUTTONUP     = 0x0205
WM_LBUTTONDBLCLK = 0x0203
WM_CONTEXTMENU   = 0x007B

SW_RESTORE  = 9
SW_SHOW     = 5

IDI_INFORMATION = 32516
IDI_QUESTION    = 32514

IDM_OPEN             = 1001
IDM_LOG              = 1002
IDM_EXIT             = 1003
IDM_AUTOLOGIN        = 1004
IDM_STATUS_ONLINE    = 1005
IDM_STATUS_IDLE      = 1006
IDM_STATUS_DND       = 1007
IDM_STATUS_INVISIBLE = 1008
IDM_VC_LEAVE         = 1011
IDM_SETTINGS         = 1013

MF_STRING    = 0x00
MF_CHECKED   = 0x08
MF_GRAYED    = 0x01
MF_SEPARATOR = 0x800
MF_POPUP     = 0x10

DISCORD_API = "https://discord.com/api/v9"
GATEWAY_URL = "wss://gateway.discord.gg/?v=9&encoding=json&compress=zlib-stream"

                                                                           
VERSION = "1.1.2"

DND_STATUSES   = {"dnd"}

_my_status: str = "online" 
_token:     str = ""   
_gw_ws    = None   
_gw_loop: asyncio.AbstractEventLoop | None = None

_vc_guild_id:   str | None = None
_vc_channel_id: str | None = None
_vc_self_mute:  bool = False
_vc_self_deaf:  bool = False

_active_call_channel_id: str | None = None
_outgoing_call_channel_id: str | None = None  
_outgoing_call_time: float = 0.0     

_has_unread: bool = False

_unread_channels: set[str] = set()
_state_icon_cache: dict[str, int] = {}
_vc_member_ids: set[str] = set() 
_vc_join_time:  float = 0.0  
_VC_JOIN_GRACE: float = 3.0  

_focused_channel_id: str | None = None
_focus_poll_stop: threading.Event = threading.Event()

def _focus_poll_thread() -> None:
    global _focused_channel_id
    while not _focus_poll_stop.is_set():
        if not _discord_has_focus():
            if _focused_channel_id is not None:
                _focused_channel_id = None
        _focus_poll_stop.wait(timeout=0.5)

def _should_suppress_channel(channel_id: str | None) -> bool:
    if not channel_id:
        return False
    if not _discord_has_focus():
        return False
    return channel_id == _focused_channel_id

def _varint_encode(value: int) -> bytes:

    parts = []
    while value > 127:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts)

def _varint_decode(data: bytes, pos: int) -> tuple[int, int]:

    result = shift = 0
    while True:
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7

def _build_status_field(status: str) -> bytes:

    status_bytes = status.encode("utf-8")
    string_value    = b"\x0a" + _varint_encode(len(status_bytes)) + status_bytes
    status_settings = b"\x0a" + _varint_encode(len(string_value)) + string_value
    return b"\x5a" + _varint_encode(len(status_settings)) + status_settings

def _replace_or_add_field11(proto_bytes: bytes, new_field11: bytes) -> bytes:

    result   = bytearray()
    pos      = 0
    replaced = False

    while pos < len(proto_bytes):
        field_start = pos
        try:
            tag, pos = _varint_decode(proto_bytes, pos)
        except (IndexError, KeyError):
            result.extend(proto_bytes[field_start:])
            break

        wire_type    = tag & 0x07
        field_number = tag >> 3

        try:
            if wire_type == 0:
                _, pos = _varint_decode(proto_bytes, pos)
            elif wire_type == 1:
                pos += 8
            elif wire_type == 2:
                length, pos = _varint_decode(proto_bytes, pos)
                pos += length
            elif wire_type == 5: 
                pos += 4
            else:
                result.extend(proto_bytes[field_start:])
                replaced = True
                break
        except (IndexError, KeyError):
            result.extend(proto_bytes[field_start:])
            replaced = True
            break

        if field_number == 11:
            result.extend(new_field11)
            replaced = True
        else:
            result.extend(proto_bytes[field_start:pos])

    if not replaced:
        result.extend(new_field11)

    return bytes(result)

_last_balloon_url:    str | None = None
_balloon_visible:     bool      = False  
_balloon_pending_sound: bool    = False 
_balloon_pending_key:   str     = "NewMessage"

_balloon_refcount:    int       = 0

_pending_update_info: "dict | None" = None                                                

_SOUND_APP_KEY   = "DiscordBalloonNotifier"

_SOUND_EVENTS: list[tuple[str, str]] = [
    ("NewMessage",   "New Message"),
    ("NewMention",   "New Mention"),
    ("Mute",         "Mute"),
    ("Unmute",       "Unmute"),
    ("Deafen",       "Deafen"),
    ("Undeafen",     "Undeafen"),
    ("JoinCall",     "Join Call"),
    ("LeaveCall",    "Leave Call"),
    ("IncomingCall", "Incoming Call"),
    ("UserJoinedVC", "User Joined VC"),
    ("UserLeftVC",   "User Left VC"),
]

def _register_sound_event() -> None:

    try:
        app_path = rf"AppEvents\Schemes\Apps\{_SOUND_APP_KEY}"
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, app_path,
                                0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "Discord Balloon Notifier")

        for event_key, label in _SOUND_EVENTS:
            label_path = rf"AppEvents\EventLabels\{event_key}"
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, label_path,
                                    0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, label)

            current_path = rf"AppEvents\Schemes\Apps\{_SOUND_APP_KEY}\{event_key}\.Current"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, current_path,
                                    0, winreg.KEY_READ):
                    pass  
            except FileNotFoundError:
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, current_path,
                                        0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "")

            default_path = rf"AppEvents\Schemes\Apps\{_SOUND_APP_KEY}\{event_key}\.Default"
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, default_path,
                                    0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "")

    except Exception as e:
        print(f"[sound] Failed to register sound event: {e}")

def _get_sound_path(event_key: str) -> "str | None":

    cfg = load_config()
    custom = cfg.get("custom_sounds", {}).get(event_key, "")
    if custom and os.path.isfile(custom):
        return custom
    try:
        current_path = rf"AppEvents\Schemes\Apps\{_SOUND_APP_KEY}\{event_key}\.Current"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, current_path,
                            0, winreg.KEY_READ) as key:
            wav_path, _ = winreg.QueryValueEx(key, None)
        if wav_path and os.path.isfile(wav_path):
            return wav_path
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return None

def _get_per_user_sound_path(user_id: str, event: str) -> "str | None":

    if not user_id:
        return None
    cfg = load_config()
    per_user = cfg.get("per_user_sounds", {})
    user_cfg = per_user.get(user_id, {})
    path = user_cfg.get(event, "")
    if path and os.path.isfile(path):
        return path
    return None

def _play_per_user_sound(user_id: str, event: str) -> bool:

    path = _get_per_user_sound_path(user_id, event)
    if not path:
        return False
    group = "message" if event == "message" else "vc_call"
    volume = _get_volume()
    threading.Thread(
        target=_pygame_play, args=(path, volume, group), daemon=True
    ).start()
    print(f"[sound] Per-user sound: user={user_id} event={event}")
    return True

def _get_volume() -> float:

    try:
        return max(0.0, min(1.0, float(load_config().get("sound_volume", 1.0))))
    except Exception:
        return 1.0

_SOUND_GROUP: dict[str, str] = {
    "NewMessage":   "message",
    "NewMention":   "message",
    "Mute":         "vc_toggle",
    "Unmute":       "vc_toggle",
    "Deafen":       "vc_toggle",
    "Undeafen":     "vc_toggle",
    "JoinCall":     "vc_call",
    "LeaveCall":    "vc_call",
    "IncomingCall": "vc_call",
    "UserJoinedVC": "vc_call",
    "UserLeftVC":   "vc_call",
}

_pygame_ok: bool = False
_mixer = None

try:
    import pygame.mixer as _mixer
    _mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    _pygame_ok = True
    print("[sound] pygame.mixer initialized")
except Exception as _e:
    print(f"[sound] pygame.mixer unavailable, falling back to winsound: {_e}")

_group_locks: dict[str, threading.Lock] = {
    "message":   threading.Lock(),
    "vc_toggle": threading.Lock(),
    "vc_call":   threading.Lock(),
}
_group_channel: dict[str, object] = {
    "message":   None,
    "vc_toggle": None,
    "vc_call":   None,
}

_sound_cache: dict[str, tuple[int, object]] = {}
_sound_cache_lock = threading.Lock()

def _clear_sound_cache() -> None:

    with _sound_cache_lock:
        _sound_cache.clear()
    print("[sound] Cache cleared")

def _load_sound(path: str) -> "object | None":

    if not _pygame_ok:
        return None

    try:
        mtime = os.stat(path).st_mtime_ns
    except OSError as e:
        print(f"[sound] Cannot stat '{path}': {e}")
        return None

    with _sound_cache_lock:
        cached = _sound_cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]

    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".wav":
            snd = _mixer.Sound(path)
        else:
            try:
                from pydub import AudioSegment
                seg = AudioSegment.from_file(path)
                buf = io.BytesIO()
                seg.export(buf, format="wav")
                buf.seek(0)
                snd = _mixer.Sound(buf)
            except ImportError:
                snd = _mixer.Sound(path)

        with _sound_cache_lock:
            _sound_cache[path] = (mtime, snd)

        print(f"[sound] Loaded '{os.path.basename(path)}' "
              f"({snd.get_length():.2f}s)")
        return snd

    except Exception as e:
        print(f"[sound] Failed to load '{path}': {e}")
        return None

def _stop_group(group: str) -> None:

    ch = _group_channel.get(group)
    if ch is not None:
        try:
            ch.stop()
        except Exception:
            pass
        _group_channel[group] = None

def _pygame_play(path: str, volume: float, group: str,
                 loops: int = 0) -> "object | None":

    snd = _load_sound(path)
    if snd is None:
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME
                               | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception:
            pass
        return None

    with _group_locks[group]:
        _stop_group(group) 
        ch = snd.play(loops=loops)
        if ch is not None:
            ch.set_volume(max(0.0, min(1.0, volume)))
            _group_channel[group] = ch

    return ch

def _play_notification_sound(event_key: str = "NewMessage") -> None:

    group = _SOUND_GROUP.get(event_key, "message")

    def _play() -> None:
        try:
            wav_path = _get_sound_path(event_key)
            if not wav_path:
                _play_question_beep()
                return
            volume = _get_volume()
            if volume <= 0.0:
                return
            print(f"[sound] Playing {event_key} (group={group}, vol={volume:.2f})")
            _pygame_play(wav_path, volume, group)
        except Exception as e:
            print(f"[sound] Playback error ({event_key}): {e}")

    threading.Thread(target=_play, daemon=True).start()

_incoming_call_stop  = threading.Event()
_outgoing_call_stop  = threading.Event()

def _start_looping_sound(event_key: str,
                          stop_event: threading.Event,
                          label: str,
                          path_override: "str | None" = None) -> threading.Thread:

    group = _SOUND_GROUP.get(event_key, "vc_call")
    stop_event.clear()

    def _loop() -> None:
        try:
            wav_path = path_override or _get_sound_path(event_key)
            if not wav_path:
                return

            snd = _load_sound(wav_path)
            duration = snd.get_length() if snd is not None else 2.0

            while not stop_event.is_set():
                volume = _get_volume()

                if volume <= 0.0:
                    stop_event.wait(timeout=duration)
                    continue

                ch = _pygame_play(wav_path, volume, group)
                if ch is None:
                    stop_event.wait(timeout=duration)
                    continue
                stop_event.wait(timeout=duration + 0.05)

        except Exception as e:
            print(f"[sound] {label} loop error: {e}")

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t

def _stop_looping_sound(stop_event: threading.Event,
                         event_key: str = "IncomingCall") -> None:

    group = _SOUND_GROUP.get(event_key, "vc_call")
    stop_event.set()
    with _group_locks[group]:
        _stop_group(group)

def _start_incoming_call_sound(path_override: "str | None" = None) -> None:
    _start_looping_sound(
        "IncomingCall", _incoming_call_stop, "Incoming call",
        path_override=path_override,
    )

def _stop_incoming_call_sound() -> None:
    _stop_looping_sound(_incoming_call_stop, "IncomingCall")

def _open_sound_control_panel() -> None:

    try:
        subprocess.Popen(["rundll32.exe", "shell32.dll,Control_RunDLL",
                          "mmsys.cpl,,2"], close_fds=True)
    except Exception as e:
        print(f"[sound] Failed to open Sound control panel: {e}")

def _get_base_dir() -> str:

    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_get_base_dir(), "discord_balloon_config.json")

def load_config() -> dict:
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

_log_queue: queue.Queue = queue.Queue()

import builtins
_real_print = builtins.print

def _intercepted_print(*args, sep=" ", end="\n", **kwargs):
    msg = sep.join(str(a) for a in args)
    if _token and _token in msg:
        msg = msg.replace(_token, "[TOKEN]")
    _log_queue.put(msg)
    try:
        _real_print(*args, sep=sep, end=end, **kwargs)
    except Exception:
        pass

builtins.print = _intercepted_print

def _get_langs_dir() -> str:

    return os.path.join(_get_base_dir(), "langs")

    path = os.path.join(_get_langs_dir(), f"{code}.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

_STRINGS_EN_BUILTIN: dict[str, str] = {
    "win_title":           "Discord Balloon Notifier",
    "header_title":        "Discord Balloon Notifier",
    "header_sub":          "Enter your Discord user token to connect.",
    "lbl_token":           "Discord user token:",
    "chk_show":            "Show token",
    "grp_settings":        " Settings ",
    "chk_remember":        "Remember token",
    "chk_autologin":       "Sign in automatically",
    "chk_startup":         "Start with Windows",
    "btn_connect":         "Connect",
    "btn_cancel":          "Cancel",
    "err_no_token":        "Please enter a token.",
    "lbl_language":        "Language / Idioma:",
    "balloon_connected":   "Discord connected",
    "balloon_signed_in":   "Signed in as {name}",
    "balloon_friend_req":  "Friend Request",
    "balloon_friend_body": "{who} sent you a friend request",
    "balloon_incoming":    "Incoming call",
    "balloon_calling":     "{caller} is calling you\u2026",
    "grp_client":          " Open with ",
    "radio_discord":       "Discord",
    "radio_canary":        "Discord Canary",
    "radio_dm":            "Discord Messenger",
    "lbl_dm_path":         "Path to DiscordMessenger.exe:",
    "btn_browse":          "Browse\u2026",
                       
    "menu_voice_header":   "Voice channel",
    "menu_leave_call":     "  \u260e Leave Call",
    "menu_status":         "Status",
    "menu_status_online":  "\u25cf Online",
    "menu_status_idle":    "\u263d Idle",
    "menu_status_dnd":     "\u25a0 Do Not Disturb",
    "menu_status_invis":   "\u25cb Invisible",
    "menu_open_discord":   "Open Discord",
    "menu_open_dm":        "Open Discord Messenger",
    "menu_hide_log":       "Hide Event Log",
    "menu_show_log":       "Show Event Log",
    "menu_autologin":      "Auto-login",
    "menu_settings":       "Settings\u2026",
    "menu_exit":           "Exit Notifier",
    "lang_label":          "English",

    "settings_title":      "Settings",
    "tab_notif_mode":      "Notif. Mode",
    "tab_notif_style":     "Notif. Style",
    "tab_sounds":          "Custom Sounds",
    "tab_icons":           "Tray Icons",
    "tab_per_user":        "Per-User",
    "tab_more":            "More",
    "btn_ok":              "OK",
    "btn_apply":           "Apply",
    "grp_notif_mode":      " Notification Mode ",
    "notif_all_title":     "All messages",
    "notif_all_desc":      "Show a balloon for every new message in non-muted channels/servers.",
    "notif_mention_title": "Mentions only  (@me, @everyone, @here, replies)",
    "notif_mention_desc":  "In servers: only notify when you are directly mentioned.\nDMs are always shown regardless of this setting.",
    "grp_launch":          " On Connect ",
    "chk_auto_open":       "Auto-open Discord when connected",
    "chk_auto_open_desc":  "Launches / brings Discord to focus automatically after signing in.",
    "grp_notif_style":     " Notification Style ",
    "style_instant_title": "Instant  (one balloon per message)",
    "style_instant_desc":  "Every message fires its own balloon immediately.\nBest if you're in few/quiet servers.",
    "style_replace_title": "Replace  (Discord-style)",
    "style_replace_desc":  "New messages replace the active balloon after a cooldown.\nPrevents spam without losing any notification.",
    "style_queue_title":   "Queue  (Discord Messenger-style)",
    "style_queue_desc":    "Messages accumulate silently. The balloon shows a count.\nClick it to open up Discord.",
    "grp_cooldown":        " Replace Cooldown ",
    "lbl_cooldown":        "Cooldown:",
    "lbl_cooldown_note":   "(Replace mode only)",
    "grp_volume":          " Volume ",
    "sounds_hint":         "Set a .wav file for each event. Leave blank for silence.",
    "per_user_hint":       "Play a custom sound when a specific user triggers an event.\nUse the user's Discord ID (18-digit number — enable Developer Mode in Discord).\nMessage sound is ignored in Queue mode.",
    "btn_add_user":        "+ Add User",
    "icons_hint":          "Choose a PNG or ICO icon for each tray state (16\u00d716 or 32\u00d732 recommended).\nLeave blank to keep the default Discord icon for that state.",
    "grp_icons":           " Icons by State ",

                        
    "grp_balloon_sound":      " Balloon Sound Mode ",
    "chk_balloon_sound":      "Use Windows balloon sound (all modes)",
    "chk_balloon_sound_desc": "Play sounds via the Windows notification system instead of pygame.\nThis is how Queue mode works — the OS plays the sound as the balloon appears.\nWhen enabled, per-user and pygame volume controls are bypassed for message sounds.",

                   
    "grp_exit_settings":   " On Exit ",
    "exit_chk_close_discord": "Close Discord on exit",

                 
    "grp_update":              " Updates ",
    "chk_check_updates":       "Check for updates on startup",
    "chk_check_updates_desc":  "Check GitHub for a new version when Balloncord starts.",
    "chk_auto_update":         "Auto-update Balloncord",
    "chk_auto_update_desc":    "Automatically download and install new versions on startup (requires Check for updates).",
    "balloon_update_title":    "Balloncord \u2014 Update available",
    "balloon_update_body":     "A new version ({ver}) is available. Click to download now.",
    "balloon_updated_title":   "Balloncord \u2014 Update ready",
    "balloon_updated_body":    "v{ver} downloaded. Restart Balloncord to apply.",

                 
    "exit_dlg_title":      "Exit",
    "exit_dlg_msg":        "Exit the Discord Balloon Notifier?",
    "exit_chk_also_close": "Also close Discord",
    "exit_chk_remember":   "Don't ask again",
    "exit_btn_exit":       "Exit",
}

_lang_cache: dict[str, dict] = {}

def _get_lang_strings(code: str) -> dict:

    if code not in _lang_cache:
        path = os.path.join(_get_langs_dir(), f"{code}.json")
        try:
            with open(path, encoding="utf-8") as _f:
                _lang_cache[code] = json.load(_f)
        except Exception:
            _lang_cache[code] = {}
    return _lang_cache[code]

def _available_languages() -> list:

    langs_dir = _get_langs_dir()
    results: list = []
    try:
        for fname in sorted(os.listdir(langs_dir)):
            if not fname.lower().endswith(".json"):
                continue
            code = fname[:-5]
            data = _get_lang_strings(code) or {}
            label = data.get("lang_label", code)
            results.append((code, label))
    except OSError:
        pass
    codes = {c for c, _ in results}
    if not results or "en" not in codes:
        results.insert(0, ("en", "English"))
    if "es" not in codes:
        results.append(("es", "Espanol"))
    return results

def _t(key: str, **kwargs) -> str:

    lang = load_config().get("language", "en")
    strings = _get_lang_strings(lang)
    value = strings.get(key)
    if value is None:
        en_strings = _get_lang_strings("en")
        value = en_strings.get(key, _STRINGS_EN_BUILTIN.get(key, key))
    return value.format(**kwargs) if kwargs else value

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize",           ctypes.wintypes.DWORD),
        ("hWnd",             ctypes.wintypes.HWND),
        ("uID",              ctypes.wintypes.UINT),
        ("uFlags",           ctypes.wintypes.UINT),
        ("uCallbackMessage", ctypes.wintypes.UINT),
        ("hIcon",            ctypes.wintypes.HICON),
        ("szTip",            ctypes.c_wchar * 128),
        ("dwState",          ctypes.wintypes.DWORD),
        ("dwStateMask",      ctypes.wintypes.DWORD),
        ("szInfo",           ctypes.c_wchar * 256),
        ("uTimeout",         ctypes.wintypes.UINT),
        ("szInfoTitle",      ctypes.c_wchar * 64),
        ("dwInfoFlags",      ctypes.wintypes.DWORD),
        ("guidItem",         ctypes.c_byte * 16),
        ("hBalloonIcon",     ctypes.wintypes.HICON),
    ]

NIIF_USER = 0x00000004 

MB_ICONQUESTION = 0x00000020

def _play_question_beep() -> None:

    threading.Thread(
        target=lambda: user32.MessageBeep(MB_ICONQUESTION),
        daemon=True,
    ).start()

import urllib.request as _urllib_request
import tempfile        as _tempfile

_pfp_cache:    dict[tuple, str] = {}
_pfp_lock      = threading.Lock()
_avatar_hicon: int = 0 
_orig_hicon:   int = 0

class _GdipStartupInput(ctypes.Structure):
    _fields_ = [
        ("GdiplusVersion",           ctypes.c_uint32),
        ("DebugEventCallback",       ctypes.c_void_p),
        ("SuppressBackgroundThread", ctypes.c_bool),
        ("SuppressExternalCodecs",   ctypes.c_bool),
    ]

_ULongPtr = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

def _pfp_cdn_url(user_id: str, avatar_hash: "str | None") -> str:

    if avatar_hash:
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=64"
    idx = (int(user_id) >> 22) % 6
    return f"https://cdn.discordapp.com/embed/avatars/{idx}.png"

def _download_pfp(user_id: str, avatar_hash: "str | None") -> "str | None":

    if not user_id:
        return None
    key = (user_id, avatar_hash)
    with _pfp_lock:
        cached = _pfp_cache.get(key)
        if cached and os.path.exists(cached):
            return cached
    try:
        fd, path = _tempfile.mkstemp(suffix=".png", prefix="dbn_pfp_")
        os.close(fd)
        req = _urllib_request.Request(
            _pfp_cdn_url(user_id, avatar_hash),
            headers={"User-Agent": "DiscordBalloonNotifier/1.0"},
        )
        with _urllib_request.urlopen(req, timeout=6) as resp, open(path, "wb") as fh:
            fh.write(resp.read())
        with _pfp_lock:
            _pfp_cache[key] = path
        print(f"[avatar] Downloaded: {user_id} -> {os.path.basename(path)}")
        return path
    except Exception as exc:
        print(f"[avatar] Download FAILED WHAT({user_id}): {exc}")
        return None

def _png_to_hicon(png_path: str, size: int = 32) -> int:

    if not png_path or not os.path.exists(png_path):
        print(f"[avatar] _png_to_hicon: file not found → {png_path}")
        return 0
    try:
        gdi = ctypes.WinDLL("gdiplus.dll")
    except OSError as e:
        print(f"[avatar] _png_to_hicon: unable to load gdiplus.dll → {e}")
        return 0

    inp = _GdipStartupInput(GdiplusVersion=1)
    tok = _ULongPtr(0)
    status = gdi.GdiplusStartup(ctypes.byref(tok), ctypes.byref(inp), None)
    if status != 0:
        print(f"[avatar] GdiplusStartup failed (status={status})")
        return 0

    hicon = 0
    try:
        src = ctypes.c_void_p(0)
        wpath = ctypes.create_unicode_buffer(png_path)
        st = gdi.GdipCreateBitmapFromFile(wpath, ctypes.byref(src))
        if st != 0 or not src:
            print(f"[avatar] GdipCreateBitmapFromFile falló (status={st})")
            return 0

        dst = ctypes.c_void_p(0)
        st = gdi.GdipCreateBitmapFromScan0(size, size, 0, 0x0026200A,
                                            None, ctypes.byref(dst))
        if st != 0 or not dst:
            print(f"[avatar] GdipCreateBitmapFromScan0 falló (status={st})")
            gdi.GdipDisposeImage(src)
            return 0

        gfx = ctypes.c_void_p(0)
        if gdi.GdipGetImageGraphicsContext(dst, ctypes.byref(gfx)) == 0 and gfx:
            gdi.GdipGraphicsClear(gfx, ctypes.c_uint(0x00000000))
            gdi.GdipSetInterpolationMode(gfx, 7)
            gdi.GdipDrawImageRectI(gfx, src, 0, 0, size, size)
            gdi.GdipDeleteGraphics(gfx)

        raw = ctypes.wintypes.HICON(0)
        st = gdi.GdipCreateHICONFromBitmap(dst, ctypes.byref(raw))
        if st == 0:
            hicon = raw.value or 0
        else:
            print(f"[avatar] GdipCreateHICONFromBitmap falló (status={st})")

        gdi.GdipDisposeImage(dst)
        gdi.GdipDisposeImage(src)
    finally:
        gdi.GdiplusShutdown(tok)

    print(f"[avatar] HICON loaded: {hicon:#010x} desde {os.path.basename(png_path)}")
    return hicon

def _set_discord_icon_on_window(win: tk.Toplevel) -> None:

    try:
        exe = _find_discord_exe()
        if exe:
            win.iconbitmap(exe)
    except Exception:
        pass 

def _set_tray_icon_handle(hicon: int) -> None:

    if not (_nid and _hwnd) or not hicon:
        return
    tmp = NOTIFYICONDATAW()
    tmp.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    tmp.hWnd   = _hwnd
    tmp.uID    = _nid.uID
    tmp.uFlags = NIF_ICON
    tmp.hIcon  = ctypes.c_void_p(hicon)
    shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(tmp))

def _restore_tray_icon() -> None:

    global _avatar_hicon, _balloon_refcount
    _balloon_refcount = max(0, _balloon_refcount - 1)
    if _balloon_refcount > 0:
        return
    if _avatar_hicon:
        user32.DestroyIcon(ctypes.c_void_p(_avatar_hicon))
        _avatar_hicon = 0
    _update_tray_icon_for_state()

def _file_to_hicon(path: str, size: int = 16) -> int:

    if not path or not os.path.exists(path):
        return 0
    ext = os.path.splitext(path)[1].lower()
    if ext == ".ico":
        IMAGE_ICON      = 1
        LR_LOADFROMFILE = 0x0010
        hicon = user32.LoadImageW(None, path, IMAGE_ICON, size, size, LR_LOADFROMFILE)
        if hicon:
            print(f"[tray] ICO loaded ({size}px): {os.path.basename(path)}")
            return hicon
        print(f"[tray] LoadImageW failed for ICO: {path}")
        return 0
    return _png_to_hicon(path, size)

def _clear_state_icon_cache() -> None:

    global _state_icon_cache
    for hicon in _state_icon_cache.values():
        if hicon:
            try:
                user32.DestroyIcon(ctypes.c_void_p(hicon))
            except Exception:
                pass
    _state_icon_cache = {}
    print("[tray] State icon cache cleared")

def _get_state_hicon() -> int:

    if _vc_channel_id is not None:
        if _vc_self_deaf:
            state = "deaf"
        elif _vc_self_mute:
            state = "muted"
        else:
            state = "vc"
    elif _has_unread:
        state = "unread"
    else:
        state = "normal"

    cfg  = load_config()
    path = cfg.get("tray_icons", {}).get(state, "")
    if path and os.path.isfile(path):
        cached = _state_icon_cache.get(path, 0)
        if cached:
            return cached
        hicon = _file_to_hicon(path, size=16)
        if hicon:
            _state_icon_cache[path] = hicon
            return hicon

    return _orig_hicon

def _update_tray_icon_for_state() -> None:

    hicon = _get_state_hicon()
    if not hicon:
        return
    if _nid:
        _nid.hIcon = ctypes.c_void_p(hicon)
    _set_tray_icon_handle(hicon)
_pending_avatar_png: "str | None" = None

def _set_pending_avatar(png_path: "str | None") -> None:
    global _pending_avatar_png
    _pending_avatar_png = png_path

LRESULT     = ctypes.wintypes.LPARAM
WNDPROCTYPE = ctypes.WINFUNCTYPE(
    LRESULT,
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
)

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize",        ctypes.wintypes.UINT),
        ("style",         ctypes.wintypes.UINT),
        ("lpfnWndProc",   WNDPROCTYPE),
        ("cbClsExtra",    ctypes.c_int),
        ("cbWndExtra",    ctypes.c_int),
        ("hInstance",     ctypes.wintypes.HINSTANCE),
        ("hIcon",         ctypes.wintypes.HICON),
        ("hCursor",       ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HBRUSH),
        ("lpszMenuName",  ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
        ("hIconSm",       ctypes.wintypes.HICON),
    ]

_hwnd:         ctypes.wintypes.HWND | None = None
_nid:          NOTIFYICONDATAW | None      = None
_wnd_proc_ref: WNDPROCTYPE | None         = None
_tray_ready    = threading.Event()

_tk_root: tk.Tk | None = None
_log_win = None  

def _find_discord_exe() -> str | None:
    local = os.environ.get("LOCALAPPDATA", "")
    patterns = [
        os.path.join(local, "Discord",       "app-*", "Discord.exe"),
        os.path.join(local, "DiscordPTB",    "app-*", "DiscordPTB.exe"),
        os.path.join(local, "DiscordCanary", "app-*", "DiscordCanary.exe"),
    ]
    for pattern in patterns:
        matches = sorted(glob.glob(pattern), reverse=True)
        if matches:
            return matches[0]
    return None

def _load_discord_icon() -> ctypes.wintypes.HICON:
    exe = _find_discord_exe()
    if exe:
        hicon = shell32.ExtractIconW(None, exe, 0)
        if hicon and hicon != 1:
            return hicon
    return user32.LoadIconW(None, ctypes.cast(IDI_INFORMATION, ctypes.wintypes.LPCWSTR))

TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize",              ctypes.wintypes.DWORD),
        ("cntUsage",            ctypes.wintypes.DWORD),
        ("th32ProcessID",       ctypes.wintypes.DWORD),
        ("th32DefaultHeapID",   ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID",        ctypes.wintypes.DWORD),
        ("cntThreads",          ctypes.wintypes.DWORD),
        ("th32ParentProcessID", ctypes.wintypes.DWORD),
        ("pcPriClassBase",      ctypes.c_long),
        ("dwFlags",             ctypes.wintypes.DWORD),
        ("szExeFile",           ctypes.c_wchar * 260),
    ]

DISCORD_EXE_NAMES = {"discord.exe", "discordptb.exe", "discordcanary.exe"}

def _get_discord_pids() -> set[int]:

    pids: set[int] = set()
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.wintypes.HANDLE(-1).value:
        return pids
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = kernel32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.lower() in DISCORD_EXE_NAMES:
                pids.add(entry.th32ProcessID)
            ok = kernel32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snap)
    return pids

def _find_discord_hwnd() -> ctypes.wintypes.HWND | None:

    discord_pids = _get_discord_pids()
    if not discord_pids:
        return None

    result: list = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool,
                                          ctypes.wintypes.HWND,
                                          ctypes.wintypes.LPARAM)
    pid_buf = ctypes.wintypes.DWORD(0)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        if not buf.value:
            return True
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
        if pid_buf.value in discord_pids:
            result.append(hwnd)
            return False 
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return result[0] if result else None

def _discord_has_focus() -> bool:
    fg_hwnd = user32.GetForegroundWindow()
    if not fg_hwnd:
        return False
    pid_buf = ctypes.wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(fg_hwnd, ctypes.byref(pid_buf))
    fg_pid = pid_buf.value
    client = load_config().get("client_app", "discord")
    if client == "dm":
        dm_hwnd = _find_dm_hwnd()
        return bool(dm_hwnd and fg_hwnd == dm_hwnd)
    if client == "canary":
        canary_pids: set[int] = set()
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap != ctypes.wintypes.HANDLE(-1).value:
            try:
                entry = PROCESSENTRY32W()
                entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
                ok = kernel32.Process32FirstW(snap, ctypes.byref(entry))
                while ok:
                    if entry.szExeFile.lower() == "discordcanary.exe":
                        canary_pids.add(entry.th32ProcessID)
                    ok = kernel32.Process32NextW(snap, ctypes.byref(entry))
            finally:
                kernel32.CloseHandle(snap)
        return fg_pid in canary_pids
    return fg_pid in _get_discord_pids()

def _launch_discord() -> None:
    local = os.environ.get("LOCALAPPDATA", "")
    for folder, exename in [
        ("Discord",       "Discord.exe"),
        ("DiscordPTB",    "DiscordPTB.exe"),
        ("DiscordCanary", "DiscordCanary.exe"),
    ]:
        updater = os.path.join(local, folder, "Update.exe")
        if os.path.exists(updater):
            subprocess.Popen([updater, "--processStart", exename], close_fds=True)
            return
    exe = _find_discord_exe()
    if exe:
        subprocess.Popen([exe], close_fds=True)

def _maximize_discord() -> None:
    hwnd = _find_discord_hwnd()
    if not hwnd:
        _launch_discord()
        return
    ASFW_ANY        = 0xFFFFFFFF
    VK_MENU         = 0x12
    KEYEVENTF_KEYUP = 0x0002
    SW_SHOWMAXIMIZED = 3
    user32.AllowSetForegroundWindow(ASFW_ANY)
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)

DM_CLASS_NAME = "DiscordMessengerClass"

def _find_dm_hwnd() -> ctypes.wintypes.HWND | None:

    hwnd = user32.FindWindowW(DM_CLASS_NAME, None)
    return hwnd if hwnd else None

def _find_canary_hwnd() -> ctypes.wintypes.HWND | None:

    canary_pids: set[int] = set()
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.wintypes.HANDLE(-1).value:
        return None
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = kernel32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.lower() == "discordcanary.exe":
                canary_pids.add(entry.th32ProcessID)
            ok = kernel32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snap)

    if not canary_pids:
        return None

    result: list = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool,
                                          ctypes.wintypes.HWND,
                                          ctypes.wintypes.LPARAM)
    pid_buf = ctypes.wintypes.DWORD(0)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        if not buf.value:
            return True
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
        if pid_buf.value in canary_pids:
            result.append(hwnd)
            return False
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return result[0] if result else None

def _launch_discord_canary() -> None:
    local = os.environ.get("LOCALAPPDATA", "")
    updater = os.path.join(local, "DiscordCanary", "Update.exe")
    if os.path.exists(updater):
        subprocess.Popen([updater, "--processStart", "DiscordCanary.exe"],
                         close_fds=True)
        return
    exe = os.path.join(local, "DiscordCanary", "DiscordCanary.exe")
    if os.path.exists(exe):
        subprocess.Popen([exe], close_fds=True)

def _maximize_discord_canary() -> None:
    hwnd = _find_canary_hwnd()
    if not hwnd:
        _launch_discord_canary()
        return
    ASFW_ANY        = 0xFFFFFFFF
    VK_MENU         = 0x12
    KEYEVENTF_KEYUP = 0x0002
    user32.AllowSetForegroundWindow(ASFW_ANY)
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)

def _launch_discord_messenger() -> None:
    exe = load_config().get("dm_exe_path", "")
    if exe and os.path.isfile(exe):
        try:
            subprocess.Popen([exe], close_fds=True)
            print(f"[dm] Launched {exe!r}")
        except Exception as e:
            print(f"[dm] Failed to launch {exe!r}: {e}")
    else:
        print("[dm] DiscordMessenger.exe path not configured or not found.")

def _maximize_discord_messenger() -> None:
    hwnd = _find_dm_hwnd()
    if not hwnd:
        _launch_discord_messenger()
        return
    ASFW_ANY        = 0xFFFFFFFF
    VK_MENU         = 0x12
    KEYEVENTF_KEYUP = 0x0002
    user32.AllowSetForegroundWindow(ASFW_ANY)
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOW)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)

def _open_client(channel_url: "str | None" = None) -> None:

    client = load_config().get("client_app", "discord")
    if client == "dm":
        _maximize_discord_messenger()
    elif client == "canary":
        if channel_url:
            try:
                os.startfile(channel_url)
                return
            except Exception as e:
                print(f"[balloon] Failed to open deep link {channel_url!r}: {e}")
        _maximize_discord_canary()
    else:
        if channel_url:
            try:
                os.startfile(channel_url)
                return
            except Exception as e:
                print(f"[balloon] Failed to open deep link {channel_url!r}: {e}")
        _maximize_discord()

import dataclasses

@dataclasses.dataclass
class _QueuedNotif:
    title:     str
    body:      str
    url:       "str | None"
    ts:        float = dataclasses.field(default_factory=time.time)
    read:      bool  = False
    sound_key: str   = "NewMessage"

_notif_queue:      list[_QueuedNotif] = []
_notif_queue_lock: threading.Lock     = threading.Lock()

_last_balloon_time: float = 0.0
_replace_pending:   "_QueuedNotif | None" = None
_replace_timer:     "threading.Timer | None" = None

_queue_sound_cooldown: float = 4.0 
_queue_last_sound_time: float = 0.0

def _raw_show_balloon(title: str, body: str, url: "str | None",
                      suppress_sound: bool = False,
                      sound_key: str = "NewMessage") -> None:

    global _last_balloon_url, _avatar_hicon, _pending_avatar_png
    if not (_nid and _hwnd):
        return
    _last_balloon_url = url

    use_avatar = load_config().get("show_avatar_icon", True)
    avatar_png = _pending_avatar_png
    _pending_avatar_png = None 

    new_hicon = 0
    if use_avatar and avatar_png:
        new_hicon = _png_to_hicon(avatar_png, size=32)

    if new_hicon:
        if _avatar_hicon:
            user32.DestroyIcon(ctypes.c_void_p(_avatar_hicon))
        _avatar_hicon = new_hicon
        _nid.hIcon = ctypes.c_void_p(new_hicon)
        balloon_flags_base = NIIF_USER  
    else:
        balloon_flags_base = NIIF_INFO

    _nid.uFlags          = NIF_INFO | NIF_ICON | NIF_MESSAGE | NIF_TIP
    _nid.szInfoTitle     = title[:63]
    _nid.szInfo          = body[:255]
    cfg2 = load_config()
    is_queue            = cfg2.get("notif_style", "instant") == "queue"
    balloon_sound_mode  = cfg2.get("balloon_sound_mode", False) and not suppress_sound
    use_balloon_sound   = is_queue or balloon_sound_mode
                                                                            
                                                                             
    if balloon_sound_mode and not is_queue:
        wav_path = _get_sound_path(sound_key)
        _set_balloon_sound_registry(wav_path)
    _nid.dwInfoFlags = balloon_flags_base if use_balloon_sound else (balloon_flags_base | NIIF_NOSOUND)
    _nid.uTimeout        = 7000
    global _balloon_refcount
    _balloon_refcount += 1
    shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(_nid))

def _style_instant(title: str, body: str, url: "str | None",
                   sound_key: str = "NewMessage") -> None:
    _raw_show_balloon(title, body, url, sound_key=sound_key)

def _style_replace(title: str, body: str, url: "str | None",
                   sound_key: str = "NewMessage") -> None:
    global _last_balloon_time, _replace_pending, _replace_timer
    cfg     = load_config()
    cooldown = float(cfg.get("replace_cooldown", 4.0))
    now      = time.time()
    elapsed  = now - _last_balloon_time

    if _replace_timer:
        _replace_timer.cancel()
        _replace_timer = None

    if elapsed >= cooldown:
        _last_balloon_time = now
        _raw_show_balloon(title, body, url, sound_key=sound_key)
    else:
        _replace_pending = _QueuedNotif(title, body, url, sound_key=sound_key)
        delay = cooldown - elapsed

        def _fire():
            global _last_balloon_time, _replace_pending, _replace_timer
            _replace_timer = None
            pend = _replace_pending
            _replace_pending = None
            if pend:
                _last_balloon_time = time.time()
                _raw_show_balloon(pend.title, pend.body, pend.url,
                                  sound_key=pend.sound_key)

        _replace_timer = threading.Timer(delay, _fire)
        _replace_timer.daemon = True
        _replace_timer.start()

def _set_balloon_sound_registry(wav_path: "str | None") -> None:
    try:
        key_path = r"AppEvents\Schemes\Apps\.Default\SystemNotification\.Current"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                            0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, wav_path or "")
    except Exception as e:
        print(f"[sound] Failed to set balloon sound registry: {e}")

def _style_queue_add(title: str, body: str, url: "str | None",
                     sound_key: str = "NewMessage") -> None:
    global _queue_last_sound_time

    with _notif_queue_lock:
        _notif_queue.append(_QueuedNotif(title, body, url))
        snapshot = list(_notif_queue)

    count = len(snapshot)

    if count == 1:
        n = snapshot[0]
        balloon_title = n.title + ":"
        balloon_body  = n.body
    else:
        balloon_title = f"{count} new notifications"
        lines = []
        for n in snapshot[:5]:
            line = f"{n.title}: {n.body}"
            line = line.replace("\n", " ").replace("\r", " ")
            lines.append(line)
        balloon_body = "\r\n".join(lines)

    now     = time.time()
    elapsed = now - _queue_last_sound_time
    if elapsed >= _queue_sound_cooldown:
        wav_path = _get_sound_path(sound_key)
        _set_balloon_sound_registry(wav_path)
        _queue_last_sound_time = now
        print(f"[queue] Sound armed (elapsed={elapsed:.2f}s, wav={wav_path})")
    else:
        _set_balloon_sound_registry("")
        print(f"[queue] Sound suppressed (elapsed={elapsed:.2f}s < cooldown={_queue_sound_cooldown}s)")

    _raw_show_balloon(balloon_title, balloon_body, None)

def show_balloon(title: str, body: str, url: "str | None" = None,
                 is_system: bool = False, sound_key: str = "NewMessage",
                 channel_id: "str | None" = None) -> bool:
    global _has_unread
    if is_system:
        _raw_show_balloon(title, body, url, suppress_sound=True)
        return False

    if _should_suppress_channel(channel_id):
        print(f"[notif] Suppressed (viewing channel {channel_id}) — marking unread silently")
        _unread_channels.discard(channel_id)
        if not _unread_channels:
            _has_unread = False
        _update_tray_icon_for_state()
        return True

    if channel_id and _discord_has_focus():
        print(f"[notif] Discord has focus (different channel) — showing balloon for {channel_id}")

    _has_unread = True
    if channel_id:
        _unread_channels.add(channel_id)
    _update_tray_icon_for_state()
    style = load_config().get("notif_style", "instant")
    if style == "replace":
        _style_replace(title, body, url, sound_key=sound_key)
    elif style == "queue":
        _style_queue_add(title, body, url, sound_key=sound_key)
    else:
        _style_instant(title, body, url, sound_key=sound_key)
    return False

def _open_balloon_url() -> None:
    global _pending_update_info
                                                                                  
    if _pending_update_info is not None:
        info = _pending_update_info
        _pending_update_info = None
        _launch_updater_download(info.get("version", ""), info.get("download_url", ""))
        return
    style = load_config().get("notif_style", "instant")
    if style == "queue":
        global _has_unread
        _has_unread = False
        _unread_channels.clear()
        _update_tray_icon_for_state()
        with _notif_queue_lock:
            _notif_queue.clear()
        print("[queue] Balloon clicked — notifications cleared")
        return
    _open_client(_last_balloon_url)

def _send_gateway_message(data: dict) -> None:
    if _gw_ws is None or _gw_loop is None or _gw_loop.is_closed():
        return
    try:
        asyncio.run_coroutine_threadsafe(_gw_ws.send(json.dumps(data)), _gw_loop)
    except Exception as e:
        print(f"[gateway] Send error: {e}")

def _gateway_set_status(status: str) -> None:
    global _my_status
    _my_status = status
    _send_gateway_message({
        "op": 3,
        "d": {"since": None, "activities": [], "status": status, "afk": False},
    })
    if _gw_loop and not _gw_loop.is_closed() and _token:
        asyncio.run_coroutine_threadsafe(
            _async_set_status_proto(_token, status), _gw_loop
        )
    print(f"[app] Status set to {status}")

def _was_mentioned(d: dict, my_user_id: str) -> bool:

    if any(u.get("id") == my_user_id for u in d.get("mentions", [])):
        return True

    if d.get("mention_everyone", False):
        return True

    ref = d.get("referenced_message") or {}
    if ref.get("author", {}).get("id") == my_user_id:
        return True

    return False

def _leave_voice_channel() -> None:
    if not _vc_channel_id:
        print("[vc] Not in a voice channel, nothing to leave")
        return

    _send_gateway_message({
        "op": 4,
        "d": {
            "guild_id":   _vc_guild_id,
            "channel_id": _vc_channel_id,
            "self_mute":  True,
            "self_deaf":  False,
        },
    })
    print("[vc] Sent op 4 leave signal (conflict disconnect)")

    _send_gateway_message({
        "op": 4,
        "d": {
            "guild_id":   _vc_guild_id,
            "channel_id": None,
            "self_mute":  False,
            "self_deaf":  False,
        },
    })
    print("[vc] Sent op 4 channel_id=None (leave voice)")

def _kill_client_process() -> None:
    cfg = load_config()
    if cfg.get("client_app") == "dm":
        exe_path = cfg.get("dm_exe_path", "")
        target   = os.path.basename(exe_path).lower() if exe_path else "discordmessenger.exe"
    else:
        target = None 

    TH32CS_SNAPPROCESS = 0x00000002
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.wintypes.HANDLE(-1).value:
        return
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = kernel32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            name_lo = entry.szExeFile.lower()
            if target:
                match = (name_lo == target)
            else:
                match = name_lo in DISCORD_EXE_NAMES
            if match:
                h = kernel32.OpenProcess(1, False, entry.th32ProcessID)
                if h:
                    kernel32.TerminateProcess(h, 0)
                    kernel32.CloseHandle(h)
                    print(f"[exit] Terminated {entry.szExeFile} (pid={entry.th32ProcessID})")
            ok = kernel32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snap)

def _load_question_photoimage(size: int = 32) -> "tk.PhotoImage | None":
    try:
        gdi32 = ctypes.windll.gdi32

        IMAGE_ICON   = 1
        LR_SHARED    = 0x8000
        LR_DEFAULTSIZE = 0x0040

        hicon = user32.LoadImageW(
            None,
            ctypes.cast(IDI_QUESTION, ctypes.wintypes.LPCWSTR),
            IMAGE_ICON, size, size,
            LR_SHARED,
        )
        if not hicon:
            return None

        hdc_screen = user32.GetDC(None)
        hdc_mem    = gdi32.CreateCompatibleDC(hdc_screen)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize",          ctypes.c_int32),
                ("biWidth",         ctypes.c_int32),
                ("biHeight",        ctypes.c_int32),
                ("biPlanes",        ctypes.c_int16),
                ("biBitCount",      ctypes.c_int16),
                ("biCompression",   ctypes.c_uint32),
                ("biSizeImage",     ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed",       ctypes.c_uint32),
                ("biClrImportant",  ctypes.c_uint32),
            ]

        bih = BITMAPINFOHEADER()
        bih.biSize        = ctypes.sizeof(BITMAPINFOHEADER)
        bih.biWidth       = size
        bih.biHeight      = -size 
        bih.biPlanes      = 1
        bih.biBitCount    = 32
        bih.biCompression = 0 

        class BITMAPINFO(ctypes.Structure):
            _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                        ("bmiColors", ctypes.c_uint32 * 3)]

        bmi = BITMAPINFO()
        bmi.bmiHeader = bih

        bits_ptr = ctypes.c_void_p(0)
        hbmp = gdi32.CreateDIBSection(
            hdc_screen, ctypes.byref(bmi), 0,
            ctypes.byref(bits_ptr), None, 0,
        )
        if not hbmp:
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(None, hdc_screen)
            return None

        old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

        SRCCOPY = 0x00CC0020
        r, g, b = 212, 208, 200
        hbr = gdi32.CreateSolidBrush(r | (g << 8) | (b << 16))
        rc  = ctypes.wintypes.RECT(0, 0, size, size)
        user32.FillRect(hdc_mem, ctypes.byref(rc), hbr)
        gdi32.DeleteObject(hbr)
        DI_NORMAL = 3
        user32.DrawIconEx(hdc_mem, 0, 0, hicon, size, size, 0, None, DI_NORMAL)
        buf = (ctypes.c_uint8 * (size * size * 4))()
        gdi32.GetBitmapBits(hbmp, size * size * 4, buf)

        gdi32.SelectObject(hdc_mem, old_bmp)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)

        import struct as _struct
        header = f"P6\n{size} {size}\n255\n".encode()
        rows   = bytearray(size * size * 3)
        for i in range(size * size):
            b_, g_, r_ = buf[i*4], buf[i*4+1], buf[i*4+2]
            rows[i*3], rows[i*3+1], rows[i*3+2] = r_, g_, b_

        import io as _io
        import base64 as _b64
        ppm = header + bytes(rows)

        img = tk.PhotoImage(data=_b64.b64encode(ppm))
        return img

    except Exception as e:
        print(f"[icon] _load_question_photoimage failed: {e}")
        return None

def _confirm_exit(hwnd) -> None:
    cfg       = load_config()
    close_pref = cfg.get("exit_close_client", None)

    if close_pref is not None:
        if close_pref:
            _kill_client_process()
        user32.DestroyWindow(hwnd)
        threading.Timer(0.5, os._exit, args=(0,)).start()
        return

    user32.MessageBeep(MB_ICONQUESTION)

    dlg = tk.Toplevel(_tk_root)
    dlg.title(_t("exit_dlg_title"))
    dlg.resizable(False, False)
    dlg.configure(bg=XP_FACE)
    dlg.grab_set()
    _set_discord_icon_on_window(dlg)

    top = tk.Frame(dlg, bg=XP_FACE)
    top.pack(fill=tk.X, padx=12, pady=(14, 6))

    _ico_img = _load_question_photoimage(32)
    if _ico_img:
        ico_lbl = tk.Label(top, image=_ico_img, bg=XP_FACE)
        ico_lbl.image = _ico_img
        ico_lbl.pack(side=tk.LEFT, padx=(0, 12), anchor=tk.N)

    tk.Label(top, text=_t("exit_dlg_msg"),
             bg=XP_FACE, fg=XP_TEXT, font=XP_FONT,
             justify=tk.LEFT).pack(side=tk.LEFT, anchor=tk.W)

    chk_frame = tk.Frame(dlg, bg=XP_FACE)
    chk_frame.pack(fill=tk.X, padx=18, pady=(0, 8))

    also_var     = tk.BooleanVar(value=False)
    remember_var = tk.BooleanVar(value=False)

    xp_checkbox(chk_frame, _t("exit_chk_also_close"), also_var).pack(anchor=tk.W, pady=2)
    xp_checkbox(chk_frame, _t("exit_chk_remember"),   remember_var).pack(anchor=tk.W, pady=(2, 0))

    sep = tk.Frame(dlg, bg=XP_BORDER, height=1)
    sep.pack(fill=tk.X, padx=8)

    btn_row = tk.Frame(dlg, bg=XP_FACE)
    btn_row.pack(fill=tk.X, padx=8, pady=8)

    def _do_exit():
        close_client = also_var.get()
        if remember_var.get():
            c = load_config()
            c["exit_close_client"] = close_client
            save_config(c)
        dlg.destroy()
        if close_client:
            _kill_client_process()
        user32.DestroyWindow(hwnd)
        threading.Timer(0.5, os._exit, args=(0,)).start()

    def _cancel():
        dlg.destroy()

    xp_button(btn_row, _t("exit_btn_exit"),   _do_exit, width=10).pack(side=tk.RIGHT, padx=(4, 2))
    xp_button(btn_row, _t("btn_cancel"),      _cancel,  width=10).pack(side=tk.RIGHT, padx=2)

    dlg.update_idletasks()
    w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
    sw   = dlg.winfo_screenwidth()
    sh   = dlg.winfo_screenheight()
    dlg.geometry(f"{max(w,340)}x{max(h,160)}+{(sw-max(w,340))//2}+{(sh-max(h,160))//2}")

def _show_context_menu(hwnd) -> None:
    try:
        TPM_RETURNCMD   = 0x0100
        TPM_BOTTOMALIGN = 0x0020
        TPM_RIGHTALIGN  = 0x0008
        TPM_NONOTIFY    = 0x0080

        hmenu = user32.CreatePopupMenu()
        if not hmenu:
            print("[menu] CreatePopupMenu failed")
            return

        if _vc_channel_id is not None:
            user32.AppendMenuW(hmenu, MF_STRING | MF_GRAYED, 0, _t("menu_voice_header"))
            user32.AppendMenuW(hmenu, MF_STRING, ctypes.c_size_t(IDM_VC_LEAVE), _t("menu_leave_call"))
            user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)

        status_menu = user32.CreatePopupMenu()
        if not status_menu:
            print("[menu] CreatePopupMenu (status) failed")
            user32.DestroyMenu(hmenu)
            return

        for idm, key, tkey in [
            (IDM_STATUS_ONLINE,    "online",    "menu_status_online"),
            (IDM_STATUS_IDLE,      "idle",      "menu_status_idle"),
            (IDM_STATUS_DND,       "dnd",       "menu_status_dnd"),
            (IDM_STATUS_INVISIBLE, "invisible", "menu_status_invis"),
        ]:
            flag = MF_STRING | (MF_CHECKED if _my_status == key else 0)
            user32.AppendMenuW(status_menu, flag, ctypes.c_size_t(idm), _t(tkey))

        user32.AppendMenuW(hmenu, MF_POPUP, ctypes.c_size_t(status_menu), _t("menu_status"))
        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)

        log_lbl   = _t("menu_hide_log") if (_log_win and _log_win.visible) else _t("menu_show_log")
        auto_flag = MF_STRING | (MF_CHECKED if load_config().get("auto_login") else 0)

        open_lbl = _t("menu_open_dm") if load_config().get("client_app") == "dm" else _t("menu_open_discord")
        user32.AppendMenuW(hmenu, MF_STRING, ctypes.c_size_t(IDM_OPEN),     open_lbl)
        user32.AppendMenuW(hmenu, MF_STRING,    ctypes.c_size_t(IDM_LOG),       log_lbl)
        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(hmenu, auto_flag,    ctypes.c_size_t(IDM_AUTOLOGIN), _t("menu_autologin"))
        user32.AppendMenuW(hmenu, MF_STRING,    ctypes.c_size_t(IDM_SETTINGS),  _t("menu_settings"))
        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(hmenu, MF_STRING,    ctypes.c_size_t(IDM_EXIT),      _t("menu_exit"))

        user32.SetForegroundWindow(hwnd)
        pt = ctypes.wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))

        cmd = user32.TrackPopupMenu(
            hmenu,
            TPM_RETURNCMD | TPM_BOTTOMALIGN | TPM_RIGHTALIGN | TPM_NONOTIFY,
            pt.x, pt.y, 0, hwnd, None,
        )
        user32.DestroyMenu(hmenu)

        if   cmd == IDM_OPEN:             _open_client()
        elif cmd == IDM_LOG:
            if _tk_root and _log_win:     _tk_root.after(0, _log_win.toggle)
        elif cmd == IDM_AUTOLOGIN:
            cfg = load_config()
            cfg["auto_login"] = not cfg.get("auto_login", False)
            save_config(cfg)
        elif cmd == IDM_STATUS_ONLINE:    _gateway_set_status("online")
        elif cmd == IDM_STATUS_IDLE:      _gateway_set_status("idle")
        elif cmd == IDM_STATUS_DND:       _gateway_set_status("dnd")
        elif cmd == IDM_STATUS_INVISIBLE: _gateway_set_status("invisible")
        elif cmd == IDM_VC_LEAVE:         _leave_voice_channel()
        elif cmd == IDM_SETTINGS:
            if _tk_root:              _tk_root.after(0, _open_settings_window)
        elif cmd == IDM_EXIT:
            if _tk_root: _tk_root.after(0, lambda h=hwnd: _confirm_exit(h))

    except Exception as e:
        print(f"[menu] Error: {e}")

def _wnd_proc(hwnd, msg, wparam, lparam):
    global _balloon_visible, _balloon_pending_sound, _balloon_pending_key
    try:
        if msg == WM_TRAYICON:
            event = lparam & 0xFFFF

            if event == NIN_BALLOONSHOW:
                _balloon_visible = True

            elif event == NIN_BALLOONUSERCLICK:
                _balloon_visible       = False
                _balloon_pending_sound = False
                _restore_tray_icon() 
                _open_balloon_url()

            elif event == NIN_BALLOONHIDE:
                if load_config().get("notif_style", "instant") != "queue":
                    _balloon_visible = False
                _restore_tray_icon()

            elif event == NIN_BALLOONTIMEOUT:
                _balloon_visible = False
                _restore_tray_icon() 
                if _balloon_pending_sound:
                    key = _balloon_pending_key
                    _balloon_pending_sound = False
                    _play_notification_sound(key)

            elif event == WM_LBUTTONDBLCLK:
                _open_client()
            elif event in (WM_RBUTTONUP, WM_CONTEXTMENU):
                _show_context_menu(hwnd)
            return 0

        if msg == WM_DESTROY:
            if _nid:
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(_nid))
            user32.PostQuitMessage(0)
            if _tk_root:
                _tk_root.after(0, _tk_root.quit)
            return 0

    except Exception as e:
        print(f"[wndproc] Error: {e}")

    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

def _create_tray_icon() -> None:
    global _hwnd, _nid, _wnd_proc_ref

    _wnd_proc_ref = WNDPROCTYPE(_wnd_proc)
    hinstance     = kernel32.GetModuleHandleW(None)
    class_name    = "DiscordBalloonNotifier"

    wc = WNDCLASSEXW()
    wc.cbSize        = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc   = _wnd_proc_ref
    wc.hInstance     = hinstance
    wc.lpszClassName = class_name
    user32.RegisterClassExW(ctypes.byref(wc))

    _hwnd = user32.CreateWindowExW(
        0, class_name, "Discord Balloon Notifier",
        0, 0, 0, 0, 0, 0, 0, hinstance, None,
    )

    hicon = _load_discord_icon()

    global _orig_hicon
    _orig_hicon = hicon 

    _nid = NOTIFYICONDATAW()
    _nid.cbSize           = ctypes.sizeof(NOTIFYICONDATAW)
    _nid.hWnd             = _hwnd
    _nid.uID              = 1
    _nid.uFlags           = NIF_ICON | NIF_MESSAGE | NIF_TIP
    _nid.uCallbackMessage = WM_TRAYICON
    _nid.hIcon            = hicon
    _nid.szTip            = "Discord Balloon Notifier"
    shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(_nid))
                                                                         
    _update_tray_icon_for_state()

def _message_loop() -> None:
    _create_tray_icon()
    _tray_ready.set()
    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

def _parse_iso(ts: str) -> float:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0

def _parse_muted(guild_settings: list) -> tuple[set[str], set[str]]:
    now             = time.time()
    muted_guilds:   set[str] = set()
    muted_channels: set[str] = set()

    for entry in guild_settings:
        if entry.get("muted"):
            end_time = (entry.get("mute_config") or {}).get("end_time")
            if end_time is None or _parse_iso(end_time) > now:
                guild_id = entry.get("guild_id")
                if guild_id:
                    muted_guilds.add(guild_id)

        for ch in entry.get("channel_overrides", []):
            if ch.get("muted"):
                ch_end = (ch.get("mute_config") or {}).get("end_time")
                if ch_end is None or _parse_iso(ch_end) > now:
                    ch_id = ch.get("channel_id")
                    if ch_id:
                        muted_channels.add(ch_id)

    return muted_guilds, muted_channels

async def _get_channel_info(http, token: str,
                             guild_id: str | None,
                             channel_id: str | None) -> tuple[str, str]:
    channel_name = guild_name = ""
    try:
        if channel_id:
            async with http.get(f"{DISCORD_API}/channels/{channel_id}",
                                headers={"Authorization": token}) as r:
                if r.status == 200:
                    channel_name = (await r.json()).get("name", "")
        if guild_id:
            async with http.get(f"{DISCORD_API}/guilds/{guild_id}",
                                headers={"Authorization": token}) as r:
                if r.status == 200:
                    guild_name = (await r.json()).get("name", "")
    except Exception:
        pass
    return channel_name, guild_name

async def _get_nick(http, token: str, guild_id: str | None, author: dict) -> str:
    user_id = author.get("id", "")
    name    = author.get("global_name") or author.get("username", "?")
    if not guild_id:
        return name
    try:
        async with http.get(f"{DISCORD_API}/guilds/{guild_id}/members/{user_id}",
                            headers={"Authorization": token}) as r:
            if r.status == 200:
                data = await r.json()
                return data.get("nick") or name
    except Exception:
        pass
    return name

async def _fetch_user_status(http, token: str) -> str:
    try:
        async with http.get(f"{DISCORD_API}/users/@me/settings",
                            headers={"Authorization": token}) as r:
            if r.status == 200:
                return (await r.json()).get("status", "online")
    except Exception:
        pass
    return "online"

def _resolve_mentions(content: str, d: dict) -> str:
    user_map: dict[str, str] = {}
    for u in d.get("mentions", []):
        uid = u.get("id")
        if uid:
            user_map[uid] = u.get("global_name") or u.get("username", uid)

    def replace_user(m: re.Match) -> str:
        return "@" + user_map.get(m.group(1), m.group(1))
    content = re.sub(r"<@!?(\d+)>", replace_user, content)

    content = re.sub(r"<#(\d+)>", lambda m: f"#channel", content)

    content = re.sub(r"<@&\d+>", "@role", content)

    content = re.sub(r"<a?:(\w+):\d+>", lambda m: f":{m.group(1)}:", content)

    def _mask_spoiler(m: re.Match) -> str:
        inner = m.group(1)
        blocks = min(len(inner), 30)
        return "\u2588" * blocks
    content = re.sub(r"\|\|(.+?)\|\|", _mask_spoiler, content, flags=re.DOTALL)

    return content

async def _async_set_status_proto(token: str, new_status: str) -> None:

    import base64 as _b64
    import aiohttp

    try:
        async with aiohttp.ClientSession() as http:
            async with http.get(
                f"{DISCORD_API}/users/@me/settings-proto/1",
                headers={"Authorization": token},
            ) as r:
                if r.status != 200:
                    print(f"[app] GET proto falló: {r.status}")
                    return
                proto_b64  = (await r.json()).get("settings", "")
                proto_bytes = _b64.b64decode(proto_b64) if proto_b64 else b""

            new_field11 = _build_status_field(new_status)
            new_proto   = _replace_or_add_field11(proto_bytes, new_field11)

            async with http.patch(
                f"{DISCORD_API}/users/@me/settings-proto/1",
                headers={"Authorization": token, "Content-Type": "application/json"},
                json={"settings": _b64.b64encode(new_proto).decode()},
            ) as r:
                if r.status == 200:
                    print(f"[app] Estado proto actualizado a '{new_status}'")
                else:
                    print(f"[app] Proto PATCH falló: {r.status} {await r.text()}")
    except Exception as e:
        print(f"[app] Error en proto PATCH: {e}")

async def run_gateway(token: str) -> None:
    global _gw_ws, _gw_loop, _my_status, _token, _has_unread
    _token = token

    try:
        import websockets
        import aiohttp
    except ImportError:
        print("Install dependencies:\n  pip install websockets aiohttp")
        sys.exit(1)

    session_id:     str | None = None
    resume_url:     str | None = None
    sequence:       int | None = None
    muted_guilds:   set[str] = set()
    muted_channels: set[str] = set()

    while True:
        zlib_ctx        = zlib.decompressobj()
        buffer          = bytearray()
        my_user_id:     str | None = None
        heartbeat_task: asyncio.Task | None = None
        channel_cache:  dict[str, tuple[str, str]] = {}
        nick_cache:     dict[tuple, str] = {}

        ack_times:      dict[str, float] = {}

        try:
            async with aiohttp.ClientSession() as http:
                connect_url = (
                    (resume_url + "?v=9&encoding=json&compress=zlib-stream")
                    if (session_id and resume_url) else GATEWAY_URL
                )
                async with websockets.connect(connect_url, max_size=None) as ws:
                    _gw_ws   = ws
                    _gw_loop = asyncio.get_event_loop()
                    print("[gateway] Connected.")

                    raw_hello = await ws.recv()
                    if isinstance(raw_hello, bytes):
                        raw_hello = zlib_ctx.decompress(raw_hello).decode()
                    hello = json.loads(raw_hello)
                    heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000

                    if session_id and sequence is not None:
                        await ws.send(json.dumps({
                            "op": 6,
                            "d": {"token": token, "session_id": session_id, "seq": sequence},
                        }))
                        print("[gateway] Attempting session resume...")
                    else:
                        await ws.send(json.dumps({
                            "op": 2,
                            "d": {
                                "token": token,
                                "capabilities": 16381,
                                "compress": False,
                                "properties": {
                                    "os": "Windows",
                                    "browser": "Discord",
                                    "device": "",
                                    "system_locale": "en-US",
                                    "browser_user_agent": (

                                    ),
                                    "browser_version": "120.0.0.0",
                                    "os_version": "10",
                                    "release_channel": "stable",
                                    "client_build_number": 0,
                                    "client_event_source": None,
                                },
                                "presence": {
                                    "status": "online",
                                    "since": 0,
                                    "activities": [],
                                    "afk": False,
                                },
                                "client_state": {
                                    "guild_versions": {},
                                },
                            },
                        }))

                    async def heartbeat():
                        nonlocal sequence
                        while True:
                            await asyncio.sleep(heartbeat_interval)
                            await ws.send(json.dumps({"op": 1, "d": sequence}))

                    heartbeat_task = asyncio.create_task(heartbeat())

                    async for raw in ws:
                        if isinstance(raw, bytes):
                            buffer.extend(raw)
                            if len(raw) < 4 or raw[-4:] != b'\x00\x00\xff\xff':
                                continue
                            try:
                                raw = zlib_ctx.decompress(buffer).decode()
                                buffer.clear()
                            except Exception:
                                buffer.clear()
                                continue

                        event = json.loads(raw)
                        if event.get("s"):
                            sequence = event["s"]

                        op = event.get("op")
                        t  = event.get("t")
                        d  = event.get("d") or {}

                        if op == 7:
                            print("[gateway] Reconnect requested.")
                            break

                        if op == 9:
                            can_resume = bool(d) if isinstance(d, bool) else False
                            if not can_resume:
                                session_id = None
                                sequence   = None
                                print("[gateway] Session invalidated, will re-identify.")
                            else:
                                print("[gateway] Session invalid but Discord says retry.")
                            await asyncio.sleep(1)
                            break

                        if t == "READY":
                            user       = d.get("user", {})
                            my_user_id = user.get("id")
                            name       = user.get("username", "?")

                            session_id = d.get("session_id")
                            resume_url = (d.get("resume_gateway_url") or "").rstrip("/")

                            ugs     = d.get("user_guild_settings", {})
                            entries = ugs if isinstance(ugs, list) else ugs.get("entries", [])
                            muted_guilds, muted_channels = _parse_muted(entries)

                            _my_status = await _fetch_user_status(http, token)

                                                                                 
                                                                                   
                                                                                     
                                                                                 
                                                                                
                                                                                        
                            _unread_channels.clear()
                            _has_unread = False
                            try:
                                                                                                   
                                read_state_entries = d.get("read_state", {})
                                if isinstance(read_state_entries, dict):
                                    read_state_entries = read_state_entries.get("entries", [])
                                last_read: dict[str, str] = {}
                                for rs in (read_state_entries or []):
                                    ch_id = rs.get("channel_id") or rs.get("id")
                                    lm    = rs.get("last_message_id") or rs.get("last_read_message_id") or "0"
                                    if ch_id:
                                        last_read[ch_id] = str(lm)

                                async with http.get(

                                    f"?limit=25&roles=true&everyone=true",
                                    headers={"Authorization": token},
                                ) as r:
                                    if r.status == 200:
                                        mentions = await r.json()
                                        for msg in mentions:
                                            ch_id  = msg.get("channel_id")
                                            msg_id = str(msg.get("id", "0"))
                                            if not ch_id or ch_id in muted_channels:
                                                continue
                                                                                                       
                                            already_read_up_to = last_read.get(ch_id, "0")
                                            if msg_id > already_read_up_to:
                                                _unread_channels.add(ch_id)
                                        if _unread_channels:
                                            _has_unread = True
                                            print(f"[gateway] Seeded {len(_unread_channels)} "
                                                  f"unread channel(s) from /mentions")
                                        else:
                                            print("[gateway] No unread mentions at connect")
                                    else:
                                        print(f"[gateway] /mentions returned {r.status}")
                            except Exception as _e:
                                print(f"[gateway] Could not seed unread state: {_e}")
                            _update_tray_icon_for_state()
                                                                                

                            print(f"[gateway] Logged in as: {name} (id={my_user_id})")
                            print(f"[gateway] Status: {_my_status} | "

                                  f"Muted channels: {len(muted_channels)}")
                            show_balloon(_t("balloon_connected"), _t("balloon_signed_in", name=name), is_system=True)
                            if load_config().get("auto_open_client", False):
                                _tk_root.after(1500, _open_client)
                            continue

                        if t == "RESUMED":
                            print("[gateway] Session resumed successfully.")
                            continue

                        if t == "READY_SUPPLEMENTAL":
                                                                                         
                                                                                 
                            continue

                        if t == "PRESENCE_UPDATE":
                            if d.get("user", {}).get("id") == my_user_id:
                                new_stat = d.get("status")
                                if new_stat:
                                    _my_status = new_stat
                                    print(f"[gateway] Own presence updated: {_my_status}")
                            continue

                        if t == "USER_SETTINGS_PROTO_UPDATE":
                            new_stat = await _fetch_user_status(http, token)
                            _my_status = new_stat
                            print(f"[gateway] Settings updated, status now: {_my_status}")
                            continue

                        if t == "RELATIONSHIP_ADD":
                            if d.get("type") == 3:
                                u    = d.get("user", {})
                                who  = u.get("global_name") or u.get("username", "Someone")
                                print(f"[msg] Friend request from {who}")
                                show_balloon(_t("balloon_friend_req"), _t("balloon_friend_body", who=who),
                                             is_system=True)
                            continue

                        if t == "RELATIONSHIP_REMOVE":
                            continue

                        if t == "VOICE_STATE_UPDATE":
                            global _vc_guild_id, _vc_channel_id, _vc_self_mute, _vc_self_deaf, _active_call_channel_id, _outgoing_call_channel_id, _outgoing_call_time

                            other_uid = d.get("user_id")
                            other_ch  = d.get("channel_id")
                            if (other_uid and other_uid != my_user_id
                                    and other_ch == _active_call_channel_id
                                    and not _outgoing_call_stop.is_set()):
                                print(f"[call] Call answered by {other_uid}")

                            if d.get("user_id") == my_user_id:
                                prev_channel = _vc_channel_id
                                prev_mute    = _vc_self_mute
                                prev_deaf    = _vc_self_deaf

                                _vc_guild_id   = d.get("guild_id")
                                _vc_channel_id = d.get("channel_id") 
                                _vc_self_mute  = bool(d.get("self_mute", False))
                                _vc_self_deaf  = bool(d.get("self_deaf", False))

                                if _vc_channel_id and not prev_channel:

                                    print(f"[vc] Joined channel {_vc_channel_id}")
                                    _stop_incoming_call_sound()
                                    _play_notification_sound("JoinCall")
                                    _vc_member_ids.clear()
                                    _vc_join_time = time.time()
                                elif not _vc_channel_id and prev_channel:

                                    print("[vc] Left voice channel")
                                    _play_notification_sound("LeaveCall")
                                    _vc_member_ids.clear()
                                else:

                                    if _vc_self_deaf and not prev_deaf:
                                        print("[vc] Deafened")
                                        _play_notification_sound("Deafen")
                                    elif not _vc_self_deaf and prev_deaf:
                                        print("[vc] Undeafened")
                                        _play_notification_sound("Undeafen")
                                    elif _vc_self_mute and not prev_mute:
                                        print("[vc] Muted")
                                        _play_notification_sound("Mute")
                                    elif not _vc_self_mute and prev_mute:
                                        print("[vc] Unmuted")
                                        _play_notification_sound("Unmute")

                                    if _vc_channel_id:
                                        mute_str = " (muted)"    if _vc_self_mute else ""
                                        deaf_str = " (deafened)" if _vc_self_deaf else ""
                                        print(f"[vc] State updated{mute_str}{deaf_str}")

                                _update_tray_icon_for_state()

                            elif other_uid and other_uid != my_user_id:
                                if _vc_channel_id is not None:
                                    if other_ch == _vc_channel_id:
                                        if other_uid not in _vc_member_ids:
                                            _vc_member_ids.add(other_uid)
                                            in_grace = (time.time() - _vc_join_time) < _VC_JOIN_GRACE
                                            if not in_grace:
                                                print(f"[vc] User {other_uid} joined VC → UserJoinedVC")
                                                if not _play_per_user_sound(other_uid, "vc_join"):
                                                    _play_notification_sound("UserJoinedVC")
                                            else:
                                                print(f"[vc] User {other_uid} was already in VC (grace)")
                                    else:
                                        if other_uid in _vc_member_ids:
                                            _vc_member_ids.discard(other_uid)
                                            if (time.time() - _vc_join_time) >= _VC_JOIN_GRACE:
                                                print(f"[vc] User {other_uid} left VC → UserLeftVC")
                                                if not _play_per_user_sound(other_uid, "vc_leave"):
                                                    _play_notification_sound("UserLeftVC")
                                        else:
                                            _vc_member_ids.discard(other_uid)
                            continue

                        if t == "CALL_CREATE":
                            call_channel = d.get("channel_id")
                            voice_states = d.get("voice_states", [])
                            already_in   = any(
                                vs.get("user_id") == my_user_id for vs in voice_states
                            )
                            print(f"[call] CALL_CREATE channel={call_channel} already_in={already_in} voice_states={len(voice_states)}")

                            if not call_channel:
                                continue
                            is_answer_event = (
                                call_channel == _outgoing_call_channel_id
                                and time.time() - _outgoing_call_time < 30.0
                                and not already_in
                                and len(voice_states) == 0
                            )
                            if is_answer_event:
                                print(f"[call] Suppressing answer-CALL_CREATE for outgoing call")
                                _outgoing_call_channel_id = None
                                continue

                            if already_in:
                                _active_call_channel_id   = call_channel
                                _outgoing_call_channel_id = call_channel
                                _outgoing_call_time       = time.time()
                                print(f"[call] Outgoing call started in channel {call_channel}")

                            else:
                                _active_call_channel_id = call_channel

                                caller = "Someone"
                                caller_user_id: str | None = None
                                try:
                                    async with http.get(
                                        f"{DISCORD_API}/channels/{call_channel}",
                                        headers={"Authorization": token},
                                    ) as r:
                                        if r.status == 200:
                                            ch = await r.json()
                                            ch_type = ch.get("type", -1)
                                            if ch_type == 1:
                                                for u in ch.get("recipients", []):
                                                    if u.get("id") != my_user_id:
                                                        caller = u.get("global_name") or u.get("username", "Someone")
                                                        caller_user_id = u.get("id")
                                                        break
                                            elif ch_type == 3:
                                                caller = ch.get("name") or ""
                                                if not caller:
                                                    names = [
                                                        u.get("global_name") or u.get("username", "?")
                                                        for u in ch.get("recipients", [])
                                                        if u.get("id") != my_user_id
                                                    ]
                                                    caller = ", ".join(names[:3])
                                                    if len(names) > 3:
                                                        caller += f" +{len(names) - 3}"
                                except Exception as e:
                                    print(f"[call] Could not resolve caller name: {e}")
                                    if voice_states:
                                        u = voice_states[0].get("member", {}).get("user", {})
                                        caller = u.get("global_name") or u.get("username", "Someone")

                                print(f"[call] Incoming call from {caller} in channel {call_channel}")
                                url = f"discord://-/channels/@me/{call_channel}"
                                show_balloon(_t("balloon_incoming"), _t("balloon_calling", caller=caller), url=url)
                                pu_call_path = _get_per_user_sound_path(caller_user_id, "call") if caller_user_id else None
                                _start_incoming_call_sound(path_override=pu_call_path)

                                def _call_timeout(ch=call_channel):
                                    time.sleep(60)
                                    if _active_call_channel_id == ch:
                                        print("[call] Ring timeout — stopping sound")
                                        _stop_incoming_call_sound()
                                threading.Thread(target=_call_timeout, daemon=True).start()
                            continue

                        if t == "CALL_DELETE":
                            print(f"[call] CALL_DELETE channel={d.get('channel_id')} active={_active_call_channel_id}")
                            if d.get("channel_id") == _active_call_channel_id:
                                print("[call] Call ended / missed")
                                _active_call_channel_id   = None
                                _outgoing_call_channel_id = None
                                _stop_incoming_call_sound()
                            continue

                        if t == "CHANNEL_DELETE":
                            del_ch = d.get("id")
                            if del_ch and del_ch in _unread_channels:
                                _unread_channels.discard(del_ch)
                                if not _unread_channels:
                                    _has_unread = False
                                _update_tray_icon_for_state()
                                print(f"[gateway] CHANNEL_DELETE cleaned unread for {del_ch}")
                            continue

                        if t == "USER_GUILD_SETTINGS_UPDATE":
                            upd_g, upd_c = _parse_muted([d])
                            gid = d.get("guild_id")
                            if gid:
                                muted_guilds.discard(gid)
                            muted_guilds   |= upd_g
                            muted_channels |= upd_c
                            print(f"[gateway] Mutes updated — "
                                  f"servers: {len(muted_guilds)}, channels: {len(muted_channels)}")
                            continue

                        if t == "MESSAGE_ACK":
                            global _focused_channel_id
                            ack_ch = d.get("channel_id")
                            if ack_ch:
                                ack_times[ack_ch] = time.time()
                                if _discord_has_focus():
                                    _focused_channel_id = ack_ch
                                if ack_ch in _unread_channels:
                                    _unread_channels.discard(ack_ch)
                                    if not _unread_channels:
                                        _has_unread = False
                                    _update_tray_icon_for_state()
                                    print(f"[gateway] ACK channel {ack_ch} — "
                                          f"{'all read' if not _unread_channels else f'{len(_unread_channels)} remaining'}")
                                else:
                                    print(f"[gateway] ACK channel {ack_ch} (focused, not tracked)")
                            continue

                        if t == "CHANNEL_UNREAD_UPDATE":
                            updates = d.get("channel_unread_updates", [])
                            changed = False
                            for upd in updates:
                                ch_id = upd.get("id")
                                if ch_id and ch_id in _unread_channels:
                                    _unread_channels.discard(ch_id)
                                    changed = True
                            if changed:
                                if not _unread_channels:
                                    _has_unread = False
                                _update_tray_icon_for_state()
                                print(f"[gateway] CHANNEL_UNREAD_UPDATE — "
                                      f"{'all read' if not _unread_channels else f'{len(_unread_channels)} unread'}")
                            continue

                        if t == "NOTIFICATION_CENTER_ITEM_CREATE":
                            item = d.get("item", d)
                            ch_id = item.get("channel_id")
                            if ch_id and ch_id not in muted_channels:
                                _unread_channels.add(ch_id)
                                _has_unread = True
                                _update_tray_icon_for_state()
                                print(f"[gateway] NOTIFICATION_CENTER: unread += {ch_id}")
                            continue

                        if t != "MESSAGE_CREATE":
                            continue

                        if not my_user_id:
                            print("[msg] Dropping MESSAGE_CREATE — my_user_id not yet known (reconnecting)")
                            continue

                        author = d.get("author", {})
                        if author.get("bot"):
                            continue
                        if author.get("id") == my_user_id:
                            continue

                        guild_id   = d.get("guild_id")
                        channel_id = d.get("channel_id")

                        if _my_status in DND_STATUSES:

                            if not guild_id:
                                print(f"[dnd] DM suppressed (status=dnd)")
                                continue
                            if not _was_mentioned(d, my_user_id):
                                print(f"[dnd] Notification suppressed (status=dnd, no mention)")
                                continue

                        if guild_id and guild_id in muted_guilds:
                            print(f"[muted] Muted server ({guild_id}), skipping.")
                            continue
                        if channel_id and channel_id in muted_channels:
                            print(f"[muted] Muted channel ({channel_id}), skipping.")
                            continue
                            
                        _notif_mode = load_config().get("notification_mode", "all")
                        if _notif_mode == "mentions_only" and guild_id:
                            if not _was_mentioned(d, my_user_id):
                                print(f"[msg] Skipped (mentions_only mode, no mention)")
                                continue

                        content = d.get("content", "").strip()
                        if not content:
                            attachments = d.get("attachments", [])
                            stickers    = d.get("sticker_items", [])
                            embeds      = d.get("embeds", [])
                            if attachments:
                                content = f"[{len(attachments)} attachment(s)]"
                            elif stickers:
                                content = "[sticker]"
                            elif embeds:
                                e     = embeds[0]
                                parts = [p for p in [e.get("title", ""),
                                                     e.get("description", "")] if p]
                                content = " — ".join(parts) if parts else "[embed]"
                            else:
                                content = "[media]"

                        if len(content) > 200:
                            content = content[:197] + "…"

                        nick_key  = (guild_id, author.get("id"))
                        need_nick = nick_key not in nick_cache
                        need_chan  = guild_id and channel_id not in channel_cache

                        if need_nick and need_chan:
                            nick, chan_info = await asyncio.gather(
                                _get_nick(http, token, guild_id, author),
                                _get_channel_info(http, token, guild_id, channel_id),
                            )
                            nick_cache[nick_key]      = nick
                            channel_cache[channel_id] = chan_info
                        elif need_nick:
                            nick_cache[nick_key] = await _get_nick(http, token, guild_id, author)
                        elif need_chan:
                            channel_cache[channel_id] = await _get_channel_info(
                                http, token, guild_id, channel_id)

                        name = nick_cache[nick_key]
                        is_reply = bool(d.get("referenced_message"))

                        notif_style = load_config().get("notif_style", "instant")
                        if notif_style == "queue":

                            verb = " replied" if is_reply else " wrote"
                            if guild_id:
                                channel_name, guild_name = channel_cache[channel_id]
                                in_part = f" in #{channel_name}" if channel_name else ""
                                title = f"{name}{verb}{in_part}"
                            else:
                                title = f"{name}{verb}"
                        else:
                            if guild_id:
                                channel_name, guild_name = channel_cache[channel_id]
                                ctx   = []
                                if channel_name: ctx.append(f"#{channel_name}")
                                if guild_name:   ctx.append(guild_name)
                                title = f"{name} ({', '.join(ctx)})" if ctx else name
                            else:
                                title = name

                        last_ack = ack_times.get(channel_id, 0.0)
                        content = _resolve_mentions(content, d)
                        print(f"[msg] {title}: {content}")
                        if guild_id:
                            url = f"discord://-/channels/{guild_id}/{channel_id}"
                        else:
                            url = f"discord://-/channels/@me/{channel_id}"

                        if load_config().get("show_avatar_icon", True):
                            pfp_user_id   = author.get("id", "")
                            pfp_avatar    = author.get("avatar")
                            print(f"[avatar] Downloading PFP: user={pfp_user_id} hash={pfp_avatar}")
                            pfp_path = await asyncio.get_event_loop().run_in_executor(
                                None, _download_pfp, pfp_user_id, pfp_avatar
                            )
                            print(f"[avatar] da PFP is ready: {pfp_path}")
                            _set_pending_avatar(pfp_path)

                        show_balloon(title, content, url=url,
                                     channel_id=channel_id,
                                     sound_key="NewMention" if _was_mentioned(d, my_user_id) else "NewMessage")

                        if load_config().get("notif_style", "instant") != "queue":
                            if not load_config().get("balloon_sound_mode", False):
                                if not _should_suppress_channel(channel_id):
                                    author_id = author.get("id", "")
                                    if not _play_per_user_sound(author_id, "message"):
                                        if _was_mentioned(d, my_user_id):
                                            _play_notification_sound("NewMention")
                                        else:
                                            _play_notification_sound("NewMessage")

        except Exception as e:
            print(f"[gateway] Error: {e}")
        finally:
            _gw_ws = None
            if heartbeat_task:
                heartbeat_task.cancel()

        print("[gateway] Retrying in 5 seconds...")
        await asyncio.sleep(5)

XP_FACE      = "#D4D0C8"
XP_FACE_DARK = "#C0C0C0" 
XP_WHITE     = "#FFFFFF" 
XP_BORDER    = "#808080"
XP_HIGHLIGHT = "#0A246A" 
XP_HITEXT    = "#FFFFFF" 
XP_TEXT      = "#000000" 
XP_GREY_TXT  = "#444444" 
XP_TITLEBAR  = "#0054E3"
XP_BTN_TXT   = "#000000"
CMD_BG       = "#000000"
CMD_FG       = "#C0C0C0" 
CMD_GREEN    = "#00FF00"  
CMD_YELLOW   = "#FFFF00" 
CMD_RED      = "#FF0000"  
CMD_CYAN     = "#00FFFF"  
CMD_DARKGREY = "#808080"   

XP_FONT      = ("Tahoma", 8)
XP_FONT_BOLD = ("Tahoma", 8, "bold")
CMD_FONT     = ("Lucida Console", 9)

def xp_title_bar(parent: tk.Widget, title: str, icon: str = ""):

    bar = tk.Frame(parent, bg=XP_TITLEBAR, height=28)
    bar.pack(fill=tk.X)
    bar.pack_propagate(False)
    lbl_text = f"  {icon}  {title}" if icon else f"  {title}"
    tk.Label(bar, text=lbl_text, bg=XP_TITLEBAR, fg=XP_HITEXT,
             font=("Tahoma", 9, "bold")).pack(side=tk.LEFT, padx=4, pady=4)
    return bar

def xp_button(parent, text, command, width=None, **kw):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=XP_FACE, fg=XP_BTN_TXT,
        activebackground=XP_FACE_DARK, activeforeground=XP_BTN_TXT,
        relief=tk.RAISED, bd=2,
        font=XP_FONT,
        cursor="arrow",
        **kw,
    )
    if width:
        btn.config(width=width)
    return btn

def xp_label(parent, text, fg=XP_TEXT, **kw):
    return tk.Label(parent, text=text, bg=XP_FACE, fg=fg, font=XP_FONT, **kw)

def xp_checkbox(parent, text, variable, **kw):
    return tk.Checkbutton(
        parent, text=text,
        variable=variable,
        bg=XP_FACE, fg=XP_TEXT,
        selectcolor=XP_WHITE,
        activebackground=XP_FACE, activeforeground=XP_TEXT,
        font=XP_FONT,
        **kw,
    )

def xp_separator(parent):
    return tk.Frame(parent, bg=XP_BORDER, height=1)

class LogWindow:

    def __init__(self, root: tk.Tk) -> None:
        self.root    = root
        self.visible = False

        self.win = tk.Toplevel(root)
        self.win.title("Event Log")
        self.win.geometry("680x400")
        self.win.configure(bg=XP_FACE)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)
        self.win.withdraw()
        _set_discord_icon_on_window(self.win)

        self._build()
        self._poll()

    def _build(self) -> None:
        toolbar = tk.Frame(self.win, bg=XP_FACE, bd=1, relief=tk.FLAT)
        toolbar.pack(fill=tk.X, padx=2, pady=(2, 0))

        xp_button(toolbar, "Clear", self._clear, width=8).pack(side=tk.LEFT, padx=4, pady=2)

        self.hide_muted_var = tk.BooleanVar(value=True)
        xp_checkbox(toolbar, "Hide muted traces", self.hide_muted_var).pack(
            side=tk.LEFT, padx=(8, 4), pady=2)

        xp_separator(self.win).pack(fill=tk.X, padx=2, pady=2)

        frame = tk.Frame(self.win, bg=CMD_BG, bd=2, relief=tk.SUNKEN)
        frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.text = tk.Text(
            frame,
            bg=CMD_BG, fg=CMD_FG,
            font=CMD_FONT,
            state=tk.DISABLED,
            wrap=tk.WORD,
            relief=tk.FLAT,
            insertbackground=CMD_FG,
            selectbackground=XP_HIGHLIGHT,
            selectforeground=XP_HITEXT,
            cursor="arrow",
            bd=0,
        )
        sb = tk.Scrollbar(frame, command=self.text.yview,
                          bg=XP_FACE, troughcolor=XP_FACE_DARK, relief=tk.FLAT)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(fill=tk.BOTH, expand=True)

        self.text.tag_configure("ts",      foreground=CMD_DARKGREY)
        self.text.tag_configure("gateway", foreground=CMD_CYAN)
        self.text.tag_configure("msg",     foreground=CMD_GREEN)
        self.text.tag_configure("muted",   foreground=CMD_DARKGREY)
        self.text.tag_configure("dnd",     foreground=CMD_YELLOW)
        self.text.tag_configure("error",   foreground=CMD_RED)
        self.text.tag_configure("info",    foreground=CMD_FG)

    def _tag_for(self, msg: str) -> str:
        if "[gateway]" in msg: return "gateway"
        if "[msg]"     in msg: return "msg"
        if "[muted]"   in msg: return "muted"
        if "[dnd]"     in msg: return "dnd"
        if "error" in msg.lower() or "Error" in msg: return "error"
        return "info"

    def _poll(self) -> None:
        try:
            while True:
                msg = _log_queue.get_nowait()
                self._append(msg)
        except queue.Empty:
            pass
        self.root.after(120, self._poll)

    def _append(self, msg: str) -> None:
        if "[muted]" in msg and self.hide_muted_var.get():
            return
        ts  = datetime.now().strftime("%H:%M:%S")
        tag = self._tag_for(msg)
        self.text.configure(state=tk.NORMAL)
        self.text.insert(tk.END, f"{ts}  ", "ts")
        self.text.insert(tk.END, msg + "\n", tag)
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def _clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)

    def show(self) -> None:
        self.win.deiconify()
        self.win.lift()
        self.visible = True

    def hide(self) -> None:
        self.win.withdraw()
        self.visible = False

    def toggle(self) -> None:
        if self.visible:
            self.hide()
        else:
            self.show()

_settings_win_instance = None

def _open_settings_window() -> None:
    global _settings_win_instance
    if _settings_win_instance and _settings_win_instance.alive:
        _settings_win_instance.lift()
        return
    _settings_win_instance = SettingsWindow(_tk_root)

class SettingsWindow:

    def __init__(self, root: tk.Tk) -> None:
        self.root  = root
        self.alive = True

        self.win = tk.Toplevel(root)
        self.win.title(_t("settings_title"))
        self.win.resizable(True, True)
        self.win.minsize(520, 420)
        self.win.configure(bg=XP_FACE)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        _set_discord_icon_on_window(self.win)

        self._cfg = load_config()

        self._notif_var       = tk.StringVar(value=self._cfg.get("notification_mode", "all"))
        self._check_updates_var = tk.BooleanVar(value=bool(self._cfg.get("check_for_updates", True)))
        self._auto_update_var = tk.BooleanVar(value=bool(self._cfg.get("auto_update", False)))
        self._balloon_sound_var = tk.BooleanVar(value=bool(self._cfg.get("balloon_sound_mode", False)))
        _exit_close = self._cfg.get("exit_close_client", None)
        self._exit_close_var = tk.BooleanVar(value=(_exit_close is True))
        self._style_var     = tk.StringVar(value=self._cfg.get("notif_style", "instant"))
        self._cooldown_var  = tk.IntVar(value=int(self._cfg.get("replace_cooldown", 4.0)))
        self._cooldown_lbl  = tk.StringVar(value=f"{self._cooldown_var.get()}s")
        _vol                = int(self._cfg.get("sound_volume", 1.0) * 100)
        self._vol_var       = tk.IntVar(value=_vol)
        self._vol_label_var = tk.StringVar(value=f"{_vol}%")
        self._sound_vars: dict[str, tk.StringVar] = {}
        self._icon_vars:  dict[str, tk.StringVar] = {}
        self._user_sound_entries: list[dict] = []

        self._build()
        self._center(580, 500)

    def _center(self, w: int, h: int) -> None:
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def lift(self) -> None:
        self.win.deiconify()
        self.win.lift()

    def _on_close(self) -> None:
        self.alive = False
        self.win.destroy()

    def _build(self) -> None:
        self._tab_btns: list[tk.Button] = []
        self._pages:    list[tk.Frame]  = []
        tab_bar = tk.Frame(self.win, bg=XP_FACE)
        tab_bar.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(6, 0))

        for i, lbl in enumerate([_t("tab_notif_mode"), _t("tab_notif_style"), _t("tab_sounds"), _t("tab_icons"), _t("tab_per_user"), _t("tab_more")]):
            btn = tk.Button(
                tab_bar, text=lbl, font=XP_FONT_BOLD,
                bg=XP_FACE, fg=XP_TEXT,
                activebackground=XP_WHITE, activeforeground=XP_TEXT,
                relief=tk.RAISED, bd=2, cursor="arrow",
                command=lambda idx=i: self._switch_tab(idx),
            )
            btn.pack(side=tk.LEFT, padx=(0, 2))
            self._tab_btns.append(btn)

        xp_separator(self.win).pack(side=tk.TOP, fill=tk.X, padx=6)

        xp_separator(self.win).pack(side=tk.BOTTOM, fill=tk.X, padx=6)
        btn_row = tk.Frame(self.win, bg=XP_FACE)
        btn_row.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)
        xp_button(btn_row, _t("btn_ok"),     self._save_and_close, width=10).pack(side=tk.RIGHT, padx=(4, 2))
        xp_button(btn_row, _t("btn_cancel"), self._on_close,       width=10).pack(side=tk.RIGHT, padx=2)
        xp_button(btn_row, _t("btn_apply"),  self._save,           width=10).pack(side=tk.RIGHT, padx=2)

        self._container = tk.Frame(self.win, bg=XP_FACE)
        self._container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=4)

        for fn in (self._build_notif_page,
                   self._build_style_page,
                   self._build_sounds_page,
                   self._build_tray_icons_page,
                   self._build_per_user_sounds_page,
                   self._build_more_page):
            page = tk.Frame(self._container, bg=XP_FACE)
            fn(page)
            self._pages.append(page)

        self._switch_tab(0)

    def _switch_tab(self, idx: int) -> None:
        for i, btn in enumerate(self._tab_btns):
            btn.config(
                relief=tk.SUNKEN if i == idx else tk.RAISED,
                bg=XP_WHITE    if i == idx else XP_FACE,
            )
        for i, page in enumerate(self._pages):
            if i == idx:
                page.pack(fill=tk.BOTH, expand=True)
            else:
                page.pack_forget()

    def _build_notif_page(self, parent: tk.Frame) -> None:
        grp = tk.LabelFrame(parent, text=_t("grp_notif_mode"),
                            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                            bd=2, relief=tk.GROOVE)
        grp.pack(fill=tk.X, padx=4, pady=8)

        for val, title, desc in [
            ("all",      _t("notif_all_title"),      _t("notif_all_desc")),
            ("mentions_only", _t("notif_mention_title"), _t("notif_mention_desc")),
        ]:
            tk.Radiobutton(grp, text=title, variable=self._notif_var, value=val,
                           bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                           activebackground=XP_FACE, activeforeground=XP_TEXT,
                           font=XP_FONT_BOLD, anchor=tk.W,
                           ).pack(fill=tk.X, padx=10, pady=(8, 0))
            tk.Label(grp, text=desc, bg=XP_FACE, fg=XP_GREY_TXT,
                     font=("Tahoma", 7), justify=tk.LEFT, anchor=tk.W,
                     ).pack(fill=tk.X, padx=28, pady=(0, 4))

        launch_grp = tk.LabelFrame(parent, text=_t("grp_launch"),
                                   bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                   bd=2, relief=tk.GROOVE)
        launch_grp.pack(fill=tk.X, padx=4, pady=(0, 8))

        self._auto_open_var = tk.BooleanVar(value=bool(self._cfg.get("auto_open_client", False)))
        xp_checkbox(launch_grp, _t("chk_auto_open"), self._auto_open_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 2))
        tk.Label(launch_grp, text=_t("chk_auto_open_desc"),
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

    def _build_style_page(self, parent: tk.Frame) -> None:
        grp = tk.LabelFrame(parent, text=_t("grp_notif_style"),
                            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                            bd=2, relief=tk.GROOVE)
        grp.pack(fill=tk.X, padx=4, pady=8)

        for val, title, desc in [
            ("instant", _t("style_instant_title"), _t("style_instant_desc")),
            ("replace", _t("style_replace_title"), _t("style_replace_desc")),
            ("queue",   _t("style_queue_title"),   _t("style_queue_desc")),
        ]:
            tk.Radiobutton(grp, text=title, variable=self._style_var, value=val,
                           bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                           activebackground=XP_FACE, activeforeground=XP_TEXT,
                           font=XP_FONT_BOLD, anchor=tk.W,
                           ).pack(fill=tk.X, padx=10, pady=(8, 0))
            tk.Label(grp, text=desc, bg=XP_FACE, fg=XP_GREY_TXT,
                     font=("Tahoma", 7), justify=tk.LEFT, anchor=tk.W,
                     ).pack(fill=tk.X, padx=28, pady=(0, 4))

        cool_grp = tk.LabelFrame(parent, text=_t("grp_cooldown"),
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        cool_grp.pack(fill=tk.X, padx=4, pady=(0, 8))

        row = tk.Frame(cool_grp, bg=XP_FACE)
        row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(row, _t("lbl_cooldown")).pack(side=tk.LEFT)
        tk.Scale(row, from_=1, to=30, orient=tk.HORIZONTAL,
                 variable=self._cooldown_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=180,
                 command=lambda v: self._cooldown_lbl.set(f"{int(float(v))}s"),
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(row, textvariable=self._cooldown_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=3,
                 ).pack(side=tk.LEFT)
        xp_label(row, _t("lbl_cooldown_note"), fg=XP_GREY_TXT).pack(side=tk.LEFT, padx=(8, 0))

                                                                                
        bsnd_grp = tk.LabelFrame(parent, text=_t("grp_balloon_sound"),
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        bsnd_grp.pack(fill=tk.X, padx=4, pady=(0, 8))
        xp_checkbox(bsnd_grp, _t("chk_balloon_sound"), self._balloon_sound_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 2))
        tk.Label(bsnd_grp, text=_t("chk_balloon_sound_desc"),
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

    def _build_sounds_page(self, parent: tk.Frame) -> None:
        vol_grp = tk.LabelFrame(parent, text=_t("grp_volume"),
                                bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                bd=2, relief=tk.GROOVE)
        vol_grp.pack(fill=tk.X, padx=4, pady=(6, 4))

        vrow = tk.Frame(vol_grp, bg=XP_FACE)
        vrow.pack(fill=tk.X, padx=10, pady=6)
        xp_label(vrow, "\u25a1").pack(side=tk.LEFT)
        tk.Scale(vrow, from_=0, to=100, orient=tk.HORIZONTAL,
                 variable=self._vol_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=240,
                 command=lambda v: self._vol_label_var.set(f"{int(float(v))}%"),
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(vrow, textvariable=self._vol_label_var,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=4,
                 ).pack(side=tk.LEFT)
        xp_label(vrow, "\u266a").pack(side=tk.LEFT, padx=(0, 4))

        xp_label(parent, _t("sounds_hint"),
                 fg=XP_GREY_TXT,
                 ).pack(anchor=tk.W, padx=6, pady=(0, 2))

        outer = tk.Frame(parent, bg=XP_BORDER, bd=1, relief=tk.SUNKEN)
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        canvas = tk.Canvas(outer, bg=XP_FACE, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview,
                          bg=XP_FACE, troughcolor=XP_FACE_DARK, relief=tk.FLAT)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas, bg=XP_FACE)
        win_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        custom_sounds = self._cfg.get("custom_sounds", {})
        for event_key, label in _SOUND_EVENTS:
            row = tk.Frame(inner, bg=XP_FACE)
            row.pack(fill=tk.X, padx=6, pady=3)
            tk.Label(row, text=label, width=14, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            var = tk.StringVar(value=custom_sounds.get(event_key, ""))
            self._sound_vars[event_key] = var
            ef = tk.Frame(row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
            tk.Entry(ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                     ).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(row, "…", lambda ek=event_key: self._browse_sound(ek), width=2).pack(side=tk.LEFT, padx=(0, 2))
            xp_button(row, "▶", lambda ek=event_key: self._preview_sound(ek), width=2).pack(side=tk.LEFT)

    _PU_EVENTS: list[tuple[str, str]] = [
        ("message",  "Message"),
        ("call",     "Call"),
        ("vc_join",  "VC Join"),
        ("vc_leave", "VC Leave"),
    ]

    def _build_per_user_sounds_page(self, parent: tk.Frame) -> None:
        xp_label(parent, _t("per_user_hint"), fg=XP_GREY_TXT).pack(anchor=tk.W, padx=6, pady=(6, 2))

        btn_row = tk.Frame(parent, bg=XP_FACE)
        btn_row.pack(fill=tk.X, padx=6, pady=(0, 4))
        xp_button(btn_row, _t("btn_add_user"), self._pu_add_user, width=12).pack(side=tk.LEFT)
        outer = tk.Frame(parent, bg=XP_BORDER, bd=1, relief=tk.SUNKEN)
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self._pu_canvas = tk.Canvas(outer, bg=XP_FACE, highlightthickness=0)
        pu_sb = tk.Scrollbar(outer, orient=tk.VERTICAL,
                             command=self._pu_canvas.yview,
                             bg=XP_FACE, troughcolor=XP_FACE_DARK, relief=tk.FLAT)
        self._pu_canvas.configure(yscrollcommand=pu_sb.set)
        pu_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._pu_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._pu_inner = tk.Frame(self._pu_canvas, bg=XP_FACE)
        self._pu_win_id = self._pu_canvas.create_window(
            (0, 0), window=self._pu_inner, anchor=tk.NW
        )
        self._pu_canvas.bind(
            "<Configure>",
            lambda e: self._pu_canvas.itemconfig(self._pu_win_id, width=e.width)
        )
        self._pu_inner.bind(
            "<Configure>",
            lambda e: self._pu_canvas.configure(scrollregion=self._pu_canvas.bbox("all"))
        )

        saved = self._cfg.get("per_user_sounds", {})
        for uid, sounds in saved.items():
            self._pu_add_user(uid, sounds)

    def _pu_add_user(self, user_id: str = "", sounds: "dict | None" = None) -> None:

        if sounds is None:
            sounds = {}

        frame = tk.LabelFrame(
            self._pu_inner, text=" User ",
            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
            bd=2, relief=tk.GROOVE,
        )
        frame.pack(fill=tk.X, padx=4, pady=4)

        hdr = tk.Frame(frame, bg=XP_FACE)
        hdr.pack(fill=tk.X, padx=6, pady=(4, 2))
        xp_label(hdr, "Discord User ID:").pack(side=tk.LEFT)
        id_var = tk.StringVar(value=user_id)
        id_frame = tk.Frame(hdr, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        id_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))
        tk.Entry(id_frame, textvariable=id_var, bg=XP_WHITE, fg=XP_TEXT,
                 insertbackground=XP_TEXT, relief=tk.FLAT, font=("Lucida Console", 8),
                 ).pack(fill=tk.X, ipady=3, padx=1, pady=1)

        entry: dict = {"frame": frame, "id_var": id_var}

        def _remove(e=entry):
            self._pu_remove_user(e)

        xp_button(hdr, "✕ Remove", _remove, width=9).pack(side=tk.LEFT)

        for ev_key, ev_label in self._PU_EVENTS:
            row = tk.Frame(frame, bg=XP_FACE)
            row.pack(fill=tk.X, padx=6, pady=2)
            tk.Label(row, text=ev_label, width=9, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            var = tk.StringVar(value=sounds.get(ev_key, ""))
            entry[f"{ev_key}_var"] = var
            ef = tk.Frame(row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
            tk.Entry(ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                     ).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(row, "…",
                      lambda v=var, ek=ev_key: self._pu_browse(v, ek),
                      width=2).pack(side=tk.LEFT, padx=(0, 2))
            xp_button(row, "▶",
                      lambda v=var: self._pu_preview(v),
                      width=2).pack(side=tk.LEFT)

        tk.Frame(frame, bg=XP_FACE, height=2).pack()

        self._user_sound_entries.append(entry)

    def _pu_remove_user(self, entry: dict) -> None:
        entry["frame"].destroy()
        self._user_sound_entries.remove(entry)

    def _pu_browse(self, var: tk.StringVar, event_key: str) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win,
            title=f"Select audio for: {event_key}",
            filetypes=[("Audio files", "*.wav *.mp3 *.ogg *.flac"),
                       ("WAV files", "*.wav"), ("All files", "*.*")],
        )
        if path:
            var.set(path)

    def _pu_preview(self, var: tk.StringVar) -> None:
        path = var.get().strip()
        if path and os.path.isfile(path):
            volume = _get_volume()
            threading.Thread(
                target=_pygame_play, args=(path, volume, "message"), daemon=True
            ).start()

    def _browse_sound(self, event_key: str) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win,
            title=f"Select .wav for: {event_key}",
            filetypes=[("Audio files", "*.wav *.mp3 *.ogg *.flac"), ("WAV files", "*.wav"), ("All files", "*.*")],
        )
        if path:
            self._sound_vars[event_key].set(path)

    def _preview_sound(self, event_key: str) -> None:
        path = self._sound_vars[event_key].get().strip()
        if path and os.path.isfile(path):
            group = _SOUND_GROUP.get(event_key, "message")
            volume = _get_volume()
            threading.Thread(
                target=_pygame_play,
                args=(path, volume, group),
                daemon=True,
            ).start()

    _ICON_STATES: list[tuple[str, str]] = [
        ("normal",  "Normal"),
        ("unread",  "Unread Messages"),
        ("vc",      "In Voice Channel"),
        ("muted",   "Muted"),
        ("deaf",    "Deafened"),
    ]

    def _build_tray_icons_page(self, parent: tk.Frame) -> None:
        xp_label(parent, _t("icons_hint"), fg=XP_GREY_TXT).pack(anchor=tk.W, padx=6, pady=(6, 4))

        grp = tk.LabelFrame(parent, text=_t("grp_icons"),
                            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                            bd=2, relief=tk.GROOVE)
        grp.pack(fill=tk.X, padx=4, pady=(0, 6))

        icon_paths = self._cfg.get("tray_icons", {})
        for state_key, label in self._ICON_STATES:
            row = tk.Frame(grp, bg=XP_FACE)
            row.pack(fill=tk.X, padx=6, pady=3)
            tk.Label(row, text=label, width=18, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            var = tk.StringVar(value=icon_paths.get(state_key, ""))
            self._icon_vars[state_key] = var
            ef = tk.Frame(row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
            tk.Entry(ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                     ).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(row, "…",
                      lambda sk=state_key: self._browse_icon(sk),
                      width=2).pack(side=tk.LEFT, padx=(0, 2))
            xp_button(row, "▶",
                      lambda sk=state_key: self._preview_icon(sk),
                      width=2).pack(side=tk.LEFT)

        note_row = tk.Frame(parent, bg=XP_FACE)
        note_row.pack(fill=tk.X, padx=4, pady=(0, 4))
        xp_label(note_row,
                 "▶ previews the icon in the tray immediately (reverts on next state change).",
                 fg=XP_GREY_TXT).pack(anchor=tk.W, padx=6)

        state_row = tk.Frame(parent, bg=XP_FACE)
        state_row.pack(fill=tk.X, padx=4)
        cur_state = (
            "deaf"   if (_vc_self_deaf and _vc_channel_id) else
            "muted"  if (_vc_self_mute and _vc_channel_id) else
            "vc"     if _vc_channel_id else
            "unread" if _has_unread else
            "normal"
        )
        xp_label(state_row,
                 f"Current state: {cur_state}",
                 fg=XP_GREY_TXT).pack(anchor=tk.W, padx=6)

    def _browse_icon(self, state_key: str) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win,
            title=f"Select PNG icon for state: {state_key}",
            filetypes=[("PNG files", "*.png"), ("ICO files", "*.ico"),
                       ("All files", "*.*")],
        )
        if path:
            self._icon_vars[state_key].set(path)

    def _preview_icon(self, state_key: str) -> None:
        path = self._icon_vars[state_key].get().strip()
        if not path or not os.path.isfile(path):
            return
        hicon = _file_to_hicon(path, size=16)
        if hicon:
            _set_tray_icon_handle(hicon)
            print(f"[tray] Preview icon for '{state_key}': {os.path.basename(path)}")

    def _build_more_page(self, parent: tk.Frame) -> None:
                                                                                
        exit_grp = tk.LabelFrame(parent, text=_t("grp_exit_settings"),
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        exit_grp.pack(fill=tk.X, padx=4, pady=(8, 4))

        xp_checkbox(exit_grp, _t("exit_chk_close_discord"), self._exit_close_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 6))

                                                                               
        update_grp = tk.LabelFrame(parent, text=_t("grp_update"),
                                   bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                   bd=2, relief=tk.GROOVE)
        update_grp.pack(fill=tk.X, padx=4, pady=(8, 4))

        xp_checkbox(update_grp, _t("chk_check_updates"), self._check_updates_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 2))
        tk.Label(update_grp, text=_t("chk_check_updates_desc"),
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 4))

        xp_checkbox(update_grp, _t("chk_auto_update"), self._auto_update_var,
                    ).pack(anchor=tk.W, padx=10, pady=(2, 2))
        tk.Label(update_grp, text=_t("chk_auto_update_desc"),
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

                                                                                
        about_grp = tk.LabelFrame(parent, text=" About ",
                                  bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                  bd=2, relief=tk.GROOVE)
        about_grp.pack(fill=tk.X, padx=4, pady=(0, 8))

        tk.Label(
            about_grp,
            text=f"Balloncord v{VERSION}",
            bg=XP_FACE, fg=XP_TEXT,
            font=("Tahoma", 10, "bold"),
            anchor=tk.W,
        ).pack(anchor=tk.W, padx=12, pady=(10, 0))

        tk.Label(
            about_grp,
            text="Made by Mozaico",
            bg=XP_FACE, fg=XP_GREY_TXT,
            font=("Tahoma", 8),
            anchor=tk.W,
        ).pack(anchor=tk.W, padx=12, pady=(2, 10))

    def _save(self) -> None:
        cfg = load_config()
        cfg["notification_mode"] = self._notif_var.get()
        cfg["notif_style"]       = self._style_var.get()
        cfg["replace_cooldown"]  = float(self._cooldown_var.get())
        cfg["sound_volume"]      = round(self._vol_var.get() / 100.0, 2)
        cfg["custom_sounds"]     = {ek: v.get().strip()
                                    for ek, v in self._sound_vars.items()
                                    if v.get().strip()}
        cfg["tray_icons"]        = {sk: v.get().strip()
                                    for sk, v in self._icon_vars.items()
                                    if v.get().strip()}
        per_user: dict = {}
        for entry in self._user_sound_entries:
            uid = entry["id_var"].get().strip()
            if not uid:
                continue
            sounds = {
                ev: entry[f"{ev}_var"].get().strip()
                for ev, _ in self._PU_EVENTS
                if entry[f"{ev}_var"].get().strip()
            }
            if sounds:
                per_user[uid] = sounds
        cfg["per_user_sounds"] = per_user
        cfg["auto_open_client"] = bool(getattr(self, "_auto_open_var", tk.BooleanVar()).get())
        cfg["check_for_updates"] = bool(getattr(self, "_check_updates_var", tk.BooleanVar(value=True)).get())
        cfg["auto_update"]      = bool(getattr(self, "_auto_update_var", tk.BooleanVar()).get())
        cfg["balloon_sound_mode"] = bool(getattr(self, "_balloon_sound_var", tk.BooleanVar()).get())
        if getattr(self, "_exit_close_var", tk.BooleanVar()).get():
            cfg["exit_close_client"] = True
        else:
            cfg.pop("exit_close_client", None)
        save_config(cfg)
        _clear_sound_cache()  
        _clear_state_icon_cache()    
        _update_tray_icon_for_state() 
        print(f"[settings] Saved. mode={cfg['notification_mode']}, "

              f"per_user_sounds={len(cfg.get('per_user_sounds', {}))}")

    def _save_and_close(self) -> None:
        self._save()
        self._on_close()

class LoginWindow:

    def __init__(self, root: tk.Tk, on_login) -> None:
        self.root     = root
        self.on_login = on_login

        cfg = load_config()

        self.win = tk.Toplevel(root)
        self.win.title(_t("win_title"))
        self.win.resizable(False, False)
        self.win.configure(bg=XP_FACE)
        self.win.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        _set_discord_icon_on_window(self.win)

        if cfg.get("auto_login") and cfg.get("token"):
            self.win.withdraw()
            on_login(cfg["token"])
            return

        self._build()
        self.win.update_idletasks()
        h = max(self.win.winfo_reqheight(), 480)
        self._center(440, h)

    def _center(self, w: int, h: int) -> None:
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _rebuild(self) -> None:

        for w in self.win.winfo_children():
            w.destroy()
        self.win.title(_t("win_title"))
        self._build()
        self.win.update_idletasks()
        h = max(self.win.winfo_reqheight(), 480)
        self._center(440, h)

    def _build(self) -> None:
        cfg = load_config()

        xp_title_bar(self.win, _t("win_title"), "")

        header = tk.Frame(self.win, bg=XP_WHITE, bd=1, relief=tk.FLAT)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text=_t("header_title"),
            bg=XP_WHITE, fg=XP_TEXT,
            font=("Tahoma", 10, "bold"),
        ).pack(side=tk.LEFT, padx=12, pady=10)

        tk.Label(
            header,
            text=_t("header_sub"),
            bg=XP_WHITE, fg=XP_GREY_TXT,
            font=("Tahoma", 8),
        ).pack(side=tk.LEFT, padx=0, pady=10)

        xp_separator(self.win).pack(fill=tk.X)

        body = tk.Frame(self.win, bg=XP_FACE)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        lang_row = tk.Frame(body, bg=XP_FACE)
        lang_row.pack(fill=tk.X, pady=(0, 6))
        xp_label(lang_row, _t("lbl_language")).pack(side=tk.LEFT)

        _langs          = _available_languages()      
        _lang_codes     = [c for c, _ in _langs]
        _lang_labels    = [l for _, l in _langs]
        _cur_code       = cfg.get("language", "en")
        _cur_label      = _lang_labels[_lang_codes.index(_cur_code)] if _cur_code in _lang_codes else _lang_labels[0]

        self.lang_var = tk.StringVar(value=_cur_label)

        _lang_combo = ttk.Combobox(
            lang_row,
            textvariable=self.lang_var,
            values=_lang_labels,
            state="readonly",
            width=16,
            font=XP_FONT,
        )
        _lang_combo.pack(side=tk.LEFT, padx=(8, 0))

        def _on_lang_change(*_):
            selected_label = self.lang_var.get()
            if selected_label in _lang_labels:
                new_lang = _lang_codes[_lang_labels.index(selected_label)]
            else:
                new_lang = "en"
            c = load_config()
            c["language"] = new_lang
            save_config(c)
            _lang_cache.clear()
            self._rebuild()

        _lang_combo.bind("<<ComboboxSelected>>", _on_lang_change)

        xp_label(body, _t("lbl_token")).pack(anchor=tk.W, pady=(4, 2))

        entry_frame = tk.Frame(body, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        entry_frame.pack(fill=tk.X, pady=(0, 4))

        self.token_var = tk.StringVar(value=cfg.get("token", ""))
        self.entry = tk.Entry(
            entry_frame,
            textvariable=self.token_var,
            show="*",
            bg=XP_WHITE, fg=XP_TEXT,
            insertbackground=XP_TEXT,
            relief=tk.FLAT,
            font=("Lucida Console", 9),
        )
        self.entry.pack(fill=tk.X, ipady=4, padx=1, pady=1)

        self.show_var = tk.BooleanVar()
        xp_checkbox(body, _t("chk_show"), self.show_var,
                    command=self._toggle_show).pack(anchor=tk.W, pady=(0, 6))

        grp_outer = tk.LabelFrame(
            body, text=_t("grp_settings"),
            bg=XP_FACE, fg=XP_TEXT,
            font=XP_FONT,
            bd=2, relief=tk.GROOVE,
        )
        grp_outer.pack(fill=tk.X, pady=(4, 6))

        self.remember_var    = tk.BooleanVar(value=bool(cfg.get("remember_token", True)))
        self.auto_login_var  = tk.BooleanVar(value=bool(cfg.get("auto_login", False)))
        self.start_win_var   = tk.BooleanVar(value=bool(cfg.get("start_with_windows", False)))

        xp_checkbox(grp_outer, _t("chk_remember"),
                    self.remember_var).pack(anchor=tk.W, padx=8, pady=(4, 1))
        xp_checkbox(grp_outer, _t("chk_autologin"),
                    self.auto_login_var).pack(anchor=tk.W, padx=8, pady=1)
        xp_checkbox(grp_outer, _t("chk_startup"),
                    self.start_win_var).pack(anchor=tk.W, padx=8, pady=(1, 6))

        grp_client = tk.LabelFrame(
            body, text=_t("grp_client"),
            bg=XP_FACE, fg=XP_TEXT,
            font=XP_FONT,
            bd=2, relief=tk.GROOVE,
        )
        grp_client.pack(fill=tk.X, pady=(0, 6))

        self.client_var = tk.StringVar(value=cfg.get("client_app", "discord"))

        tk.Radiobutton(
            grp_client, text=_t("radio_discord"),
            variable=self.client_var, value="discord",
            bg=XP_FACE, fg=XP_TEXT,
            selectcolor=XP_WHITE,
            activebackground=XP_FACE, activeforeground=XP_TEXT,
            font=XP_FONT,
            command=self._on_client_change,
        ).pack(anchor=tk.W, padx=8, pady=(4, 1))

        tk.Radiobutton(
            grp_client, text=_t("radio_canary"),
            variable=self.client_var, value="canary",
            bg=XP_FACE, fg=XP_TEXT,
            selectcolor=XP_WHITE,
            activebackground=XP_FACE, activeforeground=XP_TEXT,
            font=XP_FONT,
            command=self._on_client_change,
        ).pack(anchor=tk.W, padx=8, pady=(1, 1))

        tk.Radiobutton(
            grp_client, text=_t("radio_dm"),
            variable=self.client_var, value="dm",
            bg=XP_FACE, fg=XP_TEXT,
            selectcolor=XP_WHITE,
            activebackground=XP_FACE, activeforeground=XP_TEXT,
            font=XP_FONT,
            command=self._on_client_change,
        ).pack(anchor=tk.W, padx=8, pady=(1, 2))

        self._dm_path_frame = tk.Frame(grp_client, bg=XP_FACE)
        xp_label(self._dm_path_frame, _t("lbl_dm_path")).pack(anchor=tk.W)
        path_row = tk.Frame(self._dm_path_frame, bg=XP_FACE)
        path_row.pack(fill=tk.X)
        self.dm_path_var = tk.StringVar(value=cfg.get("dm_exe_path", ""))
        dm_entry_frame = tk.Frame(path_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        dm_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Entry(
            dm_entry_frame,
            textvariable=self.dm_path_var,
            bg=XP_WHITE, fg=XP_TEXT,
            insertbackground=XP_TEXT,
            relief=tk.FLAT,
            font=XP_FONT,
        ).pack(fill=tk.X, ipady=3, padx=1, pady=1)
        xp_button(path_row, _t("btn_browse"), self._browse_dm_exe, width=8).pack(side=tk.LEFT, padx=(4, 0))
        self._on_client_change() 

        self.status_var = tk.StringVar()
        tk.Label(body, textvariable=self.status_var,
                 bg=XP_FACE, fg="#CC0000",
                 font=("Tahoma", 8)).pack(anchor=tk.W, pady=(2, 0))
        xp_separator(self.win).pack(fill=tk.X)
        btn_row = tk.Frame(self.win, bg=XP_FACE)
        btn_row.pack(fill=tk.X, padx=8, pady=6)

        xp_button(btn_row, _t("btn_connect"), self._login, width=12).pack(side=tk.RIGHT, padx=(4, 2))
        xp_button(btn_row, _t("btn_cancel"), lambda: os._exit(0), width=10).pack(side=tk.RIGHT, padx=2)

        self.entry.bind("<Return>", lambda _: self._login())
        self.entry.focus_set()

    def _on_client_change(self) -> None:
        if self.client_var.get() == "dm":
            self._dm_path_frame.pack(fill=tk.X, padx=8, pady=(0, 6))
        else:
            self._dm_path_frame.pack_forget()

    def _browse_dm_exe(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select DiscordMessenger.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self.dm_path_var.set(path)

    def _toggle_show(self) -> None:
        self.entry.config(show="" if self.show_var.get() else "*")

    def _login(self) -> None:
        token = self.token_var.get().strip()
        if not token:
            self.status_var.set(_t("err_no_token"))
            return

        cfg = load_config()

        if self.remember_var.get():
            cfg["token"] = token
        else:
            cfg.pop("token", None)

        cfg["remember_token"]      = self.remember_var.get()
        cfg["auto_login"]          = self.auto_login_var.get()
        cfg["start_with_windows"]  = self.start_win_var.get()
        cfg["client_app"]          = self.client_var.get()
        cfg["dm_exe_path"]         = self.dm_path_var.get().strip()
        save_config(cfg)

        self._apply_startup(self.start_win_var.get())

        self.win.destroy()
        self.on_login(token)

    def _apply_startup(self, enable: bool) -> None:

        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "DiscordBalloonNotifier"
            if getattr(sys, "frozen", False):
                launch_cmd = f'"{sys.executable}"'
            else:
                exe_path = os.path.abspath(sys.argv[0])
                launch_cmd = f'"{sys.executable}" "{exe_path}"'

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, launch_cmd)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        pass
        except Exception:
            pass

def _launch_updater_download(version: str, url: str) -> None:

    base       = _get_base_dir()
    candidates = [
        os.path.join(base, "BalloncordUpdater.exe"),
        os.path.join(base, "updater.exe"),
    ]
    for exe in candidates:
        if os.path.isfile(exe):
            try:
                subprocess.Popen(
                    [exe, "--download", version, url],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    close_fds=True,
                )
                print(f"[updater] Launched {os.path.basename(exe)} --download {version} — exiting")
            except Exception as e:
                print(f"[updater] Failed to launch updater for download: {e}")
                return
            time.sleep(0.5)
            os._exit(0)

    py_path = os.path.join(base, "updater.py")
    if os.path.isfile(py_path):
        try:
            subprocess.Popen(
                [sys.executable, py_path, "--download", version, url],
                creationflags=subprocess.CREATE_NO_WINDOW,
                close_fds=True,
            )
            print(f"[updater] Launched updater.py --download {version} (dev mode) — exiting")
        except Exception as e:
            print(f"[updater] Failed to launch updater.py: {e}")
            return
        time.sleep(0.5)
        os._exit(0)

def _launch_updater() -> None:

    cfg = load_config()
    if not cfg.get("check_for_updates", True):
        print("[updater] Check for updates is disabled. Skipping.")
        return

    base       = _get_base_dir()
    candidates = [
        os.path.join(base, "BalloncordUpdater.exe"),
        os.path.join(base, "updater.exe"),
    ]
    for exe in candidates:
        if os.path.isfile(exe):
            try:
                subprocess.Popen(
                    [exe],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    close_fds=True,
                )
                print(f"[updater] Launched {os.path.basename(exe)}")
            except Exception as e:
                print(f"[updater] Failed to launch updater: {e}")
            return
                                                            
    py_path = os.path.join(base, "updater.py")
    if os.path.isfile(py_path):
        try:
            subprocess.Popen(
                [sys.executable, py_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                close_fds=True,
            )
            print("[updater] Launched updater.py (dev mode)")
        except Exception as e:
            print(f"[updater] Failed to launch updater.py: {e}")

def _poll_update_flag() -> None:

    import time
    time.sleep(6)                                                     

    flag_path = os.path.join(_get_base_dir(), "_balloncord_update.json")
    try:
        with open(flag_path, encoding="utf-8") as f:
            info = json.load(f)
        os.remove(flag_path)
    except FileNotFoundError:
        return                      
    except Exception as e:
        print(f"[updater] Could not read flag file: {e}")
        return

    global _pending_update_info

    ver          = info.get("version", "?")
    ready        = info.get("ready", False)
    download_url = info.get("download_url", "")

    if ready:
                                                                     
        _raw_show_balloon(
            "Balloncord \u2014 Update ready",
            f"v{ver} downloaded. Restart Balloncord to apply.",
            None,
        )
        print(f"[updater] Showed 'restart to apply' balloon for v{ver}")
    else:
                                                                                     
        _pending_update_info = {"version": ver, "download_url": download_url}
        _raw_show_balloon(
            "Balloncord \u2014 Update available",
            f"A new version (v{ver}) is available. Click to download now.",
            None,                                                              
        )
        print(f"[updater] Showed 'update available' balloon for v{ver}")

def _ensure_version_file() -> None:

    path = os.path.join(_get_base_dir(), "version.txt")
    try:
        existing = open(path, encoding="utf-8").read().strip().lstrip("v")
    except Exception:
        existing = ""
    if existing != VERSION:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(VERSION)
            print(f"[app] version.txt written: {VERSION}")
        except Exception as e:
            print(f"[app] Could not write version.txt: {e}")

def main() -> None:
    global _tk_root, _log_win
    _ensure_version_file()                                                         
    _register_sound_event()
    _launch_updater()                                           
    root = tk.Tk()
    root.withdraw()
    _tk_root = root
    _log_win = LogWindow(root)
    tray_thread = threading.Thread(target=_message_loop, daemon=True)
    tray_thread.start()
    _tray_ready.wait()

                                                                
    threading.Thread(target=_poll_update_flag, daemon=True).start()

    def on_login(token: str) -> None:
        print("[app] Starting gateway...")

        def run_async():
            asyncio.run(run_gateway(token))

        threading.Thread(target=run_async, daemon=True).start()

    LoginWindow(root, on_login)

    root.mainloop()

if __name__ == "__main__":
    main()
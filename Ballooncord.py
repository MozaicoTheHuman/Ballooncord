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

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageChops
    _PIL_OK = True
except Exception:
    _PIL_OK = False
import tkinter as tk
from tkinter import ttk
from datetime import datetime

import unicodedata as _unicodedata

_EMOJI_MAP: dict[str, str] = {
    "\u00B7": ".",
    "\u0387": ".",
    "\u2027": ".",
    "\u2024": ".",
    "\U0001F600": "☺",
    "\U0001F601": "☺",
    "\U0001F602": "☺",
    "\U0001F603": "☺",
    "\U0001F604": "☺",
    "\U0001F605": "☺",
    "\U0001F606": "☺",
    "\U0001F607": "☺",
    "\U0001F608": "☺",
    "\U0001F609": "☺",
    "\U0001F60A": "☺",
    "\U0001F60B": "☺",
    "\U0001F60C": "☺",
    "\U0001F60D": "☺",
    "\U0001F60E": "☺",
    "\U0001F60F": "☺",
    "\U0001F610": "😐",
    "\U0001F611": "😐",
    "\U0001F614": "☹",
    "\U0001F615": "☹",
    "\U0001F61E": "☹",
    "\U0001F61F": "☹",
    "\U0001F620": "☹",
    "\U0001F621": "☹",
    "\U0001F622": "☹",
    "\U0001F623": "☹",
    "\U0001F624": "☹",
    "\U0001F625": "☹",
    "\U0001F626": "☹",
    "\U0001F627": "☹",
    "\U0001F628": "☹",
    "\U0001F629": "☹",
    "\U0001F62A": "☹",
    "\U0001F62B": "☹",
    "\U0001F62D": "☹",
    "\U0001F62E": "☹",
    "\U0001F62F": "☹",
    "\U0001F630": "☹",
    "\U0001F631": "☹",
    "\U0001F632": "☹",
    "\U0001F633": "☺",
    "\U0001F635": "☹",
    "\U0001F637": "☺",
    "\U0001F641": "☹",
    "\U0001F642": "☺",
    "\U0001F644": "☹",
    "\U0001F910": "☺",
    "\U0001F912": "☹",
    "\U0001F913": "☺",
    "\U0001F914": "☺",
    "\U0001F915": "☹",
    "\U0001F917": "☺",
    "\U0001F920": "☺",
    "\U0001F922": "☹",
    "\U0001F923": "☺",
    "\U0001F924": "☺",
    "\U0001F925": "☺",
    "\U0001F927": "☹",
    "\U0001F928": "☺",
    "\U0001F929": "☺",
    "\U0001F92A": "☺",
    "\U0001F92C": "☹",
    "\U0001F92D": "☺",
    "\U0001F92E": "☹",
    "\U0001F92F": "☺",
    "\U0001F970": "☺",
    "\U0001F971": "☺",
    "\U0001F972": "☹",
    "\U0001F973": "☺",
    "\U0001F974": "☹",
    "\U0001F975": "☹",
    "\U0001F976": "☹",
    "\U0001F97A": "☹",
    "\u263A": "☺",
    "\u263B": "☻",
    "\u2639": "☹",
    "\u2764": "♥",
    "\U0001F493": "♥",
    "\U0001F494": "♥",
    "\U0001F495": "♥",
    "\U0001F496": "♥",
    "\U0001F497": "♥",
    "\U0001F498": "♥",
    "\U0001F499": "♥",
    "\U0001F49A": "♥",
    "\U0001F49B": "♥",
    "\U0001F49C": "♥",
    "\U0001F49D": "♥",
    "\U0001F49E": "♥",
    "\U0001F49F": "♥",
    "\U0001F5A4": "♥",
    "\U0001F90D": "♥",
    "\U0001F90E": "♥",
    "\u2B50": "★",
    "\U0001F31F": "★",
    "\U0001F4AB": "✦",
    "\u2728": "✦",
    "\u2733": "✦",
    "\u2734": "✦",
    "\u2605": "★",
    "\u2606": "☆",
    "\u2600": "☀",
    "\U0001F31E": "☀",
    "\u2601": "☁",
    "\u26C5": "⛅",
    "\U0001F327": "☁",
    "\U0001F328": "☁",
    "\U0001F329": "⚡",
    "\U0001F32A": "☁",
    "\u26A1": "⚡",
    "\u2744": "❄",
    "\u26C4": "⛄",
    "\U0001F31B": "☽",
    "\U0001F31C": "☾",
    "\U0001F31D": "○",
    "\U0001F31A": "○",
    "\U0001F319": "☽",
    "\U0001F308": "☼",
    "\U0001F3B5": "♪",
    "\U0001F3B6": "♫",
    "\U0001F3B7": "♪",
    "\U0001F3B8": "♪",
    "\U0001F3B9": "♪",
    "\U0001F3BA": "♪",
    "\U0001F3BB": "♪",
    "\U0001F3BC": "♬",
    "\u266A": "♪",
    "\u266B": "♫",
    "\u266C": "♬",
    "\u266D": "♭",
    "\u266E": "♮",
    "\u266F": "♯",
    "\u2660": "♠",
    "\u2661": "♡",
    "\u2662": "♢",
    "\u2663": "♣",
    "\u2664": "♠",
    "\u2665": "♥",
    "\u2666": "♦",
    "\u2667": "♣",
    "\u265A": "♚",
    "\u265B": "♛",
    "\u265C": "♜",
    "\u265D": "♝",
    "\u265E": "♞",
    "\u265F": "♟",
    "\u2654": "♔",
    "\u2655": "♕",
    "\u2656": "♖",
    "\u2657": "♗",
    "\u2658": "♘",
    "\u2659": "♙",
    "\U0001F451": "♛",
    "\U0001F48E": "◆",
    "\U0001F3C6": "★",
    "\u2705": "✓",
    "\u2714": "✔",
    "\u2713": "✓",
    "\u274C": "✗",
    "\u274E": "✗",
    "\u2716": "✖",
    "\u2717": "✗",
    "\u2718": "✘",
    "\u2611": "☑",
    "\u2610": "☐",
    "\u2612": "☒",
    "\u26A0": "⚠",
    "\u2139": "ℹ",
    "\u2753": "?",
    "\u2754": "?",
    "\u2755": "!",
    "\u2757": "!",
    "\u203C": "‼",
    "\u2049": "⁉",
    "\u2B55": "○",
    "\u26AB": "●",
    "\u26AA": "○",
    "\U0001F534": "●",
    "\U0001F535": "●",
    "\U0001F7E2": "●",
    "\U0001F7E1": "●",
    "\U0001F7E0": "●",
    "\U0001F7E3": "●",
    "\U0001F7E4": "●",
    "\u25CF": "●",
    "\u25CB": "○",
    "\u25AA": "▪",
    "\u25AB": "▫",
    "\u2B06": "↑",
    "\u2B07": "↓",
    "\u2B05": "←",
    "\u27A1": "→",
    "\u2194": "↔",
    "\u2195": "↕",
    "\u2196": "↖",
    "\u2197": "↗",
    "\u2198": "↘",
    "\u2199": "↙",
    "\u21A9": "↩",
    "\u21AA": "↪",
    "\u21BA": "↺",
    "\u21BB": "↻",
    "\U0001F501": "↺",
    "\U0001F502": "↺",
    "\U0001F503": "↻",
    "\U0001F504": "↻",
    "\u25B6": "▶",
    "\u25C0": "◀",
    "\u25B2": "▲",
    "\u25BC": "▼",
    "\u23E9": "»",
    "\u23EA": "«",
    "\u23EB": "↑",
    "\u23EC": "↓",
    "\u23F8": "‖",
    "\u23F9": "■",
    "\u23FA": "●",
    "\u260E": "☎",
    "\U0001F4DE": "☎",
    "\U0001F4DF": "☎",
    "\u2709": "✉",
    "\U0001F4E7": "✉",
    "\U0001F4E8": "✉",
    "\U0001F4E9": "✉",
    "\U0001F4EA": "✉",
    "\U0001F4EB": "✉",
    "\U0001F4EC": "✉",
    "\U0001F4ED": "✉",
    "\u270F": "✎",
    "\u270E": "✎",
    "\u2711": "✑",
    "\u2712": "✒",
    "\u2702": "✂",
    "\U0001F4DD": "✎",
    "\U0001F4CE": "📎",
    "\U0001F4CC": "📌",
    "\u2620": "☠",
    "\U0001F480": "☠",
    "\u2622": "☢",
    "\u2623": "☣",
    "\u262E": "☮",
    "\u262F": "☯",
    "\u2695": "⚕",
    "\u2694": "⚔",
    "\u267B": "♻",
    "\u267E": "∞",
    "\U0001F4B2": "$",
    "\U0001F4B0": "$",
    "\U0001F4B1": "$",
    "\U0001F4B3": "$",
    "\U0001F4B4": "$",
    "\U0001F4B5": "$",
    "\U0001F4B6": "$",
    "\U0001F4B7": "$",
    "\U0001F4B8": "$",
    "\U0001F4B9": "$",
    "\u2030": "‰",
    "\U0001F4AF": "%",
    "\u2122": "™",
    "\u00AE": "®",
    "\u00A9": "©",
    "\U0001F514": "🔔",
    "\U0001F515": "🔕",
    "\u2020": "†",
    "\u2021": "‡",
    "\u271D": "✝",
    "\u2605": "★",
    "\u2606": "☆",
    "\u25C6": "◆",
    "\u25C7": "◇",
    "\u25B3": "△",
    "\u25BD": "▽",
    "\U0001F4A5": "※",
    "\U0001F4A4": "…",
    "\U0001F6AB": "⊘",
    "\u26D4": "⊘",
    "\u2205": "∅",
    "\u2298": "⊘",
    "\u2648": "♈",  "\u2649": "♉",  "\u264A": "♊",  "\u264B": "♋",
    "\u264C": "♌",  "\u264D": "♍",  "\u264E": "♎",  "\u264F": "♏",
    "\u2650": "♐",  "\u2651": "♑",  "\u2652": "♒",  "\u2653": "♓",
}

_EMOJI_DROP: frozenset[int] = frozenset([
    0xFE0F,
    0xFE0E,
    0x200D,
    0x20E3,
    0x200B,
    0x200C,
    0xFEFF,
])

def _replace_emojis(text: str) -> str:
    if not text:
        return text
    text = _unicodedata.normalize("NFKC", text)
    result: list[str] = []
    for ch in text:
        cp = ord(ch)

        if cp in _EMOJI_DROP:
            continue

        mapped = _EMOJI_MAP.get(ch)
        if mapped is not None:
            result.append(mapped)
            continue

        is_emoji = (
            0x1F300 <= cp <= 0x1FAFF
            or 0x1F1E0 <= cp <= 0x1F1FF
            or (0x2600 <= cp <= 0x27BF and
                _unicodedata.category(ch) == "So")
        )
        if is_emoji:
            continue

        result.append(ch)

    return "".join(result)

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
WM_DEVICECHANGE = 0x0219

WM_TASKBARCREATED: int = 0

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

                                                                           
VERSION = "1.2.0"

DND_STATUSES   = {"dnd"}

_my_status: str = "online" 
_token:     str = ""   
_gw_ws    = None   
_gw_loop: asyncio.AbstractEventLoop | None = None

_vc_guild_id:   str | None = None
_vc_channel_id: str | None = None
_vc_self_mute:   bool = False
_vc_self_deaf:   bool = False
_vc_self_stream: bool = False
_vc_self_video:  bool = False

_active_call_channel_id: str | None = None
_outgoing_call_channel_id: str | None = None  
_outgoing_call_time: float = 0.0     

_has_unread: bool = False

_unread_channels: set[str] = set()
_unread_channel_info: dict[str, dict] = {}
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
_balloon_sent:        bool      = False
_balloon_pending_sound: bool    = False 
_balloon_pending_key:   str     = "NewMessage"

_balloon_refcount:    int       = 0
_balloon_dismiss_timer: "threading.Timer | None" = None
_last_balloon_channel_id: "str | None" = None

_pending_update_info: "dict | None" = None

YAHOO_TOAST_W: int = 280
YAHOO_TOAST_H: int = 72
YAHOO_MAX_STACK: int = 4
YAHOO_GAP: int = 0
_yahoo_toasts: list = []
_yahoo_lock: threading.Lock = threading.Lock()
                                                

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
    ("StartStream",    "Start Streaming"),
    ("StopStream",     "Stop Streaming"),
    ("VideoOn",        "Video On"),
    ("VideoOff",       "Video Off"),
    ("FriendRequest",  "Friend Request"),
    ("FriendAccepted", "Friend Accepted"),
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
    "StartStream":    "vc_toggle",
    "StopStream":     "vc_toggle",
    "VideoOn":        "vc_toggle",
    "VideoOff":       "vc_toggle",
    "FriendRequest":  "message",
    "FriendAccepted": "message",
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

_audio_reinit_lock = threading.Lock()

def _reinit_audio_device() -> None:
    global _pygame_ok
    if not _pygame_ok or _mixer is None:
        return
    if not _audio_reinit_lock.acquire(blocking=False):
        return
    try:
        time.sleep(1.0)
        try:
            _mixer.stop()
        except Exception:
            pass
        try:
            _mixer.quit()
        except Exception:
            pass
        try:
            _mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            _clear_sound_cache()
            _pygame_ok = True
            print("[sound] Audio device changed — mixer reinitialized OK")
        except Exception as e:
            _pygame_ok = False
            print(f"[sound] Mixer reinit failed after device change: {e}")
    finally:
        _audio_reinit_lock.release()

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
    "chk_check_updates_desc":  "Check GitHub for a new version when Ballooncord starts.",
    "chk_auto_update":         "Auto-update Ballooncord",
    "chk_auto_update_desc":    "Automatically download and install new versions on startup (requires Check for updates).",
    "balloon_update_title":    "Ballooncord \u2014 Update available",
    "balloon_update_body":     "A new version ({ver}) is available. Click to download now.",
    "balloon_updated_title":   "Ballooncord \u2014 Update ready",
    "balloon_updated_body":    "v{ver} downloaded. Restart Ballooncord to apply.",

                 
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

    if state == "normal" and cfg.get("tray_status_icons_enabled", False):
        status_map = {"online": "online", "dnd": "dnd", "idle": "idle",
                      "invisible": "invisible"}
        status_key = status_map.get(_my_status, "")
        if status_key:
            status_path = cfg.get("status_icons", {}).get(status_key, "")
            if status_path and os.path.isfile(status_path):
                cached = _state_icon_cache.get(status_path, 0)
                if cached:
                    return cached
                hicon = _file_to_hicon(status_path, size=16)
                if hicon:
                    _state_icon_cache[status_path] = hicon
                    return hicon

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

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def _compose_titlebar_tex(width: int, left_path: str, mid_path: str, right_path: str):
    if not _PIL_OK:
        return None
    try:
        from PIL import Image, ImageTk
        left = Image.open(left_path).convert("RGBA")
        mid = Image.open(mid_path).convert("RGBA")
        right = Image.open(right_path).convert("RGBA")
        h = left.height
        chroma = _hex_to_rgb(load_config().get("toast_chroma_key", "#FF00FF"))
        r, g, b = chroma
        result = Image.new("RGBA", (width, h), (r, g, b, 255))
        lw = left.width
        rw = right.width
        mw = width - lw - rw
        result.paste(left, (0, 0), left)
        if mw > 0:
            _resample = getattr(Image, "Resampling", Image).NEAREST
            mid_stretched = mid.resize((mw, h), _resample)
            result.paste(mid_stretched, (lw, 0), mid_stretched)
        result.paste(right, (width - rw, 0), right)
        return ImageTk.PhotoImage(result)
    except Exception as e:
        print(f"[toast] Failed to compose titlebar texture: {e}")
        return None

def _load_tex_photoimage(path: str):
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).convert("RGBA")
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[toast] Failed to load texture {path}: {e}")
        return None

def _get_user_titlebar_tex(user_id: str) -> dict:
    if not user_id:
        return {}
    cfg = load_config()
    per_user = cfg.get("per_user_sounds", {})
    user_cfg = per_user.get(user_id, {})
    result = {}
    for key in ("titlebar_left", "titlebar_mid", "titlebar_right", "close_btn"):
        path = user_cfg.get(key, "").strip()
        if path and os.path.isfile(path):
            result[key] = path
    return result

def _get_active_titlebar_tex(author_id: str) -> dict:
    tex = _get_user_titlebar_tex(author_id)
    if tex:
        mapping = {
            "titlebar_left": "toast_titlebar_left",
            "titlebar_mid": "toast_titlebar_mid",
            "titlebar_right": "toast_titlebar_right",
            "close_btn": "toast_close_btn",
        }
        return {mapping[k]: v for k, v in tex.items()}
    cfg = load_config()
    result = {}
    for key in ("toast_titlebar_left", "toast_titlebar_mid", "toast_titlebar_right", "toast_close_btn"):
        path = cfg.get(key, "").strip()
        if path and os.path.isfile(path):
            result[key] = path
    return result
class YahooToast:

    def __init__(self, title: str, body: str, url: "str | None",
                 avatar_path: "str | None" = None,
                 sound_key: str = "NewMessage",
                 channel_id: "str | None" = None,
                 author_name: str = "",
                 guild_name: str = "",
                 channel_name: str = "",
                 titlebar_start: "str | None" = None,
                 titlebar_end: "str | None" = None,
                 author_id: str = "",
                 compact_mode: bool = False,
                 compact_icons: "dict | None" = None) -> None:
        self.title = title
        self.body = body
        self.url = url
        self.avatar_path = avatar_path
        self.sound_key = sound_key
        self.channel_id = channel_id
        self.author_name = author_name
        self.guild_name = guild_name
        self.channel_name = channel_name
        self.titlebar_start = titlebar_start
        self.titlebar_end = titlebar_end
        self.author_id = author_id
        self.compact_mode = compact_mode
        self.compact_icons = compact_icons or {}
        self.toast_w = YAHOO_TOAST_W
        self.toast_h = 52 if compact_mode else YAHOO_TOAST_H
        self.win: tk.Toplevel | None = None
        self._timer: threading.Timer | None = None
        self._after_ids: list = []
        self._closed = False
        self._final_x = 0
        self._final_y = 0

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        h = hex_color.lstrip("#")
        if len(h) == 3:
            h = "".join([c*2 for c in h])
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _on_click(self, event=None) -> None:
        try:
            if self._closed:
                return
            self.close(animate=False)
            if self.channel_id:
                with _yahoo_lock:
                    same_channel = [t for t in _yahoo_toasts if t.channel_id == self.channel_id]
                for t in same_channel:
                    t.close(animate=False)
            url = self.url
            if url and isinstance(url, str) and url.strip():
                _open_client(url)
            else:
                _open_client()
        except Exception as e:
            print(f"[toast] Click handler error: {e}")

    def close(self, animate: bool = True) -> None:
        if self._closed:
            return
        self._closed = True
        if self._timer:
            self._timer.cancel()
        for aid in self._after_ids:
            try:
                self.win.after_cancel(aid)
            except Exception:
                pass
        if animate and self.win:
            start_y = self.win.winfo_y()
            end_y = self.win.winfo_screenheight()
            def step(i=0):
                if not self.win:
                    _remove_yahoo_toast(self)
                    return
                if i >= 8:
                    try:
                        self.win.destroy()
                    except Exception:
                        pass
                    _remove_yahoo_toast(self)
                    return
                y = start_y + int((end_y - start_y) * (i / 8))
                try:
                    self.win.geometry(f"{self.toast_w}x{self.toast_h}+{self._final_x}+{y}")
                except Exception:
                    pass
                self.win.after(10, lambda: step(i + 1))
            step()
        else:
            if self.win:
                try:
                    self.win.destroy()
                except Exception:
                    pass
            _remove_yahoo_toast(self)

    def build(self, index: int) -> None:
        self.win = tk.Toplevel(_tk_root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#808080")
        self.win.resizable(False, False)

        outer = tk.Frame(self.win, bg="#808080", bd=0)
        outer.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(outer, height=28, bd=0, highlightthickness=0, bg="#808080")
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)

        title_canvas = tk.Canvas(title_bar, highlightthickness=0, bd=0, height=28, bg="#808080")
        title_canvas.pack(fill=tk.BOTH, expand=True)

        tex_cfg = _get_active_titlebar_tex(getattr(self, 'author_id', ''))
        tex_photo = None
        use_tex = False
        r1 = g1 = b1 = r2 = g2 = b2 = 0

        left_path = tex_cfg.get("toast_titlebar_left")
        mid_path = tex_cfg.get("toast_titlebar_mid")
        right_path = tex_cfg.get("toast_titlebar_right")

        if left_path and mid_path and right_path and _PIL_OK:
            tex_photo = _compose_titlebar_tex(YAHOO_TOAST_W, left_path, mid_path, right_path)
            if tex_photo:
                chroma = load_config().get("toast_chroma_key", "#FF00FF")
                title_bar.configure(bg=chroma)
                title_canvas.configure(bg=chroma)
                title_canvas.create_image(0, 0, image=tex_photo, anchor=tk.NW)
                title_canvas._titlebar_photo = tex_photo
                use_tex = True

        if not use_tex:
            cfg = load_config()
            if self.titlebar_start and self.titlebar_end:
                start_hex = self.titlebar_start
                end_hex = self.titlebar_end
            else:
                start_hex = cfg.get("toast_gradient_start", "#0058CE")
                end_hex = cfg.get("toast_gradient_end", "#2B93FF")
            r1, g1, b1 = self._hex_to_rgb(start_hex)
            r2, g2, b2 = self._hex_to_rgb(end_hex)
            for y in range(28):
                t = y / 27 if 27 else 0
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
                color = f"#{r:02x}{g:02x}{b:02x}"
                title_canvas.create_line(0, y, YAHOO_TOAST_W, y, fill=color, width=1)

        if self.guild_name:
            title_text = f"{self.guild_name}, #{self.channel_name}" if self.channel_name else self.guild_name
        else:
            title_text = load_config().get("toast_default_title", "Discord") or "Discord"
        title_text = _replace_emojis(title_text)[:35]

        title_id = title_canvas.create_text(6, 14, text=title_text,
                                            anchor=tk.W, fill="white",
                                            font=("Tahoma", 8, "bold"))
        title_canvas.tag_bind(title_id, "<Button-1>", self._on_click)

        close_path = tex_cfg.get("toast_close_btn")
        if close_path and os.path.isfile(close_path):
            close_photo = _load_tex_photoimage(close_path)
            if close_photo:
                chroma = load_config().get("toast_chroma_key", "#FF00FF")
                close_lbl = tk.Label(
                    title_bar,
                    image=close_photo,
                    bg=chroma if use_tex else "#808080",
                    bd=0,
                    highlightthickness=0,
                    cursor="hand2",
                )
                close_lbl.image = close_photo
                close_lbl.place(x=YAHOO_TOAST_W - 24, y=4, width=19, height=19)
                close_lbl.bind("<Button-1>", lambda _e: self.close())
        elif not use_tex:

            t_btn = 7 / 27
            r_btn = int(r1 + (r2 - r1) * t_btn)
            g_btn = int(g1 + (g2 - g1) * t_btn)
            b_btn = int(b1 + (b2 - b1) * t_btn)
            btn_bg = f"#{r_btn:02x}{g_btn:02x}{b_btn:02x}"
            close_btn = tk.Button(
                title_bar,
                text="×",
                command=lambda: self.close(),
                bg=btn_bg,
                fg="#222222",
                activebackground=btn_bg,
                activeforeground="#000000",
                font=("Tahoma", 9, "bold"),
                relief=tk.RAISED,
                bd=1,
                highlightthickness=0,
                padx=0,
                pady=0,
                cursor="hand2",
            )
            close_btn.place(x=YAHOO_TOAST_W - 22, y=5, width=18, height=15)
            close_btn.lift()
        else:
            close_id = title_canvas.create_text(
                YAHOO_TOAST_W - 12, 14, text="×",
                anchor=tk.CENTER, fill="white",
                font=("Tahoma", 9, "bold")
            )
            title_canvas.tag_bind(close_id, "<Button-1>",
                                  lambda _e: self.close())

        _border_col = (
            _get_user_body_border(getattr(self, "author_id", ""))
            or load_config().get("toast_body_border_color", "#808080")
        )
        body_border = tk.Frame(outer, bg=_border_col, bd=0)
        body_border.pack(fill=tk.BOTH, expand=True)

        body_frm = tk.Frame(body_border, bg="#E8E4E0")
        body_frm.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        if self.compact_mode:
            _ck_map = {
                "NewMessage":    "message",
                "NewMention":    "mention",
                "FriendRequest": "friend_request",
                "FriendAccepted":"friend_request",
                "IncomingCall":  "call",
            }
            _ck = _ck_map.get(self.sound_key, "message")
            _ci_path = self.compact_icons.get(_ck, "")
            _ci_img = None
            if _ci_path and os.path.isfile(_ci_path):
                if _PIL_OK:
                    try:
                        _pil_img = Image.open(_ci_path).convert("RGBA").resize((16, 16), Image.LANCZOS)
                        _ci_img = ImageTk.PhotoImage(_pil_img)
                    except Exception as _e:
                        print(f"[compact] Failed to load icon '{_ci_path}': {_e}")
                        _ci_img = None
                else:
                    try:
                        _raw = tk.PhotoImage(file=_ci_path)
                        if _raw.width() > 16:
                            _raw = _raw.subsample(max(1, _raw.width() // 16))
                        _ci_img = _raw
                    except Exception:
                        _ci_img = None
            _fallback_syms = {"message": "✉", "mention": "@", "friend_request": "♟", "call": "☎"}
            if _ci_img:
                body_icon = tk.Label(body_frm, image=_ci_img, bg="#E8E4E0")
                body_icon.image = _ci_img
            else:
                body_icon = tk.Label(body_frm, text=_fallback_syms.get(_ck, "✉"),
                                     bg="#E8E4E0", fg="#5A3E8C", font=("Tahoma", 10))
            body_icon.pack(side=tk.LEFT, padx=(5, 3), pady=2)
            body_icon.bind("<Button-1>", self._on_click)

            if self.author_name:
                _pfx  = _replace_emojis(f"{self.author_name}: ")
                _body = _replace_emojis(self.body)
                msg_text = _truncate_toast_msg(_body, wrap_px=230, max_lines=2, prefix=_pfx)
            else:
                msg_text = _truncate_toast_msg(_replace_emojis(self.body), wrap_px=230, max_lines=2)

            msg_lbl = tk.Label(body_frm, text=msg_text, bg="#E8E4E0", fg="black",
                     font=("Tahoma", 8), justify=tk.LEFT, anchor=tk.NW,
                     wraplength=230)
            msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4), pady=2)
            msg_lbl.bind("<Button-1>", self._on_click)
        else:
            img32 = None
            if self.avatar_path and os.path.exists(self.avatar_path):
                try:
                    img = tk.PhotoImage(file=self.avatar_path)
                    factor = max(1, img.width() // 32)
                    img32 = img.subsample(factor, factor)
                except Exception:
                    pass
            if not img32:
                custom_icon = load_config().get("tray_icons", {}).get("normal", "")
                if custom_icon and os.path.isfile(custom_icon):
                    try:
                        if PIL_OK:
                            _ci_raw = Image.open(custom_icon)
                            if hasattr(_ci_raw, "n_frames") and _ci_raw.n_frames > 1:
                                best_idx, best_diff = 0, float("inf")
                                for _fi in range(_ci_raw.n_frames):
                                    _ci_raw.seek(_fi)
                                    _fw, _fh = _ci_raw.size
                                    diff = abs(_fw - 32) + abs(_fh - 32)
                                    if diff < best_diff:
                                        best_diff, best_idx = diff, _fi
                                _ci_raw.seek(best_idx)
                            _ci = _ci_raw.convert("RGBA").resize((32, 32), Image.LANCZOS)
                            img32 = ImageTk.PhotoImage(_ci)
                        else:
                            img = tk.PhotoImage(file=custom_icon)
                            factor = max(1, img.width() // 32)
                            img32 = img.subsample(factor, factor)
                    except Exception:
                        pass
            if img32:
                body_icon = tk.Label(body_frm, image=img32, bg="#E8E4E0")
                body_icon.image = img32
                body_icon.pack(side=tk.LEFT, padx=6, pady=4)
                body_icon.bind("<Button-1>", self._on_click)
            else:
                body_icon = tk.Label(body_frm, text="☺", bg="#E8E4E0", fg="#5A3E8C",
                         font=("Tahoma", 20))
                body_icon.pack(side=tk.LEFT, padx=6, pady=4)
                body_icon.bind("<Button-1>", self._on_click)

            if self.author_name:
                _pfx  = _replace_emojis(f"{self.author_name}: ")
                _body = _replace_emojis(self.body)
                msg_text = _truncate_toast_msg(_body, wrap_px=210, max_lines=2, prefix=_pfx)
            else:
                msg_text = _truncate_toast_msg(_replace_emojis(self.body))
            msg_lbl = tk.Label(body_frm, text=msg_text, bg="#E8E4E0", fg="black",
                     font=("Tahoma", 8), justify=tk.LEFT, anchor=tk.NW,
                     wraplength=210)
            msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6), pady=4)
            msg_lbl.bind("<Button-1>", self._on_click)

        for widget in (outer, body_frm):
            widget.bind("<Button-1>", self._on_click)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        _y_offset = int(load_config().get("toast_y_offset", 0))
        self._final_x = sw - self.toast_w - 4
        self._final_y = sh - self.toast_h - 4 - (index * (self.toast_h + YAHOO_GAP)) - _y_offset
        start_y = sh

        self.win.geometry(f"{self.toast_w}x{self.toast_h}+{self._final_x}+{start_y}")
        self.win.update_idletasks()

        if use_tex:
            chroma = load_config().get("toast_chroma_key", "#FF00FF")
            self.win.attributes('-transparentcolor', chroma)

        _anim_cfg = load_config()
        anim_style = _anim_cfg.get("toast_anim_style", "simple")
        _speed_steps = {1: 6, 2: 10, 3: 15, 4: 22, 5: 30}
        total_steps = _speed_steps.get(int(_anim_cfg.get("toast_anim_speed", 3)), 15)

        if anim_style == "yahoo":
            try:
                self.win.attributes("-alpha", 0.0)
            except Exception:
                pass

            def animate_step(i=0):
                if not self.win or self._closed:
                    return
                if i >= total_steps:
                    try:
                        self.win.geometry(f"{self.toast_w}x{self.toast_h}+{self._final_x}+{self._final_y}")
                        self.win.attributes("-alpha", 1.0)
                    except Exception:
                        pass
                    return
                t = i / total_steps
                t_e = 1.0 - (1.0 - t) ** 2 
                alpha = t_e
                scale = 0.9 + 0.1 * t_e
                w = max(1, int(self.toast_w * scale))
                h = max(1, int(self.toast_h * scale))
                x = self._final_x + (self.toast_w - w) // 2
                y = self._final_y + (self.toast_h - h) // 2
                try:
                    self.win.geometry(f"{w}x{h}+{x}+{y}")
                    self.win.attributes("-alpha", alpha)
                except Exception:
                    pass
                aid = self.win.after(10, lambda: animate_step(i + 1))
                self._after_ids.append(aid)

            animate_step()
        else:
            def animate_step(i=0):
                if not self.win or self._closed:
                    return
                if i >= total_steps:
                    self.win.geometry(f"{self.toast_w}x{self.toast_h}+{self._final_x}+{self._final_y}")
                    return
                t = i / total_steps
                y = int(start_y + (self._final_y - start_y) * t)
                try:
                    self.win.geometry(f"{self.toast_w}x{self.toast_h}+{self._final_x}+{y}")
                except Exception:
                    pass
                aid = self.win.after(10, lambda: animate_step(i + 1))
                self._after_ids.append(aid)

            animate_step()

        self._timer = threading.Timer(8.0, lambda: _tk_root.after(0, self.close))
        self._timer.daemon = True
        self._timer.start()

def _remove_yahoo_toast(toast: YahooToast) -> None:
    with _yahoo_lock:
        if toast in _yahoo_toasts:
            _yahoo_toasts.remove(toast)
    if _tk_root:
        _tk_root.after(0, _reposition_yahoo_toasts)

def _reposition_yahoo_toasts() -> None:
    if not _tk_root:
        return
    sh = _tk_root.winfo_screenheight()
    _y_offset = int(load_config().get("toast_y_offset", 0))
    y_cursor = sh - 4 - _y_offset
    for t in _yahoo_toasts:
        if t.win and not t._closed:
            new_y = y_cursor - t.toast_h
            t._final_y = new_y
            try:
                t.win.geometry(f"{t.toast_w}x{t.toast_h}+{t._final_x}+{new_y}")
            except Exception:
                pass
            y_cursor = new_y - YAHOO_GAP

def _truncate_toast_msg(text: str, wrap_px: int = 210, max_lines: int = 2,
                        prefix: str = "") -> str:
    try:
        from tkinter import font as _tkfont
        fnt = _tkfont.Font(family="Tahoma", size=8)
        ELLIPSIS = "\u2026"
        body = text.replace("\n", " ").strip()
        lines: list[str] = []

        if prefix:
            prefix_w = fnt.measure(prefix)
            remaining_w1 = wrap_px - prefix_w
            if remaining_w1 < 20 or not body:
                lines.append(prefix.rstrip())
                remaining = body
            else:
                lo, hi = 0, len(body)
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if fnt.measure(body[:mid]) <= remaining_w1:
                        lo = mid
                    else:
                        hi = mid - 1
                fit = max(lo, 1)
                if fit >= len(body):
                    lines.append((prefix + body).rstrip())
                    remaining = ""
                else:
                    chunk = body[:fit]
                    rest  = body[fit:]
                    if rest[:1] != " ":
                        sp = chunk.rfind(" ")
                        if sp > 0:
                            rest  = chunk[sp + 1:] + rest
                            chunk = chunk[:sp]
                    lines.append((prefix + chunk).rstrip())
                    remaining = rest.lstrip()
        else:
            remaining = body
        while remaining and len(lines) < max_lines:
            lo, hi = 0, len(remaining)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if fnt.measure(remaining[:mid]) <= wrap_px:
                    lo = mid
                else:
                    hi = mid - 1
            fit = max(lo, 1)

            if fit >= len(remaining):
                lines.append(remaining)
                remaining = ""
            else:
                chunk = remaining[:fit]
                rest  = remaining[fit:]
                if rest[:1] != " ":
                    sp = chunk.rfind(" ")
                    if sp > 0:
                        rest  = chunk[sp + 1:] + rest
                        chunk = chunk[:sp]
                lines.append(chunk.rstrip())
                remaining = rest.lstrip()

        if remaining:
            last = lines[-1]
            while last and fnt.measure(last + ELLIPSIS) > wrap_px:
                last = last[:-1]
            lines[-1] = last.rstrip() + ELLIPSIS

        return "\n".join(lines)

    except Exception:
        MAX_CH = max(10, wrap_px // 6)
        full   = (prefix + text).replace("\n", " ").strip()
        fb_lines: list[str] = []
        rem = full
        while rem and len(fb_lines) < max_lines:
            if len(rem) <= MAX_CH:
                fb_lines.append(rem)
                rem = ""
            else:
                sp = rem[:MAX_CH].rfind(" ")
                if sp > 0:
                    fb_lines.append(rem[:sp])
                    rem = rem[sp + 1:]
                else:
                    fb_lines.append(rem[:MAX_CH])
                    rem = rem[MAX_CH:]
        if rem and fb_lines:
            last = fb_lines[-1]
            fb_lines[-1] = last[:MAX_CH - 1].rstrip() + "…"
        return "\n".join(fb_lines)

def _get_user_titlebar_gradient(user_id: str) -> "tuple[str | None, str | None]":
    if not user_id:
        return (None, None)
    cfg = load_config()
    per_user = cfg.get("per_user_sounds", {})
    user_cfg = per_user.get(user_id, {})
    start = user_cfg.get("titlebar_start", "").strip()
    end = user_cfg.get("titlebar_end", "").strip()
    if start and end:
        return (start, end)
    return (None, None)

def _get_user_body_border(user_id: str) -> "str | None":
    if not user_id:
        return None
    cfg = load_config()
    per_user = cfg.get("per_user_sounds", {})
    user_cfg = per_user.get(user_id, {})
    col = user_cfg.get("body_border_color", "").strip()
    return col if col else None

def _push_yahoo_toast(title: str, body: str, url: "str | None",
                      avatar_png: "str | None" = None,
                      sound_key: str = "NewMessage",
                      channel_id: "str | None" = None,
                      author_name: str = "",
                      guild_name: str = "",
                      channel_name: str = "",
                      author_id: str = "") -> None:
    def _do() -> None:
        _cfg = load_config()
        _max_stack = int(_cfg.get("yahoo_max_stack", YAHOO_MAX_STACK))
        _compact = _cfg.get("toast_display_mode", "normal") == "compact"
        _compact_icons = _cfg.get("compact_icons", {})

        oldest_to_close = None
        with _yahoo_lock:
            if len(_yahoo_toasts) >= _max_stack:
                oldest_to_close = _yahoo_toasts.pop()
            new_toast = YahooToast(title, body, url, avatar_png, sound_key, channel_id,
                                   author_name, guild_name, channel_name,
                                   titlebar_start=None, titlebar_end=None,
                                   author_id=author_id,
                                   compact_mode=_compact,
                                   compact_icons=_compact_icons)
            _yahoo_toasts.insert(0, new_toast)
            new_toast.build(0)
            sh = _tk_root.winfo_screenheight()
            _y_offset = int(_cfg.get("toast_y_offset", 0))
            y_cursor = sh - 4 - _y_offset
            for t in _yahoo_toasts:
                if t.win and not t._closed:
                    new_y = y_cursor - t.toast_h
                    t._final_y = new_y
                    try:
                        t.win.geometry(f"{t.toast_w}x{t.toast_h}+{t._final_x}+{new_y}")
                    except Exception:
                        pass
                    y_cursor = new_y - YAHOO_GAP
        if oldest_to_close is not None:
            oldest_to_close.close(animate=False)
    if _tk_root:
        _tk_root.after(0, _do)

from dataclasses import dataclass, field
from typing import Optional
from tkinter import font as tkfont
import numpy as np
PIL_OK = _PIL_OK 
import sys as _sys
_WIN32_LAYERED = False
if _sys.platform == "win32":
    try:
        import ctypes as _ct
        _user32 = _ct.windll.user32
        _gdi32  = _ct.windll.gdi32

        _GWL_EXSTYLE   = -20
        _WS_EX_LAYERED = 0x00080000
        _ULW_ALPHA     = 2
        _AC_SRC_OVER   = 0
        _AC_SRC_ALPHA  = 1

        class _POINT(_ct.Structure):
            _fields_ = [("x", _ct.c_long), ("y", _ct.c_long)]

        class _SIZE(_ct.Structure):
            _fields_ = [("cx", _ct.c_long), ("cy", _ct.c_long)]

        class _BLENDFUNCTION(_ct.Structure):
            _fields_ = [("BlendOp",             _ct.c_byte),
                        ("BlendFlags",           _ct.c_byte),
                        ("SourceConstantAlpha",  _ct.c_byte),
                        ("AlphaFormat",          _ct.c_byte)]

        class _BITMAPINFOHEADER(_ct.Structure):
            _fields_ = [("biSize",          _ct.c_uint32),
                        ("biWidth",         _ct.c_int32),
                        ("biHeight",        _ct.c_int32),
                        ("biPlanes",        _ct.c_uint16),
                        ("biBitCount",      _ct.c_uint16),
                        ("biCompression",   _ct.c_uint32),
                        ("biSizeImage",     _ct.c_uint32),
                        ("biXPelsPerMeter", _ct.c_int32),
                        ("biYPelsPerMeter", _ct.c_int32),
                        ("biClrUsed",       _ct.c_uint32),
                        ("biClrImportant",  _ct.c_uint32)]

        _WIN32_LAYERED = True
    except Exception:
        pass

def _ulw(hwnd: int, pil_img) -> bool:
    if not _WIN32_LAYERED or not PIL_OK:
        return False

    w, h = pil_img.size
    img  = pil_img.convert("RGBA")

    try:
        import numpy as _np
        arr = _np.array(img, dtype=_np.uint8).copy()
        a_f = arr[:, :, 3].astype(_np.float32) / 255.0
        r_  = arr[:, :, 0].copy()
        g_  = arr[:, :, 1].copy()
        b_  = arr[:, :, 2].copy()
        arr[:, :, 0] = (b_ * a_f).astype(_np.uint8)
        arr[:, :, 1] = (g_ * a_f).astype(_np.uint8)
        arr[:, :, 2] = (r_ * a_f).astype(_np.uint8)
        bgra = arr.tobytes()
    except ImportError:
        raw  = img.tobytes()
        bgra = bytearray(len(raw))
        for i in range(0, len(raw), 4):
            r, g, b, a = raw[i], raw[i+1], raw[i+2], raw[i+3]
            af = a / 255.0
            bgra[i]   = int(b * af)
            bgra[i+1] = int(g * af)
            bgra[i+2] = int(r * af)
            bgra[i+3] = a
        bgra = bytes(bgra)

    hdc_scr = _user32.GetDC(None)
    hdc_mem = _gdi32.CreateCompatibleDC(hdc_scr)

    bmi = _BITMAPINFOHEADER()
    bmi.biSize      = _ct.sizeof(_BITMAPINFOHEADER)
    bmi.biWidth     = w
    bmi.biHeight    = -h
    bmi.biPlanes    = 1
    bmi.biBitCount  = 32
    bmi.biCompression = 0

    ppBits = _ct.c_void_p()
    hbm = _gdi32.CreateDIBSection(hdc_mem, _ct.byref(bmi), 0,
                                   _ct.byref(ppBits), None, 0)
    if not hbm:
        _gdi32.DeleteDC(hdc_mem)
        _user32.ReleaseDC(None, hdc_scr)
        return False

    _ct.memmove(ppBits, bgra, len(bgra))
    old_bm = _gdi32.SelectObject(hdc_mem, hbm)
    es = _user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
    if not (es & _WS_EX_LAYERED):
        _user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, es | _WS_EX_LAYERED)

    sz     = _SIZE(w, h)
    pt_src = _POINT(0, 0)
    blend  = _BLENDFUNCTION(_AC_SRC_OVER, 0, 255, _AC_SRC_ALPHA)
    ok = _user32.UpdateLayeredWindow(
        hwnd, hdc_scr,
        None,           
        _ct.byref(sz),
        hdc_mem, _ct.byref(pt_src),
        0, _ct.byref(blend), _ULW_ALPHA
    )

    _gdi32.SelectObject(hdc_mem, old_bm)
    _gdi32.DeleteObject(hbm)
    _gdi32.DeleteDC(hdc_mem)
    _user32.ReleaseDC(None, hdc_scr)
    return bool(ok)

WIN_WIDTH        = 220
WIN_MAX_HEIGHT   = 400
MIN_SKIN_WIDTH   = 150  
MIN_SKIN_HEIGHT  = 40   
MAX_SKIN_WIDTH   = 350 
DEFAULT_TIMEOUT  = 7    
OPACITY          = 0.88
BORDER           = True
ROUND            = True
ANIMATE          = True    
TRANS_KEY        = "#010203"
SB_WIDTH         = 22     
PADDING          = 4
TEXT_INDENT      = 22

COL_BG           = "#808080" 
COL_BORDER       = "#000000"
COL_SIDEBAR      = "#7F7F7F"
COL_TITLE_UL     = "#808080"  
COL_FIRST_LINE   = "#FFFFFF"
COL_SECOND_LINE  = "#EFEFEF"
COL_TIME         = "#DDEEFF"

CORNER_RADIUS    = 7         
LOCATION         = "bottomright"

AVATAR_BORDER_COLOR = "#000000" 
AVATAR_BORDER_WIDTH = 1     

BACK_TINT_COLOR: Optional[str] = None
STACK_GAP        = 2
FONT_AA          = True    
FONT_FAMILY      = "Segoe UI"
FONT_SIZE        = 9

def hex_to_rgb(h: str) -> tuple[int,int,int]:
    h = h.lstrip("#")
    return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)

def rgb_to_hex(r,g,b) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def overlay_blend(base_hex: str, top_hex: str) -> str:
    br, bg, bb = hex_to_rgb(base_hex)
    tr, tg, tb = hex_to_rgb(top_hex)
    def _ch(b: int, t: int) -> int:
        bf, tf = b / 255.0, t / 255.0
        if bf <= 0.5:
            out = 2.0 * bf * tf
        else:
            out = 1.0 - 2.0 * (1.0 - bf) * (1.0 - tf)
        return int(max(0.0, min(1.0, out)) * 255 + 0.5)
    return rgb_to_hex(_ch(br, tr), _ch(bg, tg), _ch(bb, tb))

def _darker(hex_col: str, factor: float = 0.75) -> str:
    r,g,b = hex_to_rgb(hex_col)
    return rgb_to_hex(int(r*factor), int(g*factor), int(b*factor))

def find_file_ci(folder: str, name: str) -> Optional[str]:
    if not folder:
        return None

    norm = name.replace('\\', '/')
    slash = norm.find('/')
    if slash != -1:
        sub_name  = norm[:slash]
        rest_name = norm[slash + 1:]
        try:
            for entry in os.listdir(folder):
                if entry.lower() == sub_name.lower():
                    sub_path = os.path.join(folder, entry)
                    if os.path.isdir(sub_path):
                        result = find_file_ci(sub_path, rest_name)
                        if result:
                            return result
        except FileNotFoundError:
            pass
        return None

    target = norm.lower()
    try:
        for entry in os.listdir(folder):
            if entry.lower() == target:
                full = os.path.join(folder, entry)
                if os.path.isfile(full):
                    return full
    except FileNotFoundError:
        pass
    for sub in glob.glob(os.path.join(folder, "*/")):
        try:
            for entry in os.listdir(sub):
                if entry.lower() == target:
                    full = os.path.join(sub, entry)
                    if os.path.isfile(full):
                        return full
        except FileNotFoundError:
            pass
    return None

def _wrap_lines(text: str, max_w: int, font_obj) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bb = font_obj.getbbox(test)
        if (bb[2] - bb[0]) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]

def _pil_font(size: int = None, bold: bool = False) -> "ImageFont.FreeTypeFont":
    fsize = size if size is not None else FONT_SIZE
    px = max(8, int(fsize * 96 / 72))

    _WIN  = "C:/Windows/Fonts/"
    _LIN  = "/usr/share/fonts/truetype/"
    _FONT_MAP = {
        "segoe ui":    (_WIN+"segoeui.ttf",        _WIN+"segoeuib.ttf"),
        "arial":       (_WIN+"arial.ttf",           _WIN+"arialbd.ttf"),
        "tahoma":      (_WIN+"tahoma.ttf",          _WIN+"tahomabd.ttf"),
        "verdana":     (_WIN+"verdana.ttf",         _WIN+"verdanab.ttf"),
        "trebuchet ms":(_WIN+"trebuc.ttf",          _WIN+"trebucbd.ttf"),
        "calibri":     (_WIN+"calibri.ttf",         _WIN+"calibrib.ttf"),
        "courier new": (_WIN+"cour.ttf",            _WIN+"courbd.ttf"),
        "consolas":    (_WIN+"consola.ttf",         _WIN+"consolab.ttf"),
        "comic sans ms":(_WIN+"comic.ttf",          _WIN+"comicbd.ttf"),
        "liberation sans":  (_LIN+"liberation/LiberationSans-Regular.ttf",
                             _LIN+"liberation/LiberationSans-Bold.ttf"),
        "dejavu sans":      (_LIN+"dejavu/DejaVuSans.ttf",
                             _LIN+"dejavu/DejaVuSans-Bold.ttf"),
        "ubuntu":           (_LIN+"ubuntu/Ubuntu-R.ttf",
                             _LIN+"ubuntu/Ubuntu-B.ttf"),
        "noto sans":        (_LIN+"noto/NotoSans-Regular.ttf",
                             _LIN+"noto/NotoSans-Bold.ttf"),
    }

    key = FONT_FAMILY.lower().strip()
    entry = _FONT_MAP.get(key)
    if entry:
        path = entry[1] if bold else entry[0]
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, px)
            except Exception:
                pass
     
        fallback = entry[0]
        if os.path.exists(fallback):
            try:
                return ImageFont.truetype(fallback, px)
            except Exception:
                pass

    name_norm = key.replace(" ", "")
    suffixes_bold = ["b.ttf", "bd.ttf", "-bold.ttf", "-b.ttf", "bold.ttf"]
    suffixes_reg  = [".ttf", "-regular.ttf", "r.ttf"]
    search_dirs = [_WIN, _LIN + "liberation/", _LIN + "dejavu/",
                   _LIN + "ubuntu/", _LIN + "noto/",
                   "/usr/share/fonts/truetype/",
                   "/System/Library/Fonts/", os.path.expanduser("~/.fonts/")]
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            fl = fname.lower().replace(" ", "").replace("-", "").replace("_", "")
            if name_norm in fl:
                suffixes = suffixes_bold if bold else suffixes_reg
                for s in suffixes:
                    if fl.endswith(s.replace("-","").replace("_","")):
                        try:
                            return ImageFont.truetype(os.path.join(d, fname), px)
                        except Exception:
                            pass
                if fl.endswith(".ttf"):
                    try:
                        return ImageFont.truetype(os.path.join(d, fname), px)
                    except Exception:
                        pass

    return ImageFont.load_default()

try:
    import freetype as _freetype
    _FREETYPE_PY_OK = True
except Exception:
    _FREETYPE_PY_OK = False

_ft_face_cache: dict = {}

def _ft_face_open(path: str):
    if path not in _ft_face_cache:
        try:
            _ft_face_cache[path] = _freetype.Face(path)
        except Exception:
            _ft_face_cache[path] = None
    return _ft_face_cache[path]

_UNICODE_FALLBACK_PATHS = [
    "C:/Windows/Fonts/seguisym.ttf",   
    "C:/Windows/Fonts/seguiemj.ttf",    
    "C:/Windows/Fonts/SegoeuiHis.ttf",  
    "C:/Windows/Fonts/segoeui.ttf",    
    "C:/Windows/Fonts/NirmalaUI.ttf",  
    "C:/Windows/Fonts/ebrima.ttf",     
    "C:/Windows/Fonts/msgothic.ttc",   
    "C:/Windows/Fonts/malgun.ttf",    
    "C:/Windows/Fonts/meiryo.ttc",    
    "C:/Windows/Fonts/msyh.ttc",     
    "C:/Windows/Fonts/YuGothR.ttc",  
    "C:/Windows/Fonts/simsun.ttc",     
    "C:/Windows/Fonts/cambria.ttc",   
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/leelawad.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/unifont/unifont.ttf",
]

_W = "C:/Windows/Fonts/"
_UNICODE_RANGE_FONT: list = [
    (0xFE30, 0xFE4F, _W + "msgothic.ttc"),
    (0xFE50, 0xFE6F, _W + "msgothic.ttc"),
    (0x3000, 0x9FFF, _W + "msgothic.ttc"),
    (0xF900, 0xFAFF, _W + "msgothic.ttc"),
    (0xAA00, 0xAA5F, _W + "ebrima.ttf"),
    (0x1C50, 0x1C7F, _W + "ebrima.ttf"),
    (0xA500, 0xA63F, _W + "ebrima.ttf"),
    (0x07C0, 0x07FF, _W + "ebrima.ttf"),
    (0x0900, 0x097F, _W + "NirmalaUI.ttf"),
    (0x0980, 0x09FF, _W + "NirmalaUI.ttf"),
    (0x0B00, 0x0B7F, _W + "NirmalaUI.ttf"),
    (0x0A80, 0x0AFF, _W + "NirmalaUI.ttf"),
    (0x0C80, 0x0CFF, _W + "NirmalaUI.ttf"),
    (0x0D00, 0x0D7F, _W + "NirmalaUI.ttf"),
    (0x2100, 0x214F, _W + "cambria.ttc"),
    (0x2200, 0x22FF, _W + "cambria.ttc"),
    (0x2070, 0x209F, _W + "cambria.ttc"),
    (0x02B0, 0x02FF, _W + "segoeui.ttf"),
    (0x2000, 0x206F, _W + "segoeui.ttf"),
    (0x2E00, 0x2E7F, _W + "segoeui.ttf"),
    (0x2600, 0x26FF, _W + "seguisym.ttf"),
    (0x2700, 0x27BF, _W + "seguisym.ttf"),
    (0x1F300, 0x1F9FF, _W + "seguiemj.ttf"),
]

_unicode_fallback_cache: dict = {}
_glyph_font_cache: dict = {}
_range_font_cache: dict = {}

def _load_fallback_fonts(px: int) -> list:
    if px in _unicode_fallback_cache:
        return _unicode_fallback_cache[px]
    loaded = []
    for path in _UNICODE_FALLBACK_PATHS:
        if os.path.exists(path):
            try:
                loaded.append(ImageFont.truetype(path, px))
            except Exception:
                pass
    _unicode_fallback_cache[px] = loaded
    return loaded

def _font_for_range(cp: int, px: int):
    for start, end, path in _UNICODE_RANGE_FONT:
        if start <= cp <= end:
            if not os.path.exists(path):
                return None
            key = (path, px)
            if key not in _range_font_cache:
                try:
                    _range_font_cache[key] = ImageFont.truetype(path, px)
                except Exception:
                    _range_font_cache[key] = None
            return _range_font_cache[key]
    return None

def _font_has_glyph(fnt: "ImageFont.FreeTypeFont", ch: str) -> bool:
    if ch in (" ", "\t", "\n"):
        return True
    try:
        if _FREETYPE_PY_OK:
            path = getattr(fnt, "path", None)
            if path:
                face = _ft_face_open(path)
                if face is not None:
                    return face.get_char_index(ord(ch)) != 0
        if _PIL_OK:
            bb_ch = fnt.getbbox(ch)
            if bb_ch is None or (bb_ch[2] - bb_ch[0]) <= 0 or (bb_ch[3] - bb_ch[1]) <= 0:
                return False
            if ch == "\uFFFD":
                return True
            w = max(bb_ch[2] - bb_ch[0], 1) + 4
            h = max(bb_ch[3] - bb_ch[1], 1) + 4
            img_ch   = Image.new("L", (w, h), 0)
            img_repl = Image.new("L", (w, h), 0)
            ImageDraw.Draw(img_ch).text(  (2, 2), ch,        font=fnt, fill=255)
            ImageDraw.Draw(img_repl).text((2, 2), "\uFFFD",  font=fnt, fill=255)
            data_ch = list(img_ch.getdata())
            if data_ch == list(img_repl.getdata()):
                return False
            for notdef in ("\u25A1", "\u25A0", "\u25FB"):
                img_nd = Image.new("L", (w, h), 0)
                ImageDraw.Draw(img_nd).text((2, 2), notdef, font=fnt, fill=255)
                if data_ch == list(img_nd.getdata()):
                    return False
            return True
        bb_ch = fnt.getbbox(ch)
        if bb_ch is None or (bb_ch[2] - bb_ch[0]) <= 0 or (bb_ch[3] - bb_ch[1]) <= 0:
            return False
        return bb_ch != fnt.getbbox("\uFFFD")
    except Exception:
        return False

def _best_font_for_char(ch: str, primary: "ImageFont.FreeTypeFont",
                        fallbacks: list) -> "ImageFont.FreeTypeFont":
    cache_key = (id(primary), ord(ch))
    if cache_key in _glyph_font_cache:
        return _glyph_font_cache[cache_key]
    if ord(ch) < 0x0100:
        _glyph_font_cache[cache_key] = primary
        return primary
    if _font_has_glyph(primary, ch):
        _glyph_font_cache[cache_key] = primary
        return primary
    px = primary.size if hasattr(primary, "size") else 12
    range_fnt = _font_for_range(ord(ch), px)
    if range_fnt is not None and _font_has_glyph(range_fnt, ch):
        _glyph_font_cache[cache_key] = range_fnt
        return range_fnt
    for fb in fallbacks:
        if _font_has_glyph(fb, ch):
            _glyph_font_cache[cache_key] = fb
            return fb
    _glyph_font_cache[cache_key] = primary
    return primary

def _get_unicode_fallback_font(px: int) -> "ImageFont.FreeTypeFont | None":
    fbs = _load_fallback_fonts(px)
    return fbs[0] if fbs else None

def _draw_text_unicode(draw: "ImageDraw.ImageDraw",
                       pos: tuple,
                       text: str,
                       font: "ImageFont.FreeTypeFont",
                       fill: tuple,
                       clip_x: int = 0) -> None:
    x, y = pos
    px = font.size if hasattr(font, "size") else 12
    fallbacks = _load_fallback_fonts(px)

    runs: list = []   
    cur_fnt = None
    cur_txt = ""
    cur_x   = x
    advance_x = x

    for ch in text:
        use_fnt = _best_font_for_char(ch, font, fallbacks)

        if use_fnt is not cur_fnt:
            if cur_txt:
                runs.append((cur_fnt, cur_txt, cur_x))
            cur_fnt = use_fnt
            cur_txt = ch
            cur_x   = advance_x
        else:
            cur_txt += ch

        try:
            bb = use_fnt.getbbox(ch)
            advance_x += (bb[2] - bb[0]) if bb else 0
        except Exception:
            pass

    if cur_txt:
        runs.append((cur_fnt, cur_txt, cur_x))

    if clip_x > 0:
        img_dest = draw._image
        tmp = Image.new("RGBA", img_dest.size, (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp)
        for fnt_r, txt_r, x_r in runs:
            tmp_draw.text((x_r, y), txt_r, font=fnt_r, fill=fill)
        mask = Image.new("L", img_dest.size, 255)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rectangle([clip_x, 0, img_dest.width, img_dest.height], fill=0)
        r, g, b, a = tmp.split()
        a = ImageChops.multiply(a, mask)
        tmp = Image.merge("RGBA", (r, g, b, a))
        img_dest.alpha_composite(tmp)
    else:
        for fnt_r, txt_r, x_r in runs:
            draw.text((x_r, y), txt_r, font=fnt_r, fill=fill)

class ExprEval:

    def eval(self, expr: str, ctx: dict) -> int:
        if not expr or expr.strip() == "":
            return 0
        expr = expr.strip()
        for k in sorted(ctx.keys(), key=len, reverse=True):
            safe_k = re.escape(k)
            expr = re.sub(safe_k, str(ctx[k]), expr)

        expr = re.sub(r'\b[A-Za-z_]\w*(?:\.\w+)+\b', '0', expr)

        expr = self._convert_max(expr)

        try:
            result = eval(expr, {"__builtins__": {}, "max": max, "min": min, "abs": abs})
            return int(result)
        except Exception:
            return 0

    def _convert_max(self, expr: str) -> str:
        _pat = re.compile(
            r'\('
            r'([^()]*(?:\([^()]*\)[^()]*)*)'
            r'\s*>\s*'
            r'([^()]*(?:\([^()]*\)[^()]*)*)'
            r'\)'
        )
        prev = None
        while prev != expr:
            prev = expr
            expr = _pat.sub(
                lambda m: f'max({m.group(1).strip()},{m.group(2).strip()})',
                expr)

        if '>' in expr:
            parts = [p.strip() for p in expr.split('>')]
            return f'max({",".join(parts)})'

        return expr

_eval = ExprEval()

@dataclass
class SkinObj:
    obj_type:    str            = ""       
    source:      str            = ""  
    x_expr:      str            = "0"
    y_expr:      str            = "0"
    w_expr:      str            = ""      
    h_expr:      str            = ""   
    mono:        bool           = False
    layer:       bool           = False
    ifset:       list           = field(default_factory=list)   
    ifnotset:    list           = field(default_factory=list)   
    color:       tuple          = None    
    proportional:bool           = False
    clocksize:   list           = field(default_factory=list)

@dataclass
class SkinDef:
    name:          str
    folder:        str
    w_expr:        str          = str(WIN_WIDTH)
    h_expr:        str          = "100"
    padding_right: int          = 0
    padding_bottom:int          = 0
    popup_version: str          = ""
    options:       dict         = field(default_factory=dict)
    objects:       list         = field(default_factory=list)

class SkinParser:

    def parse(self, text: str, name: str, folder: str) -> SkinDef:
        skin = SkinDef(name=name, folder=folder)
        lines = [l.rstrip() for l in text.replace('\r\n','\n').split('\n')]

        i = 0
        in_options = False
        in_object  = False
        cur_obj: Optional[SkinObj] = None

        while i < len(lines):
            raw = lines[i]
            if '#' in raw:
                raw = raw[:raw.index('#')]
            line = raw.strip()
            i += 1

            if not line:
                continue

            low = line.lower()
            if low == "options":
                in_options = True
                continue
            if in_options:
                if low == "end":
                    in_options = False
                    continue
                m = re.match(r'option\s+(\d+)\s+(\d+)\s+(.*)', line, re.I)
                if m:
                    oid, oval, otitle = int(m.group(1)), int(m.group(2)), m.group(3).strip()
                    skin.options[oid] = (oval, otitle)
                continue
            m = re.match(r'^(w|h)\s+(.+)$', line, re.I)
            if m and not in_object:
                if m.group(1).lower() == 'w':
                    skin.w_expr = m.group(2).strip()
                else:
                    skin.h_expr = m.group(2).strip()
                continue

            m = re.match(r'^padding-right\s+(\d+)', line, re.I)
            if m:
                skin.padding_right = int(m.group(1)); continue

            m = re.match(r'^padding-bottom\s+(\d+)', line, re.I)
            if m:
                skin.padding_bottom = int(m.group(1)); continue

            m = re.match(r'^popup-version\s+(\S+)', line, re.I)
            if m:
                skin.popup_version = m.group(1); continue

            if re.match(r'^(shadow-region-opacity|legacy-region-opacity)\s', line, re.I):
                continue

            if low == "object" or low.startswith("object "):
                in_object = True
                cur_obj = SkinObj()
                rest = line[6:].strip()
                if rest:
                    self._parse_obj_line(cur_obj, rest)
                continue

            if in_object:
                if low == "end":
                    in_object = False
                    if cur_obj and cur_obj.obj_type:
                        skin.objects.append(cur_obj)
                    cur_obj = None
                    continue
                if cur_obj:
                    self._parse_obj_line(cur_obj, line)
                continue

        return skin

    def _parse_obj_line(self, obj: SkinObj, line: str):
        low = line.lower()

        m = re.match(r'^type\s+(\w+)', line, re.I)
        if m: obj.obj_type = m.group(1).lower(); return

        m = re.match(r'^source\s+(.+)', line, re.I)
        if m: obj.source = m.group(1).strip(); return

        m = re.match(r'^x\s+(.+)', line, re.I)
        if m: obj.x_expr = m.group(1).strip(); return

        m = re.match(r'^y\s+(.+)', line, re.I)
        if m: obj.y_expr = m.group(1).strip(); return

        m = re.match(r'^w\s+(.+)', line, re.I)
        if m: obj.w_expr = m.group(1).strip(); return

        m = re.match(r'^h\s+(.+)', line, re.I)
        if m: obj.h_expr = m.group(1).strip(); return

        if low == "mono":   obj.mono  = True; return
        if low == "layer":  obj.layer = True; return

        m = re.match(r'^proportional\s+(\d+)', line, re.I)
        if m: obj.proportional = bool(int(m.group(1))); return

        m = re.match(r'^ifset\s+(\d+)', line, re.I)
        if m: obj.ifset.append(int(m.group(1))); return

        m = re.match(r'^ifnotset\s+(\d+)', line, re.I)
        if m: obj.ifnotset.append(int(m.group(1))); return

        m = re.match(r'^color\s+(\d+)\s+(\d+)\s+(\d+)', line, re.I)
        if m:
            r,g,b = int(m.group(1)),int(m.group(2)),int(m.group(3))
            obj.color = (r,g,b); return

        m = re.match(r'^clocksize\s+(.+)', line, re.I)
        if m:
            obj.clocksize = [int(x) for x in m.group(1).split()]; return

    def find_and_parse(self, folder: str) -> Optional[SkinDef]:
        skins = glob.glob(os.path.join(folder, "*.popupskin"))
        if not skins:
            return None
        path = skins[0]
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        skin = self.parse(text, name, folder)

        cfg_path = find_file_ci(folder, "popupskin.config")
        if cfg_path and cfg_path != path:
            with open(cfg_path, 'r', encoding='utf-8', errors='replace') as f:
                cfg_text = f.read()

            for _cline in cfg_text.replace('\r\n','\n').split('\n'):
                _cline = _cline.strip()
                _m = re.match(r'^#?option\s+(\d+)\s+(\d+)\s+(.*)', _cline, re.I)
                if _m:
                    _oid = int(_m.group(1))
                    _oval = int(_m.group(2))
                    _otitle = _m.group(3).strip()
                    if _oid not in skin.options:
                        skin.options[_oid] = (_oval, _otitle)
            cfg_skin = self.parse(cfg_text, name, folder)
            for k, v in cfg_skin.options.items():
                if k not in skin.options:
                    skin.options[k] = v
        return skin

class SkinRenderer:

    AVATAR_SIZE = 40

    def render(self,
               skin:               SkinDef,
               title:              str,
               message:            str,
               opts:               dict,
               color_bg:           str = COL_BG,
               color_fg:           str = COL_FIRST_LINE,
               color_msg:          str = COL_SECOND_LINE,
               back_tint:          str = None,
               icon_path:          str = None,
               avatar_path:        str = None,
               force_avatar:       Optional[bool] = None,
               force_icon:         Optional[bool] = None,
               force_clock:        Optional[bool] = None,
               avatar_corner_radius: int = 0,  
               avatar_aa: bool = True,        
               avatar_border_width: int = -1,    
               avatar_border_aa: bool = True,     
               bold_prefix: str = "",         
               ) -> Image.Image:

        if not PIL_OK:
            raise RuntimeError("Pillow no está instalado")

        bg_rgb  = hex_to_rgb(color_bg)
        fg_rgb  = hex_to_rgb(color_fg)
        msg_rgb = hex_to_rgb(color_msg)
        _effective_tint = back_tint if back_tint else BACK_TINT_COLOR
        if _effective_tint:
            try:
                mono_tint = hex_to_rgb(_effective_tint)
            except Exception:
                mono_tint = bg_rgb
        else:
            mono_tint = bg_rgb

        fnt_title = _pil_font(9, bold=True)
        fnt_body  = _pil_font(9, bold=False)
        fnt_body_bold = _pil_font(9, bold=True)
        fnt_time  = _pil_font(8, bold=False)

        def text_size(txt, fnt):
            bb = fnt.getbbox(txt)
            return (bb[2]-bb[0]), (bb[3]-bb[1])

        clock_str  = time.strftime("%H:%M")
        title_w, title_h = text_size(title, fnt_title)
        title_h = max(title_h, 16)
        text_w,  text_h  = text_size(message, fnt_body)
        clock_w, clock_h = text_size(clock_str, fnt_time)
        icon_w,  icon_h  = 16, 16
        av_w,    av_h    = 0, 0   

        def _obj_visible(obj) -> bool:
            if any(not opts.get(i, False) for i in obj.ifset):
                return False
            if any(opts.get(i, False) for i in obj.ifnotset):
                return False
            return True

        def _type_visible(obj_type: str, obj) -> bool:
            if obj_type == "clock":
                if force_clock is False:
                    return False
                return _obj_visible(obj)
            override = {"icon": force_icon, "avatar": force_avatar}.get(obj_type)
            if override is not None:
                return override
            return _obj_visible(obj)

        _CLOCKSIZE_CHARS = "-:0123456789  . "  
        for _cobj in skin.objects:
            if _cobj.obj_type == "clock":
                if not _type_visible("clock", _cobj):
                    clock_w = 0
                    clock_h = 0
                elif _cobj.clocksize:
                    _cs = _cobj.clocksize
                    _cw = 0
                    _bmp_clock_str = "-" + clock_str + "."
                    for _ch in _bmp_clock_str:
                        _idx = _CLOCKSIZE_CHARS.find(_ch)
                        if 0 <= _idx < len(_cs):
                            _cw += _cs[_idx]
                    if _cw > 0:
                        clock_w = _cw
                break
        for _iobj in skin.objects:
            if _iobj.obj_type == "icon":
                if not _type_visible("icon", _iobj):
                    icon_w = 0
                    icon_h = 0
                break
        _avatar_img: Optional[Image.Image] = None
        _av_target_w, _av_target_h = self.AVATAR_SIZE, self.AVATAR_SIZE
        _av_proportional = False
        _avatar_visible = False

        for _avobj in skin.objects:
            if _avobj.obj_type == "avatar":
                _avatar_visible = _type_visible("avatar", _avobj)
                _av_proportional = _avobj.proportional
                _simple_ctx = {
                    "options.avatarsize": self.AVATAR_SIZE,
                    "window.width": WIN_WIDTH, "window.height": 100,
                }
                if _avobj.w_expr:
                    _tw = _eval.eval(_avobj.w_expr, _simple_ctx)
                    if _tw > 0:
                        _av_target_w = _tw
                if _avobj.h_expr:
                    _th = _eval.eval(_avobj.h_expr, _simple_ctx)
                    if _th > 0:
                        _av_target_h = _th
                break

        if avatar_path and _avatar_visible:
            try:
                _avatar_img = Image.open(avatar_path).convert("RGBA")
                if _av_proportional:
                    _avatar_img.thumbnail((_av_target_w, _av_target_h), Image.LANCZOS)
                else:
                    _avatar_img = _avatar_img.resize((_av_target_w, _av_target_h), Image.LANCZOS)
                if avatar_corner_radius > 0:
                    _avatar_img = self._round_corners(_avatar_img, avatar_corner_radius, aa=avatar_aa)
                _bw = avatar_border_width if avatar_border_width >= 0 else AVATAR_BORDER_WIDTH
                if _bw > 0:
                    _avatar_img = self._add_avatar_border(
                        _avatar_img,
                        radius=avatar_corner_radius,
                        border_color=AVATAR_BORDER_COLOR,
                        border_width=_bw,
                        aa=avatar_border_aa)
                av_w, av_h = _avatar_img.size
            except Exception:
                _avatar_img = None

        _icon_img: Optional[Image.Image] = None
        if icon_path and icon_w > 0:
            try:
                _icon_raw = Image.open(icon_path)
                if hasattr(_icon_raw, "n_frames") and _icon_raw.n_frames > 1:
                    best_idx, best_diff = 0, float("inf")
                    for _fi in range(_icon_raw.n_frames):
                        _icon_raw.seek(_fi)
                        _fw, _fh = _icon_raw.size
                        diff = abs(_fw - 16) + abs(_fh - 16)
                        if diff < best_diff:
                            best_diff, best_idx = diff, _fi
                    _icon_raw.seek(best_idx)
                _icon_img = _icon_raw.convert("RGBA")
                _icon_img = _icon_img.resize((icon_w, icon_h), Image.LANCZOS)
            except Exception:
                _icon_img = None

        _chrome_w = 36 + icon_w + clock_w + av_w + 20
        _max_text_w = max(MAX_SKIN_WIDTH - _chrome_w, 40)
        ctx = {
            "window.width":     WIN_WIDTH,  
            "window.height":    100,
            "title.width":      min(title_w, _max_text_w),
            "title.height":     title_h,
            "text.width":       min(text_w,  _max_text_w),
            "text.height":      text_h,
            "clock.width":      clock_w,
            "clock.height":     clock_h,
            "icon.width":       icon_w,
            "icon.height":      icon_h,
            "avatar.width":     av_w,
            "avatar.height":    av_h,
            "options.avatarsize": self.AVATAR_SIZE,
        }

        win_w = _eval.eval(skin.w_expr, ctx) if skin.w_expr else WIN_WIDTH

        win_w = max(win_w, MIN_SKIN_WIDTH)
        win_w = min(win_w, MAX_SKIN_WIDTH)   
        ctx["window.width"] = win_w  

        body_x_est = PADDING + TEXT_INDENT  
        pr = skin.padding_right if skin.padding_right else PADDING
        wrap_w = win_w - body_x_est - pr    

        ctx_h100 = {**ctx, "window.height": 100}
        for o in skin.objects:
            if o.obj_type == "text":
                try:
                    bx = _eval.eval(o.x_expr, ctx_h100)
                    if o.w_expr:
                        tw = _eval.eval(o.w_expr, ctx_h100)
                        if tw > 10:
                            body_x_est = bx
                            wrap_w = tw
                    elif 0 < bx < win_w:
                        body_x_est = bx
                        wrap_w = win_w - bx - pr
                except Exception:
                    pass
                break  
        wrap_w = max(wrap_w - 18, 30)
        wrap_lines = _wrap_lines(message, max(wrap_w, 50), fnt_body)
        BODY_MAX_LINES = 3
        _effective_wrap_w = max(wrap_w, 50)
        if len(wrap_lines) > BODY_MAX_LINES:
            wrap_lines = wrap_lines[:BODY_MAX_LINES]
            last = wrap_lines[-1]
            while last and (fnt_body.getbbox(last + "…")[2] -
                            fnt_body.getbbox(last + "…")[0]) > _effective_wrap_w:
                last = last[:-1]
            wrap_lines[-1] = last + "…"
        line_h = fnt_body.getbbox("Ag")[3] - fnt_body.getbbox("Ag")[1]
        text_h_wrapped = len(wrap_lines) * (line_h + 1)

        ctx["text.height"]   = text_h_wrapped

        title_line_h = fnt_title.getbbox("Ag")[3] - fnt_title.getbbox("Ag")[1]
        title_line_h = max(title_line_h, 14)
        TITLE_MAX_LINES = 4
        _clock_margin = (clock_w + 8) if clock_w > 0 else 0
        title_wrap_w = win_w - 40 - _clock_margin 
        for _to in skin.objects:
            if _to.obj_type == "title":
                try:
                    _tx = _eval.eval(_to.x_expr, ctx_h100)
                    if _to.w_expr:
                        _tw = _eval.eval(_to.w_expr, ctx_h100)
                        if _tw > 10:
                            title_wrap_w = _tw
                    elif 0 < _tx < win_w:
                        title_wrap_w = win_w - _tx - 4
                except Exception:
                    pass
                break
        title_wrap_w = max(title_wrap_w, 30)
        _title_lines_raw = _wrap_lines(title, title_wrap_w, fnt_title)
        if len(_title_lines_raw) > TITLE_MAX_LINES:
            _title_lines_raw = _title_lines_raw[:TITLE_MAX_LINES]
            last = _title_lines_raw[-1]
            while last and fnt_title.getbbox(last + "…")[2] - fnt_title.getbbox(last + "…")[0] > title_wrap_w:
                last = last[:-1]
            _title_lines_raw[-1] = last + "…"
        title_wrap_lines = _title_lines_raw
        title_h_wrapped = len(title_wrap_lines) * (title_line_h + 2)
        ctx["title.height"] = title_h_wrapped
        ctx_h100["title.height"] = title_h_wrapped

        win_h = _eval.eval(skin.h_expr, ctx) if skin.h_expr else 80
        win_h = max(win_h, MIN_SKIN_HEIGHT)
        win_h = min(win_h, WIN_MAX_HEIGHT)

        ctx["window.height"] = win_h

        img = Image.new("RGBA", (win_w, win_h), (0, 0, 0, 0))

        draw = ImageDraw.Draw(img)
        draw.fontmode = "1" if not FONT_AA else "L"

        _avatar_rendered = False 
        _avatar_right_edge = 0  
        for obj in skin.objects:
            if not _type_visible(obj.obj_type, obj):
                continue

            x = _eval.eval(obj.x_expr, ctx)
            y = _eval.eval(obj.y_expr, ctx)

            if obj.obj_type == "text" and _avatar_right_edge > 0:
                if x < _avatar_right_edge + 5:
                    x = _avatar_right_edge + 5

            if obj.obj_type == "bitmap":
                src_img = self._load_bitmap(obj.source, skin.folder,
                                            obj.mono, mono_tint)
                if src_img is None:
                    continue

                sw, sh = src_img.size

                if obj.w_expr:
                    ew = _eval.eval(obj.w_expr, ctx)
                    w = max(win_w + ew, 1) if ew < 0 else max(ew, 1)
                else:
                    w = sw

                if obj.h_expr:
                    eh = _eval.eval(obj.h_expr, ctx)
                    h = max(win_h + eh, 1) if eh < 0 else max(eh, 1)
                else:
                    h = sh
                if x < 0:
                    x = win_w + x
                if y < 0:
                    y = win_h + y

                tiled = self._tile_image(src_img, w, h, tile=obj.mono)
                if obj.layer:
                    self._composite_rgba(img, tiled, x, y)
                else:
                    self._paste_rgba(img, tiled, x, y)

            elif obj.obj_type == "title":
                col = obj.color if obj.color else fg_rgb
                yy_t = y
                max_title_y = win_h - 5
                for t_ln in title_wrap_lines:
                    if yy_t + title_line_h > max_title_y:
                        break
                    _draw_text_unicode(draw, (x, yy_t), t_ln, fnt_title, (*col, 255))
                    yy_t += title_line_h + 2

            elif obj.obj_type == "text":
                col = obj.color if obj.color else msg_rgb
                if obj.w_expr:
                    ew = _eval.eval(obj.w_expr, ctx)
                    tw = max(ew - 18, 20)
                else:
                    tw = win_w - x - 4
                tw = min(tw, win_w - x - 5)
                tw = max(tw, 20)

                bp_full = bold_prefix  
                msg_body = message
                has_bp = False
                if bp_full and message.startswith(bp_full):
                    msg_body = message[len(bp_full):]
                    has_bp = True

                if has_bp:
                    bb_bp0 = fnt_body_bold.getbbox(bp_full)
                    bp_w = (bb_bp0[2] - bb_bp0[0]) if bb_bp0 else 0
                    first_tw = max(tw - bp_w, 10)
                    body_words = msg_body.split()
                    cur = ""
                    remaining_words = []
                    found_break = False
                    for wi, w in enumerate(body_words):
                        test = (cur + " " + w).strip()
                        bb = fnt_body.getbbox(test)
                        if (bb[2] - bb[0]) <= first_tw:
                            cur = test
                        else:
                            remaining_words = body_words[wi:]
                            found_break = True
                            break
                    if not found_break:
                        remaining_words = []
                    all_lines = [cur]
                    if remaining_words:
                        all_lines.extend(_wrap_lines(" ".join(remaining_words), tw, fnt_body))
                    lines = all_lines
                else:
                    if tw != _effective_wrap_w:
                        lines = _wrap_lines(message, tw, fnt_body)
                    else:
                        lines = wrap_lines

                if len(lines) > BODY_MAX_LINES:
                    lines = lines[:BODY_MAX_LINES]
                    last = lines[-1]
                    while last and (fnt_body.getbbox(last + "…")[2] -
                                    fnt_body.getbbox(last + "…")[0]) > tw:
                        last = last[:-1]
                    lines[-1] = last + "…"

                def _ellipsis_fit(txt, max_w, fnt):
                    bb = fnt.getbbox(txt)
                    if (bb[2] - bb[0]) <= max_w:
                        return txt
                    while txt and (fnt.getbbox(txt + "…")[2] -
                                   fnt.getbbox(txt + "…")[0]) > max_w:
                        txt = txt[:-1]
                    return txt + "…"

                new_lines = []
                for ln_i2, ln2 in enumerate(lines):
                    if has_bp and ln_i2 == 0:
                        lim = first_tw if has_bp else tw
                        new_lines.append(_ellipsis_fit(ln2, lim, fnt_body))
                    else:
                        new_lines.append(_ellipsis_fit(ln2, tw, fnt_body))
                lines = new_lines

                clip_right = x + tw
                yy = y
                for ln_i, ln in enumerate(lines):
                    if has_bp and ln_i == 0:
                        bb_bp1 = fnt_body_bold.getbbox(bp_full)
                        bw = (bb_bp1[2] - bb_bp1[0]) if bb_bp1 else 0
                        _draw_text_unicode(draw, (x, yy), bp_full, fnt_body_bold, (*col, 255), clip_x=clip_right)
                        if ln:
                            _draw_text_unicode(draw, (x + bw, yy), ln, fnt_body, (*col, 255), clip_x=clip_right)
                    else:
                        _draw_text_unicode(draw, (x, yy), ln, fnt_body, (*col, 255), clip_x=clip_right)
                    yy += line_h + 1

            elif obj.obj_type == "clock":
                if obj.source and obj.clocksize:
                    bmp_clock = self._load_bitmap(obj.source, skin.folder,
                                                  obj.mono, mono_tint)
                    if bmp_clock is not None:
                        cs      = obj.clocksize
                        char_h  = bmp_clock.height
                        offsets: list[tuple[int,int]] = []
                        cx_acc = 0
                        for cw_val in cs:
                            offsets.append((cx_acc, cw_val))
                            cx_acc += cw_val
                        bmp_clock_str = "-" + clock_str + "."
                        _total_clock_w = 0
                        for _ch2 in bmp_clock_str:
                            _idx2 = _CLOCKSIZE_CHARS.find(_ch2)
                            if 0 <= _idx2 < len(offsets):
                                _co2, _cw2 = offsets[_idx2]
                                if _cw2 > 0:
                                    _total_clock_w += _cw2
                        _pr = skin.padding_right if skin.padding_right else 0
                        _max_x = win_w - _total_clock_w - _pr
                        if x > _max_x:
                            x = _max_x
                        draw_x = x
                        for ch in bmp_clock_str:
                            idx = _CLOCKSIZE_CHARS.find(ch)
                            if 0 <= idx < len(offsets):
                                cx_off, cw_val = offsets[idx]
                                if cw_val > 0 and cx_off < bmp_clock.width:
                                    crop_right = min(cx_off + cw_val, bmp_clock.width)
                                    char_crop = bmp_clock.crop(
                                        (cx_off, 0, crop_right, char_h))
                                    self._composite_rgba(img, char_crop, draw_x, y)
                                    draw_x += cw_val
                    else:
                        col = obj.color if obj.color else (150, 200, 255)
                        _draw_text_unicode(draw, (x, y), clock_str, fnt_time, (*col, 255))
                else:
                    col = obj.color if obj.color else (150, 200, 255)
                    _draw_text_unicode(draw, (x, y), clock_str, fnt_time, (*col, 255))

            elif obj.obj_type == "icon":
                if _icon_img is not None:
                    self._composite_rgba(img, _icon_img, x, y)
                else:
                    ix, iy = x, y
                    r2 = 6
                    draw.ellipse([ix, iy, ix+r2*2, iy+r2*2],
                                 fill=(100, 150, 255, 200), outline=(60,100,200,255))
                    draw.text((ix+4, iy+2), "M", font=_pil_font(6, True),
                              fill=(255,255,255,255))

            elif obj.obj_type == "avatar":
                if _avatar_img is not None and not _avatar_rendered:
                    self._composite_rgba(img, _avatar_img, x, y)
                    _avatar_right_edge = x + _avatar_img.width
                    _avatar_rendered = True

        return img

    def _load_bitmap(self, source: str, folder: str,
                     mono: bool, bg_rgb: tuple) -> Optional[Image.Image]:
        src_low = source.lower()

        if src_low.startswith("pixel:"):
            hexcol = source[6:].strip()
            r,g,b = int(hexcol[0:2],16), int(hexcol[2:4],16), int(hexcol[4:6],16)
            if mono:
                r,g,b = self._tint(r,g,b, bg_rgb)
            return Image.new("RGBA", (1,1), (r,g,b,255))

        if src_low.startswith("gradient:"):
            parts = source[9:].split("/")
            direction = parts[0].lower() if parts else "v"
            c1 = parts[1].strip() if len(parts) > 1 else "808080"
            c2 = parts[2].strip() if len(parts) > 2 else "404040"
            r1,g1,b1 = int(c1[0:2],16), int(c1[2:4],16), int(c1[4:6],16)
            r2,g2,b2 = int(c2[0:2],16), int(c2[2:4],16), int(c2[4:6],16)
            sz = 64
            if direction == "v":
                grad = Image.new("RGBA", (1, sz))
                for i in range(sz):
                    t = i / (sz - 1)
                    grad.putpixel((0, i), (
                        int(r1 + t*(r2-r1)), int(g1 + t*(g2-g1)),
                        int(b1 + t*(b2-b1)), 255))
            else:
                grad = Image.new("RGBA", (sz, 1))
                for i in range(sz):
                    t = i / (sz - 1)
                    grad.putpixel((i, 0), (
                        int(r1 + t*(r2-r1)), int(g1 + t*(g2-g1)),
                        int(b1 + t*(b2-b1)), 255))
            if mono:
                grad = self._apply_mono(grad, bg_rgb)
            return grad

        path = find_file_ci(folder, source)
        if not path:
            return None
        try:
            img = Image.open(path).convert("RGBA")
        except Exception:
            return None

        tr, tg, tb = hex_to_rgb(TRANS_KEY)
        try:
            import numpy as _np
            arr = _np.array(img, dtype=_np.uint8).copy()
            mask = (arr[:,:,0] == tr) & (arr[:,:,1] == tg) & (arr[:,:,2] == tb)
            arr[mask, 3] = 0
            img = Image.fromarray(arr, "RGBA")
        except ImportError:
            data = list(img.getdata())
            data = [(r, g, b, 0) if (r, g, b) == (tr, tg, tb) else (r, g, b, a)
                    for r, g, b, a in data]
            img.putdata(data)

        if mono:
            img = self._apply_mono(img, bg_rgb)
        return img

    def _tint(self, r, g, b, tint_rgb):
        tr, tg, tb = tint_rgb
        lum = int(0.299*r + 0.587*g + 0.114*b)
        return (
            min(255, lum * tr // 128),
            min(255, lum * tg // 128),
            min(255, lum * tb // 128),
        )

    

    def _apply_mono(self, img: Image.Image, tint_rgb: tuple) -> Image.Image:
        img = img.convert("RGBA")

        arr = np.array(img).astype(np.float32)

        rgb = arr[:, :, :3] / 255.0
        alpha = arr[:, :, 3]

        tint = np.array(tint_rgb, dtype=np.float32) / 255.0
        tint = np.ones_like(rgb) * tint

        result = np.where(
            rgb <= 0.5,
            2 * rgb * tint,
            1 - 2 * (1 - rgb) * (1 - tint)
        )

        out = np.dstack([
            (result * 255).astype(np.uint8),
            alpha.astype(np.uint8)
        ])

        return Image.fromarray(out, "RGBA")
    def _has_semitransparent(self, img: Image.Image) -> bool:
        arr = np.array(img)
        a = arr[:, :, 3]
        return bool(np.any((a > 0) & (a < 255)))

    def _round_corners(self, img: Image.Image, radius: int, aa: bool = True) -> Image.Image:
        w, h = img.size
        radius = min(radius, w // 2, h // 2)
        if aa:
            scale = 4
            big_w, big_h = w * scale, h * scale
            big_mask = Image.new("L", (big_w, big_h), 0)
            d = ImageDraw.Draw(big_mask)
            big_r = radius * scale
            try:
                d.rounded_rectangle([0, 0, big_w - 1, big_h - 1], radius=big_r, fill=255)
            except AttributeError:
                d.rectangle([big_r, 0, big_w - 1 - big_r, big_h - 1], fill=255)
                d.rectangle([0, big_r, big_w - 1, big_h - 1 - big_r], fill=255)
                for cx, cy in [(0, 0), (big_w - 2*big_r, 0),
                               (0, big_h - 2*big_r), (big_w - 2*big_r, big_h - 2*big_r)]:
                    d.ellipse([cx, cy, cx + 2*big_r - 1, cy + 2*big_r - 1], fill=255)
            mask = big_mask.resize((w, h), Image.LANCZOS)
        else:
            mask = Image.new("L", (w, h), 0)
            d = ImageDraw.Draw(mask)
            try:
                d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
            except AttributeError:
                d.rectangle([radius, 0, w - 1 - radius, h - 1], fill=255)
                d.rectangle([0, radius, w - 1, h - 1 - radius], fill=255)
                for cx, cy in [(0, 0), (w - 2*radius, 0),
                               (0, h - 2*radius), (w - 2*radius, h - 2*radius)]:
                    d.ellipse([cx, cy, cx + 2*radius - 1, cy + 2*radius - 1], fill=255)
        result = img.copy()
        result.putalpha(mask)
        return result

    def _add_avatar_border(self, img: Image.Image, radius: int,
                           border_color: str = "#000000",
                           border_width: int = 1,
                           aa: bool = True) -> Image.Image:
        if border_width <= 0:
            return img
        bw = border_width
        ow, oh = img.size
        nw, nh = ow + bw * 2, oh + bw * 2
        br, bg_c, bb_c = hex_to_rgb(border_color)

        def _draw_border_shape(draw_obj, w, h, r, fill):
            try:
                draw_obj.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill)
            except AttributeError:
                draw_obj.rectangle([r, 0, w - 1 - r, h - 1], fill=fill)
                draw_obj.rectangle([0, r, w - 1, h - 1 - r], fill=fill)
                for cx, cy in [(0, 0), (w - 2*r, 0),
                               (0, h - 2*r), (w - 2*r, h - 2*r)]:
                    draw_obj.ellipse([cx, cy, cx + 2*r - 1, cy + 2*r - 1], fill=fill)

        outer_r = radius + bw
        if aa:
            scale = 4
            bw_s, nw_s, nh_s, r_s = bw*scale, nw*scale, nh*scale, outer_r*scale
            big = Image.new("RGBA", (nw_s, nh_s), (0, 0, 0, 0))
            _draw_border_shape(ImageDraw.Draw(big), nw_s, nh_s, r_s,
                               (br, bg_c, bb_c, 255))
            out = big.resize((nw, nh), Image.LANCZOS)
        else:
            out = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
            _draw_border_shape(ImageDraw.Draw(out), nw, nh, outer_r,
                               (br, bg_c, bb_c, 255))

        out.paste(img, (bw, bw), img if img.mode == "RGBA" else None)
        return out

    def _tile_image(self, src: Image.Image, w: int, h: int, tile: bool = False) -> Image.Image:
        sw, sh = src.size
        if sw == w and sh == h:
            return src
        if sw == 1 and sh == 1:
            return Image.new("RGBA", (w, h), src.getpixel((0, 0)))

        if sw == 1 and sh > 1:
            col = src.resize((1, h), Image.BILINEAR)
            out = Image.new("RGBA", (w, h))
            for xi in range(w):
                out.paste(col, (xi, 0))
            return out

        if sh == 1 and sw > 1:
            row = src.resize((w, 1), Image.BILINEAR)
            out = Image.new("RGBA", (w, h))
            for yi in range(h):
                out.paste(row, (0, yi))
            return out

        if tile:
            out = Image.new("RGBA", (w, h))
            mask = src.split()[3] if src.mode == "RGBA" else None
            for ty in range(0, h, sh):
                for tx in range(0, w, sw):
                    out.paste(src, (tx, ty), mask)
            return out

        return src.resize((w, h), Image.LANCZOS)

    def _composite_rgba(self, dst: Image.Image, src: Image.Image, x: int, y: int):
        if x >= dst.width or y >= dst.height:
            return
        sx, sy = 0, 0
        w, h = src.size
        if x < 0:
            sx = -x; w += x; x = 0
        if y < 0:
            sy = -y; h += y; y = 0
        w = min(w, dst.width  - x)
        h = min(h, dst.height - y)
        if w <= 0 or h <= 0:
            return
        src_crop = src.crop((sx, sy, sx+w, sy+h)).convert("RGBA")
        dst_crop = dst.crop((x, y, x+w, y+h)).convert("RGBA")
        merged = Image.alpha_composite(dst_crop, src_crop)
        dst.paste(merged, (x, y))

    def _paste_rgba(self, dst: Image.Image, src: Image.Image, x: int, y: int):
        if x >= dst.width or y >= dst.height:
            return
        sx, sy = 0, 0
        w, h = src.size
        if x < 0:
            sx = -x; w += x; x = 0
        if y < 0:
            sy = -y; h += y; y = 0
        w = min(w, dst.width  - x)
        h = min(h, dst.height - y)
        if w <= 0 or h <= 0:
            return
        region = src.crop((sx, sy, sx+w, sy+h))
        try:
            import numpy as _np2
            dst_arr = _np2.array(dst)
            src_arr = _np2.array(region)
            dst_arr[y:y+h, x:x+w] = src_arr
            result = Image.fromarray(dst_arr, "RGBA")
            dst.paste(result)
        except ImportError:
            mask = region.split()[3]
            dst.paste(region, (x, y), mask=mask)

class PopupStack:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._stack: list = []

    def add(self, pw):
        self._stack.append(pw)
        self._reposition()

    def remove(self, pw):
        if pw in self._stack:
            self._stack.remove(pw)
        self._reposition()

    def _reposition(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        taskbar_h = 60
        try:
            import ctypes as _ct2
            class _RECT2(_ct2.Structure):
                _fields_ = [("left", _ct2.c_long), ("top",    _ct2.c_long),
                             ("right",_ct2.c_long), ("bottom", _ct2.c_long)]
            rc = _RECT2()
            if _ct2.windll.user32.SystemParametersInfoW(0x0030, 0, _ct2.byref(rc), 0):
                taskbar_h = screen_h - rc.bottom
                taskbar_h = max(taskbar_h + 8, 8)
        except Exception:
            pass

        MARGIN_SIDE = 8
        y = screen_h - taskbar_h
        for pw in reversed(self._stack):
            h = pw.total_height
            y -= h + STACK_GAP
            x = screen_w - pw.win_width - MARGIN_SIDE if LOCATION == "bottomright" else MARGIN_SIDE
            pw.move_to(x, y)

_stack: PopupStack | None = None

_renderer = SkinRenderer()
_parser   = SkinParser()

class PopupWindow:

    ANIM_MS = 16

    def __init__(self,
                 root:      tk.Tk,
                 title:     str,
                 message:   str,
                 timeout:   int       = DEFAULT_TIMEOUT,
                 color_bg:  str       = COL_BG,
                 color_fg:  str       = COL_FIRST_LINE,
                 color_msg: str       = COL_SECOND_LINE,
                 back_tint: str       = None,
                 skin:      SkinDef   = None,
                 skin_opts: dict      = None,
                 icon_path: str       = None,
                 avatar_path: str     = None,
                 force_avatar: Optional[bool] = None,
                 force_icon:   Optional[bool] = None,
                 force_clock:  Optional[bool] = None,
                 avatar_corner_radius: int = 0,
                 avatar_aa: bool = True,
                 bold_prefix: str = "",
                 ):

        self.root        = root
        self.title       = title
        self.message     = message
        self.timeout     = timeout
        self.color_bg    = color_bg
        self.color_fg    = color_fg
        self.color_msg   = color_msg
        self.back_tint   = back_tint if back_tint is not None else BACK_TINT_COLOR
        self.skin        = skin
        self.skin_opts   = skin_opts or {}
        self.icon_path   = icon_path
        self.avatar_path = avatar_path
        self.force_avatar = force_avatar
        self.force_icon   = force_icon
        self.force_clock  = force_clock
        self.avatar_corner_radius = avatar_corner_radius
        self.avatar_aa = avatar_aa
        self.bold_prefix = bold_prefix

        self._mouse_in  = False
        self._destroyed = False
        self._close_id  = None
        self._anim_id   = None
        self._target_x  = 0
        self._target_y  = 0
        self._photo     = None

        _ff = FONT_FAMILY
        self._fnt_title = tkfont.Font(family=_ff, size=FONT_SIZE, weight="bold")
        self._fnt_body  = tkfont.Font(family=_ff, size=FONT_SIZE)
        self._fnt_time  = tkfont.Font(family=_ff, size=max(7, FONT_SIZE - 1))

        if skin and PIL_OK:
            self._init_with_skin()
        else:
            self._init_no_skin()

        for w in (self.win, self.canvas):
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)
            w.bind("<Button-1>", self._on_click)
            w.bind("<Button-3>", self._on_rclick)

        _stack.add(self)
        self._schedule_close()

    def _init_with_skin(self):
        img = _renderer.render(
            self.skin, self.title, self.message,
            self.skin_opts, self.color_bg, self.color_fg, self.color_msg,
            back_tint=self.back_tint,
            icon_path=self.icon_path, avatar_path=self.avatar_path,
            force_avatar=self.force_avatar,
            force_icon=self.force_icon,
            force_clock=self.force_clock,
            avatar_corner_radius=self.avatar_corner_radius,
            avatar_aa=self.avatar_aa,
            bold_prefix=self.bold_prefix,
        )
        self.win_width    = img.width
        self.total_height = img.height
        self._pil_img     = img
        self._use_layered = _WIN32_LAYERED

        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"{self.win_width}x{self.total_height}+9999+9999")
        self.win.update_idletasks()

        if self._use_layered:
            self._hwnd  = self.win.winfo_id()
            self.canvas = self.win
            _ulw(self._hwnd, self._pil_img)
        else:
            self._use_layered = False
            tr = int(TRANS_KEY[1:3],16)
            tg = int(TRANS_KEY[3:5],16)
            tb = int(TRANS_KEY[5:7],16)
            flat = img.convert("RGBA")
            try:
                import numpy as _np
                arr = _np.array(flat)
                mask = arr[:,:,3] == 0
                arr[mask] = [tr, tg, tb, 255]
                flat = Image.fromarray(arr, "RGBA")
            except ImportError:
                pixels = flat.load()
                for py in range(flat.height):
                    for px in range(flat.width):
                        if pixels[px, py][3] == 0:
                            pixels[px, py] = (tr, tg, tb, 255)

            self.win.attributes("-alpha", OPACITY)
            try:
                self.win.wm_attributes("-transparentcolor", TRANS_KEY)
            except tk.TclError:
                pass

            self.canvas = tk.Canvas(self.win,
                                    width=self.win_width, height=self.total_height,
                                    highlightthickness=0, bd=0, bg=TRANS_KEY)
            self.canvas.pack(fill="both", expand=True)
            self._photo = ImageTk.PhotoImage(flat)
            self.canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def _init_no_skin(self):
        self._calc_height()
        self.win_width = WIN_WIDTH

        sidebar_col   = _darker(self.color_bg, 0.75)
        underline_col = COL_TITLE_UL
        border_col    = COL_BORDER

        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", OPACITY)
        self.win.geometry(f"{WIN_WIDTH}x{self.total_height}+9999+9999")
        self.win.configure(bg=self.color_bg)

        self.canvas = tk.Canvas(self.win,
                                width=WIN_WIDTH, height=self.total_height,
                                highlightthickness=0, bd=0, bg=self.color_bg)
        self.canvas.pack(fill="both", expand=True)
        try:
            self.win.wm_attributes("-transparentcolor", TRANS_KEY)
            self.canvas.configure(bg=TRANS_KEY)
            self.win.configure(bg=TRANS_KEY)
        except tk.TclError:
            pass

        c  = self.canvas
        W, H = WIN_WIDTH, self.total_height
        r  = CORNER_RADIUS if ROUND else 0

        self._rrect(c, 0, 0, W, H, r, fill=self.color_bg, outline="")
        self._rrect(c, 0, 0, SB_WIDTH, H, r, fill=sidebar_col, outline="")
        c.create_rectangle(SB_WIDTH//2, 0, SB_WIDTH, H, fill=sidebar_col, outline="")

        if BORDER:
            self._rrect(c, 0, 0, W, H, r, fill="", outline=border_col)

        tx = PADDING + TEXT_INDENT
        ty = PADDING

        clock_str_now = time.strftime("%H:%M")
        clock_w_px    = self._fnt_time.measure(clock_str_now)
        c.create_text(W-PADDING, ty, text=clock_str_now,
                      font=self._fnt_time, fill=COL_TIME, anchor="ne")

        _icon_xoff = 0
        if self.icon_path and PIL_OK:
            try:
                _ico_raw = Image.open(self.icon_path)
                if hasattr(_ico_raw, "n_frames") and _ico_raw.n_frames > 1:
                    best_idx, best_diff = 0, float("inf")
                    for i in range(_ico_raw.n_frames):
                        _ico_raw.seek(i)
                        w_f, h_f = _ico_raw.size
                        diff = abs(w_f - 16) + abs(h_f - 16)
                        if diff < best_diff:
                            best_diff, best_idx = diff, i
                    _ico_raw.seek(best_idx)
                _ico = _ico_raw.convert("RGBA")
                _ico = _ico.resize((16, 16), Image.LANCZOS)
                self._icon_photo = ImageTk.PhotoImage(_ico)
                c.create_image(tx, ty + self._tb_h // 2, anchor="w", image=self._icon_photo)
                _icon_xoff = 20
            except Exception as _e:
                pass

        title_x    = tx + _icon_xoff
        title_max_w = W - PADDING - clock_w_px - 6 - title_x
        title_max_w = max(title_max_w, 30)
        title_txt   = self.title
        while title_txt and self._fnt_title.measure(title_txt) > title_max_w:
            title_txt = title_txt[:-1]
        if title_txt != self.title:
            while title_txt and self._fnt_title.measure(title_txt + "\u2026") > title_max_w:
                title_txt = title_txt[:-1]
            title_txt = title_txt + "\u2026"
        c.create_text(title_x, ty, text=title_txt, font=self._fnt_title,
                      fill=self.color_fg, anchor="nw")

        uly = ty + self._tb_h + PADDING//2
        c.create_line(SB_WIDTH+PADDING, uly, W-PADDING, uly, fill=underline_col)
        by = uly + 1 + PADDING
        body_max_y = H - PADDING
        bp_len_ns = len(self.bold_prefix) if (self.bold_prefix and self.message.startswith(self.bold_prefix)) else 0
        char_offset_ns = 0
        for i, ln in enumerate(self._body_lines):
            line_y = by + i * self._line_h
            if line_y + self._line_h > body_max_y:
                if i < len(self._body_lines) - 1:
                    trunc = ln
                    avail_w = W - tx - PADDING
                    while trunc and self._fnt_body.measure(trunc + "\u2026") > avail_w:
                        trunc = trunc[:-1]
                    c.create_text(tx, line_y, text=trunc + "\u2026",
                                  font=self._fnt_body, fill=self.color_msg, anchor="nw")
                break
            if bp_len_ns and char_offset_ns < bp_len_ns:
                line_end_ns = char_offset_ns + len(ln)
                if line_end_ns <= bp_len_ns:
                    c.create_text(tx, line_y, text=ln,
                                  font=self._fnt_title, fill=self.color_msg, anchor="nw")
                else:
                    split_ns = bp_len_ns - char_offset_ns
                    bpart_ns = ln[:split_ns]
                    rpart_ns = ln[split_ns:]
                    bw_ns = self._fnt_title.measure(bpart_ns)
                    if bpart_ns:
                        c.create_text(tx, line_y, text=bpart_ns,
                                      font=self._fnt_title, fill=self.color_msg, anchor="nw")
                    if rpart_ns:
                        c.create_text(tx + bw_ns, line_y, text=rpart_ns,
                                      font=self._fnt_body, fill=self.color_msg, anchor="nw")
            else:
                c.create_text(tx, line_y, text=ln,
                          font=self._fnt_body, fill=self.color_msg, anchor="nw")
            char_offset_ns += len(ln) + 1

    def _calc_height(self):
        body_w = WIN_WIDTH - (PADDING + TEXT_INDENT) - PADDING
        self._tb_h = self._fnt_title.metrics("linespace")
        self._tb_h = max(self._tb_h, 16)
        self._line_h = self._fnt_body.metrics("linespace")

        words = self.message.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if self._fnt_body.measure(test) <= body_w:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        self._body_lines = lines or [""]

        total = (PADDING + self._tb_h + PADDING//2 + 1 + PADDING +
                 len(self._body_lines) * self._line_h + PADDING)
        self.total_height = min(total, WIN_MAX_HEIGHT)

    def _rrect(self, c, x1,y1,x2,y2, r, **kw):
        if r <= 0:
            c.create_rectangle(x1,y1,x2,y2, **kw); return
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        c.create_polygon(pts, smooth=True, **kw)

    def move_to(self, x: int, y: int):
        self._target_x, self._target_y = x, y
        if self._anim_id:
            try: self.win.after_cancel(self._anim_id)
            except Exception: pass
            self._anim_id = None
        if ANIMATE:
            self._animate_move()
        else:
            self._move_frame(x, y)
            self.win.deiconify()

    def _move_frame(self, x: int, y: int):
        self.win.geometry(f"+{x}+{y}")
        if getattr(self, '_use_layered', False):
            _ulw(self._hwnd, self._pil_img)

    def _animate_move(self):
        if self._destroyed: return
        try:
            g = self.win.geometry()
            parts = g.replace("x", "+").split("+")
            cx, cy = int(parts[2]), int(parts[3])
        except Exception:
            cx, cy = self._target_x, self._target_y

        dx, dy = self._target_x - cx, self._target_y - cy
        if abs(dx) < 2 and abs(dy) < 2:
            self._anim_id = None
            self._move_frame(self._target_x, self._target_y)
            self.win.deiconify()
            return

        ax = dx//4 or (1 if dx > 0 else -1)
        ay = dy//4 or (1 if dy > 0 else -1)
        self._move_frame(cx + ax, cy + ay)
        self.win.deiconify()
        self._anim_id = self.win.after(self.ANIM_MS, self._animate_move)

    def _on_enter(self, _=None):
        self._mouse_in = True
        if self._close_id:
            self.win.after_cancel(self._close_id)
            self._close_id = None

    def _on_leave(self, _=None):
        self._mouse_in = False
        self._schedule_close(800)

    def _on_click(self,  _=None): self.destroy()
    def _on_rclick(self, _=None): self.destroy()

    def _schedule_close(self, ms=None):
        if self._close_id:
            try: self.win.after_cancel(self._close_id)
            except: pass
        delay = ms if ms is not None else self.timeout * 1000
        self._close_id = self.win.after(delay, self._auto_close)

    def _auto_close(self):
        if self._mouse_in:
            self._schedule_close(800)
        else:
            self.destroy()

    def destroy(self):
        if self._destroyed: return
        self._destroyed = True
        for aid in (self._close_id, self._anim_id):
            if aid:
                try: self.win.after_cancel(aid)
                except: pass
        _stack.remove(self)
        try: self.win.destroy()
        except: pass

_pp_parser = _parser

_pp_stack_global: "_Optional[PopupStack]" = None
_pp_active_windows: list = []
_pp_lock: threading.Lock = threading.Lock()

def _pp_ensure_stack() -> None:
    global _pp_stack_global, _stack
    if _pp_stack_global is None and _tk_root:
        _pp_stack_global = PopupStack(_tk_root)
        _stack = _pp_stack_global

def _push_popupplus_toast(title: str, body: str, url: "_Optional[str]",
                          avatar_png: "_Optional[str]" = None,
                          sound_key: str = "NewMessage",
                          channel_id: "_Optional[str]" = None,
                          author_name: str = "",
                          guild_name: str = "",
                          channel_name: str = "",
                          author_id: str = "") -> None:
    def _do() -> None:
        global _pp_stack_global
        if not _PIL_OK:
            _push_yahoo_toast(title, body, url,
                              avatar_png=avatar_png, sound_key=sound_key,
                              channel_id=channel_id, author_name=author_name,
                              guild_name=guild_name, channel_name=channel_name,
                              author_id=author_id)
            return

        _pp_ensure_stack()
        if _pp_stack_global is None:
            return

        cfg = load_config()
        max_stack  = int(cfg.get("yahoo_max_stack", YAHOO_MAX_STACK))
        skin_folder = cfg.get("pp_skin_folder", "").strip()
        skin_opts   = {int(k): v for k, v in cfg.get("pp_skin_opts", {}).items()}
        color_bg    = cfg.get("pp_color_bg",  "#808080")
        color_fg    = cfg.get("pp_color_fg",  "#FFFFFF")
        color_msg   = cfg.get("pp_color_msg", "#EFEFEF")
        back_tint   = cfg.get("pp_back_tint", "").strip() or None
        av_radius   = int(cfg.get("pp_avatar_radius", 0))
        av_aa       = bool(cfg.get("pp_avatar_aa", True))
        timeout_s   = int(cfg.get("pp_timeout", 7))
        location    = cfg.get("pp_location", "bottomright")
        font_family = cfg.get("pp_font_family", "Segoe UI")
        font_size   = int(cfg.get("pp_font_size", 9))
        force_avatar = bool(cfg.get("pp_force_avatar", True))
        force_icon   = bool(cfg.get("pp_force_icon", True))
        force_clock  = bool(cfg.get("pp_force_clock", False))
        font_aa      = bool(cfg.get("pp_font_aa", True))

        import importlib
        global FONT_FAMILY, FONT_SIZE, FONT_AA, LOCATION, BACK_TINT_COLOR
        global MIN_SKIN_WIDTH, MAX_SKIN_WIDTH, MIN_SKIN_HEIGHT
        FONT_FAMILY     = font_family
        FONT_SIZE       = font_size
        FONT_AA         = font_aa
        LOCATION        = location
        BACK_TINT_COLOR = back_tint
        MIN_SKIN_WIDTH  = int(cfg.get("pp_min_skin_width",  150))
        MAX_SKIN_WIDTH  = int(cfg.get("pp_max_skin_width",  350))
        MIN_SKIN_HEIGHT = int(cfg.get("pp_min_skin_height",  40))

        _pp_stack_global._location = location

        skin = None
        if skin_folder and os.path.isdir(skin_folder):
            try:
                skin = _pp_parser.find_and_parse(skin_folder)
            except Exception as e:
                print(f"[popupplus] Could not parse skin '{skin_folder}': {e}")

        _ck_map = {
            "NewMessage":    "message",
            "NewMention":    "mention",
            "FriendRequest": "friend_request",
            "FriendAccepted":"friend_request",
            "IncomingCall":  "call",
        }
        _ck = _ck_map.get(sound_key, "message")
        compact_icons = cfg.get("compact_icons", {})
        icon_path = compact_icons.get(_ck, "") or None
        if icon_path and not os.path.isfile(icon_path):
            icon_path = None

        avatar_path = avatar_png if (avatar_png and os.path.exists(avatar_png)) else None

        with _pp_lock:
            while len(_pp_active_windows) >= max_stack:
                oldest = _pp_active_windows.pop()
                try:
                    oldest.destroy()
                except Exception:
                    pass

        if guild_name:
            display_title = f"{guild_name}, #{channel_name}" if channel_name else guild_name
        else:
            display_title = cfg.get("toast_default_title", "Discord") or "Discord"
        if author_name and guild_name:
            display_body = f"{author_name}: {body}"
        elif author_name:
            display_body = f"{author_name}: {body}"
        else:
            display_body = body
        bold_prefix = f"{author_name}: " if (author_name and guild_name) else ""

        display_title = _replace_emojis(display_title)
        display_body  = _replace_emojis(display_body)
        bold_prefix   = _replace_emojis(bold_prefix)

        if cfg.get("pp_type_colors_enabled", False):
            _ck_map2 = {
                "NewMessage":    "message",
                "NewMention":    "mention",
                "FriendRequest": "friend_request",
                "FriendAccepted":"friend_request",
                "IncomingCall":  "call",
            }
            _ttype = _ck_map2.get(sound_key, "message")
            _tc = cfg.get("pp_type_colors", {}).get(_ttype, {})
            color_bg  = _tc.get("bg",   "").strip() or color_bg
            color_fg  = _tc.get("fg",   "").strip() or color_fg
            color_msg = _tc.get("body", "").strip() or color_msg
            back_tint = _tc.get("tint", "").strip() or back_tint

        try:
            pw = PopupWindow(
                _tk_root,
                display_title,
                display_body,
                timeout    = timeout_s,
                color_bg   = color_bg,
                color_fg   = color_fg,
                color_msg  = color_msg,
                back_tint  = back_tint,
                skin       = skin,
                skin_opts  = skin_opts,
                icon_path  = icon_path,
                avatar_path = avatar_path,
                force_avatar = force_avatar if avatar_path else False,
                force_icon   = force_icon,
                force_clock  = force_clock,
                avatar_corner_radius = av_radius,
                avatar_aa = av_aa,
                bold_prefix = bold_prefix,
            )
            _orig_destroy = pw.destroy
            def _patched_destroy(pw=pw, orig=_orig_destroy):
                orig()
                with _pp_lock:
                    if pw in _pp_active_windows:
                        _pp_active_windows.remove(pw)
            pw.destroy = _patched_destroy
            pw._channel_id = channel_id

            _TITLE_H = 22

            def _dismiss_same_channel(src_pw=pw):
                cid = getattr(src_pw, "_channel_id", None)
                with _pp_lock:
                    to_close = [w for w in list(_pp_active_windows)
                                if cid and getattr(w, "_channel_id", None) == cid]
                    if src_pw not in to_close:
                        to_close.append(src_pw)
                for w in to_close:
                    try: w.destroy()
                    except Exception: pass

            def _on_body_click(e=None, _url=url, _pw=pw):
                if _url:
                    _open_client(_url)
                _dismiss_same_channel(_pw)

            def _on_title_click(e=None, _pw=pw):
                _pw.destroy()

            def _routed_click(e, _th=_TITLE_H,
                              _body=_on_body_click, _title=_on_title_click):
                if e.y <= _th:
                    _title(e)
                else:
                    _body(e)

            try:
                pw.win.bind("<Button-1>", _routed_click)
                if hasattr(pw, "canvas") and pw.canvas is not pw.win:
                    pw.canvas.bind("<Button-1>", _routed_click)
            except Exception:
                pass

            with _pp_lock:
                _pp_active_windows.insert(0, pw)

        except Exception as e:
            print(f"[popupplus] Failed to create PopupWindow: {e}")
            import traceback
            traceback.print_exc()

    if _tk_root:
        _tk_root.after(0, _do)

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

def _dismiss_balloon() -> None:
    global _balloon_dismiss_timer
    _balloon_dismiss_timer = None
    if not (_nid and _hwnd):
        return
    try:
        tmp = NOTIFYICONDATAW()
        tmp.cbSize    = ctypes.sizeof(NOTIFYICONDATAW)
        tmp.hWnd      = _hwnd
        tmp.uID       = _nid.uID
        tmp.uFlags    = NIF_INFO
        tmp.szInfo    = ""
        tmp.szInfoTitle = ""
        tmp.dwInfoFlags = NIIF_NOSOUND
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(tmp))
        print("[balloon] Auto-dismissed")
    except Exception as e:
        print(f"[balloon] Dismiss error: {e}")

def _raw_show_balloon(title: str, body: str, url: "str | None",
                      suppress_sound: bool = False,
                      sound_key: str = "NewMessage",
                      channel_id: "str | None" = None,
                      author_name: str = "",
                      guild_name: str = "",
                      channel_name: str = "",
                      author_id: str = "") -> None:

    global _last_balloon_url, _avatar_hicon, _pending_avatar_png
    global _balloon_dismiss_timer, _last_balloon_channel_id
    global _balloon_sent, _balloon_visible
    _notif_type_cfg = load_config().get("notif_type", "popup" if load_config().get("use_yahoo_toast", False) else "balloon")
    if _notif_type_cfg == "popupplus":
        _push_popupplus_toast(title, body, url,
                              avatar_png=_pending_avatar_png,
                              sound_key=sound_key,
                              channel_id=channel_id,
                              author_name=author_name,
                              guild_name=guild_name,
                              channel_name=channel_name,
                              author_id=author_id)
        _pending_avatar_png = None
        _last_balloon_url = url
        _last_balloon_channel_id = channel_id
        _balloon_sent = True
        if _balloon_dismiss_timer:
            _balloon_dismiss_timer.cancel()
            _balloon_dismiss_timer = None
        return
    if _notif_type_cfg == "popup":
        _push_yahoo_toast(title, body, url,
                          avatar_png=_pending_avatar_png,
                          sound_key=sound_key,
                          channel_id=channel_id,
                          author_name=author_name,
                          guild_name=guild_name,
                          channel_name=channel_name,
                          author_id=author_id)
        _pending_avatar_png = None
        _last_balloon_url = url
        _last_balloon_channel_id = channel_id
        _balloon_sent = True
        if _balloon_dismiss_timer:
            _balloon_dismiss_timer.cancel()
            _balloon_dismiss_timer = None
        return
    if not (_nid and _hwnd):
        return
    _last_balloon_url      = url
    _last_balloon_channel_id = channel_id

    if _balloon_dismiss_timer:
        _balloon_dismiss_timer.cancel()
        _balloon_dismiss_timer = None

    if _balloon_sent or _balloon_visible:
        try:
            tmp = NOTIFYICONDATAW()
            tmp.cbSize      = ctypes.sizeof(NOTIFYICONDATAW)
            tmp.hWnd        = _hwnd
            tmp.uID         = _nid.uID
            tmp.uFlags      = NIF_INFO
            tmp.szInfo      = ""
            tmp.szInfoTitle = ""
            tmp.dwInfoFlags = NIIF_NOSOUND
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(tmp))
            time.sleep(0.05)
        except Exception as _e:
            print(f"[balloon] Pre-dismiss error: {_e}")

    _balloon_sent    = False
    _balloon_visible = False

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
    _nid.szInfoTitle     = _replace_emojis(title)[:63]
    _nid.szInfo          = _replace_emojis(body)[:255]
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
    _balloon_sent = True

    timeout_sec = int(load_config().get("balloon_timeout", 0))
    if timeout_sec > 0:
        _balloon_dismiss_timer = threading.Timer(timeout_sec, _dismiss_balloon)
        _balloon_dismiss_timer.daemon = True
        _balloon_dismiss_timer.start()

def _style_instant(title: str, body: str, url: "str | None",
                   sound_key: str = "NewMessage",
                   channel_id: "str | None" = None,
                   author_name: str = "",
                   guild_name: str = "",
                   channel_name: str = "",
                   author_id: str = "") -> None:
    _raw_show_balloon(title, body, url, sound_key=sound_key, channel_id=channel_id,
                      author_name=author_name, guild_name=guild_name, channel_name=channel_name,
                      author_id=author_id)

def _style_replace(title: str, body: str, url: "str | None",
                   sound_key: str = "NewMessage",
                   channel_id: "str | None" = None,
                   author_name: str = "",
                   guild_name: str = "",
                   channel_name: str = "",
                   author_id: str = "") -> None:
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
        _raw_show_balloon(title, body, url, sound_key=sound_key, channel_id=channel_id,
                          author_name=author_name, guild_name=guild_name, channel_name=channel_name,
                          author_id=author_id)
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
                                  sound_key=pend.sound_key, channel_id=channel_id,
                                  author_name=author_name, guild_name=guild_name, channel_name=channel_name,
                                  author_id=author_id)

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
                     sound_key: str = "NewMessage",
                     author_name: str = "",
                     guild_name: str = "",
                     channel_name: str = "",
                     author_id: str = "") -> None:
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
                 channel_id: "str | None" = None,
                 author_name: str = "",
                 guild_name: str = "",
                 channel_name: str = "",
                 author_id: str = "") -> bool:
    global _has_unread
    if is_system:
        _raw_show_balloon(title, body, url, suppress_sound=True,
                          sound_key=sound_key,
                          author_name=author_name, guild_name=guild_name, channel_name=channel_name)
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
        _style_replace(title, body, url, sound_key=sound_key, channel_id=channel_id,
                       author_name=author_name, guild_name=guild_name, channel_name=channel_name,
                       author_id=author_id)
    elif style == "queue":
        _style_queue_add(title, body, url, sound_key=sound_key,
                         author_name=author_name, guild_name=guild_name, channel_name=channel_name,
                         author_id=author_id)
    else:
        _style_instant(title, body, url, sound_key=sound_key, channel_id=channel_id,
                       author_name=author_name, guild_name=guild_name, channel_name=channel_name,
                       author_id=author_id)
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
        _unread_channel_info.clear()
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
    global _balloon_visible, _balloon_sent, _balloon_pending_sound, _balloon_pending_key
    try:
        if WM_TASKBARCREATED and msg == WM_TASKBARCREATED:
            print("[tray] TaskbarCreated received — re-adding tray icon")
            if _nid:
                shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(_nid))
                _update_tray_icon_for_state()
            return 0

        if msg == WM_DEVICECHANGE:
            threading.Thread(target=_reinit_audio_device, daemon=True).start()
            return 1

        if msg == WM_TRAYICON:
            event = lparam & 0xFFFF

            if event == NIN_BALLOONSHOW:
                _balloon_visible = True

            elif event == NIN_BALLOONUSERCLICK:
                _balloon_visible       = False
                _balloon_sent          = False
                _balloon_pending_sound = False
                _restore_tray_icon() 
                _open_balloon_url()

            elif event == NIN_BALLOONHIDE:
                if load_config().get("notif_style", "instant") != "queue":
                    _balloon_visible = False
                _balloon_sent = False
                _restore_tray_icon()

            elif event == NIN_BALLOONTIMEOUT:
                _balloon_visible = False
                _balloon_sent    = False
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
    global _hwnd, _nid, _wnd_proc_ref, WM_TASKBARCREATED

    WM_TASKBARCREATED = user32.RegisterWindowMessageW("TaskbarCreated")
    print(f"[tray] WM_TASKBARCREATED = {WM_TASKBARCREATED:#06x}")

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

    try:
        MSGFLT_ALLOW = 1
        user32.ChangeWindowMessageFilterEx(_hwnd, WM_TASKBARCREATED,
                                           MSGFLT_ALLOW, None)
    except Exception:
        pass

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
                             channel_id: str | None) -> tuple[str, str, int]:
    channel_name = guild_name = ""
    channel_type = -1
    try:
        if channel_id:
            async with http.get(f"{DISCORD_API}/channels/{channel_id}",
                                headers={"Authorization": token}) as r:
                if r.status == 200:
                    ch_data      = await r.json()
                    channel_name = ch_data.get("name", "")
                    channel_type = ch_data.get("type", -1)
        if guild_id:
            async with http.get(f"{DISCORD_API}/guilds/{guild_id}",
                                headers={"Authorization": token}) as r:
                if r.status == 200:
                    guild_name = (await r.json()).get("name", "")
    except Exception:
        pass
    return channel_name, guild_name, channel_type

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
    _persistent_user_id: str | None = None

    _CLEAN_DISCONNECT = object()
    _disconnect_reason: object = None

    while True:
        zlib_ctx        = zlib.decompressobj()
        buffer          = bytearray()
        my_user_id:     str | None = _persistent_user_id
        heartbeat_task: asyncio.Task | None = None
        channel_cache:  dict[str, tuple[str, str, int]] = {}
        nick_cache:     dict[tuple, str] = {}
        _disconnect_reason = None

        ack_times:      dict[str, float] = {}

        try:
            async with aiohttp.ClientSession() as http:
                connect_url = (
                    (resume_url + "?v=9&encoding=json&compress=zlib-stream")
                    if (session_id and resume_url) else GATEWAY_URL
                )
                async with websockets.connect(connect_url, max_size=None, close_timeout=5) as ws:
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

                    _hb_ack_received = True

                    async def heartbeat():
                        nonlocal sequence, _hb_ack_received
                        while True:
                            await asyncio.sleep(heartbeat_interval)
                            if not _hb_ack_received:
                                print("[gateway] Heartbeat ACK not received — closing dead connection.")
                                _disconnect_reason = _CLEAN_DISCONNECT
                                await ws.close(code=4000)
                                return
                            _hb_ack_received = False
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

                        if op == 11:
                            _hb_ack_received = True
                            continue

                        if op == 7:
                            print("[gateway] Reconnect requested.")
                            _disconnect_reason = _CLEAN_DISCONNECT
                            if heartbeat_task and not heartbeat_task.done():
                                heartbeat_task.cancel()
                            break

                        if op == 9:
                            can_resume = bool(d) if isinstance(d, bool) else False
                            if not can_resume:
                                session_id = None
                                sequence   = None
                                print("[gateway] Session invalidated, will re-identify.")
                            else:
                                print("[gateway] Session invalid but Discord says retry.")
                            _disconnect_reason = _CLEAN_DISCONNECT
                            await asyncio.sleep(1)
                            break

                        if t == "READY":
                            user       = d.get("user", {})
                            my_user_id = user.get("id")
                            _persistent_user_id = my_user_id
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
                                    f"{DISCORD_API}/users/@me/mentions?limit=25&roles=true&everyone=true",
                                    headers={"Authorization": token},
                                ) as r:
                                    if r.status == 200:
                                        mentions = await r.json()
                                        for msg in mentions:
                                            ch_id   = msg.get("channel_id")
                                            gld_id  = msg.get("guild_id") or ""
                                            msg_id  = str(msg.get("id", "0"))
                                            if not ch_id or ch_id in muted_channels:
                                                continue
                                                                                                       
                                            already_read_up_to = last_read.get(ch_id, "0")
                                            if msg_id > already_read_up_to:
                                                _unread_channels.add(ch_id)
                                                if ch_id not in _unread_channel_info:
                                                    _author = msg.get("author", {})
                                                    _content = msg.get("content", "")[:80]
                                                    if gld_id:
                                                        _url = f"discord://-/channels/{gld_id}/{ch_id}"
                                                    else:
                                                        _url = f"discord://-/channels/@me/{ch_id}"
                                                    _unread_channel_info[ch_id] = {
                                                        "guild_id":     gld_id,
                                                        "channel_name": "",
                                                        "guild_name":   "",
                                                        "url":          _url,
                                                        "last_author":  _author.get("username", ""),
                                                        "last_content": _content,
                                                    }
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
                            if not load_config().get("suppress_connect_notif", False):
                                show_balloon(_t("balloon_connected"), _t("balloon_signed_in", name=name), is_system=True)
                            if load_config().get("auto_open_client", False):
                                _tk_root.after(1500, _open_client)
                            continue

                        if t == "RESUMED":
                            if _persistent_user_id and not my_user_id:
                                my_user_id = _persistent_user_id
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
                                    _update_tray_icon_for_state()
                            continue

                        if t == "USER_SETTINGS_PROTO_UPDATE":
                            new_stat = await _fetch_user_status(http, token)
                            _my_status = new_stat
                            print(f"[gateway] Settings updated, status now: {_my_status}")
                            _update_tray_icon_for_state()
                            continue

                        if t == "RELATIONSHIP_ADD":
                            if d.get("type") == 3:
                                u    = d.get("user", {})
                                who  = u.get("global_name") or u.get("username", "Someone")
                                print(f"[msg] Friend request from {who}")
                                show_balloon(_t("balloon_friend_req"), _t("balloon_friend_body", who=who),
                                             is_system=True, sound_key="FriendRequest")
                                _play_notification_sound("FriendRequest")
                            elif d.get("type") == 1:
                                u   = d.get("user", {})
                                who = u.get("global_name") or u.get("username", "Someone")
                                print(f"[msg] Friend request accepted by {who}")
                                _play_notification_sound("FriendAccepted")
                            continue

                        if t == "RELATIONSHIP_REMOVE":
                            continue

                        if t == "VOICE_STATE_UPDATE":
                            global _vc_guild_id, _vc_channel_id, _vc_self_mute, _vc_self_deaf, _vc_self_stream, _vc_self_video, _active_call_channel_id, _outgoing_call_channel_id, _outgoing_call_time

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
                                prev_stream  = _vc_self_stream
                                prev_video   = _vc_self_video

                                _vc_guild_id    = d.get("guild_id")
                                _vc_channel_id  = d.get("channel_id") 
                                _vc_self_mute   = bool(d.get("self_mute", False))
                                _vc_self_deaf   = bool(d.get("self_deaf", False))
                                _vc_self_stream = bool(d.get("self_stream", False))
                                _vc_self_video  = bool(d.get("self_video", False))

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

                                    if _vc_self_stream and not prev_stream:
                                        print("[vc] Started streaming")
                                        _play_notification_sound("StartStream")
                                    elif not _vc_self_stream and prev_stream:
                                        print("[vc] Stopped streaming")
                                        _play_notification_sound("StopStream")
                                    elif _vc_self_video and not prev_video:
                                        print("[vc] Video on")
                                        _play_notification_sound("VideoOn")
                                    elif not _vc_self_video and prev_video:
                                        print("[vc] Video off")
                                        _play_notification_sound("VideoOff")
                                    elif _vc_self_deaf and not prev_deaf:
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
                                        stream_str = " (streaming)" if _vc_self_stream else ""
                                        mute_str   = " (muted)"    if _vc_self_mute   else ""
                                        deaf_str   = " (deafened)" if _vc_self_deaf   else ""
                                        print(f"[vc] State updated{stream_str}{mute_str}{deaf_str}")

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
                                show_balloon(_t("balloon_incoming"), _t("balloon_calling", caller=caller), url=url,
                                             sound_key="IncomingCall")
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
                                if ack_ch == _last_balloon_channel_id and _balloon_visible:
                                    _dismiss_balloon()
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
                            ch_id  = item.get("channel_id")
                            gld_id = item.get("guild_id") or ""
                            if ch_id and ch_id not in muted_channels:
                                if ch_id not in _unread_channel_info:
                                    if gld_id:
                                        _nc_url = f"discord://-/channels/{gld_id}/{ch_id}"
                                    else:
                                        _nc_url = f"discord://-/channels/@me/{ch_id}"
                                    _unread_channel_info[ch_id] = {
                                        "guild_id":    gld_id,
                                        "channel_name": "",
                                        "guild_name":   "",
                                        "url":          _nc_url,
                                        "last_author":  "",
                                        "last_content": "",
                                    }
                                print(f"[gateway] NOTIFICATION_CENTER: item for {ch_id} (unread tracking via MESSAGE_CREATE only)")
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
                        _msg_type = d.get("type", 0)
                        if _msg_type not in {0, 19}:
                            print(f"[msg] Skipped system message type={_msg_type}")
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

                        if guild_id and channel_id in channel_cache:
                            _ch_name, _gn, _ch_type = channel_cache[channel_id]
                        else:
                            _ch_type = -1
                        _VC_TEXT_TYPES = {2, 13}
                        if _ch_type in _VC_TEXT_TYPES and channel_id != _vc_channel_id:
                            print(f"[msg] Skipping text-in-VC message (channel {channel_id}, not in that VC)")
                            continue

                        notif_style = load_config().get("notif_style", "instant")
                        _ch_name = ""
                        _gn = ""
                        if guild_id and channel_id in channel_cache:
                            _ch_name, _gn, _ = channel_cache[channel_id]

                        if notif_style == "queue":

                            verb = " replied" if is_reply else " wrote"
                            if guild_id:
                                in_part = f" in #{_ch_name}" if _ch_name else ""
                                title = f"{name}{verb}{in_part}"
                            else:
                                title = f"{name}{verb}"
                        else:
                            if guild_id:
                                ctx   = []
                                if _ch_name: ctx.append(f"#{_ch_name}")
                                if _gn:      ctx.append(_gn)
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

                        was_suppressed = show_balloon(title, content, url=url,
                                     channel_id=channel_id,
                                     sound_key="NewMention" if _was_mentioned(d, my_user_id) else "NewMessage",
                                     author_name=name,
                                     guild_name=_gn,
                                     channel_name=_ch_name,
                                     author_id=author.get("id", ""))

                        if not was_suppressed:
                            _unread_channels.add(channel_id)
                            _has_unread = True
                            _update_tray_icon_for_state()
                            _unread_channel_info[channel_id] = {
                                "guild_id":    guild_id or "",
                                "channel_name": _ch_name,
                                "guild_name":   _gn,
                                "url":          url,
                                "last_author":  name,
                                "last_content": content[:80] if content else "",
                            }
                        if guild_id:
                            _ch_info = channel_cache.get(channel_id, ("", "", -1))
                            _unread_label = f"#{_ch_info[0] or channel_id} in {_ch_info[1] or guild_id}"
                        else:
                            _unread_label = f"DM (channel_id={channel_id})"
                        print(f"[unread] {'suppressed' if was_suppressed else '+'}{_unread_label} from {name} → {len(_unread_channels)} unread channel(s)")

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
            err_str = str(e)
            if "no close frame" in err_str or "ConnectionClosed" in type(e).__name__:
                print(f"[gateway] Connection lost: {e}")
            else:
                print(f"[gateway] Error: {e}")
        finally:
            _gw_ws = None
            if heartbeat_task:
                heartbeat_task.cancel()

        if _disconnect_reason is _CLEAN_DISCONNECT:
            print("[gateway] Reconnecting...")
        else:
            _raw_show_balloon("Ballooncord", "Reconnecting...", None, suppress_sound=True)
            print("[gateway] Retrying in 5 seconds...")
            await asyncio.sleep(5)

TOAST_TRANSPARENT = "#FF00FF"
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
        xp_button(toolbar, "Unread Channels", self._show_unread, width=16).pack(side=tk.LEFT, padx=(0, 4), pady=2)

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

    def _show_unread(self) -> None:
        dlg = tk.Toplevel(self.win)
        dlg.title("Unread Channels (debug)")
        dlg.geometry("540x360")
        dlg.configure(bg=CMD_BG)
        dlg.grab_set()

        hdr = tk.Label(dlg,
                       text=f"Tracked unread: {len(_unread_channels)}  |  _has_unread = {_has_unread}",
                       bg=CMD_BG, fg=CMD_CYAN, font=CMD_FONT, anchor=tk.W)
        hdr.pack(fill=tk.X, padx=6, pady=(6, 2))

        list_outer = tk.Frame(dlg, bg=CMD_BG, bd=2, relief=tk.SUNKEN)
        list_outer.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        canvas = tk.Canvas(list_outer, bg=CMD_BG, highlightthickness=0)
        sb = tk.Scrollbar(list_outer, command=canvas.yview,
                          bg=XP_FACE, troughcolor=XP_FACE_DARK, relief=tk.FLAT)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas, bg=CMD_BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        inner.bind("<Configure>", lambda e: (canvas.configure(scrollregion=canvas.bbox("all")),
                                              canvas.itemconfig(win_id, width=canvas.winfo_width())))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        def _mw_unread(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except tk.TclError:
                pass
        canvas.bind_all("<MouseWheel>", _mw_unread)
        canvas.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        def _refresh_list():
            for w in inner.winfo_children():
                w.destroy()
            hdr.configure(text=f"Tracked unread: {len(_unread_channels)}  |  _has_unread = {_has_unread}")
            if not _unread_channels:
                tk.Label(inner, text="  (no unread channels)", bg=CMD_BG,
                         fg=CMD_DARKGREY, font=CMD_FONT).pack(anchor=tk.W, padx=6, pady=4)
                return
            for ch_id in sorted(_unread_channels):
                info = _unread_channel_info.get(ch_id, {})
                ch_name   = info.get("channel_name", "")
                gn        = info.get("guild_name", "")
                last_auth = info.get("last_author", "")
                last_msg  = info.get("last_content", "")
                url       = info.get("url", "")
                if not url:
                    url = f"discord://-/channels/@me/{ch_id}"

                if ch_name and gn:
                    display = f"#{ch_name}  ({gn})"
                elif ch_name:
                    display = f"#{ch_name}"
                elif gn:
                    display = f"DM / {gn}"
                else:
                    display = f"channel {ch_id}"

                row = tk.Frame(inner, bg=CMD_BG, bd=0)
                row.pack(fill=tk.X, padx=4, pady=3)

                if url:
                    def _open_ch(u=url, cid=ch_id):
                        _open_client(u)
                    open_btn = xp_button(row, "Open", _open_ch, width=6)
                    open_btn.configure(font=("Tahoma", 7))
                    open_btn.pack(side=tk.LEFT, padx=(0, 6))

                ch_lbl = tk.Label(row, text=display, bg=CMD_BG, fg=CMD_GREEN,
                                  font=CMD_FONT, anchor=tk.W)
                ch_lbl.pack(side=tk.LEFT)

                if last_auth or last_msg:
                    preview = f"{last_auth}: {last_msg}" if last_auth else last_msg
                    if len(preview) > 60:
                        preview = preview[:57] + "…"
                    tk.Label(row, text=f"  ← {preview}", bg=CMD_BG,
                             fg=CMD_DARKGREY, font=("Lucida Console", 8),
                             anchor=tk.W).pack(side=tk.LEFT)

        _refresh_list()

        btn_row = tk.Frame(dlg, bg=CMD_BG)
        btn_row.pack(fill=tk.X, padx=6, pady=(0, 6))
        xp_button(btn_row, "Close", dlg.destroy, width=10).pack(side=tk.RIGHT)
        xp_button(btn_row, "Refresh", _refresh_list, width=10).pack(side=tk.RIGHT, padx=(0, 4))
        xp_button(btn_row, "Clear All (debug)", lambda: self._debug_clear_unread(_refresh_list, hdr), width=16).pack(side=tk.RIGHT, padx=(0, 4))

    def _debug_clear_unread(self, refresh_fn, hdr: tk.Label) -> None:
        global _has_unread
        _unread_channels.clear()
        _unread_channel_info.clear()
        _has_unread = False
        _update_tray_icon_for_state()
        refresh_fn()
        print("[debug] Unread channels cleared manually from log window")

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
        _timeout_raw        = int(self._cfg.get("balloon_timeout", 0))
        self._timeout_var   = tk.IntVar(value=_timeout_raw)
        self._timeout_lbl   = tk.StringVar(value=("Never" if _timeout_raw == 0 else f"{_timeout_raw}s"))
        _vol                = int(self._cfg.get("sound_volume", 1.0) * 100)
        self._vol_var       = tk.IntVar(value=_vol)
        self._vol_label_var = tk.StringVar(value=f"{_vol}%")
        self._sound_vars: dict[str, tk.StringVar] = {}
        self._icon_vars:  dict[str, tk.StringVar] = {}
        self._user_sound_entries: list[dict] = []
        self._grad_start_var = tk.StringVar(value=self._cfg.get("toast_gradient_start", "#0058CE"))
        self._grad_end_var = tk.StringVar(value=self._cfg.get("toast_gradient_end", "#2B93FF"))
        self._body_border_var = tk.StringVar(value=self._cfg.get("toast_body_border_color", "#808080"))
        self._toast_anim_style_var = tk.StringVar(value=self._cfg.get("toast_anim_style", "simple"))
        _speed_raw = int(self._cfg.get("toast_anim_speed", 3))
        self._toast_anim_speed_var = tk.IntVar(value=_speed_raw)
        _speed_labels = {1: "Muy rápida", 2: "Rápida", 3: "Normal", 4: "Lenta", 5: "Muy lenta"}
        self._toast_anim_speed_lbl = tk.StringVar(value=_speed_labels.get(_speed_raw, "Normal"))
        self._toast_default_title_var = tk.StringVar(value=self._cfg.get("toast_default_title", "Discord"))
        self._suppress_connect_var = tk.BooleanVar(value=bool(self._cfg.get("suppress_connect_notif", False)))

        self._toast_display_mode_var = tk.StringVar(value=self._cfg.get("toast_display_mode", "normal"))
        _compact_icons_cfg = self._cfg.get("compact_icons", {})
        self._compact_icon_vars: dict[str, tk.StringVar] = {
            "message":        tk.StringVar(value=_compact_icons_cfg.get("message", "")),
            "mention":        tk.StringVar(value=_compact_icons_cfg.get("mention", "")),
            "friend_request": tk.StringVar(value=_compact_icons_cfg.get("friend_request", "")),
            "call":           tk.StringVar(value=_compact_icons_cfg.get("call", "")),
        }
        _max_stack_raw = int(self._cfg.get("yahoo_max_stack", YAHOO_MAX_STACK))
        self._max_stack_var = tk.IntVar(value=_max_stack_raw)
        self._max_stack_lbl = tk.StringVar(value=f"{_max_stack_raw} toasts")

        self._tray_status_icons_var = tk.BooleanVar(value=bool(self._cfg.get("tray_status_icons_enabled", False)))
        _status_icons_cfg = self._cfg.get("status_icons", {})
        self._status_icon_vars: dict[str, tk.StringVar] = {
            "online":    tk.StringVar(value=_status_icons_cfg.get("online", "")),
            "dnd":       tk.StringVar(value=_status_icons_cfg.get("dnd", "")),
            "idle":      tk.StringVar(value=_status_icons_cfg.get("idle", "")),
            "invisible": tk.StringVar(value=_status_icons_cfg.get("invisible", "")),
        }

        self._build()
        self._center(580, 500)
        self._notif_type_var.trace_add("write", self._refresh_style_tab)

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
        container = tk.Frame(parent, bg=XP_FACE)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=XP_FACE, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview,
                                 bg=XP_FACE, troughcolor=XP_FACE_DARK, relief=tk.FLAT)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas, bg=XP_FACE)
        win_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

        def _on_inner_configure(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        parent = inner

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

        type_grp = tk.LabelFrame(parent, text=" Notification Type ",
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        type_grp.pack(fill=tk.X, padx=4, pady=(0, 8))

        _notif_type_raw = self._cfg.get("notif_type", "")
        if _notif_type_raw == "popupplus":
            _notif_type_init = "popupplus"
        elif _notif_type_raw == "popup" or self._cfg.get("use_yahoo_toast", False):
            _notif_type_init = "popup"
        else:
            _notif_type_init = "balloon"
        self._notif_type_var = tk.StringVar(value=_notif_type_init)

        tk.Radiobutton(type_grp, text="Windows native balloons",
                       variable=self._notif_type_var, value="balloon",
                       bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                       activebackground=XP_FACE, activeforeground=XP_TEXT,
                       font=XP_FONT_BOLD, anchor=tk.W,
                       ).pack(fill=tk.X, padx=10, pady=(8, 0))
        tk.Label(type_grp, text="Use the standard Windows tray balloon notifications.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 4))

        tk.Radiobutton(type_grp, text="Popup toasts (sliding windows)",
                       variable=self._notif_type_var, value="popup",
                       bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                       activebackground=XP_FACE, activeforeground=XP_TEXT,
                       font=XP_FONT_BOLD, anchor=tk.W,
                       ).pack(fill=tk.X, padx=10, pady=(8, 0))
        tk.Label(type_grp, text="Show retro-style popup windows that slide up from behind the taskbar.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 4))

        tk.Radiobutton(type_grp, text="PopupPlus skin  (Miranda NG .popupskin)",
                       variable=self._notif_type_var, value="popupplus",
                       bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                       activebackground=XP_FACE, activeforeground=XP_TEXT,
                       font=XP_FONT_BOLD, anchor=tk.W,
                       ).pack(fill=tk.X, padx=10, pady=(4, 0))
        tk.Label(type_grp, text="Render notifications using a .popupskin file (Miranda NG / Popup Plus format).\nRequires Pillow. Configure the skin folder in the Style tab.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

        style_grp = tk.LabelFrame(parent, text=_t("grp_notif_style"),
                            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                            bd=2, relief=tk.GROOVE)
        style_grp.pack(fill=tk.X, padx=4, pady=(8, 4))

        for val, title, desc in [
            ("instant", _t("style_instant_title"), _t("style_instant_desc")),
            ("replace", _t("style_replace_title"), _t("style_replace_desc")),
            ("queue",   _t("style_queue_title"),   _t("style_queue_desc")),
        ]:
            tk.Radiobutton(style_grp, text=title, variable=self._style_var, value=val,
                           bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                           activebackground=XP_FACE, activeforeground=XP_TEXT,
                           font=XP_FONT_BOLD, anchor=tk.W,
                           ).pack(fill=tk.X, padx=10, pady=(8, 0))
            tk.Label(style_grp, text=desc, bg=XP_FACE, fg=XP_GREY_TXT,
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

        dismiss_grp = tk.LabelFrame(parent, text="Balloon Auto-Dismiss",
                                    bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                    bd=2, relief=tk.GROOVE)
        dismiss_grp.pack(fill=tk.X, padx=4, pady=(0, 8))

        def _on_timeout_change(val):
            v = int(float(val))
            self._timeout_lbl.set("Never" if v == 0 else f"{v}s")

        d_row = tk.Frame(dismiss_grp, bg=XP_FACE)
        d_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(d_row, "Dismiss after:").pack(side=tk.LEFT)
        tk.Scale(d_row, from_=0, to=60, orient=tk.HORIZONTAL,
                 variable=self._timeout_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=180,
                 command=_on_timeout_change,
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(d_row, textvariable=self._timeout_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=5,
                 ).pack(side=tk.LEFT)
        tk.Label(dismiss_grp,
                 text="0 = never force-close. Also dismisses instantly\nif you read the channel that sent the message.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 6))
    def _build_style_page(self, parent: tk.Frame) -> None:
        _sc = tk.Frame(parent, bg=XP_FACE)
        _sc.pack(fill=tk.BOTH, expand=True)
        _canvas = tk.Canvas(_sc, bg=XP_FACE, highlightthickness=0)
        _sb = tk.Scrollbar(_sc, orient=tk.VERTICAL, command=_canvas.yview,
                           bg=XP_FACE, troughcolor=XP_FACE_DARK, relief=tk.FLAT)
        _canvas.configure(yscrollcommand=_sb.set)
        _sb.pack(side=tk.RIGHT, fill=tk.Y)
        _canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _inner = tk.Frame(_canvas, bg=XP_FACE)
        _win_id = _canvas.create_window((0, 0), window=_inner, anchor=tk.NW)
        _inner.bind("<Configure>", lambda e: (_canvas.configure(scrollregion=_canvas.bbox("all")),
                                               _canvas.itemconfig(_win_id, width=_canvas.winfo_width())))
        _canvas.bind("<Configure>", lambda e: _canvas.itemconfig(_win_id, width=e.width))
        def _style_mousewheel(event):
            try:
                _canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        _canvas.bind_all("<MouseWheel>", _style_mousewheel)
        _canvas.bind("<Destroy>", lambda e: _canvas.unbind_all("<MouseWheel>"))
        parent = _inner

        self._style_inner = parent
        self._style_canvas = _canvas

        self._build_style_content(parent)

    def _build_style_content(self, parent: tk.Frame) -> None:
        for w in parent.winfo_children():
            w.destroy()

        ntype = self._notif_type_var.get()

        if ntype == "popupplus":
            self._build_style_popupplus(parent)
        else:
            self._build_style_yahoo(parent)

    def _refresh_style_tab(self, *_):
        if hasattr(self, "_style_inner"):
            self._build_style_content(self._style_inner)

    def _build_style_popupplus(self, parent: tk.Frame) -> None:
        cfg = self._cfg

        skin_grp = tk.LabelFrame(parent, text=" PopupPlus Skin Folder ",
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        skin_grp.pack(fill=tk.X, padx=4, pady=(8, 4))

        if not hasattr(self, "_pp_skin_folder_var"):
            self._pp_skin_folder_var = tk.StringVar(value=cfg.get("pp_skin_folder", ""))
            self._pp_skin_opts = {int(k): v for k, v in cfg.get("pp_skin_opts", {}).items()}
            self._pp_skin_obj = None

        skin_row = tk.Frame(skin_grp, bg=XP_FACE)
        skin_row.pack(fill=tk.X, padx=10, pady=6)
        self._pp_skin_lbl = tk.Label(skin_row,
            text=self._pp_skin_folder_var.get() or "(no skin selected)",
            bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
            anchor=tk.W, wraplength=280, justify=tk.LEFT)
        self._pp_skin_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _browse_skin():
            from tkinter import filedialog
            folder = filedialog.askdirectory(
                parent=self.win, title="Select PopupPlus skin folder", mustexist=True)
            if not folder:
                fpath = filedialog.askopenfilename(
                    parent=self.win,
                    title="Or select a .popupskin file",
                    filetypes=[("Popup Plus Skin", "*.popupskin"), ("All files", "*.*")])
                if fpath:
                    folder = os.path.dirname(fpath)
            if folder:
                self._pp_skin_folder_var.set(folder)
                self._pp_skin_lbl.config(text=folder, fg=XP_TEXT)
                self._pp_load_skin()

        def _clear_skin():
            self._pp_skin_folder_var.set("")
            self._pp_skin_obj = None
            self._pp_skin_opts = {}
            self._pp_skin_lbl.config(text="(no skin selected)", fg=XP_GREY_TXT)
            for w in opts_frame.winfo_children():
                w.destroy()

        btn_row = tk.Frame(skin_grp, bg=XP_FACE)
        btn_row.pack(fill=tk.X, padx=10, pady=(0, 6))
        xp_button(btn_row, "Browse…", _browse_skin, width=10).pack(side=tk.LEFT)
        xp_button(btn_row, "✕ Clear", _clear_skin, width=8).pack(side=tk.LEFT, padx=(4, 0))

        opts_frame = tk.Frame(skin_grp, bg=XP_FACE)
        opts_frame.pack(fill=tk.X, padx=10, pady=(0, 4))
        self._pp_opts_frame = opts_frame
        self._pp_opt_vars: dict = {}

        if self._pp_skin_obj:
            self._pp_build_opts_ui()

        dim_grp = tk.LabelFrame(parent, text=" Skin Dimensions ",
                                bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                bd=2, relief=tk.GROOVE)
        dim_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        if not hasattr(self, "_pp_min_w_var"):
            self._pp_min_w_var = tk.IntVar(value=int(cfg.get("pp_min_skin_width", 150)))
            self._pp_max_w_var = tk.IntVar(value=int(cfg.get("pp_max_skin_width", 350)))
            self._pp_min_h_var = tk.IntVar(value=int(cfg.get("pp_min_skin_height", 40)))

        dim_row1 = tk.Frame(dim_grp, bg=XP_FACE)
        dim_row1.pack(fill=tk.X, padx=10, pady=4)
        xp_label(dim_row1, "Min width:").pack(side=tk.LEFT)
        tk.Spinbox(dim_row1, from_=50, to=600, textvariable=self._pp_min_w_var,
                   width=5, bg=XP_WHITE, fg=XP_TEXT, relief=tk.FLAT,
                   font=("Tahoma", 8)).pack(side=tk.LEFT, padx=(4, 12))
        xp_label(dim_row1, "Max width:").pack(side=tk.LEFT)
        tk.Spinbox(dim_row1, from_=100, to=1200, textvariable=self._pp_max_w_var,
                   width=5, bg=XP_WHITE, fg=XP_TEXT, relief=tk.FLAT,
                   font=("Tahoma", 8)).pack(side=tk.LEFT, padx=(4, 0))

        dim_row2 = tk.Frame(dim_grp, bg=XP_FACE)
        dim_row2.pack(fill=tk.X, padx=10, pady=(0, 6))
        xp_label(dim_row2, "Min height:").pack(side=tk.LEFT)
        tk.Spinbox(dim_row2, from_=20, to=400, textvariable=self._pp_min_h_var,
                   width=5, bg=XP_WHITE, fg=XP_TEXT, relief=tk.FLAT,
                   font=("Tahoma", 8)).pack(side=tk.LEFT, padx=(4, 0))

        content_grp = tk.LabelFrame(parent, text=" Content ",
                                    bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                    bd=2, relief=tk.GROOVE)
        content_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        if not hasattr(self, "_pp_force_avatar_var"):
            self._pp_force_avatar_var = tk.BooleanVar(value=bool(cfg.get("pp_force_avatar", True)))
            self._pp_force_icon_var   = tk.BooleanVar(value=bool(cfg.get("pp_force_icon", True)))
            self._pp_force_clock_var  = tk.BooleanVar(value=bool(cfg.get("pp_force_clock", False)))
            self._pp_font_aa_var      = tk.BooleanVar(value=bool(cfg.get("pp_font_aa", True)))

        xp_checkbox(content_grp, "Show avatar (pfp)", self._pp_force_avatar_var
                    ).pack(anchor=tk.W, padx=10, pady=(6, 1))
        xp_checkbox(content_grp, "Show icon", self._pp_force_icon_var
                    ).pack(anchor=tk.W, padx=10, pady=1)
        xp_checkbox(content_grp, "Show clock", self._pp_force_clock_var
                    ).pack(anchor=tk.W, padx=10, pady=1)
        xp_checkbox(content_grp, "Antialiased fonts", self._pp_font_aa_var
                    ).pack(anchor=tk.W, padx=10, pady=(1, 6))

        font_grp = tk.LabelFrame(parent, text=" Font ",
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        font_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        if not hasattr(self, "_pp_font_family_var"):
            self._pp_font_family_var = tk.StringVar(value=cfg.get("pp_font_family", "Segoe UI"))
            self._pp_font_size_var   = tk.IntVar(value=int(cfg.get("pp_font_size", 9)))

        font_row = tk.Frame(font_grp, bg=XP_FACE)
        font_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(font_row, "Family:").pack(side=tk.LEFT)
        _FONT_CHOICES = ["Segoe UI", "Arial", "Tahoma", "Verdana",
                         "Trebuchet MS", "Calibri", "Courier New", "Consolas"]
        font_om = tk.OptionMenu(font_row, self._pp_font_family_var, *_FONT_CHOICES)
        font_om.config(bg=XP_WHITE, fg=XP_TEXT, relief=tk.FLAT,
                       font=("Tahoma", 8), highlightthickness=1, width=13)
        font_om["menu"].config(bg=XP_WHITE, fg=XP_TEXT, font=("Tahoma", 8))
        font_om.pack(side=tk.LEFT, padx=(4, 12))
        xp_label(font_row, "Size:").pack(side=tk.LEFT)
        tk.Spinbox(font_row, from_=6, to=24, textvariable=self._pp_font_size_var,
                   width=4, bg=XP_WHITE, fg=XP_TEXT, relief=tk.FLAT,
                   font=("Tahoma", 8)).pack(side=tk.LEFT, padx=4)

        col_grp = tk.LabelFrame(parent, text=" Colors (fallback / no-skin mode) ",
                                bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                bd=2, relief=tk.GROOVE)
        col_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        if not hasattr(self, "_pp_color_bg_var"):
            self._pp_color_bg_var  = tk.StringVar(value=cfg.get("pp_color_bg",  "#808080"))
            self._pp_color_fg_var  = tk.StringVar(value=cfg.get("pp_color_fg",  "#FFFFFF"))
            self._pp_color_msg_var = tk.StringVar(value=cfg.get("pp_color_msg", "#EFEFEF"))
            self._pp_back_tint_var = tk.StringVar(value=cfg.get("pp_back_tint", ""))

        def _make_col_row(parent, label, var):
            row = tk.Frame(parent, bg=XP_FACE)
            row.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(row, text=label, width=14, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            swatch = tk.Label(row, text="   ", bg=var.get() or "#808080", relief=tk.FLAT, width=3)
            swatch.pack(side=tk.LEFT, padx=(0, 4))
            ef = tk.Frame(row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
            tk.Entry(ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                     width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            def _pick(v=var, s=swatch):
                from tkinter import colorchooser
                c = colorchooser.askcolor(parent=self.win, initialcolor=v.get())[1]
                if c:
                    v.set(c)
                    s.config(bg=c)
            xp_button(row, "…", _pick, width=2).pack(side=tk.LEFT)
            var.trace_add("write", lambda *_: swatch.config(bg=var.get() if len(var.get()) == 7 else "#808080"))

        _make_col_row(col_grp, "Background:", self._pp_color_bg_var)
        _make_col_row(col_grp, "Title color:", self._pp_color_fg_var)
        _make_col_row(col_grp, "Body color:", self._pp_color_msg_var)

        bt_row = tk.Frame(col_grp, bg=XP_FACE)
        bt_row.pack(fill=tk.X, padx=10, pady=(0, 6))
        xp_label(bt_row, "Back tint:").pack(side=tk.LEFT)
        bt_ef = tk.Frame(bt_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        bt_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
        tk.Entry(bt_ef, textvariable=self._pp_back_tint_var, bg=XP_WHITE, fg=XP_TEXT,
                 insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                 width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
        xp_label(col_grp, "(back tint: empty = use background color; #RRGGBB = fixed overlay blend)",
                 fg=XP_GREY_TXT).pack(anchor=tk.W, padx=10, pady=(0, 6))

        cpt_grp = tk.LabelFrame(parent, text=" Colors per-type ",
                                bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                bd=2, relief=tk.GROOVE)
        cpt_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        if not hasattr(self, "_pp_type_colors_var"):
            self._pp_type_colors_var = tk.BooleanVar(
                value=bool(cfg.get("pp_type_colors_enabled", False)))
            _tc_saved = cfg.get("pp_type_colors", {})
            self._pp_type_color_vars: dict = {}
            for _ttype, _tlabel in [("message", "Message"),
                                     ("mention", "@Mention"),
                                     ("friend_request", "Friend Request"),
                                     ("call", "Call")]:
                _td = _tc_saved.get(_ttype, {})
                self._pp_type_color_vars[_ttype] = {
                    "bg":   tk.StringVar(value=_td.get("bg",   "")),
                    "fg":   tk.StringVar(value=_td.get("fg",   "")),
                    "body": tk.StringVar(value=_td.get("body", "")),
                    "tint": tk.StringVar(value=_td.get("tint", "")),
                }

        def _toggle_cpt():
            _state = tk.NORMAL if self._pp_type_colors_var.get() else tk.DISABLED
            for _child in _cpt_inner.winfo_children():
                try: _child.configure(state=_state)
                except Exception: pass
                for _gc in _child.winfo_children():
                    try: _gc.configure(state=_state)
                    except Exception: pass

        xp_checkbox(cpt_grp, "Override colors per notification type",
                    self._pp_type_colors_var,
                    command=_toggle_cpt).pack(anchor=tk.W, padx=10, pady=(6, 2))

        _cpt_inner = tk.Frame(cpt_grp, bg=XP_FACE)
        _cpt_inner.pack(fill=tk.X, padx=10, pady=(0, 6))

        _TYPE_LABELS = [("message", "Message"), ("mention", "@Mention"),
                        ("friend_request", "Friend Req."), ("call", "Call")]
        _COL_LABELS  = [("bg", "BG"), ("fg", "Title"), ("body", "Body"), ("tint", "Tint")]

        _hdr = tk.Frame(_cpt_inner, bg=XP_FACE)
        _hdr.pack(fill=tk.X)
        tk.Label(_hdr, text="", width=11, bg=XP_FACE).pack(side=tk.LEFT)
        for _, _cl in _COL_LABELS:
            tk.Label(_hdr, text=_cl, width=9, bg=XP_FACE, fg=XP_TEXT,
                     font=("Tahoma", 7, "bold")).pack(side=tk.LEFT, padx=1)

        def _make_cpt_entry(parent_row, var):
            ef = tk.Frame(parent_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ef.pack(side=tk.LEFT, padx=2)
            e = tk.Entry(ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                         insertbackground=XP_TEXT, relief=tk.FLAT,
                         font=("Tahoma", 7), width=7)
            e.pack(fill=tk.X, ipady=2, padx=1, pady=1)

        for _ttype, _tlabel in _TYPE_LABELS:
            _row = tk.Frame(_cpt_inner, bg=XP_FACE)
            _row.pack(fill=tk.X, pady=1)
            tk.Label(_row, text=_tlabel+":", width=11, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=("Tahoma", 7)).pack(side=tk.LEFT)
            for _ckey, _ in _COL_LABELS:
                _make_cpt_entry(_row, self._pp_type_color_vars[_ttype][_ckey])

        xp_label(_cpt_inner,
                 "Leave empty to use the default colors above.",
                 fg=XP_GREY_TXT).pack(anchor=tk.W, pady=(4, 0))

        _toggle_cpt()

        av_grp = tk.LabelFrame(parent, text=" Avatar ",
                               bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                               bd=2, relief=tk.GROOVE)
        av_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        if not hasattr(self, "_pp_avatar_radius_var"):
            self._pp_avatar_radius_var = tk.IntVar(value=int(cfg.get("pp_avatar_radius", 0)))
            self._pp_avatar_radius_lbl = tk.StringVar(
                value=f"{self._pp_avatar_radius_var.get()}px")

        av_row = tk.Frame(av_grp, bg=XP_FACE)
        av_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(av_row, "Corner radius:").pack(side=tk.LEFT)
        tk.Scale(av_row, from_=0, to=30, orient=tk.HORIZONTAL,
                 variable=self._pp_avatar_radius_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=160,
                 command=lambda v: self._pp_avatar_radius_lbl.set(f"{int(float(v))}px"),
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(av_row, textvariable=self._pp_avatar_radius_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=5,
                 ).pack(side=tk.LEFT)
        xp_label(av_grp, "0 = square avatar. Higher = more rounded corners.",
                 fg=XP_GREY_TXT).pack(anchor=tk.W, padx=10, pady=(0, 6))

        if not hasattr(self, "_pp_avatar_aa_var"):
            self._pp_avatar_aa_var = tk.BooleanVar(value=bool(cfg.get("pp_avatar_aa", True)))
        xp_checkbox(av_grp, "Antialiased corners (smooth edges)",
                    self._pp_avatar_aa_var).pack(anchor=tk.W, padx=10, pady=(0, 6))

        to_grp = tk.LabelFrame(parent, text=" Popup Timeout ",
                               bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                               bd=2, relief=tk.GROOVE)
        to_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        if not hasattr(self, "_pp_timeout_var"):
            self._pp_timeout_var = tk.IntVar(value=int(cfg.get("pp_timeout", 7)))
            self._pp_timeout_lbl = tk.StringVar(value=f"{self._pp_timeout_var.get()}s")

        to_row = tk.Frame(to_grp, bg=XP_FACE)
        to_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(to_row, "Dismiss after:").pack(side=tk.LEFT)
        tk.Scale(to_row, from_=1, to=60, orient=tk.HORIZONTAL,
                 variable=self._pp_timeout_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=160,
                 command=lambda v: self._pp_timeout_lbl.set(f"{int(float(v))}s"),
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(to_row, textvariable=self._pp_timeout_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=4,
                 ).pack(side=tk.LEFT)

        stack_grp = tk.LabelFrame(parent, text=" Max Notification Stack ",
                                  bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                  bd=2, relief=tk.GROOVE)
        stack_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        def _on_stack_pp(val):
            self._max_stack_lbl.set(f"{int(float(val))} toasts")
        st_row = tk.Frame(stack_grp, bg=XP_FACE)
        st_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(st_row, "Max stacked:").pack(side=tk.LEFT)
        tk.Scale(st_row, from_=1, to=12, orient=tk.HORIZONTAL,
                 variable=self._max_stack_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=160,
                 command=_on_stack_pp,
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(st_row, textvariable=self._max_stack_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=10, anchor=tk.W,
                 ).pack(side=tk.LEFT)
        tk.Label(stack_grp,
                 text="Maximum number of PopupPlus windows visible at the same time.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 6))

        if not hasattr(self, "_pp_location_var"):
            self._pp_location_var = tk.StringVar(value=cfg.get("pp_location", "bottomright"))

        pos_grp = tk.LabelFrame(parent, text=" Position ",
                                bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                bd=2, relief=tk.GROOVE)
        pos_grp.pack(fill=tk.X, padx=4, pady=(0, 4))
        for val, lbl in [("bottomright", "Bottom-right"), ("bottomleft", "Bottom-left")]:
            tk.Radiobutton(pos_grp, text=lbl, variable=self._pp_location_var, value=val,
                           bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                           activebackground=XP_FACE, activeforeground=XP_TEXT,
                           font=XP_FONT_BOLD, anchor=tk.W,
                           ).pack(fill=tk.X, padx=10, pady=(4, 0))
        tk.Frame(pos_grp, bg=XP_FACE, height=4).pack()

        compact_icons_grp = tk.LabelFrame(parent, text=" Type Icons (Compact / PopupPlus) ",
                                          bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                          bd=2, relief=tk.GROOVE)
        compact_icons_grp.pack(fill=tk.X, padx=4, pady=(0, 4))
        tk.Label(compact_icons_grp,
                 text="PNG or ICO (16×16). Used as the icon object in the skin when \n"
                      "no avatar is available. Also used in Yahoo Compact mode.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(4, 2))

        for ci_label, ci_key in [("Message:",        "message"),
                                  ("@Mention:",       "mention"),
                                  ("Friend Request:", "friend_request"),
                                  ("Call:",           "call")]:
            ci_row = tk.Frame(compact_icons_grp, bg=XP_FACE)
            ci_row.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(ci_row, text=ci_label, width=16, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            var = self._compact_icon_vars[ci_key]
            ci_ef = tk.Frame(ci_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ci_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
            tk.Entry(ci_ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT,
                     font=("Tahoma", 7), width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(ci_row, "…",
                      lambda v=var: self._browse_compact_icon(v),
                      width=2).pack(side=tk.LEFT)

        anim_grp = tk.LabelFrame(parent, text=" Animation ",
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        anim_grp.pack(fill=tk.X, padx=4, pady=(0, 8))

        for val, lbl, desc in [
            ("simple", "Simple  (slide up)", "Classic slide-up animation."),
            ("yahoo",  "Yahoo Messenger  (fade + scale)",
             "Fades in from 0% opacity with a subtle scale from 90→100% using ease-out."),
        ]:
            tk.Radiobutton(anim_grp, text=lbl,
                           variable=self._toast_anim_style_var, value=val,
                           bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                           activebackground=XP_FACE, activeforeground=XP_TEXT,
                           font=XP_FONT_BOLD, anchor=tk.W,
                           ).pack(fill=tk.X, padx=10, pady=(6, 0))
            tk.Label(anim_grp, text=desc, bg=XP_FACE, fg=XP_GREY_TXT,
                     font=("Tahoma", 7), justify=tk.LEFT, anchor=tk.W,
                     ).pack(fill=tk.X, padx=28, pady=(0, 2))

        _speed_label_map = {1: "Very fast", 2: "Fast", 3: "Normal", 4: "Slow", 5: "Very slow"}
        def _on_speed_change_pp(val):
            self._toast_anim_speed_lbl.set(_speed_label_map.get(int(float(val)), "Normal"))

        spd_row = tk.Frame(anim_grp, bg=XP_FACE)
        spd_row.pack(fill=tk.X, padx=10, pady=(4, 6))
        xp_label(spd_row, "Speed:").pack(side=tk.LEFT)
        tk.Scale(spd_row, from_=1, to=5, orient=tk.HORIZONTAL,
                 variable=self._toast_anim_speed_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=160,
                 command=_on_speed_change_pp,
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(spd_row, textvariable=self._toast_anim_speed_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=12, anchor=tk.W,
                 ).pack(side=tk.LEFT)

    def _pp_load_skin(self):
        folder = self._pp_skin_folder_var.get().strip()
        if not folder:
            return
        try:
            skin = _pp_parser.find_and_parse(folder)
        except Exception as e:
            print(f"[popupplus] Failed to parse skin: {e}")
            skin = None
        self._pp_skin_obj = skin
        self._pp_skin_opts = {}
        if skin:
            self._pp_skin_opts = {oid: False for oid in skin.options}
        self._pp_build_opts_ui()

    def _pp_build_opts_ui(self):
        opts_frame = getattr(self, "_pp_opts_frame", None)
        if opts_frame is None:
            return
        for w in opts_frame.winfo_children():
            w.destroy()
        self._pp_opt_vars.clear()
        skin = getattr(self, "_pp_skin_obj", None)
        if not skin or not skin.options:
            return
        saved = getattr(self, "_pp_skin_opts", {})
        for oid, (oval, otitle) in sorted(skin.options.items()):
            var = tk.BooleanVar(value=bool(saved.get(oid, False)))
            self._pp_opt_vars[oid] = var
            def _update(oid=oid, var=var):
                self._pp_skin_opts[oid] = var.get()
            tk.Checkbutton(opts_frame, text=f"[{oid}] {otitle}",
                           variable=var,
                           bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                           activebackground=XP_FACE, activeforeground=XP_TEXT,
                           font=("Tahoma", 8),
                           command=_update,
                           ).pack(anchor=tk.W, padx=4, pady=1)

    def _build_style_yahoo(self, parent: tk.Frame) -> None:
        compact_grp = tk.LabelFrame(parent, text=" Toast Display Mode ",
                                    bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                    bd=2, relief=tk.GROOVE)
        compact_grp.pack(fill=tk.X, padx=4, pady=(8, 4))

        tk.Radiobutton(compact_grp, text="Normal  (pfp + message)",
                       variable=self._toast_display_mode_var, value="normal",
                       bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                       activebackground=XP_FACE, activeforeground=XP_TEXT,
                       font=XP_FONT_BOLD, anchor=tk.W,
                       ).pack(fill=tk.X, padx=10, pady=(6, 0))
        tk.Label(compact_grp,
                 text="Classic style: avatar on the left, message text on the right.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 4))

        tk.Radiobutton(compact_grp, text="Compact  (small icon + message)",
                       variable=self._toast_display_mode_var, value="compact",
                       bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                       activebackground=XP_FACE, activeforeground=XP_TEXT,
                       font=XP_FONT_BOLD, anchor=tk.W,
                       ).pack(fill=tk.X, padx=10, pady=(4, 0))
        tk.Label(compact_grp,
                 text="Yahoo 2009 style: pfp replaced by a tiny type icon,\nless vertical space, more messages on screen at once.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

        compact_icons_grp = tk.LabelFrame(parent, text=" Compact Mode: Type Icons ",
                                          bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                          bd=2, relief=tk.GROOVE)
        compact_icons_grp.pack(fill=tk.X, padx=4, pady=(0, 4))
        tk.Label(compact_icons_grp,
                 text="PNG or ICO (16×16 recommended). Leave blank for a text fallback.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(4, 2))

        for ci_label, ci_key in [("Message:",        "message"),
                                  ("@Mention:",       "mention"),
                                  ("Friend Request:", "friend_request"),
                                  ("Call:",           "call")]:
            ci_row = tk.Frame(compact_icons_grp, bg=XP_FACE)
            ci_row.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(ci_row, text=ci_label, width=16, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            var = self._compact_icon_vars[ci_key]
            ci_ef = tk.Frame(ci_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ci_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
            tk.Entry(ci_ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT,
                     font=("Tahoma", 7), width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(ci_row, "\u2026",
                      lambda v=var: self._browse_compact_icon(v),
                      width=2).pack(side=tk.LEFT)

        stack_grp = tk.LabelFrame(parent, text=" Max Notification Stack ",
                                  bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                  bd=2, relief=tk.GROOVE)
        stack_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        def _on_stack_change(val):
            self._max_stack_lbl.set(f"{int(float(val))} toasts")
        st_row = tk.Frame(stack_grp, bg=XP_FACE)
        st_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(st_row, "Max stacked:").pack(side=tk.LEFT)
        tk.Scale(st_row, from_=1, to=12, orient=tk.HORIZONTAL,
                 variable=self._max_stack_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=160,
                 command=_on_stack_change,
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(st_row, textvariable=self._max_stack_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=10, anchor=tk.W,
                 ).pack(side=tk.LEFT)
        tk.Label(stack_grp,
                 text="Maximum number of popup toasts visible at the same time.\nOldest toast is removed when the limit is reached.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 6))

        tex_frm = tk.LabelFrame(parent, text=" Titlebar Textures ",
                                bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                bd=2, relief=tk.GROOVE)
        tex_frm.pack(fill=tk.X, padx=4, pady=(8, 4))

        self._titlebar_tex_vars: dict[str, tk.StringVar] = {}
        for lbl, key in [("Left edge (≤49 px):", "toast_titlebar_left"),
                         ("Middle (stretch):",   "toast_titlebar_mid"),
                         ("Right edge (≤49 px):","toast_titlebar_right"),
                         ("Close button (19×19):","toast_close_btn")]:
            row = tk.Frame(tex_frm, bg=XP_FACE)
            row.pack(fill=tk.X, padx=10, pady=3)
            xp_label(row, lbl).pack(side=tk.LEFT)
            var = tk.StringVar(value=self._cfg.get(key, ""))
            self._titlebar_tex_vars[key] = var
            ef = tk.Frame(row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4))
            tk.Entry(ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT,
                     font=("Tahoma", 7), width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(row, "\u2026", lambda v=var: self._browse_tex(v), width=2).pack(side=tk.LEFT)

        chroma_row = tk.Frame(tex_frm, bg=XP_FACE)
        chroma_row.pack(fill=tk.X, padx=10, pady=4)
        xp_label(chroma_row, "Chroma key:").pack(side=tk.LEFT)
        self._chroma_var = tk.StringVar(value=self._cfg.get("toast_chroma_key", "#FF00FF"))
        chroma_ef = tk.Frame(chroma_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        chroma_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4))
        tk.Entry(chroma_ef, textvariable=self._chroma_var, bg=XP_WHITE, fg=XP_TEXT,
                 insertbackground=XP_TEXT, relief=tk.FLAT,
                 font=("Tahoma", 7), width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
        def _pick_chroma():
            from tkinter import colorchooser
            c = colorchooser.askcolor(parent=self.win, title="Chroma key", initialcolor=self._chroma_var.get())[1]
            if c:
                self._chroma_var.set(c)
        xp_button(chroma_row, "\u2026", _pick_chroma, width=2).pack(side=tk.LEFT)
        tk.Label(tex_frm,
                 text="Pixels with full transparency in textures are replaced\nwith this colour before chroma-key removes them.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 4))

        border_grp = tk.LabelFrame(parent, text=" Notification Box Border Colour ",
                                   bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                   bd=2, relief=tk.GROOVE)
        border_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        border_row = tk.Frame(border_grp, bg=XP_FACE)
        border_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(border_row, "Border colour:").pack(side=tk.LEFT)
        border_ef = tk.Frame(border_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        border_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4))
        tk.Entry(border_ef, textvariable=self._body_border_var, bg=XP_WHITE, fg=XP_TEXT,
                 insertbackground=XP_TEXT, relief=tk.FLAT,
                 font=("Tahoma", 7), width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
        def _pick_border_color():
            from tkinter import colorchooser
            c = colorchooser.askcolor(
                parent=self.win, title="Choose notification box border colour",
                initialcolor=self._body_border_var.get())[1]
            if c:
                self._body_border_var.set(c)
        xp_button(border_row, "\u2026", _pick_border_color, width=2).pack(side=tk.LEFT)
        tk.Label(border_grp,
                 text="Colour of the border around the grey notification box (Yahoo Messenger style only).",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 6))

        self._y_offset_var = tk.IntVar(value=int(self._cfg.get("toast_y_offset", 0)))
        self._y_offset_lbl = tk.StringVar(value=f"{self._y_offset_var.get()}px")
        off_row = tk.Frame(parent, bg=XP_FACE)
        off_row.pack(fill=tk.X, padx=10, pady=(4, 2))
        xp_label(off_row, "Y offset (taskbar height):").pack(side=tk.LEFT)
        tk.Scale(off_row, from_=0, to=120, orient=tk.HORIZONTAL,
                 variable=self._y_offset_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=180,
                 command=lambda v: self._y_offset_lbl.set(f"{int(float(v))}px"),
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(off_row, textvariable=self._y_offset_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=4,
                 ).pack(side=tk.LEFT)
        tk.Label(parent,
                 text="Increase this if the popup covers your taskbar.\nTypical taskbar height is 40-48 px.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 4))

        title_grp = tk.LabelFrame(parent, text=" Default Titlebar Title ",
                                  bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                  bd=2, relief=tk.GROOVE)
        title_grp.pack(fill=tk.X, padx=4, pady=(0, 4))

        title_row = tk.Frame(title_grp, bg=XP_FACE)
        title_row.pack(fill=tk.X, padx=10, pady=6)
        xp_label(title_row, "Title text:").pack(side=tk.LEFT)
        title_ef = tk.Frame(title_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        title_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4))
        tk.Entry(title_ef, textvariable=self._toast_default_title_var,
                 bg=XP_WHITE, fg=XP_TEXT, insertbackground=XP_TEXT,
                 relief=tk.FLAT, font=("Tahoma", 8),
                 ).pack(fill=tk.X, ipady=3, padx=1, pady=1)
        tk.Label(title_grp,
                 text="Shown in the titlebar for non-server notifications (DMs, system messages).\nLeave blank to use \"Discord\".",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 6))

        anim_grp = tk.LabelFrame(parent, text=" Toast Animation ",
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        anim_grp.pack(fill=tk.X, padx=4, pady=(0, 8))

        for val, lbl, desc in [
            ("simple", "Simple  (slide up)", "The classic slide-up animation."),
            ("yahoo",  "Yahoo Messenger  (fade + scale)",
             "Fades in from 0% opacity with a subtle scale from 90→100% using ease-out."),
        ]:
            tk.Radiobutton(anim_grp, text=lbl,
                           variable=self._toast_anim_style_var, value=val,
                           bg=XP_FACE, fg=XP_TEXT, selectcolor=XP_WHITE,
                           activebackground=XP_FACE, activeforeground=XP_TEXT,
                           font=XP_FONT_BOLD, anchor=tk.W,
                           ).pack(fill=tk.X, padx=10, pady=(6, 0))
            tk.Label(anim_grp, text=desc, bg=XP_FACE, fg=XP_GREY_TXT,
                     font=("Tahoma", 7), justify=tk.LEFT, anchor=tk.W,
                     ).pack(fill=tk.X, padx=28, pady=(0, 2))

        _speed_label_map = {1: "Muy rápida", 2: "Rápida", 3: "Normal", 4: "Lenta", 5: "Muy lenta"}
        def _on_speed_change(val):
            self._toast_anim_speed_lbl.set(_speed_label_map.get(int(float(val)), "Normal"))

        spd_row = tk.Frame(anim_grp, bg=XP_FACE)
        spd_row.pack(fill=tk.X, padx=10, pady=(4, 6))
        xp_label(spd_row, "Speed:").pack(side=tk.LEFT)
        tk.Scale(spd_row, from_=1, to=5, orient=tk.HORIZONTAL,
                 variable=self._toast_anim_speed_var, showvalue=False,
                 bg=XP_FACE, fg=XP_TEXT, troughcolor=XP_WHITE,
                 activebackground=XP_FACE_DARK, highlightthickness=0,
                 bd=1, relief=tk.FLAT, sliderlength=18, length=160,
                 command=_on_speed_change,
                 ).pack(side=tk.LEFT, padx=6)
        tk.Label(spd_row, textvariable=self._toast_anim_speed_lbl,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD, width=12, anchor=tk.W,
                 ).pack(side=tk.LEFT)
        tk.Label(anim_grp,
                 text="Applies to both animation styles.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(0, 6))

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
            lbl = sounds.get("_label", "")
            self._pu_create_panel(uid, lbl, sounds)

    def _pu_add_user(self, user_id: str = "", sounds: "dict | None" = None) -> None:
        if sounds is None:
            sounds = {}
        label = sounds.get("_label", "")

        if not user_id and not label:
            self._pu_open_edit_dialog(None, "", "", sounds)
        else:
            self._pu_create_panel(user_id, label, sounds)

    def _pu_open_edit_dialog(
        self,
        entry: "dict | None",
        user_id: str,
        label: str,
        sounds: "dict | None" = None,
    ) -> None:
        if sounds is None:
            sounds = {}

        dialog = tk.Toplevel(self.win)
        dialog.title("Usuario" if entry is None else "Editar usuario")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg=XP_FACE)

        self.win.update_idletasks()
        wx = self.win.winfo_rootx() + self.win.winfo_width() // 2
        wy = self.win.winfo_rooty() + self.win.winfo_height() // 2
        dialog.geometry(f"+{wx - 160}+{wy - 70}")

        body = tk.Frame(dialog, bg=XP_FACE)
        body.pack(padx=12, pady=(10, 4))

        tk.Label(body, text="Nombre:", width=16, anchor=tk.W,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).grid(row=0, column=0, sticky=tk.W, pady=3)
        name_var = tk.StringVar(value=label)
        name_frame = tk.Frame(body, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        name_frame.grid(row=0, column=1, sticky=tk.EW, pady=3)
        name_entry_w = tk.Entry(name_frame, textvariable=name_var, bg=XP_WHITE, fg=XP_TEXT,
                                insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 8), width=26)
        name_entry_w.pack(fill=tk.X, ipady=3, padx=1, pady=1)

        tk.Label(body, text="Discord User ID:", width=16, anchor=tk.W,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).grid(row=1, column=0, sticky=tk.W, pady=3)
        id_var = tk.StringVar(value=user_id)
        id_frame = tk.Frame(body, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        id_frame.grid(row=1, column=1, sticky=tk.EW, pady=3)
        tk.Entry(id_frame, textvariable=id_var, bg=XP_WHITE, fg=XP_TEXT,
                 insertbackground=XP_TEXT, relief=tk.FLAT,
                 font=("Lucida Console", 8), width=26).pack(fill=tk.X, ipady=3, padx=1, pady=1)

        body.columnconfigure(1, weight=1)

        status_var = tk.StringVar()
        tk.Label(dialog, textvariable=status_var, bg=XP_FACE, fg="#CC0000",
                 font=("Tahoma", 8)).pack(anchor=tk.W, padx=12)

        btn_row = tk.Frame(dialog, bg=XP_FACE)
        btn_row.pack(fill=tk.X, padx=8, pady=(2, 8))

        def _confirm():
            new_id    = id_var.get().strip()
            new_label = name_var.get().strip()
            if not new_id:
                status_var.set("El ID de usuario no puede estar vacío.")
                return
            if not new_label:
                status_var.set("El nombre no puede estar vacío.")
                return
            dialog.destroy()
            if entry is None:
                self._pu_create_panel(new_id, new_label, sounds)
            else:
                entry["id_var"].set(new_id)
                entry["name_var"].set(new_label)
                entry["frame"].config(text=f" {new_label} ")

        xp_button(btn_row, "Aceptar", _confirm, width=10).pack(side=tk.RIGHT, padx=(4, 2))
        xp_button(btn_row, "Cancelar", dialog.destroy, width=10).pack(side=tk.RIGHT, padx=2)

        name_entry_w.focus_set()
        dialog.bind("<Return>", lambda _: _confirm())
        dialog.bind("<Escape>", lambda _: dialog.destroy())

    def _pu_create_panel(self, user_id: str, label: str, sounds: dict) -> None:
        id_var   = tk.StringVar(value=user_id)
        name_var = tk.StringVar(value=label)

        frame = tk.LabelFrame(
            self._pu_inner,
            text=f" {label} " if label else " User ",
            bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
            bd=2, relief=tk.GROOVE,
        )
        frame.pack(fill=tk.X, padx=4, pady=4)

        entry: dict = {"frame": frame, "id_var": id_var, "name_var": name_var}

        top_row = tk.Frame(frame, bg=XP_FACE)
        top_row.pack(fill=tk.X, padx=6, pady=(4, 2))

        def _edit(e=entry):
            self._pu_open_edit_dialog(
                e,
                e["id_var"].get(),
                e["name_var"].get(),
            )

        def _remove(e=entry):
            self._pu_remove_user(e)

        xp_button(top_row, "Editar",    _edit,   width=8).pack(side=tk.RIGHT, padx=(2, 0))
        xp_button(top_row, "✕ Quitar", _remove,  width=8).pack(side=tk.RIGHT, padx=2)

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

        tex_frm = tk.Frame(frame, bg=XP_FACE)
        entry["_pu_tex_frm"] = tex_frm
        tex_frm.pack(fill=tk.X, padx=6, pady=(0, 2))
        for lbl_text, key in [("Titlebar left:",  "titlebar_left"),
                              ("Titlebar mid:",   "titlebar_mid"),
                              ("Titlebar right:", "titlebar_right"),
                              ("Close btn:",      "close_btn")]:
            tex_row = tk.Frame(tex_frm, bg=XP_FACE)
            tex_row.pack(fill=tk.X, padx=0, pady=2)
            tk.Label(tex_row, text=lbl_text, width=14, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            tex_var = tk.StringVar(value=sounds.get(key, ""))
            entry[f"{key}_var"] = tex_var
            tex_ef = tk.Frame(tex_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            tex_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
            tk.Entry(tex_ef, textvariable=tex_var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                     width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(tex_row, "…",
                      lambda v=tex_var: self._pu_browse_tex(v),
                      width=2).pack(side=tk.LEFT, padx=(0, 2))

        border_row = tk.Frame(frame, bg=XP_FACE)
        border_row.pack(fill=tk.X, padx=6, pady=(2, 4))
        tk.Label(border_row, text="Border colour:", width=14, anchor=tk.W,
                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
        pu_border_var = tk.StringVar(value=sounds.get("body_border_color", ""))
        entry["body_border_color_var"] = pu_border_var
        border_ef = tk.Frame(border_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
        border_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
        tk.Entry(border_ef, textvariable=pu_border_var, bg=XP_WHITE, fg=XP_TEXT,
                 insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                 width=8).pack(fill=tk.X, ipady=3, padx=1, pady=1)
        xp_button(border_row, "…",
                  lambda v=pu_border_var: self._pu_pick_color(v),
                  width=2).pack(side=tk.LEFT, padx=(0, 2))

        tk.Frame(frame, bg=XP_FACE, height=2).pack()

        self._user_sound_entries.append(entry)

    def _pu_remove_user(self, entry: dict) -> None:
        entry["frame"].destroy()
        self._user_sound_entries.remove(entry)

    def _pu_pick_color(self, var: tk.StringVar) -> None:
        from tkinter import colorchooser
        color = colorchooser.askcolor(parent=self.win, title="Choose titlebar color")[1]
        if color:
            var.set(color)

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
        _sc = tk.Frame(parent, bg=XP_FACE)
        _sc.pack(fill=tk.BOTH, expand=True)
        _canvas = tk.Canvas(_sc, bg=XP_FACE, highlightthickness=0)
        _sb = tk.Scrollbar(_sc, orient=tk.VERTICAL, command=_canvas.yview,
                           bg=XP_FACE, troughcolor=XP_FACE_DARK, relief=tk.FLAT)
        _canvas.configure(yscrollcommand=_sb.set)
        _sb.pack(side=tk.RIGHT, fill=tk.Y)
        _canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _inner = tk.Frame(_canvas, bg=XP_FACE)
        _win_id = _canvas.create_window((0, 0), window=_inner, anchor=tk.NW)
        _inner.bind("<Configure>", lambda e: (_canvas.configure(scrollregion=_canvas.bbox("all")),
                                               _canvas.itemconfig(_win_id, width=_canvas.winfo_width())))
        _canvas.bind("<Configure>", lambda e: _canvas.itemconfig(_win_id, width=e.width))
        def _icons_mousewheel(event):
            try:
                _canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        _canvas.bind_all("<MouseWheel>", _icons_mousewheel)
        _canvas.bind("<Destroy>", lambda e: _canvas.unbind_all("<MouseWheel>"))
        parent = _inner

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

        xp_separator(parent).pack(fill=tk.X, padx=4, pady=(8, 4))

        status_hdr = tk.LabelFrame(parent, text=" Icons for Idle Statuses ",
                                   bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                   bd=2, relief=tk.GROOVE)
        status_hdr.pack(fill=tk.X, padx=4, pady=(0, 4))

        xp_checkbox(status_hdr, "Tray icons for different statuses",
                    self._tray_status_icons_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 2))
        tk.Label(status_hdr,
                 text="When enabled, the tray icon changes based on your Discord\n"
                      "status (online/dnd/idle/invisible). VC and unread states\n"
                      "still take priority over status icons.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

        status_icons_grp = tk.LabelFrame(parent, text=" Status Icon Files ",
                                         bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                         bd=2, relief=tk.GROOVE)
        status_icons_grp.pack(fill=tk.X, padx=4, pady=(0, 6))
        tk.Label(status_icons_grp,
                 text="PNG or ICO (16×16 recommended). Only used when the checkbox above is enabled.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=10, pady=(4, 2))

        for si_label, si_key in [("● Online:",    "online"),
                                  ("■ Do Not Disturb:", "dnd"),
                                  ("☽ Idle:",     "idle"),
                                  ("○ Invisible:", "invisible")]:
            si_row = tk.Frame(status_icons_grp, bg=XP_FACE)
            si_row.pack(fill=tk.X, padx=6, pady=3)
            tk.Label(si_row, text=si_label, width=18, anchor=tk.W,
                     bg=XP_FACE, fg=XP_TEXT, font=XP_FONT).pack(side=tk.LEFT)
            var = self._status_icon_vars[si_key]
            si_ef = tk.Frame(si_row, bg=XP_BORDER, bd=1, relief=tk.FLAT)
            si_ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2))
            tk.Entry(si_ef, textvariable=var, bg=XP_WHITE, fg=XP_TEXT,
                     insertbackground=XP_TEXT, relief=tk.FLAT, font=("Tahoma", 7),
                     ).pack(fill=tk.X, ipady=3, padx=1, pady=1)
            xp_button(si_row, "…",
                      lambda k=si_key: self._browse_status_icon(k),
                      width=2).pack(side=tk.LEFT, padx=(0, 2))
            xp_button(si_row, "▶",
                      lambda k=si_key: self._preview_status_icon(k),
                      width=2).pack(side=tk.LEFT)

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

    def _browse_status_icon(self, status_key: str) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win,
            title=f"Select PNG icon for status: {status_key}",
            filetypes=[("PNG files", "*.png"), ("ICO files", "*.ico"),
                       ("All files", "*.*")],
        )
        if path:
            self._status_icon_vars[status_key].set(path)

    def _preview_status_icon(self, status_key: str) -> None:
        path = self._status_icon_vars[status_key].get().strip()
        if not path or not os.path.isfile(path):
            return
        hicon = _file_to_hicon(path, size=16)
        if hicon:
            _set_tray_icon_handle(hicon)
            print(f"[tray] Preview status icon for '{status_key}': {os.path.basename(path)}")

    def _build_more_page(self, parent: tk.Frame) -> None:
                                                                                
        exit_grp = tk.LabelFrame(parent, text=_t("grp_exit_settings"),
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        exit_grp.pack(fill=tk.X, padx=4, pady=(8, 4))

        xp_checkbox(exit_grp, _t("exit_chk_close_discord"), self._exit_close_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 6))

        conn_grp = tk.LabelFrame(parent, text=" Notifications de conexión ",
                                 bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                 bd=2, relief=tk.GROOVE)
        conn_grp.pack(fill=tk.X, padx=4, pady=(0, 4))
        xp_checkbox(conn_grp, "Desactivar notificación \"Conectado a [usuario]\"",
                    self._suppress_connect_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 2))
        tk.Label(conn_grp,
                 text="Suprime el globo que aparece al conectarse a los\nservidores de Discord al iniciar Ballooncord.",
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

        launch_grp = tk.LabelFrame(parent, text=_t("grp_launch"),
                                   bg=XP_FACE, fg=XP_TEXT, font=XP_FONT_BOLD,
                                   bd=2, relief=tk.GROOVE)
        launch_grp.pack(fill=tk.X, padx=4, pady=(8, 4))

        self._auto_open_var = tk.BooleanVar(value=bool(self._cfg.get("auto_open_client", False)))
        xp_checkbox(launch_grp, _t("chk_auto_open"), self._auto_open_var,
                    ).pack(anchor=tk.W, padx=10, pady=(6, 2))
        tk.Label(launch_grp, text=_t("chk_auto_open_desc"),
                 bg=XP_FACE, fg=XP_GREY_TXT, font=("Tahoma", 7),
                 justify=tk.LEFT, anchor=tk.W,
                 ).pack(fill=tk.X, padx=28, pady=(0, 6))

                                                                               
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
            text=f"Ballooncord v{VERSION}",
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
        _tex_vars = getattr(self, "_titlebar_tex_vars", {})
        for key in ("toast_titlebar_left", "toast_titlebar_mid", "toast_titlebar_right", "toast_close_btn"):
            val = _tex_vars.get(key, tk.StringVar()).get().strip() if _tex_vars else ""
            if val:
                cfg[key] = val
            else:
                cfg.pop(key, None)
        _chroma = getattr(self, "_chroma_var", None)
        cfg["toast_chroma_key"] = _chroma.get().strip() if _chroma else "#FF00FF"
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
            label = entry["name_var"].get().strip()
            if label:
                sounds["_label"] = label
            mode = entry.get("_pu_mode_var", tk.StringVar(value="texture")).get()
            for key in ("titlebar_left", "titlebar_mid", "titlebar_right", "close_btn"):
                    var = entry.get(f"{key}_var")
                    if var:
                        c = var.get().strip()
                        if c:
                            sounds[key] = c
            border_var = entry.get("body_border_color_var")
            if border_var:
                bc = border_var.get().strip()
                if bc:
                    sounds["body_border_color"] = bc
            if sounds:
                per_user[uid] = sounds
        cfg["per_user_sounds"] = per_user
        cfg["auto_open_client"] = bool(getattr(self, "_auto_open_var", tk.BooleanVar()).get())
        cfg["check_for_updates"] = bool(getattr(self, "_check_updates_var", tk.BooleanVar(value=True)).get())
        cfg["auto_update"]      = bool(getattr(self, "_auto_update_var", tk.BooleanVar()).get())
        cfg["balloon_sound_mode"] = bool(getattr(self, "_balloon_sound_var", tk.BooleanVar()).get())
        cfg["balloon_timeout"]    = int(getattr(self, "_timeout_var",       tk.IntVar()).get())
        _ntype = self._notif_type_var.get()
        cfg["notif_type"] = _ntype
        cfg["use_yahoo_toast"] = (_ntype == "popup")
        if hasattr(self, "_pp_skin_folder_var"):
            cfg["pp_skin_folder"] = self._pp_skin_folder_var.get().strip()
        if hasattr(self, "_pp_color_bg_var"):
            cfg["pp_color_bg"] = self._pp_color_bg_var.get().strip() or "#808080"
        if hasattr(self, "_pp_color_fg_var"):
            cfg["pp_color_fg"] = self._pp_color_fg_var.get().strip() or "#FFFFFF"
        if hasattr(self, "_pp_color_msg_var"):
            cfg["pp_color_msg"] = self._pp_color_msg_var.get().strip() or "#EFEFEF"
        if hasattr(self, "_pp_back_tint_var"):
            cfg["pp_back_tint"] = self._pp_back_tint_var.get().strip()
        if hasattr(self, "_pp_avatar_radius_var"):
            cfg["pp_avatar_radius"] = int(self._pp_avatar_radius_var.get())
        if hasattr(self, "_pp_avatar_aa_var"):
            cfg["pp_avatar_aa"] = bool(self._pp_avatar_aa_var.get())
        if hasattr(self, "_pp_font_family_var"):
            cfg["pp_font_family"] = self._pp_font_family_var.get()
        if hasattr(self, "_pp_font_size_var"):
            cfg["pp_font_size"] = int(self._pp_font_size_var.get())
        if hasattr(self, "_pp_force_avatar_var"):
            cfg["pp_force_avatar"] = bool(self._pp_force_avatar_var.get())
        if hasattr(self, "_pp_force_icon_var"):
            cfg["pp_force_icon"] = bool(self._pp_force_icon_var.get())
        if hasattr(self, "_pp_force_clock_var"):
            cfg["pp_force_clock"] = bool(self._pp_force_clock_var.get())
        if hasattr(self, "_pp_font_aa_var"):
            cfg["pp_font_aa"] = bool(self._pp_font_aa_var.get())
        if hasattr(self, "_pp_skin_opts"):
            cfg["pp_skin_opts"] = self._pp_skin_opts
        if hasattr(self, "_pp_min_w_var"):
            cfg["pp_min_skin_width"] = int(self._pp_min_w_var.get())
        if hasattr(self, "_pp_max_w_var"):
            cfg["pp_max_skin_width"] = int(self._pp_max_w_var.get())
        if hasattr(self, "_pp_min_h_var"):
            cfg["pp_min_skin_height"] = int(self._pp_min_h_var.get())
        if hasattr(self, "_pp_timeout_var"):
            cfg["pp_timeout"] = int(self._pp_timeout_var.get())
        if hasattr(self, "_pp_location_var"):
            cfg["pp_location"] = self._pp_location_var.get()
        if hasattr(self, "_pp_type_colors_var"):
            cfg["pp_type_colors_enabled"] = bool(self._pp_type_colors_var.get())
        if hasattr(self, "_pp_type_color_vars"):
            cfg["pp_type_colors"] = {
                _ttype: {
                    _ckey: _var.get().strip()
                    for _ckey, _var in _cdict.items()
                }
                for _ttype, _cdict in self._pp_type_color_vars.items()
            }
        cfg["toast_gradient_start"] = self._grad_start_var.get().strip() or "#0058CE"
        cfg["toast_gradient_end"] = self._grad_end_var.get().strip() or "#2B93FF"
        cfg["toast_body_border_color"] = self._body_border_var.get().strip() or "#808080"
        cfg["toast_y_offset"] = int(self._y_offset_var.get()) if hasattr(self, "_y_offset_var") else int(self._cfg.get("toast_y_offset", 0))
        cfg["toast_anim_style"] = self._toast_anim_style_var.get()
        cfg["toast_anim_speed"] = int(self._toast_anim_speed_var.get())
        cfg["toast_default_title"] = self._toast_default_title_var.get().strip() or "Discord"
        cfg["suppress_connect_notif"] = bool(self._suppress_connect_var.get())
        cfg["toast_display_mode"] = self._toast_display_mode_var.get()
        cfg["compact_icons"] = {k: v.get().strip() for k, v in self._compact_icon_vars.items() if v.get().strip()}
        cfg["yahoo_max_stack"] = int(self._max_stack_var.get())
        cfg["tray_status_icons_enabled"] = bool(self._tray_status_icons_var.get())
        cfg["status_icons"] = {k: v.get().strip() for k, v in self._status_icon_vars.items() if v.get().strip()}
        _new_close = bool(getattr(self, "_exit_close_var", tk.BooleanVar()).get())
        _prev_close = self._cfg.get("exit_close_client", None)
        if _new_close:
            cfg["exit_close_client"] = True
        elif _prev_close is not None:
            cfg["exit_close_client"] = False
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

    def _browse_compact_icon(self, var: tk.StringVar) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win,
            title="Select compact icon (PNG or ICO)",
            filetypes=[("PNG files", "*.png"), ("ICO files", "*.ico"), ("All files", "*.*")],
        )
        if path:
            var.set(path)

    def _browse_tex(self, var: tk.StringVar) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win,
            title="Select texture",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if path:
            var.set(path)

    def _pu_browse_tex(self, var: tk.StringVar) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win,
            title="Select texture",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if path:
            var.set(path)
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
        os.path.join(base, "BallooncordUpdater.exe"),
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
        os.path.join(base, "BallooncordUpdater.exe"),
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

    flag_path = os.path.join(_get_base_dir(), "_Ballooncord_update.json")
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
            "Ballooncord \u2014 Update ready",
            f"v{ver} downloaded. Restart Ballooncord to apply.",
            None,
        )
        print(f"[updater] Showed 'restart to apply' balloon for v{ver}")
    else:
                                                                                     
        _pending_update_info = {"version": ver, "download_url": download_url}
        _raw_show_balloon(
            "Ballooncord \u2014 Update available",
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
"""Small typed Win32 bridge. No keyboard recording or background text log."""
import ctypes as C
from ctypes import wintypes as W
import sys
import queue
import threading

if sys.platform != "win32":
    raise OSError("Глобальная замена доступна только в Windows.")

u = C.WinDLL("user32", use_last_error=True)
k = C.WinDLL("kernel32", use_last_error=True)


def bind(dll, name, args, result):
    fn = getattr(dll, name)
    fn.argtypes, fn.restype = args, result
    return fn


_register = bind(u, "RegisterHotKey", [W.HWND, C.c_int, W.UINT, W.UINT], W.BOOL)
_unregister = bind(u, "UnregisterHotKey", [W.HWND, C.c_int], W.BOOL)
peek = bind(u, "PeekMessageW", [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT], W.BOOL)
foreground = bind(u, "GetForegroundWindow", [], W.HWND)
ancestor = bind(u, "GetAncestor", [W.HWND, W.UINT], W.HWND)
key_state = bind(u, "GetAsyncKeyState", [C.c_int], C.c_short)
sequence = bind(u, "GetClipboardSequenceNumber", [], W.DWORD)
open_clipboard = bind(u, "OpenClipboard", [W.HWND], W.BOOL)
close_clipboard = bind(u, "CloseClipboard", [], W.BOOL)
get_data = bind(u, "GetClipboardData", [W.UINT], W.HANDLE)
set_data = bind(u, "SetClipboardData", [W.UINT, W.HANDLE], W.HANDLE)
empty = bind(u, "EmptyClipboard", [], W.BOOL)
alloc = bind(k, "GlobalAlloc", [W.UINT, C.c_size_t], W.HGLOBAL)
lock = bind(k, "GlobalLock", [W.HGLOBAL], C.c_void_p)
unlock = bind(k, "GlobalUnlock", [W.HGLOBAL], W.BOOL)
free = bind(k, "GlobalFree", [W.HGLOBAL], W.HGLOBAL)


class KeyboardInput(C.Structure):
    _fields_ = [("vk", W.WORD), ("scan", W.WORD), ("flags", W.DWORD),
                ("time", W.DWORD), ("extra", C.c_size_t)]


class MouseInput(C.Structure):
    _fields_ = [("dx", W.LONG), ("dy", W.LONG), ("data", W.DWORD),
                ("flags", W.DWORD), ("time", W.DWORD), ("extra", C.c_size_t)]


class InputUnion(C.Union):
    _fields_ = [("keyboard", KeyboardInput), ("mouse", MouseInput)]


class Input(C.Structure):
    _fields_ = [("type", W.DWORD), ("value", InputUnion)]


send_input = bind(u, "SendInput", [W.UINT, C.POINTER(Input), C.c_int], W.UINT)


def shortcut(letter):
    # Scan codes for physical Ctrl+C / Ctrl+V: independent of RU/EN layout.
    scan = {"c": 0x2E, "v": 0x2F}[letter]
    items = []
    for code, released in ((0x1D, False), (scan, False), (scan, True), (0x1D, True)):
        item = Input()
        item.type = 1
        item.value.keyboard = KeyboardInput(0, code, 0x0008 | (2 if released else 0), 0, 0)
        items.append(item)
    data = (Input * len(items))(*items)
    if send_input(len(data), data, C.sizeof(Input)) != len(data):
        # Always attempt to release synthesized keys, even on partial delivery.
        releases = (Input * 2)(items[2], items[3])
        send_input(2, releases, C.sizeof(Input))
        raise OSError("Windows заблокировала сочетание клавиш.")


def modifiers_down():
    return any(key_state(vk) & 0x8000 for vk in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0x77, 0x78, 0x79))


def read_clipboard(owner):
    if not open_clipboard(owner):
        raise OSError("Буфер обмена занят. Повторите замену.")
    try:
        handle = get_data(13)  # CF_UNICODETEXT
        if not handle:
            return ""
        ptr = lock(handle)
        if not ptr:
            raise C.WinError(C.get_last_error())
        try:
            return C.wstring_at(ptr)
        finally:
            unlock(handle)
    finally:
        close_clipboard()


def write_clipboard(owner, text):
    raw = text.encode("utf-16-le") + b"\x00\x00"
    handle = alloc(0x0002, len(raw))  # GMEM_MOVEABLE
    if not handle:
        raise MemoryError("Не удалось выделить память для текста.")
    try:
        ptr = lock(handle)
        if not ptr:
            raise C.WinError(C.get_last_error())
        try:
            C.memmove(ptr, raw, len(raw))
        finally:
            unlock(handle)
        if not open_clipboard(owner):
            raise OSError("Буфер обмена занят. Повторите замену.")
        try:
            if not empty() or not set_data(13, handle):
                raise C.WinError(C.get_last_error())
            handle = None  # Ownership passed to Windows.
        finally:
            close_clipboard()
    finally:
        if handle:
            free(handle)


class HotkeyService:
    """Own message queue, so Tk's event loop cannot swallow WM_HOTKEY."""
    def __init__(self):
        self.commands = queue.Queue()
        self.events = queue.Queue()
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        registered = set()
        msg = W.MSG()
        try:
            while not self.stopping.is_set():
                while True:
                    try:
                        action, args, response = self.commands.get_nowait()
                    except queue.Empty:
                        break
                    if action == "register":
                        key_id, modifiers, vk = args
                        ok = bool(_register(None, key_id, modifiers, vk))
                        if ok:
                            registered.add(key_id)
                    else:
                        key_id, = args
                        ok = bool(_unregister(None, key_id))
                        registered.discard(key_id)
                    response.put(ok)
                while peek(C.byref(msg), None, 0x0312, 0x0312, 1):
                    self.events.put(msg.wParam)
                self.stopping.wait(0.02)
        finally:
            for key_id in registered:
                _unregister(None, key_id)

    def request(self, action, *args):
        response = queue.Queue()
        self.commands.put((action, args, response))
        return response.get(timeout=2)

    def register(self, key_id, modifiers, vk):
        return self.request("register", key_id, modifiers, vk)

    def unregister(self, key_id):
        return self.request("unregister", key_id)

    def hotkeys(self):
        while True:
            try:
                yield self.events.get_nowait()
            except queue.Empty:
                return

    def close(self):
        self.stopping.set()
        self.thread.join(timeout=2)

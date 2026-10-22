"""
AitMate Desktop AI Assistant — Windows System Tray Companion Daemon
Provides persistent system tray access, background execution, and global hotkeys.
"""

import os
import sys
import webbrowser
import threading
import subprocess
import urllib.request
import json
import win32api
import win32con
import win32gui

WM_TRAYMESSAGE = win32con.WM_USER + 20
ID_TRAY_OPEN_QUICK = 1001
ID_TRAY_OPEN_FULL = 1002
ID_TRAY_CHECK_HEALTH = 1003
ID_TRAY_EXIT = 1004
HOTKEY_ID_ALT_A = 2001

FRONTEND_URL = "http://localhost:5173"
BACKEND_HEALTH_URL = "http://127.0.0.1:8000/api/v1/health"

class AitMateTrayIcon:
    def __init__(self):
        self.class_name = "AitMateTrayWndClass"
        self.hwnd = None
        self.hicon = None

    def register_window_class(self):
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = self.class_name
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = self.wnd_proc

        try:
            win32gui.RegisterClass(wc)
        except win32gui.error:
            pass  # Already registered

    def create_window(self):
        self.hwnd = win32gui.CreateWindowEx(
            0,
            self.class_name,
            "AitMate System Tray Daemon",
            win32con.WS_OVERLAPPED | win32con.WS_SYSMENU,
            0, 0, 0, 0,
            0, 0,
            win32api.GetModuleHandle(None),
            None
        )
        win32gui.UpdateWindow(self.hwnd)

        # Load standard app icon
        self.hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        # Add Tray Icon to Taskbar Notification Area
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, WM_TRAYMESSAGE, self.hicon, "AitMate Desktop AI (Active)")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

        # Register Global Windows Hotkey: Alt + A
        # MOD_ALT = 0x0001
        try:
            win32api.RegisterHotKey(self.hwnd, HOTKEY_ID_ALT_A, win32con.MOD_ALT, ord('A'))
            print("[AitMate Tray] Global hotkey registered: Alt + A")
        except Exception as e:
            print(f"[AitMate Tray] Could not register global hotkey Alt+A: {e}")

    def open_assistant(self):
        """Open or focus the AitMate assistant frontend."""
        try:
            webbrowser.open(FRONTEND_URL)
        except Exception as e:
            print(f"[AitMate Tray] Error opening assistant: {e}")

    def check_health(self):
        """Query backend health and show a Windows balloon notification."""
        try:
            req = urllib.request.Request(BACKEND_HEALTH_URL, headers={"User-Agent": "AitMateTray/0.1"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                status = data.get("status", "unknown")
                provider = data.get("active_provider", "groq")
                msg = f"Status: {status.upper()} | Provider: {provider}"
                win32gui.Shell_NotifyIcon(
                    win32gui.NIM_MODIFY,
                    (self.hwnd, 0, win32gui.NIF_INFO, WM_TRAYMESSAGE, self.hicon, "AitMate", msg, 200, "AitMate Health")
                )
        except Exception as e:
            win32gui.Shell_NotifyIcon(
                win32gui.NIM_MODIFY,
                (self.hwnd, 0, win32gui.NIF_INFO, WM_TRAYMESSAGE, self.hicon, "AitMate", f"Backend offline: {e}", 200, "AitMate Warning")
            )

    def show_popup_menu(self):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_TRAY_OPEN_QUICK, "Open Quick Assistant (Alt + A)")
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_TRAY_OPEN_FULL, "Open Command Center")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_TRAY_CHECK_HEALTH, "Check Backend Status")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_TRAY_EXIT, "Exit AitMate")

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_RIGHTBUTTON, pos[0], pos[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYMESSAGE:
            if lparam == win32con.WM_LBUTTONUP or lparam == win32con.WM_LBUTTONDBLCLK:
                self.open_assistant()
            elif lparam == win32con.WM_RBUTTONUP:
                self.show_popup_menu()
            return 0

        elif msg == win32con.WM_COMMAND:
            cmd = win32api.LOWORD(wparam)
            if cmd in (ID_TRAY_OPEN_QUICK, ID_TRAY_OPEN_FULL):
                self.open_assistant()
            elif cmd == ID_TRAY_CHECK_HEALTH:
                self.check_health()
            elif cmd == ID_TRAY_EXIT:
                win32gui.DestroyWindow(self.hwnd)
            return 0

        elif msg == win32con.WM_HOTKEY:
            if wparam == HOTKEY_ID_ALT_A:
                print("[AitMate Tray] Global hotkey Alt+A pressed! Opening assistant...")
                self.open_assistant()
            return 0

        elif msg == win32con.WM_DESTROY:
            # Unregister hotkey and remove tray icon
            try:
                win32api.UnregisterHotKey(self.hwnd, HOTKEY_ID_ALT_A)
            except Exception:
                pass
            nid = (self.hwnd, 0)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def run(self):
        self.register_window_class()
        self.create_window()
        print("[AitMate Tray] System Tray Companion running in Windows Notification Area.")
        print("[AitMate Tray] Press Alt+A anywhere on Windows to summon AitMate.")
        win32gui.PumpMessages()

if __name__ == "__main__":
    app = AitMateTrayIcon()
    app.run()

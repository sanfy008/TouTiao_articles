"""
Browser Utilities for Toutiao Publisher Skill
Handles browser launching, stealth features, and common interactions
"""

import os
import sys
import json
import time
import socket
import random
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional

from patchright.sync_api import Playwright, BrowserContext, Page
from config import BROWSER_PROFILE_DIR, STATE_FILE, BROWSER_ARGS


def find_chrome_executable() -> Optional[str]:
    """Find installed Google Chrome executable path on current platform."""
    env_path = os.environ.get("CHROME_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    if sys.platform == "win32":
        try:
            import winreg

            for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for subkey in [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                ]:
                    try:
                        with winreg.OpenKey(root, subkey) as key:
                            val, _ = winreg.QueryValueEx(key, "")
                            if val and os.path.isfile(val):
                                return val
                    except OSError:
                        pass
        except ImportError:
            pass

        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Google\Chrome Dev\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome Dev\Application\chrome.exe"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path

    which_chrome = shutil.which("chrome") or shutil.which("google-chrome")
    if which_chrome and os.path.isfile(which_chrome):
        return which_chrome

    return None


def get_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cleanup_profile_processes(profile_dir: str):
    """Ensure no stale browser processes are locking the profile directory."""
    if sys.platform != "win32":
        return
    norm_path = str(Path(profile_dir).resolve()).lower()
    ps_cmd = (
        'Get-CimInstance Win32_Process -Filter "Name = \'chrome.exe\'" | '
        'Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress'
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
        )
        if not res.stdout.strip():
            return
        data = json.loads(res.stdout)
        if isinstance(data, dict):
            data = [data]
        for item in data:
            cmd = (item.get("CommandLine") or "").lower()
            if norm_path in cmd:
                pid = item.get("ProcessId")
                if pid:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True,
                        timeout=3,
                    )
    except Exception:
        pass


def reset_profile_crash_state(profile_dir: str):
    """Reset exit_type to Normal in Preferences to prevent 'Restore pages?' modal popup."""
    try:
        pref_path = Path(profile_dir) / "Default" / "Preferences"
        if pref_path.exists():
            with open(pref_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            modified = False
            if "profile" in data and isinstance(data["profile"], dict):
                if data["profile"].get("exit_type") != "Normal":
                    data["profile"]["exit_type"] = "Normal"
                    data["profile"]["exited_cleanly"] = True
                    modified = True
            if modified:
                with open(pref_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
    except Exception:
        pass


def force_window_to_foreground(target_pid: int, timeout_sec: float = 4.0) -> bool:
    """Force the Chrome window belonging to target_pid to the foreground on Windows."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        start_t = time.time()
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        while time.time() - start_t < timeout_sec:
            found_hwnds = []

            def enum_cb(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value == target_pid:
                        rect = wintypes.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        width = rect.right - rect.left
                        height = rect.bottom - rect.top
                        # Prefer primary browser windows over tiny dialogs/tooltips
                        if width > 300 and height > 200:
                            found_hwnds.append(hwnd)
                return True

            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            if found_hwnds:
                hwnd = found_hwnds[0]
                SW_SHOWMAXIMIZED = 3
                SW_RESTORE = 9
                HWND_TOPMOST = -1
                HWND_NOTOPMOST = -2
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_SHOWWINDOW = 0x0040

                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.ShowWindow(hwnd, SW_SHOWMAXIMIZED)
                user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE
                )
                user32.SetWindowPos(
                    hwnd,
                    HWND_NOTOPMOST,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
                )
                user32.SwitchToThisWindow(hwnd, True)
                user32.BringWindowToTop(hwnd)

                cur_thread = kernel32.GetCurrentThreadId()
                fg_hwnd = user32.GetForegroundWindow()
                fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
                if fg_thread and fg_thread != cur_thread:
                    user32.AttachThreadInput(cur_thread, fg_thread, True)
                    user32.SetForegroundWindow(hwnd)
                    user32.AttachThreadInput(cur_thread, fg_thread, False)
                else:
                    user32.SetForegroundWindow(hwnd)
                return True
            time.sleep(0.2)
    except Exception:
        pass
    return False


class BrowserFactory:
    """Factory for creating configured browser contexts"""

    @staticmethod
    def launch_persistent_context(
        playwright: Playwright,
        headless: bool = True,
        user_data_dir: str = str(BROWSER_PROFILE_DIR),
        state_file: str = str(STATE_FILE),
    ) -> BrowserContext:
        """
        Launch a persistent browser context with anti-detection features
        and cookie workaround.
        """
        if not headless and sys.platform == "win32":
            chrome_exe = find_chrome_executable()
            if chrome_exe:
                try:
                    return BrowserFactory._launch_native_cdp_context(
                        playwright,
                        chrome_exe=chrome_exe,
                        user_data_dir=user_data_dir,
                        state_file=state_file,
                    )
                except Exception as e:
                    print(
                        f"  ⚠️  Native Chrome CDP launch failed ({e}), falling back to standard launch..."
                    )

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",  # Use real Chrome
            headless=headless,
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            args=BROWSER_ARGS,
        )

        # Cookie Workaround for Playwright bug #36139
        # Session cookies (expires=-1) don't persist in user_data_dir automatically
        BrowserFactory._inject_cookies(context, state_file=state_file)
        return context

    @staticmethod
    def _launch_native_cdp_context(
        playwright: Playwright,
        chrome_exe: str,
        user_data_dir: str,
        state_file: str,
    ) -> BrowserContext:
        """Launch native Chrome process on Windows and connect via CDP for guaranteed visible GUI."""
        cleanup_profile_processes(user_data_dir)
        Path(user_data_dir).mkdir(parents=True, exist_ok=True)
        reset_profile_crash_state(user_data_dir)
        port = get_free_port()

        cmd = [
            chrome_exe,
            f"--remote-debugging-port={port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized",
        ]

        existing_arg_prefixes = {arg.split("=")[0] for arg in cmd}
        for arg in BROWSER_ARGS:
            prefix = arg.split("=")[0]
            if prefix not in existing_arg_prefixes:
                cmd.append(arg)

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        cdp_url = f"http://127.0.0.1:{port}"
        connected = False
        start_t = time.time()
        while time.time() - start_t < 6.0:
            if proc.poll() is not None:
                raise RuntimeError(
                    f"Chrome process exited unexpectedly with code {proc.returncode}"
                )
            try:
                with urllib.request.urlopen(f"{cdp_url}/json/version", timeout=1) as resp:
                    if resp.status == 200:
                        connected = True
                        break
            except Exception:
                time.sleep(0.2)

        if not connected:
            proc.terminate()
            raise TimeoutError(
                f"Timed out waiting for Chrome DevTools server on port {port}"
            )

        browser = playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()

        # Force Chrome window into the foreground on Windows
        force_window_to_foreground(proc.pid)
        context.bring_to_front = lambda: force_window_to_foreground(proc.pid)

        orig_close = context.close

        def clean_close():
            try:
                orig_close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            reset_profile_crash_state(user_data_dir)

        context.close = clean_close

        BrowserFactory._inject_cookies(context, state_file=state_file)
        return context

    @staticmethod
    def _inject_cookies(context: BrowserContext, state_file=STATE_FILE):
        """Inject cookies from state.json if available"""
        state_file = Path(state_file)
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    if "cookies" in state and len(state["cookies"]) > 0:
                        context.add_cookies(state["cookies"])
                        # print(f"  🔧 Injected {len(state['cookies'])} cookies from state.json")
            except Exception as e:
                print(f"  ⚠️  Could not load state.json: {e}")


class StealthUtils:
    """Human-like interaction utilities"""

    @staticmethod
    def random_delay(min_ms: int = 100, max_ms: int = 500):
        """Add random delay"""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    @staticmethod
    def human_type(
        page: Page, selector: str, text: str, wpm_min: int = 320, wpm_max: int = 480
    ):
        """Type with human-like speed"""
        element = page.query_selector(selector)
        if not element:
            # Try waiting if not immediately found
            try:
                element = page.wait_for_selector(selector, timeout=2000)
            except:
                pass

        if not element:
            print(f"⚠️ Element not found for typing: {selector}")
            return

        # Click to focus
        element.click()

        # Type
        for char in text:
            element.type(char, delay=random.uniform(25, 75))
            if random.random() < 0.05:
                time.sleep(random.uniform(0.15, 0.4))

    @staticmethod
    def realistic_click(page: Page, selector: str):
        """Click with realistic movement"""
        element = page.query_selector(selector)
        if not element:
            return

        # Optional: Move mouse to element (simplified)
        box = element.bounding_box()
        if box:
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
            page.mouse.move(x, y, steps=5)

        StealthUtils.random_delay(100, 300)
        element.click()
        StealthUtils.random_delay(100, 300)

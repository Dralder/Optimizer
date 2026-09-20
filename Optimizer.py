import os
import shutil
import subprocess
import ctypes
import sys
import time
from datetime import datetime, timedelta

VERSION = "v1.1.0"

CREATE_NO_WINDOW = 0x08000000

SERVICES_TO_STOP = [
    "wuauserv", "bits", "dosvc", "SysMain", "WSearch",
    "DiagTrack", "dmwappushservice", "RemoteRegistry", "PrintNotify",
    "Spooler", "MapsBroker", "WerSvc", "PcaSvc", "TrkWks", "lfsvc",
    "WaaSMedicSvc", "DusmSvc", "RetailDemo",
    "XblAuthManager", "XblGameSave", "XboxNetApiSvc"
]

MIN_FILE_AGE_MINUTES = 15
TEMP_CLEAN_INTERVAL_SECONDS = 1800
SERVICE_CHECK_INTERVAL_SECONDS = 60


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def get_time():
    return datetime.now().strftime("%H:%M:%S")


def log(tag, msg):
    print(f"[{get_time()}] [{tag}] {msg}")


def get_safe_temp_paths():
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    candidates = [
        os.environ.get('TEMP'),
        os.path.join(local_app_data, 'Temp') if local_app_data else None,
        os.path.join(local_app_data, 'CrashDumps') if local_app_data else None,
        os.path.join(local_app_data, 'Microsoft', 'Windows', 'INetCache') if local_app_data else None,
    ]
    return [p for p in candidates if p and os.path.exists(p)]


def is_old_enough(path):
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return datetime.now() - mtime > timedelta(minutes=MIN_FILE_AGE_MINUTES)
    except OSError:
        return False


def clean_temp_folders():
    log("CLEANUP", "Scanning safe temp folders...")
    deleted = 0
    for path in get_safe_temp_paths():
        try:
            items = os.listdir(path)
        except OSError:
            continue
        for item in items:
            item_path = os.path.join(path, item)
            if not is_old_enough(item_path):
                continue
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                    deleted += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                    deleted += 1
            except OSError:
                continue
    log("CLEANUP", f"Removed {deleted} item(s) older than {MIN_FILE_AGE_MINUTES} min.")


def stop_services():
    stopped = 0
    for service in SERVICES_TO_STOP:
        try:
            result = subprocess.run(
                ["sc", "query", service],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW, text=True
            )
            if "RUNNING" in result.stdout:
                subprocess.run(
                    ["sc", "stop", service],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW
                )
                stopped += 1
        except Exception:
            continue
    return stopped


def apply_network_tweaks():
    log("NETWORK", "Applying global TCP stack tweaks...")
    commands = [
        ["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"],
        ["netsh", "int", "tcp", "set", "global", "ecncapability=disabled"],
        ["netsh", "int", "tcp", "set", "heuristics", "disabled"],
    ]
    for cmd in commands:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
    log("NETWORK", "Done.")


def apply_game_settings():
    log("GAME", "Applying user-level game settings...")
    commands = [
        ["reg", "add", r"HKCU\System\GameConfigStore", "/v", "GameDVR_Enabled",
         "/t", "REG_DWORD", "/d", "0", "/f"],
        ["reg", "add", r"HKCU\System\GameConfigStore", "/v", "GameDVR_FSEBehaviorMode",
         "/t", "REG_DWORD", "/d", "2", "/f"],
        ["reg", "add", r"HKCU\System\GameConfigStore", "/v", "GameDVR_HonorUserFSEBehaviorMode",
         "/t", "REG_DWORD", "/d", "1", "/f"],
        ["reg", "add", r"HKCU\Software\Microsoft\GameBar", "/v", "AutoGameModeEnabled",
         "/t", "REG_DWORD", "/d", "1", "/f"],
    ]
    for cmd in commands:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
    log("GAME", "Done.")


def watchdog_tick():
    restarted = stop_services()
    if restarted:
        log("SERVICES", f"Re-stopped {restarted} service(s) Windows had restarted.")


if __name__ == "__main__":
    if not is_admin():
        script_path = os.path.abspath(__file__)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
        sys.exit()

    os.system('cls' if os.name == 'nt' else 'clear')
    print("==============================================")
    print("          GAMING OPTIMIZER ACTIVATED           ")
    print(f"                {VERSION} by Dralder")
    print("==============================================")

    try:
        log("SETUP", "Running one-time optimizations...")
        clean_temp_folders()
        stop_services()
        apply_network_tweaks()
        apply_game_settings()
        log("SETUP", "Initial optimization complete. Entering background watchdog mode.")
        print("----------------------------------------------")

        last_temp_clean = time.time()
        while True:
            time.sleep(SERVICE_CHECK_INTERVAL_SECONDS)
            watchdog_tick()
            if time.time() - last_temp_clean >= TEMP_CLEAN_INTERVAL_SECONDS:
                clean_temp_folders()
                last_temp_clean = time.time()

    except KeyboardInterrupt:
        log("EXIT", "Stopped by user. Services/settings remain applied.")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")

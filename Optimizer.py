import os
import shutil
import subprocess
import ctypes
import sys
import time
from datetime import datetime

CREATE_NO_WINDOW = 0x08000000

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_time():
    return datetime.now().strftime("%H:%M:%S")

def clean_temp_folders():
    print(f"[{get_time()}] [CLEANUP] Starting temporary file removal...")
    
    system_root = os.environ.get('SystemRoot', 'C:\\Windows')
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    
    temp_paths = [
        os.environ.get('TEMP'),
        os.path.join(system_root, 'Temp'),
        os.path.join(system_root, 'Prefetch'),
        os.path.join(system_root, 'ServiceProfiles', 'LocalService', 'AppData', 'Local', 'Temp'),
        os.path.join(system_root, 'ServiceProfiles', 'NetworkService', 'AppData', 'Local', 'Temp'),
        os.path.join(system_root, 'SoftwareDistribution', 'Download'),
        os.path.join(system_root, 'System32', 'LogFiles'),
        os.path.join(local_app_data, 'CrashDumps') if local_app_data else None,
        os.path.join(local_app_data, 'Microsoft', 'Windows', 'INetCache') if local_app_data else None
    ]
    
    files_deleted = 0
    for path in temp_paths:
        if not path or not os.path.exists(path): 
            continue
            
        subprocess.run(['takeown', '/f', path, '/r', '/d', 'y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        subprocess.run(['icacls', path, '/grant', 'administrators:F', '/t'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)

        try:
            items = os.listdir(path)
        except:
            continue
            
        for item in items:
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                    files_deleted += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    files_deleted += 1
            except:
                continue
                
    print(f"[{get_time()}] [CLEANUP] Successfully cleared {files_deleted} items.")

def stop_background_hogs():
    print(f"[{get_time()}] [SERVICES] Suspending background hogs...")
    services = [
        "wuauserv", "bits", "dosvc", "SysMain", "WSearch", 
        "DiagTrack", "dmwappushservice", "RemoteRegistry", 
        "PrintNotify", "Spooler", "MapsBroker", "WerSvc", 
        "PcaSvc", "TrkWks", "lfsvc", "WaaSMedicSvc", 
        "DusmSvc", "RetailDemo", "XblAuthManager", 
        "XblGameSave", "XboxNetApiSvc"
    ]
    for service in services:
        try:
            subprocess.run(["sc", "stop", service], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["sc", "config", service, "start=", "demand"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        except:
            continue
    print(f"[{get_time()}] [SERVICES] All targeted services are paused.")

def flush_ram():
    print(f"[{get_time()}] [MEMORY] Flushing unused RAM...")
    try:
        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
    except:
        pass

if __name__ == "__main__":
    if is_admin():
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("==============================================")
            print("            OPTIMIZER ACTIVATED               ")
            print("==============================================")
            while True:
                clean_temp_folders()
                stop_background_hogs()
                flush_ram()
                print(f"[{get_time()}] [IDLE] Optimization complete. Sleeping for 20 mins...")
                print("----------------------------------------------")
                time.sleep(1200) 
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to exit...")
    else:
        script_path = os.path.abspath(__file__)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)

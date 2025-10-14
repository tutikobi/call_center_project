# call_center_project/desktop_agent/monitors/windows_monitor.py
import win32gui
import win32process
import psutil
import uiautomation as uia

def get_browser_url(process_name):
    try:
        if "chrome.exe" in process_name or "msedge.exe" in process_name:
            control = uia.EditControl(ClassName='Chrome_OmniboxView')
            return control.GetValuePattern().Value
        elif "firefox.exe" in process_name:
            control = uia.EditControl(Name='Barra de endereço e de pesquisa')
            return control.GetValuePattern().Value
    except Exception:
        return None

def get_active_window_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd: return None
        
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        process_name = process.name()
        window_title = win32gui.GetWindowText(hwnd)
        
        url = None
        if process_name.lower() in ["chrome.exe", "firefox.exe", "msedge.exe"]:
            url = get_browser_url(process_name)

        return {"title": window_title, "process": process_name, "url": url}
    except (psutil.NoSuchProcess, psutil.AccessDenied, win32gui.error):
        return None
    except Exception:
        return None
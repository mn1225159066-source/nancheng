import sys
import os
import socket
import threading
import time
import webbrowser
import subprocess
import multiprocessing
from http.server import BaseHTTPRequestHandler, HTTPServer

# Ensure support for multiprocessing (crucial for PyInstaller on macOS/Windows)
multiprocessing.freeze_support()

def resolve_path(path):
    if getattr(sys, "frozen", False):
        candidates = []
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(os.path.join(meipass, path))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, path))
        # macOS .app bundle Resources
        app_root = os.path.abspath(os.path.join(exe_dir, "..", ".."))
        resources_dir = os.path.join(app_root, "Resources")
        candidates.append(os.path.join(resources_dir, path))
        # Sibling collected folder (when .app sits next to onedir folder)
        collected_dir = os.path.abspath(os.path.join(app_root, "..", os.path.basename(app_root)))
        candidates.append(os.path.join(collected_dir, path))
        for p in candidates:
            if os.path.exists(p):
                return p
        return os.path.join(exe_dir, path)
    else:
        basedir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(basedir, path)

def get_free_port():
    """Find a free port on localhost"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]
    except:
        return 8501 # Fallback

def wait_for_server(port, timeout=60):
    """Wait for server to start listening on port"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(1)
    return False

def wait_for_http_ready(port, timeout=90):
    try:
        import requests
    except Exception:
        return True
    start = time.time()
    url = f"http://127.0.0.1:{port}/"
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200 and len(r.text) > 100:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def open_browser(port):
    if not (wait_for_server(port) and wait_for_http_ready(port)):
        return
    url = f"http://127.0.0.1:{port}/?start=1"
    # Always use the default system browser to open app UI.
    # Do NOT start a remote-debugging browser here to avoid interfering with CDP session used for cookie.
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', url], check=False)
        else:
            webbrowser.open(url)
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass

def open_url(url):
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', url], check=False)
        else:
            webbrowser.open(url)
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass

def detect_default_browser():
    try:
        import sys
        if sys.platform != 'win32':
            return None
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice")
        progid, _ = winreg.QueryValueEx(key, "ProgId")
        s = str(progid).lower()
        if "chrome" in s:
            return "chrome"
        if "edge" in s:
            return "edge"
        return None
    except Exception:
        return None

def find_debug_port():
    try:
        import requests
        port = os.environ.get('FANQIE_REMOTE_DEBUG_PORT')
        if port:
            try:
                r = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=0.5)
                if r.status_code == 200:
                    return port
            except Exception:
                pass
        for p in range(9222, 9236):
            try:
                r = requests.get(f"http://127.0.0.1:{p}/json/version", timeout=0.5)
                if r.status_code == 200:
                    return str(p)
            except Exception:
                continue
    except Exception:
        pass
    return None

def open_default_debug_browser():
    # If a debug session already exists, reuse it
    if os.environ.get('FANQIE_DEBUG_STARTED') == '1':
        return
    if find_debug_port():
        os.environ['FANQIE_DEBUG_STARTED'] = '1'
        return
    local = os.environ.get('LOCALAPPDATA') or ''
    chrome_paths = [
        os.path.join(local, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ]
    exe = None
    for p in chrome_paths:
        if os.path.exists(p):
            exe = p; break
    if not exe:
        return
    # Choose user profile dir (Default)
    base = os.path.join(local, 'Google', 'Chrome', 'User Data')
    user_data_dir = os.path.join(base, 'Default')
    if not os.path.exists(user_data_dir):
        try:
            os.makedirs(user_data_dir, exist_ok=True)
        except Exception:
            pass
    debug_port = os.environ.get('FANQIE_REMOTE_DEBUG_PORT') or '9225'
    os.environ['FANQIE_REMOTE_DEBUG_PORT'] = debug_port
    args = [
        exe,
        f"--remote-debugging-port={debug_port}",
        f"--remote-allow-origins=http://127.0.0.1:{debug_port}",
        f"--user-data-dir={user_data_dir}",
        "https://fanqienovel.com/"
    ]
    try:
        subprocess.Popen(args, close_fds=True)
        os.environ['FANQIE_DEBUG_STARTED'] = '1'
    except Exception:
        return
    # Wait until debug port becomes ready
    try:
        import requests, time as _t
        start = _t.time()
        while _t.time() - start < 2:
            try:
                r = requests.get(f"http://127.0.0.1:{debug_port}/json/version", timeout=0.4)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            _t.sleep(0.2)
    except Exception:
        pass

import traceback

if __name__ == "__main__":
    log_path = "/tmp/fanqie_startup.log"
    try:
        f = open(log_path, 'w', encoding='utf-8', buffering=1)
        sys.stdout = f
        sys.stderr = f
        print(f"Startup log initialized at {time.ctime()}")
        print(f"Executable: {sys.executable}")
        print(f"Frozen: {getattr(sys, 'frozen', False)}")
        print(f"Platform: {sys.platform}")
    except Exception as e:
        try:
            with open("/tmp/fanqie_startup_error.txt", "w") as f2:
                f2.write(f"Failed to setup logging: {e}\n")
        except Exception:
            pass
    try:
        from streamlit.web import cli as stcli
    except Exception as e:
        print("Import streamlit failed")
        print(str(e))
        time.sleep(1)
        raise

    app_path = resolve_path(os.path.join("src", "ui", "app.py"))
    
    # --- LOCK FILE LOGIC START ---
    lock_file = os.path.join(os.path.expanduser("~"), ".fanqie_lock")
    
    # Check if lock file exists
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                existing_port = int(f.read().strip())
            print(f"Checking existing instance on port {existing_port}...")
            ready = False
            try:
                import requests
                r = requests.get(f"http://127.0.0.1:{existing_port}/", timeout=2)
                if r.status_code == 200 and len(r.text) > 100:
                    ready = True
            except Exception:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        ready = s.connect_ex(('127.0.0.1', existing_port)) == 0
                except Exception:
                    ready = False
            if ready:
                print(f"Found active instance on port {existing_port}. Opening browser.")
                open_url(f"http://127.0.0.1:{existing_port}/?start=1")
                sys.exit(0)
            else:
                print(f"Existing lock is stale or not ready. Starting new instance.")
        except Exception as e:
            print(f"Error checking lock file: {e}")

    # 1. Get a random free port
    port = get_free_port()
    shutdown_port = get_free_port()

    child_proc = None

    class ShutdownHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith('/shutdown'):
                self.send_response(200)
                self.end_headers()
                def _shutdown():
                    try:
                        if child_proc is not None:
                            child_proc.terminate()
                            try:
                                child_proc.wait(timeout=1)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    time.sleep(0.1)
                    os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, format, *args):
            return
        def do_POST(self):
            if self.path.startswith('/shutdown'):
                # Drain body if any
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                except:
                    length = 0
                if length > 0:
                    try:
                        _ = self.rfile.read(length)
                    except:
                        pass
                self.send_response(200)
                self.end_headers()
                def _shutdown():
                    try:
                        if child_proc is not None:
                            child_proc.terminate()
                            try:
                                child_proc.wait(timeout=1)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    time.sleep(0.1)
                    os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()
            else:
                self.send_response(404)
                self.end_headers()

    def start_shutdown_server(p):
        srv = HTTPServer(('127.0.0.1', p), ShutdownHandler)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        return p

    start_shutdown_server(shutdown_port)
    os.environ['FANQIE_SHUTDOWN_PORT'] = str(shutdown_port)
    
    # Write new lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(port))
    except Exception as e:
        print(f"Failed to write lock file: {e}")
    # --- LOCK FILE LOGIC END ---

    # Start a default browser debug session early so that '自动获取 Cookie' is instant
    try:
        threading.Thread(target=open_default_debug_browser, name="InitDebugBrowser", daemon=True).start()
    except Exception:
        pass

    # 2. Start browser opener in a separate thread
    # Daemon=True ensures it dies when main thread dies
    t = threading.Thread(target=open_browser, args=(port,), daemon=True)
    t.start()

    # 3. Configure Streamlit and run in-process for PyInstaller windowed bundle
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--browser.serverAddress=127.0.0.1",
        "--browser.gatherUsageStats=false",
        "--theme.base=light",
    ]
    try:
        sys.exit(stcli.main())
    except Exception:
        print("CRITICAL ERROR DURING STARTUP:")
        traceback.print_exc()
        time.sleep(1)
        raise

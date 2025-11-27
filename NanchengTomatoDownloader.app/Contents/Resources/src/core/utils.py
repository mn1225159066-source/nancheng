import requests
import base64
import platform
import subprocess
import re
import os
import datetime

# Default User Agents (Fallbacks)
UA_CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
UA_EDGE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
UA_FIREFOX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
UA_MACOS_CHROME = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
UA_SAFARI = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

def log_debug(message):
    """Log debug message to a file on Desktop"""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        log_file = os.path.join(desktop, "fanqie_debug.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def get_real_chrome_version():
    """Try to detect the installed Chrome version on macOS"""
    if platform.system() != 'Darwin':
        return None
    
    try:
        # Standard path for Google Chrome on macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=1)
            # Output format: "Google Chrome 142.0.7444.176"
            version_match = re.search(r"Google Chrome (\d+\.\d+\.\d+\.\d+)", result.stdout)
            if version_match:
                full_ver = version_match.group(1)
                log_debug(f"Detected Chrome version: {full_ver}")
                return full_ver
    except Exception as e:
        log_debug(f"Failed to detect Chrome version: {e}")
    
    return None

def get_headers(cookie_str=None, user_agent=None):
    """
    Returns headers for requests, including User-Agent and optional Cookie.
    """
    log_debug(f"Generating headers with UA: {user_agent}")
    if cookie_str:
        log_debug(f"Cookie length: {len(cookie_str)}")
        if "sessionid" in cookie_str:
            log_debug("Cookie contains sessionid")
        else:
            log_debug("WARNING: Cookie missing sessionid")
    else:
        log_debug("No cookie provided")

    os_name = platform.system()
    
    # Try to upgrade UA if it's the default/generic one and we are on macOS Chrome
    detected_version = None
    if user_agent == UA_MACOS_CHROME or (user_agent and "Chrome/120" in user_agent):
        detected_version = get_real_chrome_version()
        if detected_version:
            # Reconstruct UA with real version
            user_agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{detected_version} Safari/537.36"
            log_debug(f"Upgraded UA to: {user_agent}")

    if not user_agent:
        if os_name == 'Windows':
            user_agent = UA_CHROME
            sec_platform = '"Windows"'
        else:
            # Attempt detection if not provided
            detected_version = get_real_chrome_version()
            if detected_version:
                user_agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{detected_version} Safari/537.36"
            else:
                user_agent = UA_MACOS_CHROME
            sec_platform = '"macOS"'
    else:
        # Simple heuristic for platform based on UA if provided
        if "Macintosh" in user_agent or "Mac OS" in user_agent:
            sec_platform = '"macOS"'
        elif "Windows" in user_agent:
            sec_platform = '"Windows"'
        else:
            sec_platform = '"Linux"' # Default/Unknown

    # Extract major version for Sec-Ch-Ua
    major_version = "131" # Default fallback
    if "Chrome/" in user_agent:
        try:
            major_version = user_agent.split("Chrome/")[1].split(".")[0]
        except:
            pass

    headers = {
        "User-Agent": user_agent,
        "Referer": "https://fanqienovel.com/",
        "Origin": "https://fanqienovel.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }
    
    # Only add Sec-Ch-Ua headers for Chrome/Chromium
    if "Chrome" in user_agent:
        headers["Sec-Ch-Ua"] = f'"Not_A Brand";v="8", "Chromium";v="{major_version}", "Google Chrome";v="{major_version}"'
        headers["Sec-Ch-Ua-Mobile"] = "?0"
        headers["Sec-Ch-Ua-Platform"] = sec_platform

    if cookie_str:
        headers["Cookie"] = cookie_str
    return headers

def download_font_as_base64(font_url):
    """
    Downloads the font from the given URL and returns it as a base64 encoded string.
    Returns None if download fails.
    """
    try:
        response = requests.get(font_url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Error downloading font: {e}")
        return None

def clean_filename(filename):
    """
    Removes invalid characters from filename.
    """
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '-', '_', '.', '(', ')', '！', '，')]).strip()

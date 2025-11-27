import streamlit as st
import sys
import os
import browser_cookie3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.scraper import FanqieScraper
from src.core.utils import clean_filename, UA_CHROME, UA_EDGE, UA_FIREFOX, UA_MACOS_CHROME, UA_SAFARI, log_debug
import platform
import subprocess
import time
import threading
from streamlit.web.server.server import Server

# --- Auto Shutdown Logic ---
def auto_shutdown_loop():
    time.sleep(2)
    idle_start = None
    had_session = False
    while True:
        try:
            current_server = Server.get_current()
            session_infos = current_server._session_info_by_id
            active_count = len(session_infos)
        except Exception:
            # 在无法读取会话信息时，按“无活动会话”处理，避免后台常驻
            active_count = 0
        if active_count > 0:
            had_session = True
            idle_start = None
        else:
            if had_session:
                if idle_start is None:
                    idle_start = time.time()
                elif time.time() - idle_start > 2.0:
                    try:
                        if len(Server.get_current()._session_info_by_id) == 0:
                            os._exit(0)
                    except Exception:
                        os._exit(0)
        time.sleep(0.5)

# Start background thread singleton
_enable_auto_shutdown = os.environ.get("STREAMLIT_DISABLE_AUTO_SHUTDOWN") not in ("1", "true", "True")
if _enable_auto_shutdown:
    found_thread = False
    for t in threading.enumerate():
        if t.name == "StreamlitAutoShutdown":
            found_thread = True
            break
    if not found_thread:
        t = threading.Thread(target=auto_shutdown_loop, name="StreamlitAutoShutdown", daemon=True)
        t.start()
# ---------------------------

st.set_page_config(page_title="洋柿子小说下载器", page_icon="🍅")

# --- Theme Management ---
if 'theme' not in st.session_state:
    st.session_state.theme = "活力橙"
allowed_themes = ["豆沙绿", "活力橙"]
if st.session_state.get('theme') not in allowed_themes:
    st.session_state.theme = "活力橙"

def get_theme_css(theme_name):
    themes = {
        
        "豆沙绿": {
            "bg": "#C7EDCC",
            "card_bg": "rgba(255, 255, 255, 0.4)",
            "text": "#2E4033",
            "border": "1px solid rgba(199, 237, 204, 0.8)",
            "shadow": "0 8px 32px 0 rgba(0, 100, 0, 0.05)",
            "input_bg": "rgba(255, 255, 255, 0.4)",
            "dropdown_bg": "rgba(255, 255, 255, 0.4)",
            "placeholder": "rgba(46,64,51,0.6)",
            "accent": "#2AA96B"
        },
        "活力橙": {
            "bg": "linear-gradient(120deg, #f6d365 0%, #fda085 100%)",
            "card_bg": "rgba(255, 255, 255, 0.45)",
            "text": "#4A2C2A",
            "border": "1px solid rgba(255, 255, 255, 0.5)",
            "shadow": "0 8px 32px 0 rgba(255, 100, 0, 0.15)",
            "input_bg": "rgba(255, 255, 255, 0.45)",
            "dropdown_bg": "rgba(255, 255, 255, 0.45)",
            "placeholder": "rgba(74,44,42,0.55)",
            "accent": "#FF9800"
        }
    }
    
    t = themes.get(theme_name, themes["活力橙"])
    
    # Text color handling for dark mode vs light mode components
    input_text_color = t['text']
    
    return f"""
    <style>
    /* Global Background */
    .stApp {{
        background: {t['bg']};
        background-attachment: fixed;
        color: {t['text']};
    }}
    
    /* Liquid Glass Effect for Containers */
    div[data-testid="stExpander"], div[data-testid="stForm"] {{
        background: {t['card_bg']};
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 16px;
        border: {t['border']};
        box-shadow: {t['shadow']};
        padding: 10px;
    }}

    /* Inputs and Selectboxes - Remove outer styling to avoid double/triple glass */
    .stTextInput > div > div, .stSelectbox > div > div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    /* Fix Browser Autofill Background - Prevent gray/yellow background on inputs */
    input:-webkit-autofill,
    input:-webkit-autofill:hover, 
    input:-webkit-autofill:focus, 
    input:-webkit-autofill:active {{
        -webkit-box-shadow: 0 0 0 30px rgba(0,0,0,0) inset !important;
        -webkit-text-fill-color: {t['text']} !important;
        transition: background-color 5000s ease-in-out 0s;
        background: transparent !important;
    }}

    .stSelectbox div[role="combobox"] {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    .stSelectbox div[role="combobox"] * {{
        background: transparent !important;
    }}
    /* Clear inner white blocks inside Select value row */
    .stSelectbox [data-baseweb="value-container"],
    .stSelectbox [data-baseweb="text-block"],
    .stSelectbox [data-baseweb="input-container"],
    .stSelectbox div[data-baseweb="select"] input {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    .stSelectbox div[data-baseweb="select"]::before,
    .stSelectbox div[data-baseweb="select"]::after,
    div[data-baseweb="input"]::before,
    div[data-baseweb="input"]::after {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    .stSelectbox [class^="css-"],
    .stSelectbox [class*=" css-"],
    .stTextInput [class^="css-"],
    .stTextInput [class*=" css-"] {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    .stMultiSelect > div > div, .stNumberInput > div > div, .stTextArea > div > div {{
        background: {t['card_bg']} !important;
        border: {t['border']} !important;
        color: {t['text']} !important;
    }}
    div[data-baseweb="input"] {{
        background: {t['card_bg']} !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: {t['border']} !important;
        color: {t['text']} !important;
        border-radius: 12px !important;
        box-shadow: {t['shadow']};
    }}
    div[data-baseweb="input"] input {{
        color: {t['text']} !important;
        background: transparent !important;
    }}
    /* Deep inner wrappers of TextInput transparent */
    .stTextInput > div > div * {{
        background: transparent !important;
    }}
    /* Ensure Cookie password input inner wrappers transparent */
    .stTextInput [type="password"],
    .stTextInput [type="password"] * {{
        background: transparent !important;
    }}
    /* Ensure inner wrappers of inputs are transparent (avoid white overlay) */
    div[data-baseweb="input"] > div {{
        background: transparent !important;
    }}
    div[data-baseweb="input"] > div > div {{
        background: transparent !important;
    }}
    div[data-baseweb="input"] * {{
        background: transparent !important;
    }}
    input, textarea {{
        color: {t['text']} !important;
        background: transparent !important;
    }}
    input::placeholder, textarea::placeholder {{
        color: {t['placeholder']} !important;
        opacity: 1 !important;
    }}
    .stMultiSelect > div > div, .stNumberInput > div > div, .stTextArea > div > div {{
        background: {t['card_bg']} !important;
        border: {t['border']} !important;
        color: {t['text']} !important;
    }}
    input, textarea {{
        color: {t['text']} !important;
        background: transparent !important;
    }}
    input::placeholder, textarea::placeholder {{
        color: {t['placeholder']} !important;
        opacity: 1 !important;
    }}
    
    /* Fix Dropdown Menu Visibility (especially for Dark Mode) */
    /* FORCE FIX for Inputs/Selects inside Expanders to remove white background */
    div[data-testid="stExpander"] div[data-baseweb="input"],
    div[data-testid="stExpander"] div[data-baseweb="select"],
    div[data-testid="stExpander"] div[data-baseweb="base-input"] {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        box-shadow: none !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    /* Remove any white background from inner input containers inside expanders */
    div[data-testid="stExpander"] .stTextInput > div > div,
    div[data-testid="stExpander"] .stSelectbox > div > div {{
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* Popover (dropdown) force light theme */
    div[data-baseweb="popover"] {{
        background: {t['dropdown_bg']} !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 12px !important;
        border: {t['border']} !important;
        box-shadow: {t['shadow']} !important;
    }}
    div[data-baseweb="popover"] *,
    div[aria-hidden="false"][data-baseweb="popover"],
    div[aria-hidden="false"][data-baseweb="popover"] * {{
        background: transparent !important;
        color: {t['text']} !important;
    }}
    div[data-baseweb="layer"] {{
        background: transparent !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }}
    div[data-baseweb="layer"] * {{
        background: transparent !important;
        color: {t['text']} !important;
    }}
    ul[data-baseweb="menu"], ul[role="listbox"] {{
        background: transparent !important;
    }}
    div[data-baseweb="menu"], div[role="listbox"] {{
        background: transparent !important;
    }}
    div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li {{
        background: transparent !important;
        color: {t['text']} !important;
    }}
    li[data-baseweb="menu-item"], li[role="option"] {{
        color: {t['text']} !important;
    }}
    li[data-baseweb="menu-item"] div, li[role="option"] div {{
        color: {t['text']} !important;
        background: transparent !important;
    }}
    li[role="option"][aria-disabled="true"] {{
        opacity: 0.7 !important;
        color: {t['text']} !important;
    }}
    li[data-baseweb="menu-item"]:hover, li[role="option"]:hover {{
        background: rgba(255,255,255,0.12) !important;
    }}
    li[aria-selected="true"][data-baseweb="menu-item"], li[aria-selected="true"][role="option"] {{
        background: rgba(255,255,255,0.18) !important;
    }}
    div[data-baseweb="select"] *, div[data-baseweb="select"] svg {{
        color: {t['text']} !important;
        fill: {t['text']} !important;
        background: transparent !important;
    }}
    div[data-baseweb="select"] {{
        background: {t['card_bg']} !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: {t['border']} !important;
        border-radius: 12px !important;
    }}
    div[data-baseweb="select"] > div {{
        background: transparent !important;
    }}
    div[data-baseweb="select"] [aria-expanded="true"] {{
        background: transparent !important;
    }}
    /* Ensure inner wrappers of selects are transparent */
    div[data-baseweb="select"] > div > div {{
        background: transparent !important;
    }}
    div[data-baseweb="select"] [role="combobox"] {{
        background: transparent !important;
    }}
    /* Tooltip bubbles (Press Enter to apply, help ?) */
    div[data-baseweb="tooltip"],
    div[role="tooltip"] {{
        background: {t['dropdown_bg']} !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        color: {t['text']} !important;
        border: {t['border']} !important;
        border-radius: 12px !important;
        box-shadow: {t['shadow']} !important;
    }}
    div[data-baseweb="tooltip"] *,
    div[role="tooltip"] * {{
        background: transparent !important;
        color: {t['text']} !important;
    }}
    div[data-baseweb="tooltip"] svg,
    div[role="tooltip"] svg {{
        fill: {t['text']} !important;
    }}
    div[data-testid="stWidgetHelp"],
    div[data-testid="stWidgetHelp"] * {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: {t['text']} !important;
    }}
    .stTextInput input {{
        background: transparent !important;
        color: {t['text']} !important;
    }}
    .stTextArea textarea {{
        background: transparent !important;
        color: {t['text']} !important;
    }}
    /* Static info/help texts transparent */
    .stMarkdown, .stText, .stCaption, .stMarkdown * , .stText * {{
        background: transparent !important;
    }}
    /* Expander header inner elements transparent to avoid white chips */
    div[data-testid="stExpander"] > div[role="button"] * {{
        background: transparent !important;
    }}
    div[data-baseweb="tag"] {{
        background: rgba(255,255,255,0.35) !important;
        color: {t['text']} !important;
        border: {t['border']} !important;
    }}
    div[data-testid="stExpander"] > div[role="button"] {{
        background: {t['card_bg']} !important;
        color: {t['text']} !important;
        border: {t['border']} !important;
    }}
    div[data-testid="stExpander"] svg {{
        fill: {t['text']} !important;
    }}
    
    /* Text Color overrides */
    h1, h2, h3, p, label, .stMarkdown, .stText, span, div {{
        color: {t['text']} !important;
    }}
    .stSelectbox label, .stTextInput label, .stMultiSelect label, .stNumberInput label {{
        color: {t['text']} !important;
    }}
    
    /* Button Styling to match */
    .stButton > button {{
        background: {t['card_bg']} !important;
        color: {t['text']} !important;
        border: {t['border']} !important;
        border-radius: 12px;
        backdrop-filter: blur(5px);
        transition: all 0.3s ease;
        font-weight: bold;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        filter: brightness(1.1);
    }}
    .stDownloadButton > button {{
        background: {t['card_bg']} !important;
        color: {t['text']} !important;
        border: {t['border']} !important;
        border-radius: 12px !important;
    }}
    /* Link Button */
    div[data-testid="stLinkButton"] a {{
        background: {t['card_bg']} !important;
        color: {t['text']} !important;
        border: {t['border']} !important;
        border-radius: 12px !important;
        text-decoration: none !important;
        padding: 8px 16px !important;
        display: inline-block;
        box-shadow: {t['shadow']};
    }}
    .stAlert {{
        border-radius: 12px !important;
        border: {t['border']} !important;
        background: {t['card_bg']} !important;
        box-shadow: {t['shadow']};
        color: {t['text']} !important;
    }}
    .stAlert * {{
        background: transparent !important;
    }}
    div[data-baseweb="notification"] {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* Hide Deploy/Toolbar */
    [data-testid="stToolbar"] {{visibility: hidden; height: 0; position: fixed;}}
    .viewerBadge_container__1QSob {{display: none;}}
    .viewerBadge_container__2Ynd {{display: none;}}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    """

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

st.title("🍅 洋柿子小说下载器")

# 安装成功提醒（首次在 /Applications 路径运行时）
try:
    exe_path = sys.executable
    if '/Applications/' in exe_path:
        marker_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'YangShiziDownloader')
        os.makedirs(marker_dir, exist_ok=True)
        marker = os.path.join(marker_dir, 'installed.flag')
        if not os.path.exists(marker):
            with open(marker, 'w') as f:
                f.write('ok')
            st.success("安装成功，已就绪！")
except Exception:
    pass

with st.expander("⚙️ 软件设置", expanded=False):
    st.write("🎨 **界面主题**")
    st.selectbox(
        "选择主题",
        ["豆沙绿", "活力橙"],
        key="theme",
        label_visibility="collapsed"
    )

# 已移除启动日志区域，保持界面简洁

# Sidebar for app control
# Removed as per user request
# with st.sidebar:
#     st.header("程序控制")
#     if st.button("🔴 关闭程序"):
#         st.warning("正在关闭程序...")
#         os._exit(0)
#     st.info("如果下载出现问题，请先尝试点击上方按钮彻底关闭程序，然后重新打开。")

st.markdown("""
**使用提示**:
1. 先在默认浏览器登录番茄小说主页。
2. 回到本页面点击“自动获取 Cookie”后再下载。
3. 下载 VIP 章节必须在默认浏览器中登录番茄会员，否则无法下载；推荐使用谷歌浏览器（Chrome）。
4. 小说主页链接是包含书名、简介、章节目录的那一页链接，请在浏览器地址栏复制该链接并粘贴到输入框。
""")
st.markdown("""
<style>
.sponsor-link {
    display: block;
    text-align: center;
    margin: 10px 0;
    padding: 10px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    text-decoration: none !important;
    color: inherit !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(5px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.sponsor-link:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border-color: rgba(255, 255, 255, 0.4);
}
</style>
<a href="https://www.bijianchuanqi.com/web/?zjwd&tuid=2" target="_blank" class="sponsor-link">
    <span style="font-size: 0.9rem; opacity: 0.9;">本软件由 </span>
    <strong style="font-size: 1rem; margin: 0 4px;">笔尖传奇AI</strong>
    <span style="font-size: 0.9rem; opacity: 0.9;"> 倾情赞助</span>
</a>
""", unsafe_allow_html=True)
st.link_button("一键打开番茄小说主页进行登录", "https://fanqienovel.com/")

# 彻底关闭程序（用于后台进程常驻时）
def request_shutdown():
    import requests
    p = os.environ.get('FANQIE_SHUTDOWN_PORT')
    if p:
        try:
            requests.get(f"http://127.0.0.1:{p}/shutdown", timeout=1)
        except Exception:
            pass

if st.button("彻底关闭程序（后台进程占用时使用）"):
    request_shutdown()
    st.success("已发送退出指令，请稍候重新打开软件。")

def get_browser_cookies(domain_name):
    log_debug(f"Attempting to load cookies for domain: {domain_name}")
    cookies = []
    try:
        cj = browser_cookie3.chrome(domain_name=domain_name)
        if len(cj) > 0:
            cookies.append(("Chrome", cj))
    except Exception as e:
        log_debug(f"Chrome default error: {e}")
    try:
        cj = browser_cookie3.edge(domain_name=domain_name)
        if len(cj) > 0:
            cookies.append(("Edge", cj))
    except Exception as e:
        log_debug(f"Edge default error: {e}")
    try:
        cj = browser_cookie3.firefox(domain_name=domain_name)
        if len(cj) > 0:
            cookies.append(("Firefox", cj))
    except Exception as e:
        log_debug(f"Firefox default error: {e}")

    try:
        local = os.environ.get('LOCALAPPDATA') or ''
        roaming = os.environ.get('APPDATA') or ''
        profiles = ['Default'] + [f'Profile {i}' for i in range(1, 21)]

        def scan_chrome_like(name, base_dir, use_edge=False):
            if not base_dir:
                return
            key_file = os.path.join(base_dir, 'Local State')
            for prof in profiles:
                paths = [
                    os.path.join(base_dir, prof, 'Network', 'Cookies'),
                    os.path.join(base_dir, prof, 'Cookies'),
                ]
                for p in paths:
                    if os.path.exists(p):
                        try:
                            if use_edge:
                                cj = browser_cookie3.edge(domain_name=domain_name, cookie_file=p)
                            else:
                                # 尝试显式传入 key_file，提高兼容能力
                                try:
                                    cj = browser_cookie3.chrome(domain_name=domain_name, cookie_file=p, key_file=key_file)
                                except TypeError:
                                    cj = browser_cookie3.chrome(domain_name=domain_name, cookie_file=p)
                            if len(cj) > 0:
                                cookies.append((name, cj))
                        except Exception as e:
                            log_debug(f"{name} profile {prof} error: {e}")

        # 官方 Chrome/Edge
        scan_chrome_like('Chrome', os.path.join(local, 'Google', 'Chrome', 'User Data'))
        scan_chrome_like('Edge', os.path.join(local, 'Microsoft', 'Edge', 'User Data'), use_edge=True)

        # 常见国产/第三方 Chromium 浏览器
        scan_chrome_like('Brave', os.path.join(local, 'BraveSoftware', 'Brave-Browser', 'User Data'))
        scan_chrome_like('Vivaldi', os.path.join(local, 'Vivaldi', 'User Data'))
        # Opera 存在于 Roaming
        opera_base = os.path.join(roaming, 'Opera Software', 'Opera Stable')
        if os.path.exists(opera_base):
            # Opera 的结构稍有不同，直接检查 Cookies 文件
            operapaths = [
                os.path.join(opera_base, 'Network', 'Cookies'),
                os.path.join(opera_base, 'Cookies'),
            ]
            for p in operapaths:
                if os.path.exists(p):
                    try:
                        cj = browser_cookie3.chrome(domain_name=domain_name, cookie_file=p)
                        if len(cj) > 0:
                            cookies.append(('Opera', cj))
                    except Exception as e:
                        log_debug(f"Opera error: {e}")

        # 国产常见：360、QQ、搜狗、2345（路径可能因版本变化）
        scan_chrome_like('360Chrome', os.path.join(local, '360Chrome', 'User Data'))
        scan_chrome_like('QQBrowser', os.path.join(local, 'Tencent', 'QQBrowser', 'User Data'))
        scan_chrome_like('SogouExplorer', os.path.join(local, 'SogouExplorer', 'User Data'))
        scan_chrome_like('2345Explorer', os.path.join(local, '2345Explorer', 'User Data'))

        # 开源 Chromium
        scan_chrome_like('Chromium', os.path.join(local, 'Chromium', 'User Data'))

    except Exception as e:
        log_debug(f"Profile scanning error: {e}")

    return cookies

def format_cookie_str(cookie_jar):
    return "; ".join([f"{c.name}={c.value}" for c in cookie_jar])

# --- Cookie helpers (robust) ---
def _format_cookie_pairs(cookie_jar):
    pairs = []
    try:
        for c in cookie_jar:
            pairs.append((c.name, c.value))
    except Exception:
        try:
            pairs = [(c.name, c.value) for c in list(cookie_jar)]
        except Exception:
            pairs = []
    return pairs

def format_cookie_str_from_list(jar_list):
    seen = {}
    for jar in jar_list:
        for name, value in _format_cookie_pairs(jar):
            seen[name] = value
    return "; ".join([f"{k}={v}" for k, v in seen.items()])

def get_possible_fanqie_cookies():
    domains = [
        "fanqienovel.com",
        ".fanqienovel.com",
        "novel.snssdk.com",
        "i.snssdk.com",
        "passport.toutiao.com",
    ]
    buckets = {}
    for d in domains:
        found = get_browser_cookies(d)
        for name, jar in found:
            buckets.setdefault(name, []).append(jar)
    return buckets

def _find_debug_port():
    port = os.environ.get('FANQIE_REMOTE_DEBUG_PORT')
    if port:
        try:
            import requests
            r = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=0.5)
            if r.status_code == 200:
                return port
        except Exception:
            pass
    try:
        import requests
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

def launch_debug_browser(open_site: bool = True):
    try:
        # If a debug port is already active, do not launch a new browser
        if _find_debug_port():
            return True
        local = os.environ.get('LOCALAPPDATA') or ''
        chrome_paths = [
            os.path.join(local, 'Google', 'Chrome', 'Application', 'chrome.exe'),
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
        edge_paths = [
            os.path.join(local, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
            r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
            r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        ]
        port = os.environ.get('FANQIE_REMOTE_DEBUG_PORT') or '9225'
        os.environ['FANQIE_REMOTE_DEBUG_PORT'] = port

        # Prefer reusing existing logged-in browser profile to read cookies
        # Try Chrome default/profile directories, then Edge; fallback to isolated profile
        chrome_base = os.path.join(local, 'Google', 'Chrome', 'User Data')
        edge_base = os.path.join(local, 'Microsoft', 'Edge', 'User Data')
        candidate_profiles = ['Default'] + [f'Profile {i}' for i in range(1, 6)]
        user_data_dir = None
        for prof in candidate_profiles:
            p = os.path.join(chrome_base, prof)
            if os.path.exists(p):
                user_data_dir = p
                break
        if user_data_dir is None:
            for prof in candidate_profiles:
                p = os.path.join(edge_base, prof)
                if os.path.exists(p):
                    user_data_dir = p
                    break
        if user_data_dir is None:
            user_data_dir = os.path.join(os.path.expanduser('~'), '.fanqie_cdp_profile')
            os.makedirs(user_data_dir, exist_ok=True)

        exe = None
        for p in chrome_paths:
            if os.path.exists(p):
                exe = p; break
        if exe is None:
            for p in edge_paths:
                if os.path.exists(p):
                    exe = p; break
        if not exe:
            return False
        args = [
            exe,
            f"--remote-debugging-port={port}",
            f"--remote-allow-origins=http://127.0.0.1:{port}",
            f"--user-data-dir={user_data_dir}",
        ]
        if open_site:
            args.append("https://fanqienovel.com/")
        subprocess.Popen(args, shell=False)
        # Wait briefly for remote debugging endpoint to become ready
        try:
            import requests, time as _t
            start = _t.time()
            while _t.time() - start < 3:
                try:
                    r = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=0.5)
                    if r.status_code == 200:
                        break
                except Exception:
                    pass
                _t.sleep(0.3)
        except Exception:
            pass
        return True
    except Exception:
        return False

def fetch_cookies_via_cdp(domain):
    try:
        import json
        import requests
        import websocket
        port = os.environ.get('FANQIE_REMOTE_DEBUG_PORT')
        if not port:
            for p in range(9222, 9236):
                try:
                    r = requests.get(f"http://127.0.0.1:{p}/json/version", timeout=0.5)
                    if r.status_code == 200:
                        port = str(p)
                        break
                except Exception:
                    continue
        if not port:
            return None
        pages = requests.get(f"http://127.0.0.1:{port}/json", timeout=2).json()
        # Only use a tab that is already on the target domain to avoid hijacking the app UI tab
        target_ws = None
        for pg in pages:
            u = pg.get('url','')
            if pg.get('type') == 'page' and domain in u and 'webSocketDebuggerUrl' in pg:
                target_ws = pg['webSocketDebuggerUrl']
                break
        if not target_ws:
            return None
        ws = websocket.create_connection(target_ws, timeout=3)
        ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        try:
            ws.recv()
        except Exception:
            pass
        ws.send(json.dumps({"id": 2, "method": "Network.getCookies"}))
        res = json.loads(ws.recv())
        ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "navigator.userAgent"}}))
        ua_res = json.loads(ws.recv())
        ws.close()
        cookies = res.get('result', {}).get('cookies', [])
        pairs = []
        for c in cookies:
            d = c.get('domain','')
            if domain in d:
                pairs.append(f"{c['name']}={c['value']}")
        cookie_str_val = "; ".join(pairs)
        ua = ua_res.get('result', {}).get('result', {}).get('value', UA_CHROME)
        if cookie_str_val:
            return cookie_str_val, ua
        return None
    except Exception:
        return None

url = st.text_input("小说主页链接", placeholder="https://fanqienovel.com/page/...")

# Cookie handling
st.markdown("### 🔑 VIP 登录 (可选)")

has_auto_cookie = bool(st.session_state.get('auto_cookie'))
if 'cdp_site_opened' not in st.session_state:
    st.session_state['cdp_site_opened'] = False

col_c1, col_c2 = st.columns([3, 1])

with col_c1:
    cookie_str = ""
    with st.expander("无法自动获取？手动输入 Cookie", expanded=False):
        cookie_str = st.text_input("Cookie (手动输入)", type="password", help="在浏览器控制台输入 document.cookie 获取")

with col_c2:
    st.write("") # Spacer
    st.write("") 
    if st.button("🖥️ 自动获取 Cookie"):
        with st.spinner("正在从浏览器获取 Cookie..."):
            done = False
            # Try CDP first (if a debug browser is already running)
            cdp = fetch_cookies_via_cdp("fanqienovel.com")
            if cdp:
                cookie_str_val, ua = cdp
                st.session_state['auto_cookie'] = cookie_str_val
                st.session_state['auto_ua'] = ua
                st.session_state['cookie_fetched_len'] = len(cookie_str_val)
                done = True
            if not done:
                if not st.session_state.get('cdp_site_opened'):
                    launched = launch_debug_browser(open_site=True)
                    st.session_state['cdp_site_opened'] = True
                else:
                    launched = launch_debug_browser(open_site=False)
                # Poll CDP for a short period to collect cookies after login
                import time as _t
                start = _t.time()
                while _t.time() - start < 12:
                    cdp = fetch_cookies_via_cdp("fanqienovel.com")
                    if cdp:
                        cookie_str_val, ua = cdp
                        st.session_state['auto_cookie'] = cookie_str_val
                        st.session_state['auto_ua'] = ua
                        st.session_state['cookie_fetched_len'] = len(cookie_str_val)
                        done = True
                        break
                    _t.sleep(1)
            if not done:
                # Fallback: read cookies directly from browser profiles for multiple related domains
                buckets = get_possible_fanqie_cookies()
                if buckets:
                    order = ["Chrome", "Edge", "Firefox"]
                    chosen_name = None
                    for n in order:
                        if n in buckets:
                            chosen_name = n; break
                    if not chosen_name:
                        chosen_name = list(buckets.keys())[0]
                    jar_list = buckets.get(chosen_name, [])
                    if jar_list:
                        cookie_str_val = format_cookie_str_from_list(jar_list)
                        ua = UA_CHROME if chosen_name == "Chrome" else (UA_EDGE if chosen_name == "Edge" else UA_FIREFOX)
                        st.session_state['auto_cookie'] = cookie_str_val
                        st.session_state['auto_ua'] = ua
                        st.session_state['cookie_fetched_len'] = len(cookie_str_val)
                        done = True
            if not done:
                st.error("未能自动获取 Cookie，请确认已在默认浏览器登录后重试")

def auto_cookie_fetch_loop():
    while True:
        try:
            if 'auto_cookie' in st.session_state and st.session_state['auto_cookie']:
                break
            cdp = fetch_cookies_via_cdp("fanqienovel.com")
            if cdp and not st.session_state.get('auto_cookie'):
                cookie_str_val, ua = cdp
                st.session_state['auto_cookie'] = cookie_str_val
                st.session_state['auto_ua'] = ua
            # Fallback multi-domain lookup
            buckets = get_possible_fanqie_cookies()
            found = []
            for name, jars in buckets.items():
                if jars:
                    found.append((name, jars))
            if found:
                order = ["Chrome", "Edge", "Firefox"]
                chosen = None
                for n in order:
                    for name, jars in found:
                        if name == n:
                            chosen = (name, jars)
                            break
                    if chosen:
                        break
                if not chosen:
                    chosen = found[0]
                name, jars = chosen
                cookie_str_val = format_cookie_str_from_list(jars)
                if name == "Chrome":
                    ua = UA_CHROME
                elif name == "Edge":
                    ua = UA_EDGE
                else:
                    ua = UA_FIREFOX
                st.session_state['auto_cookie'] = cookie_str_val
                st.session_state['auto_ua'] = ua
            time.sleep(3)
        except Exception:
            time.sleep(3)

# Start auto cookie fetch background thread once
cookie_thread_found = False
for t in threading.enumerate():
    if t.name == "AutoCookieFetch":
        cookie_thread_found = True
        break
if not cookie_thread_found:
    threading.Thread(target=auto_cookie_fetch_loop, name="AutoCookieFetch", daemon=True).start()

# Use session state cookie
if 'auto_cookie' in st.session_state:
    cookie_str = st.session_state['auto_cookie']
    if cookie_str:
        st.success("已自动填充 Cookie，无需手动输入")
        if 'cookie_fetched_len' in st.session_state:
            st.success(f"已自动获取 Cookie (长度: {st.session_state['cookie_fetched_len']} 字符)")

if 'novel_data' not in st.session_state:
    st.session_state.novel_data = None
if 'chapters' not in st.session_state:
    st.session_state.chapters = []

if st.button("获取信息"):
    if not url:
        st.error("请输入链接")
    else:
        with st.spinner("正在获取小说信息..."):
            user_agent = st.session_state.get('auto_ua')
            if not user_agent:
                user_agent = UA_MACOS_CHROME if platform.system() == 'Darwin' else UA_CHROME
            
            scraper = FanqieScraper(cookie_str, user_agent)
            metadata = scraper.get_novel_metadata(url)
            if metadata:
                st.session_state.novel_data = metadata
                st.session_state.chapters = scraper.get_chapter_list(url)
                st.success("获取成功！")
            else:
                st.error("获取失败，请检查链接或网络。")

if st.session_state.novel_data:
    novel = st.session_state.novel_data
    st.divider()
    col1, col2 = st.columns([1, 3])
    with col1:
        if novel.get('cover_url'):
            st.image(novel['cover_url'], width=150)
    with col2:
        st.subheader(novel['title'])
        st.write(f"**作者**: {novel['author']}")
        st.write(f"**章节数**: {len(st.session_state.chapters)}")

    st.divider()
    
    # Range selection
    chapter_options = [f"{i+1}. {c['title']}" for i, c in enumerate(st.session_state.chapters)]
    
    # Select All Checkbox
    select_all = st.checkbox("全选所有章节", value=True)
    
    if select_all:
        selected_chapters = st.multiselect("选择章节", chapter_options, default=chapter_options)
    else:
        selected_chapters = st.multiselect("选择章节", chapter_options)
    
    if st.button("开始下载"):
        user_agent = st.session_state.get('auto_ua')
        if not user_agent:
            user_agent = UA_MACOS_CHROME if platform.system() == 'Darwin' else UA_CHROME
                
        scraper = FanqieScraper(cookie_str, user_agent)
        
        # Determine chapters to download
        chapters_to_download = []
        if not selected_chapters:
            # Fallback if somehow nothing selected but list is empty, though 'select all' handles this
            chapters_to_download = [] 
            st.warning("请至少选择一个章节")
        else:
            indices = [int(s.split('.')[0]) - 1 for s in selected_chapters]
            chapters_to_download = [st.session_state.chapters[i] for i in sorted(indices)]

        if chapters_to_download:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Prepare result list
            downloaded_content = []
            
            completed_count = 0
            failed_count = 0
            
            import random
            
            # Single-threaded download
            for i, chapter in enumerate(chapters_to_download):
                try:
                    # Random delay to avoid detection
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    content = scraper.get_chapter_content(chapter['url']) or scraper.get_chapter_content_cdp(chapter['url'])
                    if content:
                        content['title'] = chapter['title']
                        downloaded_content.append(content)
                        completed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    log_debug(f"Error fetching {chapter['title']}: {e}")
                    failed_count += 1
                
                # Update progress
                progress = (i + 1) / len(chapters_to_download)
                progress_bar.progress(progress)
                status_text.text(f"进度: {i + 1}/{len(chapters_to_download)} (成功: {completed_count}, 失败: {failed_count})")
            
            # Filter out failed downloads (already filtered by append logic)
            valid_content = downloaded_content
            
            if not valid_content:
                st.error("所有章节下载失败！请检查：\n1. 网络连接\n2. 是否需要更新 Cookie (VIP章节)")
                status_text.text("下载失败")
            else:
                if failed_count > 0:
                    st.warning(f"下载完成，但有 {failed_count} 个章节失败。")
                else:
                    st.success("所有章节下载完成！")
                
                status_text.text("正在生成文件...")
                
                filename = clean_filename(novel['title'])
                
                file_content = scraper.generate_txt(novel, valid_content)
                file_ext = "txt"
                mime_type = "text/plain"
                    
                try:
                    save_dir = os.path.join(os.path.expanduser("~"), "bijianchuanqi")
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, f"{filename}.{file_ext}")
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(file_content)
                    st.success(f"✅ 文件已保存到: **{save_path}**")
                except Exception as e:
                    st.error(f"自动保存失败: {e}")

                st.download_button(
                    label=f"点击下载 {file_ext.upper()} 文件 (另存为)",
                    data=file_content,
                    file_name=f"{filename}.{file_ext}",
                    mime=mime_type
                )
                st.balloons()

import streamlit as st
import sys
import os
import browser_cookie3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.scraper import FanqieScraper
from src.core.utils import clean_filename, UA_CHROME, UA_EDGE, UA_FIREFOX, UA_MACOS_CHROME, UA_SAFARI, log_debug
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

st.set_page_config(page_title="南城洋柿子小说下载器", page_icon="🍅")

st.title("🍅 南城洋柿子小说下载器")

# Sidebar for app control
# Removed as per user request
# with st.sidebar:
#     st.header("程序控制")
#     if st.button("🔴 关闭程序"):
#         st.warning("正在关闭程序...")
#         os._exit(0)
#     st.info("如果下载出现问题，请先尝试点击上方按钮彻底关闭程序，然后重新打开。")

st.markdown("""
**说明**: 
1. 输入小说主页链接。
2. 点击“获取信息”查看小说详情。
3. **如果下载 VIP 章节失败，请尝试先在浏览器打开任意一章 VIP 章节，然后关闭浏览器再重试。**
""")

def get_browser_cookies(domain_name):
    """Try to load cookies from common browsers"""
    log_debug(f"Attempting to load cookies for domain: {domain_name}")
    cookies = []
    # Try Chrome
    try:
        log_debug("Checking Chrome...")
        cj = browser_cookie3.chrome(domain_name=domain_name)
        if len(cj) > 0:
            log_debug(f"Found {len(cj)} cookies in Chrome")
            cookies.append(("Chrome", cj))
        else:
             log_debug("Chrome cookies empty for domain")
    except Exception as e:
        log_debug(f"Chrome cookie error: {e}")
    
    # Try Edge
    try:
        log_debug("Checking Edge...")
        cj = browser_cookie3.edge(domain_name=domain_name)
        if len(cj) > 0:
            log_debug(f"Found {len(cj)} cookies in Edge")
            cookies.append(("Edge", cj))
        else:
             log_debug("Edge cookies empty for domain")
    except Exception as e:
        log_debug(f"Edge cookie error: {e}")
        
    # Try Firefox
    try:
        log_debug("Checking Firefox...")
        cj = browser_cookie3.firefox(domain_name=domain_name)
        if len(cj) > 0:
             log_debug(f"Found {len(cj)} cookies in Firefox")
             cookies.append(("Firefox", cj))
        else:
             log_debug("Firefox cookies empty for domain")
    except Exception as e:
        log_debug(f"Firefox cookie error: {e}")
        
    return cookies

def format_cookie_str(cookie_jar):
    return "; ".join([f"{c.name}={c.value}" for c in cookie_jar])

url = st.text_input("小说主页链接", placeholder="https://fanqienovel.com/page/...")

# Cookie handling
st.markdown("### 🔑 VIP 登录 (可选)")

# Add Browser Selection
browser_type = st.selectbox(
    "Cookie 来源浏览器 (请选择您获取 Cookie 的浏览器)",
    ["Chrome / Edge", "Safari", "Firefox"],
    help="VIP 章节下载失败时，请确保此选项与您获取 Cookie 的浏览器一致"
)

col_c1, col_c2 = st.columns([3, 1])

with col_c1:
    cookie_str = st.text_input("Cookie (手动输入)", type="password", help="在浏览器控制台输入 document.cookie 获取")

with col_c2:
    st.write("") # Spacer
    st.write("") 
    if st.button("🖥️ 自动获取 Cookie"):
        with st.spinner("正在从浏览器获取 Cookie..."):
            found_cookies = get_browser_cookies("fanqienovel.com")
            if found_cookies:
                # Prioritize Chrome or first found
                name, jar = found_cookies[0]
                cookie_str_val = format_cookie_str(jar)
                
                # Determine User-Agent based on browser
                ua = None
                if name == "Chrome":
                    if platform.system() == 'Darwin':
                        ua = UA_MACOS_CHROME
                    else:
                        ua = UA_CHROME
                elif name == "Edge":
                    ua = UA_EDGE
                elif name == "Firefox":
                    ua = UA_FIREFOX

                # We can't update text_input programmatically easily without rerun or session state
                # But we can store it in session state and reload
                st.session_state['auto_cookie'] = cookie_str_val
                st.session_state['auto_ua'] = ua
                st.success(f"已从 {name} 获取 Cookie! (长度: {len(cookie_str_val)} 字符)")
            else:
                st.error("未在常用浏览器(Chrome/Edge)中找到番茄小说 Cookie，请先在浏览器登录番茄小说网。")
                st.warning("如果浏览器已打开，请尝试关闭浏览器后重试，或检查是否已登录。")

# Use session state cookie if available and input is empty
if 'auto_cookie' in st.session_state and not cookie_str:
    cookie_str = st.session_state['auto_cookie']
    st.info("已自动填充 Cookie")

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
                if browser_type == "Safari":
                    user_agent = UA_SAFARI
                elif browser_type == "Firefox":
                    user_agent = UA_FIREFOX
                else:
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
            if browser_type == "Safari":
                user_agent = UA_SAFARI
            elif browser_type == "Firefox":
                user_agent = UA_FIREFOX
            else:
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
                    
                    content = scraper.get_chapter_content(chapter['url'])
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
                    
                # Auto-save to Desktop
                try:
                    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                    save_path = os.path.join(desktop_path, f"{filename}.{file_ext}")
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(file_content)
                    st.success(f"✅ 文件已保存到桌面: **{save_path}**")
                except Exception as e:
                    st.error(f"自动保存到桌面失败: {e}")

                st.download_button(
                    label=f"点击下载 {file_ext.upper()} 文件 (另存为)",
                    data=file_content,
                    file_name=f"{filename}.{file_ext}",
                    mime=mime_type
                )
                st.balloons()

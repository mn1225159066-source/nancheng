import requests
from bs4 import BeautifulSoup
import re
import os
import tempfile
from fontTools.ttLib import TTFont
from .utils import get_headers, download_font_as_base64, clean_filename, log_debug

# Static mapping string for Fanqie font de-obfuscation
# Derived from reverse engineering of the font glyph order
FANQIE_CHAR_MAP = (
    "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "的一是了我不人在他有这个上们来到时"
    "大地为子中你说生国年着就那和要她出也得里"
    "后自以会家可下而过天去能对小多然于心学么"
    "之都好看起发当没成只如事把还用第样道想作"
    "种开美总从无情己面最女但现前些所同日手又"
    "行意动方期它头经长儿回位分爱老因很给名法"
    "间斯知世什两次使身者被高已亲其进此话常与"
    "活正感见明问力理尔点文几定本公特做外孩相"
    "西果走将月十实向声车全信重三机工物气每并"
    "别真打太新比才便夫再书部水像眼等体却加电"
    "主界门利海受听表德少克代员许稜先口由死安"
    "写性马光白或住难望教命花结乐色更拉东神记"
    "处让母父应直字场平报友关放至张认接告入笑"
    "内英军候民岁往何度山觉路带万男边风解叫任"
    "金快原吃妈变通师立象数四失满战远格士音轻"
    "目条呢"
)

class FanqieScraper:
    def __init__(self, cookie_str=None, user_agent=None):
        self.headers = get_headers(cookie_str, user_agent)
        self.base_url = "https://fanqienovel.com"
        # Cache for font maps: font_url -> map_dict
        self.font_maps = {}
        # Use a session for persistence
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_novel_metadata(self, url):
        """
        Fetches novel title, author, and cover image.
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Title"
            author = soup.find('span', class_='author-name-text').text.strip() if soup.find('span', class_='author-name-text') else "Unknown Author"
            
            # Try to find cover image
            cover_img = soup.find('img', class_='novel-cover-image')
            cover_url = cover_img['src'] if cover_img else None

            return {
                "title": title,
                "author": author,
                "cover_url": cover_url,
                "url": url
            }
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return None

    def get_chapter_list(self, url):
        """
        Fetches list of chapters (title and url).
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            # This selector might need adjustment based on actual page structure
            # Based on research: div.chapter-item a
            chapter_items = soup.select('.chapter-item a')
            
            for item in chapter_items:
                title = item.text.strip()
                link = item['href']
                if not link.startswith('http'):
                    link = self.base_url + link
                chapters.append({"title": title, "url": link})
                
            return chapters
        except Exception as e:
            print(f"Error fetching chapter list: {e}")
            return []

    def get_chapter_content(self, chapter_url):
        """
        Fetches chapter content and font URL.
        """
        log_debug(f"Fetching chapter: {chapter_url}")
        try:
            response = self.session.get(chapter_url)
            log_debug(f"Response Status: {response.status_code}")
            response.raise_for_status()
            html = response.text
            log_debug(f"Response Length: {len(html)}")
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract content div
            # Based on research: div.muye-reader-content
            content_div = soup.find('div', class_='muye-reader-content')
            if not content_div:
                log_debug("Content div not found")
                
                # Debug: Save error page
                try:
                    debug_dir = os.path.join(os.path.expanduser("~"), "Desktop", "fanqie_errors")
                    os.makedirs(debug_dir, exist_ok=True)
                    chapter_id = chapter_url.split('/')[-1]
                    with open(os.path.join(debug_dir, f"error_{chapter_id}.html"), 'w', encoding='utf-8') as f:
                        f.write(html)
                    log_debug(f"Saved error page to error_{chapter_id}.html")
                except:
                    pass
                
                # Fallback: check for 'no-content'
                if soup.find('div', class_='no-content'):
                    log_debug("Found 'no-content' div - VIP blocked?")
                    print(f"Content blocked for {chapter_url}. Cookie might be required.")
                return None

            log_debug("Content div found successfully")
            # Extract font URL
            font_url = None
            font_match = re.search(r"https://[^\"']+\.woff2", html)
            if font_match:
                font_url = font_match.group(0)
                log_debug(f"Font URL found: {font_url}")
            else:
                log_debug("Font URL NOT found")

            return {
                "content_html": str(content_div),
                "font_url": font_url
            }
        except Exception as e:
            log_debug(f"Error fetching chapter content: {e}")
            print(f"Error fetching chapter content: {e}")
            return None
    
    def _get_font_map(self, font_url):
        """
        Downloads and parses the woff2 font to create a mapping from obfuscated code to real char.
        """
        if not font_url:
            return {}
        
        if font_url in self.font_maps:
            return self.font_maps[font_url]

        try:
            print(f"Downloading font: {font_url}")
            resp = self.session.get(font_url, timeout=10)
            resp.raise_for_status()
            
            with tempfile.NamedTemporaryFile(suffix='.woff2', delete=False) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
            
            # Ensure brotli is importable before using fontTools with woff2
            try:
                import brotli
            except ImportError:
                print("Error: brotli module not found. WOFF2 decompression will fail.")
                # We can return a special dict to indicate error, but for now just log it.

            try:
                font = TTFont(tmp_path)
                
                # New Logic: Map based on Glyph Order and Static List
                glyph_order = font.getGlyphOrder()
                cmap = font.getBestCmap()
                mapping = {}
                
                # Map GlyphName -> RealChar using FANQIE_CHAR_MAP
                # Glyph 0 is .notdef, so Glyph 1 corresponds to index 0 in map string
                glyph_name_to_char = {}
                for i, name in enumerate(glyph_order):
                    if i == 0: continue # Skip .notdef
                    if i - 1 < len(FANQIE_CHAR_MAP):
                        glyph_name_to_char[name] = FANQIE_CHAR_MAP[i - 1]
                
                # Map Code -> GlyphName -> RealChar
                for code, name in cmap.items():
                    if name in glyph_name_to_char:
                        mapping[code] = glyph_name_to_char[name]
                    elif name.startswith('uni'):
                        # Fallback for standard names if mixed
                        try:
                            mapping[code] = chr(int(name[3:], 16))
                        except:
                            pass
                
                font.close()
                self.font_maps[font_url] = mapping
                return mapping
            except Exception as font_err:
                print(f"Error parsing font with TTFont: {font_err}")
                self.font_maps[font_url] = {} # Avoid retrying
                return {}
            finally:
                 if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            print(f"Error processing font {font_url}: {e}")
            return {}

    def generate_html(self, novel_data, chapters_content):
        """
        Generates a single HTML file with all chapters and embedded font.
        chapters_content: list of dicts {title, content_html, font_url}
        """
        # Use the font from the first chapter (assuming consistent font for the novel/session)
        font_base64 = None
        if chapters_content and chapters_content[0].get('font_url'):
            font_base64 = download_font_as_base64(chapters_content[0]['font_url'])

        font_face_css = ""
        if font_base64:
            font_face_css = f"""
            @font-face {{
                font-family: 'FanqieFont';
                src: url(data:font/woff2;charset=utf-8;base64,{font_base64}) format('woff2');
            }}
            .muye-reader-content {{
                font-family: 'FanqieFont', sans-serif;
            }}
            """

        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{novel_data['title']} - {novel_data['author']}</title>
            <style>
                body {{
                    font-family: sans-serif;
                    line-height: 1.6;
                    max_width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .chapter {{
                    background: #fff;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                h1 {{ text-align: center; color: #333; }}
                h2 {{ border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                p {{ margin-bottom: 1em; text-indent: 2em; }}
                {font_face_css}
            </style>
        </head>
        <body>
            <h1>{novel_data['title']}</h1>
            <p style="text-align: center;">作者：{novel_data['author']}</p>
            
            {{chapters_html}}
            
        </body>
        </html>
        """
        
        chapters_html = ""
        for chapter in chapters_content:
            chapters_html += f"""
            <div class="chapter">
                <h2>{chapter['title']}</h2>
                {chapter['content_html']}
            </div>
            """
            
        return html_template.format(chapters_html=chapters_html)

    def generate_txt(self, novel_data, chapters_content):
        """
        Generates a TXT file with de-obfuscated content.
        """
        txt_content = f"{novel_data['title']}\n作者：{novel_data['author']}\n\n"
        
        for chapter in chapters_content:
            txt_content += f"{chapter['title']}\n\n"
            
            raw_html = chapter.get('content_html')
            if not raw_html:
                 txt_content += "[章节内容获取失败，可能需要Cookie或为付费章节]\n\n" + "="*20 + "\n\n"
                 continue

            soup = BeautifulSoup(raw_html, 'html.parser')
            text = soup.get_text(separator='\n')
            
            # De-obfuscate if font_url is present
            font_url = chapter.get('font_url')
            if font_url:
                try:
                    mapping = self._get_font_map(font_url)
                    if mapping:
                        # Replace characters
                        new_text = ""
                        for char in text:
                            code = ord(char)
                            if code in mapping:
                                new_text += mapping[code]
                            else:
                                new_text += char
                        text = new_text
                    else:
                        # If mapping is empty but font_url exists, it likely failed.
                        text = f"[系统提示：字体解密失败 (Mapping Empty)]\n[Font URL: {font_url}]\n" + text
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    text = f"[系统提示：字体解密发生严重错误]\n[错误信息: {str(e)}]\n[Traceback: {tb}]\n" + text
            
            txt_content += text + "\n\n" + "="*20 + "\n\n"
            
        return txt_content

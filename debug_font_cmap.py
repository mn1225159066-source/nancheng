import requests
from fontTools.ttLib import TTFont
import tempfile
import os

url = "https://lf6-awef.bytetos.com/obj/awesome-font/c/dc027189e0ba4cd.woff2"
print(f"Downloading font: {url}")

try:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    
    with tempfile.NamedTemporaryFile(suffix='.woff2', delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = tmp.name

    font = TTFont(tmp_path)
    
    print(f"Font tables: {font.keys()}")
    
    print("\n--- Cmap Tables ---")
    for table in font['cmap'].tables:
        print(f"Platform: {table.platformID}, Encoding: {table.platEncID}, Format: {table.format}")
        # print(f"  Length: {len(table.cmap)}")
    
    print("\n--- Name Table ---")
    if 'name' in font:
        for record in font['name'].names:
            try:
                print(f"ID: {record.nameID}, String: {record.toUnicode()}")
            except:
                pass
    else:
        print("No name table found")

    print("\n--- Post Table ---")
    if 'post' in font:
        print(f"Format: {font['post'].formatType}")
        try:
             print(f"Extra names: {font['post'].extraNames[:10]}")
        except:
            print("No extra names")

    font.close()
    os.remove(tmp_path)

except Exception as e:
    print(f"Error: {e}")

import requests
from fontTools.ttLib import TTFont
import os

font_url = "https://lf6-awef.bytetos.com/obj/awesome-font/c/dc027189e0ba4cd.woff2"
font_path = "temp_font.woff2"
xml_path = "temp_font.ttx"

# Download font
try:
    response = requests.get(font_url)
    with open(font_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded font to {font_path}")
except Exception as e:
    print(f"Failed to download: {e}")
    exit(1)

# Analyze font
try:
    font = TTFont(font_path)
    
    # 1. Check ALL cmap tables
    print("\n--- Checking ALL Cmap Tables ---")
    for table in font['cmap'].tables:
        print(f"Platform: {table.platformID}, Encoding: {table.platEncID}, Format: {table.format}")
        # Reverse map this table
        rev_map = {}
        for code, name in table.cmap.items():
            if name not in rev_map:
                rev_map[name] = []
            rev_map[name].append(code)
        
        # Check a few glyphs
        print(f"  Sample reverse mappings:")
        sample_gids = ['gid58344', 'gid58345'] # Use ones we saw before
        for gid in sample_gids:
            if gid in rev_map:
                codes = [f"{c} (0x{c:x})" for c in rev_map[gid]]
                print(f"    {gid} <- {codes}")
            else:
                print(f"    {gid} not in this table")

    # 2. Check GlyphOrder again
    glyph_order = font.getGlyphOrder()
    
    # 3. Check GSUB (Ligatures can sometimes reveal mappings)
    if 'GSUB' in font:
        print("\nGSUB table found")
    else:
        print("\nNo GSUB table")

    # 4. Check CFF table
    print("\n--- Checking CFF Table ---")
    if 'CFF ' in font:
        print("CFF table found!")
        cff = font['CFF ']
        top_dict = cff.cff.topDictIndex[0]
        # print(f"CFF TopDict: {top_dict}")
        
        if hasattr(top_dict, 'CharStrings'):
            char_strings = top_dict.CharStrings
            print(f"CharStrings keys (first 10): {list(char_strings.keys())[:10]}")
            
            # Check if CharStrings use standard names
            sample_key = list(char_strings.keys())[1] # Skip .notdef
            print(f"Sample CharString key: {sample_key}")
    else:
        print("No CFF table found.")


except Exception as e:
    print(f"Error analyzing font: {e}")

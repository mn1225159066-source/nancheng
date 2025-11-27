from fontTools.ttLib import TTFont

font = TTFont('test.woff2')
cmap = font.getBestCmap()
for code, name in list(cmap.items())[:10]:
    print(f"Code: {hex(code)}, Name: {name}")

# Check if names are uniXXXX
is_uni = all(name.startswith('uni') for name in cmap.values())
print(f"All glyph names start with 'uni': {is_uni}")

if is_uni:
    print("Example mapping:")
    for code, name in list(cmap.items())[:5]:
        real_char = chr(int(name[3:], 16))
        print(f"{hex(code)} -> {name} -> {real_char}")

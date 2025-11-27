from fontTools.ttLib import TTFont

font = TTFont('test.woff2')
cmap = font.getBestCmap()

# Build reverse map: gid -> list of codes
gid_to_codes = {}
for code, name in cmap.items():
    if name not in gid_to_codes:
        gid_to_codes[name] = []
    gid_to_codes[name].append(code)

# Check if any PUA code (0xE000-0xF8FF) shares a gid with a standard code
found_mapping = False
for name, codes in gid_to_codes.items():
    pua_codes = [c for c in codes if 0xE000 <= c <= 0xF8FF]
    std_codes = [c for c in codes if not (0xE000 <= c <= 0xF8FF)]
    
    if pua_codes and std_codes:
        print(f"Match found! GID: {name}, PUA: {[hex(c) for c in pua_codes]}, STD: {[chr(c) for c in std_codes]}")
        found_mapping = True
        break

if not found_mapping:
    print("No direct mapping found via shared GIDs.")

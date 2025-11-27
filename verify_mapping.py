from fontTools.ttLib import TTFont

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

try:
    font = TTFont("temp_font.woff2")
    glyph_order = font.getGlyphOrder()
    
    print(f"Total glyphs: {len(glyph_order)}")
    print(f"First real glyph (index 1): {glyph_order[1]}")
    print(f"Maps to char: {FANQIE_CHAR_MAP[0]}")
    
    # Check '的'
    de_index = FANQIE_CHAR_MAP.find('的')
    print(f"'的' is at index {de_index} in map string.")
    
    if de_index != -1:
        target_glyph_index = de_index + 1
        if target_glyph_index < len(glyph_order):
            glyph_name = glyph_order[target_glyph_index]
            print(f"Glyph for '的' should be at index {target_glyph_index}: {glyph_name}")
            
            # Check cmap for this glyph
            cmap = font.getBestCmap()
            reverse_cmap = {v: k for k, v in cmap.items()}
            if glyph_name in reverse_cmap:
                print(f"Code for '的': {hex(reverse_cmap[glyph_name])}")
            else:
                print(f"Glyph {glyph_name} not in cmap?")
        else:
            print("Index out of bounds")

except Exception as e:
    print(f"Error: {e}")

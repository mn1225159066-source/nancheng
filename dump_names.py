from fontTools.ttLib import TTFont

font = TTFont('test.woff2')
if 'name' in font:
    for record in font['name'].names:
        try:
            print(f"{record.nameID}: {record.toUnicode()}")
        except:
            pass

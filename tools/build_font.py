"""Generate EFMSGFONT_KANJI24.BIN (SA2 PC, 24x24 RGBA glyphs) with Hangul in the kanji slots.

All glyphs are drawn from Noto Sans CJK (SIL OFL 1.1); no original game data is used.
usage: python build_font.py out.bin [font.ttc]
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import charmap

TOTAL_GLYPHS = 3528          # size of the original file (8,128,512 bytes)
DEFAULT_TTC = '/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc'


def render(ch, font, size=24, scale=4):
    S = size * scale
    img = Image.new('L', (S, S), 0)
    dr = ImageDraw.Draw(img)
    l, t, r, b = dr.textbbox((0, 0), ch, font=font)
    w, h = r - l, b - t
    # center horizontally, put em-box vertically centred
    asc, desc = font.getmetrics()
    x = (S - w) / 2 - l
    em_top = (S - (asc + desc)) / 2
    y = em_top
    dr.text((x, y), ch, font=font, fill=255)
    return np.asarray(img.resize((size, size), Image.LANCZOS))


def main(out, ttc=DEFAULT_TTC):
    fkr = ImageFont.truetype(ttc, 22 * 4, index=1)   # Noto Sans CJK KR
    fjp = ImageFont.truetype(ttc, 22 * 4, index=0)   # Noto Sans CJK JP
    table = charmap.build_table()
    by_index = {gi: ch for ch, (gi, _) in table.items()}
    glyphs = np.zeros((TOTAL_GLYPHS, 24, 24), np.uint8)
    for gi in range(len(charmap.ORDER)):
        if gi in by_index:
            glyphs[gi] = render(by_index[gi], fkr)
        else:
            ch = charmap.ORDER[gi]
            if ch not in ' 　〔':
                glyphs[gi] = render(ch, fjp)
    g = glyphs.astype(np.uint8)
    rgba = np.repeat(g[..., None], 4, axis=3)
    open(out, 'wb').write(rgba.tobytes())
    print('wrote', out, rgba.nbytes, 'bytes,', len(table), 'hangul')


if __name__ == '__main__':
    main(*sys.argv[1:])

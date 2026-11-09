"""Hangul <-> Shift-JIS slot mapping for the SA2 PC kanji font (EFMSGFONT_KANJI24.BIN).

The game's kanji font holds 3423 glyphs in JIS order (see kanji_order.txt).
Glyphs 458..3422 are JIS level-1 kanji (亜..腕).  We re-draw those slots with
Hangul syllables and encode Korean text using the matching Shift-JIS codes.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = open(os.path.join(HERE, 'kanji_order.txt'), encoding='utf-8').read()
assert len(ORDER) == 3423
KANJI_START = ORDER.index('亜')  # 458


def ksx1001_hangul():
    out = []
    for cp in range(0xAC00, 0xD7A4):
        ch = chr(cp)
        try:
            if len(ch.encode('euc_kr')) == 2:
                out.append(ch)
        except UnicodeEncodeError:
            pass
    return out


BASE_HANGUL = ksx1001_hangul()          # 2350 syllables, fixed order
assert len(BASE_HANGUL) == 2350
EXTRA_FILE = os.path.join(HERE, 'extra_hangul.txt')


def extra_hangul():
    if os.path.exists(EXTRA_FILE):
        return [c for c in open(EXTRA_FILE, encoding='utf-8').read() if '가' <= c <= '힣']
    return []


def build_table():
    """returns dict hangul -> (glyph_index, sjis_bytes)"""
    syl = BASE_HANGUL + [c for c in extra_hangul() if c not in BASE_HANGUL]
    slots = len(ORDER) - KANJI_START
    if len(syl) > slots:
        raise ValueError('too many hangul syllables: %d > %d' % (len(syl), slots))
    table = {}
    for k, ch in enumerate(syl):
        gi = KANJI_START + k
        kanji = ORDER[gi]
        table[ch] = (gi, kanji.encode('cp932'))
    return table


# characters that may stay as-is (single byte, drawn with the ASCII font)
ASCII_OK = set(' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~\n')
# full-width punctuation that exist in kanji font rows 1-3 (encoded via cp932)
FULLWIDTH_OK = set(ORDER[:KANJI_START]) - {'〔'}


def encode(text, table=None):
    table = table or build_table()
    out = bytearray()
    text = text.replace('\u00b7', '\u30fb')  # middle dot -> katakana middle dot (in font)
    for ch in text:
        if ch in table:
            out += table[ch][1]
        elif ch in ASCII_OK or ord(ch) < 0x20:
            out += ch.encode('latin-1')
        elif ch in FULLWIDTH_OK or ch == '〔':
            out += ch.encode('cp932')
        else:
            raise ValueError('cannot encode %r in %r' % (ch, text))
    return bytes(out)


def decode(data, table=None):
    table = table or build_table()
    rev = {v[1]: k for k, v in table.items()}
    out = []
    i = 0
    while i < len(data):
        b = data[i]
        if (0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef) and i + 1 < len(data):
            pair = bytes(data[i:i + 2])
            out.append(rev.get(pair) or pair.decode('cp932', 'replace'))
            i += 2
        else:
            out.append(chr(b))
            i += 1
    return ''.join(out)

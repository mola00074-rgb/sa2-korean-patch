"""Split message strings into control codes and translatable text units."""
import re, hashlib

CTRL = re.compile(rb'(\x0c[^\x07]*\x07|\x07)')

SKIP_FILES = ('MsgAlKinderFoName_j', 'MsgChaoKarateName_j')   # binary chao-name tables, left untouched


def split(s):
    """bytes -> list of (is_text, bytes)"""
    out = []
    for part in CTRL.split(s):
        if not part:
            continue
        out.append((not CTRL.fullmatch(part), part))
    return out


def unit_id(b):
    return hashlib.sha1(b).hexdigest()[:12]


def is_translatable(b):
    t = b.decode('cp932', 'replace')
    return any(ord(c) > 0x7f for c in t)

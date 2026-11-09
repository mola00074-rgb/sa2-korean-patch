"""Generic SA2 message container: header with u32 pointers to NUL-terminated strings."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import prs

EVMES_BASE = 0x817B0000 - 0x1A0

def fmt_for(name):
    n = os.path.basename(name)
    if n.startswith('evmes'):
        return ('>', EVMES_BASE)
    if n.startswith('msgChaoKin'):
        return ('<', 0)
    return ('>', 0)

def load(path):
    raw = open(path, 'rb').read()
    return prs.decompress(raw) if path.lower().endswith('.prs') else raw

def parse(d, endian, base):
    n = len(d)
    u = lambda i: struct.unpack_from(endian + 'I', d, i)[0]
    # all aligned candidates
    cands = []
    for i in range(0, n - 3, 4):
        o = u(i) - base
        if 0 < o < n:
            cands.append((i, o))
    # string start S: smallest target such that every byte from S on is "texty" region
    # heuristic: S = min target among candidates located before that target
    # iterate: choose S = min o where o > i (pointer lies before target) and d[o-1]==0
    def starts(o):
        return d[o - 1] == 0 or (o >= 4 and d[o - 4:o] == b'\xff\xff\xff\xff')
    targets = sorted(set(o for i, o in cands if o > i and starts(o)))
    # header end must be <= S; take S as smallest target where all candidate pointers to >=S lie < S
    S = None
    for t in targets:
        ptrs = [(i, o) for i, o in cands if i < t and o >= t]
        if ptrs and all(starts(o) for _, o in ptrs):
            S = t
            break
    ptrs = [(i, o) for i, o in cands if i < S and o >= S and starts(o)]
    strings = {}
    for _, o in ptrs:
        if o not in strings:
            e = d.index(b'\0', o)
            strings[o] = d[o:e]
    return S, ptrs, strings

def rebuild(d, endian, base, S, ptrs, newstrings, minsize=0):
    """newstrings: dict old_offset -> bytes"""
    head = bytearray(d[:S])
    body = bytearray()
    newoff = {}
    aligned = all(o % 4 == 0 for o in newstrings) and len(newstrings) > 1
    for o in sorted(newstrings):
        if aligned:
            while (S + len(body)) % 4:
                body += b'\0'
        newoff[o] = S + len(body)
        body += newstrings[o] + b'\0'
    for i, o in ptrs:
        struct.pack_into(endian + 'I', head, i, newoff[o] + base)
    out = bytes(head + body)
    while len(out) % 4:
        out += b'\0'
    if len(out) < minsize:
        out += b'\0' * (minsize - len(out))
    return out


def targets(root):
    import glob
    out = []
    for p in sorted(glob.glob(os.path.join(root, '**', '*'), recursive=True)):
        if os.path.isdir(p):
            continue
        n = os.path.basename(p)
        rel = os.path.relpath(p, root).replace(os.sep, '/')
        if rel.startswith('event/'):
            if n.startswith('evmes') and n[6] == '0':
                out.append(rel)
            continue
        if not (n.endswith('j.prs') or n.endswith('_j.bin')):
            continue
        if rel.startswith(('Message/', 'MessageK/')) or n.lower().startswith('msg'):
            out.append(rel)
    return out

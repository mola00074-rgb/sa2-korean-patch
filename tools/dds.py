"""Minimal DXT5 DDS writer (with mipmaps) for small UI icons."""
import struct
import numpy as np
from PIL import Image


def _565(c):
    r, g, b = (int(x) for x in c[:3])
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def _unpack565(v):
    r = (v >> 11) & 31; g = (v >> 5) & 63; b = v & 31
    return np.array([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], float)


def _block(px):
    """px: (16,4) uint8 -> 16 bytes DXT5"""
    px = px.astype(float)
    a = px[:, 3]
    a0, a1 = int(a.max()), int(a.min())
    if a0 == a1:
        aidx = np.zeros(16, int)
    else:
        pal = [a0, a1] + [((7 - i) * a0 + i * a1) / 7 for i in range(1, 7)]
        aidx = np.argmin(np.abs(a[:, None] - np.array(pal)[None, :]), axis=1)
    abits = 0
    for i, v in enumerate(aidx):
        abits |= int(v) << (3 * i)
    alpha = struct.pack('<BB', a0, a1) + abits.to_bytes(6, 'little')

    rgb = px[:, :3]
    w = a > 0
    src = rgb[w] if w.any() else rgb
    lum = src @ np.array([0.299, 0.587, 0.114])
    hi = src[lum.argmax()]; lo = src[lum.argmin()]
    c0, c1 = _565(hi), _565(lo)
    if c0 < c1:
        c0, c1 = c1, c0
    if c0 == c1:
        cidx = np.zeros(16, int)
    else:
        p0, p1 = _unpack565(c0), _unpack565(c1)
        pal = np.array([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3])
        cidx = np.argmin(((rgb[:, None, :] - pal[None]) ** 2).sum(2), axis=1)
    cbits = 0
    for i, v in enumerate(cidx):
        cbits |= int(v) << (2 * i)
    return alpha + struct.pack('<HHI', c0, c1, cbits)


def _compress(img):
    arr = np.asarray(img.convert('RGBA'))
    h, w = arr.shape[:2]
    pw, ph = max(4, w), max(4, h)
    if (pw, ph) != (w, h):
        pad = np.zeros((ph, pw, 4), np.uint8); pad[:h, :w] = arr; arr = pad
    out = bytearray()
    for by in range(0, ph, 4):
        for bx in range(0, pw, 4):
            out += _block(arr[by:by + 4, bx:bx + 4].reshape(16, 4))
    return bytes(out)


def write_dxt5(img, mips=True):
    img = img.convert('RGBA')
    w, h = img.size
    levels = [img]
    if mips:
        while levels[-1].size != (1, 1):
            nw, nh = max(1, levels[-1].width // 2), max(1, levels[-1].height // 2)
            levels.append(img.resize((nw, nh), Image.LANCZOS))
    data = b''.join(_compress(l) for l in levels)
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000 | (0x20000 if mips else 0)
    hdr = struct.pack('<4sIIIIIII', b'DDS ', 124, flags, h, w, max(1, w // 4) * max(1, h // 4) * 16, 0, len(levels))
    hdr += b'\0' * 44
    hdr += struct.pack('<II4sIIIII', 32, 0x4, b'DXT5', 0, 0, 0, 0, 0)
    caps = 0x1000 | ((0x8 | 0x400000) if mips else 0)
    hdr += struct.pack('<IIIII', caps, 0, 0, 0, 0)
    assert len(hdr) == 128
    return hdr + data

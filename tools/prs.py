"""SEGA PRS compression (decompress + compress)."""

def decompress(data: bytes) -> bytes:
    out = bytearray()
    pos = 0
    bitpos = 8
    cmd = 0

    def bit():
        nonlocal pos, bitpos, cmd
        if bitpos == 8:
            cmd = data[pos]; pos += 1; bitpos = 0
        b = (cmd >> bitpos) & 1
        bitpos += 1
        return b

    while True:
        if bit():
            out.append(data[pos]); pos += 1
            continue
        if bit():
            v = data[pos] | (data[pos + 1] << 8); pos += 2
            if v == 0:
                break
            off = (v >> 3) - 0x2000
            size = v & 7
            if size == 0:
                size = data[pos] + 1; pos += 1
            else:
                size += 2
        else:
            size = ((bit() << 1) | bit()) + 2
            off = data[pos] - 256; pos += 1
        start = len(out) + off
        for i in range(size):
            out.append(out[start + i])
    return bytes(out)


class _BitWriter:
    def __init__(self):
        self.out = bytearray([0])
        self.cmdpos = 0
        self.nbits = 0

    def bit(self, b):
        if self.nbits == 8:
            self.cmdpos = len(self.out)
            self.out.append(0)
            self.nbits = 0
        if b:
            self.out[self.cmdpos] |= 1 << self.nbits
        self.nbits += 1

    def byte(self, b):
        self.out.append(b & 0xFF)


def compress(data: bytes) -> bytes:
    w = _BitWriter()
    n = len(data)
    i = 0
    # hash chains of 3-byte sequences
    head = {}
    prev = [-1] * n
    def insert(p):
        if p + 2 < n:
            k = data[p:p + 3]
            prev[p] = head.get(k, -1)
            head[k] = p

    while i < n:
        best_len, best_off = 0, 0
        if i + 2 < n:
            k = data[i:i + 3]
            p = head.get(k, -1)
            limit = min(256, n - i)
            tries = 0
            while p >= 0 and i - p <= 0x1FFF and tries < 256:
                l = 3
                while l < limit and data[p + l] == data[i + l]:
                    l += 1
                if l > best_len:
                    best_len, best_off = l, p - i
                    if l == limit:
                        break
                p = prev[p]; tries += 1
        # short 2-byte match within 255
        if best_len < 3 and i + 1 < n:
            for p in range(i - 1, max(-1, i - 256), -1):
                if data[p] == data[i] and data[p + 1] == data[i + 1]:
                    best_len, best_off = 2, p - i
                    break
        if best_len >= 2 and (best_len <= 5 and best_off >= -256):
            w.bit(0); w.bit(0)
            s = best_len - 2
            w.bit((s >> 1) & 1); w.bit(s & 1)
            w.byte(best_off & 0xFF)
        elif best_len >= 3:
            w.bit(0); w.bit(1)
            off = best_off & 0x1FFF
            if best_len <= 9:
                v = (off << 3) | (best_len - 2)
                w.byte(v & 0xFF); w.byte(v >> 8)
            else:
                v = off << 3
                w.byte(v & 0xFF); w.byte(v >> 8)
                w.byte(best_len - 1)
        else:
            w.bit(1); w.byte(data[i])
            best_len = 1
        for p in range(i, i + best_len):
            insert(p)
        i += best_len
    w.bit(0); w.bit(1); w.byte(0); w.byte(0)
    return bytes(w.out)

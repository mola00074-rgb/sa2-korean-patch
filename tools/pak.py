"""SA2 PC .pak texture archive (read / write)."""
import struct


def read(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'\x01pak', 'not a pak'
    p = 0x39
    count = struct.unpack_from('<I', d, p)[0]; p += 4
    entries = []
    for _ in range(count):
        n = struct.unpack_from('<I', d, p)[0]; p += 4
        longname = d[p:p + n]; p += n
        n = struct.unpack_from('<I', d, p)[0]; p += 4
        name = d[p:p + n]; p += n
        ln, ln2 = struct.unpack_from('<II', d, p); p += 8
        entries.append([longname, name, ln])
    out = []
    for longname, name, ln in entries:
        out.append((longname.decode('latin-1'), name.decode('latin-1'), d[p:p + ln]))
        p += ln
    assert p == len(d), (p, len(d))
    return d[:0x39], out


def write(path, header, files):
    body = bytearray()
    body += struct.pack('<I', len(files))
    for longname, name, data in files:
        ln, nm = longname.encode('latin-1'), name.encode('latin-1')
        body += struct.pack('<I', len(ln)) + ln + struct.pack('<I', len(nm)) + nm
        body += struct.pack('<II', len(data), len(data))
    for _, _, data in files:
        body += data
    h = bytearray(header)
    total = sum(len(d) for _, _, d in files)
    struct.pack_into('<III', h, 0x25, len(files), total, total)
    open(path, 'wb').write(bytes(h) + bytes(body))

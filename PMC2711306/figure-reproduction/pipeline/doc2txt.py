"""Plain text of a Word 97-2003 (.doc) file, read through its piece table (no Word needed)."""
import olefile, struct, sys
def doc_text(path):
    ole = olefile.OleFileIO(path)
    wd = ole.openstream('WordDocument').read()
    flags = struct.unpack_from('<H', wd, 0x0A)[0]
    table = '1Table' if flags & 0x0200 else '0Table'
    tbl = ole.openstream(table).read()
    # FibRgFcLcb97: fcClx at offset 0x01A2, lcbClx at 0x01A6
    fcClx, lcbClx = struct.unpack_from('<II', wd, 0x01A2)
    clx = tbl[fcClx:fcClx+lcbClx]
    i = 0
    while clx[i] == 0x01:  # Prc
        cb = struct.unpack_from('<H', clx, i+1)[0]; i += 3 + cb
    assert clx[i] == 0x02
    lcb = struct.unpack_from('<I', clx, i+1)[0]; plc = clx[i+5:i+5+lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack_from('<%dI' % (n+1), plc, 0)
    out = []
    for k in range(n):
        pcd = plc[4*(n+1)+8*k: 4*(n+1)+8*(k+1)]
        fc = struct.unpack_from('<I', pcd, 2)[0]
        nch = cps[k+1]-cps[k]
        if fc & 0x40000000:
            off = (fc & ~0x40000000) // 2
            out.append(wd[off:off+nch].decode('cp1252', 'replace'))
        else:
            out.append(wd[fc:fc+2*nch].decode('utf-16-le', 'replace'))
    t = ''.join(out)
    return t.replace('\r', '\n').replace('\x07', '\t').replace('\x0b', '\n')
if __name__ == '__main__':
    sys.stdout.write(doc_text(sys.argv[1]))

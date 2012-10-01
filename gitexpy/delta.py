"""
Testing Git's delta coding.

>>> for (p, l) in [(1,1), (2**32-1, 2**16-1), (0,1), (0,65536), (256,256)]:
...     assert decode_copycommand(encode_copycommand(p, l)) == (p, l)
"""

from .sixx import byte2int, int2byte

def decode_delta(delta, src):
    pos = 0
    (srcsize, pos) = __decode_delta_header_size(delta, pos)
    (dstsize, pos) = __decode_delta_header_size(delta, pos)
    try:
        srclen = len(src)
    except:
        srclen = None
    assert srclen is None or srclen == srcsize
    data = b''
    while pos < len(delta):
        (d, pos) = __decode_deltacommand(src, srcsize, delta, pos)
        data += d
        assert len(d) >= 1
        assert len(data) <= dstsize
    assert len(data) == dstsize
    return data

def __decode_delta_header_size(buf, pos):
    i = 0
    sz = byte2int(buf[pos + i]) & 0b01111111
    while byte2int(buf[pos + i]) & 0b10000000:
        i += 1
        sz += (128**i)*(byte2int(buf[pos + i]) & 0b01111111)
    return (sz, pos + i + 1)

def __decode_deltacommand(src, srcsize, buf, pos):
    if byte2int(buf[pos]) & 0b10000000:
        # copy
        ((p,l), pos2) = __decode_copycommand(buf, pos)
        assert p < srcsize
        assert p + l <= srcsize
        return (src[p:p+l], pos2)
    else:
        # insert
        length = byte2int(buf[pos])
        return (buf[pos+1:pos+1+length], pos+length+1)

def encode_copycommand(p, l):
    """
    Encode delta copy command.

    >>> def format_bytes(x):
    ...     return '.'.join('%02x' % byte2int(b) for b in x)
    >>> format_bytes(encode_copycommand(1445429087, 2344))
    'bf.5f.7f.27.56.28.09'
    >>> format_bytes(encode_copycommand(0, 65536))
    '80'
    >>> format_bytes(encode_copycommand(1, 65536))
    '81.01'
    >>> format_bytes(encode_copycommand(0, 1))
    '90.01'
    >>> format_bytes(encode_copycommand(1, 1))
    '91.01.01'
    >>> format_bytes(encode_copycommand(256, 256))
    'a2.01.01'
    >>> format_bytes(encode_copycommand(2**32-1, 2**16-1))
    'bf.ff.ff.ff.ff.ff.ff'
    """
    assert 0 <= p < 2**32
    assert 0 < l <= 2**16
    Q = {}
    Q[6] = l // (2**16)
    Q[5] =(l  - (2**16)*Q[6]) // (2**8)
    Q[4] = l  - (2**16)*Q[6]   - (2**8)*Q[5]
    assert l == (2**16)*Q[6]   + (2**8)*Q[5] + Q[4]
    Q[3] = p // (2**24)
    Q[2] =(p  - (2**24)*Q[3]) // (2**16)
    Q[1] =(p  - (2**24)*Q[3]   - (2**16)*Q[2]) // (2**8)
    Q[0] = p  - (2**24)*Q[3]   - (2**16)*Q[2]   - (2**8)*Q[1]
    assert p == (2**24)*Q[3]   + (2**16)*Q[2]   + (2**8)*Q[1] + Q[0]
    assert all(0 <= Q[i] < 256 for i in Q)
    (k, q) = (128, b'')
    for i in range(6):
        if Q[i] != 0:
            q = q + int2byte(Q[i])
            k = k + 2**i
    return int2byte(k) + q

def decode_copycommand(c):
    """
    Decode delta copy command.

    >>> decode_copycommand(int2byte(0x80))
    (0, 65536)
    >>> decode_copycommand(b''.join(int2byte(x) for x in [0xbf, 0x5f, 0x7f, 0x27, 0x56, 0x28, 0x09]))
    (1445429087, 2344)
    """
    return __decode_copycommand(c, 0)[0]

def __decode_copycommand(buf, pos):
    Q = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    j = 0
    for i in range(6):
        if ((byte2int(buf[pos+0]) & 2**i) != 0):
            j += 1
            Q[i] = byte2int(buf[pos+j])
    p = (2**24)*Q[3]   + (2**16)*Q[2]   + (2**8)*Q[1] + Q[0]
    l = (2**16)*Q[6]   + (2**8)*Q[5] + Q[4]
    if l == 0:
        l = 65536
    return ((p, l), pos + j + 1)

def debug_delta(delta):
    pos = 0
    (srcsize, pos) = __decode_delta_header_size(delta, pos)
    (dstsize, pos) = __decode_delta_header_size(delta, pos)
    yield '(srcsize=%d,dstsize=%d)' % (srcsize,dstsize)
    while pos < len(delta):
        (cmdtxt, pos) = __debug_deltacommand(srcsize, delta, pos)
        yield cmdtxt

def __debug_deltacommand(srcsize, buf, pos):
    if byte2int(buf[pos]) & 0b10000000:
        # copy
        ((p,l), pos2) = __decode_copycommand(buf, pos)
        if p < srcsize and p + l <= srcsize:
            mark = ''
        else:
            mark = '*'
        return ('<C:%d,%d%s>' % (p,l,mark), pos2)
    else:
        # insert
        length = byte2int(buf[pos])
        return ('<I:%d:%r>' % (length, buf[pos+1:pos+1+length]), pos+length+1)

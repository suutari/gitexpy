from nose.tools import *

from .outputwindow import *

def test():
    ow = OutputWindow(max_size=5)
    s = b''

    eq_(len(ow), len(s))
    eq_(ow.last_n(0), b'')
    eq_(ow[0:0], s[0:0])

    ow.append_bytes(b'abc')
    s += b'abc'

    eq_(len(ow), len(s))
    eq_(ow[0], s[0])
    eq_(ow[1], s[1])
    eq_(ow[2], s[2])
    eq_(ow.last_n(0), b'')
    eq_(ow.last_n(1), s[-1:])
    eq_(ow.last_n(2), s[-2:])
    eq_(ow.last_n(3), s[-3:])
    eq_(ow[0:0], s[0:0])
    eq_(ow[0:1], s[0:1])
    eq_(ow[0:2], s[0:2])
    eq_(ow[0:3], s[0:3])
    eq_(ow[1:2], s[1:2])
    eq_(ow[1:3], s[1:3])
    eq_(ow[2:3], s[2:3])
    eq_(ow[2:], s[2:])
    eq_(ow[:], s[:])
    with assert_raises_regexp(Error, 'n too large \(n=4, max=3\)'):
        ow.last_n(4)

    ow.append_bytes(b'de')
    s += b'de'

    eq_(len(ow), len(s))
    eq_(ow[0], s[0])
    eq_(ow[1], s[1])
    eq_(ow[2], s[2])
    eq_(ow[3], s[3])
    eq_(ow[4], s[4])
    eq_(ow.last_n(3), s[-3:])
    eq_(ow[1:3], s[1:3])
    eq_(ow[2:5], s[2:5])
    eq_(ow[0:4], s[0:4])
    eq_(ow[0:4:2], s[0:4:2])
    eq_(ow[0:4:3], s[0:4:3])
    eq_(ow[2:], s[2:])
    eq_(ow[:], s[:])

    ow.append_bytes(b'f')
    s += b'f'

    eq_(len(ow), len(s))
    eq_(ow[1], s[1])
    eq_(ow[2], s[2])
    eq_(ow[3], s[3])
    eq_(ow[4], s[4])
    eq_(ow[5], s[5])
    eq_(ow.last_n(3), s[-3:])

    ow.append_bytes(b'gh')
    s += b'gh'

    eq_(len(ow), len(s))
    eq_(ow[3], s[3])
    eq_(ow[4], s[4])
    eq_(ow[5], s[5])
    eq_(ow[6], s[6])
    eq_(ow[7], s[7])
    eq_(ow.last_n(3), s[-3:])
    eq_(ow.last_n(5), s[-5:])
    eq_(ow[3:6], s[3:6])
    eq_(ow[4:7], s[4:7])
    eq_(ow[5:7], s[5:7])
    eq_(ow[6:8], s[6:8])
    eq_(ow[3:8], s[3:8])
    eq_(ow[3:8:2], s[3:8:2])
    eq_(ow[3:8:3], s[3:8:3])
    eq_(ow[3:], s[3:])
    eq_(ow[5:], s[5:])

    with assert_raises_regexp(
        Error, 'Key out of range \(key=42, valid range=\[3,7\]\)'):
        ow[42]
    with assert_raises_regexp(Error, 'Length too large \(length=42, max=5\)'):
        ow[3:45]
    with assert_raises_regexp(Error, 'n too large \(n=6, max=5\)'):
        ow.last_n(6)

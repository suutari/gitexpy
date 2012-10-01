"""
Extra stuff for Python 2/3 compatibility.
"""

from six import *

if PY3:
    def byte2int(b):
        try:
            return b[0]
        except:
            return b

    def ints2bytes(seq):
        return bytes(seq)

    def bytes2ints(seq):
        return list(seq)

else:
    def byte2int(b):
        return ord(b)

    def ints2bytes(seq):
        return ''.join(chr(x) for x in seq)

    def bytes2ints(seq):
        return [ord(x) for x in seq]

if PY3:
    def astr(x):
        try:
            return x.decode('ascii')
        except AttributeError:
            return x
else:
    def astr(x):
        return x.encode('ascii')

if PY3:
    import builtins
    input = builtins.input
else:
    input = raw_input

if PY3:
    def make_streams_binary(sys):
        sys.stdin = sys.stdin.detach()
        sys.stdout = sys.stdout.detach()
else:
    def make_streams_binary(sys):
        pass

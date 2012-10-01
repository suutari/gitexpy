from .sixx import int2byte

def to_bin(x):
    assert isinstance(x, int)
    return '{:08b}'.format(x)

def to_bin_inverted(x):
    assert isinstance(x, int)
    return ''.join(reversed(to_bin(x)))

def is_printable(x):
    assert isinstance(x, int)
    return int2byte(x).isalnum() or x in range(32, 127)

def to_printable(x):
    assert isinstance(x, int)
    return int2byte(x).decode('ascii') if is_printable(x) else '.'

def to_printable2(x):
    assert isinstance(x, int)
    return int2byte(x).decode('ascii') + ' ' if is_printable(x) else '__'

def to_printable8(x):
    assert isinstance(x, int)
    return '\\ %02x %s/' % (x, to_printable2(x))

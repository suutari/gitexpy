from . import rabin
from .memoize import memoized
from .sixx import byte2int, int2byte

crc32poly_mirrored = 0xedb88320

def crc32(x):
    """
    Calculate CRC32 of x.

    >>> '%x' % crc32(b'123456789')
    'cbf43926'
    """
    T = get_crc32_table()
    crc = 0xffffffff
    for c in x:
        crc = (crc >> 8) ^ T[(crc ^ byte2int(c)) & 0xff]
    return crc ^ 0xffffffff

@memoized
def get_crc32_table():
    table = {}
    for i in range(256):
        crc = i
        for j in range(8):
            outbit = crc & 0x00000001
            crc >>= 1
            if outbit:
                crc ^= crc32poly_mirrored
        table[i] = crc
    return table

def r_crc32(x):
    """
    Calculate CRC32 of x using Rabin.

    >>> '{c:08x} {c:032b}'.format(c=r_crc32(b'123456789'))
    'cbf43926 11001011111101000011100100100110'
    >>> '{c:08x} {c:032b}'.format(c=r_crc32(b'a'))
    'e8b7be43 11101000101101111011111001000011'
    >>> '{c:08x} {c:032b}'.format(c=r_crc32(b''))
    '00000000 00000000000000000000000000000000'
    >>> '{c:08x} {c:032b}'.format(c=r_crc32(b'abc'))
    '352441c2 00110101001001000100000111000010'
    """
    x_processed = complement_firstbytes(4, mirror_bytes(x) + b'\0\0\0\0')
    fp = get_rabin_crc32().fingerprint(x_processed)
    return mirror_int32_bits(fp ^ 0xffffffff)

def mirror_bytes(x):
    return b''.join(mirror_byte(c) for c in x)

@memoized
def mirror_byte(c):
    return int2byte(int(''.join(reversed('{:08b}'.format(byte2int(c)))), 2))

def complement_firstbytes(n, x):
    r = bytearray(x)
    for i in range(n):
        r[i] ^= 0xff
    return bytes(r)

def mirror_int32_bits(x):
    return int(''.join(reversed('{:032b}'.format(x))), 2)

@memoized
def get_rabin_crc32():
    crc32poly = 2**32 + mirror_int32_bits(crc32poly_mirrored)
    return rabin.Rabin(polynomial=crc32poly)

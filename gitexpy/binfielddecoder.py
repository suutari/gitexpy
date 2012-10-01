from six.moves import xrange

LSB_FIRST='LSB_FIRST'
MSB_FIRST='MSB_FIRST'
BIG_ENDIAN='BIG_ENDIAN'
LITTLE_ENDIAN='LITTLE_ENDIAN'

class BinFieldDecoder(object):
    def __init__(self, add, bitorder, byteorder):
        self.add = add
        self.bitorder = bitorder
        self.byteorder = byteorder
        assert self.bitorder in (LSB_FIRST, MSB_FIRST)
        assert self.byteorder in (BIG_ENDIAN, LITTLE_ENDIAN)
    def __call__(self, x):
        if x == '':
            x = '0'
        if self.bitorder == LSB_FIRST:
            y = ''.join(reversed(x))
        else:
            y = x
        if (self.bitorder == LSB_FIRST) == (self.byteorder == BIG_ENDIAN):
            z = ''
            for i in xrange(0, len(y), 8):
                z = y[i:i+8] + z
        else:
            z = y
        return int(z, 2) + self.add

BfdLsbB = lambda x: BinFieldDecoder(x, LSB_FIRST, BIG_ENDIAN)
BfdLsbL = lambda x: BinFieldDecoder(x, LSB_FIRST, LITTLE_ENDIAN)
BfdLsb = BfdLsbB
BfdMsbB = lambda x: BinFieldDecoder(x, MSB_FIRST, BIG_ENDIAN)
BfdMsbL = lambda x: BinFieldDecoder(x, MSB_FIRST, LITTLE_ENDIAN)
BfdMsb = BfdMsbB

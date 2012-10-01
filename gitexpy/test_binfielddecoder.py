from nose.tools import *

from .binfielddecoder import *

def test():
    testdata = [
        # orig                   lb      ll      mb      ml
        ('',                      0,      0,      0,      0),
        ('0',                     0,      0,      0,      0),
        ('00',                    0,      0,      0,      0),
        ('11',                    3,      3,      3,      3),
        ('0000',                  0,      0,      0,      0),
        ('0001',                  8,      8,      1,      1),
        ('1000',                  1,      1,      8,      8),
        ('00000000',              0,      0,      0,      0),
        ('00000001',            128,    128,      1,      1),
        ('10000000',              1,      1,    128,    128),
        ('11111111',            255,    255,    255,    255),
        ('0000000100000010',  32832,  16512,    258,    513),
        ('1000000000000010',    320,  16385,  32770,    640),
        ]
    def check_decoder(bitorder, byteorder, bitstr, expected_result):
        eq_(BinFieldDecoder(0, bitorder, byteorder)(bitstr), expected_result)
    for (bitstr, lb, ll, mb, ml) in testdata:
        for (bitorder, byteorder, expected) in (
            (LSB_FIRST, BIG_ENDIAN, lb),
            (LSB_FIRST, LITTLE_ENDIAN, ll),
            (MSB_FIRST, BIG_ENDIAN, mb),
            (MSB_FIRST, LITTLE_ENDIAN, ml)):
            yield (check_decoder, bitorder, byteorder, bitstr, expected)

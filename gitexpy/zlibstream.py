import sys
from .binfielddecoder import BfdMsbL
from .errors import *
from .deflate import DeflateBitString
from .fieldlist import FieldList
from .infoprint import iprint

def parse(in_stream=sys.stdin, out_stream=sys.stdout, info_stream=sys.stderr):
    binstr = DeflateBitString(in_stream, info_stream)
    f = FieldList()
    f.add_field('zlib_header', binstr.take(16), BfdMsbL(0))
    if f.get_decoded('zlib_header') % 31 != 0:
        raise Error('Invalid checksum in ZLIB header')
    for line in str(f).split('\n'):
        iprint(info_stream, 'HEADER: %s' % line)
    for data in binstr.decode_blocks():
        out_stream.write(data)

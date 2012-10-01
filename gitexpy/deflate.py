from collections import defaultdict
from six.moves import xrange
from .binfielddecoder import BfdMsb, BfdMsbB
from .bitstring import BitString
from .errors import *
from .fieldlist import FieldList
from .outputwindow import OutputWindow
from .chrconvert import to_bin, to_printable
from .infoprint import iprint
from .sixx import int2byte

cclorder = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]

class DeflateError(Error):
    """Deflate Error"""

class DeflateBitString(BitString):
    def __init__(self, in_stream, info_stream=None):
        BitString.__init__(self, in_stream)
        self.info_stream = info_stream
        self.stats = None
    def iprint(self, text):
        if self.info_stream:
            iprint(self.info_stream, text)
    def decode_blocks(self):
        final = False
        window = OutputWindow(max_size=32768)
        self.stats = DeflateStats(self.info_stream)
        self.stats.start_offset = self.offset
        assert window.sz == 0
        while not final:
            for (data, fin) in self.decode_block(window):
                yield data
                final = fin
        self.iprint(str(self.stats))
    def decode_block(self, window):
        blockstats = self.stats.add_blockstats()
        blockstats['start_offset'] = self.offset
        f = FieldList()
        f.add_field('BFINAL', self.take(1), BfdMsb(0))
        assert f['BFINAL'] in ('0', '1')
        final = bool(f.get_decoded('BFINAL'))
        f.add_field('BTYPE', self.take(2), BfdMsb(1))
        btype = f.get_decoded('BTYPE')
        if btype not in (1, 2, 3):
            raise DeflateError(
                'Invalid block type %s at offset %d' % (btype, self.offset))
        blockstats['type'] = btype
        if btype == 1:
            decoder = self.decode_uncompressed_block
        elif btype == 2:
            decoder = self.decode_type2_block
        elif btype == 3:
            decoder = self.decode_type3_block
        for data in decoder(f, window):
            yield (data, final)
    def decode_uncompressed_block(self, f, window):
        # uncompressed
        blockstats = self.stats.blockstats[-1]
        self.discard((8 - self.offset) % 8)
        block_len = BfdMsbB(0)(self.take(16))
        block_len_check = BfdMsbB(0)(self.take(16))
        self.iprint('BLOCK HEADER: LEN=%s' % (block_len,))
        if block_len + block_len_check != 2**16 - 1:
            raise DeflateError(
                'Uncompressed block length decode error at offset %d' %
                self.offset)
        blockstats['codes_start_offset'] = self.offset
        blockstats['data_start_offset'] = self.offset
        blockstats['output_start_offset'] = len(window) * 8
        data = b''
        for dummy in xrange(block_len):
            data += int2byte(BfdMsb(0)(self.take(8)))
        blockstats['data_stop_offset'] = self.offset
        blockstats['output_stop_offset'] = (len(window) + len(data)) * 8
        yield data
    def decode_type2_block(self, f, window):
        # type 2, fixed tables
        blockstats = self.stats.blockstats[-1]
        ll_sq = (144 * [8]) + (112 * [9]) + (24 * [7]) + (8 * [8])
        d_sq = 32 * [5]
        blockstats['codes_start_offset'] = self.offset
        blockstats['data_start_offset'] = self.offset
        blockstats['output_start_offset'] = len(window) * 8
        return self.decode_block_using_sqs(f, ll_sq, d_sq, window)
    def decode_type3_block(self, f, window):
        # type 3, dynamic tables
        blockstats = self.stats.blockstats[-1]
        blockstats['codes_start_offset'] = self.offset
        f.add_field('HLIT', self.take(5), BfdMsb(257))
        f.add_field('HDIST', self.take(5), BfdMsb(1))
        f.add_field('HCLEN', self.take(4), BfdMsb(4))
        for i in xrange(f.get_decoded('HCLEN')):
            field_name = 'CCL_%s' % cclorder[i]
            f.add_field(field_name, self.take(3), BfdMsb(0))
        code_to_sym = generate_huffman_codes_from_code_lengths(
            code_length_list_from_fieldlist(f))
        self.set_sq_huffman_codes(code_to_sym)
        blockstats['ll_codes_start_offset'] = self.offset
        ll_sq = self.take_sq(f.get_decoded('HLIT'))
        blockstats['d_codes_start_offset'] = self.offset
        d_sq = self.take_sq(f.get_decoded('HDIST'))
        blockstats['data_start_offset'] = self.offset
        blockstats['output_start_offset'] = len(window) * 8
        return self.decode_block_using_sqs(f, ll_sq, d_sq, window)
    def decode_block_using_sqs(self, f, ll_sq, d_sq, window):
        ll_codes = generate_huffman_codes_from_code_lengths(ll_sq)
        d_codes = generate_huffman_codes_from_code_lengths(d_sq)
        for line in str(f).split('\n'):
            self.iprint('BLOCK HEADER: %s' % line)
        for codes in (ll_codes, d_codes):
            for (sym, code) in sorted(
                (sym,code) for (code, sym) in codes.items()):
                c = '.'
                if sym < 256:
                    c = to_printable(sym)
                self.iprint('BLOCK HEADER: %s\t%s\t%s' % (code, c, sym))
        #self.iprint('BLOCK DATA: %s' % self)
        self.set_data_huffman_codes(ll_codes, d_codes)
        return self.take_data(window)
    def take_sq(self, num):
        sq = []
        self.use_sq_codes()
        while len(sq) < num:
            found_match = False
            sym = self.take_sym()
            if sym < 16:
                sq.append(sym)
            elif sym == 16:
                reps = BfdMsb(3)(self.take(2))
                sq += reps * [sq[-1]]
            elif sym == 17:
                reps = BfdMsb(3)(self.take(3))
                sq += reps * [0]
            elif sym == 18:
                reps = BfdMsb(11)(self.take(7))
                sq += reps * [0]
            else:
                raise DeflateError(
                    'Invalid sequence symbol %d at offset %d' %
                    (sym, self.offset))
        if len(sq) != num:
            raise DeflateError('Invalid number of lit/dist codes')
        return sq
    def take_data(self, window):
        blockstats = self.stats.blockstats[-1]
        flush_limit = 1024
        assert window.max_size >= flush_limit
        win_len = len(window)
        last_flush = win_len
        lt = get_ll_table()
        dt = get_d_table()
        length = None
        at_end = False
        self.use_ll_codes()
        while not at_end:
            sym = self.take_sym()
            if not length:
                if sym < 256:
                    window.append_byte(sym)
                    win_len += 1
                    if win_len - last_flush >= flush_limit:
                        yield window.last_n(flush_limit)
                        last_flush = win_len
                elif sym == 256:
                    at_end = True
                else:
                    (extra_bits, first_len) = lt[sym]
                    length = BfdMsbB(first_len)(self.take(extra_bits))
                    self.use_d_codes()
            else:
                (extra_bits, first_d) = dt[sym]
                dist = BfdMsbB(first_d)(self.take(extra_bits))
                start = win_len - dist
                assert(start >= 0)
                for i in xrange(start, start + length):
                    window.append_byte_from(i)
                    win_len += 1
                    if win_len - last_flush >= flush_limit:
                        yield window.last_n(flush_limit)
                        last_flush = win_len
                length = None
                self.use_ll_codes()
        if win_len > last_flush:
            yield window.last_n(win_len - last_flush)
        blockstats['data_stop_offset'] = self.offset
        blockstats['output_stop_offset'] = len(window) * 8
    def set_sq_huffman_codes(self, sq_codes):
        self.sq_codes = self.generate_codetable(sq_codes)
    def set_data_huffman_codes(self, ll_codes, d_codes):
        self.ll_codes = self.generate_codetable(ll_codes)
        self.d_codes = self.generate_codetable(d_codes)
    def use_sq_codes(self):
        self.codetable = self.sq_codes
    def use_ll_codes(self):
        self.codetable = self.ll_codes
    def use_d_codes(self):
        self.codetable = self.d_codes
    def generate_codetable(self, codes):
        ct = codes.items()
        lookup = defaultdict(list)
        for b in xrange(2**8):
            bits = to_bin(b)
            for (code, sym) in ct:
                if bits.startswith(code[0:8]):
                    lookup[bits].append((code, sym))
        return (ct, lookup)
    def take_sym(self):
        (ct, lookup) = self.codetable
        p = self.peek(8)
        for (code, sym) in lookup[p]:
            if p.startswith(code) or self.startswith(code):
                self.discard(len(code))
                return sym
        for (code, sym) in ct:
            if self.startswith(code):
                self.discard(len(code))
                return sym
        raise DeflateError(
            'Cannot decode symbol at offset %d' % self.offset)

class DeflateBlockStats(dict):
    def __init__(self, blocknumber, info_stream):
        dict.__init__(self)
        self.blocknumber = blocknumber
        self.info_stream = info_stream
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if self.info_stream:
            iprint(
                self.info_stream,
                'BLOCK[%d]: %s=%s' % (self.blocknumber, key, value))

class DeflateStats(object):
    def __init__(self, info_stream):
        self.start_offset = None
        self.blockstats = []
        self.info_stream = info_stream
    def add_blockstats(self):
        x = DeflateBlockStats(len(self.blockstats), self.info_stream)
        self.blockstats.append(x)
        return x
    def __str__(self):
        ret = ''
        def widen(text, width=35):
            return text + (width - len(text)) * ' '
        block_type_counts = defaultdict(int)
        total_compressed_size = 0
        total_uncompressed_size = 0
        total_overhead_size = 0
        for (i, bs) in enumerate(self.blockstats):
            nv = {
                'type': bs['type'],
                'size':
                    bs['data_stop_offset'] - bs['start_offset'],
                'codes_size':
                    bs['data_start_offset'] - bs['codes_start_offset'],
                'data_size':
                    bs['data_stop_offset'] - bs['data_start_offset'],
                'overhead_size':
                    bs['data_start_offset'] - bs['start_offset'],
                'uncompressed_size':
                    bs['output_stop_offset'] - bs['output_start_offset'],
                }
            if nv['size'] > 0:
                nv['overhead_ratio'] = float(nv['overhead_size']) / nv['size']
                nv['compress_ratio'] = float(nv['uncompressed_size']) / nv['size']
            else:
                nv['overhead_ratio'] = 'inf'
                nv['compress_ratio'] = 'inf'
            block_type_counts[bs['type']] += 1
            total_compressed_size += nv['size']
            total_uncompressed_size += nv['uncompressed_size']
            total_overhead_size += nv['overhead_size']
            for (name, val) in sorted(nv.items()):
                ret += widen('block_%02d_%s' % (i, name))
                if 'size' in name:
                    ret += '= %s b = %s B\n' % (val, val / 8.0)
                else:
                    ret += '= %s\n' % val
        ret += widen('uncompressed blocks') + ('= %s\n' % block_type_counts[1])
        ret += widen('type 2 blocks') + ('= %s\n' % block_type_counts[2])
        ret += widen('type 3 blocks') + ('= %s\n' % block_type_counts[3])
        ret += widen('total compressed size')
        ret += '= %s b = %s B\n' % (total_compressed_size, total_compressed_size / 8.0)
        ret += widen('total uncompressed size')
        ret += '= %s b = %s B\n' % (total_uncompressed_size, total_uncompressed_size / 8.0)
        ret += widen('total overhead size')
        ret += '= %s b = %s B\n' % (total_overhead_size, total_overhead_size / 8.0)
        ret += widen('total compress ratio')
        ret += '= %s\n' % (float(total_uncompressed_size) / total_compressed_size)
        return ret

ll_table = None
def get_ll_table():
    """Return ll_table.

    ll_table is dict in format: code -> (extra_bits, first_length)

    >>> ll = get_ll_table()
    >>> sorted(ll.keys()) == list(range(257, 285+1))
    True
    >>> [ll[257], ll[258], ll[259]]
    [(0, 3), (0, 4), (0, 5)]
    >>> [ll[272], ll[273]]
    [(2, 31), (3, 35)]
    >>> max(xtra for (xtra, flen) in ll.values())
    5
    >>> max(flen for (xtra, flen) in ll.values())
    258
    >>> max(flen + 2**xtra-1 for (xtra, flen) in ll.values())
    258
    """
    global ll_table
    if ll_table:
        return ll_table
    stops = [257, 265, 269, 273, 277, 281, 285]
    ll = {}
    next_len = 3
    for (i, start) in enumerate(stops):
        if i >= len(stops) - 1:
            break
        stop = stops[i + 1]
        for c in xrange(start, stop):
            ll[c] = (i, next_len)
            next_len += 2**i
    ll[285] = (0, 258)
    ll_table = ll
    return ll_table

d_table = None
def get_d_table():
    """Return d_table.

    d_table is dict in format: code -> (extra_bits, distance)

    Some properties:

    >>> dt = get_d_table()
    >>> sorted(dt.keys()) == list(range(0, 29+1))
    True
    >>> [dt[0], dt[1], dt[2]]
    [(0, 1), (0, 2), (0, 3)]
    >>> [dt[15], dt[16], dt[17], dt[18]]
    [(6, 193), (7, 257), (7, 385), (8, 513)]
    >>> max(xtra for (xtra, dist) in dt.values())
    13
    >>> max(dist for (xtra, dist) in dt.values())
    24577
    >>> max(dist + 2**xtra-1 for (xtra, dist) in dt.values())
    32768
    """
    global d_table
    if d_table:
        return d_table
    stops = [0] + list(range(4, 31, 2))
    dt = {}
    next_d = 1
    for (i, start) in enumerate(stops):
        if i >= len(stops) - 1:
            break
        stop = stops[i + 1]
        for c in xrange(start, stop):
            dt[c] = (i, next_d)
            next_d += 2**i
    d_table = dt
    return d_table

def code_length_list_from_fieldlist(fl):
    cll = []
    for i in sorted(cclorder):
        key = 'CCL_%s' % i
        if key in fl:
            cl = fl.get_decoded(key)
        else:
            cl = 0
        cll.append(cl)
    return cll

def generate_huffman_codes_from_code_lengths(code_lengths):
    bl_count = defaultdict(int)
    for cl in code_lengths:
        bl_count[cl] += 1
    bl_count[0] = 0
    next_code = {}
    code = 0
    max_code_length = max(code_lengths)
    for bits in xrange(1, max_code_length + 1):
        code = (code + bl_count[bits - 1]) * 2
        next_code[bits] = code
    codes = {}
    for (k, cl) in enumerate(code_lengths):
        if cl:
            codes[k] = next_code[cl]
            next_code[cl] += 1
    code_to_sym = {}
    for k in codes.keys():
        b = bin(codes[k]).split('b')[1]
        b = (code_lengths[k] - len(b)) * '0' + b
        code_to_sym[b] = k
    return code_to_sym

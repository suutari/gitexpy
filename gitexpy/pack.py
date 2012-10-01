import binascii
import hashlib
import mmap
import struct
import zlib

from . import delta
from .sixx import byte2int

class Error(Exception):
    """Pack Error"""

OBJ_TYPE_COMMIT = 1
OBJ_TYPE_TREE = 2
OBJ_TYPE_BLOB = 3
OBJ_TYPE_TAG = 4
OBJ_TYPE_OFS_DELTA = 6
OBJ_TYPE_REF_DELTA = 7
object_types = {
    1: 'commit',
    2: 'tree',
    3: 'blob',
    4: 'tag',
    6: 'ofs_delta',
    7: 'ref_delta',
}

DELTA_OBJECT_TYPES = [OBJ_TYPE_OFS_DELTA, OBJ_TYPE_REF_DELTA]

class Packfile(object):
    def __init__(self, filename):
        self.__file = open(filename, 'rb')
        if self.__file.read(4) != b'PACK':
            raise Error('Not a packfile: %s' % filename)
        self.version = struct.unpack('>L', self.__file.read(4))[0]
        if self.version != 2:
            raise Error(
                'Version %d packfile is not supported: %s' %
                (self.version, filename))
        self.__objectcount = struct.unpack('>L', self.__file.read(4))[0]
        self.header_length = self.__file.tell()
        self.data = mmap.mmap(
            self.__file.fileno(), length=0, access=mmap.ACCESS_READ)
        self.object_offset_map = {}
        self.offset_id_map = {}
        self.offsets = [self.header_length]
    @property
    def filename(self):
        return self.__file.name
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
    def first_object(self):
        return self.object_at(self.header_length)
    def object_at(self, offset):
        try:
            return self.object_offset_map[offset]
        except KeyError:
            obj = PackfileObject(self, offset)
            self.object_offset_map[offset] = obj
            return obj
    def object_by_id(self, object_id):
        try:
            return self.object_at(self.offset_id_map[object_id])
        except KeyError:
            for obj in self:
                self.offset_id_map[obj.id] = obj.offset
                if obj.id == object_id:
                    return obj
        raise Error(
            'Object with id=%s not found' %
            binascii.hexlify(object_id).decode('ascii'))
    def __len__(self):
        return self.__objectcount
    def __getitem__(self, i):
        if i < 0 or i >= len(self):
            raise IndexError(
                'Object index %d is not in [0,%d]' % (i, len(self)-1))
        if len(self.offsets) <= i:
            offset = self.offsets[-1]
            n = len(self.offsets) - 1
            while n <= i:
                offset = self.object_at(offset).end
                n += 1
                assert n == len(self.offsets)
                self.offsets.append(offset)
        assert len(self.offsets) > i
        return self.object_at(self.offsets[i])
    def is_checksum_ok(self):
        sha = hashlib.sha1()
        sha.update(self.data[:-20])
        return self.data[-20:] == sha.digest()
    def verify(self):
        last_object_end = self[len(self)-1].end
        assert last_object_end == len(self.data) - 20
        assert self.is_checksum_ok
        for obj in self:
            assert obj.size == len(obj.decompressed_data)
            if obj.type in DELTA_OBJECT_TYPES:
                assert obj.delta_base

class PackfileObject(object):
    def __init__(self, packfile, offset):
        self.packfile = packfile
        self.pack = packfile.data
        self.offset = offset
        self.__init_from_header()
        self.__end = None
        self.__delta_base = None
        self.__delta_depth = None
        self.__real_type = None
        self.__decompressed_data = None
        self.__data = None
        self.__id = None
    def __init_from_header(self):
        pos = self.offset
        self.type = (byte2int(self.pack[pos]) & 0b01110000) >> 4
        sz = byte2int(self.pack[pos]) & 0b00001111
        shift = 4
        while byte2int(self.pack[pos]) & 0b10000000:
            pos += 1
            sz |= (byte2int(self.pack[pos]) & 0b01111111) << shift
            shift += 7
        self.size = sz
        if self.type == OBJ_TYPE_OFS_DELTA:
            pos += 1
            dplus = 0
            dplusadd = 1
            doff = byte2int(self.pack[pos]) & 0b01111111
            while byte2int(self.pack[pos]) & 0b10000000:
                pos += 1
                dplusadd <<= 7
                dplus |= dplusadd
                doff <<= 7
                doff |= (byte2int(self.pack[pos]) & 0b01111111)
            self.delta_offset = doff + dplus
            self.__delta_base_id = None
        elif self.type == OBJ_TYPE_REF_DELTA:
            self.delta_offset = None
            self.__delta_base_id = self.pack[pos+1:pos+21]
            pos += 20
        else:
            self.delta_offset = None
            self.__delta_base_id = None
        self.start = pos + 1
    @property
    def end(self):
        if self.__end is None:
            self.__decompress()
        return self.__end
    @property
    def delta_base(self):
        if self.__delta_base is None:
            if self.delta_offset is not None:
                self.__delta_base = self.packfile.object_at(
                    self.offset - self.delta_offset)
            elif self.__delta_base_id is not None:
                self.__delta_base = self.packfile.object_by_id(
                    self.__delta_base_id)
        return self.__delta_base
    @property
    def delta_base_id(self):
        if self.__delta_base_id is None:
            if self.delta_base is not None:
                self.__delta_base_id = self.delta_base.id
        return self.__delta_base_id
    @property
    def delta_depth(self):
        if self.__delta_depth is None:
            if self.delta_base is not None:
                self.__delta_depth = self.delta_base.delta_depth + 1
            else:
                self.__delta_depth = 0
        return self.__delta_depth
    @property
    def real_type(self):
        if self.__real_type is None:
            if self.delta_base is not None:
                self.__real_type = self.delta_base.real_type
            else:
                self.__real_type = self.type
        return self.__real_type
    @property
    def raw_data(self):
        return self.pack[self.start:self.end]
    @property
    def decompressed_data(self):
        if self.__decompressed_data is None:
            self.__decompress()
        return self.__decompressed_data
    @property
    def data(self):
        if self.__data is None:
            if self.type in DELTA_OBJECT_TYPES:
                self.__data = delta.decode_delta(
                    self.decompressed_data, self.delta_base.data)
            else:
                self.__data = self.decompressed_data
        return self.__data
    @property
    def id(self):
        if self.__id is None:
            hdr = '%s %d\0' % (object_types[self.real_type], len(self.data))
            sha = hashlib.sha1()
            sha.update(hdr.encode('ascii') + self.data)
            self.__id = sha.digest()
        return self.__id
    def __decompress(self):
        block_len = 4096
        decompressor = zlib.decompressobj()
        pos = self.start
        data = b''
        while True:
            in_block_len = min(block_len, len(self.pack) - pos)
            in_block = self.pack[pos:pos+in_block_len]
            assert len(in_block) == in_block_len, '%d != %d' % (len(in_block), in_block_len)
            decompressed = decompressor.decompress(in_block)
            pos += in_block_len
            data += decompressed
            if decompressor.unused_data:
                break
            if pos >= len(self.pack):
                assert pos == len(self.pack)
                assert not decompressor.unconsumed_tail
                break
        self.__decompressed_data = data
        self.__end = pos - len(decompressor.unused_data)
    def __repr__(self):
        typestr = (
            object_types[self.type] if self.type in object_types
            else 'type=%d' % self.type)
        return '<%s %s offset=%d>' % (
            self.__class__.__name__, typestr, self.offset)

def main(sys):
    Packfile(sys.argv[1]).verify()

if __name__ == '__main__':
    import sys
    main(sys)

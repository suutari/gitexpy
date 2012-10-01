import binascii
import hashlib
import os
import subprocess
import zlib
from six import print_
from . import pack
from .sixx import astr, bytes2ints

packfile_cache = {}

class Error(Exception):
    """GOM Error"""

def main(sys):
    try:
        cmd = sys.argv[1]
        obj_id = sys.argv[2]
        if cmd == 'dump':
            func = dump
        elif cmd == 'walk':
            func = walk
        else:
            raise Exception('Unknown cmd')
    except:
        print('Usage: %s cmd obj_id' % sys.argv[0])
        print('  where cmd should be "dump" or "walk"')
        sys.exit(1)
    func(obj_id)

def dump(obj_id):
    obj = get_git_object_by_id(obj_id)
    print(obj.pretty_str())

def walk(obj_id):
    top = get_git_object_by_id(obj_id)
    assert str(top.get_object_id()) == obj_id
    print_(top.pretty_str(), end='')
    for (path, objpath, obj) in walk_objects(top):
        print(str(obj.get_object_id()), path)

def walk_objects(start_obj):
    start_objid = str(start_obj.get_object_id())
    for (name, objid) in start_obj.get_named_links():
        obj = get_git_object_by_id(objid)
        objpath = start_objid + '.' + str(objid)
        yield (name, objpath, obj)
        for (sub_name, sub_objpath, sub_obj) in walk_objects(obj):
            yield (name + '/' + sub_name, objpath + '.' + sub_objpath, sub_obj)

def get_git_object_by_id(object_id):
    try:
        return parse_object_file_contents(get_git_object_file_contents(object_id))
    except IOError:
        packdir = os.path.join('.git', 'objects', 'pack')
        for packname in os.listdir(packdir):
            if packname.endswith('.pack'):
                pf = packfile_cache.get(packname, None)
                if pf is None:
                    packpath = os.path.join(packdir, packname)
                    pf = pack.Packfile(packpath)
                    packfile_cache[packname] = pf
                try:
                    packobj = pf.object_by_id(ObjectId(object_id).b)
                except pack.Error:
                    continue
                tp = pack.object_types[packobj.real_type].encode('ascii')
                ObjType = git_object_types[tp]
                return ObjType.from_contents(packobj.data)
        raise Error('Object not found: %s' % object_id)

def get_git_object_file_contents(object_id):
    d = str(object_id)[0:2]
    f = str(object_id)[2:]
    return open(os.path.join('.git', 'objects', d, f), 'rb').read()
    #tp = run_cmd('git cat-file -t %s' % object_id).strip()
    #return compress(run_cmd('git cat-file %s %s' % (tp, object_id)))

def parse_object_file(f):
    return parse_object_file_contents(f.read())

def parse_object_file_contents(x):
    (header, data) = decompress(x).split(b'\0', 1)
    (tp, sz) = header.split(b' ')
    assert len(data) == int(sz)
    ObjType = git_object_types[tp]
    return ObjType.from_contents(data)

def decompress(f):
    return zlib.decompress(f)

def sha1(x):
    z = hashlib.sha1()
    z.update(x)
    return z.digest()

def to_hex_str(x):
    return astr(binascii.hexlify(x))

def from_hex_str(x):
    return binascii.unhexlify(x.encode('ascii'))

def run_cmd(cmd):
    return subprocess.check_output(cmd.split(' '))

class ObjectId(object):
    """
    Git object identifier.

    >>> oid = ObjectId('0102030405060708090a0b0c0d0e0f406080a0ff')
    >>> oid
    ObjectId('0102030405060708090a0b0c0d0e0f406080a0ff')
    >>> bytes2ints(oid.b) == [
    ...     1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
    ...     12, 13, 14, 15, 64, 96, 128, 160, 255]
    True

    >>> oid = ObjectId(b'abcdefghijklmnopqrst')
    >>> oid
    ObjectId('6162636465666768696a6b6c6d6e6f7071727374')
    >>> bytes2ints(oid.b) == [
    ...     97, 98, 99, 100, 101, 102, 103, 104, 105, 106,
    ...     107, 108, 109, 110, 111, 112, 113, 114, 115, 116]
    True

    >>> ObjectId(oid).b == oid.b
    True
    """
    def __init__(self, x):
        try:
            self.b = x.b
        except AttributeError:
            if len(x) == 20:
                self.b = x
            elif len(x) == 40:
                self.b = from_hex_str(x)
            else:
                raise Exception('Unknown arg of len %s for ObjectId' % len(x))
    def __str__(self):
        return to_hex_str(self.b)
    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(to_hex_str(self.b)) + ')'

class FileMode(bytes):
    pass

class GitObject(object):
    def get_object_id(self):
        sha = hashlib.sha1()
        sha.update(self.get_object_type())
        sha.update((' %d\0' % self.get_size()).encode('ascii'))
        for x in self.iterate_contents():
            sha.update(x)
        return ObjectId(sha.digest())
    def get_object_type(self):
        raise NotImplementedError
    def get_contents(self):
        return b''.join(self.iterate_contents())
    def iterate_contents(self):
        raise NotImplementedError
    def get_size(self):
        return len(self.get_contents())
    def pretty_str(self):
        raise NotImplementedError

class BlobObject(GitObject):
    def __init__(self, contents):
        self.contents = contents
    def get_object_type(self):
        return b'blob'
    def iterate_contents(self):
        yield self.contents
    def pretty_str(self):
        return self.contents
    def get_named_links(self):
        return ()
    @classmethod
    def from_contents(cls, contents):
        return cls(contents)

class TreeObject(GitObject):
    def __init__(self, entries):
        self.entries = entries
    def get_object_type(self):
        return b'tree'
    def iterate_contents(self):
        for (mode, name, oid) in self.entries:
            yield mode + b' ' + name + b'\0' + oid.b
    def pretty_str(self):
        return '\n'.join(str(e) for e in self.entries)
    def get_named_links(self):
        for (m, n, i) in self.entries:
            yield (n, i)
    @classmethod
    def from_file(cls, objfile):
        return cls.from_contents(objfile.read())
    @classmethod
    def from_contents(cls, contents):
        entries = []
        i = 0
        while i < len(contents):
            space_pos = contents.find(b' ', i + 1)
            assert space_pos > 0
            null_pos = contents.find(b'\0', space_pos + 1)
            assert null_pos > space_pos
            mode = contents[i:space_pos]
            name = contents[space_pos+1:null_pos]
            oid = contents[null_pos+1:null_pos+21]
            assert len(oid) == 20
            i = null_pos+21
            entries.append((FileMode(mode), name, ObjectId(oid)))
        return cls(entries)

class CommitObject(GitObject):
    """NYI: CommitObject"""
    def get_object_type(self):
        return b'commit'

class TagObject(GitObject):
    """NYI: TagObject"""
    def get_object_type(self):
        return b'tag'

git_object_types = {
    b'blob': BlobObject,
    b'tree': TreeObject,
    b'commit': CommitObject,
    b'tag': TagObject,
    }

if __name__ == '__main__':
    import sys
    main(sys)

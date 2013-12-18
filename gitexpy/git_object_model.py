"""
Utils for parsing Git Objects.
"""
import binascii
import hashlib
import os
import zlib
from six import print_
from . import pack
from .sixx import astr

PACKFILE_CACHE = {}


class Error(Exception):
    """GOM Error"""


def main(sys):
    """
    Run git object experiments.
    """
    try:
        cmd = sys.argv[1]
        obj_id = sys.argv[2]
        if cmd == 'dump':
            func = dump
        elif cmd == 'walk':
            func = walk
        else:
            raise Exception('Unknown cmd')
    except Exception:  # pylint: disable=broad-except
        print('Usage: %s cmd obj_id' % sys.argv[0])
        print('  where cmd should be "dump" or "walk"')
        sys.exit(1)
    func(obj_id)


def dump(obj_id):
    """
    Dump Git object by obj_id.
    """
    obj = get_git_object_by_id(obj_id)
    print(obj.pretty_str())


def walk(obj_id):
    """
    Walk a chain of Git objects and print them.
    """
    top = get_git_object_by_id(obj_id)
    assert str(top.get_object_id()) == obj_id
    print_(top.pretty_str(), end='')
    for (path, _, obj) in walk_objects(top):
        print(str(obj.get_object_id()), path)


def walk_objects(start_obj):
    """
    Walk a chaing of Git objects and yield them.
    """
    start_objid = str(start_obj.get_object_id())
    for (name, objid) in start_obj.get_named_links():
        obj = get_git_object_by_id(objid)
        objpath = start_objid + '.' + str(objid)
        yield (name, objpath, obj)
        for (sub_name, sub_objpath, sub_obj) in walk_objects(obj):
            yield (name + '/' + sub_name, objpath + '.' + sub_objpath, sub_obj)


def get_git_object_by_id(object_id):
    """
    Get Git object by object_id.
    """
    try:
        contents = get_git_object_file_contents(object_id)
        return parse_object_file_contents(contents)
    except IOError:
        packdir = os.path.join('.git', 'objects', 'pack')
        for packname in os.listdir(packdir):
            if packname.endswith('.pack'):
                packfile = PACKFILE_CACHE.get(packname, None)
                if packfile is None:
                    packpath = os.path.join(packdir, packname)
                    packfile = pack.Packfile(packpath)
                    PACKFILE_CACHE[packname] = packfile
                try:
                    packobj = packfile.object_by_id(ObjectId(object_id).bytes)
                except pack.Error:
                    continue
                obj_type_name = pack.object_types[packobj.real_type]
                obj_type_class = GIT_OBJECT_TYPES[obj_type_name]
                return obj_type_class.from_contents(packobj.data)
        raise Error('Object not found: %s' % object_id)


def get_git_object_file_contents(object_id):
    """
    Get contents of a Git object file by object_id.
    """
    dirname = str(object_id)[0:2]
    filename = str(object_id)[2:]
    filepath = os.path.join('.git', 'objects', dirname, filename)
    return open(filepath, 'rb').read()


def parse_object_file(fileobj):
    """
    Parse contents of Git object file using file object.
    """
    return parse_object_file_contents(fileobj.read())


def parse_object_file_contents(contents):
    """
    Parse contents of Git object file.
    """
    (header, data) = decompress(contents).split(b'\0', 1)
    (obj_type_name, size) = header.decode('ascii').split(' ')
    assert len(data) == int(size)
    obj_type_class = GIT_OBJECT_TYPES[obj_type_name]
    return obj_type_class.from_contents(data)


def decompress(contents):
    """
    Decompress Git object contents.
    """
    return zlib.decompress(contents)


def sha1(x):
    """
    Calculate SHA1 of given bytes.

    >>> to_hex_str(sha1(b''))
    'da39a3ee5e6b4b0d3255bfef95601890afd80709'
    """
    return hashlib.sha1(x).digest()


def to_hex_str(x):
    """
    Convert bytes to hexadecimal form.

    >>> to_hex_str(b'\x42\x6a\x5f')
    '426a5f'
    """
    return astr(binascii.hexlify(x))


def from_hex_str(x):
    """
    Convert hexadecimal string to bytes.
    """
    return binascii.unhexlify(x.encode('ascii'))


class ObjectId(object):  # pylint: disable=too-few-public-methods
    """
    Git object identifier.

    >>> oid = ObjectId('0102030405060708090a0b0c0d0e0f406080a0ff')
    >>> oid
    ObjectId('0102030405060708090a0b0c0d0e0f406080a0ff')
    >>> [x if isinstance(x, int) else ord(x) for x in oid.bytes] == [
    ...     1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
    ...     12, 13, 14, 15, 64, 96, 128, 160, 255]
    True

    >>> oid = ObjectId(b'abcdefghijklmnopqrst')
    >>> oid
    ObjectId('6162636465666768696a6b6c6d6e6f7071727374')
    >>> [x if isinstance(x, int) else ord(x) for x in oid.bytes] == [
    ...     97, 98, 99, 100, 101, 102, 103, 104, 105, 106,
    ...     107, 108, 109, 110, 111, 112, 113, 114, 115, 116]
    True

    >>> ObjectId(oid).bytes == oid.bytes
    True
    """
    def __init__(self, x):
        try:
            self.bytes = x.bytes
        except AttributeError:
            if len(x) == 20:
                self.bytes = x
            elif len(x) == 40:
                self.bytes = from_hex_str(x)
            else:
                raise Exception('Unknown arg of len %s for ObjectId' % len(x))

    def __str__(self):
        return to_hex_str(self.bytes)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, to_hex_str(self.bytes))


class FileMode(bytes):  # pylint: disable=too-many-public-methods
    """
    File mode in Git tree object.
    """


class GitObject(object):
    """
    Base class for Git objects.
    """
    @classmethod
    def from_contents(cls, contents):
        """
        Generate Git object from bytes contents.
        """
        return cls(contents)

    @classmethod
    def from_file(cls, objfile):
        """
        Generate Git object from file object contents.
        """
        return cls.from_contents(objfile.read())

    def get_object_id(self):
        """Get id of this object."""
        sha = hashlib.sha1()
        sha.update(self.get_object_type())
        sha.update((' %d\0' % self.get_size()).encode('ascii'))
        for x in self.iterate_contents():
            sha.update(x)
        return ObjectId(sha.digest())

    def get_object_type(self):
        """Get type of this object."""
        raise NotImplementedError

    def get_contents(self):
        """Get contents of this object as bytes."""
        return b''.join(self.iterate_contents())

    def iterate_contents(self):
        """
        Iterate contents of this object.

        Iterating the contents will yield bytes chunk by
        chunk. Concatenating the chunks should give the same result as
        with `get_contents`.
        """
        raise NotImplementedError

    def get_size(self):
        """Get size of this object."""
        return len(self.get_contents())

    def pretty_str(self):
        """Get pretty representation of this object."""
        raise NotImplementedError

    def get_named_links(self):
        """
        Get iterable of name-object_id pairs.

        Each pair represents a subobject of this object.
        """
        raise NotImplementedError


class BlobObject(GitObject):
    """
    Git blob object.
    """
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


class TreeObject(GitObject):
    """
    Git tree object.
    """
    def __init__(self, entries):
        self.entries = entries

    def get_object_type(self):
        return b'tree'

    def iterate_contents(self):
        for (mode, name, oid) in self.entries:
            yield mode + b' ' + name + b'\0' + oid.bytes

    def pretty_str(self):
        return '\n'.join(str(e) for e in self.entries)

    def get_named_links(self):
        for (_, name, oid) in self.entries:
            yield (name, oid)

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


# class CommitObject(GitObject):
#     """NYI: CommitObject"""
#     def get_object_type(self):
#         return b'commit'


# class TagObject(GitObject):
#     """NYI: TagObject"""
#     def get_object_type(self):
#         return b'tag'


GIT_OBJECT_TYPES = {
    'blob': BlobObject,
    'tree': TreeObject,
    #'commit': CommitObject,
    #'tag': TagObject,
    }


if __name__ == '__main__':
    import sys as sys_module
    main(sys_module)

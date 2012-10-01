from __future__ import division

import hashlib
import math
from . import rabin

def blockify(data, avgsize=1024, minsize=256, maxsize=8192):
    assert avgsize > 0
    assert minsize > 0
    assert maxsize > minsize
    matchbits = int(math.log(avgsize, 2) + 0.5)
    mask = 2**matchbits - 1
    splitval = mask
    # FIXME: Decorate data with something that implements windowing
    # (of size maxsize) and supports getitem. For now implementing
    # this with deep copy of all data.
    data = b''.join(data)
    lastsplit = 0
    for stop in rabin_split(data, mask, splitval, maxsize - minsize):
        blocklen = stop - lastsplit
        assert blocklen <= maxsize
        if blocklen < minsize:
            continue
        yield data[lastsplit:stop]
        lastsplit = stop
    if lastsplit < stop:
        yield data[lastsplit:stop]

def rabin_split(data, mask, splitval, maxsize):
    last_pos = -1
    for (pos, fp) in enumerate(rabin.iterate_fingerprints(data)):
        if fp & mask == splitval or pos - last_pos >= maxsize:
            if pos > last_pos:
                yield pos
                last_pos = pos
    if pos > last_pos:
        yield pos

def pretty_print_blocks(data, mask=7, splitval=0):
    assert len(data) < 10000
    blockmap = {}
    for (n, block) in enumerate(blockify(data, mask, splitval)):
        try:
            dupinfo = ' [duplicate of #%03d]' % blockmap[block]
        except KeyError:
            dupinfo = ''
            blockmap[block] = n
        print('#%03d %-40r %3d%s' % (n, block, len(block), dupinfo))

def stat_blockify(
    data,
    avgsize=1024,
    minsize=512,
    maxsize=2048,
    checkduplicates=True):
    if checkduplicates:
        sizebyhash = {}
    blocksizes = []
    duplicates = 0
    duplicated_sizes = []
    for (n, block) in enumerate(blockify(data, avgsize, minsize, maxsize)):
        if checkduplicates:
            blockhash = sha1(block)
            if blockhash in sizebyhash:
                duplicated_sizes.append(len(block))
                assert sizebyhash[blockhash] == len(block)
            else:
                sizebyhash[blockhash] = len(block)
        blocksizes.append(len(block))
    #assert sum(blocksizes) == len(data)
    for (a, b) in [
        (1,5), (6,10), (11,15), (16,20),
        (1, 100), (101,200), (201,300), (301,400), (401,500), (501,600),
        (601,700), (701,800), (801,900), (901,1000), (1001,1100), (1101,1200),
        (1201,1300), (1301,1400), (1401,1500), (1501,1600),
        (1601,1700), (1701,1800), (1801, 1900), (1901,2000),
        (2001,2100), (2101,2200), (2201,2300), (2301,2400), (2401,2500),
        (2501,2600), (2601,2700), (2701,2800), (2801,2900), (2901,3000),
        (3001,4000), (4001,5000), (5001,6000), (6001,7000),
        (7001,8000), (8001,9000), (9001,10000),
        (10001,100000), (100001,1000000)]:
        freq = sum(1 for s in blocksizes if a <= s <= b)
        bar = (200 * freq // len(blocksizes)) * '-'
        if len(bar) > 100:
            bar = 100 * '-' + '>'
        print('%-22s %7d to %7d: %7d %s' % (
                'Block size histogram:', a, b, freq, bar))
    print('%-40s %9d' % (
            'Number of blocks:', len(blocksizes)))
    print('%-40s %12.2f' % (
            'Average block size:', sum(blocksizes) / len(blocksizes)))
    print('%-40s %9d' % (
            'Minimum block size:', min(blocksizes)))
    print('%-40s %9d' % (
            'Maximum block size:', max(blocksizes)))
    print('%-40s %9d' % ('Total size:', sum(blocksizes)))
    if checkduplicates:
        print('%-40s %9d' % ('Total bytes in unique blocks:', sum(sizebyhash.values())))
        print('%-40s %9d' % ('Number of unique blocks:', len(sizebyhash)))
        print('%-40s %9d' % (
                'Number of duplicate blocks:',
                len(duplicated_sizes)))
        print('%-40s %9d = %3d %%' % (
                'Duplicated size:',
                sum(duplicated_sizes),
                100 * sum(duplicated_sizes) / sum(blocksizes)))

def sha1(data):
    sha = hashlib.sha1()
    sha.update(data)
    return sha.digest()

def main(sys):
    try:
        stdin = sys.stdin.detach()
    except:
        stdin = sys.stdin
    stat_blockify(bytefy_stream(stdin))
    sys.exit(0)

def bytefy_stream(stream):
    for block in split_stream_to_constant_size_blocks(stream, 4096):
        for byte in block:
            yield byte

def split_stream_to_constant_size_blocks(stream, blocksize):
    assert blocksize >= 1
    block = stream.read(blocksize)
    while block:
        yield block
        block = stream.read(blocksize)

if __name__ == '__main__':
    import sys
    main(sys)

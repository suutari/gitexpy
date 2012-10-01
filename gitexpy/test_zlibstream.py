import base64
from nose.tools import *
from six import BytesIO, StringIO

from . import zlibstream

def generate_deflate_data(input_string, compression_level=9):
    """
    Used for generating test data in this file.

    >>> generate_deflate_data(b'Hello World!')
    'eNrzSM3JyVcIzy/KSVEEABxJBD4='
    >>> generate_deflate_data(100*b'a'+1000*b'b'+100*b'c')
    'eNpLTKQ9SBoFo2AUDHuQTAcAACS8y3A='
    >>> generate_deflate_data(999 * b'Hello World!')
    'eNrtxjENACAQBDAr4OYdYAC2Sz7B/4ALpnZqnaTH6ps9y93d3d3d3d3d3d3d3d3d3d3d3d3d3d394x/82or8'
    >>> generate_deflate_data(b'Hello Deflate', 0)
    'eAEBDQDy/0hlbGxvIERlZmxhdGUgjATK'
    """
    import zlib
    from .sixx import astr
    return astr(
        base64.b64encode(
            zlib.compress(input_string, compression_level)))

testdata = {
    'simple type 2': (
        b'Hello World!',
        b'eNrzSM3JyVcIzy/KSVEEABxJBD4=', {
            'uncompressed blocks': 0,
            'type 2 blocks': 1,
            'type 3 blocks': 0,
            'total compressed size': 106,
            'total uncompressed size': 96,
            'total overhead size': 3,
            'block_00_codes_size': 0,
            }),
    'simple uncompressed': (
        b'Hello Deflate',
        b'eAEBDQDy/0hlbGxvIERlZmxhdGUgjATK', {
            'uncompressed blocks': 1,
            'type 2 blocks': 0,
            'type 3 blocks': 0,
            'total compressed size': 144,
            'total uncompressed size': 104,
            'total overhead size': 40,
            'block_00_codes_size': 0,
            }),
    'longer type 2': (
        100*b'a'+1000*b'b'+100*b'c',
        b'eNpLTKQ9SBoFo2AUDHuQTAcAACS8y3A=', {
            'uncompressed blocks': 0,
            'type 2 blocks': 1,
            'type 3 blocks': 0,
            'total compressed size': 131,
            'total uncompressed size': 9600,
            'total overhead size': 3,
            'block_00_codes_size': 0,
            }),
    'long type 3': (
        999 * b'Hello World!',
        b'eNrtxjENACAQBDAr4OYdYAC2Sz7B/4ALpnZqnaTH6p'
        b's9y93d3d3d3d3d3d3d3d3d3d3d3d3d3d394x/82or8', {
            'uncompressed blocks': 0,
            'type 2 blocks': 0,
            'type 3 blocks': 1,
            'total compressed size': 454,
            'total uncompressed size': 95904,
            'total overhead size': 198,
            'block_00_codes_size': 195,
            }),
    }

erroneous_testdata = {
    'empty data': (
        'Unexpected end of stream',
        b''),
    'too short data': (
        'Unexpected end of stream',
        b'QQ=='),
    'invalid zlib header': (
        'Invalid checksum in ZLIB header',
        b'YtqrAAB4eQB5'),
    'incorrect block len': (
        'Uncompressed block length decode error',
        b'AAAAAAAAAAAAAAAA'),
    'invalid number of lit/dist codes': (
        'Invalid number of lit/dist codes',
        b'eNrtxjENYSAQBDDg5h1gALZLPsH/gAumdmqdpMfqmz'
        b'3L3d3d3d3d3d3d3d3d3d3d3d3d3d3d3f3jH/zaivw='),
    }

def run_zlibstream_parse_on(b64encoded):
    """
    Run zlibstream.parse on given data, which is first decoded with b64.
    """
    compressed = base64.b64decode(b64encoded)
    in_stream = BytesIO(compressed)
    result = BytesIO()
    info_stream = StringIO()
    zlibstream.parse(in_stream, result, info_stream)
    assert not in_stream.read(), 'zlibstream.parse did not read all data'
    decompressed = result.getvalue()
    info = info_stream.getvalue()
    return (decompressed, info)

def test_decompression():
    def check(idx):
        (original, b64encoded) = testdata[idx][0:2]
        (decompressed, info) = run_zlibstream_parse_on(b64encoded)
        eq_(decompressed, original)
    for idx in testdata:
        yield (check, idx)

def parse_info(info):
    data = {}
    for line in info.split('\n'):
        if (line.startswith('BLOCK HEADER:') or
            line.startswith('HEADER') or
            line.startswith('BLOCK[')):
            continue
        if not '=' in line:
            continue
        (field, valstr) = line.split('=', 1)
        field = field.strip()
        if '=' in valstr:
            valstr = valstr.split('=', 1)[0]
        valstr = valstr.strip()
        if valstr.endswith(' b'):
            valstr = valstr[:-2]
        if 'ratio' in field:
            val = float(valstr)
        else:
            val = int(valstr)
        data[field] = val
    return data

def test_info():
    def check(idx):
        (original, b64encoded, expected_info) = testdata[idx]
        (decompressed, info) = run_zlibstream_parse_on(b64encoded)
        info = parse_info(info)
        for k in expected_info:
            eq_(info[k], expected_info[k],
                'invalid value for field %r: got %r, expected %r' % (
                    k,info[k],expected_info[k]))
    for idx in testdata:
        yield (check, idx)

def test_erroneous_input():
    def check(idx):
        (errormsg, b64encoded) = erroneous_testdata[idx]
        try:
            (result, info) = run_zlibstream_parse_on(b64encoded)
            ok_(False,
                'zlibstream.parse did not raise an exception'
                ' on erroneous data, got result=%r instead' % result)
        except Exception as e:
            ok_(errormsg in str(e),
                'Error message %r did not contain %r as expected' %
                (str(e), errormsg))
    for idx in erroneous_testdata:
        yield (check, idx)

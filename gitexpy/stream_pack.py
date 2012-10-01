from . import pack
from . import sixx

def main(sys):
    sixx.make_streams_binary(sys)
    if sys.argv[1] == '--undeltify':
        undeltify = True
        packfile_path = sys.argv[2]
    else:
        undeltify = False
        packfile_path = sys.argv[1]
    stream_pack(packfile_path, sys.stdout, undeltify)
    sys.exit(0)

def stream_pack(packfile_path, out_stream, undeltify):
    for data in iterate_packfile_stream(packfile_path, undeltify):
        out_stream.write(data)

def iterate_packfile_stream(packfile_path, undeltify):
    for obj in pack.Packfile(packfile_path):
        if undeltify:
            data = obj.data
        else:
            data = obj.decompressed_data
        yield ('%d\n' % len(data)).encode('ascii')
        yield data

if __name__ == '__main__':
    import sys
    main(sys)

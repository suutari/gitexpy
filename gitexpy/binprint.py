from six.moves import xrange
from .chrconvert import to_bin, to_bin_inverted, to_printable8
from .sixx import bytes2ints

def main(sys):
    """
    Main function of binprint.

    >>> import sys
    >>> sys.argv = ['binprint', 'hello']; main(sys)
    01101000 01100101 01101100 01101100 01101111
    \ 68 h / \ 65 e / \ 6c l / \ 6c l / \ 6f o /
    >>> sys.argv = ['binprint', '-i', 'hello']; main(sys)
    00010110 10100110 00110110 00110110 11110110
    \ 68 h / \ 65 e / \ 6c l / \ 6c l / \ 6f o /
    >>> sys.argv = ['binprint', '--', '-i']; main(sys)
    00101101 01101001
    \ 2d - / \ 69 i /
    """
    got_dashdash = False
    data = ''
    flags = ''
    for arg in sys.argv[1:]:
        if arg.startswith('-') and not got_dashdash:
            if arg == '--':
                got_dashdash = True
            for opt in arg[1:]:
                flags += opt
        else:
            if data != '':
                data += ' '
            data += arg
    if not data:
        sixx.make_streams_binary(sys)
        data = sys.stdin.read()
    else:
        data = data.encode('utf8')
    binprint(data, flags)

def binprint(data, flags=''):
    """
    Print binary presentation of data.

    The flags argument controls the output mode:
      * 'i' in flags: Invert bits of every byte
      * 'n' in flags: No space between bytes
      * 'r' in flags: Reverse bytes
      * 'w' in flags: Wide output, 1000000 bytes per line

    >>> binprint(b'hello')
    01101000 01100101 01101100 01101100 01101111
    \ 68 h / \ 65 e / \ 6c l / \ 6c l / \ 6f o /
    >>> binprint(b'hello', 'i')
    00010110 10100110 00110110 00110110 11110110
    \ 68 h / \ 65 e / \ 6c l / \ 6c l / \ 6f o /
    >>> binprint(b'xy', 'r')
    01111001 01111000
    \ 79 y / \ 78 x /
    >>> binprint(b'xy', 'n')
    0111100001111001
    \ 78 x /\ 79 y /
    """
    data = bytes2ints(data)
    to_bits = to_bin
    sep = ' '
    bytes_per_line = 12
    if 'i' in flags:
        to_bits = to_bin_inverted
    if 'n' in flags:
        sep = ''
    if 'r' in flags:
        data = list(reversed(data))
    if 'w' in flags:
        bytes_per_line = 1000000
    length = len(data)
    for i in xrange((length // bytes_per_line) + 1):
        start = i * bytes_per_line
        stop = min(start + bytes_per_line, length)
        if i != 0:
            print('')
        print(
            sep.join(
                to_bits(x)
                for x in data[start:stop]))
        print(
            sep.join(
                to_printable8(x)
                for x in data[start:stop]))

if __name__ == '__main__':
    import sys
    main(sys)

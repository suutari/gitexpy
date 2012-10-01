from .chrconvert import to_bin_inverted
from .outputwindow import OutputWindow
from .sixx import byte2int

class EndOfStreamError(Exception):
    """End Of Stream Error"""

class BitString(object):
    def __init__(self, in_stream):
        self.winsize = 8 * 4096
        self.window = OutputWindow(self.winsize)
        self.in_stream = in_stream
        self.offset = 0
        self.readbits = 0
    def startswith(self, x):
        self.__ensure_has(len(x))
        return self.window[self.offset:self.offset + len(x)] == x.encode('ascii')
    def discard(self, n):
        self.offset += n
    def peek(self, n):
        self.__ensure_has(n)
        return ''.join(chr(x) for x in self.window[self.offset:self.offset + n])
    def take(self, n):
        ret = ''.join(reversed(self.peek(n)))
        self.discard(n)
        return ret
    def has_n_bits_left(self, n):
        try:
            self.__ensure_has(n)
            return True
        except EndOfStreamError:
            return False
    def __ensure_has(self, n):
        """Ensure that at least n bits are available from current offset."""
        if n <= self.readbits - self.offset:
            return
        bits_to_read = self.winsize // 2
        for b in self.in_stream.read(bits_to_read // 8):
            bits = to_bin_inverted(byte2int(b))
            self.window.append_bytes(bits.encode('ascii'))
            self.readbits += len(bits)
        if n >= self.readbits - self.offset:
            raise EndOfStreamError('Unexpected end of stream')

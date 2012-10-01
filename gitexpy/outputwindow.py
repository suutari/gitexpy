from .errors import *
from .sixx import int2byte

class OutputWindow(object):
    def __init__(self, max_size):
        self.arr = bytearray(max_size)
        self.sz = 0
        self.p = 0
        self.max_size = max_size
    def append_byte(self, x):
        self.arr[self.p] = x
        self.sz += 1
        self.p = (self.p + 1) % self.max_size
    def append_byte_from(self, i):
        #todo_error_handling(i < self.sz - self.max_size)
        #todo_error_handling(i >= self.sz)
        shifted_i = (self.p + i - self.sz) % self.max_size
        self.arr[self.p] = self.arr[shifted_i]
        self.sz += 1
        self.p = (self.p + 1) % self.max_size
    def append_bytes(self, x):
        for c in x:
            self.append_byte(c)
    def __len__(self):
        return self.sz
    def __getitem__(self, key):
        def shifted(i):
            return (self.p + i - self.sz) % self.max_size
        try:
            start = key.start if key.start is not None else 0
            stop = key.stop if key.stop is not None else self.sz
            step = key.step
        except AttributeError:
            if (key < self.sz - self.max_size) or (key >= self.sz):
                raise Error(
                    'Key out of range (key=%d, valid range=[%d,%d])' %
                    (key, self.sz - self.max_size, self.sz - 1))
            shifted_i = shifted(key)
            assert shifted_i >= 0
            assert shifted_i < self.max_size
            return int2byte(self.arr[shifted_i])[0]
        length = stop - start
        if length > self.max_size:
            raise Error(
                'Length too large (length=%d, max=%d)' %
                (length, self.max_size))
        return self.last_n(self.sz - start)[0:length:step]
    def last_n(self, n):
        if n > min(self.sz, self.max_size):
            raise Error(
                'n too large (n=%d, max=%d)' %
                (n, min(self.sz, self.max_size)))
        start = self.p - n
        if start < 0:
            return self.arr[self.max_size + start:] + self.arr[:self.p]
        else:
            assert start + n <= self.max_size
            return self.arr[start:self.p]

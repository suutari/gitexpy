import operator

from six.moves import reduce

from . import git_delta
from .binarypolynomial import BinaryPolynomial
from .randompolynomial import random_irreducible_polynomial
from .sixx import byte2int

SHIFT_AMOUNT = git_delta.POLYNOMIAL_DEGREE - 8
WINDOW_SIZE = git_delta.WINDOW_SIZE

class Rabin(object):
    """
    Rabin fingerprint generator.

    >>> r31_16 = Rabin(degree=31, window_size=16)
    >>> data16 = b'1234567890123456'
    >>> fp = r31_16.fingerprint(data16)
    >>> assert fp in r31_16.fingerprints(b'x' + data16 + b'y')
    >>> len(list(r31_16.fingerprints(b'xyz')))
    3
    >>> len(list(r31_16.fingerprints(data16 + data16)))
    32
    >>> assert all(
    ...     0 <= fp < 2**31
    ...     for fp in r31_16.fingerprints(b'x' + data16 + b'y'))
    >>> r = Rabin(degree=31, polynomial=0xab59b4d1, window_size=16)
    >>> assert r.fingerprint(data16) == 254454016
    >>> assert list(r.fingerprints(data16 + data16)) == [
    ...             49,      12594,    3224115,  825373492,
    ...      915216495, 2114795168,  556963157,  131089866,
    ...      669958133, 2061695404, 1775952552,  817288244,
    ...     1333839130,   52869085, 1983632130,  254454016,
    ...     1853827091,  881391686,  435164733, 1961967486,
    ...      181860145, 1469847685,  812671538, 2127377651,
    ...      615955722, 1086911299,  264685306, 2144334612,
    ...     2050986543, 1340319929,   37610922,  254454016]
    """
    def __init__(self, degree=None, window_size=16, polynomial=None, bits=None):
        self.degree = degree
        self.window_size = window_size
        if not polynomial:
            if not self.degree:
                self.degree = 31
            self.polynomial = random_irreducible_polynomial(self.degree)
        else:
            try:
                self.polynomial = BinaryPolynomial.from_int(int(polynomial))
            except TypeError:
                self.polynomial = polynomial
            self.degree = self.polynomial.degree
        assert self.degree == self.polynomial.degree
        self.shift_amount = self.degree - 8
        self.bits = bits if bits else bits_for_degree(self.degree)
        assert self.bits >= self.degree
        self.mask = 2**self.bits - 1
        (self.T, self.U) = generate_rabin_tables(
            self.polynomial, self.window_size, self.bits)
        self.minvalue = 0
        self.maxvalue = 2**self.degree - 1
    def __repr__(self):
        return '{c}(polynomial=0x{p:x}, window_size={w}, bits={b})'.format(
            c=self.__class__.__name__,
            p=self.polynomial.to_int(), w=self.window_size, b=self.bits)
    def fingerprints(self, data):
        return iterate_fingerprints(
            data, self.T, self.U,
            self.window_size, self.shift_amount, self.mask)
    def fingerprint(self, data):
        return fingerprint(data, self.T, self.shift_amount, self.mask)
    def debug_fingerprints(self, data):
        for (i, fp) in enumerate(self.fingerprints(data)):
            print(
                '{i:2d}{x} {c}={ci:02x}={ci:08b} {fp:0{w}b} {fp:x}'.format(
                    i=i, x=('_' if (i + 1) % self.window_size == 0 else ' '),
                    c=data[i], ci=byte2int(data[i]), fp=fp, w=self.bits))

def bits_for_degree(degree):
    bits = 8
    while bits < degree:
        bits *= 2
    return bits

def iterate_fingerprints(
    data,
    T=git_delta.T, U=git_delta.U,
    window_size=WINDOW_SIZE, shift_amount=SHIFT_AMOUNT,
    mask=0xffffffff):
    window = bytearray(window_size * b'\0')
    assert len(window) == window_size
    assert all(U[window[i]] == 0 for i in range(window_size))
    window_ptr = 0
    fp = 0
    for x in data:
        fp ^= U[window[window_ptr]]
        window[window_ptr] = x
        window_ptr = (window_ptr + 1) % window_size
        fp = (((fp<<8) | byte2int(x)) & mask) ^ T[fp>>shift_amount]
        yield fp

def fingerprint(
    data,
    T=git_delta.T,
    shift_amount=SHIFT_AMOUNT, mask=0xffffffff):
    fp = 0
    for x in data:
        fp = (((fp<<8) | byte2int(x)) & mask) ^ T[fp>>shift_amount]
    return fp

def generate_rabin_tables(polynomial, window_size, bits, bw=8):
    """
    Generate tables T and U for Rabin fingerprinting.

    Here is an example how the T table is used:

    Assume that bits = 16, polynomial degree = 13 and bw = 8.
    Then shift = degree-bw = 5 and mask = 2**bits-1 = 65535 =
    0b1111111111111111.

    Entries in T will have their bits-degree = 3 highest bits set as
    follows:
      T[*****001] = 001***** ********
      T[*****010] = 010***** ********
      T[*****100] = 100***** ********
    and in general
      T[*****xyz] = xyz***** ********.

    The fingerprinting algorithm is:
      for x in data:
          fp = (((fp<<bw) | byte2int(x)) & mask) ^ T[fp>>shift]

    In the algorithm the pointer to T, i.e. fp>>shift, should be in
    0...2**bw-1 range and therefore every fp value should have its 3
    highest bits set to zero. The 16 bit fp value can be divided as
    follows:
               ptr to T
              /-------\
      fp = 000***** ********
                       \___/ these 5 bits will be shifted out

    Let's follow the algorithm for the input data
      xyz***** abc***** def*****.
    Initially
      fp = 00000000 00000000.
    Shift a byte in and xor with T[00000000] = 00000000 00000000. Then
      fp = 00000000 xyz*****.
    Shift a byte in and xor with T[00000xyz] = xyz***** ghi*****. Then
      fp = 000***** ABC*****, where ABC = abc ^ ghi.
    Shift a byte in and xor with T[*****ABC] = ABC***** jkl*****. Then
      fp = 000***** DEF*****, where DEF = def ^ jkl.
    And so on.
    """
    #assert polynomial.is_irreducible()
    assert bits >= polynomial.degree
    assert bw <= polynomial.degree
    x = BinaryPolynomial.from_str('x')
    # First we need the values of the powers of two
    T_lookup = {
        2**i: pow(x, polynomial.degree + i, polynomial).to_int()
        for i in range(bw)}
    U_lookup = {
        2**i: pow(x, bw * (window_size - 1) + i, polynomial).to_int()
        for i in range(bw)}
    # Now set the H = min(bits-polynomial.degree,bw) highest bits of
    # T_lookup[2**i] to match the H lowest bits of 2**i for all
    # i=0...H-1. This is needed to keep the H highest bits zero in the
    # fingreprint values (without using an extra and mask operation).
    #
    # All the high bits that we are about to set should be zero
    # initially, since all T values are polynomials modulo polynomial,
    # so only polynomial.degree lowest bits should be set.
    assert all(
        T_lookup[2**i] & 2**(polynomial.degree + i) == 0
        for i in range(min(bits - polynomial.degree, bw)))
    # Now set the high bits
    for i in range(min(bits - polynomial.degree, bw)):
        T_lookup[2**i] |= 2**(polynomial.degree + i)
    # Now generate the tables by xorring the lookup entries
    T = [combine_val(T_lookup, i) for i in range(2**bw)]
    U = [combine_val(U_lookup, i) for i in range(2**bw)]
    return (T, U)

def combine_val(lookup_table, index):
    """
    Combine value for given index from the lookup_table.

    >>> lookup = {1: 0x001, 2: 0x010, 4: 0x100}
    >>> assert combine_val(lookup, 5) == lookup[4] ^ lookup[1] == 0x101
    >>> assert combine_val(lookup, 6) == lookup[4] ^ lookup[2] == 0x110
    >>> assert combine_val(lookup, 0) == 0
    """
    return reduce(
        operator.xor,
        (lookup_table[2**i] for i in twopowers(index)),
        0)

def twopowers(n):
    """
    Get powers of two which compose n.

    For any integer n return a list of integer exponents e1, ..., eK
    such that n = 2**e1 + ... + 2**eK and e1 < ... < eK.

    >>> assert twopowers(19) == [0, 1, 4]
    >>> assert sum(2**e for e in twopowers(55)) == 55
    >>> assert twopowers(0) == []
    >>> assert twopowers(1) == [0]
    >>> assert twopowers(128) == [7]
    >>> assert twopowers(2**31+5) == [0, 2, 31]
    >>> assert twopowers(2**123+2**45+2**6) == [6, 45, 123]
    """
    return [e for (e,k) in enumerate(reversed('{:b}'.format(n))) if k == '1']

from .primes import prime_divisors

class BinaryPolynomial(object):
    """
    Polynomial in Z_2[x].

    >>> p = BinaryPolynomial(1,0,0,0,1,1)
    >>> q = BinaryPolynomial(1,0)
    >>> r = BinaryPolynomial(1,1,0,0)
    >>> z = BinaryPolynomial(0)
    >>> o = BinaryPolynomial(1)
    >>> str(p)
    'x^5 + x + 1'
    >>> str(q)
    'x'
    >>> str(r)
    'x^3 + x^2'
    >>> str(z)
    '0'
    >>> bool(p)
    True
    >>> bool(z)
    False
    >>> assert p != z
    >>> assert z == 0
    >>> assert o == 1
    >>> assert p != 0
    >>> assert p != 1
    >>> assert p != q
    >>> assert not (p == q)
    >>> assert q != 1
    >>> assert not (q == 1)
    >>> p * z
    BinaryPolynomial(0)
    >>> assert p * o == p
    >>> assert o * p == p
    >>> assert o * o == o
    >>> assert p * 0 == 0
    >>> assert p * 1 == p
    >>> assert 0 * p == 0
    >>> assert 1 * p == p
    >>> print(p * q)
    x^6 + x^2 + x
    >>> print(p * r)
    x^8 + x^7 + x^4 + x^2
    >>> assert BinaryPolynomial.from_str(str(p)) == p
    >>> assert BinaryPolynomial.from_str(str(q)) == q
    >>> assert BinaryPolynomial.from_str(str(r)) == r
    >>> assert BinaryPolynomial.from_str(str(z)) == z
    >>> assert p + p == 0
    >>> assert q + q == 0
    >>> assert p + 0 == p
    >>> assert 0 + q == q
    >>> assert o + 1 == z
    >>> p + q
    BinaryPolynomial(1,0,0,0,0,1)
    >>> p + r
    BinaryPolynomial(1,0,1,1,1,1)
    >>> print(BinaryPolynomial.from_str('x^55') + 1)
    x^55 + 1
    >>> p.to_int()
    35
    >>> print(BinaryPolynomial.from_int(42))
    x^5 + x^3 + x
    >>> print(p % r)
    x^2 + x + 1
    >>> print((p * r) % r)
    0
    >>> print((p * r + 1) % r)
    1
    >>> x = BinaryPolynomial.from_str('x')
    >>> print(x**17 + x**4 + x**3 + x + 1)
    x^17 + x^4 + x^3 + x + 1
    >>> print((p * r + x**2 + 1) % r)
    x^2 + 1
    >>> assert p % 1 == 0
    >>> assert q % 1 == 0
    >>> p % z
    Traceback (most recent call last):
      ...
    ZeroDivisionError: BinaryPolynomial modulo by zero
    >>> assert (p * q) // q == p
    >>> assert (p * r) // r == p
    >>> assert (p * q) // p == q
    >>> assert (p * r) // p == r
    >>> assert p // 1 == p
    >>> assert q // 1 == q
    >>> assert q // p == 0
    >>> p // z
    Traceback (most recent call last):
      ...
    ZeroDivisionError: BinaryPolynomial division by zero
    """
    def __new__(cls, *factors, **kwargs):
        inst = object.__new__(cls)
        if 'val' in kwargs:
            inst.val = kwargs['val']
        elif factors:
            try:
                inst.val = factors[0].val
            except AttributeError:
                factors = list(factors)
                assert all(a in (0, 1) for a in factors)
                inst.val = sum(
                    (f * (2**k)
                     for (k, f) in enumerate(reversed(factors))),
                    0)
        else:
            inst.val = 0
        return inst
    @property
    def degree(self):
        return len(bin(self.val)) - 3
    def __str__(self):
        lst = []
        for (i, a) in enumerate(bin(self.val)[2:]):
            if a == '0':
                continue
            k = self.degree - i
            if k == 0:
                lst.append('1')
            elif k == 1:
                lst.append('x')
            else:
                lst.append('x^%d' % k)
        if lst:
            return ' + '.join(lst)
        else:
            return '0'
    @classmethod
    def from_str(cls, s):
        factormap = {}
        for factorstr in s.replace(' ', '').split('+'):
            if factorstr == '0':
                continue
            elif factorstr == '1':
                exp = 0
            elif factorstr == 'x':
                exp = 1
            else:
                assert factorstr.startswith('x^')
                exp = int(factorstr.split('^', 1)[1])
            factormap[exp] = (factormap.get(exp, 0) + 1) % 2
        if not factormap:
            return BinaryPolynomial.from_int(0)
        res = []
        for i in range(max(factormap.keys()) + 1):
            res.append(factormap.get(i, 0))
        return BinaryPolynomial(*reversed(res))
    @classmethod
    def from_int(cls, n):
        bp = object.__new__(cls)
        bp.val = n
        return bp
    def to_int(self):
        return self.val
    def __bool__(self):
        return self.val != 0
    def __nonzero__(self):
        return self.__bool__()
    def __eq__(self, other):
        try:
            other_val = other.val
        except AttributeError:
            other_val = other
        return self.val == other_val
    def __ne__(self, other):
        return not(self == other)
    def __int__(self):
        return self.val
    def __mul__(self, other):
        row = int(other)
        res = 0
        s = self.val
        while s:
            if s % 2:
                res ^= row
            row <<= 1
            s //= 2
        return BinaryPolynomial.from_int(res)
    def __rmul__(self, other):
        return self.__mul__(other)
    def __add__(self, other):
        return BinaryPolynomial.from_int(self.val ^ int(other))
    def __pow__(self, e, mod=None):
        self_mod = self % mod if mod else self
        r = BinaryPolynomial.from_int(1)
        if e > 0:
            for b in '{:b}'.format(e):
                r *= r
                if b == '1':
                    r *= self_mod
                if mod:
                    r %= mod
        return r
    def __neg__(self):
        return self
    def __sub__(self, other):
        return self + other
    def __rsub__(self, other):
        return self + other
    def __radd__(self, other):
        return self.__add__(other)
    def __floordiv__(self, other):
        if not other:
            raise ZeroDivisionError('BinaryPolynomial division by zero')
        div = int(other)
        if div == 1:
            return self
        len_bin_div = len(bin(div))
        left = self.val
        res = 0
        while left != 0 and len(bin(left)) >= len_bin_div:
            shift = (len(bin(left)) - len_bin_div)
            res ^= 2**shift
            left ^= (div << shift)
        return BinaryPolynomial.from_int(res)
    def __mod__(self, other):
        if not other:
            raise ZeroDivisionError('BinaryPolynomial modulo by zero')
        div = int(other)
        if div == 1:
            return BinaryPolynomial.from_int(0)
        len_bin_div = len(bin(div))
        res = self.val
        while res != 0 and len(bin(res)) >= len_bin_div:
            res ^= (div << (len(bin(res)) - len_bin_div))
        return BinaryPolynomial.from_int(res)
    def is_irreducible(self):
        if self.val <= 1:
            return False
        if self.val <= 3:
            return True
        if pow(x, 2**self.degree, self) - x:
            return False
        for primediv in prime_divisors(self.degree):
            m = self.degree//primediv
            # Note: By Eucledian algorithm:
            # gcd(pow(x,2**m)-x, self) == gcd(self, (pow(x,2**m)-x) % self)
            #  == gcd(self, (pow(x,2**m,self)-x) % self)
            if self.gcd_with((pow(x,2**m,self)-x) % self) != 1:
                return False
        return True
    def gcd_with(self, other):
        if other == 0:
            return self
        else:
            return other.gcd_with(self % other)
    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ','.join(a for a in bin(self.val)[2:]))

def from_one(lst):
    """
    Return elements of list starting from first element that is 1.

    >>> from_one([0,0,1,0,1,1])
    [1, 0, 1, 1]
    >>> from_one([0,0])
    []
    >>> from_one(['a','b',1,'c'])
    [1, 'c']
    """
    if 1 not in lst:
        return []
    return lst[lst.index(1):]

x = BinaryPolynomial.from_str('x')

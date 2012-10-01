from .binarypolynomial import BinaryPolynomial
from .memoize import memoized

class IrreduciblePolynomials:
    """
    Iterator for all irreducible binary polynomials to some point.

    Generates irreducible polynomials with Sieve of Eratosthenes.

    >>> list(IrreduciblePolynomials(90))
    [2, 3, 7, 11, 13, 19, 25, 31, 37, 41, 47, 55, 59, 61, 67, 73, 87]

    >>> ips = set(IrreduciblePolynomials(2**12))
    >>> for q in ips:
    ...     assert BinaryPolynomial.from_int(q).is_irreducible()
    >>> (min(ips), max(ips), len(ips), sum(ips))
    (2, 4091, 412, 784361)
    >>> for i in range(2**12):
    ...     is_irreducible = BinaryPolynomial.from_int(i).is_irreducible()
    ...     assert (i in ips) == is_irreducible
    >>> sum(IrreduciblePolynomials(2**14))
    10603804
    """
    def __init__(self, polynomial):
        try:
            self.n = polynomial.to_int()
        except AttributeError:
            self.n = int(polynomial)
    def __iter__(self):
        if self.n <= 2:
            return
        p = 2
        yield p
        numbers_left = set(range(3, self.n, 2))
        n_ceil = 2**(len(bin(self.n))-2)
        while numbers_left and p * p <= n_ceil:
            p = min(numbers_left)
            yield p
            # Remove all (k*p) from numbers_left, where k iterates
            # over all odd polynomials (1, x+1, x^2+1, x^2+x+1, ...)
            k = 1
            while k:
                # Calculate polynomial multiplication k*p to res
                res = p
                row = p << 1
                s = k // 2
                while s:
                    if s % 2:
                        res ^= row
                    row <<= 1
                    s //= 2
                numbers_left.discard(res)
                k += 2
                if len(bin(res)) > len(bin(self.n)):
                    k = 0
        for q in sorted(numbers_left):
            yield q

@memoized
def irreducible_polynomials_under_degree(n):
    return list(IrreduciblePolynomials(2**(n+1)))

def factorize_polynomial(p):
    """
    Factorize binary polynomial p to irreducible factors.

    For example:
    >>> x = BinaryPolynomial.from_str('x')
    >>> p1 = BinaryPolynomial.from_str('x+1')
    >>> p2 = BinaryPolynomial.from_str('x^2+x+1')
    >>> p3 = BinaryPolynomial.from_str('x^3+x^2+1')
    >>> assert factorize_polynomial(x*p1*p2*p3) == [x, p1, p2, p3]
    """
    if p.is_irreducible():
        return [p]
    tried = set()
    for degree in (5, 10, 12, 15, 16, 17, 18, 19, 20):
        for qint in irreducible_polynomials_under_degree(degree):
            if qint in tried:
                continue
            tried.add(qint)
            q = BinaryPolynomial.from_int(qint)
            if p % q == 0:
                return [q] + factorize_polynomial(p // q)
    raise Exception('Polynomial %s too big to factorize.' % p)

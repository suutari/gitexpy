from six.moves import xrange

class Primes:
    """
    Iterator for all prime numbers smaller than a specified value.

    Generates primes with Sieve of Eratosthenes.

    >>> list(Primes(60))
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
    """
    def __init__(self, n):
        """
        All primes smaller than n.
        """
        self.n = n
    def __iter__(self):
        # Use Sieve of Eratosthenes to get the primes
        if self.n <= 2:
            return
        p = 2
        yield p
        numbers_left = set(xrange(3, self.n, 2))
        while p**2 <= self.n:
            p = min(numbers_left)
            yield p
            for k in xrange(p, self.n, p * 2):
                numbers_left.discard(k)
        for q in sorted(numbers_left):
            yield q

def prime_divisors(n):
    """
    Get prime divisors of n.

    >>> prime_divisors(3*7*7*13*61)
    [3, 7, 13, 61]
    """
    m = int(n)
    divs = set()
    pdivs = set()
    while m % 2 == 0:
        pdivs.add(2)
        m //= 2
    div = 3
    while div <= n and m != 1:
        if is_probable_prime(div):
            while m % div == 0:
                divs.add(div)
                m //= div
        div += 2
    for d in divs:
        for p in Primes(d + 1):
            if n % p == 0:
                pdivs.add(p)
    return sorted(pdivs)

def is_probable_prime(n):
    """
    Test if n is probable prime with Fermat's test for compositeness.
    """
    if n <= 1 or n % 2 == 0:
        return n == 2
    return pow(2, n - 1, n) == 1

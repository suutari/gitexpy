import random

from .binarypolynomial import BinaryPolynomial

def random_irreducible_polynomial(degree):
    f = find_irreducible_polynomial(degree)
    # FIXME: Implement a bit more randomness here
    return f

def find_irreducible_polynomial(degree):
    while True:
        randval = 2 * random.randint(2**(degree-1), 2**degree - 1) + 1
        q = BinaryPolynomial.from_int(randval)
        if not q.is_irreducible():
            continue
        return q


from .binarypolynomial import BinaryPolynomial
from .randompolynomial import random_irreducible_polynomial

p = BinaryPolynomial(1,1,1)
nip = p * p

assert p.is_irreducible()
assert not nip.is_irreducible()
nip = random_irreducible_polynomial(4)
degree = nip.degree

symbols = '01abcdefghijklmn'
elems = {
    symbols[i]: BinaryPolynomial.from_int(i) % nip
    for i in range(2**degree)
}
revelems = {y.to_int(): x for (x, y) in elems.items()}



print('')
print('\n'.join('%s: %s' % (s,elems[s]) for s in sorted(elems)))

print('   ' + ' '.join('%2s' % s for s in sorted(elems)))
for s1 in sorted(elems):
    row = '%2s ' % s1
    row += ' '.join('%2s' % revelems[((elems[s1] * elems[s2]) % nip).to_int()] for s2 in sorted(elems))
    print(row)

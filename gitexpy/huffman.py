import math
from collections import defaultdict
from six.moves import xrange

def is_leaf(x):
    try:
        return x.left_child is None and x.right_child is None
    except:
        return True

class Node(object):
    def __init__(self):
        self.left_child = None
        self.right_child = None
    def __hash__(self):
        return hash((self.left_child, self.right_child))

def dict_union(x, y):
    result = dict(x)
    result.update(y)
    return result

def make_huffman_codemap(symbols, freqs):
    rootnode = make_huffman_tree(symbols, freqs)
    return nodes_to_codemap(rootnode)

def make_huffman_tree(symbols, freqs):
    assert len(symbols) >= 2
    nodes = list(symbols)
    freqs = dict(freqs)
    while len(nodes) >= 2:
        nodes.sort(key=lambda x: freqs[x])
        n1 = nodes[0]
        n2 = nodes[1]
        newnode = Node()
        newnode.left_child = n1
        newnode.right_child = n2
        freqs[newnode] = freqs[n1] + freqs[n2]
        nodes = [newnode] + nodes[2:]
    assert len(nodes) == 1
    return nodes[0]

def nodes_to_codemap(node, prefix=''):
    if is_leaf(node):
        symbol = node # leaf nodes are the symbols
        return {symbol: prefix}
    else:
        left = nodes_to_codemap(node.left_child, prefix + '0')
        right = nodes_to_codemap(node.right_child, prefix + '1')
        return dict_union(left, right)

def print_codemap(codemap):
    for (sym, c) in codemap.items():
        print('%s\t%s' % (sym, c))

def count_symbol_frequencies(string):
    freqs = defaultdict(int)
    symbols = set()
    for c in string:
        freqs[c] +=1
        symbols.add(c)
    return (symbols, freqs)

def unordered_pairs(iterable):
    lst = list(iterable)
    for (i, x) in enumerate(lst):
        for j in xrange(i + 1, len(lst)):
            yield (x, lst[j])

def is_prefix_codemap(codemap):
    return is_prefix_code(codemap.values())

def is_prefix_code(code):
    """
    Test if given code is a prefix code.

    >>> is_prefix_code(['a', 'b', 'ca'])
    True
    >>> is_prefix_code(['ab', 'a'])
    False
    >>> is_prefix_code(['a'])
    True
    >>> is_prefix_code([])
    False
    """
    if not code:
        return False # Empty set is not a prefix code
    codewords = code
    for (c1, c2) in unordered_pairs(codewords):
        if c1.startswith(c2) or c2.startswith(c1):
            return False
    return True

def encode_with_codemap(string, codemap):
    return ''.join(codemap[c] for c in string)

def decode_with_codemap(string, codemap, align=False):
    left = string
    decoded = ''
    while left:
        for (sym, codeword) in codemap.items():
            if left.startswith(codeword):
                if align:
                    decoded += (len(codeword) - 1) * '`'
                decoded += sym
                left = left[len(codeword):]
                break
    return decoded

def entropy(symbol_frequencies):
    totalfreq = float(sum(symbol_frequencies.values()))
    s = 0.0
    for freq in symbol_frequencies.values():
        prob = freq / totalfreq
        s += - prob * math.log(prob, 2)
    return s

def lambda_of_codemap(symbol_frequencies, codemap):
    totalfreq = float(sum(symbol_frequencies.values()))
    s = 0.0
    for (sym, freq) in symbol_frequencies.items():
        prob = freq / totalfreq
        s += prob * len(codemap[sym])
    return s

def normalize_codemap(codemap):
    x = list(sorted(codemap.keys()))
    lengths = [len(codemap[xi]) for xi in x]
    result = {x[i]: c for (i,c) in enumerate(normalized_huffman_code(lengths))}
    assert is_normalized_codemap(result)
    assert all(len(codemap[k]) == len(result[k]) for k in x)
    return result

def is_normalized_codemap(codemap):
    """
    Check that given codemap is normalized.

    Example of normalized codemap:
    >>> is_normalized_codemap({0: 'a', 1: 'ba', 2: 'bb'})
    True

    For normalized codemap, (i) the code should be a prefix code:
    >>> is_normalized_codemap({0: 'a', 1: 'ab'})
    False

    (ii) shorter codewords should be before longer codewords in
    lexicographical order:
    >>> is_normalized_codemap({0: 'aa', 1: 'b', 2: 'c'})
    False

    and (iii) if two symbols have codeword of same length, then the
    smaller symbol should have a codeword that is before the codeword
    of the other symbol in lexicographical order:
    >>> is_normalized_codemap({0: 'b', 1: 'a'})
    False
    """
    if not is_prefix_codemap(codemap):
        return False # (i) fails
    for (x1, cw1) in codemap.items():
        for (x2, cw2) in codemap.items():
            if len(cw1) < len (cw2):
                if cw1 > cw2:
                    return False # (ii) fails
            elif len(cw1) == len(cw2):
                if x1 < x2:
                    if cw1 > cw2:
                        return False # (iii) fails
    return True

def normalized_huffman_code(lengths):
    def binary(x, n):
        if n == 0:
            return ''
        return '{x:0{n}b}'.format(x=x, n=n)
    n = len(lengths)
    def l(i):
        return lengths[i-1]
    def c(k):
        return sum(1 for i in range(1, n+1) if l(i) == k)
    def f(l):
        return sum(2**(l-i)*c(i) for i in range(1, l))
    assert f(0) == 0
    assert f(1) == 0
    assert f(2) == 2 * c(1)
    def s(k):
        return sum(1 for i in range(1, k) if l(i) == l(k))
    assert s(0) == 0
    assert s(1) == 0
    def t(i):
        return f(l(i)) + s(i)
    def phi(i):
        return binary(t(i), l(i))
    return tuple(phi(i) for i in range(1,n+1))

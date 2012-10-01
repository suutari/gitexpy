import gc
import random
import sys
import time
from collections import defaultdict
from six.moves import reduce, xrange
from . import randomstring
from .randomstring import randomstringpair
from .memoize import memoized

class Array(object):
    def __init__(self, n, m):
        self.t = []
        for i in xrange(n):
            r = []
            for j in xrange(m):
                r.append(None)
            self.t.append(r)
    def __getitem__(self, k):
        (i, j) = k
        return self.t[i][j]
    def __setitem__(self, k, val):
        (i, j) = k
        self.t[i][j] = val
    def __str__(self, valfmt='{:>11}'):
        return '\n'.join(
            ' '.join(valfmt.format(x) for x in row)
            for row in self.t)

def lcs_r(a, b):
    """
    Calculate LCS of a and b, recursively.

    Return longest possible tuple of pairs ((i1,j1),...,(ik,jk)) such
    that a[i1]==b[i1],...,a[ik]==b[ik].

    >>> lcs_r('abc','axc')
    ((0, 0), (2, 2))
    >>> lcs_r('aakkosto', 'pakkaus')
    ((1, 1), (2, 2), (3, 3), (5, 6))
    """
    if len(a) == 0 or len(b) == 0:
        return ()
    if a[-1] == b[-1]:
        return lcs_r(a[:-1], b[:-1]) + ((len(a)-1,len(b)-1),)
    else:
        lcs1 = lcs_r(a[:-1], b)
        lcs2 = lcs_r(a, b[:-1])
        if len(lcs1) >= len(lcs2):
            return lcs1
        else:
            return lcs2

def lcs_d1(a, b):
    """
    Calculate LCS of a and b, with dynamic programming.

    Stores the index tuples of the LCSs into table.

    Returns same as lcs_r.
    """
    t = Array(len(a) + 1, len(b) + 1)
    for i in xrange(len(a)+1):
        t[i,0] = ()
    for j in xrange(len(b)+1):
        t[0,j] = ()
    for i in xrange(len(a)):
        for j in xrange(len(b)):
            if a[i] == b[j]:
                t[i+1,j+1] = t[i,j] + ((i,j),)
            else:
                x = t[i,j+1]
                y = t[i+1,j]
                if len(x) >= len(y):
                    t[i+1,j+1] = x
                else:
                    t[i+1,j+1] = y
    return t[len(a),len(b)]


def lcs_d2(a, b):
    """
    Calculate LCS of a and b, with dynamic programming and less space
    than lcs_d1.

    Stores only the lengths of the LCSs into table.

    Returns same as lcs_r.
    """
    t = Array(len(a) + 1, len(b) + 1)
    for i in xrange(len(a)+1):
        t[i,0] = 0
    for j in xrange(len(b)+1):
        t[0,j] = 0
    for i in xrange(len(a)):
        for j in xrange(len(b)):
            if a[i] == b[j]:
                t[i+1,j+1] = t[i,j] + 1
            else:
                t[i+1,j+1] = max(t[i,j+1], t[i+1,j])
    result = ()
    i = len(a)
    j = len(b)
    while i != 0 and j != 0:
        if a[i-1] == b[j-1]:
            result = ((i-1,j-1),) + result
            i -= 1
            j -= 1
        elif t[i-1,j] >= t[i,j-1]:
            i -= 1
        else:
            j -= 1
    return result


def lcs_d3(a, b):
    """
    Calculate LCS of a and b, with dynamic programming and
    memoization.

    Only calculates those entries of the table that are needed. Fills
    the table by recursion.

    Returns same as lcs_r.
    """
    t = Array(len(a)+1,len(b)+1)
    def get_t(i,j):
        val = t[i,j]
        if val is not None:
            return val
        if i == 0 or j == 0:
            val = 0
        elif a[i-1] == b[j-1]:
            val = get_t(i-1,j-1) + 1
        else:
            val = max(get_t(i-1,j), get_t(i,j-1))
        t[i,j] = val
        return val
    result = ()
    i = len(a)
    j = len(b)
    while i != 0 and j != 0:
        if a[i-1] == b[j-1]:
            result = ((i-1,j-1),) + result
            i -= 1
            j -= 1
        elif get_t(i-1,j) >= get_t(i,j-1):
            i -= 1
        else:
            j -= 1
    return result

def lcs_d4(a, b):
    """
    Calculate LCS of a and b, with dynamic programming and custom stack.

    Only calculates those entries of the table that are needed. Fills
    the table by using local stack.

    Returns same as lcs_r.
    """
    t = Array(len(a)+1,len(b)+1)
    for i in xrange(len(a)+1):
        t[i,0] = 0
    for j in xrange(len(b)+1):
        t[0,j] = 0
    stack = [(len(a),len(b))]
    while stack:
        (i, j) = stack[-1]
        if i > 0 and j > 0 and a[i-1] == b[j-1]:
            dep = t[i-1,j-1]
            if dep is None:
                stack.append((i-1,j-1))
            else:
                t[i,j] = dep + 1
                stack.pop()
        else:
            dep1 = t[i,j-1]
            dep2 = t[i-1,j]
            if dep1 is None:
                stack.append((i,j-1))
            if dep2 is None:
                stack.append((i-1,j))
            elif dep1 is not None:
                # Neither dep1 or dep2 is None
                t[i,j] = max(dep1,dep2)
                stack.pop()
    result = ()
    i = len(a)
    j = len(b)
    while i != 0 and j != 0:
        if a[i-1] == b[j-1]:
            result = ((i-1,j-1),) + result
            i -= 1
            j -= 1
        elif t[i-1,j] >= t[i,j-1]:
            i -= 1
        else:
            j -= 1
    return result

def edit_distance(a, b):
    """
    Calculate edit distance of a and b.

    >>> edit_distance('aaa', 'bb')
    5
    >>> edit_distance('edit_distance', 'editing_dist')
    7
    """
    max_d = len(a) + len(b)
    v = {}
    v[1] = 0
    # Loop invariant:
    #   * For all j in {-d+1,-d+3,...,d-3,d-1}: (v[j],v[j]-j) is the
    #     end of furthest reaching (d-1)-path in diagonal j.
    for d in xrange(max_d+1):
        for k in xrange(-d, d+1, 2):
            # When k is not -d or d: To end up on diagonal k we can
            # extend from x=v[k-1] to right or from x=v[k+1] to
            # down. Choose the one that is farther from origo,
            # i.e. the one that has larger x value.
            #
            # If k is -d then only possibility is to extend down from
            # x=v[k+1] and if k is d then only possibility is to
            # extend right from x=v[k-1].
            if k == -d or (k != d and v[k-1] < v[k+1]):
                x = v[k+1]
            else:
                x = v[k-1] + 1
            y = x - k
            # Now (x,y) is on diagonal k. Extend on diagonal k as far
            # as the strings match.
            while x < len(a) and y < len(b) and a[x] == b[y]:
                (x, y) = (x + 1, y + 1)
            v[k] = x
            # Now (v[k],v[k]-k) is the end of furthest reaching d-path
            # in diagonal k.
            if x == len(a) and y == len(b):
                return d
    raise Exception('Length of LCS(a,b) > %d' % max_d)

def lcs_m1(a, b):
    """
    Calculate LCS of a and b, with Myers algorithm in O(d^2) space.

    >>> lcs_m1('abc','axc')
    ((0, 0), (2, 2))
    >>> lcs_m1('aakkosto', 'pakkaus')
    ((1, 1), (2, 2), (3, 3), (5, 6))
    """
    max_d = len(a) + len(b)
    v = defaultdict(dict)
    v[-1][1] = 0
    v[-1][-1] = -1
    done = False
    for d in xrange(max_d+1):
        for k in xrange(-d, d+1, 2):
            if k == -d or (k != d and v[d-1][k-1] < v[d-1][k+1]):
                x = v[d-1][k+1]
            else:
                x = v[d-1][k-1] + 1
            y = x - k
            while x < len(a) and y < len(b) and a[x] == b[y]:
                (x, y) = (x + 1, y + 1)
            v[d][k] = x
            if x == len(a) and y == len(b):
                done = True
                break
        if done:
            break
    assert k == len(a) - len(b)
    opt_path = []
    while d >= 0:
        opt_path.append((v[d][k], v[d][k]-k))
        if k + 1 > d - 1:
            k -= 1
            d -= 1
            continue
        x = v[d-1][k+1]
        y = x - k
        while x < len(a) and y < len(b) and a[x] == b[y]:
            (x, y) = (x + 1, y + 1)
        if x == v[d][k]:
            k += 1
        else:
            k -= 1
        d -= 1
    opt_path.append((v[d][k], v[d][k]-k))
    opt_path = list(reversed(opt_path))
    result = ()
    for i in xrange(1, len(opt_path)):
        (x1,y1) = opt_path[i-1]
        (x2,y2) = opt_path[i]
        if x1 - y1 == x2 - y2 + 1:
            x = x1
            y = y1 + 1
        else:
            x = x1 + 1
            y = y1
        while x < len(a) and y < len(b) and a[x] == b[y]:
            result = result + ((x, y),)
            (x, y) = (x + 1, y + 1)
        assert (x, y) == (x2, y2)
    return result

def edit_distance_and_middle_snake(a, b):
    fv = {}
    rv = {}
    delta = len(a) - len(b)
    fv[1] = 0
    rv[delta+1] = len(a) + 1
    for d in xrange((len(a)+len(b)+1)//2 + 1):
        for k in xrange(-d, d+1, 2):
            # find the end of furthest reaching forward d-path in diagonal k
            if k == -d or (k != d and fv[k-1] < fv[k+1]):
                fx = fv[k+1]
            else:
                fx = fv[k-1] + 1
            fy = fx - k
            (fx0,fy0) = (fx,fy)
            while fx < len(a) and fy < len(b) and a[fx] == b[fy]:
                (fx, fy) = (fx + 1, fy + 1)
            fv[k] = fx
            if delta % 2 == 1 and k >= delta - (d-1) and k <= delta + (d-1):
                # Test if the path overlaps the furthest reaching
                # reverse (d-1)-path in diagonal k
                if fx >= rv[k]:
                    d = 2 * d - 1
                    middle_snake = (fx0, fy0, fx, fy)
                    return (d, middle_snake)
        for k in xrange(-d, d+1, 2):
            # find the end of furthest reaching reverse d-path in diagonal k+delta
            if k == -d or (k != d and rv[k+delta-1] > rv[k+delta+1] - 1):
                rx = rv[k+delta+1] - 1
            else:
                rx = rv[k+delta-1]
            ry = rx - (k+delta)
            (rx0,ry0) = (rx,ry)
            while rx > 0 and ry > 0 and a[rx-1] == b[ry-1]:
                (rx, ry) = (rx - 1, ry - 1)
            rv[k+delta] = rx
            assert ry == rv[k+delta]-(k+delta)
            if delta % 2 == 0 and k + delta >= -d and k + delta <= d:
                # Test if the path overlaps the furthest reaching
                # forward d-path in diagonal k+delta
                if rx <= fv[k+delta]:
                    d = 2 * d
                    middle_snake = (rx, ry, rx0, ry0)
                    return (d, middle_snake)

def lcs_mg(a, b, apos, bpos):
    if len(a) == 0 or len(b) == 0:
        return
    (d, middle_snake) = edit_distance_and_middle_snake(a, b)
    (x, y, u, v) = middle_snake
    assert x - y == u - v
    assert x <= u
    if d > 1:
        for (i,j) in lcs_mg(a[:x], b[:y], apos, bpos):
            yield (i,j)
        for i in xrange(x, u):
            j = y + i - x
            assert a[i] == b[j]
            yield (i+apos,j+bpos)
        for (i,j) in lcs_mg(a[u:], b[v:], apos+u, bpos+v):
            yield (i,j)
    elif len(a) < len(b):
        i = 0
        while i < len(a) and a[i] == b[i]:
            yield (i+apos,i+bpos)
            i += 1
        while i < len(a):
            assert a[i] == b[i+1]
            yield (i+apos,i+1+bpos)
            i += 1
    else:
        j = 0
        while j < len(b) and a[j] == b[j]:
            yield (j+apos,j+bpos)
            j += 1
        while j < len(b):
            assert a[j+1] == b[j]
            yield (j+1+apos,j+bpos)
            j += 1

def lcs_m(a,b):
    """
    Calculate LCS of a and b, with Myers technique.

    Returns same as lcs_r.

    >>> lcs_m('dbcbcbcac', 'adcadcac')
    ((0, 1), (2, 2), (4, 5), (7, 6), (8, 7))
    """
    return tuple(lcs_mg(a, b, 0, 0))

def lcs_x(a,b):
    """
    Calculate LCS of a and b, with LibXDiff technique.

    LibXDiff technique is essentially the same as the Myers technique,
    but it handles common prefix and suffix specially.

    Returns same as lcs_r.

    >>> lcs_x('dbcbcbcac', 'adcadcac')
    ((0, 1), (2, 2), (6, 5), (7, 6), (8, 7))
    """
    return tuple(lcs_xg(a, b, 0, 0, len(a), len(b)))

def lcs_xg(a, b, apos, bpos, amax, bmax):
    while apos < amax and bpos < bmax and a[apos] == b[bpos]:
        yield (apos,bpos)
        (apos,bpos) = (apos+1,bpos+1)
    t = 0 # length of the tail in which the strings are same
    while amax > apos and bmax > bpos and a[amax-1] == b[bmax-1]:
        (amax,bmax,t) = (amax-1,bmax-1,t+1)
    if apos < amax and bpos < bmax:
        (x_, y_, u_, v_) = middle_snake(a[apos:amax], b[bpos:bmax])
        (x, y, u, v) = (x_+apos, y_+bpos, u_+apos, v_+bpos)
        for (i,j) in lcs_xg(a, b, apos, bpos, x, y):
            yield (i,j)
        for i in xrange(x, u):
            j = y + i - x
            assert a[i] == b[j]
            yield (i,j)
        for (i,j) in lcs_xg(a, b, u, v, amax, bmax):
            yield (i,j)
    for i in xrange(t):
        yield (amax+i, bmax+i)

def middle_snake(a, b):
    v = {} # vector for x values of forward paths
    u = {} # vector for x values of reverse paths
    delta = len(a) - len(b)
    v[1] = 0
    u[delta+1] = len(a) + 1
    for d in xrange((len(a)+len(b)+1)//2 + 1):
        for k in xrange(-d, d+1, 2):
            # find the end of furthest reaching forward d-path in diagonal k
            if k == -d or (k != d and v[k-1] < v[k+1]):
                x = v[k+1]
            else:
                x = v[k-1] + 1
            y = x - k
            (x0,y0) = (x,y)
            while x < len(a) and y < len(b) and a[x] == b[y]:
                (x, y) = (x + 1, y + 1)
            v[k] = x
            if delta % 2 == 1 and k >= delta - (d-1) and k <= delta + (d-1):
                # Test if the path overlaps the furthest reaching
                # reverse (d-1)-path in diagonal k
                if x >= u[k]:
                    return (x0, y0, x, y)
        for k in xrange(-d, d+1, 2):
            # find the end of furthest reaching reverse d-path in diagonal k+delta
            if k == -d or (k != d and u[k+delta-1] > u[k+delta+1] - 1):
                x = u[k+delta+1] - 1
            else:
                x = u[k+delta-1]
            y = x - (k+delta)
            (x0,y0) = (x,y)
            while x > 0 and y > 0 and a[x-1] == b[y-1]:
                (x, y) = (x - 1, y - 1)
            u[k+delta] = x
            if delta % 2 == 0 and k + delta >= -d and k + delta <= d:
                # Test if the path overlaps the furthest reaching
                # forward d-path in diagonal k+delta
                if x <= v[k+delta]:
                    return (x, y, x0, y0)

lcs_best = lcs_d2

class EditScript(object):
    """
    EditScript of two strings.

    Usage example:

    >>> es = EditScript.from_strings('foobar', 'moocowbat')
    >>> sorted(es.delset)
    [0, 5]
    >>> sorted(es.insmap.items())
    [(-1, 'mo'), (1, 'c'), (2, 'w'), (4, 't')]
    >>> es.size()
    7
    >>> es.apply('foobar')
    'moocowbat'
    """
    def __init__(self, delset, insset):
        self.delset = set(delset)
        self.insmap = defaultdict(str)
        self.insmap.update(insset)
    @classmethod
    def from_strings(cls, from_string, to_string):
        lcs = lcs_best(from_string, to_string)
        (delset, insset) = lcs_to_editscript(from_string, to_string, lcs)
        return cls(delset, insset)
    def size(self):
        return len(self.delset) + sum(len(s) for s in self.insmap.values())
    def apply(self, to):
        a = to
        b = self.insmap[-1]
        for i in xrange(len(a)):
            if i not in self.delset:
                b += a[i]
            b += self.insmap[i]
        return b

class Differ(object):
    """
    Difference analyzator of two strings.

    Usage example:
    >>> d = Differ('foobar', 'moocowbat')
    >>> d.a
    'foobar'
    >>> d.b
    'moocowbat'
    >>> d.lcs()
    ((1, 2), (2, 4), (3, 6), (4, 7))
    >>> d.edit_distance()
    7
    >>> d.edit_script().size()
    7
    >>> d.edit_script().apply(d.a) == d.b
    True
    >>> d.print_lcs()
      i  |   0           1       2       3   4   5     |
    ----------------------------------------------------
    a[i] |   f           o       o       b   a   r     |
     LCS |               o       o       b   a         |
    b[j] |       m   o   o   c   o   w   b   a       t |
    ----------------------------------------------------
      j  |       0   1   2   3   4   5   6   7       8 |
    """
    def __init__(self, a, b, lcs_algorithm=lcs_best):
        self.a = a
        self.b = b
        self.lcs_algorithm = lcs_algorithm
    def lcs(self):
        return self.lcs_algorithm(self.a, self.b)
    def edit_distance(self):
        return edit_distance(self.a, self.b)
    def edit_script(self):
        return EditScript.from_strings(self.a, self.b)
    def print_lcs(self):
        print_lcs(self.a, self.b, lcs=self.lcs_algorithm)

def lcs_r_cost(n,m):
    """
    Cost of lcs_r for strings of size n and m in the worst case.

    Counts the number of character comparisons done in lcs_r if called
    with strings of size n and m that do not match at any character.

    Some examples:
    >>> lcs_r_cost(0,42)
    0
    >>> lcs_r_cost(1,1)
    1
    >>> lcs_r_cost(42,1)
    42
    >>> lcs_r_cost(4,6)
    209
    >>> lcs_r_cost(20,20) == 137846528819
    True
    """
    return C(n+m,n) - 1

def C(n, m):
    """
    Calculate binomial coefficient n over m.

    This is the same as number of m-element subsets of n-element set.

    >>> C(5,1)
    5
    >>> C(7,2)
    21
    >>> C(0,0) == C(1,0) == C(0,1) == C(42,0) == 1
    True
    >>> C(0,2) == C(0,3) == C(0,4) == C(0,42) == 0
    True
    """
    return int(factorial(n)//factorial(m)//factorial(n-m))

def factorial(n):
    """
    Calculate n!

    >>> factorial(7) == 1*2*3*4*5*6*7
    True
    >>> factorial(1)
    1
    >>> factorial(0)
    1
    """
    return int(reduce((lambda a,b: a*b), (i for i in xrange(1,n+1)), 1))

def print_lcs(a, b, lcs=lcs_best):
    lcsab = lcs(a, b)
    nexti = 0
    nextj = 0
    rows_iacjb = []
    for (ai, bj) in lcsab:
        for i in xrange(nexti, ai):
            rows_iacjb.append((i, a[i], '', '', ''))
        for j in xrange(nextj, bj):
            rows_iacjb.append(('', '', '', j, b[j]))
        assert a[ai] == b[bj]
        rows_iacjb.append((ai, a[ai], a[ai], bj, b[bj]))
        nexti = ai + 1
        nextj = bj + 1
    for i in xrange(nexti, len(a)):
        rows_iacjb.append((i, a[i], '', '', ''))
    for j in xrange(nextj, len(b)):
        rows_iacjb.append(('', '', '', j, b[j]))
    for (x, label) in ((0,'  i '), (1,'a[i]'), (2, ' LCS'), (4,'b[j]'), (3,'  j ')):
        row = label + ' |'
        for v in rows_iacjb:
            row += ' %3s' % v[x]
        row += ' |'
        print(row)
        if x in (0, 4):
            print(''.join(len(row) * '-'))

def lcs_to_editscript(a, b, lcsab):
    lcs = ((-1,-1),) + lcsab + ((len(a),len(b)),)
    delset = []
    insfunc = []
    for x in xrange(1, len(lcs)):
        (i_px,j_px) = lcs[x-1]
        (i_x,j_x) = lcs[x]
        for i in xrange(i_px+1, i_x):
            delset.append(i)
        if j_px+1 < j_x:
            insfunc.append((i_px, b[j_px+1:j_x]))
        assert (i_x == len(a) and j_x == len(b)) or a[i_x] == b[j_x]
    return (delset, insfunc)

def speed_compare():
    sys.setrecursionlimit(1000000)

    randomstring.seed(59)

    times = defaultdict(list)

    lcslist = [lcs_d1, lcs_d2, lcs_d3, lcs_d4, lcs_m, lcs_x]

    for i in xrange(5):
        (a,b) = randomstringpair(minlen=0, maxlen=500, maxeditdistance=random.randint(0,200))
        nm = len(a)*len(b)
        print('n  = %4d, m = %4d, nm=%8d, d=%3d' % (len(a), len(b), nm, edit_distance(a,b)))
        for lcs in lcslist:
            gc.collect()
            gc.disable()
            t = time.time()
            result = lcs(a, b)
            t = time.time() - t
            gc.enable()
            scaled = 1000000.0 * t / nm
            times[lcs].append(scaled)
            print('%-35s took %12.8f s = %10.8f us * %d' % (lcs, t, scaled, nm))
            if len(result) != cached_lcs_len(a,b) or not is_cs(result, a, b):
                print('a=%s' % repr(a))
                print('b=%s' % repr(b))
            assert is_cs(result, a, b), 'not a common subsequence'
            assert len(result) >= cached_lcs_len(a,b), 'not the longest common subsequence'
            assert len(result) <= cached_lcs_len(a,b), 'longer than longest common subsequence?'
    print
    for lcs in lcslist:
        tl = times[lcs]
        if tl:
            print('%-35s mid=%8.6f, avg=%8.6f, min=%8.6f, max=%8.6f' % (
                lcs, avg(tl), mid(tl), min(tl), max(tl)))

@memoized
def cached_lcs(a,b):
    return lcs_best(a,b)

@memoized
def cached_lcs_len(a,b):
    return len(cached_lcs(a,b))

def is_lcs(x,a,b):
    return len(x) == cached_lcs_len(a,b) and is_cs(x,a,b)

@memoized
def is_cs(x,a,b):
    return all(a[i]==b[j] for (i,j) in x)

def mid(seq):
    return list(sorted(seq))[len(seq)//2]

def avg(seq):
    return sum(seq) / float(len(seq))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    speed_compare()

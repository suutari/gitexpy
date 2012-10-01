from nose.tools import *

from . import randomstring
from .diff import *

known_lcs = {
    ('abc', 'abc'): ((0,0), (1,1), (2,2)),
    ('cba', 'abc'): ((0,2),),
    ('xxx', 'yyy'): (),
    ('', 'yyy'): (),
    ('xxx', ''): (),
    ('x', 'x'): ((0,0),),
    ('x', ''): (),
    ('', 'y'): (),
    ('x', 'y'): (),
    ('', ''): (),
    ('abxab','ayb'): ((0,0), (4,2)),
    ('xaxcxabc', 'abcy'): ((5,0), (6,1), (7,2),),
    ('ffec','ecbcd'): ((2,0),(3,3)),
    ('aakkosto', 'pakkaus'): ((1,1),(2,2),(3,3),(5,6)),
    }
wordpairs = list(known_lcs.keys()) + [
    ('abcuixaduhae', 'kaicxahaoehxeh'),
    ]

lcs_functions = [
    lcs_r,
    lcs_d1,
    lcs_d2,
    lcs_d3,
    lcs_d4,
    lcs_m1,
    lcs_m,
    lcs_x,
    ]

# All LCS functions do not always give the same results. That is OK as
# long as the result is a LCS of the given strings, but to test the
# implementation details more carefully, we need to list here those
# entries from the known_lcs dictionary above that have a different
# result for some wordpair with their expected results.
known_lcs_specials = {
    (lcs_m1, 'cba', 'abc'): ((2,0),),
    (lcs_m1, 'xaxcxabc', 'abcy'): ((1,0), (6,1), (7,2),),
    (lcs_m1, 'ffec','ecbcd'): ((2,0),(3,1)),
    (lcs_m1, 'abcuixaduhae', 'kaicxahaoehxeh'): ((0,1),(4,2),(5,4),(6,5),(9,6),(10,7),(11,9)),
    (lcs_m, 'ffec','ecbcd'): ((2,0),(3,1)),
    (lcs_x, 'ffec','ecbcd'): ((2,0),(3,1)),
}

def assert_is_lcs(x, a, b):
    assert_is_cs(x, a, b)
    if (a,b) in known_lcs:
        expected_len = len(known_lcs[(a,b)])
    else:
        expected_len = len(lcs_x(a, b))
    assert_equal(
        len(x), expected_len,
        'LCS length mismatch: expected=%s, got=%s. (x=%s, a=%s, b=%s)' %
        (expected_len,len(x),x,a,b))
def assert_is_cs(x, a, b):
    assert_is_increasing(i for (i,j) in x)
    assert_is_increasing(j for (i,j) in x)
    assert_equal(
        [(a,b)] + [(i,j,a[i]) for (i,j) in x],
        [(a,b)] + [(i,j,b[j]) for (i,j) in x])
def assert_is_increasing(seq):
    lst = list(seq)
    for (n, cur) in enumerate(lst):
        if n != 0:
            assert_less(prev, cur, 'Not increasing: {}'.format(lst))
        prev = cur

def check_lcs_function(lcs, a, b):
    """Check that given lcs function lcs works for wordpair (a,b)"""
    assert_is_lcs(lcs(a,b),a,b)
    assert_is_lcs(lcs(b,a),b,a)

def test_basics():
    for f in lcs_functions:
        for (a,b) in wordpairs:
            if f == lcs_r and lcs_r_cost(len(a),len(b)) > 1000000:
                continue
            yield (check_lcs_function, f, a, b)

def test_random():
    randomstring.seed(123)
    for dummy in xrange(20):
        (a,b) = randomstring.get_random_stringpair()
        for f in lcs_functions:
            if f == lcs_r:
                # Too slow to test
                continue
            yield (check_lcs_function, f, a, b)

def test_exact_results():
    def check_results(f, a, b):
        try:
            expected = known_lcs_specials[(f,a,b)]
        except:
            try:
                expected = known_lcs[(a,b)]
            except:
                expected = lcs_d2(a,b)
        eq_(f(a,b), expected)
    for (a,b) in wordpairs:
        for f in lcs_functions:
            if f == lcs_r:
                continue
            yield (check_results, f, a, b)

def generate_n_length_words(n, chars):
    """
    Generate words of length n using the given characters.

    >>> list(generate_n_length_words(3, 'abc')) == [
    ...  'aaa', 'aab', 'aac', 'aba', 'abb', 'abc', 'aca', 'acb', 'acc',
    ...  'baa', 'bab', 'bac', 'bba', 'bbb', 'bbc', 'bca', 'bcb', 'bcc',
    ...  'caa', 'cab', 'cac', 'cba', 'cbb', 'cbc', 'cca', 'ccb', 'ccc']
    True
    >>> list(generate_n_length_words(3, 'a')) == ['aaa']
    True
    >>> list(generate_n_length_words(3, 'ab')) == [
    ...  'aaa', 'aab', 'aba', 'abb', 'baa', 'bab', 'bba', 'bbb']
    True
    >>> list(generate_n_length_words(2, 'abc')) == [
    ...  'aa', 'ab', 'ac', 'ba', 'bb', 'bc', 'ca', 'cb', 'cc']
    True
    """
    s = len(chars)
    for k in xrange(s**n):
        x = n * ['']
        left = k
        for i in xrange(n):
            (left, remainder) = divmod(left, s)
            x[n-1-i] = chars[remainder]
        yield ''.join(x)

def generate_wordpairs(N):
    """
    Generate pairs of words of length N or less.

    Iterates all combinations that could result in different LCS.
    """
    chars = 'abcdefghij'[:N]
    for n in xrange(N+1):
        for a in generate_n_length_words(n, chars):
            for m in xrange(N+1):
                for b in generate_n_length_words(m, chars):
                    yield (a, b)

def test_lcs_m_with_all_smaller_than_3():
    for (a,b) in generate_wordpairs(3):
        result = lcs_m(a,b)
        assert_is_cs(result,a,b)
        expected_len = len(lcs_d2(a,b))
        eq_(len(result), expected_len)

def test_edit_distance():
    def check_edit_distance(a, b, expected):
        eq_(edit_distance(a, b), expected)
        eq_(edit_distance(b, a), expected)
    for (a, b, expected_dist) in [
        ('', '', 0),
        ('', 'a', 1),
        ('', 'aa', 2),
        ('a', 'aa', 1),
        ('ab', 'aa', 2),
        ('ab', 'ba', 2),
        ('abc', '', 3),
        ('', 'abc', 3),
        ('abc', 'abc', 0),
        ('abc', 'bc', 1),
        ('aaa', 'bbb', 6),
        ('aaa', 'aba', 2),
        ('aa', 'aba', 1),
        ]:
        yield (check_edit_distance, a, b, expected_dist)

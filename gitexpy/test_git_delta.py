"""
Test some invariants of Git delta implementation tables T and U.
"""

from nose.tools import *

from .git_delta import T, U, WINDOW_SIZE
from .rabin import combine_val, generate_rabin_tables, BinaryPolynomial

def test_T():
    eq_(len(T), 256)
    eq_(max(T), 4285241020)
    eq_(T, [combine_val(T, x) for x in range(len(T))])

def test_U():
    eq_(len(U), 256)
    eq_(max(U), 2144592044)
    eq_(U, [combine_val(U, x) for x in range(len(U))])

def test_T_and_U():
    (generated_T, generated_U) = generate_rabin_tables(
        BinaryPolynomial.from_int(T[1]), window_size=WINDOW_SIZE, bits=32)
    eq_(T, generated_T)
    eq_(U, generated_U)

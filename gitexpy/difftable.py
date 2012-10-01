"""
Generate random word pairs and print difference tables.
"""

import random

from .randomstring import randomstring

def print_random_tables(n):
    for (a, b) in random_pairs(get_words(), n):
        print_diff_table_of_words(a, b)

def get_words():
    words = [
        'aakkosto',
        'dynaaminen',
        'merkki',
        'sanasto',
        'staattinen',
        'tavujono',
        'pakkaus',
        'pakkausko',
        ]
    letters = set()
    for w in words:
        letters = letters.union(set(w))
    letters = list(letters)
    for i in range(5):
        words.append(randomstring(5, 11, letters))
    return words

def random_pairs(seq, n):
    lst = list(seq)
    pop = [(x, y) for (ix, x) in enumerate(lst) for (iy, y) in enumerate(lst) if ix < iy]
    sample = random.sample(pop, min(n, len(pop)))
    random.shuffle(sample)
    return sample

def print_diff_table_of_words(a, b):
    r"""
    Print diff table of given words.

    >>> print_diff_table_of_words('aakkosto', 'pakkaus')
      a a k k o s t o.
    p                .
    a \ \            .
    k     \ \        .
    k     \ \        .
    a \ \            .
    u                .
    s           \    .
    """
    table = generate_diff_table(a, b)
    print_diff_table(table)

def generate_diff_table(a, b):
    delim = ' '
    table = [[' ' + delim] + list(delim.join(a))]
    for bx in b:
        row = [bx]
        for ax in a:
            row.append(delim + ('\\' if ax == bx else ' '))
        table.append(row)
    return table

def print_diff_table(table):
    for row in table:
        print(''.join(row) + '.')

if __name__ == '__main__':
    print_random_tables(3)

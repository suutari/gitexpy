import random

from six.moves import xrange

lowercaseletters = [chr(i) for i in range(ord('a'), ord('z')+1)]

def seed(x):
    return random.seed(x)

def generate_random_string():
    string = ''
    for sym in xrange(ord('a'), ord('z')):
        string += random.randint(0, 10) * chr(sym)
    string += 100 * 'z'
    string = shuffle_string(string)
    return string

def shuffle_string(string):
    tmp = list(string)
    random.shuffle(tmp)
    return ''.join(tmp)

def get_random_stringpair():
    chars = random.choice((
            'ab',
            'abc',
            lowercaseletters,
            ''.join(lowercaseletters) + ''.join(lowercaseletters).upper()))
    pair_type = random.randint(0, 2)
    if pair_type == 0:
        return randomstringpair(
            minlen=0, maxlen=10,
            maxeditdistance=random.randint(0,10),
            chars=chars)
    elif pair_type == 1:
        return randomstringpair(
            minlen=0, maxlen=6,
            maxeditdistance=random.randint(2,4),
            chars=chars)
    elif pair_type == 2:
        return randomstringpair(
            minlen=10, maxlen=20,
            maxeditdistance=random.randint(20,30),
            chars=chars)

def randomstringpair(minlen, maxlen, maxeditdistance, chars=lowercaseletters):
    a = randomstring(minlen, maxlen, chars)
    btable = list(a)
    deletes = random.randint(0, min(maxeditdistance, len(btable)))
    inserts = maxeditdistance - deletes
    for i in sorted(
        random.sample(xrange(len(btable)), deletes),
        reverse=True):
        del btable[i]
    while inserts > 0:
        inslen = random.randint(1, inserts)
        inspos = random.randint(0, len(btable)+1)
        btable.insert(inspos, randomstring(inslen, inslen, chars))
        inserts -= inslen
    return (a, ''.join(btable))

def randomstring(minlen, maxlen, chars=lowercaseletters):
    return ''.join(
        random.choice(chars)
        for dummy in xrange(random.randint(minlen, maxlen)))

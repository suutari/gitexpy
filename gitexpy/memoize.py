class memoized:
    """
    Memoize function call results.

    If function is decorated with @memoized, then it will be called
    only once per argument tuple and the later calls will get the
    result from memoize cache (self.c).

    >>> @memoized
    ... def f(x):
    ...     print('Calling f(%r)' % x)
    ...     return x+42
    >>> f(1)
    Calling f(1)
    43
    >>> f(1)
    43
    >>> f(2)
    Calling f(2)
    44
    >>> f(2)
    44
    """
    def __init__(self, f):
        self.f = f
        self.c = {}
    def __call__(self, *args):
        try:
            return self.c[args]
        except KeyError:
            self.c[args] = v = self.f(*args)
            return v

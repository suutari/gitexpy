"""
Delta difference stuff.

Some testing:

>>> entrylist = create_entrylist(313)
>>> entry = entrylist[0]
>>> shorten_chain(entry, len(entrylist), 5)
>>> len(entry.chain())
5
>>> entry.chain()
[Entry(0), Entry(63), Entry(126), Entry(188), Entry(251)]
"""

class Entry(object):
    def __init__(self, name):
        self.name = name
        self.next = None
    def chain(self):
        result = []
        x = self
        while x:
            result.append(x)
            x = x.next
        return result
    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.name) + ')'

def create_entrylist(n=300):
    entrylist = []
    for i in range(n):
        e = Entry(i)
        if entrylist:
            p = entrylist[-1]
            p.next = e
        entrylist.append(e)
    return entrylist

HASH_LIMIT = 64

def shorten_chain(entry, count, hash_limit=HASH_LIMIT):
    # Ported from this C code from Git
    # do {
    # 	acc += hash_count[i] - HASH_LIMIT;
    # 	if (acc > 0) {
    # 		struct unpacked_index_entry *keep = entry;
    # 		do {
    # 			entry = entry->next;
    # 			acc -= HASH_LIMIT;
    # 		} while (acc > 0);
    # 		keep->next = entry->next;
    # 	}
    # 	entry = entry->next;
    # } while (entry);
    hash_count_i = count
    acc = 0
    while entry:
        acc += hash_count_i - hash_limit
        if acc > 0:
            keep = entry
            while acc > 0:
                entry = entry.next
                acc -= hash_limit
            keep.next = entry.next
        entry = entry.next

class FieldList(object):
    def __init__(self):
        self.f = {}
        self.nf = {}
        self.d = {}
        self.n = 0
    def add_field(self, name, value, decoder=None):
        self.n += 1
        self.nf[(self.n, name)] = value
        self.f[name] = value
        self.d[name] = decoder
    def __getitem__(self, name):
        return self.f[name]
    def get_decoded(self, name):
        return self.d[name](self.f[name])
    def __contains__(self, name):
        return name in self.f
    def __str__(self):
        sorted_keys = [x[1] for x in sorted(self.nf.keys())]
        lines = []
        for key in sorted_keys:
            val = self.f[key]
            decoder = self.d[key]
            if decoder:
                decoded = decoder(val)
                line = '%s = %s (%s)' % (key, decoded, val)
            else:
                line = '%s = (%s)' % (key, val)
            lines.append(line)
        return '\n'.join(lines)

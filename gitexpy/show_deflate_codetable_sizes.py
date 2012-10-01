import os
import re
from . import zlibstream

rx_codes_offset = re.compile('^BLOCK\[[0-9]+\]: codes_start_offset=([0-9]+)$')
rx_data_offset = re.compile('^BLOCK\[[0-9]+\]: data_start_offset=([0-9]+)$')

class InfoStream(object):
    def write(self, text):
        m = rx_codes_offset.match(text)
        if m:
            self.codes_start = int(m.group(1))
        else:
            m = rx_data_offset.match(text)
            if m:
                codes_stop = int(m.group(1))
                codes_size = codes_stop - self.codes_start
                print(codes_size)

def main(sys):
    devnull = open(os.devnull, 'wb')
    try:
        sys.stdin = sys.stdin.detach()
    except:
        pass
    zlibstream.parse(
        in_stream=sys.stdin,
        out_stream=devnull,
        info_stream=InfoStream())

if __name__ == '__main__':
    import sys
    main(sys)

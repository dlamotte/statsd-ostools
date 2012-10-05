import logging
import re

log = logging.getLogger(__name__)
re_spaces = re.compile(r'\s+')

class Parser(object):
    def __init__(self, fp):
        self.fp = fp
        self.state = 0
        self.keys = []

    def __iter__(self):
        while True:
            yield self.parse_one()

    def _next(self):
        line = self.fp.readline()
        if line == '':
            raise StopIteration
        return line

class IOStatParser(Parser):
    def parse_one(self):
        row = []
        while True:
            try:
                line = self._next()
            except StopIteration:
                if row:
                    return tuple(row)
                else:
                    raise

            #log.debug('%s %s: %s' % (
            #    self.__class__.__name__,
            #    self.state,
            #    line.rstrip('\r\n')
            #))
            if self.state == 0:
                if line.startswith('Device:'):
                    self.keys = re_spaces.split(line.rstrip())
                    self.keys[0] = 'device'
                    self.state = 1

            elif self.state == 1:
                if line.startswith('Device:'):
                    self.state = 2

            elif self.state == 2:
                if not line.strip():
                    self.state = 1
                    return tuple(row)
                data = re_spaces.split(line.rstrip())
                row.append(tuple(zip(self.keys, data)))

class MPStatParser(Parser):
    def parse_one(self):
        row = []
        while True:
            try:
                line = self._next()
            except StopIteration:
                if row:
                    return tuple(row)
                else:
                    raise

            #log.debug('%s %s: %s' % (
            #    self.__class__.__name__,
            #    self.state,
            #    line.rstrip('\r\n')
            #))
            split = re_spaces.split(line.rstrip())
            if self.state == 0:
                if len(split) == 1:
                    pass

                elif split[1] == 'CPU':
                    self.keys = split[1:]
                    self.state = 2

            elif self.state == 1:
                if split[1] == 'CPU':
                    self.state = 2

            elif self.state == 2:
                if not line.strip():
                    self.state = 1
                    return tuple(row)
                row.append(tuple(zip(self.keys, split[1:])))

class VMStatParser(Parser):
    def parse_one(self):
        while True:
            line = self._next()

            #log.debug('%s %s: %s' % (
            #    self.__class__.__name__,
            #    self.state,
            #    line.rstrip('\r\n')
            #))
            if self.state == 0:
                if line.startswith('procs'):
                    self.state = 1

            elif self.state == 1:
                self.keys = re_spaces.split(line.strip())
                self.state = 2

            elif self.state == 2:
                if line.startswith('procs'):
                    pass

                else:
                    return tuple(zip(self.keys, re_spaces.split(line.strip())))

            elif self.state == 3:
                # skip header line
                self.state = 2


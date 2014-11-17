import errno
import logging
import re
import signal
import subprocess
from setproctitle import setproctitle
from statsd_ostools import parser

log = logging.getLogger(__name__)
workers = []

re_space = re.compile(r'\s+')
re_slash = re.compile(r'/+')
re_nonalphanum = re.compile(r'[^a-zA-Z_\-0-9\.]')

SIGNALED = False


def signal_handler(signum, frame):
    _ = signum, frame
    global SIGNALED
    SIGNALED = True


class Worker(object):
    parser = None

    def __init__(self, statsd, interval, send_integers):
        self.statsd = statsd
        self.interval = interval
        self.send_integers = send_integers

    def get_cmd_argv(self):
        raise NotImplementedError()

    def send(self, data):
        raise NotImplementedError()

    def clean_key(self, key):
        _ = self  # No static method, allow workers to override
        return re_nonalphanum.sub('',
            re_slash.sub('-', re_space.sub('_', key.replace('%', 'p')))
        )

    def get_cmd_string(self):
        return ' '.join(self.get_cmd_argv())

    def run(self):
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        setproctitle('statsd-ostools: %s' % self.get_cmd_string())
        p = subprocess.Popen(self.get_cmd_argv(), stdout=subprocess.PIPE)
        run_parser = self.parser(p.stdout)
        while not SIGNALED:
            try:
                data = run_parser.parse_one()
                self.send(data)
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise
            except StopIteration:
                break

        p.terminate()
        p.stdout.read()
        p.stdout.close()
        p.wait()
        return 0


@workers.append
class IOStatWorker(Worker):
    name = 'iostat'
    parser = parser.IOStatParser

    def get_cmd_argv(self):
        return ['iostat', '-xk', str(self.interval)]

    def send(self, data):
        for row in data:
            dev = row[0][1]
            prefix = '%s.%s.' % (self.name, dev)
            for k, v in row[1:]:
                if self.send_integers is True:
                    v = int(float(v))
                key = prefix + self.clean_key(k)
                log.debug('%s: %s' % (key, v))
                self.statsd.gauge(key, v)


@workers.append
class MPStatWorker(Worker):
    name = 'mpstat'
    parser = parser.MPStatParser

    def get_cmd_argv(self):
        return ['mpstat', '-P', 'ALL', str(self.interval)]

    def send(self, data):
        for row in data:
            cpu = row[0][1]
            prefix = '%s.%s.' % (self.name, cpu)
            for k, v in row[1:]:
                if self.send_integers is True:
                    v = int(float(v))
                key = prefix + self.clean_key(k)
                log.debug('%s: %s' % (key, v))
                self.statsd.gauge(key, v)


@workers.append
class VMStatWorker(Worker):
    name = 'vmstat'
    parser = parser.VMStatParser

    def get_cmd_argv(self):
        return ['vmstat', str(self.interval)]

    def send(self, data):
        prefix = '%s.' % self.name
        for k, v in data:
            if self.send_integers is True:
                v = int(float(v))
            key = prefix + self.clean_key(k)
            log.debug('%s: %s' % (key, v))
            self.statsd.gauge(key, v)

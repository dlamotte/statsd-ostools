import errno
import logging
import optparse
import os
import signal
import socket
import sys
import time
from setproctitle import setproctitle
from statsd.client import StatsClient
from statsd_ostools import worker

log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s')

SIGNALED = False

def signal_handler(signum, frame):
    global SIGNALED
    SIGNALED = True

def main():
    parser = optparse.OptionParser(
        description='send statistics with <prefix> to statsd',
        usage='%prog [options] <prefix>',
    )
    parser.epilog = 'ie: %s stats.ostools.hostname' % parser.get_prog_name()

    parser.add_option('-H', '--host',
        dest='host', metavar='HOST', default='localhost',
        help='statsd hostname/ip (default: localhost)',
    )
    parser.add_option('-p', '--port',
        dest='port', metavar='PORT', type='int', default=8125,
        help='statsd port (default: 8125)',
    )
    parser.add_option('-i', '--interval',
        dest='interval', metavar='INT', type='int', default=10,
        help='interval to pass to stat commands (default: 10)',
    )
    parser.add_option('-d', '--debug',
        dest='debug', action='store_true', default=False,
        help='turn on debugging',
    )
    (opts, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Please supply a stats prefix')
        sys.exit(1)
    prefix = args[0]

    if opts.debug:
        rootlogger = logging.getLogger()
        rootlogger.setLevel(logging.DEBUG)
        del rootlogger

    statsd = StatsClient(opts.host, opts.port, prefix)

    os.environ['LC_ALL'] = 'C' # standardize output format (datetime, ...)
    setproctitle('statsd-ostools: master %s:%s (%s)' % (
        opts.host,
        opts.port,
        prefix,
    ))

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    kids = []
    for workerklass in worker.workers:
        pid = os.fork()
        kids.append(pid)
        if pid == 0:
            sys.exit(workerklass(statsd, opts.interval).run())

    while not SIGNALED:
        log.debug('master: sleeping...')
        time.sleep(opts.interval)

    for pid in kids:
        exceptions = []
        try:
            os.kill(pid, signal.SIGTERM)
            os.waitpid(pid, 0)
        except OSError as e:
            if e.errno not in (errno.ECHILD, errno.ESRCH):
                exceptions.append(sys.exc_info())

    for exc_info in exceptions:
        log.error('unhandled error during cleanup', exc_info=exc_info)

    sys.exit(0)

if __name__ == '__main__':
    main()

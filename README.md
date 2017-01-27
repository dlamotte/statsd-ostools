statsd-ostools
==============

[![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech/)

Tools for sending OS data to statsd (currently only supports Linux).

Supported Tools
---------------

* iostat
* mpstat
* vmstat

Example usage:

    statsd-ostools --prefix stats.ostools.hostname

Installation
============

    pip install -e git+https://github.com/dlamotte/statsd-ostools.git#egg=statsd-ostools

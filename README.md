statsd-ostools
==============

Tools for sending OS data to statsd (currently only supports Linux).

Supported Tools
---------------

* iostat
* mpstat
* vmstat

Example usage:

    statsd-ostools --prefix stats.ostools.hostname


# (c) Copyright 2015 Hewlett Packard Enterprise Development LP
# (c) Copyright 2017 SUSE LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import ConfigParser
from ConfigParser import NoSectionError, NoOptionError
from optparse import OptionParser
import random
import sys
import time
from swift.common.memcached import (MemcacheRing, CONN_TIMEOUT, POOL_TIMEOUT,
                                    IO_TIMEOUT, TRY_COUNT)
from swiftlm.utils.utility import KeyNames


usage = """
Program to test the memcached ring. It uses the Swift client so the results
may not be applicable to other memcached clients. test_conns repeatedly
connects and does a get operation -- and reports on latency to connect/get.
test_gets connects once, and repeatedly does get operations. The latency
reported is the time to do the get operation.

Usage:

    swiftlm-memcached set blah "hello world"

    swiftlm-memcached get blah

    swiftlm-memcached test_conns [--keys <number>]
                                 [--run_time <seconds>]

    swiftlm-memcached test_gets  [--keys <number>]
                                 [--run_time <seconds>]


    Options:
      --config <filename>
        Defaults to /etc/swift/memcache.conf. You typically need to run
        with sudo to access /etc/swift/memcache.conf.

      --servers <server>:<port>,<server:port>,...
        Use these servers instead of from --config. You can use --servers if
        you do not have a memcache.conf file.

      --keys <number>
        In test_conns and test_gets, set this number of unique keys.
        Default is 100 keys.

      --run_time <seconds>
        In test_conns and test_gets, run for this number of seconds.
        Defaults to 30 seconds.
"""


class Buckets(object):
    """
    Track latency average and pattern
    """
    def __init__(self):
        self.slots = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 2.0, 5.0, 10.0, 15.0,
                      20.0, 25.0, 30.0, 40.0]
        self.bucket = {}
        for slot in self.slots:
            self.bucket[str(slot)] = 0
        self.bucket['>'] = 0
        self.total = 0.0
        self.count = 0
        self.min = None
        self.max = 0.0

    def record(self, latency):
        if self.min is None:
            self.min = latency
            self.max = latency
        if self.min > latency:
            self.min = latency
        if self.max < latency:
            self.max = latency
        off_end = True
        for slot in self.slots:
            if latency <= slot:
                self.bucket[str(slot)] += 1
                off_end = False
                break
        if off_end:
            self.bucket['>'] += 1
        self.total += latency
        self.count += 1

    def __repr__(self):
        lines = []
        if self.count > 0:
            lines.append('Average: %s ms' % float(self.total/self.count))
        headings = ''
        for slot in self.slots:
            headings += '   %s ' % slot
        headings += ' > '
        lines.append(headings)
        values = ''
        for slot in self.slots:
            # Does not align once slot is double-digit; not worth effort to fix
            values += ' %5d ' % self.bucket[str(slot)]
        values += ' %5d ' % self.bucket['>']
        lines.append(values)
        lines.append('Range %s ms - %s ms' % (self.min, self.max))
        return '\n'.join(lines)


def memcached_main(action, options, key=None, value=None):
    memcache_ring = MemcacheRing(
        options['servers'],
        connect_timeout=options['connect_timeout'],
        pool_timeout=options['pool_timeout'],
        tries=options['tries'],
        io_timeout=options['io_timeout'],
        allow_pickle=(options['serialization_format'] == 0),
        allow_unpickle=(options['serialization_format'] <= 1),
        max_conns=options['max_conns'])

    if action == 'set':
        start_time = time.time()
        memcache_ring = get_memcache_ring(options)
        memcache_ring.set(key, value, time=600)
        print('Duration: %s ms' % str((time.time() - start_time) * 1000))
    elif action == 'get':
        start_time = time.time()
        memcache_ring = get_memcache_ring(options)
        value, latency = memcache_get(memcache_ring, key)
        print('Duration: %s ms' % str((time.time() - start_time) * 1000))
        print('Value: %s' % value)
    elif action == 'test_conns':
        test_conns(options)
    elif action == 'test_gets':
        test_gets(memcache_ring, options)


def get_memcache_ring(options):
    memcache_ring = MemcacheRing(
        options['servers'],
        connect_timeout=options['connect_timeout'],
        pool_timeout=options['pool_timeout'],
        tries=options['tries'],
        io_timeout=options['io_timeout'],
        allow_pickle=(options['serialization_format'] == 0),
        allow_unpickle=(options['serialization_format'] <= 1),
        max_conns=options['max_conns'])
    return memcache_ring


def test_conns(options):
    # Set a value for every key
    memcache_ring = get_memcache_ring(options)
    keys = KeyNames(options['number_of_keys'])
    for key in keys.get_keys():
        memcache_ring.set(key, key, time=options['run_time'] + 100)

    # Read them back until time to stop
    start_time = time.time()
    count = 0
    buckets = Buckets()
    for key in keys.get_keys_forever():
        count += 1
        # This does not connect
        del memcache_ring
        memcache_ring = get_memcache_ring(options)
        value, latency = memcache_get(memcache_ring, key)
        buckets.record(latency)
        if time.time() - start_time > options['run_time']:
            break
    print('Duration: %s sec' % str(time.time() - start_time))
    print('Average for %s cycles: %s ms' % (
        count, str((time.time() - start_time) * 1000 / count)))
    print('Latency for: connect + get')
    print('%s' % buckets)


def test_gets(memcache_ring, options):
    # Set a value for every key
    keys = KeyNames(options['number_of_keys'])
    for key in keys.get_keys():
        memcache_ring.set(key, key, time=options['run_time'] + 100)

    # Read them back until time to stop
    start_time = time.time()
    count = 0
    buckets = Buckets()
    for key in keys.get_keys_forever():
        count += 1
        value, latency = memcache_get(memcache_ring, key)
        buckets.record(latency)
        if time.time() - start_time > options['run_time']:
            break
    print('Duration: %s sec' % str(time.time() - start_time))
    print('Average for %s cycles: %s ms' % (
        count, str((time.time() - start_time) * 1000 / count)))
    print('Latency per get:')
    print('%s' % buckets)


def memcache_get(memcache_ring, key):
    start_time = time.time()
    value = memcache_ring.get(key)
    latency = time.time() - start_time
    return value, latency * 1000


def main():
    parser = OptionParser(usage=usage)
    parser.add_option('--config', dest='config_file', default=None)
    parser.add_option('--servers', dest='servers', default=None)
    parser.add_option('--run_time', dest='run_time', default=30)
    parser.add_option('--keys', dest='keys', default=100)
    (options, args) = parser.parse_args()

    if not options.config_file:
        options.config_file = '/etc/swift/memcache.conf'

    main_options = {}
    memcache_options = {}
    main_options['serialization_format'] = 2
    main_options['max_conns'] = 2
    if options.config_file:
        memcache_conf = ConfigParser.RawConfigParser()
        if memcache_conf.read(options.config_file):
            # if memcache.conf exists we'll start with those base options
            try:
                memcache_options = dict(memcache_conf.items('memcache'))
            except NoSectionError:
                pass
            try:
                memcache_servers = \
                    memcache_conf.get('memcache', 'memcache_servers')
            except (NoSectionError, NoOptionError):
                print('Missing memcache_servers in %s' % options.config_file)
                sys.exit(1)
            try:
                main_options['serialization_format'] = int(
                    memcache_conf.get('memcache',
                                      'memcache_serialization_support'))
            except (NoSectionError, NoOptionError, ValueError):
                pass
            try:
                new_max_conns = \
                    memcache_conf.get('memcache',
                                      'memcache_max_connections')
                main_options['max_conns'] = int(new_max_conns)
            except (NoSectionError, NoOptionError, ValueError):
                pass
        elif not options.servers:
            print('unable to read %s' % options.config_file)
            sys.exit(1)
    if options.servers:
        memcache_servers = options.servers
    servers = [s.strip() for s in memcache_servers.split(',') if s.strip()]
    main_options['servers'] = servers
    main_options['connect_timeout'] = float(memcache_options.get(
        'connect_timeout', CONN_TIMEOUT))
    main_options['pool_timeout'] = float(memcache_options.get(
        'pool_timeout', POOL_TIMEOUT))
    main_options['tries'] = int(memcache_options.get('tries', TRY_COUNT))
    main_options['io_timeout'] = float(memcache_options.get('io_timeout',
                                                            IO_TIMEOUT))
    main_options['run_time'] = float(options.run_time)
    main_options['number_of_keys'] = int(options.keys)
    if len(args) == 0:
        print('Missing command')
        sys.exit(1)
    action = args[0]
    if len(args) > 1:
        key = args[1]
    else:
        key = None
    if len(args) > 2:
        value = args[2]
    else:
        value = None

    memcached_main(action, main_options, key=key, value=value)

if __name__ == '__main__':
    main()


# (c) Copyright 2015,2016 Hewlett Packard Enterprise Development LP
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

import math
import socket
from threading import Thread, BoundedSemaphore
import urlparse

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os
from collections import namedtuple

from swiftlm.utils.utility import (
    get_ring_hosts, server_type, UtilityExeception
)
from swiftlm.utils.metricdata import MetricData, get_base_dimensions
from swiftlm.utils.values import Severity, ServerType
from swiftlm.utils.utility import run_cmd

# Connectivity needs to report out target hostname and observer hostname
# rather than the normal hostname dimension
_base_dimensions = dict(get_base_dimensions())
_base_dimensions['observer_host'] = socket.gethostname()

BASE_RESULT = MetricData(
    name=__name__,
    messages={
        'ok': '{url} ok',
        'fail': '{url} {fail_message}'
    },
    dimensions=_base_dimensions
)

MAX_THREAD_LIMIT = 10
CONNECT_TIMEOUT = 2.0
JOIN_WAIT = 10.0
SWIFT_PROXY_PATH = '/opt/stack/service/swift-proxy-server/etc'
MEMCACHE_CONF_PATH = '/etc/swift'
SWIFTLM_SCAN_PATH = '/etc/swiftlm'


class HostPort(namedtuple('HostPort', ['host', 'port'])):
    @classmethod
    def from_string(cls, s):
        """ Create a HostPort instance from a string """
        # Supports:
        # http://host.name, http://host.name:port
        # host.name, host.name:port
        # 10.10.10.10, 10.10.10.10:9999
        s = s.strip()
        colon_count = s.count(':')

        if colon_count == 2:
            return cls(*s.rsplit(':', 1))
        elif colon_count == 0:
            return cls(s, '0')
        elif colon_count == 1:
            colon_index = s.find(':')

            if (len(s) >= colon_index+2 and
                    s[colon_index+1] == s[colon_index+2] == '/'):
                # We ignore this, it is a URI scheme not a port.
                # We have to check the length of s first though, if s is
                # host:1 we could cause an indexerror.
                return cls(s, '0')
            else:
                return cls(*s.rsplit(':', 1))


class CheckThread(Thread):
    """ Threaded generic check """
    def __init__(self, hostport, check_func, thread_limit, result,
                 scheme=None):
        """
        :params hostport: HostPort to be passed to check_func.
        :params check_func: function that accepts a HostPort, performs a check
                            and returns a bool indicating success or failure.
                            True is success, False is a failure
        :params thread_limit: BoundedSemaphore for limiting number of active
                              threads.
        :params result: MetricData that will contain the results of the threads
                        check.
        :params scheme: The HostPort is checked via http/https
        """
        Thread.__init__(self)
        self.thread_limit = thread_limit
        self.check_func = check_func
        self.hostport = hostport

        self.result = result
        self.result.name += '.' + check_func.__name__
        if scheme:
            self.result['url'] = '%s://%s:%s' % (scheme, hostport.host,
                                                 hostport.port)
        else:
            self.result['url'] = '//%s:%s' % (hostport.host,
                                              hostport.port)
        # Ideally, we would indicate here that the hostname dimension
        # should not be overriden by Monasca-agent, but c'est la vie.
        self.result['hostname'] = '_'

    def run(self):
        self.thread_limit.acquire()
        check_result = self.check_func(self.hostport)

        if check_result[0]:
            self.result.value = Severity.ok
        else:
            self.result.msgkey('fail_message', check_result[1])
            self.result.value = Severity.fail

        self.thread_limit.release()


def connect_check(hp):
    try:
        s = socket.create_connection(hp, CONNECT_TIMEOUT)
        return (True,)
    except (socket.error, socket.timeout) as e:
        return (False, str(e))
    finally:
        try:
            s.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass


def memcache_check(hp):
    try:
        s = socket.create_connection(hp, CONNECT_TIMEOUT)
        s.sendall('stats\n')
        _ = s.recv(1024)
        return (True,)
    except (socket.error, socket.timeout) as e:
        return (False, str(e))
    finally:
        try:
            s.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass


# The metric name string is derived from the base metrics name
# string plus the name of the function called to collect the
# metric, therefore we are using rsync_check() to check
# for the status of rsync but using the functionality of
# connect_check()
def rsync_check(hp):
    return connect_check(hp)


def ping_check(hp):
    try:
        cmd_result = run_cmd('ping -c 1 -A %s' % hp.host)
        if cmd_result.exitcode == 0:
            return (True,)
        else:
            return (False, "ping_check failed")
    except Exception:
        return (False, "ping_check failed")


def check(targets, check_func, results, scheme=None):
    threads = []
    thread_limit = BoundedSemaphore(value=MAX_THREAD_LIMIT)

    if not targets:
        # No hosts to check
        return

    for target in targets:
        t = CheckThread(target, check_func, thread_limit, BASE_RESULT.child(),
                        scheme=scheme)
        t.start()
        threads.append(t)

    # Join wait time logic: worst case is that all threads suffer a timeout.
    # Since MAX_THREAD_LIMIT threads run in parallel, we may spend
    # CONNECT_TIMEOUT * (num-threads/MAX_THREAD_LIMIT) seconds in the
    # socket connect. Add JOIN_WAIT to handle other overhead.
    wait_time = (JOIN_WAIT +
                 CONNECT_TIMEOUT * math.ceil(float(len(threads)) /
                                             float(MAX_THREAD_LIMIT)))
    for t in threads:
        t.join(wait_time)
        if t.isAlive():
            # Should not get here, but in case we do
            t.result.msgkey('fail_message', 'check thread did not complete')
            t.result.value = Severity.fail

        results.append(t.result)


def main():
    """Checks connectivity to memcache and object servers."""
    results = []

    if server_type(ServerType.proxy):
        cp = configparser.ConfigParser()
        cp.read(os.path.join(MEMCACHE_CONF_PATH, 'memcache.conf'))

        try:
            memcache_servers = [
                HostPort.from_string(s) for s in
                cp.get('memcache', 'memcache_servers').split(',')
            ]
        except configparser.NoSectionError:
            memcache_servers = []

        check(memcache_servers, memcache_check, results)

        # Check Keystone token-validation endpoint
        scheme = 'http'
        cp.read(os.path.join(SWIFT_PROXY_PATH, 'proxy-server.conf'))
        try:
            ise = cp.get('filter:authtoken', 'auth_url')
            parsed = urlparse.urlparse(ise)
            endpoint_servers = [HostPort(parsed.hostname, str(parsed.port))]
            scheme = parsed.scheme
        except configparser.NoSectionError:
            endpoint_servers = []

        check(endpoint_servers, connect_check, results, scheme=scheme)

    # rsync is required for ACO servers so filter on these server_type()
    if (server_type(ServerType.account) or server_type(ServerType.container) or
            server_type(ServerType.object)):
        # swiftlm-scan.conf is the ansible-generated source of truth
        # default in the case of ansible not laying down the rsync-target port
        cp = configparser.ConfigParser()
        cp.read(os.path.join(SWIFTLM_SCAN_PATH, 'swiftlm-scan.conf'))

        # this assumes (rightfully so) that all nodes will be using
        # the same rsync_bind_port as opposed to querying each node
        # for its possibly uniquely-configured port
        try:
            rsync_bind_port = cp.get('rsync-target', 'rsync_bind_port')
        except (configparser.NoSectionError, configparser.NoOptionError):
            rsync_bind_port = '873'

        try:
            # retrieve unique list of nodes in the ring using the ring file
            # and utilizing the configured replication network IP
            rsync_targets = []
            devices = get_ring_hosts(ring_type=None)
            rsync_set = set()
            for device in devices:
                if device.replication_ip not in rsync_set:
                    rsync_host = socket.gethostbyaddr(device.replication_ip)
                    rsync_targets.append(HostPort(rsync_host[0],
                                                  rsync_bind_port))
                    rsync_set.add(device.replication_ip)
        except Exception:
            pass

        check(rsync_targets, rsync_check, results)

    # TODO -- rewrite this as a connect_check
    # try:
    #     ping_targets = []
    #     devices = get_ring_hosts(ring_type=None)
    #     ip_set = set()
    #
    #     for device in devices:
    #         if device.ip not in ip_set:
    #             # Port not relevant for ping_check. (Empty string is an
    #             # invalid dimension value, Hence '_' used for target_port)
    #             ping_targets.append(HostPort(device.ip, '_'))
    #             ip_set.add(device.ip)
    #
    # except Exception:  # noqa
    #   # may be some problem loading ring files, but not concern of this check
    #     # to diagnose any further.
    #     pass
    #
    # check(ping_targets, ping_check, results)

    return results

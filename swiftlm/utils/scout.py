#
# Copyright (c) 2014 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import eventlet
import socket
import time
from urlparse import urlparse
import urllib2
import json
from swiftlm.utils.utility import get_ring_hosts
from swiftlm.utils.values import ServerType


class Scout(object):
    """
    Obtain swift recon information

    This code is similar to swift.cli.recon except that it supports
    signing of requests.
    """

    def __init__(self, recon_type, verbose=False, suppress_errors=False,
                 timeout=5):
        self.recon_type = recon_type
        self.verbose = verbose
        self.suppress_errors = suppress_errors
        self.timeout = timeout

    def scout_host(self, base_url, recon_type):
        """
        Perform the actual HTTP request to obtain swift recon telemtry.

        :param base_url: the base url of the host you wish to check. str of the
                        format 'http://127.0.0.1:6000/recon/'
        :param recon_type: the swift recon check to request.
        :returns: tuple of (recon url used, response body, and status)
        """
        url = base_url + recon_type
        try:
            body = urllib2.urlopen(url, timeout=self.timeout).read()
            content = json.loads(body)
            if self.verbose:
                print("-> %s: %s" % (url, content))
            status = 200
        except urllib2.HTTPError as err:
            if not self.suppress_errors or self.verbose:
                print("-> %s: %s" % (url, err))
            content = err
            status = err.code
        except urllib2.URLError as err:
            if not self.suppress_errors or self.verbose:
                print("-> %s: %s" % (url, err))
            content = err
            status = -1
        return url, content, status

    def scout(self, host):
        """
        Obtain telemetry from a host running the swift recon middleware.

        :param host: host to check
        :returns: tuple of (recon url used, response body, status, time start
                  and time end)
        """
        base_url = "http://%s:%s/recon/" % (host[0], host[1])
        ts_start = time.time()
        url, content, status = self.scout_host(base_url, self.recon_type)
        ts_end = time.time()
        return url, content, status, ts_start, ts_end


class SwiftlmScout(object):
    """
    Retrieve and report cluster info from hosts running recon middleware.
    """

    def __init__(self, node_config, suppress_errors=True, verbose=False,
                 timeout=5):
        """
        Initialize

        :param node_config: helpd unit tests
        :param suppress_errors: Don't print connection error messages
        :param verbose: Show connection requests/responses
        :param timeout: Timeout on connections/responses
        :return:
        """
        self.verbose = False
        self.suppress_errors = False
        self.timeout = timeout
        self.pool_size = 30
        self.pool = eventlet.GreenPool(self.pool_size)
        self.recon_types = ['object', 'container', 'account']
        self.all_types = ['proxy', 'object', 'container', 'account']
        self.configured = {}
        self.devices = set()
        self.recon_cache_path = {}
        # These allow unit tests -- but has a potential future use if recon
        # is in proxy pipeline
        self.proxy_nodes = node_config.get('proxy_nodes', [])
        self.proxy_bind_port = node_config.get('proxy_bind_port')
        self.results = {}
        self.suppress_errors = suppress_errors
        self.verbose = verbose
        self._load_rings()

    def _scout_for_response(self, path, hosts):
        """
        Send request to hosts and save the response
        """
        scan = {}
        recon = Scout(path, verbose=self.verbose,
                      suppress_errors=self.suppress_errors,
                      timeout=self.timeout)
        for url, response, status, _, _ in self.pool.imap(recon.scout,
                                                          hosts):
            hostname = self._hostname(url)
            if not hostname:
                continue
            if status == 200:
                self._save_response(hostname, path, response)
            else:
                self._save_error(hostname, path, status, str(response))

    def _hostname(self, url):
        pieces = urlparse(url)
        try:
            return socket.gethostbyaddr(pieces.hostname)[0]
        except (socket.herror, socket.gaierror, TypeError) as err:
            self._save_error(url, 'gethostbyaddr', '', str(err))
            return None

    def _save_response(self, hostname, path, data_item):
        if not self.results.get(path):
            self.results[path] = {}
        self.results[path][hostname] = data_item

    def _save_error(self, hostname, path, status, response):
        if not self.results.get('errors'):
            self.results['errors'] = []
        self.results['errors'].append({'hostname': hostname,
                                       'path:': path,
                                       'status': status,
                                       'response': response})

    def scout_all(self):
        """
        Scout for all known information
        """
        for path, ring in [('async', 'object'),
                           ('replication/account', 'account'),
                           ('replication/container', 'container'),
                           ('replication', 'object'),
                           ('auditor/account', 'account'),
                           ('auditor/container', 'container'),
                           ('auditor/object', 'object'),
                           ('updater/container', 'container'),
                           ('updater/object', 'object'),
                           ('expirer/object', 'object'),
                           ('load', 'all'),
                           ('diskusage', 'rings'),
                           ('ringmd5', 'all'),
                           ('quarantined', 'rings'),
                           ('driveaudit', 'rings'),
                           ('sockstat', 'all')]:
            self._scout_for_response(path, self.nodes[ring])

    def scout_aggregate(self):
        """
        Scout for information needed for swiftlm-aggregate
        """
        for path, ring in [('async', 'object'),
                           ('diskusage', 'rings'),
                           ('ringmd5', 'all'),
                           ('replication/account', 'account'),
                           ('replication/container', 'container'),
                           ('replication', 'object'),
                           ('load', 'all')]:
            self._scout_for_response(path, self.nodes[ring])

    def path(self, recon_path, ring_type):
        """
        Scout for arbitrary path

        :param recon_path: Path, e.g, expirer/object
        :param ring_type: Ring type e.g., 'all;, 'object'
        """
        self._scout_for_response(recon_path, self.nodes[ring_type])

    def get_results(self):
        return self.results

    @classmethod
    def _get_devices(cls, ring_type):
        """
        Get a list of hosts compatible with Scout

        :param ring_type: Type of the ring, such as 'object'
        :returns: a set of tuples containing the ip and port of hosts
        """
        ring_data = get_ring_hosts(ring_type=ring_type)
        ips = set((n.ip, n.port) for n in ring_data)
        return ips

    def _load_rings(self):
        """
        Load ring data
        """
        self.nodes = {}
        self.nodes['object'] = self._get_devices(ServerType.object)
        self.nodes['account'] = self._get_devices(ServerType.account)
        self.nodes['container'] = self._get_devices(ServerType.container)
        self.nodes['proxy'] = set((n, self.proxy_bind_port)
                                  for n in self.proxy_nodes)

        # Build set of all nodes, were account, then object port is
        # preferred.
        self.nodes['rings'] = set((n, p) for (n, p) in self.nodes['account'])
        for node, port in self.nodes['object']:
            if not self._contains_node(node, self.nodes['rings']):
                self.nodes['rings'].add((node, port))
        for node, port in self.nodes['container']:
            if not self._contains_node(node, self.nodes['rings']):
                self.nodes['rings'].add((node, port))

        # Build set of all known node types
        self.nodes['all'] = set((n, p) for (n, p) in self.nodes['rings'])
        for node, port in self.nodes['proxy']:
            if not self._contains_node(node, self.nodes['all']):
                self.nodes['all'].add((node, port))

    @classmethod
    def _contains_node(cls, node, node_set):
        for name, _ in node_set:
            if name == node:
                return True
        return False

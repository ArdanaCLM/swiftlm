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

from shutil import rmtree
import socket
import tempfile
import unittest
import mock
import time
from mock import patch

from swiftlm.systems import connectivity
from swiftlm.utils.utility import RingDeviceEntry, os
from swiftlm.utils.values import ServerType, Severity


class TestConnectivity(unittest.TestCase):

    @mock.patch('swiftlm.systems.connectivity.configparser.ConfigParser.read')
    @mock.patch('swiftlm.systems.connectivity.get_ring_hosts')
    @mock.patch('swiftlm.systems.connectivity.server_type')
    def test_connectivity_with_no_checks(self, mock_server_type,
                                         mock_get_hosts, mock_read):
        mock_server_type.return_value = True
        mock_get_hosts.return_value = []

        results = connectivity.main()

        mock_server_type.assert_any_call(ServerType.proxy)
        mock_server_type.assert_any_call(ServerType.account or
                                         ServerType.container or
                                         ServerType.object)
        # mock_get_hosts.assert_called_with(ring_type=None)
        self.assertTrue(mock_read.called)

        self.assertEqual(0, len(results))


class TestHostPort(unittest.TestCase):

    def test_from_string(self):
        tests = {
            'http://host.name:9999': ('http://host.name', '9999'),
            'http://host.name': ('http://host.name', '0'),
            'host.name:9999': ('host.name', '9999'),
            'host.name': ('host.name', '0'),
            'http://10.10.10.10:9999': ('http://10.10.10.10', '9999'),
            'http://10.10.10.10': ('http://10.10.10.10', '0'),
            '10.10.10.10:9999': ('10.10.10.10', '9999'),
            '10.10.10.10': ('10.10.10.10', '0'),
        }

        for k, v in tests.items():
            hp = connectivity.HostPort.from_string(k)
            self.assertTupleEqual(v, hp)


def fake_get_ring_hosts(ring_type):
    results = [RingDeviceEntry('1.2.3.4', '6001', '/dev/sdb', '1.2.3.6'),
               RingDeviceEntry('1.2.3.5', '6001', '/dev/sdb', '1.2.3.7')]
    return results


def make_fake_run_cmd_call(return_values):
    class Result(object):
            def __init__(self):
                self.exitcode = 0

    def fake_run_cmd_call(cmd_args):
        result = Result()
        if return_values:
            result.exitcode = return_values[cmd_args]
        return result
    return fake_run_cmd_call


def make_fake_create_connection(connection_status, sendall_status):
    def fake_create_connection(addr_tuple, *args):
        if connection_status:
            if connection_status[addr_tuple]:
                raise socket.error('connection refused')
        sock = mock.MagicMock()
        if sendall_status:
            sock.sendall.side_effect = [sendall_status[addr_tuple]]
        return sock
    return fake_create_connection


class TestMain(unittest.TestCase):

    def p(self, name, mock):
        p = patch(name, mock)
        p.start()
        self.addCleanup(p.stop)

    def setUp(self):
        self.module = 'swiftlm.systems.connectivity.'
        self.swiftproxytestdir = tempfile.mkdtemp()
        self.memcacheconftestdir = tempfile.mkdtemp()
        self.fake_time = 123456

        self.p(self.module + 'SWIFT_PROXY_PATH', self.swiftproxytestdir)
        self.p(self.module + 'MEMCACHE_CONF_PATH', self.memcacheconftestdir)
        self.p(self.module + 'BASE_RESULT.dimensions', {})
        self.p('swiftlm.utils.metricdata.timestamp', lambda: 123456)

        self.expected_dimensions_base = {}
        self.expected_metric_base = {
            'metric': 'swiftlm.systems.connectivity',
            'timestamp': 123456
        }

    def tearDown(self):
        rmtree(self.swiftproxytestdir, ignore_errors=True)
        rmtree(self.memcacheconftestdir, ignore_errors=True)

    # def test_no_object_ring_files(self):
    #    @patch(self.module + 'get_ring_hosts', return_value=[])
    #    @patch(self.module + 'server_type', lambda x: x != ServerType.proxy)
    #    def do_it(*args):
    #        actual = connectivity.main()
    #        expected_dimensions = dict(self.expected_dimensions_base)
    #        expected_value_meta = dict(msg='No hosts to check')
    #        expected_metric = dict(self.expected_metric_base)
    #        expected_metric['metric'] += '.ping_check'
    #        expected_metric.update(dict(dimensions=expected_dimensions,
    #                                    value=Severity.warn,
    #                                    value_meta=expected_value_meta))
    #        actual_metric = actual[0].metric()
    #        self.assertEqual(expected_metric, actual_metric)
    #    do_it()

    # def test_no_swift_dir(self):
    #    non_existent_dir = os.path.join(self.testdir, 'not_here')
    #
    #    @patch('swiftlm.utils.utility.SWIFT_PATH', non_existent_dir)
    #    @patch(self.module + 'server_type', lambda x: x != ServerType.proxy)
    #    def do_it(*args):
    #        actual = connectivity.main()
    #        expected_dimensions = dict(self.expected_dimensions_base)
    #        expected_value_meta = dict(msg='No hosts to check')
    #        expected_metric = dict(self.expected_metric_base)
    #        expected_metric['metric'] += '.ping_check'
    #        expected_metric.update(dict(dimensions=expected_dimensions,
    #                                    value=Severity.warn,
    #                                    value_meta=expected_value_meta))
    #        actual_metric = actual[0].metric()
    #        print expected_metric
    #        self.assertEqual(expected_metric, actual_metric, actual_metric)
    #    do_it()

    # def test_object_server_ping(self):
    #    # fake pings succeed to 1.2.3.4 and fail to 1.2.3.5
    #    ping_args = {'ping -c 1 -A 1.2.3.4': 0,
    #                 'ping -c 1 -A 1.2.3.5': 1}
    #    fake_ping = make_fake_run_cmd_call(ping_args)
    #
    #    expected = []
    #    scenarios = (('1.2.3.4', '_', Severity.ok, '1.2.3.4:_ ok'),
    #                 ('1.2.3.5', '_', Severity.fail,
    #                  '1.2.3.5:_ ping_check failed'))
    #    for scenario in scenarios:
    #        expected_dimensions = dict(self.expected_dimensions_base)
    #        expected_dimensions.update({'hostname': scenario[0],
    #                                    'target_port': scenario[1]})
    #        if scenario[2] == Severity.fail:
    #            expected_dimensions.update({'fail_message':
    #                                        'ping_check failed'})
    #        expected_value_meta = dict(msg=scenario[3])
    #        expected_metric = dict(self.expected_metric_base)
    #        expected_metric['metric'] += '.ping_check'
    #        expected_metric.update(dict(dimensions=expected_dimensions,
    #                                    value=scenario[2],
    #                                    value_meta=expected_value_meta))
    #        expected.append(expected_metric)
    #
    #    @patch(self.module + 'get_ring_hosts', fake_get_ring_hosts)
    #    @patch(self.module + 'run_cmd', fake_ping)
    #    @patch(self.module + 'server_type', lambda x: x != ServerType.proxy)
    #    def do_it():
    #        actual = connectivity.main()
    #        for metric in actual:
    #            metric_dict = metric.metric()
    #            self.assertTrue(metric_dict in expected,
    #                            'Unexpected result %s not in %s'
    #                            % (metric_dict, expected))
    #            expected.remove(metric_dict)
    #        self.assertFalse(expected, expected)
    #    do_it()

    def test_memcache_server_check(self):
        with open(os.path.join(self.memcacheconftestdir, 'memcache.conf'),
                  'wb') as f:
            f.write(
                '[memcache]\n'
                'memcache_servers = 1.2.3.4:11211,1.2.3.5:11211,\
                                    1.2.3.6:9999\n'
            )
        expected = []
    #    # fake pings succeed to 1.2.3.4 and fail to 1.2.3.5
    #    ping_args = {('ping -c 1 -A 1.2.3.4'): 0,
    #                 ('ping -c 1 -A 1.2.3.5'): 1}
    #    fake_ping = make_fake_run_cmd_call(ping_args)
    #
    #    scenarios = (('1.2.3.4', '_', Severity.ok, '1.2.3.4:_ ok'),
    #                 ('1.2.3.5', '_', Severity.fail,
    #                  '1.2.3.5:_ ping_check failed'))
    #    for scenario in scenarios:
    #        expected_dimensions = dict(self.expected_dimensions_base)
    #        expected_dimensions.update({'hostname': scenario[0],
    #                                    'target_port': scenario[1]})
    #        if scenario[2] == Severity.fail:
    #            expected_dimensions.update({'fail_message':
    #                                        'ping_check failed'})
    #        expected_value_meta = dict(msg=scenario[3])
    #        expected_metric = dict(self.expected_metric_base)
    #        expected_metric['metric'] += '.ping_check'
    #        expected_metric.update(dict(dimensions=expected_dimensions,
    #                                    value=scenario[2],
    #                                    value_meta=expected_value_meta))
    #        expected.append(expected_metric)
    #
        # fake memcache connections, two ok, one fails.
        # fake keystone connection warns
        connection_status = {('1.2.3.4', '11211'): 0,
                             ('1.2.3.5', '11211'): 0,
                             ('1.2.3.6', '9999'): 1}
        sendall_returns = {('1.2.3.4', '11211'): 0,
                           ('1.2.3.5', '11211'): 0,
                           ('1.2.3.6', '9999'):
                           socket.error('connection refused')}
        fake_create_connection = make_fake_create_connection(
            connection_status=connection_status,
            sendall_status=sendall_returns)

        scenarios = (('1.2.3.4', '11211', Severity.ok, '//1.2.3.4:11211 ok'),
                     ('1.2.3.5', '11211', Severity.ok, '//1.2.3.5:11211 ok'),
                     ('1.2.3.6', '9999', Severity.fail,
                      '//1.2.3.6:9999 connection refused'))
        for scenario in scenarios:
            expected_dimensions = dict(self.expected_dimensions_base)
            expected_dimensions.update({'hostname': '_',
                                        'url': '//%s:%s' %
                                        (scenario[0], scenario[1])})
            expected_value_meta = dict(msg=scenario[3])
            expected_metric = dict(self.expected_metric_base)
            expected_metric['metric'] += '.memcache_check'
            expected_metric.update(dict(dimensions=expected_dimensions,
                                        value=scenario[2],
                                        value_meta=expected_value_meta))
            expected.append(expected_metric)

        @patch(self.module + 'get_ring_hosts', fake_get_ring_hosts)
        @patch(self.module + 'server_type', lambda x: x == ServerType.proxy)
        # @patch(self.module + 'run_cmd', fake_ping)
        @patch(self.module + 'socket.create_connection',
               fake_create_connection)
        def do_it():
            actual = connectivity.main()
            for metric in actual:
                metric_dict = metric.metric()
                self.assertTrue(metric_dict in expected,
                                'Unexpected result\n%s\nnot in:\n%s'
                                % (metric_dict, expected))
                expected.remove(metric_dict)
            self.assertFalse(expected, expected)
        do_it()

    def test_keystone_endpoint_check_fails(self):
        with open(os.path.join(self.swiftproxytestdir, 'proxy-server.conf'),
                  'wb') as f:
            f.write(
                '[filter:authtoken]\n'
                'auth_url = https://10.2.3.4:5000/\n'
                'auth_uri = https://myardana.test:5000/\n'
            )
        expected = []
        # fake keystone connection fails
        connection_status = {('10.2.3.4', '5000'): 1}
        fake_create_connection = make_fake_create_connection(
            connection_status=connection_status,
            sendall_status=None)

        scenarios = (('10.2.3.4', '5000', Severity.fail,
                      'https://10.2.3.4:5000 connection refused'),)
        for scenario in scenarios:
            expected_dimensions = dict(self.expected_dimensions_base)
            expected_dimensions.update({'hostname': '_',
                                        'url': 'https://%s:%s' %
                                        (scenario[0], scenario[1])})
            expected_value_meta = dict(msg=scenario[3])
            expected_metric = dict(self.expected_metric_base)
            expected_metric['metric'] += '.connect_check'
            expected_metric.update(dict(dimensions=expected_dimensions,
                                        value=scenario[2],
                                        value_meta=expected_value_meta))
            expected.append(expected_metric)

        @patch(self.module + 'server_type', lambda x: x == ServerType.proxy)
        # @patch(self.module + 'get_ring_hosts', lambda *args: [])
        @patch(self.module + 'socket.create_connection',
               fake_create_connection)
        def do_it():
            actual = connectivity.main()
            for metric in actual:
                metric_dict = metric.metric()
                self.assertTrue(metric_dict in expected,
                                'Unexpected result\n%s\nnot in:\n%s'
                                % (metric_dict, expected))
                expected.remove(metric_dict)
            self.assertFalse(expected, expected)
        do_it()

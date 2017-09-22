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


import os
import tempfile
import unittest

from swiftlm.utils.log_tailer import LogTailer, AccessStatsRecorder, \
    split_path, parse_proxy_log_message
from swiftlm.utils.utility import KeyNames


class TestLogTailer(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.rand_names = KeyNames(1024)

    def test_log_tailer(self):
        log_file_name = os.path.join(self.tempdir, 'test')
        write_fd = open(log_file_name, 'w')
        line_count = 0

        # Write a bunch of lines to the log file
        for text in self.rand_names.get_keys_forever():
            write_fd.write('%s\n' % text)
            write_fd.flush()
            line_count += 1
            if line_count > 100:
                break

        # Open log tailer (which skips over above lines)
        log_tailer = LogTailer(log_file_name)

        # Write another bunch of lines
        line_count = 0
        expected_lines = []
        for text in self.rand_names.get_keys_forever():
            expected_lines.append('%s\n' % text)
            write_fd.write('%s\n' % text)
            write_fd.flush()
            line_count += 1
            if line_count >= 10:
                break

        # Read back *some* of the lines
        lines_received = []
        line_count = 0
        for line in log_tailer.lines():
            lines_received.append(line)
            line_count += 1
            if line_count >= 5:
                break
        self.assertEqual(expected_lines[0:4], lines_received[0:4])

        # Close, delete, reopen and write more lines to the log file
        write_fd.close()
        os.unlink(log_file_name)
        write_fd = open(log_file_name, 'w')
        line_count = 0
        for text in self.rand_names.get_keys_forever():
            expected_lines.append('%s\n' % text)
            write_fd.write('%s\n' % text)
            write_fd.flush()
            line_count += 1
            if line_count >= 6:
                break

        # Continue reading lines
        for line in log_tailer.lines():
            lines_received.append(line)

        os.unlink(log_file_name)

        self.assertEqual(expected_lines, lines_received)


class TestOpsStats(unittest.TestCase):

    def test_ops_stats(self):
        t_ops = 0
        t_put = 0
        t_get = 0
        p1_ops = 0
        p1_put = 0
        p1_get = 0
        p1c1_ops = 0
        p1c1_put = 0
        p1c1_get = 0
        p1c2_ops = 0
        p1c2_put = 0
        p1c2_get = 0
        p2_ops = 0
        p2_put = 0
        p2_get = 0
        p2c1_ops = 0
        p2c1_put = 0
        p2c1_get = 0
        p2c2_ops = 0
        p2c2_put = 0
        p2c2_get = 0

        stats = AccessStatsRecorder()

        stats.record_op('POST', 200, 100, project=None)
        t_ops += 1

        stats.record_op('POST', 401, 100, project=None)
        t_ops += 1

        stats.record_op('POST', 200, 100, project='p1')
        t_ops += 1
        p1_ops += 1

        stats.record_op('POST', 200, 100, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        t_put += 100
        p1_ops += 1
        p1_put += 100
        p1c1_ops += 1
        p1c1_put += 100

        stats.record_op('POST', 200, 200, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        t_put += 200
        p1_ops += 1
        p1_put += 200
        p1c1_ops += 1
        p1c1_put += 200

        stats.record_op('POST', 200, 999, project='p1',
                        container='p1c1', obj=None)
        t_ops += 1
        p1_ops += 1
        p1c1_ops += 1

        stats.record_op('POST', 300, 999, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        p1_ops += 1
        p1c1_ops += 1

        stats.record_op('GET', 200, 10, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        t_get += 10
        p1_ops += 1
        p1_get += 10
        p1c1_ops += 1
        p1c1_get += 10

        stats.record_op('GET', 200, 20, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        t_get += 20
        p1_ops += 1
        p1_get += 20
        p1c1_ops += 1
        p1c1_get += 20

        stats.record_op('GET', 401, 999, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        p1_ops += 1
        p1c1_ops += 1

        stats.record_op('COPY', 200, 0, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        p1_ops += 1
        p1c1_ops += 1

        stats.record_op('PUT', 200, 40, project='p1',
                        container='p1c1', obj='blah')
        t_ops += 1
        t_put += 40
        p1_ops += 1
        p1_put += 40
        p1c1_ops += 1
        p1c1_put += 40

        stats.record_op('PUT', 200, 50, project='p1',
                        container='p1c2', obj='blah')
        t_ops += 1
        t_put += 50
        p1_ops += 1
        p1_put += 50
        p1c2_ops += 1
        p1c2_put += 50

        stats.record_op('PUT', 200, 1000, project='p2',
                        container='p2c1', obj='blah')
        t_ops += 1
        t_put += 1000
        p2_ops += 1
        p2_put += 1000
        p2c1_ops += 1
        p2c1_put += 1000

        stats.record_op('GET', 200, 2000, project='p2',
                        container='p2c2', obj='blah')
        t_ops += 1
        t_get += 2000
        p2_ops += 1
        p2_get += 2000
        p2c2_ops += 1
        p2c2_get += 2000

        self.assertEqual({'name': 'total', 'ops': t_ops,
                          'bytes_put': t_put, 'bytes_get':  t_get},
                         stats.get_stats())

        num_ps = 0
        for project in stats.get_projects():
            num_ps += 1
            name = project.get_stats().get('name')
            self.assertIn(name, ['p1', 'p2'])
            if name == 'p1':
                self.assertEqual({'name': 'p1', 'ops':  p1_ops,
                                  'bytes_put': p1_put, 'bytes_get':  p1_get},
                                 project.get_stats())
                num_cs = 0
                for container in project.get_containers():
                    num_cs += 1
                    name = container.get_stats().get('name')
                    self.assertIn(name, ['p1c1', 'p1c2'])
                    if name == 'p1c1':
                        self.assertEqual({'name': 'p1c1', 'ops': p1c1_ops,
                                          'bytes_put': p1c1_put,
                                          'bytes_get': p1c1_get},
                                         container.get_stats())
                    elif name == 'p1c2':
                        self.assertEqual({'name': 'p1c2', 'ops': p1c2_ops,
                                          'bytes_put': p1c2_put,
                                          'bytes_get': p1c2_get},
                                         container.get_stats())
                self.assertEqual(num_cs, 2)
            elif name == 'p2':
                self.assertEqual({'name': 'p2', 'ops': p2_ops,
                                  'bytes_put': p2_put,
                                  'bytes_get': p2_get},
                                 project.get_stats())
                num_cs = 0
                for container in project.get_containers():
                    num_cs += 1
                    name = container.get_stats().get('name')
                    self.assertIn(name, ['p2c1', 'p2c2'])
                    if name == 'p2c1':
                        self.assertEqual({'name': 'p2c1', 'ops': p2c1_ops,
                                          'bytes_put': p2c1_put,
                                          'bytes_get': p2c1_get},
                                         container.get_stats())
                    elif name == 'p2c2':
                        self.assertEqual({'name': 'p2c2', 'ops': p2c2_ops,
                                          'bytes_put': p2c2_put,
                                          'bytes_get': p2c2_get},
                                         container.get_stats())
                self.assertEqual(num_cs, 2)
        self.assertEqual(num_ps, 2)


class TestParsing(unittest.TestCase):

    def test_split_path(self):
        self.assertEqual((None, None, None), split_path(''))
        self.assertEqual((None, None, None), split_path('/'))
        self.assertEqual((None, None, None), split_path('/v1'))
        self.assertEqual(('a', None, None), split_path('/v1/a'))
        self.assertEqual(('a', None, None), split_path('/v1/a/'))
        self.assertEqual(('a', 'c', None), split_path('/v1/a/c'))
        self.assertEqual(('a', 'c', None), split_path('/v1/a/c/'))
        self.assertEqual(('a', 'c', 'o'), split_path('/v1/a/c/o'))
        self.assertEqual(('a', 'c', 'o/sub'), split_path('/v1/a/c/o/sub'))

    def test_log_parser_valid_messages(self):
        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt proxy-server:'
               ' 192.168.245.5 192.168.245.5 27/May/2016/00/18/00 HEAD'
               ' /v1/AUTH_7eacc76d75ef4457a20dc9de49edf8d4 HTTP/1.0 204'
               ' - python-swiftclient-3.0.1.dev5 e7adf95ba0bf4e31... - - -'
               ' txdcff156137454ebabab7d-0057479238 - 0.0837 - -'
               ' 1464308280.323693037 1464308280.407376051 -')
        result = parse_proxy_log_message(msg, ['AUTH_'])
        self.assertEqual(result, {'http_status': 204,
                                  'verb': 'HEAD',
                                  'bytes_transferred':  0,
                                  'project':
                                      '7eacc76d75ef4457a20dc9de49edf8d4',
                                  'container': None,
                                  'obj': None})

        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt proxy-server:'
               ' 192.168.245.5 192.168.245.5 27/May/2016/00/18/00 PUT'
               ' /v1/SERVICE_7eacc76d75ef4457a20dc9de49edf8d4/'
               'swift_monitor_latency_test/tinyobj-136-standard-ccp-c1-m1-mgmt'
               ' HTTP/1.0 201 -'
               ' python-swiftclient-3.0.1.dev5 e7adf95ba0bf4e31... 36 - -'
               ' tx8b39b5267f6a4185a7b9a-0057479238 - 0.0281 - -'
               ' 1464308280.435175896 1464308280.463263035 0')
        result = parse_proxy_log_message(msg, ['AUTH_', 'SERVICE_'])
        self.assertEqual(result, {'http_status': 201,
                                  'verb': 'PUT',
                                  'bytes_transferred': 36,
                                  'project':
                                      '7eacc76d75ef4457a20dc9de49edf8d4',
                                  'container': 'swift_monitor_latency_test',
                                  'obj': 'tinyobj-136-standard-ccp-c1-m1-mgmt'})

        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt proxy-server:'
               ' 192.168.245.5 192.168.245.5 27/May/2016/00/18/00 GET'
               ' /v1/AUTH_7eacc76d75ef4457a20dc9de49edf8d4/'
               'swift_monitor_latency_test/tinyobj-136-standard-ccp-c1-m1-mgmt'
               ' HTTP/1.0 200 -'
               ' python-swiftclient-3.0.1.dev5 e7adf95ba0bf4e31... - 36 -'
               ' txc4ff7061f2a046ddb9e2a-0057479238 - 0.0115 - -'
               ' 1464308280.469140053 1464308280.480681896 0')
        result = parse_proxy_log_message(msg, ['AUTH_'])
        self.assertEqual(result, {'http_status': 200,
                                  'verb': 'GET',
                                  'bytes_transferred': 36,
                                  'project':
                                      '7eacc76d75ef4457a20dc9de49edf8d4',
                                  'container': 'swift_monitor_latency_test',
                                  'obj': 'tinyobj-136-standard-ccp-c1-m1-mgmt'})

        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt proxy-server:'
               ' 192.168.245.5 192.168.245.5 27/May/2016/00/18/00 GET'
               ' /junk-path'
               ' HTTP/1.0 412 -'
               ' python-swiftclient-3.0.1.dev5 e7adf95ba0bf4e31... - 36 -'
               ' txc4ff7061f2a046ddb9e2a-0057479238 - 0.0115 - -'
               ' 1464308280.469140053 1464308280.480681896 0')
        result = parse_proxy_log_message(msg, ['AUTH_'])
        self.assertEqual(result, {'http_status': 412,
                                  'verb': 'GET',
                                  'bytes_transferred': 36,
                                  'project': None,
                                  'container': None,
                                  'obj':  None})

    def test_log_parser_excluded_messages(self):
        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt proxy-server: - -'
               ' 27/May/2016/00/18/00 HEAD'
               ' /v1/AUTH_7eacc76d75ef4457a20dc9de49edf8d4/'
               'swift_monitor_latency_test HTTP/1.0 204 - Swift - - - -'
               ' tx8b39b5267f6a4185a7b9a-0057479238 - 0.0051 RL'
               ' - 1464308280.439218044 1464308280.444314957 0')
        result = parse_proxy_log_message(msg, ['AUTH_'])
        self.assertIsInstance(result, str)

        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt proxy-server: - -'
               ' 27/May/2016/00/18/00 HEAD'
               ' /v1/.internal_coount/'
               'blah HTTP/1.0 204 - Swift - - - -'
               ' tx8b39b5267f6a4185a7b9a-0057479238 - 0.0051 RL'
               ' - 1464308280.439218044 1464308280.444314957 0')
        result = parse_proxy_log_message(msg, ['AUTH_'])
        self.assertIsInstance(result, str)

    def test_log_parser_not_proxy_messages(self):
        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt object-server:'
               ' 192.168.245.4 - - [27/May/2016:00:18:00 +0000]'
               ' "DELETE /disk0/1587/'
               'AUTH_7eacc76d75ef4457a20dc9de49edf8d4/'
               'swift_monitor_latency_test/tinyobj-136-standard-ccp-c1-m1-mgmt"'
               ' 204 - "DELETE http://192.168.245.9:8080/v1/'
               'AUTH_7eacc76d75ef4457a20dc9de49edf8d4/'
               'swift_monitor_latency_test/tinyobj-136-standard-ccp-c1-m1-mgmt"'
               ' "tx33cf0f271eac46469231e-0057479238" "proxy-server 3064"'
               ' 0.0050 "-" 2835 0')
        result = parse_proxy_log_message(msg, ['AUTH_'])
        self.assertIsInstance(result, str)

        msg = ('May 27 00:18:00 standard-ccp-c1-m2-mgmt proxy-server:'
               ' Deferring reject downstream')
        result = parse_proxy_log_message(msg, ['AUTH_'])
        self.assertIsInstance(result, str)

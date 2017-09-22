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


import json
import unittest
import mock
import urllib2
from swiftlm.utils.scout import Scout, SwiftlmScout


class TestScout(unittest.TestCase):
    def setUp(self, *_args, **_kwargs):
        self.scout_instance = Scout("type", suppress_errors=True)
        self.url = 'http://127.0.0.1:8080/recon/type'
        self.server_type_url = 'http://127.0.0.1:8080/'

    @mock.patch('urllib2.urlopen')
    def test_scout_ok(self, mock_urlopen):
        mock_urlopen.return_value.read = lambda: json.dumps([])
        url, content, status, ts_start, ts_end = self.scout_instance.scout(
            ("127.0.0.1", "8080"))
        self.assertEqual(url, self.url)
        self.assertEqual(content, [])
        self.assertEqual(status, 200)

    @mock.patch('urllib2.urlopen')
    def test_scout_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib2.URLError("")
        url, content, status, ts_start, ts_end = self.scout_instance.scout(
            ("127.0.0.1", "8080"))
        self.assertTrue(isinstance(content, urllib2.URLError))
        self.assertEqual(url, self.url)
        self.assertEqual(status, -1)


class TestSwiftlmScout(unittest.TestCase):
    def setUp(self, *_args, **_kwargs):
        node_data = {'proxy_nodes': ['localhost'],
                     'proxy_bind_port': 666,
                     'secret': None}
        self.swiftlm_scout = SwiftlmScout(node_data)

    @mock.patch('urllib2.urlopen')
    def test_results(self, mock_urlopen):
        mock_urlopen.return_value.read = lambda: json.dumps({'a': 1})
        self.swiftlm_scout.path('dummya', 'proxy')
        mock_urlopen.return_value.read = lambda: json.dumps({'b': 2})
        self.swiftlm_scout.path('dummyb', 'proxy')
        results = self.swiftlm_scout.get_results()
        self.assertEqual(results, {'dummya': {'localhost': {'a': 1}},
                                   'dummyb': {'localhost': {'b': 2}}})


class TestSwiftlmScoutGetHostByIp(unittest.TestCase):
    def setUp(self, *_args, **_kwargs):
        node_data = {'proxy_nodes': ['0.0.0.0'],
                     'proxy_bind_port': 666,
                     'secret': None}
        self.swiftlm_scout = SwiftlmScout(node_data)

    @mock.patch('urllib2.urlopen')
    def test_results(self, mock_urlopen):
        mock_urlopen.return_value.read = lambda: json.dumps({'a': 1})
        self.swiftlm_scout.path('dummya', 'proxy')
        results = self.swiftlm_scout.get_results()
        self.assertTrue('errors' in results)

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


import unittest
from mock import Mock, patch

from swiftlm.systems import system
from swiftlm.utils.values import Severity
from swiftlm.utils.utility import CommandResult
from swiftlm.utils.metricdata import MetricData, CheckFailure


class TestSystem(unittest.TestCase):

    def p(self, name, mock):
        p = patch(name, mock)
        p.start()
        self.addCleanup(p.stop)

    def setUp(self):
        self.p('swiftlm.systems.system.BASE_RESULT.dimensions', {})
        self.p('swiftlm.utils.metricdata.get_base_dimensions', lambda *a: {})
        self.p('swiftlm.utils.metricdata.timestamp', lambda *a: 123456)

    def test_load_avg(self):
        mock_command = Mock()
        mock_command.return_value = '2.15 1.81 1.69 2/1570 29660\n'

        with patch('swiftlm.systems.system._get_proc_file', mock_command):
            actual = system.get_load_average()

        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), 1)
        r = actual[0]
        self.assertIsInstance(r, MetricData)

        expected = MetricData.single('load.host.val.five', value=1.81)
        self.assertEqual(r, expected)

    def test_main(self):
        # As functions are added, extend this to check that main calls them
        with patch('swiftlm.systems.system.get_load_average', lambda: ['a']):
            actual = system.main()
        self.assertListEqual(['a'], actual)

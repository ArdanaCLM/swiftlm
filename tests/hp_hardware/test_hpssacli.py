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


import unittest
import mock
import pprint

from swiftlm.hp_hardware import hpssacli
from swiftlm.utils.metricdata import MetricData
from swiftlm.utils.utility import CommandResult
from swiftlm.utils.values import Severity

from tests.data.hpssacli_data import *


class TestHpssacli(unittest.TestCase):

    def setUp(self):
        mock_metricdata_timestamp = mock.Mock()
        mock_metricdata_timestamp.return_value = 123456
        p = mock.patch('swiftlm.utils.metricdata.timestamp',
                       mock_metricdata_timestamp)
        p.start()
        self.addCleanup(p.stop)

        p = mock.patch('swiftlm.hp_hardware.hpssacli.BASE_RESULT.dimensions',
                       {})
        p.start()
        self.addCleanup(p.stop)

    def check_metrics(self, expected, metrics):
        # Checks that the expected metric exists in the metrics
        # list.
        # returns the metrics list with expected removed if it does
        # otherwise fails the test.
        for m in metrics:
            if m == expected:
                metrics.remove(m)
                return metrics

        pprint.pprint('Expected')
        pprint.pprint(expected.metric())

        pprint.pprint('Actual')
        for m in metrics:
            pprint.pprint(m.metric())
        self.fail('did not find %s in metrics %s' %
                  (repr(expected), str(metrics)))

    def test_get_info_hpssacli_error(self):
        # All of the get_*_info functions use the same hpssacli error handling
        # code. Do a generic test here.
        def do_it(func, metric_name, slot_used):
            # Test first failure condition.
            # could be anything from hpssacli is missing to insufficent
            # privileges
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(1, 'error')
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                if slot_used == "N/A":
                    with self.assertRaises(Exception) as context:
                        func()
                    self.assertTrue(context.exception.message.endswith(
                        'error: hpssacli ctrl all show detail failed with '
                        'exit code: 1'))

                elif metric_name is 'physical_drive':
                    with self.assertRaises(Exception) as context:
                        func(slot_used)
                    self.assertTrue(context.exception.message.endswith(
                        'error: hpssacli ctrl slot=1 pd all show detail '
                        'failed with exit code: 1'))

                elif metric_name is 'logical_drive':
                    with self.assertRaises(Exception) as context:
                        func(slot_used)
                    self.assertTrue(context.exception.message.endswith(
                        'error: hpssacli ctrl slot=1 ld all show detail '
                        'failed with exit code: 1'))

            # Test error output greater than 1913 characters. Output
            # should be truncated to the command text plus a preceding
            # ellipsis plus the error output for a total of 1903 or
            # 1913 characters
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(1, 'error'*500)
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                if slot_used == "N/A":
                    with self.assertRaises(Exception) as context:
                        func()
                    self.assertTrue(context.exception.message.endswith(
                        'hpssacli ctrl all show detail failed with '
                        'exit code: 1'))
                    self.assertTrue(len(context.exception.message) == 1903)

                elif metric_name is 'physical_drive':
                    with self.assertRaises(Exception) as context:
                        func(slot_used)
                    self.assertTrue(context.exception.message.endswith(
                        'hpssacli ctrl slot=1 pd all show detail failed '
                        'with exit code: 1'))
                    self.assertTrue(len(context.exception.message) == 1913)

                elif metric_name is 'logical_drive':
                    with self.assertRaises(Exception) as context:
                        func(slot_used)
                    self.assertTrue(context.exception.message.endswith(
                        'hpssacli ctrl slot=1 ld all show detail failed '
                        'with exit code: 1'))
                    self.assertTrue(len(context.exception.message) == 1913)

            # Test hpssacli providing no output. Exception is thrown
            # in the case that the controller returns a nonzero exit code
            # with the exit code and blank error output
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(0, '')
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                if slot_used == "N/A":
                    with self.assertRaises(Exception) as context:
                        func()
                    self.assertTrue(context.exception.message.endswith(
                        'hpssacli ctrl all show detail failed with '
                        'exit code: 0'))
                    self.assertTrue(len(context.exception.message) == 56)

                elif metric_name is 'physical_drive':
                    with self.assertRaises(Exception) as context:
                        func(slot_used)
                    self.assertTrue(context.exception.message.endswith(
                        'hpssacli ctrl slot=1 pd all show detail failed '
                        'with exit code: 0'))
                    self.assertTrue(len(context.exception.message) == 66)

                elif metric_name is 'logical_drive':
                    with self.assertRaises(Exception) as context:
                        func(slot_used)
                    self.assertTrue(context.exception.message.endswith(
                        'hpssacli ctrl slot=1 ld all show detail failed '
                        'with exit code: 0'))
                    self.assertTrue(len(context.exception.message) == 66)

        t_slot = "1"

        for test in (
                (hpssacli.get_physical_drive_info, 'physical_drive', t_slot),
                (hpssacli.get_logical_drive_info, 'logical_drive', t_slot),
                (hpssacli.get_controller_info, 'smart_array', "N/A"),):
            do_it(*test)

    def test_get_physical_drive_info(self):
        # List of tuples.
        # t[0] = Data set that hpssacli should return
        # t[1] = Tuple(Severity, Message, Status)
        tests = [
            (PHYSICAL_DRIVE_DATA, (Severity.ok, 'OK', 'OK')),
            (PHYSICAL_DRIVE_STATUS_FAIL, (
                Severity.fail,
                'Drive YFJMHTZD: 1:1 has status: Fail',
                'Fail'))
        ]

        test_slot = "1"

        for test_data, expected_metrics in tests:
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(0, test_data)
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                actual = hpssacli.get_physical_drive_info(test_slot)

            self.assertIsInstance(actual, list)
            self.assertTrue(len(actual), 1)
            r = actual[0]

            self.assertIsInstance(r, MetricData)

            expected = MetricData.single(
                hpssacli.__name__ + '.physical_drive',
                expected_metrics[0],  # Severity
                expected_metrics[1],   # Message
                {'box': '1', 'bay': '1', 'component': 'physical_drive',
                 'controller_slot': '1'})

            self.assertEqual(r, expected)

    def test_get_multiple_physical_drive_info(self):
        # List of test data, and severity
        # t[0] = Data set that hpssacli should return
        # t[1] = Severity
        tests = [
            (MULTIPLE_PHYSICAL_DRIVE_DATA, Severity.ok),
            (MULTIPLE_PHYSICAL_DRIVE_STATUS_FAIL, Severity.fail)
        ]

        test_slot = "1"

        for test_data, expected_metrics in tests:
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(0, test_data)
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                actual = hpssacli.get_physical_drive_info(test_slot)

            self.assertIsInstance(actual, list)
            self.assertEqual(len(actual), 2)

            # Simply check that test drives match expected drives
            expected_drives = [MetricData.single(
                hpssacli.__name__ + '.physical_drive',
                Severity.ok, 'OK',
                {'box': '1', 'bay': '1', 'component': 'physical_drive',
                 'controller_slot': '1'}),
                MetricData.single(
                hpssacli.__name__ + '.physical_drive',
                Severity.ok, 'OK',
                {'box': '1', 'bay': '2', 'component': 'physical_drive',
                 'controller_slot': '1'})]

            # Base case of not changing value
            if expected_metrics is Severity.ok:
                for drive in expected_drives:
                    actual = self.check_metrics(drive, actual)
                self.assertFalse(actual,
                                 'Got more metrics than expected')

            # Change values for each drive and check
            elif expected_metrics is Severity.fail:
                drive = None
                new_drives = []

                for drive in expected_drives:
                    drive.value = Severity.fail
                    drive.msgkey('status', 'Fail')
                    drive._message = (hpssacli.BASE_RESULT.messages
                                      ['physical_drive'])
                    new_drives.append(drive)

                for drive in new_drives:
                    # Now align serial numbers in example data
                    # after the failure patch
                    if drive.__getitem__('bay') is '1':
                        drive.msgkey('serial_number', 'YFJMHTZD')
                    elif drive.__getitem__('bay') is '2':
                        drive.msgkey('serial_number', 'YFJMHTDZ')
                    actual = self.check_metrics(drive, actual)
                self.assertFalse(actual,
                                 'Got more metrics than expected')

    def test_get_logical_drive_info(self):
        # Test that normal output and bugged output give exactly
        # the same results
        mock_command = mock.Mock()
        test_slot = "1"
        mock_command.return_value = CommandResult(0, LOGICAL_DRIVE_DATA)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                        mock_command):
            data_1 = hpssacli.get_logical_drive_info(test_slot)

        self.assertIsInstance(data_1, list)
        self.assertEqual(len(data_1), 2)

        mock_command = mock.Mock()
        mock_command.return_value = CommandResult(0, LOGICAL_DRIVE_DATA_BUGGED)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                        mock_command):
            data_2 = hpssacli.get_logical_drive_info(test_slot)

        self.assertIsInstance(data_2, list)
        self.assertEqual(len(data_2), 2)

        # Check the data is the same for both
        for d in data_1:
            data_2 = self.check_metrics(d, data_2)

        # Check data is as expected.
        expected_lun = MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive', 'sub_component': 'lun_status',
             'controller_slot': '1', 'array': 'L', 'logical_drive': '12'})
        data_1 = self.check_metrics(expected_lun, data_1)

        expected_cache = MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive', 'sub_component': 'cache_status',
             'controller_slot': '1', 'array': 'L', 'logical_drive': '12'})
        data_1 = self.check_metrics(expected_cache, data_1)

        self.assertFalse(data_1, 'Got more metrics than expected with'
                         'LOGICAL_DRIVE_DATA')
        self.assertFalse(data_2, 'Got more metrics than expected with'
                         'LOGICAL_DRIVE_DATA_BUGGED')

    def test_get_logical_drive_info_failures(self):
        tests = [
            (LOGICAL_DRIVE_LUN_FAIL, 'lun_status'),
            (LOGICAL_DRIVE_CACHE_FAIL, 'cache_status')
        ]

        test_slot = "1"
        for test_data, failed_component in tests:
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(0, test_data)
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                actual = hpssacli.get_logical_drive_info(test_slot)

            expected_lun = MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'L',
                 'logical_drive': '12',
                 'sub_component': 'lun_status'})

            expected_cache = MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'L',
                 'logical_drive': '12',
                 'sub_component': 'cache_status'})

            if expected_lun['sub_component'] == failed_component:
                expected_lun.value = Severity.fail
                expected_lun.msgkey('status', 'Fail')
                expected_lun._message = (hpssacli.BASE_RESULT.messages
                                         ['l_drive'])

            if expected_cache['sub_component'] == failed_component:
                expected_lun.msgkey('caching', 'Disabled')

            actual = self.check_metrics(expected_lun, actual)

            if expected_cache['sub_component'] == failed_component:
                expected_cache.value = Severity.fail
                expected_cache.msgkey('caching', 'Disabled')
                expected_cache._message = (hpssacli.BASE_RESULT.messages
                                           ['l_cache'])

            if expected_lun['sub_component'] == failed_component:
                expected_cache.msgkey('status', 'Fail')

            actual = self.check_metrics(expected_cache, actual)

            self.assertFalse(actual, 'Got more metrics than expected')

    def test_get_multiple_logical_drive_info(self):
        # Test that normal output and bugged output give exactly
        # the same results
        mock_command = mock.Mock()
        test_slot = "1"
        mock_command.return_value = CommandResult(
            0, MULTIPLE_LOGICAL_DRIVE_DATA)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                        mock_command):
            data_1 = hpssacli.get_logical_drive_info(test_slot)

        self.assertIsInstance(data_1, list)
        self.assertEqual(len(data_1), 8)

        mock_command = mock.Mock()
        mock_command.return_value = CommandResult(
            0, MULTIPLE_LOGICAL_DRIVE_DATA_BUGGED)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                        mock_command):
            data_2 = hpssacli.get_logical_drive_info(test_slot)

        self.assertIsInstance(data_2, list)
        self.assertEqual(len(data_2), 8)

        # Check the data is the same for both
        for d in data_1:
            data_2 = self.check_metrics(d, data_2)

        # Define two luns in OK status as basis of tests
        expected_luns = [MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'M',
             'logical_drive': '15',
             'sub_component': 'lun_status'}),
            MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'M',
             'logical_drive': '15',
             'sub_component': 'cache_status'}),
            MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'M',
             'logical_drive': '14',
             'sub_component': 'lun_status'}),
            MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'M',
             'logical_drive': '14',
             'sub_component': 'cache_status'}),
            MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'L',
             'logical_drive': '13',
             'sub_component': 'lun_status'}),
            MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'L',
             'logical_drive': '13',
             'sub_component': 'cache_status'}),
            MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'L',
             'logical_drive': '12',
             'sub_component': 'lun_status'}),
            MetricData.single(
            hpssacli.__name__ + '.logical_drive',
            Severity.ok, 'OK',
            {'component': 'logical_drive',
             'controller_slot': '1', 'array': 'L',
             'logical_drive': '12',
             'sub_component': 'cache_status'})]

        # These luns should match tests data
        for lun in expected_luns:
            data_1 = self.check_metrics(lun, data_1)

        self.assertFalse(data_1, 'Got more metrics than expected with '
                         'MULTIPLE_LOGICAL_DRIVE_DATA')
        self.assertFalse(data_2, 'Got more metrics than expected with '
                         'MULTIPLE_LOGICAL_DRIVE_DATA_BUGGED')

    def test_get_multiple_logical_drive_info_failures(self):
        tests = [
            (MULTIPLE_LOGICAL_DRIVE_LUN_FAIL, 'lun_status'),
            (MULTIPLE_LOGICAL_DRIVE_CACHE_FAIL, 'cache_status')
        ]

        test_slot = "1"

        for test_data, failed_component in tests:
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(0, test_data)
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                actual = hpssacli.get_logical_drive_info(test_slot)

            # Define four luns in OK status as basis of tests
            expected_luns = [MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'M',
                 'logical_drive': '15',
                 'sub_component': 'lun_status'}),
                MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'M',
                 'logical_drive': '15',
                 'sub_component': 'cache_status'}),
                MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'M',
                 'logical_drive': '14',
                 'sub_component': 'lun_status'}),
                MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'M',
                 'logical_drive': '14',
                 'sub_component': 'cache_status'}),
                MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'L',
                 'logical_drive': '13',
                 'sub_component': 'lun_status'}),
                MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'L',
                 'logical_drive': '13',
                 'sub_component': 'cache_status'}),
                MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'L',
                 'logical_drive': '12',
                 'sub_component': 'lun_status'}),
                MetricData.single(
                hpssacli.__name__ + '.logical_drive',
                Severity.ok, 'OK',
                {'component': 'logical_drive',
                 'controller_slot': '1', 'array': 'L',
                 'logical_drive': '12',
                 'sub_component': 'cache_status'})]

            # Change two dimensions in two cases, lun status
            # then cache status for each of two luns
            if failed_component is 'lun_status':
                new_luns = []
                for lun in expected_luns:
                    if lun['sub_component'] == failed_component:
                        lun.value = Severity.fail
                        lun.msgkey('status', 'Fail')
                        lun._message = (hpssacli.BASE_RESULT.messages
                                        ['l_drive'])
                    new_luns.append(lun)

                for lun in new_luns:
                    actual = self.check_metrics(lun, actual)
                self.assertFalse(actual,
                                 'Got more metrics than expected')

            elif failed_component is 'cache_status':
                new_luns = []
                for lun in expected_luns:
                    if lun['sub_component'] == failed_component:
                        lun.value = Severity.fail
                        lun.msgkey('status', 'Disabled')
                        lun._message = (hpssacli.BASE_RESULT.messages
                                        ['l_cache'])
                    new_luns.append(lun)

                for lun in new_luns:
                    actual = self.check_metrics(lun, actual)
                self.assertFalse(actual,
                                 'Got more metrics than expected')

    def test_get_logical_drive_info_ssd(self):
        # If the physical drive is an ssd the caching on the
        # logical drive can be disabled
        # Ensuring this is accepted
        mock_command = mock.Mock()
        test_slot = "1"
        mock_command.return_value = CommandResult(0, LOGICAL_DRIVE_SSD)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                        mock_command):
            data_1 = hpssacli.get_logical_drive_info(test_slot)

        self.assertIsInstance(data_1, list)
        self.assertEqual(len(data_1), 2)
        self.assertEqual(data_1[0].value, 0)
        self.assertEqual(data_1[1].value, 0)

    def test_get_controller_info(self):
        expected_base = MetricData(
            name=hpssacli.__name__ + '.smart_array',
            messages=hpssacli.BASE_RESULT.messages,
            dimensions={
                'model': 'Smart Array P410',
                'controller_slot': '1',
                'component': 'controller',
            })

        # List of tuples.
        # t[0] = Data set that hpssacli should return
        # t[1] = The failed component in the test data
        tests = [
            (SMART_ARRAY_DATA, []),
            (SMART_ARRAY_CACHE_FAIL, ['cache_status']),
            (SMART_ARRAY_BATTERY_FAIL, ['battery_capacitor_status']),
            (SMART_ARRAY_CONTROLLER_FAIL, ['controller_status']),
            (SMART_ARRAY_BATTERY_PRESENCE_FAIL,
                ['battery_capacitor_presence']),
        ]

        for test_data, failures in tests:
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(0, test_data)
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                actual, actual_slots = hpssacli.get_controller_info()

            self.assertIsInstance(actual, list)
            self.assertEqual(len(actual), 6)

            expected_firmware = expected_base.child('firmware')
            expected_firmware.value = 6.60
            actual = self.check_metrics(expected_firmware, actual)

            expected_hba_mode = expected_base.child(dimensions={
                'sub_component': 'controller_not_hba_mode'})
            expected_hba_mode.value = Severity.ok
            actual = self.check_metrics(expected_hba_mode, actual)

            bcp = 'battery_capacitor_presence'
            if bcp in failures:
                expected_battery_presence = expected_base.child(dimensions={
                    'sub_component': bcp})
                expected_battery_presence.value = Severity.fail
                expected_battery_presence.message = 'no_battery'
            else:
                expected_battery_presence = expected_base.child(dimensions={
                    'sub_component': bcp})
                expected_battery_presence.value = Severity.ok

            actual = self.check_metrics(expected_battery_presence, actual)

            for submetric in ('battery_capacitor_status',
                              'controller_status', 'cache_status'):
                if submetric in failures:
                    expected_status = expected_base.child(dimensions={
                        'sub_component': submetric},
                        msgkeys={'status': 'Fail'})
                    expected_status.value = Severity.fail
                    expected_status.message = 'controller_status'
                else:
                    expected_status = expected_base.child(dimensions={
                        'sub_component': submetric},
                        msgkeys={'status': 'OK'})
                    expected_status.value = Severity.ok

                actual = self.check_metrics(expected_status, actual)

            self.assertFalse(actual, 'Got more metrics than expected')

    def test_get_smart_array_info(self):
        expected_base = MetricData(
            name=hpssacli.__name__ + '.smart_array',
            messages=hpssacli.BASE_RESULT.messages,
            dimensions={
                'model': 'Smart Array P410',
                'controller_slot': '1',
                'component': 'controller',
            })

        # List of tuples.
        # t[0] = Data set that hpssacli should return
        # t[1] = The failed component in the test data
        tests = [
            (SMART_ARRAY_DATA, []),
            (SMART_ARRAY_CACHE_FAIL, ['cache_status']),
            (SMART_ARRAY_BATTERY_FAIL, ['battery_capacitor_status']),
            (SMART_ARRAY_CONTROLLER_FAIL, ['controller_status']),
            (SMART_ARRAY_BATTERY_PRESENCE_FAIL,
                ['battery_capacitor_presence']),
        ]

        for test_data, failures in tests:
            mock_command = mock.Mock()
            mock_command.return_value = CommandResult(0, test_data)
            with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                            mock_command):
                actual, actual_slots = hpssacli.get_smart_array_info()

            self.assertIsInstance(actual, list)
            self.assertEqual(len(actual), 6)

            expected_firmware = expected_base.child('firmware')
            expected_firmware.value = 6.60
            actual = self.check_metrics(expected_firmware, actual)

            expected_hba_mode = expected_base.child(dimensions={
                'sub_component': 'controller_not_hba_mode'})
            expected_hba_mode.value = Severity.ok
            actual = self.check_metrics(expected_hba_mode, actual)

            bcp = 'battery_capacitor_presence'
            if bcp in failures:
                expected_battery_presence = expected_base.child(dimensions={
                    'sub_component': bcp})
                expected_battery_presence.value = Severity.fail
                expected_battery_presence.message = 'no_battery'
            else:
                expected_battery_presence = expected_base.child(dimensions={
                    'sub_component': bcp})
                expected_battery_presence.value = Severity.ok

            actual = self.check_metrics(expected_battery_presence, actual)

            for submetric in ('battery_capacitor_status',
                              'controller_status', 'cache_status'):
                if submetric in failures:
                    expected_status = expected_base.child(dimensions={
                        'sub_component': submetric},
                        msgkeys={'status': 'Fail'})
                    expected_status.value = Severity.fail
                    expected_status.message = 'controller_status'
                else:
                    expected_status = expected_base.child(dimensions={
                        'sub_component': submetric},
                        msgkeys={'status': 'OK'})
                    expected_status.value = Severity.ok

                actual = self.check_metrics(expected_status, actual)

            self.assertFalse(actual, 'Got more metrics than expected')

    def test_get_controller_slot_count(self):

        # Expect to get 3 slots returned, slot 1, 3, & 0
        expected_slots = ["1", "3", "0"]

        test_data = SMART_ARRAY_DATA_3_CONT

        mock_command = mock.Mock()
        mock_command.return_value = CommandResult(0, test_data)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd', mock_command):
            actual, actual_slots = hpssacli.get_controller_info()

        self.assertEqual(len(actual_slots), 3)
        self.assertEqual(expected_slots, actual_slots)

    def test_smart_array_failed_cache(self):

        # expects to see one set of data with cache status failed
        # no cache status data in second set of data
        test_data = SMART_ARRAY_DATA_FAILED_CACHE

        mock_command = mock.Mock()
        mock_command.return_value = CommandResult(0, test_data)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd', mock_command):
            actual, actual_slots = hpssacli.get_controller_info()

        self.assertEqual(len(actual_slots), 2)

    def test_get_controller_info_smart_hba(self):

        # Expects to see one set of data which begins with Smart HBA
        test_data = SMART_HBA_DATA

        mock_command = mock.Mock()
        mock_command.return_value = CommandResult(0, test_data)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd', mock_command):
            actual, actual_slots = hpssacli.get_controller_info()
        model = actual[0].dimensions['model']

        self.assertEqual(model, 'Smart HBA H240')
        self.assertEqual(len(actual_slots), 1)

    def test_controller_in_hba_mode(self):
        expected_base = MetricData(
            name=hpssacli.__name__ + '.smart_array',
            messages=hpssacli.BASE_RESULT.messages,
            dimensions={
                'model': 'Smart Array P840ar',
                'controller_slot': '0',
                'component': 'controller',
            })
        expected_slots = ["0"]
        test_data = HBA_MODE_CONTROLLERS

        mock_command = mock.Mock()
        mock_command.return_value = CommandResult(0, test_data)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd', mock_command):
            actual, actual_slots = hpssacli.get_controller_info()

        self.assertEqual(len(actual_slots), 1)
        self.assertEqual(expected_slots, actual_slots)

        expected_firmware = expected_base.child('firmware')
        expected_firmware.value = 3.56
        actual = self.check_metrics(expected_firmware, actual)

        expected_hba_mode = expected_base.child(dimensions={
            'sub_component': 'controller_not_hba_mode'})
        expected_hba_mode.value = Severity.fail
        expected_hba_mode.message = 'in_hba_mode'
        actual = self.check_metrics(expected_hba_mode, actual)

        self.assertFalse(actual, 'Got more metrics than expected')

    def test_error_no_luns(self):
        mock_command = mock.Mock()
        test_slot = "0"
        mock_command.return_value = CommandResult(0, HBA_MODE_LD)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                        mock_command):
            results = hpssacli.get_logical_drive_info(test_slot)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_2_40_13_get_physical_drive_info(self):
        mock_command = mock.Mock()
        test_slot = "0"
        mock_command.return_value = CommandResult(0, HPSSACLI_2_14_14_PD_SHOW)
        with mock.patch('swiftlm.hp_hardware.hpssacli.run_cmd',
                        mock_command):
            results = hpssacli.get_physical_drive_info(test_slot)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 4)


class TestParsing(unittest.TestCase):

    def test_parse_pd_block(self):
        MULTIPLE_PHYSICAL_DRIVE_DATA = """
Controller 1 text here

   Array A

     physical drive 1
        Status: OK
        Slot: 2

     physical drive 2
        Status: BAD

Controller 2

   Unassigned

      pd 3
         Status: Another
         Something Else: has bogus
         wrapping

Controller 3 text here
  With: own attributes
  Here: and here
        """
        expected = ['.Controller 1 text here',
                    '..Array A',
                    '...physical drive 1',
                    '....Status: OK',
                    '....Slot: 2',
                    '...physical drive 2',
                    '....Status: BAD',
                    '.Controller 2',
                    '..Unassigned',
                    '...pd 3',
                    '....Status: Another',
                    '....Something Else: has bogus',
                    '....wrapping',
                    '.Controller 3 text here',
                    '..With: own attributes',
                    '..Here: and here']

        text_scanner = hpssacli.TextScanner(
            MULTIPLE_PHYSICAL_DRIVE_DATA.split('\n'))
        block = text_scanner.get_root_block()
        result = []
        for sb in block.subblocks:
            result.append('.%s' % sb.text)
            for sbb in sb.subblocks:
                result.append('..%s' % sbb.text)
                for sbbb in sbb.subblocks:
                    result.append('...%s' % sbbb.text)
                    for sbbbb in sbbb.subblocks:
                        result.append('....%s' % sbbbb.text)
        self.assertEqual(expected, result)

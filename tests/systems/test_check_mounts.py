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


import os
from shutil import rmtree
import socket
import tempfile
import unittest
import json
import time

import six
import mock
from mock import Mock
from mock import patch

from swiftlm.systems import check_mounts
from swiftlm.utils.metricdata import MetricData
from swiftlm.utils.values import Severity
from swiftlm.utils.utility import SwiftlmCheckFailure

if six.PY2:
    BUILTIN_OPEN = '__builtin__.open'
    COMMANDS_MODULE = 'commands'
else:
    BUILTIN_OPEN = 'builtins.open'
    COMMANDS_MODULE = 'subprocess'


def make_fake_os_stat(fake_returns):
    def fake_os_stat(path):
        return Mock(**fake_returns[path])
    return fake_os_stat


def make_fake_is_mount(mounts):
    def fake_ismount(mount_path):
        return mounts.get(mount_path, False)
    return fake_ismount


def make_fake_getpwuid(names):
    def fake_getpwuid(uid):
        return Mock(pw_name=names[uid])
    return fake_getpwuid


def make_fake_getgrgid(names):
    def fake_getgrgid(gid):
        return Mock(gr_name=names[gid])
    return fake_getgrgid


class TestCheckMounts(unittest.TestCase):

    @patch('os.stat')
    @patch('pwd.getpwuid')
    @patch('grp.getgrgid')
    def test_is_ug_swift(self, mock_gid, mock_uid, mock_stat):
        d = check_mounts.Device('/dev/sd#', '/srv/node/disk#', 'label#')
        mock_gid.return_value = Mock(gr_name='swift')
        mock_uid.return_value = Mock(pw_name='swift')
        response = {}
        self.assertTrue(check_mounts.is_ug_swift(d, response))
        self.assertDictEqual(response, {})

        mock_gid.return_value = Mock(gr_name='not-swift')
        mock_uid.return_value = Mock(pw_name='swift')
        response = {}
        self.assertFalse(check_mounts.is_ug_swift(d, response))
        self.assertDictEqual(response, {'user': 'swift', 'group': 'not-swift'})

        mock_gid.return_value = Mock(gr_name='swift')
        mock_uid.return_value = Mock(pw_name='not-swift')
        response = {}
        self.assertFalse(check_mounts.is_ug_swift(d, response))
        self.assertDictEqual(response, {'user': 'not-swift', 'group': 'swift'})

        mock_gid.return_value = Mock(gr_name='not-swift')
        mock_uid.return_value = Mock(pw_name='not-swift')
        response = {}
        self.assertFalse(check_mounts.is_ug_swift(d, response))
        self.assertDictEqual(
            response,
            {'user': 'not-swift', 'group': 'not-swift'}
        )

    @patch('os.stat')
    def test_is_mounted_775(self, mock_stat):
        d = check_mounts.Device('/dev/sd#', '/srv/node/disk#', 'label#')
        mock_stat.return_value = Mock(st_mode=16877)  # oct(16877) = 040775
        self.assertTrue(check_mounts.is_mounted_775(d, {}))

        mock_stat.return_value = Mock(st_mode=16804)  # oct(16804) = 040644
        response = {}
        self.assertFalse(check_mounts.is_mounted_775(d, response))
        self.assertDictEqual(response, {'permissions': '644'})

    def test_get_devices(self):
        j = '''{
        "model": "Standard PC (i440FX + PIIX, 1996)",
        "hostname": "PADAWANBASE-CCP-T1-M1-NETCLM",
        "ip_addr": "192.168.245.4",
        "devices": [
            {
                "size_gb": 18.625,
                "mounted": "True",
                "name": "/dev/sdb1",
                "swift_drive_name": "disk0"
            },
            {
                "size_gb": 18.625,
                "mounted": "True",
                "name": "/dev/sdc1",
                "swift_drive_name": "disk1"
            }
        ]
        }
        '''
        expected = [
            check_mounts.Device(
                '/dev/sdb1',
                '/srv/node/disk0'),
            check_mounts.Device(
                '/dev/sdc1',
                '/srv/node/disk1'),
        ]

        with tempfile.NamedTemporaryFile('w+') as f:
            f.write(j)
            f.flush()
            f.seek(0)

            mock_open = mock.MagicMock(spec=BUILTIN_OPEN)
            handle = mock.MagicMock()
            handle.__enter__.return_value = f
            mock_open.return_value = handle

            with mock.patch(BUILTIN_OPEN, mock_open):
                actual = check_mounts.get_devices()

        self.assertEqual(expected, actual)


class TestCheckMounts(unittest.TestCase):

    def p(self, name, mock):
        p = patch(name, mock)
        p.start()
        self.addCleanup(p.stop)

    def setUp(self):
        self.testdir = tempfile.mkdtemp()

        self.fake_devices_file = os.path.join(self.testdir, 'devices')

        self.p('swiftlm.systems.check_mounts.DEVICES', self.fake_devices_file)
        self.p('swiftlm.utils.metricdata.timestamp', lambda: 123456)
        self.p('swiftlm.utils.metricdata.get_base_dimensions', lambda: {})
        self.p('swiftlm.systems.check_mounts.BASE_RESULT.dimensions', {})
        self.p('swiftlm.systems.check_mounts.MOUNT_PATH', '')

        self.expected_metric_base = {
            'metric': 'swiftlm.systems.check_mounts',
            'dimensions': {},
            'timestamp': 123456
        }

    def tearDown(self):
        rmtree(self.testdir)

    def _make_devices(self, devs):
        results = {}
        with open(self.fake_devices_file, 'wb') as f:
            j = {'devices': []}

            for dev_no, dev in enumerate(devs):
                dev_path = os.path.join(self.testdir, 'dev', dev)
                mnt_path = 'disk' + str(dev_no)
                dev_info = {
                    'device': dev_path,
                    'label': check_mounts.LABEL_CHECK_DISABLED,
                    'mount': os.path.join(self.testdir, 'mnt', mnt_path)
                }
                results[dev] = dev_info
                j['devices'].append({
                    'name': dev_path,
                    'swift_drive_name':
                    os.path.join(self.testdir, 'mnt', mnt_path)})

            json.dump(j, f)
        return results

    def test_no_devices_found(self):
        # Unit tests have no access to /etc/ files
        self.assertRaises(SwiftlmCheckFailure, check_mounts.check_mounts)

    def test_not_mounted(self):
        dev_info = self._make_devices(('sdd', 'sde'))
        expected = []
        for dev in dev_info:
            expected_value_meta = dict(
                msg='{device} not mounted at {mount}'.format(**dev_info[dev]))
            expected_metric = dict(self.expected_metric_base)
            expected_metric.update(dict(dimensions={'mount':
                                                    dev_info[dev]['mount']},
                                        value=Severity.fail,
                                        value_meta=expected_value_meta))
            expected.append(expected_metric)

        actual = check_mounts.check_mounts()

        self.assertEqual(2, len(actual))
        for metric_data in actual:
            self.assertTrue(metric_data.metric() in expected)
            expected.remove(metric_data.metric())
        self.assertFalse(expected)

    def test_not_mounted_with_775_perms(self):

        dev_info = self._make_devices(('sdd', 'sde'))
        # sdd is not mounted,
        # sde is mounted but has wrong perms
        fake_is_mount = make_fake_is_mount(
            {dev_info['sde']['mount']: True})
        # oct(16804) = 040644
        fake_os_stat = make_fake_os_stat(
            {dev_info['sde']['mount']: dict(st_mode=16804)})

        expected = []
        # sdd
        expected_value_meta = dict(
            msg='{device} not mounted at {mount}'.format(**dev_info['sdd']))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sdd']['mount']},
                                    value=Severity.fail,
                                    value_meta=expected_value_meta))
        expected.append(expected_metric)
        # sde
        msg = '{device} mounted at {mount} has permissions 644 not 755'
        expected_value_meta = dict(msg=msg.format(**dev_info['sde']))
        dev_info['sde'].update(dict(permissions='644'))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sde']['mount']},
                                    value=Severity.fail,
                                    value_meta=expected_value_meta))
        expected.append(expected_metric)

        # avoid ridiculous nesting...
        @mock.patch('os.path.ismount', fake_is_mount)
        @mock.patch('os.stat', fake_os_stat)
        def do_it(*args):
            actual = check_mounts.check_mounts()

            self.assertEqual(2, len(actual))
            for metric_data in actual:
                metric = metric_data.metric()
                self.assertTrue(metric in expected,
                                'Unexpected metric %s\n not found in\n %s'
                                % (metric, expected))
                expected.remove(metric)
            self.assertFalse(expected)
        do_it()

    def test_not_ug_swift(self):

        dev_info = self._make_devices(('sdd', 'sde'))
        # sdd is mounted, correct perms but wrong user group
        # sde is mounted but has wrong perms
        fake_is_mount = make_fake_is_mount(
            {dev_info['sdd']['mount']: True,
             dev_info['sde']['mount']: True})
        fake_os_stat = make_fake_os_stat(
            # oct(16877) = 040775, oct(16804) = 040644
            {dev_info['sdd']['mount']: dict(st_mode=16877,
                                            st_uid=1000,
                                            st_gid=1001),
             dev_info['sde']['mount']: dict(st_mode=16804)})
        fake_getpwuid = make_fake_getpwuid({1000: 'not-swift'})
        fake_getgrgid = make_fake_getgrgid({1001: 'not-swift'})

        expected = []
        # sdd
        dev_info['sdd'].update({'user': 'not-swift', 'group': 'not-swift'})
        expected_value_meta = dict(
            msg='{device} mounted at {mount} is not owned by swift, has user: '
                '{user}, group: {group}'.format(**dev_info['sdd']))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sdd']['mount']},
                                    value=Severity.fail,
                                    value_meta=expected_value_meta))
        expected.append(expected_metric)
        # sde
        msg = '{device} mounted at {mount} has permissions 644 not 755'
        expected_value_meta = dict(msg=msg.format(**dev_info['sde']))
        dev_info['sde'].update(dict(permissions='644'))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sde']['mount']},
                                    value=Severity.fail,
                                    value_meta=expected_value_meta))
        expected.append(expected_metric)

        # avoid ridiculous nesting...
        @mock.patch('os.path.ismount', fake_is_mount)
        @mock.patch('os.stat', fake_os_stat)
        @mock.patch('pwd.getpwuid', fake_getpwuid)
        @mock.patch('grp.getgrgid', fake_getgrgid)
        def do_it(*args):
            actual = check_mounts.check_mounts()

            self.assertEqual(2, len(actual))
            for metric_data in actual:
                metric = metric_data.metric()
                self.assertTrue(metric in expected,
                                'Unexpected metric %s\n not found in\n %s'
                                % (metric, expected))
                expected.remove(metric)
            self.assertFalse(expected)
        do_it()

    def test_not_valid_label(self):
        dev_info = self._make_devices(('sdd',))
        fake_is_mount = make_fake_is_mount(
            {dev_info['sdd']['mount']: True})
        fake_os_stat = make_fake_os_stat(
            # oct(16877) = 040775, oct(16804) = 040644
            {dev_info['sdd']['mount']: dict(st_mode=16877,
                                            st_uid=1000,
                                            st_gid=1001)})
        fake_getpwuid = make_fake_getpwuid({1000: 'swift'})
        fake_getgrgid = make_fake_getgrgid({1001: 'swift'})

        expected_value_meta = dict(
            msg='{device} mounted at {mount} has invalid label {label}'
            .format(**dev_info['sdd']))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sdd']['mount']},
                               value=Severity.fail,
                               value_meta=expected_value_meta))

        # avoid ridiculous nesting...
        @mock.patch('os.path.ismount', fake_is_mount)
        @mock.patch('os.stat', fake_os_stat)
        @mock.patch('pwd.getpwuid', fake_getpwuid)
        @mock.patch('grp.getgrgid', fake_getgrgid)
        @mock.patch('swiftlm.systems.check_mounts.is_valid_label',
                    return_value=False, __name__='is_valid_label')
        def do_it(*args):
            actual = check_mounts.check_mounts()
            self.assertEqual(1, len(actual))
            actual_metric = actual[0].metric()
            self.assertEqual(expected_metric, actual_metric,
                             'Unexpected metric %s' % actual_metric)
        do_it()

    def test_not_xfs(self):
        dev_info = self._make_devices(('sdd',))
        fake_is_mount = make_fake_is_mount(
            {dev_info['sdd']['mount']: True})
        fake_os_stat = make_fake_os_stat(
            # oct(16877) = 040775, oct(16804) = 040644
            {dev_info['sdd']['mount']: dict(st_mode=16877,
                                            st_uid=1000,
                                            st_gid=1001)})
        fake_getpwuid = make_fake_getpwuid({1000: 'swift'})
        fake_getgrgid = make_fake_getgrgid({1001: 'swift'})

        expected_value_meta = dict(
            msg='{device} mounted at {mount} is not XFS'
            .format(**dev_info['sdd']))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sdd']['mount']},
                                    value=Severity.fail,
                                    value_meta=expected_value_meta))

        # avoid ridiculous nesting...
        @mock.patch('os.path.ismount', fake_is_mount)
        @mock.patch('os.stat', fake_os_stat)
        @mock.patch('pwd.getpwuid', fake_getpwuid)
        @mock.patch('grp.getgrgid', fake_getgrgid)
        @mock.patch('swiftlm.systems.check_mounts.is_valid_label',
                    return_value=True, __name__='is_valid_label')
        @mock.patch('swiftlm.systems.check_mounts.is_xfs',
                    return_value=False, __name__='is_xfs')
        def do_it(*args):
            actual = check_mounts.check_mounts()

            self.assertEqual(1, len(actual))
            actual_metric = actual[0].metric()
            self.assertEqual(expected_metric, actual_metric,
                             'Unexpected metric %s' % actual_metric)
        do_it()

    def test_not_valid_xfs(self):
        dev_info = self._make_devices(('sdd',))
        fake_is_mount = make_fake_is_mount(
            {dev_info['sdd']['mount']: True})
        fake_os_stat = make_fake_os_stat(
            # oct(16877) = 040775, oct(16804) = 040644
            {dev_info['sdd']['mount']: dict(st_mode=16877,
                                            st_uid=1000,
                                            st_gid=1001)})
        fake_getpwuid = make_fake_getpwuid({1000: 'swift'})
        fake_getgrgid = make_fake_getgrgid({1001: 'swift'})

        expected_value_meta = dict(
            msg='{device} mounted at {mount} is corrupt'
            .format(**dev_info['sdd']))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sdd']['mount']},
                                    value=Severity.fail,
                                    value_meta=expected_value_meta))

        # avoid ridiculous nesting...
        @mock.patch('os.path.ismount', fake_is_mount)
        @mock.patch('os.stat', fake_os_stat)
        @mock.patch('pwd.getpwuid', fake_getpwuid)
        @mock.patch('grp.getgrgid', fake_getgrgid)
        @mock.patch('swiftlm.systems.check_mounts.is_valid_label',
                    return_value=True, __name__='is_valid_label')
        @mock.patch('swiftlm.systems.check_mounts.is_xfs',
                    return_value=True, __name__='is_xfs')
        @mock.patch('swiftlm.systems.check_mounts.is_valid_xfs',
                    return_value=False, __name__='is_valid_xfs')
        def do_it(*args):
            actual = check_mounts.check_mounts()

            self.assertEqual(1, len(actual))
            actual_metric = actual[0].metric()
            self.assertEqual(expected_metric, actual_metric,
                             'Unexpected metric %s' % actual_metric)
        do_it()

    def test_one_ok_one_corrupt(self):
        dev_info = self._make_devices(('sdd', 'sde'))
        # sdd is mounted, correct perms but wrong user group
        # sde is OK
        fake_is_mount = make_fake_is_mount(
            {dev_info['sdd']['mount']: True,
             dev_info['sde']['mount']: True})
        fake_os_stat = make_fake_os_stat(
            # oct(16877) = 040775
            {dev_info['sdd']['mount']: dict(st_mode=16877,
                                            st_uid=1000,
                                            st_gid=1001),
             dev_info['sde']['mount']: dict(st_mode=16877,
                                            st_uid=1002,
                                            st_gid=1002)})
        fake_getpwuid = make_fake_getpwuid({1000: 'not-swift', 1002: 'swift'})
        fake_getgrgid = make_fake_getgrgid({1001: 'not-swift', 1002: 'swift'})

        expected = []
        # sdd
        dev_info['sdd'].update({'user': 'not-swift', 'group': 'not-swift'})
        expected_value_meta = dict(
            msg='{device} mounted at {mount} is not owned by swift, has user: '
                '{user}, group: {group}'.format(**dev_info['sdd']))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sdd']['mount']},
                                    value=Severity.fail,
                                    value_meta=expected_value_meta))
        expected.append(expected_metric)
        # sde
        msg = '{device} mounted at {mount} ok'
        expected_value_meta = dict(msg=msg.format(**dev_info['sde']))
        expected_metric = dict(self.expected_metric_base)
        expected_metric.update(dict(dimensions={'mount':
                                                dev_info['sde']['mount']},
                                    value=Severity.ok,
                                    value_meta=expected_value_meta))
        expected.append(expected_metric)

        # avoid ridiculous nesting...
        @mock.patch('os.path.ismount', fake_is_mount)
        @mock.patch('os.stat', fake_os_stat)
        @mock.patch('pwd.getpwuid', fake_getpwuid)
        @mock.patch('grp.getgrgid', fake_getgrgid)
        @mock.patch('swiftlm.systems.check_mounts.is_valid_label',
                    return_value=True)
        @mock.patch('swiftlm.systems.check_mounts.is_xfs', return_value=True)
        @mock.patch('swiftlm.systems.check_mounts.is_valid_xfs',
                    return_value=True)
        def do_it(*args):
            actual = check_mounts.check_mounts()

            self.assertEqual(2, len(actual))
            for metric_data in actual:
                metric = metric_data.metric()
                self.assertTrue(metric in expected,
                                'Unexpected metric %s\n not found in\n %s'
                                % (metric, expected))
                expected.remove(metric)
            self.assertFalse(expected)
        do_it()


class FakeStatvfs(object):
            def __init__(self):
                self.f_bsize = 4096
                self.f_frsize = 4096
                self.f_blocks = 130048
                self.f_bfree = 47299
                self.f_bavail = 47299

fake_statvfs_result = FakeStatvfs()


class TestDiskUsage(unittest.TestCase):

    @mock.patch('os.statvfs', return_value=fake_statvfs_result)
    def test_get_diskusage(self, *args):
        expected = {'size': 532676608,
                    'used': 338939904,
                    'avail': 193736704,
                    'usage': 64.0}
        result = check_mounts.get_diskusage(check_mounts.Device('na',
                                                                'na', 'na'))
        self.assertEqual(expected, result)

    @mock.patch('os.statvfs', return_value=fake_statvfs_result)
    @mock.patch('swiftlm.systems.check_mounts.get_devices',
                return_value=[check_mounts.Device('na', 'na', 'na')])
    @mock.patch('swiftlm.utils.metricdata.timestamp', lambda: 123456)
    def test_diskusage(self, *args):
        expected = [MetricData.single('swiftlm.diskusage.host.val.size',
                                      532676608,
                                      dimensions={'mount': 'na',
                                                  'service':
                                                  'object-storage'}),
                    MetricData.single('swiftlm.diskusage.host.val.used',
                                      338939904,
                                      dimensions={'mount': 'na',
                                                  'service':
                                                  'object-storage'}),
                    MetricData.single('swiftlm.diskusage.host.val.avail',
                                      193736704,
                                      dimensions={'mount': 'na',
                                                  'service':
                                                  'object-storage'}),
                    MetricData.single('swiftlm.diskusage.host.val.usage',
                                      64.0,
                                      dimensions={'mount': 'na',
                                                  'service':
                                                  'object-storage'}),
                    MetricData.single('swiftlm.diskusage.host.max.usage',
                                      64.0,
                                      dimensions={'service':
                                                  'object-storage'}),
                    MetricData.single('swiftlm.diskusage.host.min.usage',
                                      64.0,
                                      dimensions={'service':
                                                  'object-storage'}),
                    MetricData.single('swiftlm.diskusage.host.avg.usage',
                                      64.0,
                                      dimensions={'service':
                                                  'object-storage'})]
        results = check_mounts.diskusage()
        for result in results:
            if result in expected:
                expected.remove(result)
            else:
                self.assertEqual(True, False,
                                 msg='Not expecting %s' % result.__repr__())
        self.assertEqual(0, len(expected), msg='Missing: %s' % expected)

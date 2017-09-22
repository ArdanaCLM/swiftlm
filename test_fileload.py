# (c) Copyright 2015, 2016 Hewlett Packard Enterprise Development LP
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
import os
from shutil import rmtree
import tempfile
import unittest
import errno
import mock
import time
from swiftlm.utils import utility
from swiftlm.monasca.check_plugins import swiftlm_check  # noqa
from tests import FakeLogger

TEST_MODULE = 'swiftlm.monasca.check_plugins.swiftlm_check'


def _dump_measurements(measurements):
    lines = []
    for m in measurements:
        lines.append(
            'name: %s, value: %s, %s %s %s'
            % (m.name, m.value, m.dimensions, m.timestamp, m.value_meta))
    return '\n'.join(lines)


def _make_fake_load_instance_conf(metrics_files=None, subcommands=None,
                                  suppress_ok=None):
    def _fake_load_instance_conf(self, instance):
        self.metrics_files = metrics_files or []
        self.subcommands = subcommands or []
        self.suppress_ok = suppress_ok or []
    return _fake_load_instance_conf


class TestLoadFileTasks(unittest.TestCase):
    task_name = 'swiftlm.swiftlm_scan'
    task_entry_points = []
    sub_commands = []

    def setUp(self):
        logger = FakeLogger()
        # setup a temp dir for tests
        self.testdir = tempfile.mkdtemp()
        swiftlm_check.POSTED_DIR = self.testdir
        self.fake_time = 100000
        self.check = swiftlm_check.SwiftLMScan('unit_test', '', '',
                                               instances=None, logger=logger)

    def tearDown(self):
        rmtree(self.testdir, ignore_errors=True)

    def test_run_load_file_task(self):
        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.fake_time + 2
            metrics = []
            for v, meta in ((0, 'I am ok'), (1, 'some meta'),
                            (2, 'other meta')):
                metric = dict(metric=self.task_name,
                              timestamp=self.fake_time,
                              dimensions=dict(blah='whatever',
                                              service='object-storage'),
                              value=v,
                              value_meta=dict(msg=meta))
                metrics.append(metric)

            # read ok
            metric_file = os.path.join(self.testdir, 'afile.json')
            with open(metric_file, 'wb') as f:
                json.dump(metrics, f)
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual(metrics, actual)

            # can't read a locked file
            with utility.lock_file(metric_file, unlink=False):
                with mock.patch(TEST_MODULE + '.time.sleep') as mock_sleep:
                    actual = self.check._run_load_file_task(metric_file)
            expected_metrics = []
            self.assertEqual(expected_metrics, actual)
            self.assertEqual(5, mock_sleep.call_count)
            self.assertEqual(1, len(self.check.plugin_failures))

            # ...until it is unlocked
            self.check.plugin_failures = []
            with utility.lock_file(metric_file, unlink=False):
                with mock.patch(TEST_MODULE + '.time.sleep') as mock_sleep:
                    with mock.patch(TEST_MODULE + '.fcntl.flock') as \
                            mock_flock:
                        err = IOError()
                        err.errno = errno.EWOULDBLOCK
                        # fake lock becoming available on 3rd attempt
                        mock_flock.side_effect = [err, err, None]
                        actual = self.check._run_load_file_task(metric_file)
            expected_metrics = []  # empty because of prior posted file
            self.assertEqual(expected_metrics, actual)
            # 2 sleeps for 2 IOErrors
            self.assertEqual(2, mock_sleep.call_count)
            self.assertEqual(3, mock_flock.call_count)
            self.assertEqual(0, len(self.check.plugin_failures))

    def test_metrics_duplicates_removed(self):
        metrics = []
        for v, meta in ((0, 'I am ok'), (1, 'some meta'), (2, 'other meta')):
            metric = dict(metric=self.task_name,
                          timestamp=self.fake_time,
                          dimensions=dict(blah='whatever',
                                          service='object-storage'),
                          value=v,
                          value_meta=dict(msg=meta))
            metrics.append(metric)

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.fake_time + 2

            # Write metric data
            metric_file = os.path.join(self.testdir, 'bfile.json')
            with open(metric_file, 'wb') as f:
                json.dump(metrics, f)

            # Scan once
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual(metrics, actual)

            # Scan second time -- metrics already posted
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual([], actual)

            # Write metric data with new timestamp
            for metric in metrics:
                metric['timestamp'] = self.fake_time + 1
            with open(metric_file, 'wb') as f:
                json.dump(metrics, f)

            # Scan -- get new metrics
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual(metrics, actual)

            # Scan second time -- metrics already posted
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual([], actual)

    def test_file_not_found(self):
        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.fake_time + 2
            metric_file = os.path.join(self.testdir, 'did-not-create.json')
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual([], actual)
            self.assertEqual(1, len(self.check.plugin_failures))

    def test_file_not_json(self):
        metric_file = os.path.join(self.testdir, 'not-json.json')
        with open(metric_file, 'wb') as f:
            f.write('this is not json')

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.fake_time + 2
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual([], actual)
            self.assertEqual(1, len(self.check.plugin_failures))

    def test_old_metrics_ignored(self):
        metrics = []
        for v, meta in ((0, 'I am ok'), (1, 'some meta'), (2, 'other meta')):
            metric = dict(metric=self.task_name,
                          timestamp=self.fake_time,
                          dimensions=dict(blah='whatever',
                                          service='object-storage'),
                          value=v,
                          value_meta=dict(msg=meta))
            metrics.append(metric)

        # Write metric data
        metric_file = os.path.join(self.testdir, 'cfile.json')
        with open(metric_file, 'wb') as f:
            json.dump(metrics, f)

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.fake_time + \
                swiftlm_check.METRIC_STALE_AGE + 1
            # Scan once -- no recent metrics found
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual([], actual)
            self.assertEqual(1, len(self.check.plugin_failures))

    def test_old_metrics_purged_from_posted(self):
        metrics = []
        for v, meta in ((0, 'I am ok'), (1, 'some meta'), (2, 'other meta')):
            metric = dict(metric=self.task_name,
                          timestamp=self.fake_time,
                          dimensions=dict(blah='whatever',
                                          service='object-storage'),
                          value=v,
                          value_meta=dict(msg=meta))
            metrics.append(metric)

        # Write metric data
        metric_file = os.path.join(self.testdir, 'dfile.json')
        with open(metric_file, 'wb') as f:
            json.dump(metrics, f)

        with mock.patch('time.time') as mock_time:
            # Scan once
            mock_time.return_value = self.fake_time + 1
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual(metrics, actual)
            self.assertEqual(0, len(self.check.plugin_failures))
            with open(metric_file + '.posted', 'r') as f:
                posted_metrics = json.load(f)
            self.assertEqual(len(posted_metrics), len(metrics))

            # Scan later
            mock_time.return_value = self.fake_time + \
                swiftlm_check.METRIC_STALE_AGE + 1
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual([], actual)
            self.assertEqual(0, len(self.check.plugin_failures))
            with open(metric_file + '.posted', 'r') as f:
                posted_metrics = json.load(f)
            self.assertEqual(len(posted_metrics), len(metrics))

            # Scan much later -- posted gets purged
            mock_time.return_value = self.fake_time + \
                swiftlm_check.POSTED_STALE_AGE + 1
            actual = self.check._run_load_file_task(metric_file)
            self.assertEqual([], actual)
            self.assertEqual(0, len(self.check.plugin_failures))
            with open(metric_file + '.posted', 'r') as f:
                posted_metrics = json.load(f)
            self.assertEqual(len(posted_metrics), 0)

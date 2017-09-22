# (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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
import os
import tempfile

from swiftlm.cli.supervisor import CloudMultiSite

#
# NOTE: MOST TESTS OF SUPERVISOR are in  ../rings/test_standard.py
#


class DummyInputOptions(object):

    def __init__(self, cloud, control_plane):
        self.etc = tempfile.mkdtemp()
        self.region_name = 'region1'
        self.cloud = cloud
        self.control_plane = control_plane
        self.ring_delta = None


def cleanup(path):
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            cleanup(os.path.join(path, name))
        else:
            os.unlink(os.path.join(path, name))
    os.rmdir(path)


class TestCloudMultiSiteLegacy(unittest.TestCase):

    def setUp(self):
        self.options = DummyInputOptions(None, None)

    def tearDown(self):
        cleanup(self.options.etc)

    def test_config_file_paths(self):
        sites = CloudMultiSite(self.options)
        my_cloud = sites.my_cloud
        my_control_plane = sites.my_control_plane
        my_config = sites.path(my_cloud, my_control_plane)
        self.assertEqual(my_config.get('configuration_data'),
                         os.path.join(self.options.etc,
                                      'configuration_data.yml'))
        self.assertEqual(my_config.get('input-model'),
                         os.path.join(self.options.etc, 'input-model.yml'))
        self.assertEqual(my_config.get('swift_ring_builder_consumes'),
                         os.path.join(self.options.etc,
                                      'swift_ring_builder_consumes.yml'))
        self.assertEqual(my_config.get('builder_dir'),
                         os.path.join(self.options.etc, 'builder_dir',
                                      'region-region1'))

        self.assertEqual(my_config.get('ring-delta'),
                         os.path.join(self.options.etc, 'deploy_dir',
                                      'ring-delta.yml'))
        self.assertEqual(my_config.get('osconfig'),
                         os.path.join(self.options.etc,
                                      'drive_configurations'))


class TestCloudMultiSiteClouds(unittest.TestCase):

    def setUp(self):
        self.options = DummyInputOptions('cloud1', 'cp1')
        os.mkdir(os.path.join(self.options.etc, 'cloud1'))
        os.mkdir(os.path.join(self.options.etc, 'cloud1', 'cp1'))
        os.mkdir(os.path.join(self.options.etc, 'cloud2'))
        os.mkdir(os.path.join(self.options.etc, 'cloud2', 'cp2'))

    def tearDown(self):
        cleanup(self.options.etc)

    def test_config_file_paths(self):
        sites = CloudMultiSite(self.options)
        my_cloud = sites.my_cloud
        my_control_plane = sites.my_control_plane

        my_config = sites.path(my_cloud, my_control_plane)
        self.assertEqual(my_cloud, 'cloud1')
        self.assertEqual(my_control_plane, 'cp1')
        self.assertEqual(my_config.get('configuration_data'),
                         os.path.join(self.options.etc, 'cloud1', 'cp1',
                                      'config',
                                      'configuration_data.yml'))
        self.assertEqual(my_config.get('input-model'),
                         os.path.join(self.options.etc, 'cloud1', 'cp1',
                                      'config', 'input-model.yml'))
        self.assertEqual(my_config.get('swift_ring_builder_consumes'),
                         os.path.join(self.options.etc, 'cloud1', 'cp1',
                                      'config',
                                      'swift_ring_builder_consumes.yml'))
        self.assertEqual(my_config.get('builder_dir'),
                         os.path.join(self.options.etc, 'cloud1', 'cp1',
                                      'builder_dir'))

        self.assertEqual(my_config.get('ring-delta'),
                         os.path.join(self.options.etc, 'cloud1', 'cp1',
                                      'ring-delta.yml'))
        self.assertEqual(my_config.get('osconfig'),
                         os.path.join(self.options.etc, 'cloud1', 'cp1',
                                      'config', 'drive_configurations'))

        my_config = sites.path('cloud2', 'cp2')
        self.assertEqual(my_config.get('configuration_data'),
                         os.path.join(self.options.etc, 'cloud2', 'cp2',
                                      'config',
                                      'configuration_data.yml'))
        self.assertEqual(my_config.get('input-model'),
                         os.path.join(self.options.etc, 'cloud2', 'cp2',
                                      'config', 'input-model.yml'))
        self.assertEqual(my_config.get('swift_ring_builder_consumes'),
                         os.path.join(self.options.etc, 'cloud2', 'cp2',
                                      'config',
                                      'swift_ring_builder_consumes.yml'))
        self.assertEqual(my_config.get('builder_dir'),
                         os.path.join(self.options.etc, 'cloud2', 'cp2',
                                      'builder_dir'))

        self.assertEqual(my_config.get('ring-delta'),
                         os.path.join(self.options.etc, 'cloud2', 'cp2',
                                      'ring-delta.yml'))
        self.assertEqual(my_config.get('osconfig'),
                         os.path.join(self.options.etc, 'cloud2', 'cp2',
                                      'config', 'drive_configurations'))

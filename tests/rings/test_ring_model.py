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


import unittest
from yaml import safe_load

from swiftlm.rings.ring_model import RingSpecifications, RingSpecification,\
    DeviceInfo, DriveConfiguration, SwiftModelException, dash_to_underscore

from tests.data.rings_ringspecs import ringspec_simple, \
    ringspec_region_zones, ringspec_null_zones, ringspec_zones_not_speced, \
    ringspec_zones_duplicate_in_ring
from tests.data.rings_data import device_info_simple, \
    drive_configuration_simple, drive_configuration_simple_iter


class TestRingSpecs(unittest.TestCase):

    def test_ringspec_load(self):
        model = {'name': 'dummy',
                 'partition_power': 1,
                 'replication_policy': {'replica_count': 3},
                 'min_part_time': 2,  # Use legacy name in this test
                 'display_name': 'dummy_display',
                 'balance': 100.0,
                 'weight_step': 30}
        ringspec = RingSpecification(None)
        ringspec.load_model(model)
        self.assertEquals(ringspec.name, 'dummy')
        self.assertEquals(ringspec.display_name, 'dummy_display')
        self.assertEquals(ringspec.partition_power, 1)
        self.assertEquals(ringspec.min_part_hours, 2)
        self.assertEquals(ringspec.balance, 100.0)
        self.assertRaises(AttributeError, ringspec.__getattr__, 'junk')
        self.assertEquals(ringspec.replica_count, 3.0)
        self.assertEquals(ringspec.weight_step, 30.0)

    def test_bad_min_part_hours_value(self):
        model = {'name': 'dummy',
                 'partition_power': 1,
                 'replication_policy': {'replica_count': 3},
                 'min_part_hours': 0,  # Zero is bad value
                 'display_name': 'dummy_display',
                 'balance': 100.0,
                 'weight_step': 30}
        ringspec = RingSpecification(None)
        self.assertRaises(SwiftModelException, ringspec.load_model, model)

    def test_both_min_part_names(self):
        model = {'name': 'dummy',
                 'partition_power': 1,
                 'replication_policy': {'replica_count': 3},
                 'min_part_hours': 12,
                 'min_part_time': 6,
                 'display_name': 'dummy_display',
                 'balance': 100.0,
                 'weight_step': 30}
        ringspec = RingSpecification(None)
        self.assertRaises(SwiftModelException, ringspec.load_model, model)

    def test_simple_ringspecs(self):
        ring_model = RingSpecifications('my_cloud', 'my_control_plane',
                                        model=safe_load(ringspec_simple))
        self.assertEquals(
            len(ring_model.control_planes[('my_cloud', 'my_control_plane')].
                rings), 4)

    def test_region_zones(self):
        scenarios = [
            ('my_cloud', 'my_control_plane', 'container', ['sg21'], 2, -1),
            ('my_cloud', 'my_control_plane', 'container', ['other21', 'sg21',
                                                           'other22'], 2, -1),
            ('my_cloud', 'my_control_plane', 'object-0', ['sg31'], 3, -1),
            ('my_cloud', 'my_control_plane', 'object-0', ['other31', 'sg31',
                                                          'other32'], 3, -1),
            ('my_cloud', 'my_control_plane', 'object-0', ['junk1', 'junk2'],
             None, -1),
            ('my_cloud', 'my_control_plane', 'container', [], None, -1),
        ]
        ring_model = RingSpecifications('my_cloud', 'my_control_plane',
                                        model=safe_load(ringspec_region_zones))
        for scenario in scenarios:
            cl, cp, rng, rck, rv, rz = scenario
            r, z = ring_model.get_control_plane_rings(
                cl, cp).get_region_zone(rng, rck)
            self.assertEquals((cl, cp, rng, rck, r, z), (cl, cp, rng, rck, rv,
                                                         rz))

    def test_null_region_zones(self):
        scenarios = [
            ('my_cloud', 'my_control_plane', 'account', ['any'], -1, None),
            ('my_cloud', 'my_control_plane', 'container', ['any'], -1, -1),
        ]
        ring_model = RingSpecifications('my_cloud', 'my_control_plane',
                                        model=safe_load(ringspec_null_zones))
        for scenario in scenarios:
            cl, cp, rng, rck, rv, rz = scenario
            r, z = ring_model.get_control_plane_rings(
                cl, cp).get_region_zone(rng, rck)
            self.assertEquals((cl, cp, rng, rck, r, z), (cl, cp, rng, rck, rv,
                                                         rz))

    def test_not_speced_region_zones(self):
        scenarios = [
            ('my_cloud', 'my_control_plane', 'account', ['any'], -1, -1),
            ('my_cloud', 'my_control_plane', 'container', ['any'], -1, -1),
        ]
        ring_model = RingSpecifications('my_cloud', 'my_control_plane',
                                        model=safe_load(
                                            ringspec_zones_not_speced))
        for scenario in scenarios:
            cl, cp, rng, rck, rv, rz = scenario
            r, z = ring_model.get_control_plane_rings(
                cl, cp).get_region_zone(rng, rck)
            self.assertEquals((cl, cp, rng, rck, r, z), (cl, cp, rng, rck, rv,
                                                         rz))

    def test_duplicate_in_ring(self):
        self.assertRaises(SwiftModelException, RingSpecifications,
                          'my_cloud', 'my_control_plane',
                          model=safe_load(ringspec_zones_duplicate_in_ring))

    def test_replication_replica_count(self):
        ring_model = RingSpecifications('my_cloud', 'my_control_plane',
                                        model=safe_load(ringspec_simple))
        self.assertEquals(
            ring_model.get_control_plane_rings(
                'my_cloud', 'my_control_plane').get_ringspec(
                'account').replica_count, 1.0)
        self.assertEquals(
            ring_model.get_control_plane_rings(
                'my_cloud', 'my_control_plane').get_ringspec(
                'container').replica_count, 2.0)
        self.assertEquals(
            ring_model.get_control_plane_rings(
                'my_cloud', 'my_control_plane').get_ringspec(
                'object-0').replica_count, 3.0)
        self.assertEquals(
            ring_model.get_control_plane_rings(
                'my_cloud', 'my_control_plane').get_ringspec(
                'object-1').replica_count, 14.0)


class TestDeviceInfo(unittest.TestCase):

    def test_simple_device_info(self):
        device_info = DeviceInfo(model=safe_load(device_info_simple))
        self.assertEquals(device_info.region_name, 'region2')
        self.assertEquals(device_info.region_id, '2')
        self.assertEquals(device_info.replication_ip, None)
        self.assertEquals(device_info.presence, 'present')
        self.assertEquals(device_info.meta, 'host.example.com:disk99:/dev/sdh')
        with self.assertRaises(AttributeError):
            _ = device_info.junk
        with self.assertRaises(AttributeError):
            device_info.junk = 'junk'


class TestDriveConfiguration(unittest.TestCase):

    def TestDriveConfigationSimple(self):
        dc = DriveConfiguration()
        dc.load_model(safe_load(drive_configuration_simple))
        self.assertEquals(dc.get('hostname'), 'four')
        result = []
        for item in dc.iter_drive_info():
            result.append(item)
        self.assertEqual(result, drive_configuration_simple_iter)


class TestDashToUnderscore(unittest.TestCase):

    def test_dash_to_underscore(self):
        input = {'a-b': [{'c-d': 'not-changed', 'e_f': 'o_k'},
                         'literal-goes-here-not_changed',
                         {'g-h-i': 123}]}
        expected = {'a_b': [{'c_d': 'not-changed', 'e_f': 'o_k'},
                            'literal-goes-here-not_changed',
                            {'g_h_i': 123}]}
        self.assertEqual(dash_to_underscore(input), expected)

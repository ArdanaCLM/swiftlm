# (c) Copyright 2015-2017 Hewlett Packard Enterprise Development LP
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


import mock
import os
import unittest
from swiftlm.rings.ring_builder import RingBuilder


TESTSDIR = os.path.dirname(os.path.abspath(__file__))
SAMPLESDIR = os.path.join(TESTSDIR, 'samples')


class TestRingBuilder(unittest.TestCase):

    def test_get_devs_from_builder(self):
        device_info = []
        builder = RingBuilder(None, None)
        account_builder_file = os.path.join(SAMPLESDIR, 'account.builder')
        for device in builder._get_devs_from_builder(
                builder_filename=account_builder_file):
            # make sure the weight is the same for all the devices
            self.assertEquals(device.current_weight, 18.63)
            self.assertEquals(device.region_id, '1')
            self.assertEquals(device.zone_id, '1')
            device_info.append(device)
        # make sure we have total of 11 devices
        self.assertEquals(len(device_info), 11)
        self.assertEquals(builder.partitions, 4096)
        self.assertEquals(builder.balance, 999.99)
        self.assertEquals(builder.replica_count, 3.000000)
        self.assertEquals(builder.dispersion, 0.00)
        self.assertEquals(builder.min_part_hours, 16)
        self.assertEquals(builder.remaining, '0:00:00')
        self.assertEquals(builder.overload, 0.000000)

    def test_builder_file_not_found(self):
        builder = RingBuilder(None, None)
        account_builder_file = os.path.join(SAMPLESDIR, 'foo')
        try:
            for device in builder._get_devs_from_builder(
                    builder_filename=account_builder_file):
                pass
        except IOError:
            # bogus file should result in IOError
            pass

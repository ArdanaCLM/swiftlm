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

from swiftlm.rings.ardana_model import ServersModel
from swiftlm.rings.ring_model import DeviceInfo

from tests.data.ring_standard import standard_input_model, \
    standard_swf_rng_consumes, expected_lv_devices


lvm_disk_model = '''
global:
    all_servers:
    -   disk_model:
            name: WHATEVER
            volume_groups:
            -   logical_volumes:
                -   name: SW0
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - object-0
                            - object-1
                -   name: SW1
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - object-2
                            - object-3
                name: vg-one
                physical_volumes:
                - /dev/sda1
            -   logical_volumes:
                -   name: SW2
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - object-4
                            - object-5
                            - object-6
                name: vg=two
                physical_volumes:
                - /dev/sdb
        name: standard-ccp-c1-m1-mgmt
        network_names:
          - standard-ccp-c1-m1-mgmt
          - standard-ccp-c1-m1-obj
        rack: null
        region: regionone
    -   disk_model:
            name: WHATEVER
            volume_groups:
            -   logical_volumes:
                -   name: SW0
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - object-7
                -   name: SW1
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - object-8
                name: vg-one
                physical_volumes:
                - /dev/sda1
            -   logical_volumes:
                -   name: SW2
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - object-9
                            - object-10
                name: vg=two
                physical_volumes:
                - /dev/sdb
        name: standard-ccp-c1-m2-mgmt
        network_names:
          - standard-ccp-c1-m2-mgmt
          - standard-ccp-c1-m2-obj
        rack: null
        region: regionone
'''

device_groups_disk_model = '''
global:
    all_servers:
    -   disk_model:
            name: WHATEVER
            device_groups:
              - name: swiftac
                devices:
                    # should be 0
                  - name: /dev/sdb
                    # should be 1
                  - name: /dev/sdc
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - account
                      - container
              - name: swiftobj
                devices:
                    # should be 2
                  - name: /dev/sdd
                    # should be 3
                  - name: /dev/sde
                    # should be 4
                  - name: /dev/sdf
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - object-0
              - name: swiftobj
                devices:
                    # should be 5
                  - name: /dev/sdg
                    # should be 6
                  - name: /dev/sdh
                    # should be 7
                  - name: /dev/sdi
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - object-1
              - name: swiftobj
                devices:
                    # should be 8
                  - name: /dev/sdj
                    # should be 9
                  - name: /dev/sdk
                    # should be 10
                  - name: /dev/sdl
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - object-1
                      - object-0

        name: standard-ccp-c1-m1-mgmt
        network_names:
          - standard-ccp-c1-m1-mgmt
          - standard-ccp-c1-m1-obj
        pass_through:
            swift:
                drain: true
                remove: yes
        rack: null
        region: regionone
    -   disk_model:
            name: WHATEVER
            device_groups:
              - name: a
                devices:
                  - name: /dev/sda
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - account
              - name: b
                devices:
                  - name: /dev/sdb
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - container
              - name: c
                devices:
                  - name: /dev/sdc
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - object-0
              - name: d
                devices:
                  - name: /dev/sdd
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - object-1
              - name: e
                devices:
                  - name: /dev/sde
                consumer:
                  name: swift
                  attrs:
                    rings:
                      - object-2
        name: standard-ccp-c1-m2-mgmt
        network_names:
          - standard-ccp-c1-m2-mgmt
          - standard-ccp-c1-m2-obj
        pass_through: {}
        rack: null
        region: regionone
'''


class TestHlmModel(unittest.TestCase):

    def test_iter_volume_groups(self):
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        lv_devices = []
        lv_expected = []
        for lv_device in input_model._iter_volume_groups():
            lv_devices.append(DeviceInfo(lv_device))
        self.assertEqual(len(lv_devices), 3)

        # This could be done with a simple assertEquals(), but this allowed
        # me to pin-point differences between actual and expected results
        for lv_device in expected_lv_devices:
            lv_expected.append(DeviceInfo(lv_device))
        lv_expected = sorted(lv_expected, None,  DeviceInfo.sortkey)
        lv_devices = sorted(lv_devices, None, DeviceInfo.sortkey)
        for i in range(0, len(lv_expected)):
            self.assertEqual(sorted(lv_expected[i].keys()),
                             sorted(lv_devices[i].keys()))
            for key in lv_expected[i].keys():
                self.assertEqual(lv_expected[i].get(key),
                                 lv_devices[i].get(key))


class TestLvm(unittest.TestCase):

    def test_lvm_numbering(self):
        input_model = ServersModel('my_cloud', 'my_control_plane',
                                   config=safe_load(lvm_disk_model),
                                   consumes_model=standard_swf_rng_consumes)
        lv_devices = []
        lv_info = set()
        for lv_device in input_model._iter_volume_groups():
            lv_devices.append(DeviceInfo(lv_device))
            lv_info.add((lv_device.server_name, lv_device.server_ip,
                         lv_device.ring_name,
                         lv_device.swift_drive_name))
        self.assertEqual(len(lv_devices), 11)

        # Do not change this without also examining test_drivedata.py
        lv_expected = [
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4', 'object-0', 'lvm0'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4', 'object-1', 'lvm0'),

            ('standard-ccp-c1-m1-mgmt', '192.168.222.4', 'object-2', 'lvm1'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4', 'object-3', 'lvm1'),

            ('standard-ccp-c1-m1-mgmt', '192.168.222.4', 'object-4', 'lvm2'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4', 'object-5', 'lvm2'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4', 'object-6', 'lvm2'),

            ('standard-ccp-c1-m2-mgmt', '192.168.222.3', 'object-7', 'lvm0'),

            ('standard-ccp-c1-m2-mgmt', '192.168.222.3', 'object-8', 'lvm1'),

            ('standard-ccp-c1-m2-mgmt', '192.168.222.3', 'object-9', 'lvm2'),
            ('standard-ccp-c1-m2-mgmt', '192.168.222.3', 'object-10', 'lvm2')
        ]
        for lv in set(lv_expected):
            self.assertTrue(lv in lv_info, '%s missing from %s' % (
                lv, lv_info))
            lv_expected.remove(lv)
        self.assertEqual(0, len(lv_expected), 'still have %s' % lv_expected)


class TestDev(unittest.TestCase):

    def test_dev_numbering(self):
        input_model = ServersModel('my_cloud', 'my_control_plane',
                                   config=safe_load(device_groups_disk_model),
                                   consumes_model=standard_swf_rng_consumes)
        dev_devices = []
        dev_info = set()
        for dev_device in input_model._iter_device_groups():
            dev_devices.append(DeviceInfo(dev_device))
            dev_info.add((dev_device.server_name, dev_device.server_ip,
                          dev_device.ring_name,
                          dev_device.swift_drive_name, dev_device.device_name))
        self.assertEqual(len(dev_devices), 21)

        # Do not change this without also examining test_drivedata.py
        dev_expected = [
            ('standard-ccp-c1-m1-mgmt', '192.168.245.4',
             'account', 'disk0', '/dev/sdb'),
            ('standard-ccp-c1-m1-mgmt', '192.168.245.4',
             'container', 'disk0', '/dev/sdb'),
            ('standard-ccp-c1-m1-mgmt', '192.168.245.4',
             'account', 'disk1', '/dev/sdc'),
            ('standard-ccp-c1-m1-mgmt', '192.168.245.4',
             'container', 'disk1', '/dev/sdc'),

            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-0', 'disk2', '/dev/sdd'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-0', 'disk3', '/dev/sde'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-0', 'disk4', '/dev/sdf'),

            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-1', 'disk5', '/dev/sdg'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-1', 'disk6', '/dev/sdh'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-1', 'disk7', '/dev/sdi'),

            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-1', 'disk8', '/dev/sdj'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-0', 'disk8', '/dev/sdj'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-1', 'disk9', '/dev/sdk'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-0', 'disk9', '/dev/sdk'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-1', 'disk10', '/dev/sdl'),
            ('standard-ccp-c1-m1-mgmt', '192.168.222.4',
             'object-0', 'disk10', '/dev/sdl'),

            ('standard-ccp-c1-m2-mgmt', '192.168.245.3',
             'account', 'disk0', '/dev/sda'),
            ('standard-ccp-c1-m2-mgmt', '192.168.245.3',
             'container', 'disk1', '/dev/sdb'),
            ('standard-ccp-c1-m2-mgmt', '192.168.222.3',
             'object-0', 'disk2', '/dev/sdc'),
            ('standard-ccp-c1-m2-mgmt', '192.168.222.3',
             'object-1', 'disk3', '/dev/sdd'),
            ('standard-ccp-c1-m2-mgmt', '192.168.222.3',
             'object-2', 'disk4', '/dev/sde')
        ]
        for dev in set(dev_expected):
            self.assertTrue(dev in dev_info, '%s missing from %s' % (
                dev, dev_info))
            dev_expected.remove(dev)
        self.assertEqual(0, len(dev_expected), 'still have %s' % dev_expected)


class TestNumDevices(unittest.TestCase):

    def test_num_devices(self):
        input_model = ServersModel('my_cloud', 'my_cpntrol_plane',
                                   config=safe_load(device_groups_disk_model),
                                   consumes_model=standard_swf_rng_consumes)
        self.assertEqual(3,
                         input_model.get_num_devices('account'))
        self.assertEqual(7,
                         input_model.get_num_devices('object-0'))
        self.assertEqual(1,
                         input_model.get_num_devices('object-2'))


class TestPassThrough(unittest.TestCase):

    def test_pass_through(self):
        input_model = ServersModel('my_cloud', 'my_control_plane',
                                   config=safe_load(device_groups_disk_model),
                                   consumes_model=standard_swf_rng_consumes)
        self.assertEqual(input_model.server_draining('standard-ccp-c1-m1-mgmt'),
                         True)
        self.assertEqual(input_model.server_draining('standard-ccp-c1-m2-mgmt'),
                         False)
        self.assertEqual(input_model.server_removing('standard-ccp-c1-m1-mgmt'),
                         True)
        self.assertEqual(input_model.server_removing('standard-ccp-c1-m2-mgmt'),
                         False)
        self.assertEqual(input_model.server_draining('junk'),
                         False)
        self.assertEqual(input_model.server_removing('junk'),
                         False)

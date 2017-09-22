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


from os import listdir
import os.path
import subprocess
import sys
from datetime import timedelta
import yaml
import json

from swift.common.ring import RingBuilder as SwiftRingBuilder

from swiftlm.rings.ring_model import DeviceInfo, RingSpecification


def human_size(bytes):
    units = ['Bytes', 'KB', 'MB', 'GB', 'PB', 'EB']
    k = 1024.0
    for unit in units:
        if bytes < k:
            return '%s%s' % ('{:.2f}'.format(bytes), unit)
        bytes = bytes / k
    return '%s%s' % ('{:.2f}'.format(bytes*k), unit)


class RingDelta(object):
    """
    The ring delta describes rings in actionable terms

    The ring delta contains the following:

    delta_rings
        Is all known ring specifications. Most ring specifications originate
        in the input model. However, we might find a builder file for a ring
        that has been since deleted from the input model.

    delta_ring_actions
        Describes the actions we will take against delta_rings (such as
        create or change replica-count).

    delta_devices
        Is all known devices. Most devices originate in the input model.
        However, we may find a device in a builder file (because the
        device or server has since been removed from the input model).

        In addition to listing the device attributes, we also record the
        action (add, remove, change weight) that should happen to the
        device.
    """

    def __init__(self):
        self.delta_rings = {}
        self.delta_ring_actions = {}
        self.delta_devices = []
        self.primary = True

    def read_from_file(self, fd, fmt):
        if fmt == 'yaml':
            model = yaml.safe_load(fd)
        else:
            model = json.loads(fd)
        self.load_model(model)
        fd.close()

    def write_to_file(self, fd, fmt):
        data = self.dump_model()
        if fmt == 'yaml':
            output = yaml.safe_dump(data, default_flow_style=False)
        else:
            output = yaml.dumps(data, indent=2)
        fd.write(output)
        if not fd == sys.stdout:
            fd.close()

    def __repr__(self):
        output = ''
        for ring_name in self.delta_rings.keys():
            output += '-----------------------------\n'
            output += 'ring_name: %s\n ring_spec: %s' % (
                ring_name, self.delta_rings[ring_name])
        for ring_name in self.delta_ring_actions:
            output += '-----------------------------\n'
            output += '%s ring_name: %s\n action: %s' % (
                ring_name, self.delta_ring_actions[ring_name])
        for device in self.delta_devices:
            output += '-----------------------------\n'
            output += 'DEVICE\n'
            output += '%s\n' % device
        return output

    def dump_model(self):
        staged_rings = []
        for ring_name in self.delta_rings.keys():
            ring_specification = self.delta_rings[ring_name]
            staged_rings.append({'ring_name': ring_name,
                                 'ring_specification':
                                 ring_specification.dump_model()})
        stage_ring_actions = []
        for ring_name in self.delta_ring_actions.keys():
            action = self.delta_ring_actions[ring_name]
            stage_ring_actions.append({'ring_name': ring_name,
                                       'action': action})
        staged_devices = []
        for device in self.delta_devices:
            staged_devices.append(device.dump_model())
        return {'delta_rings': staged_rings,
                'delta_ring_actions': stage_ring_actions,
                'delta_devices': staged_devices}

    def load_model(self, data):
        staged_rings = data.get('delta_rings')
        for staged_ring in staged_rings:
            ring_name = staged_ring.get('ring_name')
            ring_specification = RingSpecification(None)
            ring_specification.load_model(staged_ring.get(
                'ring_specification'))
            self.delta_rings[ring_name] = ring_specification
        stage_ring_actions = data.get('delta_ring_actions')
        for stage_ring_action in stage_ring_actions:
            ring_name = stage_ring_action.get('ring_name')
            action = stage_ring_action.get('action')
            self.delta_ring_actions[ring_name] = action
        for staged_device in data.get('delta_devices'):
            device = DeviceInfo()
            device.load_from_model(staged_device)
            self.delta_devices.append(device)

    def append_device(self, device_info):
        self.delta_devices.append(device_info)

    def register_primary(self, is_primary_state):
        self.primary = is_primary_state

    def register_ring(self, ring_name, ring_specification):
        self.delta_rings[ring_name] = ring_specification
        self.delta_ring_actions[ring_name] = ['undetermined']

    def sort(self):
        self.delta_devices = sorted(self.delta_devices, None,
                                    DeviceInfo.sortkey)

    def get_report(self, options):
        output = ''
        if not self.primary:
            output += 'This is a secondary site - copy builder and ring\n' \
                      'files from the primary site.'
            return output
        output += 'Rings:\n'
        for ring_name in self.delta_rings.keys():
            if options.limit_ring and (options.limit_ring != ring_name):
                continue
            output += '  %s:\n' % ring_name.upper()
            if self.delta_ring_actions.get(ring_name) == ['add']:
                output += '    ring will be created\n'
            else:
                remaining = self.delta_rings[ring_name].get('remaining')
                output += '    ring exists (minimum time to next' \
                          ' rebalance: %s)\n' % remaining
            if (self.delta_ring_actions.get(ring_name) ==
                    ['set-replica-count']):
                output += '    replica-count will be changed\n'
            if (self.delta_ring_actions.get(ring_name) ==
                    ['set-min-part-hours']):
                output += '    min-part-hours will be changed\n'
            num_devices_to_add = 0
            size_to_add = 0
            num_devices_to_remove = 0
            size_to_remove = 0
            size_to_reweight = 0
            num_devices_to_set_weight = 0
            for device_info in self.delta_devices:
                if device_info.ring_name == ring_name:
                    if device_info.presence == 'add':
                        if options.detail == 'full':
                            output += '      add: %s\n' % device_info.meta
                        num_devices_to_add += 1
                        size_to_add += (float(device_info.target_weight) *
                                        options.size_to_weight)
                    elif device_info.presence == 'remove':
                        if options.detail == 'full':
                            output += '      remove: %s\n' % device_info.meta
                        num_devices_to_remove += 1
                        size_to_remove += (float(device_info.current_weight) *
                                           options.size_to_weight)
                    elif device_info.presence == 'set-weight':
                        if options.detail == 'full':
                            size_to_reweight += (abs(
                                float(device_info.target_weight) -
                                float(device_info.current_weight)) *
                                options.size_to_weight)
                            output += '      set-weight %s %s > %s > %s\n' % (
                                device_info.meta,
                                device_info.current_weight,
                                device_info.target_weight,
                                device_info.model_weight)
                        num_devices_to_set_weight += 1
            if num_devices_to_add:
                output += '    will add %s devices (%s)\n' % (
                    num_devices_to_add, human_size(size_to_add))
            if num_devices_to_set_weight:
                output += '    will change weight on %s' \
                          ' devices (%s)\n' % (num_devices_to_set_weight,
                                               human_size(size_to_reweight))
            if num_devices_to_remove:
                output += '    will remove %s' \
                          ' devices (%s)\n' % (num_devices_to_remove,
                                               human_size(size_to_remove))
            if not (num_devices_to_add or num_devices_to_set_weight or
                    num_devices_to_remove):
                output += '    no device changes\n'
            output += '    ring will be rebalanced\n'
        return output


class RingBuilder(object):

    def __init__(self, builder_dir=None, read_rings=False):
        """
        Read and issue ring update commands

        This class handles access to the builder files of a set of rings.

        :param builder_dir: The directory where the builder files are located
        :param read_rings: If True, read from existing builder files
        """
        self.builder_dir = builder_dir
        self.flat_device_list = []
        self.builder_rings = {}
        if builder_dir and not os.path.isdir(builder_dir):
                raise IOError('%s is not a directory' % builder_dir)
        if read_rings:
            for filename in [f for f in listdir(builder_dir) if
                             (os.path.isfile(os.path.join(builder_dir,
                                                          f)) and
                              f.endswith('.builder'))]:
                ring_name = filename[0:filename.find('.builder')]
                self.replica_count = 0.0
                self.balance = 0.0
                for device_info in self._get_devs_from_builder(os.path.join(
                        builder_dir, filename)):
                    device_info.ring_name = ring_name
                    self.flat_device_list.append(device_info)
                self.register_ring(ring_name,
                                   self.replica_count, self.balance,
                                   self.dispersion, self.min_part_hours,
                                   self.remaining,
                                   self.overload)

    def __repr__(self):
        output = '  RING FILES\n'
        for ring_name in self.builder_rings.keys():
            output += ' ring: %s' % ring_name
            output += ' ringspec: %s\n' % self.builder_rings[ring_name]

        output += '  FLAT DEVICES\n'
        for drive_detail in self.flat_device_list:
            output += '    %s\n' % drive_detail
        return output

    def register_ring(self, ring_name, replica_count, balance=0.0,
                      dispersion=0.0, min_part_hours=24,
                      remaining='unknown', overload=0.0):
        if not self.builder_rings.get(ring_name):
            model = {'name': ring_name,
                     'partition_power': 0,
                     'replication_policy': {'replica_count': replica_count},
                     'display_name': 'unknown',
                     'balance': balance,
                     'dispersion': dispersion,
                     'min_part_hours': min_part_hours,
                     'remaining': remaining,
                     'overload': overload}
            ringspec = RingSpecification(None)
            ringspec.load_model(model)
            self.builder_rings[ring_name] = ringspec

    def get_ringspec(self, ring_name):
        return self.builder_rings[ring_name]

    def _get_devs_from_builder(self, builder_filename):
        ring_name = builder_filename[0:builder_filename.find('.builder')]
        try:
            builder = SwiftRingBuilder.load(builder_filename)
        except Exception as e:
            raise IOError('ERROR: swift-ring-builder Problem occurred while '
                          'reading builder file: %s. %s' % (builder_filename,
                                                            e))

        self.partitions = builder.parts
        self.replica_count = builder.replicas
        balance = 0
        if builder.devs:
            balance = builder.get_balance()
        self.balance = balance
        self.dispersion = 0.00
        if builder.dispersion:
            self.dispersion = float(builder.dispersion)
        self.min_part_hours = builder.min_part_hours
        self.remaining = str(timedelta(seconds=builder.min_part_seconds_left))
        self.overload = builder.overload

        if builder.devs:
            balance_per_dev = builder._build_balance_per_dev()
            for dev in builder._iter_devs():
                if dev in builder._remove_devs:
                    # This device was added and then later removed without
                    # doing a rebalance in the meantime. We can ignore
                    # since it's marked for deletion.
                    continue
                device_info = DeviceInfo(
                    {
                        'ring_name': ring_name,
                        'zone_id': dev['zone'],
                        'region_id': dev['region'],
                        'server_ip': dev['ip'],
                        'server_bind_port': dev['port'],
                        'replication_ip': dev['replication_ip'],
                        'replication_bind_port': dev['replication_port'],
                        'swift_drive_name': dev['device'],
                        'current_weight': dev['weight'],
                        'balance': balance_per_dev[dev['id']],
                        'meta': dev['meta'],
                        'presence': 'present'
                    })
                yield device_info

    def device_count(self, ring_name):
        count = 0
        for device_info in self.flat_device_list:
            if ring_name == device_info.ring_name:
                count += 1
        return count

    def command_ring_create(self, ringspec):
        ring_name = ringspec.name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)
        return 'swift-ring-builder %s create %s %s %s' % (
            builder_path,
            ringspec.partition_power,
            ringspec.replica_count,
            ringspec.min_part_hours)

    def command_set_replica_count(self, ringspec):
        ring_name = ringspec.name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)
        return 'swift-ring-builder %s set_replicas %s' % (
            builder_path,
            ringspec.replica_count)

    def command_set_min_part_hours(self, ringspec):
        ring_name = ringspec.name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)
        return 'swift-ring-builder %s set_min_part_hours %s' % (
            builder_path,
            ringspec.min_part_hours)

    def command_device_add(self, device_info):
        ring_name = device_info.ring_name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)
        if not device_info.replication_bind_port:
            device_info.replication_bind_port = device_info.server_bind_port
        if not device_info.replication_ip:
            device_info.replication_ip = device_info.server_ip
        return ('swift-ring-builder %s add'
                ' --region %s --zone %s'
                ' --ip %s --port %s'
                ' --replication-port %s --replication-ip %s'
                ' --device %s --meta %s'
                ' --weight %s' % (builder_path,
                                  device_info.region_id,
                                  device_info.zone_id,
                                  device_info.server_ip,
                                  device_info.server_bind_port,
                                  device_info.replication_bind_port,
                                  device_info.replication_ip,
                                  device_info.swift_drive_name,
                                  device_info.meta,
                                  device_info.target_weight))

    def command_pretend_min_part_hours_passed(self, ringspec):
        ring_name = ringspec.name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)

        return ('swift-ring-builder %s pretend_min_part_hours_passed' %
                builder_path)

    def command_rebalance(self, ringspec):
        ring_name = ringspec.name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)
        return ('swift-ring-builder %s rebalance 999' % builder_path)

    def command_device_set_weight(self, device_info):
        ring_name = device_info.ring_name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)
        ipaddr = device_info.server_ip
        swift_drive_name = device_info.swift_drive_name
        search = '%s/%s' % (ipaddr, swift_drive_name)
        return('swift-ring-builder %s  set_weight %s %s' % (builder_path,
               search, device_info.target_weight))

    def command_device_remove(self, device_info):
        ring_name = device_info.ring_name
        builder_path = os.path.join(self.builder_dir, '%s.builder' % ring_name)
        ipaddr = device_info.server_ip
        swift_drive_name = device_info.swift_drive_name
        search = '%s/%s' % (ipaddr, swift_drive_name)
        return('swift-ring-builder %s  remove %s' % (builder_path, search))

    @staticmethod
    def run_cmd(cmd):
        status = 0
        try:
            output = subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as err:
            status = err.returncode
            output = err.output
        if int(status) <= 1:
            # Exited with EXIT_WARNING
            status = -1
        return (int(status), output)

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


from swiftlm.rings.ring_model import DeviceInfo, Consumes, SwiftModelException
from swiftlm.utils.drivedata import DISK_MOUNT, LVM_MOUNT


class ServersModel(object):
    """
    Access the drive data in the input model

    The input model looks like:

        global:
            all_servers:
              -  name: server1
                 server_group_list:
                 - AZ1
                 - RACK1
                 network_names:
                   - server1-ardana
                   - server1-mgmt
                   - server1-obj
                 disk_model:
                    device_groups:
                      -  consumer:
                            name: swift
                            attrs:
                                rings:
                                - object-0           # Allows raw name or
                                - name: object-0     # name as key (future
                                                     # extension
                            devices:
                              - /dev/sda
                              - /dev/sdb
                              - .etc...
                      -  consumer:
                            name: <something-else>   # We ignore
                            attrs:
                            devices:



    The main output is from iter_devices(). This returns a list of all swift
    drives with following items:

        cloud
            The cloud the server is in (added for audit purposes -- the
            server_name is used in ring building)
        control_plane
            The control plane the server is in (also for audit purposes)
        region_id
            The swift region id (e.g., 1)
        zone_id
            The swift zone id (e.g., 2)
        server_name
            The ardana ansible name/host of the server
        network_names
            The names of of the server on each of the networks
        server_ip
            The IP address of the server
        server_bind_port:
            The port number to use (e.g., 6000)
        server_groups:
            List of server groups associated with the server containing drive
        replication_ip
            The IP address of the drive on the replication network.
            Or None if no replication network
        replication_bind_port
            Port to use if a replication network is used
        swift_drive_name
            Name used in ring files (e.g. swdisk1)
        device_name
            The name of the device (e.g., /dev/sdb)
        ring_name
            The ringname (e.g., object-1)
        group_type
            'device' or 'volume'
        presence:
            Currently always 'present' (because in model it is either there
            or not. Pass-through is used to signal draining and removal.)
    """

    def __init__(self, cloud, control_plane, config=None,
                 consumes_model=None):
        '''

        :param cloud: used in unit tests
        :param control_plane: used in unit tests
        :param config: used in unit tests
        :param consumes_model: used in unit tests
        :return:
        '''
        self.servers = []
        self.consumes = None
        if consumes_model:
            # Used by unit tests
            self.register_consumes(Consumes(consumes_model))

        # Unit tests can load up a single site here; supervisor uses
        # add_servers().
        if config:
            servers = []
            if config.get('control_plane_servers'):
                servers = config.get('control_plane_servers')
            elif config.get('global'):
                if config.get('global').get('all_servers'):
                    servers = config.get('global').get('all_servers')
            self.add_servers(cloud, control_plane, servers)

    def add_servers(self, cloud, control_plane, servers):
        for server in servers:
            server['cloud'] = cloud
            server['control_plane'] = control_plane
        self.servers.extend(servers)

    def register_consumes(self, consumes):
            self.consumes = consumes

    def get_num_devices(self, ring_name):
        num_devices = 0
        for device in self.iter_devices():
            if device.ring_name == ring_name:
                num_devices += 1
        return num_devices

    def iter_devices(self):
        for device_info in self._iter_device_groups():
            yield device_info
        for device_info in self._iter_volume_groups():
            yield device_info

    def _iter_device_groups(self):
        for server in self.servers:
            server_name = server.get('ardana_ansible_host', server.get('name'))
            cloud = server.get('cloud')
            control_plane = server.get('control_plane')
            network_names = server.get('network_names')
            disk_model = server.get('disk_model')
            server_groups = server.get('server_group_list', [])
            device_index = 0
            for device_group in disk_model.get('device_groups', []):
                consumer = device_group.get('consumer')
                if consumer and consumer.get('name', 'other') == 'swift':
                    attrs = consumer.get('attrs')
                    if not attrs:
                        raise SwiftModelException('The attrs item is'
                                                  ' missing from device-groups'
                                                  ' %s in disk model %s' %
                                                  (device_group.get('name'),
                                                   disk_model.get('name')))
                    devices = device_group.get('devices')
                    if not attrs.get('rings'):
                        raise SwiftModelException('The rings item is'
                                                  ' missing from device-groups'
                                                  ' %s in disk model %s' %
                                                  (device_group.get('name'),
                                                   disk_model.get('name')))
                    for device in devices:
                        for ring in attrs.get('rings'):
                            if isinstance(ring, str):
                                ring_name = ring
                            else:
                                ring_name = ring.get('name')
                            server_ip, bind_port = self._get_server_bind(
                                ring_name, network_names)
                            if not server_ip:
                                # When a swift service (example swift-account)
                                # is configured in the input model to run a
                                # node, we expect the node to be in the
                                # "consumes" variable. e.g., consumes_SWF_ACC
                                # should have this node in its list. Since we
                                # failed to get the network name/port, it means
                                # that it is not.
                                # In model terms, we have a disk model that
                                # calls out that a device hosts a ring (e.g.
                                # account), but the node is not configured
                                # to run SWF-ACC.
                                # TODO: this may be worth warning
                                break

                            swift_drive_name = DISK_MOUNT + str(device_index)
                            device_info = DeviceInfo({
                                'cloud': cloud,
                                'control_plane': control_plane,
                                'server_groups': server_groups,
                                'region_id': 1,   # later, the server group may
                                'zone_id': 1,     # change these defaults
                                'server_name': server_name,
                                'network_names': network_names,
                                'server_ip': server_ip,
                                'server_bind_port': bind_port,
                                'replication_ip': server_ip,
                                'replication_bind_port': bind_port,
                                'swift_drive_name': swift_drive_name,
                                'device_name': device.get('name'),
                                'ring_name': ring_name,
                                'group_type': 'device',
                                'block_devices': {'percent': '100%',
                                                  'physicals':
                                                      [device.get('name')]},
                                'presence': 'present'})

                            yield device_info
                        device_index += 1

    def _iter_volume_groups(self):
        for server in self.servers:
            server_name = server.get('ardana_ansible_host', server.get('name'))
            cloud = server.get('cloud')
            control_plane = server.get('control_plane')
            network_names = server.get('network_names')
            disk_model = server.get('disk_model')
            server_groups = server.get('server_group_list', [])
            lv_index = 0
            for volume_group in disk_model.get('volume_groups', []):
                vg_name = volume_group.get('name')
                physical_volumes = volume_group.get('physical_volumes')
                for logical_volume in volume_group.get('logical_volumes', []):
                    lv_name = logical_volume.get('name')
                    percent = logical_volume.get('size')
                    consumer = logical_volume.get('consumer')
                    if consumer and consumer.get('name', 'other') == 'swift':
                        attrs = consumer.get('attrs')
                        if not attrs:
                            raise SwiftModelException('The attrs item is'
                                                      ' missing from '
                                                      ' logical volume'
                                                      ' %s in disk model %s' %
                                                      (logical_volume.get(
                                                          'name'),
                                                       disk_model.get('name')))
                        if not attrs.get('rings'):
                            raise SwiftModelException('The rings item is'
                                                      ' missing from logical'
                                                      ' volume'
                                                      ' %s in disk model %s' %
                                                      (logical_volume.get(
                                                          'name'),
                                                       disk_model.get('name')))
                        for ring in attrs.get('rings'):
                            if isinstance(ring, str):
                                ring_name = ring
                            else:
                                ring_name = ring.get('name')
                            server_ip, bind_port = self._get_server_bind(
                                ring_name, network_names)
                            if not server_ip:
                                # TODO: this may be worth warning
                                break
                            swift_drive_name = LVM_MOUNT + str(lv_index)
                            device_name = '/dev/' + vg_name + '/' + lv_name
                            device_info = DeviceInfo({
                                'cloud': cloud,
                                'control_plane': control_plane,
                                'server_groups': server_groups,
                                'region_id': 1,   # later, the server group may
                                'zone_id': 1,     # change these defaults
                                'server_name': server_name,
                                'network_names': network_names,
                                'server_ip': server_ip,
                                'server_bind_port': bind_port,
                                'replication_ip': server_ip,
                                'replication_bind_port': bind_port,
                                'swift_drive_name': swift_drive_name,
                                'device_name': device_name,
                                'ring_name': ring_name,
                                'group_type': 'lvm',
                                'block_devices': {'percent': percent,
                                                  'physicals':
                                                      physical_volumes},
                                'presence': 'present'})
                            yield device_info
                        lv_index += 1

    def _get_server_pass_through(self, server_name):
        for server in self.servers:
            if server_name == server.get('ardana_ansible_host',
                                         server.get('name')):
                pass_through_data = server.get('pass_through', {})
                if pass_through_data and isinstance(pass_through_data, dict):
                    return pass_through_data.get('swift', {})
        return {}

    def server_draining(self, server_name):
        if self._get_server_pass_through(server_name).get('drain'):
            return True
        return False

    def server_removing(self, server_name):
        if self._get_server_pass_through(server_name).get('remove'):
            return True
        return False

    def _get_server_bind(self, ring_name, network_names):
        network_name, network_ip_address, network_port = \
            self.consumes.get_network_name_port(ring_name, network_names)
        if not network_name:
            return None, None
        return (network_ip_address, network_port)

    def __repr__(self):
        output = '\nInput Model\n'
        output += '-----------\n\n'
        output += '\n  Servers\n'
        output += '    Number: %s' % len(self.servers)
        output += '\n    Device Information\n'
        for di in self.iter_devices():
            output += '\n      device info: %s' % di
        return output

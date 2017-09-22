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


import os
from yaml import safe_load


class SwiftModelException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class RingSpecification(dict):
    """
    Specification of a single ring

    This input has the following structure:

        name: <str>                        # Ring name
        display_name: <str>
        weight-step: <float>               # Optional. (default None)
        partition_power: <int>
        min_part_hours: <int>              # Old name is min_part_time
        remaining: <string>                # For rings read from a builder
                                           # file, this is set; otherwise
                                           # it is not part of input model
        default: <bool>                    # Optional (default: False)
        server_bind_port: <int>            # Reserved
        replication_bind_port: <int>       # Reserved

        replication_policy:                # Must be present for account/
            replica_count: <int>           # container rings

        erasure_coding_policy;             # Optional for object rings
             ec_num_data_fragments: <int>
             ec_num_parity_fragments: <int>
             ec_type: jerasure_rs_vand     # Optional
             ec_object_segment_size: <int>

        swift_zones:                       # Optional.
             id: <int>                     # in the input model
             server_groups:
               -  AZ1
               -  OTHER
        balance: <float>                   # Not in input model, but is in
                                           # rings read from a builder file

        parent: <obj>                      # Not in model. A pointer to
                                           # containing specification
                                           # (to inherit region and zone)
    """
    keynames = ['name', 'display_name', 'partition_power', 'min_part_hours',
                'remaining',
                'default', 'server_bind_port',
                'replication_bind_port',
                'replication_policy', 'erasure_coding_policy',
                'swift_zones', 'balance', 'parent', 'weight_step']

    def __init__(self, parent):
        super(RingSpecification, self).__init__()
        self.update({'parent': parent})

    def __getattr__(self, item):
        # Special cases
        if item == 'replica_count':
            if self.get('replication_policy'):
                return float(
                    self.get('replication_policy').get('replica_count'))
            elif self.get('erasure_coding_policy'):
                ec = self.get('erasure_coding_policy')
                return float((ec.get('ec_num_data_fragments') +
                              ec.get('ec_num_parity_fragments')))
            return None
        elif item == 'min_part_hours':
            # Elsewhere we may disallow a default
            return self.get('min_part_hours', self.get('min_part_time', 48))
        elif item == 'weight_step':
            if self.get('weight_step'):
                return float(self.get('weight_step'))
            else:
                return None

        # Return value for valid items
        if item in RingSpecification.keynames:
            return self.get(item, None)
        else:
            raise AttributeError

    def __setattr__(self, item, value):
        # Special cases
        if item == 'replica_count':
            if self.get('replication_policy'):
                self.get('replication_policy')['replica_count'] = float(value)
                return
            elif self.get('erasure_coding_policy'):
                raise SwiftModelException('Cannot set replica-count'
                                          ' directly on an EC ring')
        # Set value for valid items
        if item in RingSpecification.keynames:
            self[item] = value
        else:
            raise AttributeError

    def __repr__(self):
        output = '(ring) name: %s,' % self.name
        output += ' display-name: %s,' % self.display_name
        output += ' partition-power: %s,' % self.partition_power
        output += ' replica_count: %s' % self.__getattr__('replica_count')
        return output

    def dump_model(self):
        model = {}
        for key in self.keys():
            if key not in ['parent']:
                model[key] = self.get(key)
        return model

    def load_model(self, model):
        self.update(model)
        if not self.get('server_bind_port', None):
            if self.get('name').startswith('account'):
                port = 6002
            elif self.get('name').startswith('container'):
                port = 6001
            else:
                port = 6000
            self['server_bind_port'] = port
            self['replication_bind_port'] = self.server_bind_port
        self.validate()

    def validate(self):
        if self.get('min_part_hours') and self.get('min_part_time'):
            raise SwiftModelException('Ring: %s has specified both'
                                      ' min-part-time and'
                                      ' min-part-hours. Please use'
                                      ' min-part-hours.' % self.name)
        if not (self.get('min_part_hours') or self.get('min_part_time')):
            raise SwiftModelException('Ring: %s is missing'
                                      ' min-part-hours or has a'
                                      ' value of zero.' % self.name)
        if self.replication_policy and self.erasure_coding_policy:
            raise SwiftModelException('Ring: %s has specified both'
                                      ' replication_policy and'
                                      ' erasure_coding_policy. Only one'
                                      ' may be specified.' % self.name)
        if not (self.replication_policy or self.erasure_coding_policy):
            raise SwiftModelException('Ring: %s is missing a policy'
                                      ' type (replication_policy or'
                                      ' erasure_coding_policy).' % self.name)
        if self.swift_zones:
            groups = []
            for zone in self.swift_zones:
                zone_id = zone.get('id')
                if zone_id is None:
                    raise SwiftModelException('Ring: %s is missing id field'
                                              ' in a swift-zones'
                                              ' entry' % self.name)
                try:
                    _ = int(zone_id)
                except ValueError:
                    raise SwiftModelException('Ring: %s has invalid'
                                              ' id value in'
                                              ' in a swift-zones'
                                              ' entry' % self.name)
                groups.extend(zone.get('server_groups', []))
            if groups:
                if len(groups) != len(set(groups)):
                    raise SwiftModelException('Ring: %s has duplicate'
                                              ' server-group name'
                                              ' in a swift-zones'
                                              ' entry' % self.name)

    def get_zone(self, server_groups):
        """
        Get zone id for given server group

        :param server_groups: Server groups to search for
        :returns: -1 zones not specified. None means server_group not found
        """

        if self.swift_zones:
            for zone in self.swift_zones:
                zone_id = zone.get('id')
                for group in server_groups:
                    if group in zone.get('server_groups', []):
                        return zone_id
            return None
        else:
            return -1


class ControlPlaneRings(object):
    """
    Rings in a given control plane

    This class represents the input model's ring specfications for a
    control plane. This is specified in a configuration-data object.

    For multi-site, the primary control plane should have the
    primary-control-plane attribute set to true and the other sites
    should set to false.

    The input model looks like:

        primary_control_plane: <bool>  # optional - default to True
        rings:
          - <RingSpecification>     # see that class for details
          - second ring, etc
        swift-regions:
          - id: <number>
            server-gropups:
              - <name>
              - other group
          - etc
        swift-regions:
          - id: <number>
            server-groups:
              - <name>
              - other group
          - etc

    """
    def __init__(self, parent):
        self.parent = parent
        self.region_name = ''
        self.swift_regions = []
        self.swift_zones = []
        self.rings = []

    def __repr__(self):
        output = 'region-name: %s\n' % self.region_name
        output += 'swift-regions: %s\n' % self.swift_regions
        output += 'swift-zones: %s\n' % self.swift_zones
        output += '----rings----\n'
        for ringspec in self.rings:
            output += '\n%s' % ringspec
            output += '----end ring----\n'
        return output

    def load_model(self, model):
        self.region_name = model.get('region_name')
        self.primary_control_plane = model.get('primary_control_plane', True)
        if not self.primary_control_plane:
            return  # only attributes of primary site are used
        for ring in model.get('rings'):
            ringspec = RingSpecification(self)
            ringspec.load_model(ring)
            self.rings.append(ringspec)
        if model.get('swift_regions'):
            self.swift_regions = model.get('swift_regions')
        if model.get('swift_zones'):
            self.swift_zones = model.get('swift_zones')
        self.validate()

    def validate(self):
        if self.swift_regions:
            groups = []
            for region in self.swift_regions:
                region_id = region.get('id')
                if region_id is None:
                    raise SwiftModelException('Rings in region %s is missing'
                                              ' id field'
                                              ' in a swift-regions'
                                              ' entry' % self.region_name)
                try:
                    _ = int(region_id)
                except ValueError:
                    raise SwiftModelException('Rings in region %s has invalid'
                                              ' id value in'
                                              ' in a swift-regions'
                                              ' entry' % self.region_name)
                groups.extend(region.get('server_groups', []))
            if groups:
                if len(groups) != len(set(groups)):
                    raise SwiftModelException('Rings in region %s has '
                                              ' duplicate'
                                              ' server-group name'
                                              ' in a swift-regions'
                                              ' entry' % self.region_name)
        if self.swift_zones:
            groups = []
            for zone in self.swift_zones:
                zone_id = zone.get('id')
                if zone_id is None:
                    raise SwiftModelException('Rings in region %s is missing'
                                              ' id field in a swift-zones'
                                              ' entry' % self.region_name)
                try:
                    _ = int(zone_id)
                except ValueError:
                    raise SwiftModelException('Rings in region %s has invalid'
                                              ' id value in'
                                              ' in a swift-zones'
                                              ' entry' % self.region_name)
                groups.extend(zone.get('server_groups', []))
            if groups:
                if len(groups) != len(set(groups)):
                    raise SwiftModelException('Rings in region %s has '
                                              ' duplicate'
                                              ' server-group name'
                                              ' in a swift-zones'
                                              ' entry' % self.region_name)

    def get_ringspec(self, ring_name):
        for ringspec in self.rings:
            if ring_name == ringspec.name:
                return ringspec
        return None

    def is_primary_control_plane(self):
        return self.primary_control_plane

    def get_region(self, server_groups):
        if self.swift_regions:
            for region in self.swift_regions:
                region_id = region.get('id')
                for group in server_groups:
                    if group in region.get('server_groups', []):
                        return region_id
            return None
        else:
            return -1

    def get_zone(self, server_groups):
        """ Get zone at control plane level """
        if self.swift_zones:
            for zone in self.swift_zones:
                zone_id = zone.get('id')
                for group in server_groups:
                    if group in zone.get('server_groups', []):
                        return zone_id
            return None
        else:
            return -1

    def get_region_zone(self, ring_name, server_groups):
        """ Get region/zone; -1 means not defined """

        swift_region_id = self.get_region(server_groups)

        # See if zone defined at ring level
        swift_zone_id = -1
        for ringspec in self.rings:
            if ring_name == ringspec.name:
                swift_zone_id = ringspec.get_zone(server_groups)
                if swift_zone_id > 0:
                    return (swift_region_id, swift_zone_id)
        if swift_zone_id == -1:
            # Not defined at ring level -- get from control plane (this) level
            swift_zone_id = self.get_zone(server_groups)

        return swift_region_id, swift_zone_id


class RingSpecifications(object):
    """
    Specification of rings from multiple sites

    When there are multiple sites, one of the sites contains the
    definitive primary ring specifications. The other site(s) have a
    specification that they import the primary rings.

    The rings are specified via a configuration-data object in the
    inout model. For Swift, this looks like:

    config_data:
        control_plane_rings:
            <ControlPlaneRings>     # See that class for details
        <other-unrelated-key>: <unrelated-data>

    The model looks like:

        global:
            all_ring_specifications:
              -  <ControlPlaneRings>     # See that class for details
              -  a second region was allowed here; never used; now deprecated
    """
    def __init__(self, cloud, control_plane, fd=None, model=None,
                 configuration_data=None):
        self.control_planes = {}
        if fd:
            self.load_model(safe_load(fd))
        if model:
            # Used by unit tests
            self.load_model(cloud, control_plane, model)
        if configuration_data:
            self.load_configuration(cloud, control_plane, configuration_data)

    def __repr__(self):
        output = 'specs from all clouds:'
        for cl, cp in self.control_planes.keys():
            output += '\n------\ncloud: %s  control-plane:%s:' % (cl, cp)
            output += '\n%s' % self.control_planes[(cl, cp)]
        return output

    def load_configuration(self, cloud, control_plane, config_data):
        config_data = dash_to_underscore(config_data)
        if config_data.get('control_plane_rings'):
            control_plane_rings = ControlPlaneRings(self)
            control_plane_rings.load_model(
                config_data.get('control_plane_rings'))
            self.control_planes[(cloud, control_plane)] = control_plane_rings
        else:
            # FIXME: fail if there is no specification (when CP translates)
            pass

    def load_model(self, cloud, control_plane, model):
        # Used by unit tests
        ringspecs = model.get('global').get('all_ring_specifications')
        if not ringspecs:
            return
        for ksregion in ringspecs:
            keystone_region_rings = ControlPlaneRings(self)
            keystone_region_rings.load_model(ksregion)
            self.control_planes[(cloud, control_plane)] = keystone_region_rings

    def get_control_plane_rings(self, cloud, control_plane):
        return self.control_planes.get((cloud, control_plane), None)


class DeviceInfo(dict):
    """
    Represents all the data connected with a device

    This information is used in two contexts:
    - In the ring delta, it is sourced from the input model and specifies
      changes (if any) to make to the rings
    - Is created by reading an existing ring builder file

    Some items are present or absent depending on context as follows:

    Item                 Input Builder  Description
                         Model File
    ----                 ----- -------  ---------------------------------------
    region_name          yes   yes      Region name
    server_groups        yes   no       The groups the server is a member of
    region_id            yes   yes      Region number
    zone_id              yes   yes      Zone number
    network_names        yes   no       Alternate names of the server
    server_name          yes   no       Server name (ardana anisible name)
    server_ip            yes   yes      IP address of server
    server_bind_port     yes   yes      Bind port for this device
    replication_ip       yes   yes      Replication IP address
    replication_bind_ip  yes   yes      Replication bind port of this device
    swift_drive_name     yes   yes      Device/mount point name (e.g., disk3)
    device_name          yes   no       Block device name (e.g., /dev/sdd)
    ring_name            yes   yes      Ring name
    group_type           yes   no       Block device or LVM device
    presence             yes   yes      Action (if any) to take
    current_weight       yes   yes      Current weight of device
    target_weight        yes   no       Planned weight when added or changed
    model_weight         yes   no       The final weight based on model
    balance              no    yes      Current balance of the device
    meta                 yes   yes      Meta item
    block_devices        yes   no       For LVM, the underlying block devices
    """

    keynames = ['region_name', 'server_groups',
                'region_id', 'zone_id', 'network_names',
                'server_name', 'server_ip', 'server_bind_port',
                'replication_ip', 'replication_bind_port',
                'swift_drive_name', 'device_name', 'ring_name', 'group_type',
                'presence', 'current_weight', 'target_weight', 'model_weight',
                'balance', 'meta',
                'block_devices']

    def __init__(self, model=None):
        super(DeviceInfo, self).__init__()
        if model:
            self.load_from_model(model)

    def __getattr__(self, item):
        if item in ['zone_id', 'region_id']:
            return str(self.get(item, None))
        if item in ['network_names', 'server_groups']:
            return self.get(item, [])
        if item in DeviceInfo.keynames:
            return self.get(item, None)
        else:
            raise AttributeError('No key %s in %s' % (item, self))

    def __setattr__(self, item, value):
        if item in DeviceInfo.keynames:
            self.update({item: value})
        else:
            raise AttributeError('No key %s in %s' % (item, self))

    def is_same_device(self, device_info):
        if (self.region_name == device_info.region_name and
                self.ring_name == device_info.ring_name and
                self.server_ip == device_info.server_ip and
                self.swift_drive_name == device_info.swift_drive_name):
            return True
        return False

    def is_bad_change(self, device_info):
        if self.zone_id != device_info.zone_id:
            return 'swift-zone id from %s to %s' % (device_info.zone_id,
                                                    self.zone_id)
        if self.region_id != device_info.region_id:
            return 'swift-region id from %s to %s' % (device_info.region_id,
                                                      self.region_id)
        return None

    def dump_model(self):
        return self.copy()

    def load_from_model(self, model):
        self.update(model)
        if not self.region_name:
            self['region_name'] = 'unknown'
        if not self.group_type:
            self['group_type'] = 'device'
        if not self.presence:
            self['presence'] = 'present'
        if not self.balance:
            self['balance'] = 0
        if not self.meta and (self.swift_drive_name and self.device_name):
            self['meta'] = '%s:%s:%s' % (self.server_name,
                                         self.swift_drive_name,
                                         self.device_name)

    @staticmethod
    def sortkey(device_info):
        return (device_info.region_name + device_info.ring_name +
                device_info.server_ip + device_info.swift_drive_name)


class DriveConfigurations(object):
    """
    Represents all disk configuration of all known servers

    This contains the drive configuration for all servers. It provides
    a convenient way of getting the size of any given drive (/dev/sda) or
    partition (/dev/sda1).
    """
    def __init__(self):
        self.configurations = {}
        self.drive_data = {}

    def add(self, configuration):
        hostname = configuration.get('hostname')
        self.configurations[hostname] = configuration
        for name, size, fulldrive in configuration.iter_drive_info():
            self.drive_data[(hostname, name)] = (size, fulldrive)

    def get_drive_configuration(self, hostname):
        return self.configurations.get(hostname)

    def iter_drives(self):
        for hostname in self.configurations.keys():
            drive_configuration = self.configurations.get(hostname)
            for (name, size,
                 fulldrive) in drive_configuration.iter_drive_info():
                yield (hostname, name, size, fulldrive)

    def get_drive_data(self, hostname, name):
        return self.drive_data.get((hostname, name), (None, None))

    def get_hw(self, hostname, device_info):
        """
        Get actual size of a swift device. Also whether its a partition or not

        The device_info may refer to a block device or a volume in a LVM. If
        a block device, it may refer to a specific partition.

        LVM is made up up several physical drives and the space is then
        allocated on a % basis to each volume. We need the volume size.

        The fulldrive flag indicates is the swift drive uses all of the
        physical drive or is just one of many partitions on the drive. An
        LVM volume is considered a full drive.

        :param hostname: server name (used to find the drive configuration)
        :param device_info: description of the drive

        :returns: tuple of size, fulldrive
        """
        hw_size = None
        if device_info.group_type == 'device':
            physical = device_info.block_devices.get('physicals')[0]
            hw_size, hw_fulldrive = self.get_drive_data(hostname, physical)
        else:
            # LVM -- work out size from physical drives and % size
            physical_volumes_total = 0
            for physical in device_info.block_devices.get('physicals'):
                if physical.endswith('_root'):
                    # Templated device name - convert /dev/sdX_root to /dev/sdX
                    # This makes the LVM appear slightly bigger than it
                    # actually is since the boot partition gets counted in the
                    # size.
                    physical = physical[:-len('_root')]
                block_device_size, hw_fulldrive = self.get_drive_data(
                    hostname, physical)
                if block_device_size:
                    physical_volumes_total += block_device_size
            if physical_volumes_total:
                percent_human = device_info.block_devices.get(
                    'percent')
                try:  # should be something such as 20%
                    percent = int(percent_human.split('%')[0])
                    hw_size = physical_volumes_total * percent / 100
                except ValueError:
                    hw_size = None
            hw_fulldrive = True
        return hw_size, hw_fulldrive


class DriveConfiguration(dict):
    """
    Represents the disk drive configuration of a server

    The data originates in osconfig probe_hardware module.

    Normally the input model contains device names (e.g., /dev/sda).
    The swiftlm drive provision process will own the fill drive,
    hence it will create a single partition spanning the drive. Hence
    osconfig probe_hardware will return both the drive (/dev/sda) and the
    partition (/dev/sda1). For our purposes we use /dev/sda whether or
    not it has been partitioned.

    Alternatively (mostly to cope with non-standard layouts), we will
    allow partition names in the model (e.g., /dev/sda1). To cope with this
    we return the drive and all partitions, but mark them as not being a
    full drive.

    The hostname key here is my_ardana_ansible_name which should match
    the server_name based on ardana_ansible_host in the control_plane_servers

    The input data looks like (yaml):

        ipaddr: null
        hostname: blah1
        drives:
        -   name: /dev/sda
            bytes: 100000000
            partitions:
            -   partition: sda1
                bytes: 100000000
        -   name: /dev/sdb
            bytes: 200000000
            partitions: []
        -   name: /dev/sbc
            bytes: 300000
            partitions:
            -    partition: sdc1
                 bytes: 100000
                 partition: sdc2
                 bytes: 200000

    """
    keynames = ['ipaddr', 'hostname', 'drives']

    def __init__(self):
        super(DriveConfiguration, self).__init__()

    def load_model(self, model):
        self.update(model)

    def iter_drive_info(self):
        """
        Get list of drives

        :return: a list where each item is a tuple containing:
            name of drive (e.g. /dev/sda
            size (in bytes)
            boolean, where True means device is the full drive; False means
                it is a partition on the drive
        """
        for drive in self.get('drives'):
            name = drive.get('name')
            size = drive.get('bytes')
            partitions = drive.get('partitions')
            if len(partitions) == 0:
                yield (name, size, True)
            elif len(partitions) == 1:
                # Single partition (e.g., sda1) using full drive
                # Return drive name (e.g., /dev/sda) covers both
                yield (name, size, True)
            else:
                # Drive is partitioned into smaller chunks
                # Return drive and all partitions, e.g.,
                # /dev/sda, /dev/sda1, /dev/sda2
                yield (name, size, False)
                for partition in partitions:
                    yield (os.path.join('/dev',
                                        partition.get('partition')),
                           partition.get('bytes'), False)


class Consumes(object):
    """
    Manages the SWF_RNG variable produced by the Configuration Processor. The
    idea is that the swift-ring-builder/SWF-RNG is definded to consume
    SWF-ACC, SWF-COn and SWF-OBJ. This means the Configuration Processor
    will create the appropriate consumes relationships for those services. In
    other words, the CP will tell us whether to use blah-mgt or blah-obj as
    the appropriate network to communicate on.

    The input model looks like:

    consumes_SWF_ACC:
        members:
            private:
            -   host: standard-ccp-c1-m3-obj
                ip_address: 192.168.245.9
                port: 6002
                use_tls: false
            -   host: standard-ccp-c1-m2-obj
                ip_address: 192.168.245.10
                port: 6002
                use_tls: false
            -   host: standard-ccp-c1-m1-obj
                ip_address: 192.168.245.11
                port: 6002
                use_tls: false
    consumes_SWF_CON:
        etc...
    consumes_SWF_OBJ:
        etc...

    The main function used is get_network_name_port(). For example,
    given an input model as shown above, a ringname/ringtype of 'account'
    and a list of 'standard-ccp-c1-m2-ardana', 'standard-ccp-c1-m2-mgmt'
    and 'standard-ccp-c1-m2-obj', the function returns,,

        ('standard-ccp-c1-m2-obj', '192.168.245.10', 6002)

    ...since the appropriate network for the account-server is the '-obj'
    network.

    """

    @classmethod
    def get_node_list(cls, item, model):
        node_list = model[item]['members']['private']
        return node_list

    def __init__(self, model=None):
        self.nodes = {}
        self.nodes['account'] = []
        self.nodes['container'] = []
        self.nodes['object'] = []
        self.host_to_network = {}
        if model:
            # Used by unit tests
            self.load_model(model)

    def load_model(self, model):
        self.nodes['account'].extend(Consumes.get_node_list(
            'consumes_SWF_ACC', model))
        self.nodes['container'].extend(Consumes.get_node_list(
            'consumes_SWF_CON', model))
        self.nodes['object'].extend(Consumes.get_node_list(
            'consumes_SWF_OBJ', model))
        for ringtype in ['account', 'container', 'object']:
            for node in self.nodes[ringtype]:
                network_name = node['host']
                network_ip_address = node['ip_address']
                network_port = node['port']
                self.host_to_network[(ringtype, network_name)] = (
                    network_name, network_ip_address, network_port)

    def get_network_name_port(self, ringtype, host_network_names):
        """
        :param ringtype: Tupe if ring (account, etc.) Can be ring name
            (e.g., object-0)
        :param host_network_names: list of network names for the host
            (e.g., blah-mgmt, blah-obj, blah-ardana)
        :return: tuple of name, ip-address, port
        """
        if ringtype.startswith('object'):
            ringtype = 'object'
        for hostname in host_network_names:
            result = self.host_to_network.get((ringtype, hostname))
            if result:
                return result
        return (None, None, None)


def dash_to_underscore(obj):
    """
    Convert dashes to underscores in an input model object
    :param obj: The object to convert
    :return:The converted object
    """
    if isinstance(obj, list):
        ret_obj = []
        for item in obj:
            ret_obj.append(dash_to_underscore(item))
    elif isinstance(obj, dict):
        ret_obj = dict()
        for key in obj.keys():
            new_key = key.replace('-', '_')
            ret_obj[new_key] = dash_to_underscore(obj[key])
    else:
        ret_obj = obj
    return ret_obj

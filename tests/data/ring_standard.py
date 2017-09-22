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


#
# This file was built using:
#       ardana-input-model/2.0/ardana-ci/standard/ dated 13 July 2015
# ...with one change: the ring-specifications were changed to
# use the MGMT network
#
# How to modify this file:
#
# 1/ Run the (v2) configuration processor with the standard input model
# 2/ Copy the resulting group_vars/all file into the standard_input_model
#    variable below.
# 3/ Copy the drive_configurations data from osconfig-probe/  and put into
#   the standard_drive_configurations variable below
# 4/ If the input model has few changes, the expected_cmds variable should
#    be ok. However, any of the followingg changes will require you to update
#    expected_cmds:
#    - changes in ip addresses
#    - changes in device names causes by a change to the input model
#    - changes in weights if the standard-vagrant is changed
#    The order of the expected_cmds does not matter
#
standard_input_model = '''

global:
    # FIXME: for now, need rings here since CP wil present older models this
    # way. Later when CP converts old rings to a configuration-data object,
    # we should remove this and fix the unit tests.
    all_ring_specifications:
    - region: regionone
      swift_zones:
        -   id: 1
            server_groups:
            - AZ1
        -   id: 2
            server_groups:
            - AZ2
      swift_regions:
        -   id: 9
            server_groups:
            -   AZ1
            -   AZ2
      rings:
        -   display_name: Account Ring
            min_part_hours: 24
            name: account
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   display_name: Container Ring
            min_part_hours: 24
            name: container
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   default: true
            display_name: General
            min_part_hours: 24
            name: object-0
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   name: object-1
            weight_step: 3.3
            display_name: Extra
            min_part_hours: 12
            partition_power: 17
            replication_policy:
                replica_count: 1

control_plane_servers:
    -   disk_model:
            name: DISK_SET_COMPUTE
            volume_groups:
            -   logical_volumes:
                -   fstype: ext4
                    mount: /
                    name: root
                    size: 35%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/log
                    name: LV_LOG
                    size: 70%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/crash
                    name: LV_CRASH
                    size: 30%
                name: vg0
                physical_volumes:
                - /dev/sda1
            -   logical_volumes:
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/lib
                    name: LV_COMPUTE
                    size: 100%
                name: vg-comp
                physical_volumes:
                - /dev/sdb
        ardana_ansible_host: standard-ccp-compute0001
        network_names:
          - standard-ccp-compute0001-mgmt
        rack: null
        region_not_used: regionone
    -   disk_model:
            name: DISK_SET_COMPUTE
            volume_groups:
            -   logical_volumes:
                -   fstype: ext4
                    mount: /
                    name: root
                    size: 35%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/log
                    name: LV_LOG
                    size: 70%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/crash
                    name: LV_CRASH
                    size: 30%
                name: vg0
                physical_volumes:
                - /dev/sda1
            -   logical_volumes:
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/lib
                    name: LV_COMPUTE
                    size: 100%
                name: vg-comp
                physical_volumes:
                - /dev/sdb
            # This is put here to test that a compute node (that does not have
            # SWF-ACC, SWF-CON or SWF-OBJ configured, is allowed to have a
            # disk consumed by Swift. See SWIF-2585 for motivation
            # These drives will NOT appear in the rings
            device_groups:
            -   consumer:
                    attrs:
                        rings:
                        - account
                        - container
                        - object-0
                    name: swift
                devices:
                -   name: /dev/sdc
                -   name: /dev/sdd
                name: dummy
        ardana_ansible_host: standard-ccp-compute0002
        network_names:
          - standard-ccp-compute0002-mgmt
          - standard-ccp-compute0002-obj
        rack: null
        region_not_used: regionone
        server_group: RACK2
        server_group_list:
        - RACK2
        - AZ2
        - CLOUD
    -   disk_model:
            name: DISK_SET_COMPUTE
            volume_groups:
            -   logical_volumes:
                -   fstype: ext4
                    mount: /
                    name: root
                    size: 35%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/log
                    name: LV_LOG
                    size: 70%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/crash
                    name: LV_CRASH
                    size: 30%
                name: vg0
                physical_volumes:
                - /dev/sda1
            -   logical_volumes:
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/lib
                    name: LV_COMPUTE
                    size: 100%
                name: vg-comp
                physical_volumes:
                - /dev/sdb
        ardana_ansible_host: standard-ccp-compute0003
        network_names:
          - standard-ccp-compute0003-mgmt
        rack: null
        region_not_used: regionone
    -   disk_model:
            device_groups:
            -   consumer:
                    attrs:
                        rings:
                        - account
                        - container
                        - object-0
                    name: swift
                devices:
                -   name: /dev/sdc
                -   name: /dev/sdd
                name: swiftobj
            -   consumer:
                    name: cinder
                devices:
                -   name: /dev/sde
                name: cinder-volume
            name: DISK_SET_CONTROLLER
            volume_groups:
            -   consumer:
                    name: os
                logical_volumes:
                -   fstype: ext4
                    mount: /
                    name: root
                    size: 30%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/log
                    name: LV_LOG
                    size: 50%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/crash
                    name: LV_CRASH
                    size: 20%
                name: ardana-vg
                physical_volumes:
                - /dev/sda1
                - /dev/sdb
        ardana_ansible_host: standard-ccp-c1-m1
        network_names:
          - standard-ccp-c1-m1-mgmt
          - standard-ccp-c1-m1-obj
        rack: null
        server_group: RACK1
        server_group_list:
        - RACK1
        - AZ1
        - CLOUD
        region_not_used: regionone
    -   disk_model:
            device_groups:
            -   consumer:
                    attrs:
                        rings:
                        - account
                        - container
                        - object-0
                        - object-1
                    name: swift
                devices:
                -   name: /dev/sdc
                -   name: /dev/sdd
                name: swiftobj
            -   consumer:
                    name: cinder
                devices:
                -   name: /dev/sde
                name: cinder-volume
            name: DISK_SET_CONTROLLER
            volume_groups:
            -   consumer:
                    name: os
                logical_volumes:
                -   fstype: ext4
                    mount: /
                    name: root
                    size: 30%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/log
                    name: LV_LOG
                    size: 30%
                -   fstype: ext4
                    name: LV_SWFAC
                    size: 20%
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - name: account
                            - name: container
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/crash
                    name: LV_CRASH
                    size: 20%
                name: ardana-vg
                physical_volumes:
                - /dev/sda_root
                - /dev/sdb
        ardana_ansible_host: standard-ccp-c1-m2
        network_names:
          - standard-ccp-c1-m2-mgmt
          - standard-ccp-c1-m2-obj
        rack: null
        server_group: RACK1
        server_group_list:
        - RACK1
        - AZ1
        - CLOUD
        region_not_used: regionone
    -   disk_model:
            device_groups:
            -   consumer:
                    attrs:
                        rings:
                        - account
                        - container
                        - object-0
                    name: swift
                devices:
                -   name: /dev/sdc
                -   name: /dev/sdd
                name: swiftobj
            -   consumer:
                    name: cinder
                devices:
                -   name: /dev/sde
                name: cinder-volume
            name: DISK_SET_CONTROLLER
            volume_groups:
            -   consumer:
                    name: os
                logical_volumes:
                -   fstype: ext4
                    mount: /
                    name: root
                    size: 30%
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/log
                    name: LV_LOG
                    size: 50%
                -   fstype: ext4
                    name: LV_SWFOBJ
                    size: 10%
                    consumer:
                        name: swift
                        attrs:
                            rings:
                            - name: object-0
                -   fstype: ext4
                    mkfs_opts: -O large_file
                    mount: /var/crash
                    name: LV_CRASH
                    size: 20%
                name: ardana-vg
                physical_volumes:
                - /dev/sda1
                - /dev/sdb
        ardana_ansible_host: standard-ccp-c1-m3
        network_names:
          - standard-ccp-c1-m3-mgmt
          - standard-ccp-c1-m3-obj
        rack: null
        server_group: RACK2
        server_group_list:
        - RACK2
        - AZ2
        - CLOUD
        region_not_used: regionone
other_global:
    ansible_vars: []
    ntp_servers:
    - pool.ntp.org
    vips:
    - standard-ccp-vip-LOG-SVR-mgmt
    - standard-ccp-vip-GLA-REG-mgmt
    - standard-ccp-vip-HEA-ACW-mgmt
    - standard-ccp-vip-FND-MDB-mgmt
    - standard-ccp-vip-HEA-ACF-mgmt
    - standard-ccp-vip-CND-API-mgmt
    - standard-ccp-vip-admin-CND-API-mgmt
    - standard-ccp-vip-GLA-API-mgmt
    - standard-ccp-vip-MON-API-mgmt
    - standard-ccp-vip-KEY-API-mgmt
    - standard-ccp-vip-admin-KEY-API-mgmt
    - standard-ccp-vip-CEI-API-mgmt
    - standard-ccp-vip-admin-CEI-API-mgmt
    - standard-ccp-vip-SWF-PRX-mgmt
    - standard-ccp-vip-admin-SWF-PRX-mgmt
    - standard-ccp-vip-FND-IDB-mgmt
    - standard-ccp-vip-admin-FND-IDB-mgmt
    - standard-ccp-vip-NEU-SVR-mgmt
    - standard-ccp-vip-NOV-API-mgmt
    - standard-ccp-vip-admin-NOV-API-mgmt
    - standard-ccp-vip-HEA-API-mgmt
    - standard-ccp-vip-HZN-WEB-mgmt

    name: standard
'''

host_list_acc = [
    {'host': 'standard-ccp-c1-m3-mgmt', 'port': '6002', 'use_tls': False,
     'ip_address': '192.168.245.2'},
    {'host': 'standard-ccp-c1-m2-mgmt', 'port': '6002', 'use_tls': False,
     'ip_address': '192.168.245.3'},
    {'host': 'standard-ccp-c1-m1-mgmt', 'port': '6002', 'use_tls': False,
     'ip_address': '192.168.245.4'}
]

host_list_con = [
    {'host': 'standard-ccp-c1-m3-mgmt', 'port': '6001', 'use_tls': False,
     'ip_address': '192.168.245.2'},
    {'host': 'standard-ccp-c1-m2-mgmt', 'port': '6001', 'use_tls': False,
     'ip_address': '192.168.245.3'},
    {'host': 'standard-ccp-c1-m1-mgmt', 'port': '6001', 'use_tls': False,
     'ip_address': '192.168.245.4'}
]

# Note: put objects on -obj network (to exercise ip address resolution
host_list_obj = [
    {'host': 'standard-ccp-c1-m3-obj', 'port': '6000', 'use_tls': False,
     'ip_address': '192.168.222.2'},
    {'host': 'standard-ccp-c1-m2-obj', 'port': '6000', 'use_tls': False,
     'ip_address': '192.168.222.3'},
    {'host': 'standard-ccp-c1-m1-obj', 'port': '6000', 'use_tls': False,
     'ip_address': '192.168.222.4'}
]

standard_swf_rng_consumes = {
    'consumes_SWF_ACC': {'members': {'private': host_list_acc}},
    'consumes_SWF_CON': {'members': {'private': host_list_con}},
    'consumes_SWF_OBJ': {'members': {'private': host_list_obj}}
}

standard_configuration_data = '''
control_plane_rings:
    swift_zones:
    -   id: 1
        server_groups:
        - AZ1
    -   id: 2
        server_groups:
        - AZ2
    swift_regions:
    -   id: 9
        server_groups:
        -   AZ1
        -   AZ2
    rings:
    -   display_name: Account Ring
        min_part_hours: 24
        name: account
        partition_power: 17
        replication_policy:
            replica_count: 3
    -   display_name: Container Ring
        min_part_hours: 24
        name: container
        partition_power: 17
        replication_policy:
            replica_count: 3
    -   default: true
        display_name: General
        min_part_hours: 24
        name: object-0
        partition_power: 17
        replication_policy:
            replica_count: 3
    -   name: object-1
        weight_step: 3.3
        display_name: Extra
        min_part_hours: 12
        partition_power: 17
        replication_policy:
            replica_count: 1
'''
standard_drive_configurations = '''
ardana_drive_configuration:

-   drives:
    -   bytes: 42949672960
        name: /dev/sda
        partitions:
        -   bytes: 42941447
            partition: sda1
        -   bytes: 9999
            partition: sda2
    -   bytes: 20000000000
        name: /dev/sdb
        partitions:
        -   bytes: 20000000000
            partition: sdb1
    -   bytes: 20000000000
        name: /dev/sdc
        partitions: []
    -   bytes: 20000000000
        name: /dev/sdd
        partitions: []
    -   bytes: 20000000000
        name: /dev/sde
        partitions: []
    -   bytes: 20000000000
        name: /dev/sdf
        partitions: []
    hostname: standard-ccp-c1-m1
    ipaddr: null


-   drives:
    -   bytes: 42949672960
        name: /dev/sda
        partitions:
        -   bytes: 42941447
            partition: sda1
        -   bytes: 9999
            partition: sda2
    -   bytes: 20000000000
        name: /dev/sdb
        partitions:
        -   bytes: 20000000000
            partition: sdb1
    -   bytes: 20000000000
        name: /dev/sdc
        partitions: []
    -   bytes: 20000000000
        name: /dev/sdd
        partitions: []
    -   bytes: 20000000000
        name: /dev/sde
        partitions: []
    -   bytes: 20000000000
        name: /dev/sdf
        partitions: []
    hostname: standard-ccp-c1-m2
    ipaddr: null

-   drives:
    -   bytes: 42949672960
        name: /dev/sda
        partitions:
        -   bytes: 42941447
            partition: sda1
        -   bytes: 9999
            partition: sda2
    -   bytes: 20000000000
        name: /dev/sdb
        partitions:
        -   bytes: 20000000000
            partition: sdb1
    -   bytes: 20000000000
        name: /dev/sdc
        partitions: []
    -   bytes: 20000000000
        name: /dev/sdd
        partitions: []
    -   bytes: 20000000000
        name: /dev/sde
        partitions: []
    -   bytes: 20000000000
        name: /dev/sdf
        partitions: []
    hostname: standard-ccp-c1-m3
    ipaddr: null
'''

expected_cmds = [
    'swift-ring-builder /path/to/builder/dir/container.builder'
    ' create 17 3.0 24',
    'swift-ring-builder /path/to/builder/dir/object-0.builder '
    ' create 17 3.0 24',
    'swift-ring-builder /path/to/builder/dir/account.builder'
    ' create 17 3.0 24',
    'swift-ring-builder /path/to/builder/dir/object-1.builder'
    ' create 17 1.0 12',
    'swift-ring-builder /path/to/builder/dir/account.builder add'
    ' --region 9 --zone 2 --ip 192.168.245.2 --port 6002'
    ' --replication-port 6002 --replication-ip 192.168.245.2 --device disk0'
    ' --meta standard-ccp-c1-m3:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/account.builder add'
    ' --region 9 --zone 2 --ip 192.168.245.2 --port 6002'
    ' --replication-port 6002 --replication-ip 192.168.245.2 --device disk1'
    ' --meta standard-ccp-c1-m3:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/account.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.3 --port 6002'
    ' --replication-port 6002 --replication-ip 192.168.245.3 --device disk0'
    ' --meta standard-ccp-c1-m2:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/account.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.3 --port 6002'
    ' --replication-port 6002 --replication-ip 192.168.245.3 --device disk1'
    ' --meta standard-ccp-c1-m2:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/account.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.4 --port 6002'
    ' --replication-port 6002 --replication-ip 192.168.245.4 --device disk0'
    ' --meta standard-ccp-c1-m1:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/account.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.4 --port 6002'
    ' --replication-port 6002 --replication-ip 192.168.245.4 --device disk1'
    ' --meta standard-ccp-c1-m1:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/container.builder add'
    ' --region 9 --zone 2 --ip 192.168.245.2 --port 6001'
    ' --replication-port 6001 --replication-ip 192.168.245.2 --device disk0'
    ' --meta standard-ccp-c1-m3:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/container.builder add'
    ' --region 9 --zone 2 --ip 192.168.245.2 --port 6001'
    ' --replication-port 6001 --replication-ip 192.168.245.2 --device disk1'
    ' --meta standard-ccp-c1-m3:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/container.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.3 --port 6001'
    ' --replication-port 6001 --replication-ip 192.168.245.3 --device disk0'
    ' --meta standard-ccp-c1-m2:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/container.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.3 --port 6001'
    ' --replication-port 6001 --replication-ip 192.168.245.3 --device disk1'
    ' --meta standard-ccp-c1-m2:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/container.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.4 --port 6001'
    ' --replication-port 6001 --replication-ip 192.168.245.4 --device disk0'
    ' --meta standard-ccp-c1-m1:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/container.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.4 --port 6001'
    ' --replication-port 6001 --replication-ip 192.168.245.4 --device disk1'
    ' --meta standard-ccp-c1-m1:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/object-0.builder add'
    ' --region 9 --zone 2 --ip 192.168.222.2 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.2 --device disk0'
    ' --meta standard-ccp-c1-m3:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/object-0.builder add'
    ' --region 9 --zone 2 --ip 192.168.222.2 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.2 --device disk1'
    ' --meta standard-ccp-c1-m3:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/object-0.builder add'
    ' --region 9 --zone 1 --ip 192.168.222.3 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.3 --device disk0'
    ' --meta standard-ccp-c1-m2:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/object-0.builder add'
    ' --region 9 --zone 1 --ip 192.168.222.3 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.3 --device disk1'
    ' --meta standard-ccp-c1-m2:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/object-0.builder add'
    ' --region 9 --zone 1 --ip 192.168.222.4 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.4 --device disk0'
    ' --meta standard-ccp-c1-m1:disk0:/dev/sdc --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/object-0.builder add'
    ' --region 9 --zone 1 --ip 192.168.222.4 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.4 --device disk1'
    ' --meta standard-ccp-c1-m1:disk1:/dev/sdd --weight 18.63',
    'swift-ring-builder /path/to/builder/dir/object-1.builder add'
    ' --region 9 --zone 1 --ip 192.168.222.3 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.3 --device disk0'
    ' --meta standard-ccp-c1-m2:disk0:/dev/sdc --weight 3.30',
    'swift-ring-builder /path/to/builder/dir/object-1.builder add'
    ' --region 9 --zone 1 --ip 192.168.222.3 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.3 --device disk1'
    ' --meta standard-ccp-c1-m2:disk1:/dev/sdd --weight 3.30',
    'swift-ring-builder /path/to/builder/dir/account.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.3 --port 6002'
    ' --replication-port 6002 --replication-ip 192.168.245.3 --device lvm0'
    ' --meta standard-ccp-c1-m2:lvm0:/dev/ardana-vg/LV_SWFAC --weight 11.73',
    'swift-ring-builder /path/to/builder/dir/container.builder add'
    ' --region 9 --zone 1 --ip 192.168.245.3 --port 6001'
    ' --replication-port 6001 --replication-ip 192.168.245.3 --device lvm0'
    ' --meta standard-ccp-c1-m2:lvm0:/dev/ardana-vg/LV_SWFAC --weight 11.73',
    'swift-ring-builder /path/to/builder/dir/object-0.builder add'
    ' --region 9 --zone 2 --ip 192.168.222.2 --port 6000'
    ' --replication-port 6000 --replication-ip 192.168.222.2 --device lvm0'
    ' --meta standard-ccp-c1-m3:lvm0:/dev/ardana-vg/LV_SWFOBJ --weight 1.87',
    'swift-ring-builder /path/to/builder/dir/object-0.builder'
    ' rebalance 999',
    'swift-ring-builder /path/to/builder/dir/container.builder'
    ' rebalance 999',
    'swift-ring-builder /path/to/builder/dir/account.builder'
    ' rebalance 999',
    'swift-ring-builder /path/to/builder/dir/object-1.builder'
    ' rebalance 999'
]

# NOTE: region and zone set to 1 (they are set at later, higher, level)
expected_lv_devices = [
    {'cloud': 'standard', 'control_plane': 'ccp', 'region_id': 1,
     'zone_id': 1,
     'server_groups': ['RACK1', 'AZ1', 'CLOUD'],
     'server_name': 'standard-ccp-c1-m2', 'server_ip': '192.168.245.3',
     'network_names': ['standard-ccp-c1-m2-mgmt', 'standard-ccp-c1-m2-obj'],
     'server_bind_port': '6002', 'replication_ip': '192.168.245.3',
     'replication_bind_port': '6002',
     'swift_drive_name': 'lvm0', 'device_name': '/dev/ardana-vg/LV_SWFAC',
     'meta': 'standard-ccp-c1-m2:lvm0:/dev/ardana-vg/LV_SWFAC',
     'ring_name': 'account', 'group_type': 'lvm', 'presence': 'present',
     'block_devices': {'percent': '20%',
                       'physicals': ['/dev/sda_root', '/dev/sdb']}},
    {'cloud': 'standard', 'control_plane': 'ccp', 'region_id': 1,
     'zone_id': 1,
     'server_groups': ['RACK1', 'AZ1', 'CLOUD'],
     'server_name': 'standard-ccp-c1-m2', 'server_ip': '192.168.245.3',
     'network_names': ['standard-ccp-c1-m2-mgmt', 'standard-ccp-c1-m2-obj'],
     'server_bind_port': '6001', 'replication_ip': '192.168.245.3',
     'replication_bind_port': '6001',
     'swift_drive_name': 'lvm0', 'device_name': '/dev/ardana-vg/LV_SWFAC',
     'meta': 'standard-ccp-c1-m2:lvm0:/dev/ardana-vg/LV_SWFAC',
     'ring_name': 'container', 'group_type': 'lvm', 'presence': 'present',
     'block_devices': {'percent': '20%',
                       'physicals': ['/dev/sda_root', '/dev/sdb']}},
    {'cloud': 'standard', 'control_plane': 'ccp', 'region_id': 1,
     'zone_id': 1,
     'server_groups': ['RACK2', 'AZ2', 'CLOUD'],
     'server_name': 'standard-ccp-c1-m3', 'server_ip': '192.168.222.2',
     'network_names': ['standard-ccp-c1-m3-mgmt', 'standard-ccp-c1-m3-obj'],
     'server_bind_port': '6000', 'replication_ip': '192.168.222.2',
     'replication_bind_port': '6000',
     'swift_drive_name': 'lvm0', 'device_name': '/dev/ardana-vg/LV_SWFOBJ',
     'meta': 'standard-ccp-c1-m3:lvm0:/dev/ardana-vg/LV_SWFOBJ',
     'ring_name': 'object-0', 'group_type': 'lvm', 'presence': 'present',
     'block_devices': {'percent': '10%',
                       'physicals': ['/dev/sda1', '/dev/sdb']}}
]

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


ringspec_simple = '''
global:
    all_ring_specifications:
    -   region_name_not_used: region1
        rings:
        -   display_name: Account Ring
            min_part_hours: 12
            name: account
            partition_power: 17
            replication_policy:
                replica_count: 1
        -   display_name: Container Ring
            min_part_hours: 12
            name: container
            partition_power: 17
            replication_policy:
                replica_count: 2
        -   default: true
            display_name: General
            min_part_hours: 12
            name: object-0
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   default: false
            display_name: EC
            min_part_hours: 12
            name: object-1
            partition_power: 17
            erasure_coding_policy:
                ec_num_data_fragments: 4
                ec_num_parity_fragments: 10
                ec_type: jerasure_rs_vand
                ec_object_segment_size: 1000000
'''

ringspec_region_zones = '''
global:
    all_ring_specifications:
    -   region_name_not_used: region1
        swift_regions:
            - id: 2
              server_groups:
                - sg21
                - sgtwotwo
                - sgtwo3
            - id: 3
              server_groups:
                - sg31
                - sgthreetwo
                - sgthree3
        rings:
        -   display_name: Account Ring
            min_part_hours: 12
            name: account
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   display_name: Container Ring
            min_part_hours: 12
            name: container
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   default: true
            display_name: General
            min_part_hours: 12
            name: object-0
            partition_power: 17
            replication_policy:
                replica_count: 3
'''

ringspec_null_zones = '''
global:
    all_ring_specifications:
    -   region_name_not_used: region1
        swift_regions: []
        swift_zones: []
        rings:
        -   display_name: Account Ring
            min_part_hours: 12
            name: account
            partition_power: 17
            replication_policy:
                replica_count: 3
            swift_zones:
            - id: 2
              server_groups_omitted: on-purpose
        -   display_name: Container Ring
            min_part_hours: 12
            name: container
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   default: true
            display_name: General
            min_part_hours: 12
            name: object-0
            partition_power: 17
            replication_policy:
                replica_count: 3
'''

ringspec_zones_not_speced = '''
global:
    all_ring_specifications:
    -   region_name_not_used: region1
        rings:
        -   display_name: Account Ring
            min_part_hours: 12
            name: account
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   display_name: Container Ring
            min_part_hours: 12
            name: container
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   default: true
            display_name: General
            min_part_hours: 12
            name: object-0
            partition_power: 17
            replication_policy:
                replica_count: 3
'''


ringspec_zones_duplicate_in_ring = '''
global:
    all_ring_specifications:
    -   region_name_not_used: region1
        rings:
        -   display_name: Account Ring
            min_part_hours: 12
            name: account
            partition_power: 17
            replication_policy:
                replica_count: 3
            swift_zones:
            - id: 1
              server_groups:
              - ONE
              - SAME
            - id: 2
              server_groups:
              - TWO
              - SAME
        -   display_name: Container Ring
            min_part_hours: 12
            name: container
            partition_power: 17
            replication_policy:
                replica_count: 3
        -   default: true
            display_name: General
            min_part_hours: 12
            name: object-0
            partition_power: 17
            replication_policy:
                replica_count: 3
'''

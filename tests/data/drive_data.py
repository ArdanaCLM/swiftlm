# (c) Copyright 2015 Hewlett Packard Enterprise Development LP
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


TEST_CONTROLLER_DATA = (
    0,
    '\nSmart Array P420i in Slot 1\n   '
    'Bus Interface: PCI\n   Slot: 1\n   '
    'Serial Number: PCFBB0B9V3X04L\n   '
    'Cache Serial Number: PBKUC0BRH5B1Y5\n   '
    'RAID 6 (ADG) Status: Enabled\n   '
    'Controller Status: OK\n   '
    'Hardware Revision: B\n   '
    'Firmware Version: 5.42\n   '
    'Rebuild Priority: Low\n   '
    'Expand Priority: Medium\n   '
    'Surface Scan Delay: 3 secs\n   '
    'Surface Scan Mode: Idle\n   '
    'Queue Depth: Automatic\n   '
    'Monitor and Performance Delay: 60  min\n   '
    'Elevator Sort: Enabled\n   '
    'Degraded Performance Optimization: Disabled\n   '
    'Inconsistency Repair Policy: Disabled\n   '
    'Wait for Cache Room: Disabled\n   '
    'Surface Analysis Inconsistency Notification: '
    'Disabled\n   '
    'Post Prompt Timeout: 15 secs\n   '
    'Cache Board Present: True\n   '
    'Cache Status: OK\n   '
    'Cache Ratio: 10% Read / 90% Write\n   '
    'Drive Write Cache: Disabled\n   '
    'Total Cache Size: 1024 MB\n   '
    'Total Cache Memory Available: 816 MB\n   '
    'No-Battery Write Cache: Disabled\n   '
    'SSD Caching RAID5 WriteBack Enabled: False\n   '
    'SSD Caching Version: 1\n   '
    'Cache Backup Power Source: Capacitors\n  '
    'Battery/Capacitor Count: 1\n   '
    'Battery/Capacitor Status: OK\n   '
    'SATA NCQ Supported: True\n   '
    'Spare Activation Mode: Activate '
    'on physical drive failure (default)\n   '
    'Controller Temperature (C): 47\n   '
    'Cache Module Temperature (C): 33\n   '
    'Capacitor Temperature  (C): 32\n   '
    'Number of Ports: 2 Internal only\n   '
    'Encryption Supported: False\n   '
    'Driver Name: hpsa\n   '
    'Driver Version: 3.4.0\n   '
    'Driver Supports HP SSD Smart Path: False\n')

TEST_HPSSACLI_FAILURE = (
    1,
    '/usr/sbin/hpssacli: 12: /usr/sbin/hpssacli: '
    '/opt/hp/hpssacli/bld/mklocks.sh: not found\n'
    '/usr/sbin/hpssacli: 16: /usr/sbin/hpssacli: '
    '/opt/hp/hpssacli/bld/hpssacli: not found\n'
    'Could not find hpssacli in /usr/sbin/hpssacli\n')

TEST_SLOT_DATA = (
    0,
    '\nSmart Array P420i in Slot 1'
    '               (sn: PCFBB0B9V3X04L)\n')
TEST_DRIVE_DATA = (
    0,
    '\nSmart Array P420i in Slot 1\n\n   '
    'array A\n\n      '
    'physicaldrive 2I:1:1\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 1\n         '
    'Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n        '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130560662        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 24\n         '
    'Maximum Temperature (C): 43\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array B\n\n      '
    'physicaldrive 2I:1:2\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 2\n         '
    'Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130567806        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 26\n         '
    'Maximum Temperature (C): 47\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array C\n\n      '
    'physicaldrive 2I:1:3\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 3\n         '
    'Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130547389        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 27\n         '
    'Maximum Temperature (C): 43\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array D\n\n      physicaldrive 2I:1:4\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 4\n         '
    'Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130589869        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 27\n         '
    'Maximum Temperature (C): 47\n         PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array E\n\n      '
    'physicaldrive 2I:1:5\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 5\n         '
    'Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130587564        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 27\n         '
    'Maximum Temperature (C): 51\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array F\n\n      physicaldrive 2I:1:6\n         '
    'Port: 2I\n         Box: 1\n         '
    'Bay: 6\n         Status: OK\n        '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130587865        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 28\n         '
    'Maximum Temperature (C): 48\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n        '
    ' Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array G\n\n      '
    'physicaldrive 2I:1:7\n         Port: 2I\n         '
    'Box: 1\n         Bay: 7\n         Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130590172        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 28\n         '
    'Maximum Temperature (C): 44\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array H\n\n      '
    'physicaldrive 2I:1:8\n         '
    'Port: 2I\n         Box: 1\n         Bay: 8\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130599346        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 28\n         '
    'Maximum Temperature (C): 47\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array I\n\n      '
    'physicaldrive 2I:1:9\n         '
    'Port: 2I\n         Box: 1\n         Bay: 9\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130611949        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 30\n         '
    'Maximum Temperature (C): 46\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array J\n\n      '
    'physicaldrive 2I:1:10\n         '
    'Port: 2I\n         Box: 1\n         Bay: 10\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130671356        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 29\n         '
    'Maximum Temperature (C): 42\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array K\n\n      '
    'physicaldrive 2I:1:11\n         '
    'Port: 2I\n         Box: 1\n         '
    'Bay: 11\n         Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130560091        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 30\n         '
    'Maximum Temperature (C): 44\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array L\n\n      '
    'physicaldrive 2I:1:12\n         Port: 2I\n         '
    'Box: 1\n         Bay: 12\n         Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130587524        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 31\n         '
    'Maximum Temperature (C): 45\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array M\n\n      physicaldrive 2I:1:13\n         '
    'Port: 2I\n         Box: 1\n         Bay: 13\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130548532        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 30\n         '
    'Maximum Temperature (C): 44\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array N\n\n      physicaldrive 2I:1:14\n         '
    'Port: 2I\n         Box: 1\n         Bay: 14\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: Solid State SATA\n         '
    'Size: 100 GB\n         Native Block Size: 512\n         '
    'Firmware Revision: 5DV1HPG0\n         '
    'Serial Number: BTTV343307NK100FGN  \n         '
    'Model: ATA     MK0100GCTYU     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 26\n         '
    'Maximum Temperature (C): 42\n         '
    'Usage remaining: 99.97%\n         '
    'Power On Hours: 3843\n         '
    'Estimated Life Remaining based on workload to date: '
    '533589 days\n         '
    'SSD Smart Trip Wearout: False\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array O\n\n      physicaldrive 2I:1:15\n         '
    'Port: 2I\n         Box: 1\n         Bay: 15\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: Solid State SATA\n         '
    'Size: 100 GB\n         Native Block Size: 512\n         '
    'Firmware Revision: 5DV1HPG0\n         '
    'Serial Number: BTTV343306L5100FGN  \n         '
    'Model: ATA     MK0100GCTYU     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 26\n         '
    'Maximum Temperature (C): 43\n         '
    'Usage remaining: 99.97%\n         '
    'Power On Hours: 3843\n         '
    'Estimated Life Remaining based on workload to '
    'date: 533589 days\n         '
    'SSD Smart Trip Wearout: False\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n')

TEST_SINGLE_DRIVE_FAILURE_DATA = (
    0,
    '\nSmart Array P420i in Slot 1\n\n   '
    'array A\n\n      '
    'physicaldrive 2I:1:1\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 1\n         '
    'Status: FAIL\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n        '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130560662        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 24\n         '
    'Maximum Temperature (C): 43\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array B\n\n      '
    'physicaldrive 2I:1:2\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 2\n         '
    'Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130567806        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 26\n         '
    'Maximum Temperature (C): 47\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array C\n\n      '
    'physicaldrive 2I:1:3\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 3\n         '
    'Status: FAIL\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130547389        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 27\n         '
    'Maximum Temperature (C): 43\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array D\n\n      physicaldrive 2I:1:4\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 4\n         '
    'Status: WARN\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130589869        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 27\n         '
    'Maximum Temperature (C): 47\n         PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array E\n\n      '
    'physicaldrive 2I:1:5\n         '
    'Port: 2I\n         '
    'Box: 1\n         '
    'Bay: 5\n         '
    'Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130587564        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 27\n         '
    'Maximum Temperature (C): 51\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array F\n\n      physicaldrive 2I:1:6\n         '
    'Port: 2I\n         Box: 1\n         '
    'Bay: 6\n         Status: OK\n        '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130587865        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 28\n         '
    'Maximum Temperature (C): 48\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n        '
    ' Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array G\n\n      '
    'physicaldrive 2I:1:7\n         Port: 2I\n         '
    'Box: 1\n         Bay: 7\n         Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130590172        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 28\n         '
    'Maximum Temperature (C): 44\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array H\n\n      '
    'physicaldrive 2I:1:8\n         '
    'Port: 2I\n         Box: 1\n         Bay: 8\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130599346        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 28\n         '
    'Maximum Temperature (C): 47\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array I\n\n      '
    'physicaldrive 2I:1:9\n         '
    'Port: 2I\n         Box: 1\n         Bay: 9\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130611949        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 30\n         '
    'Maximum Temperature (C): 46\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array J\n\n      '
    'physicaldrive 2I:1:10\n         '
    'Port: 2I\n         Box: 1\n         Bay: 10\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130671356        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 29\n         '
    'Maximum Temperature (C): 42\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array K\n\n      '
    'physicaldrive 2I:1:11\n         '
    'Port: 2I\n         Box: 1\n         '
    'Bay: 11\n         Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         '
    'Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130560091        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 30\n         '
    'Maximum Temperature (C): 44\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   array L\n\n      '
    'physicaldrive 2I:1:12\n         Port: 2I\n         '
    'Box: 1\n         Bay: 12\n         Status: OK\n         '
    'Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130587524        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 31\n         '
    'Maximum Temperature (C): 45\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array M\n\n      physicaldrive 2I:1:13\n         '
    'Port: 2I\n         Box: 1\n         Bay: 13\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: SATA\n         Size: 3 TB\n         '
    'Native Block Size: 512\n         '
    'Rotational Speed: 7200\n         '
    'Firmware Revision: HPG2    \n         '
    'Serial Number: WCC130548532        \n         '
    'Model: ATA     MB3000GCVBT     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 30\n         '
    'Maximum Temperature (C): 44\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array N\n\n      physicaldrive 2I:1:14\n         '
    'Port: 2I\n         Box: 1\n         Bay: 14\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: Solid State SATA\n         '
    'Size: 100 GB\n         Native Block Size: 512\n         '
    'Firmware Revision: 5DV1HPG0\n         '
    'Serial Number: BTTV343307NK100FGN  \n         '
    'Model: ATA     MK0100GCTYU     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 26\n         '
    'Maximum Temperature (C): 42\n         '
    'Usage remaining: 99.97%\n         '
    'Power On Hours: 3843\n         '
    'Estimated Life Remaining based on workload to date: '
    '533589 days\n         '
    'SSD Smart Trip Wearout: False\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n\n   '
    'array O\n\n      physicaldrive 2I:1:15\n         '
    'Port: 2I\n         Box: 1\n         Bay: 15\n         '
    'Status: OK\n         Drive Type: Data Drive\n         '
    'Interface Type: Solid State SATA\n         '
    'Size: 100 GB\n         Native Block Size: 512\n         '
    'Firmware Revision: 5DV1HPG0\n         '
    'Serial Number: BTTV343306L5100FGN  \n         '
    'Model: ATA     MK0100GCTYU     \n         '
    'SATA NCQ Capable: True\n         '
    'SATA NCQ Enabled: True\n         '
    'Current Temperature (C): 26\n         '
    'Maximum Temperature (C): 43\n         '
    'Usage remaining: 99.97%\n         '
    'Power On Hours: 3843\n         '
    'Estimated Life Remaining based on workload to '
    'date: 533589 days\n         '
    'SSD Smart Trip Wearout: False\n         '
    'PHY Count: 1\n         '
    'PHY Transfer Rate: 6.0Gbps\n         '
    'Drive Authentication Status: OK\n         '
    'Carrier Application Version: 11\n         '
    'Carrier Bootloader Version: 6\n\n'
)

TEST_DISK_LABEL = (
    '''b1415969245
c1415969254
d1415969265
e1415969275
'''
)

TEST_GLOB = ['/etc/swift/object-1.ring.gz']

TEST_GLOB_MULTIPLE = [
    '/etc/swift/object-1.ring.gz',
    '/etc/swift/container-1.ring.gz',
    '/etc/swift/account-1.ring.gz',
    '/etc/swift/object.ring.gz'
]

TEST_JSON = {
    'instance-type': 'baremetal',
    'local-ipv4': '192.168.116.38',
    'reservation-id': 'r-1xvfdeij',
    'local-hostname': ('ov--soswiftstorage1-swiftscaleoutobject1-'
                       '5wj6yyd5lbww.novalocal'),
    'placement': {
        'availability-zone': 'nova'
    },
    'ami-launch-index': '0',
    'public-hostname': ('ov--soswiftstorage1-swiftscaleoutobject1-'
                        '5wj6yyd5lbww.novalocal'),
    'hostname': ('ov--soswiftstorage1-swiftscaleoutobject1-'
                 '5wj6yyd5lbww.novalocal'),
    'ramdisk-id': 'ari-00000003',
    'public-keys': {
        '0': {
            'openssh-key': ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDfubS31rvs'
                            '2owsfv7xQc13pdMfK4cChW5Ce+sTzCTCQ1UHHATAVK5AojhnL'
                            'xoq4R2VaBJDg7qZ4fmu3QZq+aVcZC3gsjile0XJwc/c+52AM5'
                            'TeFz0/ao1J2qaSoiiVgsqjrd945omQ+7GrwLvWBafRgEyzljU'
                            '8qRxmc6VRUE3GDxRXay6lCLtvu9DDGcAahg3SJc6DHSkQb8l1'
                            'CWURbv+fchbQ6Jo35jyuniMzxenpm3ymKcmyFsiHOykXghzSr'
                            'Mtad0gvFAdy39nsZd/ygOKlUA1oBriepdtOk3uIYhfsWL3/W7'
                            'G5+uiLBbOCE03VpYGXI8OnXpZkItIo/KD2PPGh'
                            ' root@hLinux\n')
        }
    },
    'ami-id': 'ami-00000001',
    'kernel-id': 'aki-00000002',
    'public-ipv4': '',
    'block-device-mapping': {
        'ami': 'sda',
        'root': '/dev/sda',
        'ephemeral0': '/dev/sda1'
    },
    'ami-manifest-path': 'FIXME',
    'security-groups': '',
    'instance-action': 'none',
    'instance-id': 'i-00000007'
}

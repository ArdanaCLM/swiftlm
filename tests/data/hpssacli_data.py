# (c) Copyright 2015,2016 Hewlett Packard Enterprise Development LP
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


PHYSICAL_DRIVE_DATA = """

Smart Array P410 in Slot 1

    array A

      physicaldrive 2C:1:1
         Port: 2C
         Box: 1
         Bay: 1
         Status: OK
         Drive Type: Data Drive
         Interface Type: SAS
         Size: 2 TB
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: HPD3
         Serial Number:         YFJMHTZD
         Model: HP      MB2000FBUCL
         Current Temperature (C): 27
         Maximum Temperature (C): 38
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown
"""
PHYSICAL_DRIVE_STATUS_FAIL = PHYSICAL_DRIVE_DATA.replace(
    'Status: OK', 'Status: Fail')

MULTIPLE_PHYSICAL_DRIVE_DATA = """

Smart Array P410 in Slot 1

    array A

      physicaldrive 2C:1:1
         Port: 2C
         Box: 1
         Bay: 1
         Status: OK
         Drive Type: Data Drive
         Interface Type: SAS
         Size: 2 TB
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: HPD3
         Serial Number:         YFJMHTZD
         Model: HP      MB2000FBUCL
         Current Temperature (C): 27
         Maximum Temperature (C): 38
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown

      physicaldrive 2C:1:2
         Port: 2C
         Box: 1
         Bay: 2
         Status: OK
         Drive Type: Data Drive
         Interface Type: SAS
         Size: 2 TB
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: HPD3
         Serial Number:         YFJMHTDZ
         Model: HP      MB2000FBUCL
         Current Temperature (C): 27
         Maximum Temperature (C): 38
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown

    unassigned

      physicaldrive 1I:1:14
         Port: 1I
         Box: 10
         Bay: 20
         Status: OK
         Drive Type: Unassigned Drive
         Interface Type: SAS
         Size: 300 GB
         Native Block Size: 512
         Rotational Speed: 10000
         Firmware Revision: HPDD
         Serial Number: 6SE118DD0000B10811XD
         Model: HP      EG0300FAWHV
         Current Temperature (C): 29
         Maximum Temperature (C): 48
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown
"""
MULTIPLE_PHYSICAL_DRIVE_STATUS_FAIL = MULTIPLE_PHYSICAL_DRIVE_DATA.replace(
    'Status: OK', 'Status: Fail')

LOGICAL_DRIVE_DATA = """

Smart Array P410 in Slot 1

    array L

      Logical Drive: 12
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76404
         Disk Name: /dev/sdl
         Mount Points: /srv/node/disk11 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB69
         Drive Type: Data
         LD Acceleration Method: Controller Cache
"""
LOGICAL_DRIVE_LUN_FAIL = LOGICAL_DRIVE_DATA.replace(
    'Status: OK', 'Status: Fail')
LOGICAL_DRIVE_CACHE_FAIL = LOGICAL_DRIVE_DATA.replace(
    'Caching:  Enabled', 'Caching: Disabled')
LOGICAL_DRIVE_SSD = LOGICAL_DRIVE_CACHE_FAIL.replace(
    'LD Acceleration Method: Controller Cache',
    'LD Acceleration Method: HPE SSD Smart Path')
# Places Disk Name and Mount Points on the same line.
LOGICAL_DRIVE_DATA_BUGGED = """

Smart Array P410 in Slot 1

    array L

      Logical Drive: 12
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76404
         Disk Name: /dev/sdl  \
    Mount Points: /srv/node/disk11 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB69
         Drive Type: Data
         LD Acceleration Method: Controller Cache
"""

MULTIPLE_LOGICAL_DRIVE_DATA = """

Smart Array P410 in Slot 1

    array L

      Logical Drive: 12
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76404
         Disk Name: /dev/sdl
         Mount Points: /srv/node/disk11 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB69
         Drive Type: Data
         LD Acceleration Method: Controller Cache

      Logical Drive: 13
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76405
         Disk Name: /dev/sdm
         Mount Points: /srv/node/disk12 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB70
         Drive Type: Data
         LD Acceleration Method: Controller Cache

    array M

      Logical Drive: 14
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76406
         Disk Name: /dev/sdn
         Mount Points: /srv/node/disk13 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB71
         Drive Type: Data
         LD Acceleration Method: Controller Cache

      Logical Drive: 15
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76407
         Disk Name: /dev/sdo
         Mount Points: /srv/node/disk14 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB72
         Drive Type: Data
         LD Acceleration Method: Controller Cache
"""
MULTIPLE_LOGICAL_DRIVE_LUN_FAIL = MULTIPLE_LOGICAL_DRIVE_DATA.replace(
    'Status: OK', 'Status: Fail')
MULTIPLE_LOGICAL_DRIVE_CACHE_FAIL = MULTIPLE_LOGICAL_DRIVE_DATA.replace(
    'Caching:  Enabled', 'Caching: Disabled')
# Places Disk Name and Mount Points on the same line.
MULTIPLE_LOGICAL_DRIVE_DATA_BUGGED = """

Smart Array P410 in Slot 1

    array L

      Logical Drive: 12
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76404
         Disk Name: /dev/sdl  \
    Mount Points: /srv/node/disk11 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB69
         Drive Type: Data
         LD Acceleration Method: Controller Cache

      Logical Drive: 13
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76405
         Disk Name: /dev/sdm \
    Mount Points: /srv/node/disk12 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB70
         Drive Type: Data
         LD Acceleration Method: Controller Cache

    array M

      Logical Drive: 14
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76406
         Disk Name: /dev/sdn  \
    Mount Points: /srv/node/disk13 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB71
         Drive Type: Data
         LD Acceleration Method: Controller Cache

      Logical Drive: 15
         Size: 1.8 TB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CEA938043498011A76407
         Disk Name: /dev/sdo \
    Mount Points: /srv/node/disk14 1.8 TB Partition Number 2
         OS Status: LOCKED
         Logical Drive Label: AF3C73D8PACCR0M9VZ41S4QEB72
         Drive Type: Data
         LD Acceleration Method: Controller Cache
"""

SMART_ARRAY_DATA = """

Smart Array P410 in Slot 1
   Bus Interface: PCI
   Slot: 1
   Serial Number: PACCR0M9VZ41S4Q
   Cache Serial Number: PACCQID12061TTQ
   RAID 6 (ADG) Status: Disabled
   Controller Status: OK
   Hardware Revision: C
   Firmware Version: 6.60
   Rebuild Priority: Medium
   Expand Priority: Medium
   Surface Scan Delay: 15 secs
   Surface Scan Mode: Idle
   Queue Depth: Automatic
   Monitor and Performance Delay: 60  min
   Elevator Sort: Enabled
   Degraded Performance Optimization: Disabled
   Inconsistency Repair Policy: Disabled
   Wait for Cache Room: Disabled
   PCI Address (Domain:Bus:Device.Function): 0000:03:00.0
   Surface Analysis Inconsistency Notification: Disabled
   Post Prompt Timeout: 15 secs
   Cache Board Present: True
   Cache Status: OK
   Cache Ratio: 25% Read / 75% Write
   Drive Write Cache: Disabled
   Total Cache Size: 256 MB
   Total Cache Memory Available: 144 MB
   No-Battery Write Cache: Disabled
   Cache Backup Power Source: Batteries
   Battery/Capacitor Count: 1
   Battery/Capacitor Status: OK
   SATA NCQ Supported: True
   Number of Ports: 2 Internal only
   Encryption Supported: False
   Driver Name: hpsa
   Driver Version: 3.4.0
   Driver Supports HP SSD Smart Path: False
"""

SMART_ARRAY_CONTROLLER_FAIL = SMART_ARRAY_DATA.replace(
    "Controller Status: OK", "Controller Status: Fail")
SMART_ARRAY_CACHE_FAIL = SMART_ARRAY_DATA.replace(
    "Cache Status: OK", "Cache Status: Fail")
SMART_ARRAY_BATTERY_FAIL = SMART_ARRAY_DATA.replace(
    "Battery/Capacitor Status: OK", "Battery/Capacitor Status: Fail")
SMART_ARRAY_BATTERY_PRESENCE_FAIL = SMART_ARRAY_DATA.replace(
    "Battery/Capacitor Count: 1", "Battery/Capacitor Count: 0")

SMART_ARRAY_DATA_3_CONT = """

Smart Array P410 in Slot 1
   Bus Interface: PCI
   Slot: 1
   Serial Number: PACCR0M9VZ41S4Q
   Cache Serial Number: PACCQID12061TTQ
   RAID 6 (ADG) Status: Disabled
   Controller Status: OK
   Hardware Revision: C
   Firmware Version: 6.60
   Rebuild Priority: Medium
   Expand Priority: Medium
   Surface Scan Delay: 15 secs
   Surface Scan Mode: Idle
   Queue Depth: Automatic
   Monitor and Performance Delay: 60  min
   Elevator Sort: Enabled
   Degraded Performance Optimization: Disabled
   Inconsistency Repair Policy: Disabled
   Wait for Cache Room: Disabled
   PCI Address (Domain:Bus:Device.Function): 0000:03:00.0
   Surface Analysis Inconsistency Notification: Disabled
   Post Prompt Timeout: 15 secs
   Cache Board Present: True
   Cache Status: OK
   Cache Ratio: 25% Read / 75% Write
   Drive Write Cache: Disabled
   Total Cache Size: 256 MB
   Total Cache Memory Available: 144 MB
   No-Battery Write Cache: Disabled
   Cache Backup Power Source: Batteries
   Battery/Capacitor Count: 1
   Battery/Capacitor Status: OK
   SATA NCQ Supported: True
   Number of Ports: 2 Internal only
   Encryption Supported: False
   Driver Name: hpsa
   Driver Version: 3.4.0
   Driver Supports HP SSD Smart Path: False

Smart Array P410 in Slot 3
   Bus Interface: PCI
   Slot: 3
   Serial Number: PACCR0M9VZ41S4P
   Cache Serial Number: PACCQID12061TTP
   RAID 6 (ADG) Status: Disabled
   Controller Status: OK
   Hardware Revision: C
   Firmware Version: 6.60
   Rebuild Priority: Medium
   Expand Priority: Medium
   Surface Scan Delay: 15 secs
   Surface Scan Mode: Idle
   Queue Depth: Automatic
   Monitor and Performance Delay: 60  min
   Elevator Sort: Enabled
   Degraded Performance Optimization: Disabled
   Inconsistency Repair Policy: Disabled
   Wait for Cache Room: Disabled
   PCI Address (Domain:Bus:Device.Function): 0000:03:00.0
   Surface Analysis Inconsistency Notification: Disabled
   Post Prompt Timeout: 15 secs
   Cache Board Present: True
   Cache Status: OK
   Cache Ratio: 25% Read / 75% Write
   Drive Write Cache: Disabled
   Total Cache Size: 256 MB
   Total Cache Memory Available: 144 MB
   No-Battery Write Cache: Disabled
   Cache Backup Power Source: Batteries
   Battery/Capacitor Count: 1
   Battery/Capacitor Status: OK
   SATA NCQ Supported: True
   Number of Ports: 2 Internal only
   Encryption Supported: False
   Driver Name: hpsa
   Driver Version: 3.4.0
   Driver Supports HP SSD Smart Path: False

Smart Array P440ar in Slot 0 (Embedded) (HBA Mode)
   Bus Interface: PCI
   Slot: 0
   Serial Number: PDNLH0BRH7V7GC
   Cache Serial Number: PDNLH0BRH7V7GC
   Controller Status: OK
   Hardware Revision: B
   Firmware Version: 2.14
   Controller Temperature (C): 50
   Number of Ports: 2 Internal only
   Driver Name: hpsa
   Driver Version: 3.4.4
   HBA Mode Enabled: True
   PCI Address (Domain:Bus:Device.Function): 0000:03:00.0
   Negotiated PCIe Data Rate: PCIe 3.0 x8 (7880 MB/s)
   Controller Mode: HBA
   Controller Mode Reboot: Not Required
   Current Power Mode: MaxPerformance
   Host Serial Number: MXQ51906YF

"""

SMART_ARRAY_DATA_FAILED_CACHE = """

Smart Array P410 in Slot 1

CACHE STATUS PROBLEM DETECTED: The cache on this controller has a problem.
                               To prevent data loss, configuration changes to
                               this controller are not allowed.
                               Please replace the cache to be able to continue
                               to configure this controller.

   Bus Interface: PCI
   Slot: 1
   Serial Number: PACCR0M9VZ41S4Q
   Cache Serial Number: PACCQID12061TTQ
   RAID 6 (ADG) Status: Disabled
   Controller Status: OK
   Hardware Revision: C
   Firmware Version: 6.60
   Rebuild Priority: Medium
   Expand Priority: Medium
   Surface Scan Delay: 15 secs
   Surface Scan Mode: Idle
   Queue Depth: Automatic
   Monitor and Performance Delay: 60  min
   Elevator Sort: Enabled
   Degraded Performance Optimization: Disabled
   Inconsistency Repair Policy: Disabled
   Wait for Cache Room: Disabled
   PCI Address (Domain:Bus:Device.Function): 0000:03:00.0
   Surface Analysis Inconsistency Notification: Disabled
   Post Prompt Timeout: 15 secs
   Cache Board Present: True
   Cache Status: OK
   Cache Ratio: 25% Read / 75% Write
   Drive Write Cache: Disabled
   Total Cache Size: 256 MB
   Total Cache Memory Available: 144 MB
   No-Battery Write Cache: Disabled
   Cache Backup Power Source: Batteries
   Battery/Capacitor Count: 1
   Battery/Capacitor Status: OK
   SATA NCQ Supported: True
   Number of Ports: 2 Internal only
   Encryption Supported: False
   Driver Name: hpsa
   Driver Version: 3.4.0
   Driver Supports HP SSD Smart Path: False

Smart Array P410 in Slot 3
   Bus Interface: PCI
   Slot: 3
   Serial Number: PACCR0M9VZ41S4P
   Cache Serial Number: PACCQID12061TTP
   RAID 6 (ADG) Status: Disabled
   Controller Status: OK
   Hardware Revision: C
   Firmware Version: 6.60
   Rebuild Priority: Medium
   Expand Priority: Medium
   Surface Scan Delay: 15 secs
   Surface Scan Mode: Idle
   Queue Depth: Automatic
   Monitor and Performance Delay: 60  min
   Elevator Sort: Enabled
   Degraded Performance Optimization: Disabled
   Inconsistency Repair Policy: Disabled
   Wait for Cache Room: Disabled
   PCI Address (Domain:Bus:Device.Function): 0000:03:00.0
   Surface Analysis Inconsistency Notification: Disabled
   Post Prompt Timeout: 15 secs
   Cache Board Present: True
   Cache Status: OK
   Cache Ratio: 25% Read / 75% Write
   Drive Write Cache: Disabled
   Total Cache Size: 256 MB
   Total Cache Memory Available: 144 MB
   No-Battery Write Cache: Disabled
   Cache Backup Power Source: Batteries
   Battery/Capacitor Count: 1
   Battery/Capacitor Status: OK
   SATA NCQ Supported: True
   Number of Ports: 2 Internal only
   Encryption Supported: False
   Driver Name: hpsa
   Driver Version: 3.4.0
   Driver Supports HP SSD Smart Path: False

"""

SMART_HBA_DATA = """

Smart HBA H240 in Slot 1 (RAID Mode)
   Bus Interface: PCI
   Slot: 1
   Serial Number: PDNNK0ARH9G0AN
   Cache Serial Number: PDNNK0ARH9G0AN
   RAID 6 (ADG) Status: Disabled
   Controller Status: OK
   Hardware Revision: B
   Firmware Version: 3.00
   Rebuild Priority: High
   Surface Scan Delay: 3 secs
   Surface Scan Mode: Idle
   Parallel Surface Scan Supported: Yes
   Current Parallel Surface Scan Count: 1
   Max Parallel Surface Scan Count: 16
   Queue Depth: Automatic
   Monitor and Performance Delay: 60  min
   Elevator Sort: Enabled
   Degraded Performance Optimization: Disabled
   Inconsistency Repair Policy: Disabled
   Wait for Cache Room: Disabled
   Surface Analysis Inconsistency Notification: Disabled
   Post Prompt Timeout: 15 secs
   Cache Board Present: False
   Drive Write Cache: Disabled
   Total Cache Size: 256 MB
   SATA NCQ Supported: True
   Spare Activation Mode: Activate on physical drive failure (default)
   Controller Temperature (C): 42
   Number of Ports: 2 Internal only
   Encryption: Disabled
   Express Local Encryption: False
   Driver Name: hpsa
   Driver Version: 3.4.14
   Driver Supports HP SSD Smart Path: True
   PCI Address (Domain:Bus:Device.Function): 0000:08:00.0
   Negotiated PCIe Data Rate: PCIe 3.0 x8 (7880 MB/s)
   Controller Mode: RAID Mode
   Controller Mode Reboot: Not Required
   Latency Scheduler Setting: Disabled
   Current Power Mode: MaxPerformance
   Host Serial Number: SGH548Y4P5

"""

HBA_MODE_CONTROLLERS = """

Smart Array P840ar in Slot 0 (Embedded) (HBA Mode)
   Bus Interface: PCI
   Slot: 0
   Serial Number: PDNLL0ARH8W03H
   Cache Serial Number: PDNLL0ARH8W03H
   Controller Status: OK
   Hardware Revision: B
   Firmware Version: 3.56
   Controller Temperature (C): 52
   Cache Module Temperature (C): 38
   Number of Ports: 2 Internal only
   Driver Name: hpsa
   Driver Version: 3.4.14
   HBA Mode Enabled: True
   PCI Address (Domain:Bus:Device.Function): 0000:03:00.0
   Negotiated PCIe Data Rate: PCIe 3.0 x8 (7880 MB/s)
   Controller Mode: HBA
   Controller Mode Reboot: Not Required
   Current Power Mode: MaxPerformance
   Host Serial Number: CZ3541HDAH
   Primary Boot Volume: None
   Secondary Boot Volume: None

"""

HBA_MODE_LD = """

Error: The specified device does not have any logical drives.
"""

HPSSACLI_2_14_14_PD_SHOW = """

Smart Array P840ar in Slot 0 (Embedded) (HBA Mode)

   HBA Drives

      physicaldrive 1I:1:13
         Port: 1I
         Box: 1
         Bay: 13
         Status: OK
         Drive Type: HBA Mode Drive
         Interface Type: SAS
         Size: 3 TB
         Drive exposed to OS: True
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: HPD9
         Serial Number: S1Z1D21J0000K5525BMF
         Model: HP      MB3000FCWDH
         Current Temperature (C): 32
         Maximum Temperature (C): 35
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown
         Drive Authentication Status: Not Applicable
         Disk Name: /dev/sda
         Mount Points: /boot/efi 488 MB Part Numb 3, /boot 488 MB Part Numb 4
         Sanitize Erase Supported: False

      physicaldrive 1I:1:14
         Port: 1I
         Box: 1
         Bay: 14
         Status: OK
         Drive Type: HBA Mode Drive
         Interface Type: SAS
         Size: 3 TB
         Drive exposed to OS: True
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: HPD9
         Serial Number: Z1Y3HCZ80000R546JFBL
         Model: HP      MB3000FCWDH
         Current Temperature (C): 34
         Maximum Temperature (C): 38
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown
         Drive Authentication Status: Not Applicable
         Disk Name: /dev/sdb
         Mount Points: /srv/node/disk0 2.7 TB Partition Number 2
         Sanitize Erase Supported: False

      physicaldrive 1I:1:15
         Port: 1I
         Box: 1
         Bay: 15
         Status: OK
         Drive Type: HBA Mode Drive
         Interface Type: SAS
         Size: 3 TB
         Drive exposed to OS: True
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: HPD9
         Serial Number: S1Z1CP160000K5511ANR
         Model: HP      MB3000FCWDH
         Current Temperature (C): 35
         Maximum Temperature (C): 39
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown
         Drive Authentication Status: Not Applicable
         Disk Name: /dev/sdc
         Mount Points: /srv/node/disk1 2.7 TB Partition Number 2
         Sanitize Erase Supported: False

      physicaldrive 2I:1:12
         Port: 2I
         Box: 1
         Bay: 12
         Status: OK
         Drive Type: HBA Mode Drive
         Interface Type: SAS
         Size: 3 TB
         Drive exposed to OS: True
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: HPD9
         Serial Number: S1Z1CPQV0000K5512XDJ
         Model: HP      MB3000FCWDH
         Current Temperature (C): 30
         Maximum Temperature (C): 36
         PHY Count: 2
         PHY Transfer Rate: 6.0Gbps, Unknown
         Drive Authentication Status: Not Applicable
         Disk Name: /dev/sdx
         Mount Points: None
         Sanitize Erase Supported: False

"""

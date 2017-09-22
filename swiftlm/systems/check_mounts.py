
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

from __future__ import print_function

import grp
from math import ceil as ceil
import os
import pwd
import json
from collections import namedtuple

from swiftlm.utils.values import Severity
from swiftlm.utils.metricdata import MetricData
from swiftlm.utils.utility import run_cmd
from swiftlm.utils.utility import Aggregate, SwiftlmCheckFailure
from swiftlm.utils.utility import get_swift_mount_point

DEVICES = '/etc/ansible/facts.d/swift_drive_info.fact'
LABEL_CHECK_DISABLED = '---NA---'

Device = namedtuple('Device', ['device', 'mount', 'label'])

MOUNT_PATH = get_swift_mount_point()


def get_devices():
    """
    Parses ansible facts file in JSON format to discover drives.
    Required facts in the format are shown below.
    {
        ...
        "devices": [{
            "name": "/dev/sd#",
            "swift_drive_name": "disk0",
            "label": "0000000d001",
            ...
            }
        ]
        ...
    }

    label is not currently in the file so we stub it out with NO_LABEL.
    """
    try:
        with open(DEVICES, 'r') as f:
            data = json.load(f)['devices']
    except (IOError, ValueError) as err:
        raise SwiftlmCheckFailure('Failure opening %s: %s' % (DEVICES, err))

    devices = []
    for d in data:
        l = d.get('label', LABEL_CHECK_DISABLED)
        devices.append(Device(
            device=d['name'],
            mount=MOUNT_PATH+d['swift_drive_name'],
            label=l
        ))

    return devices


def is_mounted(d, r):
    return os.path.ismount(d.mount)


def is_mounted_775(d, r):
    # Take the last three digits of the octal repr of the permissions.
    perms = oct(os.stat(d.mount).st_mode)[-3:]
    if perms == '755':
        return True
    else:
        r.msgkey('permissions', perms)
        return False


def is_ug_swift(d, r):
    """Checks mount point is owned by swift"""
    stats = os.stat(d.mount)
    uid = stats.st_uid
    gid = stats.st_gid

    user = pwd.getpwuid(uid).pw_name
    group = grp.getgrgid(gid).gr_name
    if user == group == 'swift':
        return True
    else:
        r.msgkey('user', user)
        r.msgkey('group', group)
        return False


def is_valid_label(d, r):
    if d.label == LABEL_CHECK_DISABLED:
        return True

    rc = run_cmd('xfs_admin -l %s | grep -q %s' % (d.mount, d.label))
    if rc.exitcode == 0:
        return True
    else:
        return False


def is_xfs(d, r):
    rc = run_cmd('mount | grep -qE "%s.*xfs"' % d.mount)
    if rc.exitcode == 0:
        return True
    else:
        return False


def is_valid_xfs(d, r):
    rc = run_cmd('xfs_info %s' % d.mount)
    if rc.exitcode == 0:
        return True
    else:
        return False


BASE_RESULT = MetricData(
    name=__name__,
    messages={
        is_mounted.__name__: '{device} not mounted at {mount}',
        is_mounted_775.__name__: ('{device} mounted at {mount} has permissions'
                                  ' {permissions} not 755'),
        is_ug_swift.__name__: ('{device} mounted at {mount} is not owned by'
                               ' swift, has user: {user}, group: {group}'),
        is_valid_label.__name__: ('{device} mounted at {mount} has invalid '
                                  'label {label}'),
        is_xfs.__name__: '{device} mounted at {mount} is not XFS',
        is_valid_xfs.__name__: '{device} mounted at {mount} is corrupt',
        'ok': '{device} mounted at {mount} ok'
    }
)

DISKUSAGE_RESULT = MetricData(name='diskusage.host', messages={})


def check_mounts():
    results = []
    checks = (
        is_mounted,
        is_mounted_775,
        is_ug_swift,
        is_valid_label,
        is_xfs,
        is_valid_xfs)

    devices = get_devices()
    if not devices:
        raise SwiftlmCheckFailure('No devices found to check. See %s' %
                                  DEVICES)

    for d in devices:
        result = BASE_RESULT.child(dimensions={'mount': d.mount},
                                   msgkeys={'device': d.device,
                                            'label': d.label})
        for check in checks:
            if not check(d, result):
                result.message = check.__name__
                result.value = Severity.fail
                break
        else:
            result.value = Severity.ok

        results.append(result)

    return results


def get_diskusage(device):
    """
    Get diskusage data
    :param device:
    :returns: dictionary containing key data
    """
    try:
        path = os.path.join(device.mount)
        disk = os.statvfs(path)
        used = float(disk.f_blocks - disk.f_bfree)
        avail = float(disk.f_bavail)
        size = float(disk.f_blocks)
        usedpercent = float(ceil(100.0 * used / (used + avail)))
        sizebytes = int(size * disk.f_frsize)
        usedbytes = int(used * disk.f_frsize)
        availbytes = int(avail * disk.f_frsize)
        return {'size': sizebytes, 'used': usedbytes, 'avail': availbytes,
                'usage': usedpercent}
    except IOError:
        return {}


def diskusage():
    results = []
    usage_aggr = Aggregate()
    devices = get_devices()
    for d in devices:
        for key, value in get_diskusage(d).items():
            result = DISKUSAGE_RESULT.child(name='val.' + key,
                                            dimensions={'mount': d.mount},
                                            msgkeys={'device': d.device,
                                                     'label': d.label})
            result.value = value
            results.append(result)
            if key == 'usage':
                usage_aggr.add(value)
    if usage_aggr.count:
        result = DISKUSAGE_RESULT.child(name='max.usage')
        result.value = usage_aggr.max
        results.append(result)
        result = DISKUSAGE_RESULT.child(name='min.usage')
        result.value = usage_aggr.min
        results.append(result)
        result = DISKUSAGE_RESULT.child(name='avg.usage')
        result.value = usage_aggr.avg
        results.append(result)
    return results


def main():
    """Checks the relevant swift mount points and diskusage"""
    results = []
    results.extend(check_mounts())
    results.extend(diskusage())
    return results


if __name__ == "__main__":
    print(main())

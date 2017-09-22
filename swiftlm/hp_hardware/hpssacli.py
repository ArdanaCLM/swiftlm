
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


# Python library for running hpssacli commnads

import re
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
from collections import OrderedDict
from swiftlm.utils.metricdata import MetricData
from swiftlm.utils.values import Severity
from swiftlm.utils.utility import run_cmd
from swiftlm import CONFIG_FILE


LOCK_FILE_COMMAND = '/usr/bin/flock -w 10 /var/lock/hpssacli-swiftlm.lock '
BASE_RESULT = MetricData(
    name=__name__,
    messages={
        'no_battery': 'No cache battery',
        'unknown': 'hpssacli command failed',
        'controller_status': '{sub_component} status is {status}',
        'in_hba_mode': 'Controller is in HBA mode; performance will be poor',
        'physical_drive': 'Drive {serial_number}: '
        '{box}:{bay} has status: {status}',
        'l_drive': 'Logical Drive {logical_drive} has status: {status}',
        'l_cache': 'Logical Drive {logical_drive} has cache status: {caching}',
        'ok': 'OK',
        'fail': 'FAIL',
    }
)

# This is all the data we are looking for in the hpssacli output so we
# will _only_ gather whatever values are in this list
METRIC_KEYS = ['array', 'physicaldrive', 'logical_drive', 'caching',
               'serial_number', 'slot', 'firmware_version',
               'controller_mode',
               'battery_capacitor_presence', 'battery_capacitor_status',
               'controller_status', 'cache_status', 'box', 'bay', 'status',
               'ld acceleration method']


def indent_at(line):
    indent = 0
    for char in line:
        if char.isspace():
            indent += 1
        else:
            break
    return indent


class TextBlock(object):
    """
    Structure to represent the scanning that TextScanner performs. The
    members are as follows:

        text:
            A line of text. This can be a title or attribute/value pair

        subblocks:
            TextBlock objects that are "under" (indented) under the
            above line.
    """
    def __init__(self, text):
        self.text = text
        self.subblocks = []

    def make_subblock(self, text):
        subblock = TextBlock(text)
        self.subblocks.append(subblock)
        return subblock


class TextScanner(object):
    """
    Scans blocks of text

    This scanner processes column-aligned text into a block/subblock
    structure. The result is the TextBlock class, where each block is
    a line of text (title or attribute). Any text indented under the line
    is a listed in the subblocks member (which in turn is another
    TextBlock object.
    """

    def __init__(self, lines):
        self.line_index = None
        self.root_block = TextBlock('root')
        self.scan_text_blocks(lines, -1, self.root_block)

    def scan_text_blocks(self, lines, indent, block):
        '''
        Scan blocks of text recursively

        Normally each line is scanned once (incrementing self.line_index)
        However, if we're called and realise the line is
        an outer block (because indent is less than current), we
        decrement line_index so that we reprocess that line.

        :param lines: an array of lines of text
        :param indent: the current indentation level
        :param block: the outer block
        '''
        if self.line_index is None:
            self.line_index = 0
        while self.line_index < len(lines):
            line = lines[self.line_index]
            self.line_index += 1
            if not line or line.isspace():
                continue
            if indent_at(line) <= indent:
                # Text is outer block -- out block has ended
                self.line_index += -1
                return
            # Text at same level as our peers -- save the text
            subblock = block.make_subblock(line.strip())
            # Look for more lines
            self.scan_text_blocks(lines, indent_at(line), subblock)

    def get_root_block(self):
        return self.root_block


def parse_array_name(text):
    return text.split()[0], text.split()[1].strip(), text


def parse_controller_name(text):
    model = text.strip().split("in Slot")[0].strip()
    controller_key = text.strip().split("(Embedded)")[0].strip()
    return model, controller_key


def parse_ld_name(text):
    return parse_attribute(text, underscoring=False)


def parse_attribute(text, underscoring=True):
    try:
        k, v = text.split(': ', 1)
    except ValueError:
        raise
    k = k.strip().lower()
    if underscoring:
        k = re.sub('[/|() ]', '_', k)
    return k, v.strip()


def parse_cont_attribute(attribute, info, slots=None):
    try:
        k, v = parse_attribute(attribute.text)
    except ValueError:
        raise
    if 'slot' in k:
        slots.append(v)
    if 'battery_capacitor_count' in k:
        k = 'battery_capacitor_presence'
    if any(k in s for s in METRIC_KEYS):
        info.update({k: v})


def get_smart_array_info():
    """
    Function entry point used by cinderlm
    """
    return get_controller_info()


def get_controller_info():
    """
    parses controller data from hpssacli in the form.
    returns a dict.
    key's are lowercased versions of the key name on each line,
    including special characters.
    Values are not changed.

    keys 'model' and 'slot' are parsed from the first line

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
    results = []
    controller_slots = []
    controller_result = BASE_RESULT.child()
    controller_result.name += '.' + 'smart_array'

    rc = run_cmd(LOCK_FILE_COMMAND + 'hpssacli ctrl all show detail')

    if rc.exitcode != 0:
        if 'Error: No controllers detected.' in str(rc.output):
            return [[], []]
        if len(rc.output) > 1847:
            rc = rc._replace(exitcode=rc.exitcode,
                             output='...' + rc.output[-1844:])
        raise Exception('{0}: hpssacli ctrl all show detail '
                        'failed with exit code: {1}'.format(
                            rc.output, rc.exitcode))

    if rc.output:
        lines = rc.output.split('\n')
    else:
        raise Exception('{0}: hpssacli ctrl all show detail '
                        'failed with exit code: {1}'.format(
                            rc.output, rc.exitcode))

    info = []
    text_scanner = TextScanner(lines)
    root = text_scanner.get_root_block()
    c_info = None
    # Extract controller information
    for controller in root.subblocks:
        line = controller.text
        if line.startswith('Smart Array') or line.startswith('Smart HBA'):
            model, _ = parse_controller_name(line)
            c_info = {'model': model}
            info.append(c_info)

            # Process controller attributes
            for attribute in controller.subblocks:
                parse_cont_attribute(attribute, c_info, controller_slots)

        elif line.startswith('CACHE STATUS'):
            for attribute in controller.subblocks:
                # Process controller attributes
                att = attribute.text
                if ': ' in att and c_info:
                    parse_cont_attribute(attribute, c_info, controller_slots)
        else:
            # Unknown controller type
            continue

    # Walk dictionary to gather controller metrics
    for c_info in info:
        results.extend(check_controller(c_info, controller_result))

    return results, controller_slots


def check_controller(c, base):
    results = []
    base = base.child(dimensions={
        'model': c.get('model', 'NA'),
        'controller_slot': c.get('slot', 'NA'),
        'component': 'controller',
    })

    # Firmware version
    try:
        f = c.get('firmware_version', '0')
        f = float(f)
    except ValueError:
        f = 0
    r = base.child()
    r.name += '.' + 'firmware'
    r.value = f
    results.append(r)

    # Check for HBA mode
    try:
        hba_mode = c.get('controller_mode', 'not-hba')
    except ValueError:
        hba_mode = 'not-hba'
    r = base.child()
    r['sub_component'] = 'controller_not_hba_mode'
    if hba_mode == 'HBA':
        r.value = Severity.fail
        r.message = 'in_hba_mode'
        results.append(r)
        return results  # no point in looking at cache, battery, etc.
    else:
        r.value = Severity.ok
    results.append(r)

    # Battery presence
    try:
        bcp = c.get('battery_capacitor_presence', '0')
        bcp = int(bcp)
    except ValueError:
        bcp = 0
    r = base.child()
    r['sub_component'] = 'battery_capacitor_presence'
    if bcp < 1:
        r.value = Severity.fail
        r.message = 'no_battery'
    else:
        r.value = Severity.ok
    results.append(r)

    # Statuses
    for i in ('controller_status', 'cache_status', 'battery_capacitor_status'):
        s = c.get(i, 'NA')
        r = base.child()
        r['sub_component'] = i
        r.msgkey('status', s)
        if s != 'OK':
            r.value = Severity.fail
            r.message = 'controller_status'
        else:
            r.value = Severity.ok
        results.append(r)

    return results


def get_physical_drive_info(controller_slot):
    """
    Parses drive data from hpssacli in the form.
    There are multiple drives in the output.

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
    results = []
    drive_result = BASE_RESULT.child(dimensions={
        'controller_slot': str(controller_slot)
    })
    drive_result.name += '.physical_drive'
    rc = run_cmd(
        LOCK_FILE_COMMAND + 'hpssacli ctrl slot=%s pd all show detail'
                            % controller_slot)

    if rc.exitcode != 0:
        if len(rc.output) > 1847:
            rc = rc._replace(exitcode=rc.exitcode,
                             output='...' + rc.output[-1844:])
        raise Exception('{0}: hpssacli ctrl slot={1} pd all show detail '
                        'failed with exit code: {2}'.format(
                            rc.output, controller_slot, rc.exitcode))

    lines = rc.output.split('\n')
    if lines == ['']:
        raise Exception('{0}: hpssacli ctrl slot={1} pd all show detail '
                        'failed with exit code: {2}'.format(
                            rc.output, controller_slot, rc.exitcode))

    drive_info = []
    text_scanner = TextScanner(lines)
    root = text_scanner.get_root_block()

    # Extract drive information
    for controller in root.subblocks:
        line = controller.text
        if line.startswith("Smart Array"):
            _, controller_key = parse_controller_name(line)
            for assignment in controller.subblocks:
                line = assignment.text
                if "array" in line:
                    # drives assigned to a LUN
                    pass
                elif "hba drives" in line.lower():
                    # controller in HBA mode
                    pass
                elif "unassigned" in line.lower():
                    # Unassigned drives are probably unassigned for a reason
                    # (such as failed) so we'll ignore them
                    continue
                else:
                    # Unrecognised assignment - ignore
                    continue

                for pd in assignment.subblocks:
                    # Parse drive attributes
                    pd_data = {}
                    for attribute in pd.subblocks:
                        parse_cont_attribute(attribute, pd_data)

                    drive_info.append(pd_data)

    # Now walk drive_info to get metrics' data from the controller(s),
    # array(s), physical drive(s), and logical drive(s)
    for pd_data in drive_info:
        results.extend(check_physical_drive(pd_data, drive_result))
    return results


def check_physical_drive(d, base):
    r = base.child(dimensions={
        'box': d.get('box', 'NA'), 'bay': d.get('bay', 'NA'),
        'component': 'physical_drive'},
        msgkeys={'status': d.get('status', 'NA'), 'serial_number': d.get(
            'serial_number', 'NA')})

    if d.get('status', 'NA') != 'OK':
        r.value = Severity.fail
        r.message = 'physical_drive'
    else:
        r.value = Severity.ok

    return [r]


def get_logical_drive_info(controller_slot, cache_check=True):
    """
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
    results = []
    drive_result = BASE_RESULT.child(dimensions={
        'controller_slot': controller_slot
        })
    drive_result.name += '.' + 'logical_drive'
    rc = run_cmd(
        LOCK_FILE_COMMAND + 'hpssacli ctrl slot=%s ld all show detail'
                            % controller_slot)

    if rc.exitcode != 0:
        if len(rc.output) > 1847:
            rc = rc._replace(exitcode=rc.exitcode,
                             output='...' + rc.output[-1844:])
        raise Exception('{0}: hpssacli ctrl slot={1} ld all show detail '
                        'failed with exit code: {2}'.format(
                            rc.output, controller_slot, rc.exitcode))

    lines = rc.output.split('\n')
    if lines == ['']:
        raise Exception('{0}: hpssacli ctrl slot={1} ld all show detail '
                        'failed with exit code: {2}'.format(
                            rc.output, controller_slot, rc.exitcode))

    drive_info = []
    text_scanner = TextScanner(lines)
    root = text_scanner.get_root_block()

    # Extract logical drive information
    for controller in root.subblocks:
        line = controller.text
        if line.startswith("Smart Array"):
            for array in controller.subblocks:
                line = array.text
                if "array" in line:
                    _, array_letter, array_name = parse_array_name(line)
                    for lun in array.subblocks:
                        line = lun.text
                        if "Logical Drive:" in line:
                            logical_drive = line.strip()
                            try:
                                _, ld_num = parse_ld_name(line)
                                ld_data = {'array': array_letter,
                                           'logical_drive': ld_num}
                            except ValueError:
                                continue
                            for attribute in lun.subblocks:
                                line = attribute.text
                                try:
                                    k, v = parse_attribute(line,
                                                           underscoring=False)
                                except ValueError:
                                    continue
                                if any(k in s for s in METRIC_KEYS):
                                    ld_data.update({k: v})
                            drive_info.append(ld_data)

    # Now walk the LUNs and check them
    for ld_data in drive_info:
        results.extend(check_logical_drive(ld_data, drive_result, cache_check))

    return results


def check_logical_drive(d, base, cache_check):
    results = []
    base = base.child(dimensions={
                      'component': 'logical_drive',
                      'array': d.get('array', 'NA'),
                      'logical_drive': d.get('logical_drive', 'NA')},
                      msgkeys={'status': d.get('status', 'NA'),
                               'caching': d.get('caching', 'NA')})
    r = base.child()
    r['sub_component'] = 'lun_status'
    if d.get('status', 'NA') != 'OK':
        r.value = Severity.fail
        r.message = 'l_drive'
    else:
        r.value = Severity.ok
    results.append(r)

    if cache_check:
        r = base.child()
        r['sub_component'] = 'cache_status'
        cache_must_be_enabled = True
        if d.get('ld acceleration method', 'NA') == 'HPE SSD Smart Path':
            cache_must_be_enabled = False
        if cache_must_be_enabled and d.get('caching', 'NA') != 'Enabled':
            r.value = Severity.fail
            r.message = 'l_cache'
        else:
            r.value = Severity.ok
        results.append(r)
    return results


def main():
    """Check controller and drive information with hpssacli"""
    cache_check = True
    try:
        cp = configparser.RawConfigParser()
        cp.read(CONFIG_FILE)
        cc = cp.getboolean('hpssacli', 'check_cache')
        if not cc:
            cache_check = False
    except Exception:
        pass

    results, controller_slots = get_controller_info()

    for controller_slot in controller_slots:
        results.extend(get_physical_drive_info(controller_slot))
        results.extend(get_logical_drive_info(controller_slot,
                                              cache_check=cache_check))

    return results

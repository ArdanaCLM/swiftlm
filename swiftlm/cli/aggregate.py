#
# (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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

"""
    Aggregate scouted data and produce metric file
"""

import json
import optparse
import socket
import sys
import time
import yaml
from swiftlm.utils.scout import SwiftlmScout
from swiftlm.utils.utility import Aggregate, lock_file


def process_collected(data, desired, dimensions, timestamp):
    """
    Process collected data and derive aggregated metrics
    :param data: the data from scouting the nodes
    :param desired: a list of aggregations to perform
    :return: metrics
    """
    metrics = []
    if 'async' in desired:
        async(data, metrics, dimensions, timestamp)
    if 'diskusage' in desired:
        diskusage(data, metrics, dimensions, timestamp)
    if 'ringmd5' in desired:
        ringmd5(data, metrics, dimensions, timestamp)
    if 'load' in desired:
        load(data, metrics, dimensions, timestamp)
    if 'replication' in desired:
        replication(data, metrics, dimensions, timestamp)
    return metrics


def async(data, metrics, dimensions, timestamp):
    agr = Aggregate()
    if not data.get('async'):
        return
    for name, item in data.get('async').items():
        try:
            agr.add(item.get('async_pending'))
        except TypeError:
            pass
    metrics.append({'metric': 'swiftlm.async_pending.cp.total.queue_length',
                    'dimensions': dimensions,
                    'value': agr.total,
                    'value_meta': {},
                    'timestamp': timestamp})


def diskusage(data, metrics, dimensions, timestamp):
    avail = Aggregate()
    used = Aggregate()
    size = Aggregate()
    usage = Aggregate()
    if not data.get('diskusage'):
        return

    for name, drives in data.get('diskusage').items():
        try:
            for drive in drives:
                try:
                    avail.add(int(drive.get('avail')))
                    used.add(int(drive.get('used')))
                    size.add(int(drive.get('size')))
                    usage.add(100.0 *
                              float(drive.get('used')) /
                              float(drive.get('size')))
                except ValueError:
                        pass  # directory in /srv/node, not mounted FS
        except TypeError:
            pass
    metrics.append({'metric': 'swiftlm.diskusage.cp.total.avail',
                    'dimensions': dimensions,
                    'value': avail.total,
                    'value_meta': {},
                    'timestamp': timestamp})
    metrics.append({'metric': 'swiftlm.diskusage.cp.total.used',
                    'dimensions': dimensions,
                    'value': used.total,
                    'value_meta': {},
                    'timestamp': timestamp})
    metrics.append({'metric': 'swiftlm.diskusage.cp.total.size',
                    'dimensions': dimensions,
                    'value': size.total,
                    'value_meta': {},
                    'timestamp': timestamp})
    metrics.append({'metric': 'swiftlm.diskusage.cp.avg.usage',
                    'dimensions': dimensions,
                    'value': usage.avg,
                    'value_meta': {},
                    'timestamp': timestamp})
    metrics.append({'metric': 'swiftlm.diskusage.cp.min.usage',
                    'dimensions': dimensions,
                    'value': usage.min,
                    'value_meta': {},
                    'timestamp': timestamp})
    metrics.append({'metric': 'swiftlm.diskusage.cp.max.usage',
                    'dimensions': dimensions,
                    'value': usage.max,
                    'value_meta': {},
                    'timestamp': timestamp})


def replication(data, metrics, dimensions, timestamp):
    # Object data can be in either replication or replication/object
    # Object keys are prefixed with object_. The a/c are not.
    object_data = data.get('replication', data.get('replication/object', {}))
    account_data = data.get('replication/account', {})
    container_data = data.get('replication/container', {})
    for pre, styp, data in [(p, s, d) for (p, s, d) in [
            ('object_', 'object', object_data),
            ('', 'account', account_data),
            ('', 'container', container_data)]
            if d]:
        last = Aggregate()
        duration = Aggregate()
        for name, item in data.items():
            try:
                replication_last = item.get('%sreplication_last' % pre)
                ago = time.time() - replication_last
                last.add(ago)
                duration.add(item.get('%sreplication_time' % pre))
            except TypeError:
                pass
        replication_dimensions = dict(dimensions)  # make copy
        replication_dimensions.update({'component': '%s-replicator' % styp})
        metrics.append({'metric': 'swiftlm.replication.cp.max.%s_last' % styp,
                        'dimensions': replication_dimensions,
                        'value': last.max,
                        'value_meta': {},
                        'timestamp': timestamp})
        metrics.append({'metric': 'swiftlm.replication.cp.avg.'
                                  '%s_duration' % styp,
                        'dimensions': replication_dimensions,
                        'value': duration.avg,
                        'value_meta': {},
                        'timestamp': timestamp})


def load(data, metrics, dimensions, timestamp):
    if not data.get('load'):
        return
    fivemin = Aggregate()
    for host, item in data.get('load').items():
        try:
            fivemin.add(item.get('5m', 0))
        except TypeError:
            pass
    metrics.append({'metric': 'swiftlm.load.cp.avg.five',
                    'dimensions': dimensions,
                    'value': fivemin.avg,
                    'value_meta': {},
                    'timestamp': timestamp})
    metrics.append({'metric': 'swiftlm.load.cp.max.five',
                    'dimensions': dimensions,
                    'value': fivemin.max,
                    'value_meta': {},
                    'timestamp': timestamp})
    metrics.append({'metric': 'swiftlm.load.cp.min.five',
                    'dimensions': dimensions,
                    'value': fivemin.min,
                    'value_meta': {},
                    'timestamp': timestamp})


def ringmd5(data, metrics, dimensions, timestamp):
    if not data.get('ringmd5'):
        return
    ringdata = {}
    hostdata = {}
    for host, rings in data.get('ringmd5').items():
        try:
            for ringname, checksum in rings.items():
                if not ringdata.get(ringname):
                    ringdata[ringname] = set([checksum])
                else:
                    ringdata[ringname].add(checksum)
                if not hostdata.get(host):
                    hostdata[host] = [ringname]
                else:
                    hostdata[host].append(ringname)
        except TypeError:
            pass
    problem = False
    for ring, checksums in ringdata.items():
        if len(checksums) > 1:
            # Checksums differ
            problem = True
    expected_number_rings = None
    for host, rings in hostdata.items():
        if expected_number_rings is None:
            # Use first host as canonical
            expected_number_rings = len(rings)
        if expected_number_rings != len(rings):
            # This host has different number of rings than first host
            problem = True
    if problem:
        value = 2
        msg = 'Checksum or number of rings not the same on all hosts'
    else:
        value = 0
        msg = 'Rings are consistent on all hosts'
    metrics.append({'metric': 'swiftlm.md5sum.cp.check.ring_checksums',
                    'dimensions': dimensions,
                    'value': value,
                    'value_meta': {'msg': msg},
                    'timestamp': timestamp})


def scout_main():
        """
        Gather data and create metrics output
        """
        usage = '''
        usage: {prog} [--metrics= <file> | -]
                      [--conf=<file>]
                      [--all] | [--async] [--diskusage] [--ringmd5]
                                [--replication] [--load]
                      [--timeout=<seconds>]
                      [--verbose]
                      [--outformat= yaml | json]

        Examples:
            {prog} --all --metrics=/var/cache/swiftlm/aggregated.json
            cat /var/cache/swiftlm/aggregated.json | python -mjson.tool

            {prog} --async --outformat=yaml
        '''.format(prog='swiftlm-aggregate')
        args = optparse.OptionParser(usage)
        args.add_option('--metrics', metavar='METRICS_FILE', default=None,
                        help='File to dump metrics into')
        args.add_option('--all', action='store_true', default=False,
                        help='Aggregate everything')
        args.add_option('--async', action='store_true', default=False,
                        help='Aggregate async')
        args.add_option('--diskusage', action='store_true', default=False,
                        help='Aggregate disk usage')
        args.add_option('--ringmd5', action='store_true', default=False,
                        help='Check ringmd5')
        args.add_option('--load', action='store_true', default=False,
                        help='Aggregate 5m load average')
        args.add_option('--replication', action='store_true', default=False,
                        help='Aggregate replication data')
        args.add_option('--outformat', type='string', metavar='FORMAT',
                        help='Format of output.'
                        ' Supported values are:'
                        ' "yaml", "json" (default)',
                        default='json')
        args.add_option('--timeout', type='int', metavar='SECONDS',
                        help='Time to wait for a response from a server',
                        default=5)
        args.add_option('--conf', default='/etc/swiftlm/scout.conf',
                        help='Reserved for future use')
        args.add_option('--verbose', action='store_true',
                        help='Print verbose info. Useful to troubleshoot.')
        args.add_option('--show_errors', action='store_true',
                        default=False,
                        help='Do not suppress errors')
        options, arguments = args.parse_args()
        aggregations = set()
        if options.all:
            aggregations = set(['async', 'diskusage', 'ringmd5', 'load',
                                'replication'])
        if options.async:
            aggregations.add('async')
        if options.diskusage:
            aggregations.add('diskusage')
        if options.ringmd5:
            aggregations.add('ringmd5')
        if options.load:
            aggregations.add('load')
        if options.replication:
            aggregations.add('replication')

        dimensions = {'service': 'object-storage',
                      'observer_host': socket.gethostname(),
                      'hostname': '_'}
        timestamp = time.time()
        suppress_errors = True
        if options.show_errors:
            suppress_errors = False
        if options.verbose:
            suppress_errors = False

        recon_data = SwiftlmScout({},
                                  suppress_errors=suppress_errors,
                                  verbose=options.verbose,
                                  timeout=options.timeout)

        recon_data.scout_aggregate()
        collected = recon_data.get_results()

        metrics = process_collected(collected, aggregations, dimensions,
                                    timestamp)
        if options.outformat == 'json':
            items = []
            for item in metrics:
                items.append(json.dumps(item))
            dumped_metrics = '[\n'
            dumped_metrics += ',\n'.join(items)
            dumped_metrics += '\n]\n'
        elif options.outformat == 'yaml':
            dumped_metrics = yaml.safe_dump(metrics, allow_unicode=True,
                                            default_flow_style=False)
        else:
            print('Invalid value for --outformat')
            sys.exit(1)
        out_stream = sys.stdout
        if options.metrics:
            if options.metrics == '-':
                out_stream = sys.stdout
                out_stream.write(dumped_metrics)
            else:
                try:
                    with lock_file(options.metrics, 2, unlink=False) as cf:
                        cf.truncate()
                        cf.write(dumped_metrics)
                except (Exception, Timeout) as err:
                    print('ERROR: %s' % err)
                    sys.exit(1)


def main():
    try:
        scout_main()
    except KeyboardInterrupt:
        print('\n')


if __name__ == '__main__':
    main()

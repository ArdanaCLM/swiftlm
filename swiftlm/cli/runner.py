# encoding: utf-8

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

import argparse
import pkg_resources
import json
import sys
import traceback
import yaml

from swiftlm.utils.metricdata import MetricData
from swiftlm.utils.values import Severity
from swiftlm.utils.utility import SwiftlmCheckFailure, lock_file


def display_json(metrics, pretty):
    dumped_metrics = ''
    if pretty:
        kwargs = {
            'sort_keys': True,
            'indent': 2,
        }
        dumped_metrics = json.dumps(metrics, **kwargs)
    else:
        items = []
        for item in metrics:
            items.append(json.dumps(item))
        dumped_metrics = '[\n'
        dumped_metrics += ',\n'.join(items)
        dumped_metrics += '\n]\n'
    return dumped_metrics


def display_yaml(metrics, pretty):
    yaml.add_representer(Severity, Severity.yaml_repr, yaml.SafeDumper)
    kwargs = {}
    if pretty:
        kwargs = {'default_flow_style': False}

    return(yaml.safe_dump(metrics, **kwargs))


FORMATS = {
    'json': display_json,
    'yaml': display_yaml,
}


def construct_parser(plugins):
    parser = argparse.ArgumentParser(description='XXX')

    # Create a flag for each plugin that adds the matching function to the
    # selected list if it appears on the command line.
    selection_group = parser.add_argument_group(
        'Available Checks',
        'Select one or more of the available checks to run as a subset.'
    )
    for name, unloaded_func in plugins.items():
        func = unloaded_func.load()
        help_string = func.__doc__ or 'Reserved for future use.'

        selection_group.add_argument(
            '--' + name,
            dest='selected',
            action='append_const',
            const=func,
            help=help_string
        )

    parser.add_argument(
        '--format',
        choices=FORMATS.keys(),
        default='json',
        help='Format output (default: %(default)s).'
    )
    parser.add_argument(
        '-p', '--pretty',
        action='store_true',
        help='Format output in a more easy to read way.'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count'
    )
    parser.add_argument(
        '--filename', metavar='<FILENAME>',
        default=False, help='File to store scan results into'
    )

    return parser


def parse_args():
    ps = pkg_resources.get_entry_map('swiftlm', 'swiftlm.plugins')
    p = construct_parser(ps)
    args = p.parse_args()

    # we make the common case easy, No selected flags indicate that we should
    # run all diagnostics.
    if args.selected is None:
        args.selected = [f.load() for f in ps.values()]

    return args


def main():
    args = parse_args()
    metrics = []

    for func in args.selected:
        try:
            r = func()
            if isinstance(r, list) and r and isinstance(r[0], MetricData):
                metrics.extend([result.metric() for result in r])
            elif isinstance(r, MetricData):
                metrics.append(r.metric())
        except SwiftlmCheckFailure as err:
            r = MetricData.single('check.failure', Severity.fail,
                                  '{error} | Failed with: {check}',
                                  dimensions={'component': 'swiftlm-scan',
                                              'service': 'object-storage'},
                                  msgkeys={'check': func.__module__,
                                           'error': str(err)})
            metrics.append(r.metric())
        except:   # noqa
            t, v, tb = sys.exc_info()
            backtrace = ' '.join(traceback.format_exception(t, v, tb))
            r = MetricData.single('check.failure', Severity.fail,
                                  '{error} | Failed with: {check}',
                                  dimensions={'component': 'swiftlm-scan',
                                              'service': 'object-storage'},
                                  msgkeys={'check': func.__module__,
                                           'error':
                                               backtrace.replace('\n', ' ')})
            metrics.append(r.metric())

    # There is no point in reporting multiple measurements of
    # swiftlm.check.failure metric in same cycle.
    check_failures_found = []
    for metric in metrics:
        if metric.get('metric') == 'swiftlm.check.failure':
            check_failures_found.append(metric)
    if check_failures_found:
        # Remove all except one instance
        for metric in check_failures_found[:-1]:
            metrics.remove(metric)
    else:
        r = MetricData.single('check.failure', Severity.ok, 'ok',
                              dimensions={'component': 'swiftlm-scan',
                                          'service': 'object-storage'})
        metrics.append(r.metric())

    dumped_metrics = FORMATS[args.format](metrics, args.pretty)

    out_stream = sys.stdout
    if args.filename:
        try:
            with lock_file(args.filename, 2, unlink=False) as cf:
                cf.truncate()
                cf.write(dumped_metrics)
        except (Exception, Timeout) as err:
            print('ERROR: %s' % err)
            sys.exit(1)
    else:
        out_stream = sys.stdout
        out_stream.write(dumped_metrics)


if __name__ == '__main__':
    main()

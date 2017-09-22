#!/usr/bin/python

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

import sys
from os import environ
from time import sleep
import datetime
from optparse import OptionParser
import json
from swiftlm.utils.jahmonapi import JahmonConnection, JahmonClientException


verbose = False


def print_verbose(msg):
    global verbose
    if verbose:
        print(msg)


def print_result(result, fmt='compact'):
    name = result.get('name')
    dimensions = result.get('dimensions', {})
    timestamp = result.get('timestamp', '')
    value = result.get('value', '')
    meta = result.get('value_meta', {})
    if fmt == 'compact':
        dimvals = []
        for key, val in dimensions.items():
            dimvals.append(val)
        valuemeta = []
        for key, val in meta.items():
            valuemeta.append(val)
        dimmsg = ','.join(dimvals)
        valmsg = ','.join(valuemeta)
        print('%s %s %s {%s} {%s}' % (timestamp, name, value, dimmsg, valmsg))
    elif fmt == 'flat':
        print('%s %s %s %s %s' % (timestamp, name, value,
                                  json.dumps(dimensions),
                                  json.dumps(meta)))
    elif fmt == 'json':
        out = {'name': name, 'timestamp': timestamp, 'value': value,
               'dimensions': dimensions, 'value_meta': meta}
        print('%s' % json.dumps(out))


def main():
    global verbose
    usage = '''
Usage:

    Set environment variables

    export OS_USERNAME=name
    export OS_PASSWORD=secret
    export OS_AUTH_URL=https://region-a.geo-1.identity.hpcloudsvc.com/v2.0
    export OS_REGION_NAME=region-a.geo-1
    export OS_PROJECT_ID=12345678912345

    OR
    unset OS_AUTH_URL
    {name} <verb>
            --url=http://192.168.245.9:8070/v2.0
            --token=HPAuth1234

    Convenience Functions

    List metrics -- one metric per line.
    {name} metrics [--metric_name=<name>]
                   [--dim=<name>:<value>]...

    List metrics/measurements. This first gets all metrics matching the
    name and dimensions and then for each metric, gets the measurements.
    Unlike the merge_metrics feature of the Monasca API, this lists the
    metric associated with each measurement. However, the data may not be
    sorted by time.
    The output format is specified with --format. Note: the JSON format
    outputs JSON on each line -- the output as a whole is not JSON.
    The data is not necessarily in timestamp order.
    Even
    {name} find [--metric_name=<name>]
                [--dim=<name>:<value>]...
                --start_time= -<minutes> | yyyy:mm:ddThh:mm.000Z
                --end_time= 0 | -1 | -2 | yyyy:mm:ddThh:mm.000Z
                [--format compact | flat | json]
                [--merge_metrics]
                [--count=<number>]

    List merged metrics/measurements.
    {name} merge [--metric_name=<name>]
                 [--dim=<name>:<value>]...
                 --start_time= -<minutes> | yyyy:mm:ddThh:mm.000Z
                 --end_time= 0 | -1 | -2 | yyyy:mm:ddThh:mm.000Z
                 [--format= compact | flat | json]
                 [--count=<number>]

    Tail metrics/measurements. This is similar to find except that it runs
    continuously. The timestamps may not be in order.
    NOTE: it will not show metrics posted less than two minutes ago.
    {name} tail [--metric_name=<name>]
                [--dim=<name>:<value>]...
                --format compact | flat | json

    Aggregate measurements. This prints the average, min, max, total and
    count of a given metric.
    {name} aggregate -metric_name=<name>  [--dim=<name>:<value>]...

    Monasca API Wrappers

    These are thin wrappers for the corresponding API function.

    Get versions
    {name} versions

    Post a metric/measurement: POST /metrics API
    {name} post_metric --metric_name=<name>
                       --value=123.45 [--dim=<name>:<value>]...
                       [--value_meta=<name>:<value>]...

    List metrics: GET /metrics API
    {name} metrics_api [--metric_name=<name>]
                       [--dim=<name>:<value>]...

    Get measurements. GET /metrics/measurements
    {name} meas  --metric_name=<name>
                 [--dim=<name>:<value>]...
                 --start_time= -<minutes> | yyyy:mm:ddThh:mm.000Z
                 --end_time= 0 | -<minutes> | yyyy:mm:ddThh:mm.000Z
                 --offset=yyyy:mm:ddThh:mm.000Z
                 [--merge_metrics]

Examples:

    {name} post_metric --metric_name=disk_read_bytes_count
                       --dim=az:2 --dim=instance_id:2741581
                       --value=48523.0
                       --value_meta=msg:hi_there

    {name} find --dim=service:object-storage
     --metric_name=swiftlm.swift.swift_services
     --start_time=-2 --end_time=0 --format=compact

    {name} tail --dim=service:object-storage
                --dim=hostname:standard-ccp-c1-m1-mgmt

    {name} aggregate --metric_name=swiftlm.avg_latency_sec
                 --dim=component:rest-api --start_time=-100000 --end_time=0
    '''.format(name='swiftlm-monasca')
    https_proxy = environ.get('https_proxy', None)
    if https_proxy:
        print 'I suggest you unset https_proxy and try again.'
        sys.exit(1)
    parser = OptionParser(usage=usage)
    parser.add_option('--metric_name', dest='metric_name',
                      help='The metric name')
    parser.add_option('--value', dest='value', help='Value (as integer/float)')
    parser.add_option('--dim', dest='dim_list', action='append', default=None,
                      help='A dimension. Format as name:value.'
                           ' For multiple dimensions, repeat --dim')
    parser.add_option('--value_meta', dest='vm_list', action='append',
                      default=None, help='Value meta. Format name:value')
    parser.add_option('--start_time', dest='start_time', default=None,
                      help='Start time. Express as negative minutes ago'
                           ' or as UTC. Examples: -2,'
                           ' 2015-11-24T10:42:29.000Z')
    parser.add_option('--end_time', dest='end_time', default='0',
                      help='End time. Same format as --start-time except also'
                           ' accepts "0" to mean "now"')
    parser.add_option('--offset', dest='offset', default=None,
                      help='Offset as used in Monasca a API. Not needed by'
                           ' the convenience functions')
    parser.add_option('--merge_metrics', dest='merge_metrics', default=False,
                      action='store_true', help='As used by Monasca API')
    parser.add_option('--count', dest='count', default=None,
                      help='Number of measurements to get (per metric)')
    parser.add_option('--format', dest='fmt', default='flat',
                      help='Output format (some functions only). Options'
                           ' are "compact", "flat" or "json". Default is'
                           ' "flat". ')
    parser.add_option('--url', dest='jahmon_url', default=None,
                      help='Monasca endpoint (use with --token).')
    parser.add_option('--token', dest='jahmon_token', default=None,
                      help='A token (used with --jahmon_url)')
    parser.add_option('--verbose', dest='verbose', action='store_true',
                      default=False)
    (options, args) = parser.parse_args()

    os_username = environ.get('OS_USERNAME', None)
    os_password = environ.get('OS_PASSWORD', None)
    os_region_name = environ.get('OS_REGION_NAME', None)
    os_auth_url = environ.get('OS_AUTH_URL', None)
    os_project_id = environ.get('OS_TENANT_ID',
                                environ.get('OS_PROJECT_ID', None))
    os_project_name = environ.get('OS_TENANT_NAME',
                                  environ.get('OS_PROJECT_NAME', None))
    os_user_id = environ.get('OS_USER_ID', None)
    os_user_domain_name = environ.get('OS_USER_DOMAIN_NAME', None)
    os_user_domain_id = environ.get('OS_USER_DOMAIN_ID', None)
    os_project_domain_name = environ.get('OS_PROJECT_DOMAIN_NAME', None)
    os_project_domain_id = environ.get('OS_PROJECT_DOMAIN_ID', None)
    if options.jahmon_url:
        os_username = os_password = os_region_name = os_auth_url = None
        os_project_id = None
    if not len(args) == 1:
        print 'Invalid number of arguments'
        sys.exit(1)

    if not options.dim_list:
        options.dim_list = []
    dimensions = {}
    for dim in options.dim_list:
        name, val = dim.split(':', 1)
        dimensions[name] = val
    if not options.vm_list:
        options.vm_list = []
    value_meta = {}
    for vm in options.vm_list:
        name, val = vm.split(':', 1)
        value_meta[name] = val
    if options.start_time:
        if options.start_time == '0':
            pass
        elif options.start_time.startswith('-'):
            try:
                float(options.start_time)
            except ValueError:
                print('Invalid --start_time')
                sys.exit(1)
        else:
            try:
                datetime.datetime.strptime(options.start_time,
                                           '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                print('Invalid --start_time')
                sys.exit(1)
    if options.end_time:
        if options.end_time == '0':
            pass
        elif options.end_time.startswith('-'):
            try:
                float(options.end_time)
            except ValueError:
                print('Invalid --end_time')
                sys.exit(1)
        else:
            try:
                datetime.datetime.strptime(options.end_time,
                                           '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                print('Invalid --end_time')
                sys.exit(1)
    verbose = options.verbose
    measurement_count = None
    if options.count:
        measurement_count = int(options.count)

    try:
        print_verbose('Setup...')
        conn = JahmonConnection(auth_url=os_auth_url,
                                jahmon_url=options.jahmon_url,
                                jahmon_token=options.jahmon_token,
                                username=os_username,
                                password=os_password,
                                project_id=os_project_id,
                                project_name=os_project_name,
                                region_name=os_region_name,
                                user_domain_name=os_user_domain_name,
                                user_domain_id=os_user_domain_id,
                                project_domain_name=os_project_domain_name,
                                project_domain_id=os_project_domain_id,
                                user_id=os_user_id)
    except JahmonClientException as err:
        print('...failed; Got %s code; reason: %s' % (err.http_status, err))
        sys.exit(1)

    try:
        print_verbose('Authenticating...')
        conn.get_versions()
    except JahmonClientException as err:
        print '...failed; Got %s code; reason: %s' % (err.http_status, err)
        sys.exit(1)

    if os_auth_url:
        print_verbose('...Monasca endpoint: %s' % conn.url)
        print_verbose('...token: %s' % conn.token)
        print_verbose('...after %s attempts' % conn.attempts)
    else:
        print_verbose('...using %s with token %s' % (conn.url, conn.token))

    if args[0].lower().startswith('post_metric'):
        try:
            print_verbose('POST /metric...')
            conn.post_metric(options.metric_name,
                             options.value,
                             dimensions=dimensions,
                             value_meta=value_meta,
                             timestamp=None,
                             for_project=None)
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)
        print_verbose('...status: %s' % conn.status_code)
        print_verbose('...after %s attempts' % conn.attempts)

    elif args[0].lower().startswith('versions'):
        try:
            print_verbose('GET /...')
            reply = conn.get_versions()
            print json.dumps(reply, indent=2, separators=(',', ': '))
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)
        print_verbose('...status: %s' % conn.status_code)
        print_verbose('...after %s attempts' % conn.attempts)

    elif args[0].lower().startswith('metrics_api'):
        try:
            print_verbose('GET /metrics...')
            reply = conn.get_metrics_api(options.metric_name,
                                         dimensions=dimensions,
                                         for_project=None)
            print(json.dumps(reply, indent=2, separators=(',', ': ')))
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)
        print_verbose('...status: %s' % conn.status_code)
        print_verbose('...after %s attempts' % conn.attempts)

    elif args[0].lower().startswith('metrics'):
        try:
            metrics = conn.get_metrics(options.metric_name,
                                       dimensions=dimensions,
                                       for_project=None)
            for metric in metrics:
                print('%s %s' % (metric.get('name'),
                                 json.dumps(metric.get('dimensions'))))
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)

    elif args[0].lower().startswith('meas'):
        try:
            print_verbose('GET /metrics/measurements...')
            merge_metrics = options.merge_metrics
            reply = conn.get_measurements_api(options.metric_name,
                                              options.start_time,
                                              options.end_time,
                                              dimensions=dimensions,
                                              for_project=None,
                                              merge_metrics=merge_metrics,
                                              offset=options.offset)
            print(json.dumps(reply, indent=2, separators=(',', ': ')))
        except Exception as err:
            print('...failed; reason: %s' % err)
        print_verbose('...status: %s' % conn.status_code)
        print_verbose('...after %s attempts' % conn.attempts)

    elif args[0].lower().startswith('find'):
        try:
            metrics = conn.get_metrics(options.metric_name,
                                       dimensions=dimensions)
            for metric in metrics:
                items = conn.get_measurements(metric,
                                              options.start_time,
                                              options.end_time,
                                              for_project=None,
                                              count=measurement_count)
                for item in items:
                    print_result(item, options.fmt)
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)

    elif args[0].lower().startswith('merge'):
        try:
            metric = {'name': options.metric_name,
                      'dimensions': dimensions}
            items = conn.get_measurements(metric,
                                          options.start_time,
                                          options.end_time,
                                          for_project=None,
                                          merge_metrics=True,
                                          count=measurement_count)
            for item in items:
                print_result(item, options.fmt)
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)

    elif args[0].lower().startswith('aggregate'):
        try:
            min = None
            max = 0.0
            total = 0.0
            count = 0
            metrics = conn.get_metrics(options.metric_name,
                                       dimensions=dimensions)
            for metric in metrics:
                items = conn.get_measurements(metric,
                                              options.start_time,
                                              options.end_time,
                                              for_project=None,
                                              merge_metrics=True,
                                              count=measurement_count)
                for item in items:
                    count += 1
                    value = item.get('value')
                    total += value
                    if min is None:
                        min = value
                    if value < min:
                        min = value
                    if value > max:
                        max = value
            avg = float(total)/count
            print('avg: %s min-max: %s-%s  total: %s   count: %s' % (avg, min,
                  max, total, count))
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)

    elif args[0].lower().startswith('tail'):
        try:
            metrics = []
            items = conn.get_metrics(options.metric_name,
                                     dimensions=dimensions)
            for item in items:
                metrics.append(item)

            start_time = conn.utctime(-4)  # First time through, show more
            while True:
                # A measurement may be posted well after it's timestamp
                # Hence the tailed results are always two minutes behind.
                end_time = conn.utctime(-2)
                for metric in metrics:
                    items = conn.get_measurements(metric, start_time, end_time,
                                                  for_project=None)
                    for item in items:
                        print_result(item, options.fmt)
                sleep(60)
                start_time = conn.utctime(-3)
        except Exception as err:
            print('...failed; reason: %s' % err)
            sys.exit(1)

    else:
        print('Invalid command. Try --help')
        sys.exit(1)


if __name__ == "__main__":
    main()

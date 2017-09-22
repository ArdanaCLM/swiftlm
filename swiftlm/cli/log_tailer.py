#!/usr/bin/python

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

import ConfigParser
from ConfigParser import NoSectionError, NoOptionError
import logging
from optparse import OptionParser
import json
import time

from swiftlm.utils.log_tailer import LogTailer, parse_proxy_log_message, \
    AccessStatsRecorder
from swiftlm.utils.utility import dump_swiftlm_uptime_data, get_logger, \
    sleep_interval


usage = """
Program to tail a swift log file, extract messages coming from the
proxy-logging middleware and derive stats such as number of operations, bytes
put and bytes get. The stats are worked out as a total and for each
project.

At the end of each cycle, it writes the stats as metrics to a metrics
json file. The swiftlm plugin will send these to Monasca.

Usage:

    swiftlm-log-tail --config <filename>

Options:
    --config <filename>
    Defaults to /etc/swiftlm/swiftlm-scan.conf

Example configuration file:

    [log-tailer]
    tailed_log_file=/var/log/swift/swift.log
    metric_file=/var/cache/swiftlm/access_log_metrics.json
    interval=60
    monasca_agent_interval=30
    reseller_prefixes=AUTH_,SERVICE_

    [logging]
    log_level = info
    log_facility = LOG_LOCAL0
    log_format = '%(name)s: %(message)s'

where:

    tailed_log_file
        Name of file to tail.
        Defaults to /var/log/swift/swift.log

    metric_file
        Name of file to write metrics. Defaults to
        /var/cache/swiftlm/access_log_metrics.json

    interval
        Cycle time (time between reads of log file). Defaults to 60 seconds

    monasca_agent_interval
        How often Monasca Agent runs. Defaults to 30 seconds (it may run
        more often than this without harm).

    reseller_prefixes
        Project prefix to make a Swift account name. Defaults to AUTH_
"""


def make_measurements(metric_name_prefix, stats, timestamp,
                      dimensions={}):
    """
    Convert stats structure into metric format

    :param metric_name_prefix: first part of metric name
    :param stats: the stats
    :param timestamp: timestamp
    :param dimensions: dimensions (optional)
    :return:
    """
    metrics = []
    for stat_item, metric_name in [('ops', 'ops'),
                                   ('bytes_put', 'put.bytes'),
                                   ('bytes_get', 'get.bytes')]:
        dimensions.update({'service': 'object-storage'})
        metrics.append({'metric': metric_name_prefix + metric_name,
                        'value': stats.get(stat_item),
                        'timestamp': timestamp,
                        'dimensions': dimensions})
    return metrics


def purge_old_measurements(metrics, interval, monasca_agent_interval):
    """
    Purge old measurements

    Monasca agent may run less than our interval. If we only
    kept the latest measurements in the metric json file, the agent
    might miss them. So instead of overwriting, we append metrics. This
    function purges metrics when we're convinced that the agent
    has read them.

    Since we're keeping measurements from several cycles in the metrix json
    file, the reader must discard duplicates (the Swiftlm Monasca plugin
    discards duplicates).

    :param metrics: List of metrics
    :param interval: How often we generate new measurements
    :param monasca_agent_interval: How long to retain old measurements
    :return: metrics is updated in place
    """
    retain_time = interval + monasca_agent_interval
    for metric in list(metrics):  # Note: iterate over a copy
        if (metric.get('timestamp') + retain_time) < time.time():
            metrics.remove(metric)


def run_forever(log_file_name, interval, metric_file, reseller_prefixes,
                logger, monasca_agent_interval):
    """
    The main cycle loop

    :param log_file_name: name of file we are tailing
    :param interval: how often we report metrics
    :param metric_file: file to dump metrics into
    :param reseller_prefixes: list of account prefixes to process
    :param logger: a logger
    """

    logger.info('Starting. Reading from: %s' % log_file_name)
    # Get into sync with wake up interval
    WAKE_UP_TIME = 60
    time.sleep(sleep_interval(interval, time.time(), WAKE_UP_TIME))

    while True:
        try:
            log_tail = LogTailer(log_file_name)
            break
        except IOError as err:
            if err.errno == 2:
                # Log file does not yet exist
                time.sleep(sleep_interval(interval, time.time(), WAKE_UP_TIME))
            else:
                raise err

    cycle = 10
    metric_data = []
    while True:
        try:
            # Sleep until next wake up
            time.sleep(sleep_interval(interval, time.time(), WAKE_UP_TIME))

            # Timestamp means the metrics are measurements of the data
            # gathered in the *last* time interval (i.e., timestamp is the
            # end of the cycle)
            timestamp = time.time()

            # Read lines written to the log since we last read the file
            # and process lines to extract stats.
            stats = AccessStatsRecorder()
            for line in log_tail.lines():
                result = parse_proxy_log_message(
                    line, reseller_prefixes=reseller_prefixes)
                if isinstance(result, dict):
                    stats.record_op(result.get('verb'),
                                    result.get('http_status'),
                                    result.get('bytes_transferred'),
                                    project=result.get('project'),
                                    container=result.get('container'),
                                    obj=result.get('obj'))

            # Convert stats into metric measurements
            total_metrics = make_measurements('swiftlm.access.host.operation.',
                                              stats.get_stats(), timestamp)
            for measurement in total_metrics:
                metric_data.append(measurement)

            # Occasionally, log the totals
            cycle += 1
            if cycle >= 10:
                for metric in total_metrics:
                    logger.info('Metric: %s' % json.dumps(metric))
                cycle = 0

            for project in stats.get_projects():
                project_metrics = make_measurements(
                    'swiftlm.access.host.operation.project.',
                    project.get_stats(), timestamp,
                    dimensions={'tenant_id': project.get_stats().get('name')})
                for measurement in project_metrics:
                    metric_data.append(measurement)

            # Record that we processed data without error
            metric_data.append({'metric':
                                'swiftlm.access.host.operation.status',
                                'value': 0, 'timestamp': timestamp,
                                'dimensions': {'service': 'object-storage'},
                                'value_meta': {'msg': 'OK'}})
        except Exception as err:  # noqa
            metric_data = []
            metric_data.append({'metric':
                                'swiftlm.access.host.operation.status',
                                'value': 2, 'timestamp': time.time(),
                                'dimensions': {'service': 'object-storage'},
                                'value_meta': {'msg': err}})

        purge_old_measurements(metric_data, interval, monasca_agent_interval)
        dump_swiftlm_uptime_data(metric_data, metric_file, logger,
                                 lock_timeout=2)


def main():
    parser = OptionParser(usage=usage)
    parser.add_option('--config', dest='config_file',
                      default='/etc/swiftlm/swiftlm-scan.conf')
    (options, args) = parser.parse_args()
    config = ConfigParser.RawConfigParser()
    prefix_list = 'AUTH_'
    interval = 60
    monasca_agent_interval = 30
    metric_file = '/var/cache/swiftlm/access_log_metrics.json'
    log_file_name = '/var/log/swift/swift.log'
    if config.read(options.config_file):
        try:
            interval = int(config.get('log-tailer', 'interval'))
        except (NoSectionError, NoOptionError):
            pass
        try:
            metric_file = config.get('log-tailer', 'metric_file')
        except (NoSectionError, NoOptionError):
            pass
        try:
            log_file_name = config.get('log-tailer', 'tailed_log_file')
        except (NoSectionError, NoOptionError):
            pass
        try:
            monasca_agent_interval = int(config.get('log-tailer',
                                                    'monasca_agent_interval'))
        except (NoSectionError, NoOptionError):
            pass
        try:
            prefix_list = config.get('log-tailer', 'reseller_prefixes')
        except (NoSectionError, NoOptionError):
            pass
        try:
            logger = get_logger(dict(config.items('logging')),
                                name='log-tailer')
        except (NoSectionError, NoOptionError):
            logging.basicConfig(level=logging.DEBUG)
            logger = logging
    else:
        logging.basicConfig(level=logging.DEBUG)
        logger = logging
    reseller_prefixes = prefix_list.strip().split(',')

    run_forever(log_file_name, interval, metric_file, reseller_prefixes,
                logger, monasca_agent_interval)

if __name__ == '__main__':
    main()

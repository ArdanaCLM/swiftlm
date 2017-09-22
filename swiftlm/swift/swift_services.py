
# (c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP
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


from swiftlm.utils.utility import server_type, get_all_proc_and_cmdlines,\
                                  get_network_interface_conf,\
                                  get_rsync_target_conf
from swiftlm.utils.metricdata import MetricData, get_base_dimensions
from swiftlm.utils.values import Severity

BASE_RESULT = MetricData(
    name=__name__,
    messages={
        'fail': '{component} is not running',
        'ok': '{component} is running',
        'unknown': 'no swift services running',
    }
)

SERVICES = [
    "account-auditor",
    "account-reaper",
    "account-replicator",
    "account-server",
    "container-replicator",
    "container-server",
    "container-updater",
    "container-auditor",
    "container-reconciler",
    "container-sync",
    "object-replicator",
    "object-server",
    "object-updater",
    "object-auditor",
    "object-reconstructor",
    "proxy-server"
]


def services_to_check():
    # Filter SERVICES down to what should be running on the node.
    # server_type returns a dict of {'object': bool, etc}
    prefix_server_type = tuple(k for k, v in server_type().items() if v)
    services = [s for s in SERVICES if s.startswith(prefix_server_type)]

    return services


def check_swift_processes():
    results = []

    services = services_to_check()

    if not services:
        c = BASE_RESULT.child()
        c.value = Severity.unknown
        return c

    for service in services:
        c = BASE_RESULT.child(dimensions={'component': service})

        if not is_service_running(service):
            c.value = Severity.fail
        else:
            c.value = Severity.ok

        results.append(c)

    return results


def is_service_running(service):
    for _, cmdline in get_all_proc_and_cmdlines():
        if len(cmdline) >= 3:
            if (cmdline[1].endswith("swift-" + service) and
                    cmdline[2].endswith(".conf")):
                return True
    # Reach here if no matching process not found in /proc/cmdline
    return False


def get_rsync_bind_ip():
    rsync_running = False

    data = get_network_interface_conf()
    rsync_bind_ip_conf = data["rsync_bind_ip"]
    port = get_rsync_target_conf()
    rsync_bind_port_conf = port["rsync_bind_port"]

    for process, cmdline in get_all_proc_and_cmdlines():
        if len(cmdline) >= 2:
            if cmdline[0].endswith('/rsync') and cmdline[1] == '--daemon':
                rsync_running = True
                rsync_laddr = process.connections()
                rsync_laddr_ip, rsync_laddr_port = rsync_laddr[0].laddr
                continue

    if not rsync_running:
        return False, False

    ip_port_match = False
    if (rsync_bind_ip_conf == rsync_laddr_ip and
            rsync_bind_port_conf == str(rsync_laddr_port)):
        ip_port_match = True

    return rsync_running, ip_port_match


def check_rsync():
    metrics = []
    rsync_running, ip_port_match = get_rsync_bind_ip()
    if not rsync_running:
        dimensions = get_base_dimensions()
        dimensions["component"] = "rsync"
        metrics.append(MetricData.single('swiftlm.swift.swift_services',
                                         Severity.fail,
                                         message='rsync is not running',
                                         dimensions=dimensions))
        return metrics
    else:
        dimensions = get_base_dimensions()
        dimensions["component"] = "rsync"
        metrics.append(MetricData.single('swiftlm.swift.swift_services',
                                         Severity.ok,
                                         message='rsync is running',
                                         dimensions=dimensions))
    if not ip_port_match:
        dimensions = get_base_dimensions()
        dimensions["component"] = "rsync"
        metrics.append(MetricData.single(
            'swiftlm.swift.swift_services.check_ip_port', Severity.fail,
            message='rsync is not listening on the correct ip or port',
            dimensions=dimensions))
    else:
        dimensions = get_base_dimensions()
        dimensions["component"] = "rsync"
        metrics.append(MetricData.single(
            'swiftlm.swift.swift_services.check_ip_port', Severity.ok,
            message='OK', dimensions=dimensions))
    return metrics


def main():
    """Check that the relevant services are running."""
    metrics = []

    metrics.extend(check_swift_processes())
    metrics.extend(check_rsync())

    return metrics

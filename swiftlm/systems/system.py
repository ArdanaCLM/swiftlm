
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


import re

from swiftlm.utils.metricdata import MetricData, CheckFailure
from swiftlm.utils.values import Severity
from swiftlm.utils.utility import run_cmd

BASE_RESULT = MetricData(
    name='load.host',
    messages={}
)


def _get_proc_file(path):
    return open(path, mode='r').read()


def get_load_average():
    r = BASE_RESULT.child(name='val.five')
    load_avg_data = _get_proc_file('/proc/loadavg')
    r.value = float(load_avg_data.split()[1])
    return [r]


def main():
    """ Get system data (such as load average) """
    results = []
    results.extend(get_load_average())
    return results

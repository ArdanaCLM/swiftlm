
.. code::

    (c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP
    (c) Copyright 2017 SUSE LLC

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


Swiftlm Documentation
=====================


Introduction
------------

The swiftlm project contains a number of features designed to help manage
and monitor Swift.

The main components in swiftlm as as follows:

* swiftlm-scan

  The swiftlm-scan utility comprises a number of checks and metric-measurement
  functions. When run, it scans the system and generates a list of metrics.
  The metrics are encoded in JSON. The format and layout of the metrics
  is designed to be compatible with Monasca. Howerver, since the data
  is encoded as JSON, it is possible to integrate the results with other
  monitoring systems.

* swiftlm-aggregate

  This uses the recon mechanism to gather system-wide data and create
  metrics for consumption by the Monasca-agent plugin.

* swiftlm-uptime-monitor

  The swiftlm-uptime-monitor program monitors the VIP of a Swift system and
  determines if the system is responding. It measures the uptime and
  latency of the Swift service.

* swiftlm-access-log-tailer

  The swiftlm-access-log-tailer scans the swift.log looking for records from
  the swift-proxy-server that relate to API requests made by clients. It
  counts these requests to work out the operation rate and number of object
  bytes read and written. It reports these as totals and by project id.

  Since this data relates to a given host, the metrics only make sense
  when aggregated across all Swift project server hosts.

* Monasca Agent for swiftlm

  This is a Monasca-Agent plug in. It's purpose is to report metrics generated
  by swiftlm-scan and swiftlm_uptime_mon to Monasca.

* swiftlm-ring-supervisor

  This utility is used to build and manage rings. The swiftlm-ring-supervisor
  is tightly integrated with the Ardana OpenStack Lifecycle Manager (Ardana)
  data model. The concept is that you provide a declarative description of
  your cloud (the input model) and the swiftlm-ring-supervisor will
  figure out the appropriate ring changes so that the Swift system uses
  the cloud resources as specified in the input model.


Metric Information
------------------

The metrics produced by swiftlm are described in:

* :ref:`swiftlm-scan-metrics`

* :ref:`swiftlm-uptime-mon-metrics`

* :ref:`swiftlm-aggregate-metrics`

* :ref:`swiftlm-access-log-tailer-metrics`

Developer Information
---------------------

* `Standalone Script Setup <standalone_scripts.html>`_

* `Monasca Plugin <monasca_plugin.html>`_

* `Developing swiftlm-scan Checks <test_runner.html>`_

Building these documents
------------------------

You can build HTML versions of the docs with::

    tox -e docs

Point your browser at this URL, where ``<path>`` is where the swiftlm
repository is checked out::

    file:///home/<path>/swiftlm/doc/build/html/index.html

To test correctness of an rst file, run rst2html.py as follows::

    rst2html < blah.rst > ../build/blah.rst

The rst2html.py utility is in docutils. Install as follows::

    pip install docutils

Table of Contents
------------------

.. toctree::
    :maxdepth: 2

    monasca_plugin
    swiftlm_scan_metrics
    swiftlm_uptime_mon_metrics
    aggregate_scout
    test_runner
    standalone_scripts





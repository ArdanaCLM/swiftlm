
.. code::

    (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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


Access Log Metrics (swiftlm-access-log-tailer)
==============================================

Introduction
------------

The access log (aka the swift proxy log) is scanned by the
swiftlm-access-log-tailer program. This program identifies and
counts operations made against accounts (aka projects). The purpose of
the metrics is to calculate the rate at which operations are being performed
and to calculate the number of bytes written and read.

The data is reported every minute i.e., the accesses during the proceeding
minutes are counted and reported on at the end of that minute.
In general, the data is reported as:

- Totals for all projects accessed during the period

- Per-project accesses. These metrics include a project dimension

The metrics are written as a json file. This file can then be consumed
by the Monasca Swiftlm Plugin. Since the metrics are reported by each proxy
server and since requests are randomly distributed among proxy servers, the
values for any given host do not have much meaning. Instead, these
metrics are mostly designed to be consumed my the Monasa Transform process
that will aggregate values across all proxy servers.

.. _swiftlm-access-log-tailer-metrics:

Metrics Produced by swiftlm-access-log-tailer-metrics
-----------------------------------------------------

The Monasca Agent will add additional dimensions such as:

* hostname
* cluster
* control_plane

These are not listed in the dimensions below.

* swiftlm.access.host.operation.ops

  - The number of API requests made during the last minute to this
    host

  - Dimensions:

    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric is a count of the all the API requests made to Swift
    that were processed by this host during the last minute.

    Requests to /healthcheck and /info are not counted.

    The count includes invalid requests, so the value may be larger
    than an aggregation of swiftlm.access.host.operation.project.ops
    because that only counts operations to an identified project.

* swiftlm.access.host.operation.project.ops

  - The number of API requests made during the last minute to this
    host for a specific project

  - Dimensions:

    * tenant_id: the project id being accessed
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric is a count of the all the API requests made to Swift
    that were processed by this host during the last minute to a given
    project id.

    All requests, whether successful or not, are counted.

    The project id is identified by its position in the request path,
    so the project id might not be a valid project id (i.e., it might
    not exist in Keystone).

* swiftlm.access.host.operation.get.bytes

  - The number of object bytes read by clients through this host

  - Dimensions:

    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric is the number of bytes read from objects in GET requests
    processed by this host during the last minute. Only successful GET requests
    to objects are counted. GET requests to the account
    or container is not included.

* swiftlm.access.host.operation.project.get.bytes

  - The number of object bytes read by clients through this host for
    a specific project

  - Dimensions:

    * tenant_id: project id
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric is the number of bytes read from objects in GET requests
    processed by this host for a given project during the last minute. Only
    successful GET requests to objects are counted. GET requests to the
    account or container is not included.

* swiftlm.access.host.operation.put.bytes

  - The number of object bytes writen by clients through this host

  - Dimensions:

    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric is the number of bytes written to objects in PUT or
    POST requests processed by this host during the last minute. Only
    successful requests to objects are counted. Requests to the account
    or container is not included.

* swiftlm.access.host.operation.project.put.bytes

  - The number of object bytes written by clients through this host for
    a specific project

  - Dimensions:

    * tenant_id: project id
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric is the number of bytes written to objects in PUT or POST requests
    processed by this host for a given project during the last minute. Only
    successful requests to objects are counted. Requests to the
    account or container is not included.

* swiftlm.access.host.operation.status

  - The status of the swiftlm-access-log-tailer program

  - Dimensions:

    * service: object-storage

  - Value Class: Status
  - Value Meta: A message indicating the problem

  - Description

    This metric reports whether the swiftlm-access-log-tailer program
    is running normally.
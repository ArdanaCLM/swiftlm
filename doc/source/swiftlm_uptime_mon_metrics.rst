
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

swiftlm-uptime-monitor
======================

The swiftlm-uptime-monitor program monitors the VIP of a Swift system and
determines if the system is responding. It measures the latency of the
Keystone authentication process and the Swift service in two ways. The
first check is the latency of a single successful keystone authentication
round trip followed by N-iterations of the latency of an object store
put-get-delete processes, then N-iterations of queries to the object
store healthcheck REST API function.

Introduction
------------

The swiftlm-uptime-monitor program emits a number of metrics
corresponding to the data it monitors.

The metric information is organised as follows:

* Metric name

  This is the name of the metric being described. This is the name that
  Monasca receives.

* Value Class

  This is one the following. This is not a Monasca concept. We use it so that
  the table is less verbose.

  - Measurement -- this is used when the value of the metric reports a
    value. For example, the voltage of a 12V battery might be 11.98.

  - Status -- this is used when the value represents a state or status
    something in the system. The following values are used:
    ::

        0. Status is normal or ok
        1. Status is in a warning state
        2. Status is in a failed state
        3. The state is unknown cannot be determined or not applicable at the current time

    Generally, a metric of this value class will also have a value_meta

* Dimensions. This is the dimensions as sent to Monasca

* Value_meta. This is optional. When present, it contains additional data
  in addition to the value of the metric.

* Description. This provides a longer description of the values and
  meaning of the metric.

* Troubleshooting/Resolution. This provides some suggestions for using and
  interpreting the metric values to troubleshoot and resolve problems on
  your system.

.. _swiftlm-uptime-mon-metrics:

Metrics Produced by swiftlm-uptime-monitor
------------------------------------------

I am assuming that, as mentioned in the aggregate_scout.rst doc,
the Monasca Agent will add the "control_plane" dimension so it is not
listed in the dimensions below.

* swiftlm.umon.target.min.latency_sec

  Reports the minimum latency recorded in a sequence of response time checks of a component.

  - Dimensions:

       * component: the API being checked
         * keystone: The Keystone API (used to get an auth token)
         * rest-api: The Swift object-storage API (object put, get, and delete)
         * healthcheck: The /healthcheck REST call of the Swift API
       * hostname: Set to '_'
       * observer_host: The host reporting the metric.
       * service: object-storage
       * url: the base URL of the REST service called

  - Value Class:

       The minimum value of response latency in seconds

  - Description

       This metric reports the minimum response time in seconds of a REST call
       from the observer to the component REST API listening on the reported host

  - Troubleshooting/Resolution.

       The troubleshooting and resolution steps heavily depend on the nature
       of the failure.  The keystone service could be stopped, in which
       case none of these checks will pass. Look through the $HOME/keystone.osrc
       file for the configured OS_AUTH_URL and verify that the keystone port
       is listening.  For Swift Object Store and Swift Object Store Healthcheck,
       make sure that Swift services are active.


* swiftlm.umon.target.max.latency_sec

  Reports the maximum latency recorded in a sequence of response time checks of a component.

  - Dimensions:

       * component: the API being checked
         * keystone: The Keystone API (used to get an auth token)
         * rest-api: The Swift object-storage API (object put, get, and delete)
         * healthcheck: The /healthcheck REST call of the Swift API
       * hostname: Set to '_'
       * observer_host: The host reporting the metric.
       * service: object-storage
       * url: the base URL of the REST service called

  - Value Class:

       The maximum value of response latency in seconds

  - Description

       This metric reports the maximum response time in seconds of a REST call
       from the observer to the component REST API listening on the reported host

  - Troubleshooting/Resolution:

       The troubleshooting and resolution steps heavily depend on the nature
       of the failure.  The keystone service could be stopped, in which
       case none of these checks will pass. Look through the $HOME/keystone.osrc
       file for the configured OS_AUTH_URL and verify that the keystone port
       is listening.  For Swift Object Store and Swift Object Store Healthcheck,
       make sure that Swift services are active.


* swiftlm.umon.target.avg.latency_sec

  This metric reports the average value of the last N-iterations of latency
  measurements which have been recorded for a component.

  - Dimensions:

       * component: the API being checked
         * keystone: The Keystone API (used to get an auth token)
         * rest-api: The Swift object-storage API (object put, get, and delete)
         * healthcheck: The /healthcheck REST call of the Swift API
       * hostname: Set to '_'
       * observer_host: The host reporting the metric.
       * service: object-storage
       * url: the base URL of the REST service called

  - Value Class:

       The average value in seconds for N-iterations of response latency measures

  - Description

       Reports the average value of N-iterations of the latency values recorded
       for a component.

  - Troubleshooting/Resolution:

       The troubleshooting and resolution steps heavily depend on the nature
       of the failure.  The keystone service could be stopped, in which
       case none of these checks will pass. Look through the $HOME/keystone.osrc
       file for the configured OS_AUTH_URL and verify that the keystone port
       is listening.  For Swift Object Store and Swift Object Store Healthcheck,
       make sure that Swift services are active.


* swiftlm.umon.target.check.state

  This metric reports the state of the last completed check of the component.

  - Dimensions:

       * component: the API being checked
         * keystone: The Keystone API (used to get an auth token)
         * rest-api: The Swift object-storage API (object put, get, and delete)
         * healthcheck: The /healthcheck REST call of the Swift API
       * hostname: Set to '_'
       * observer_host: The host reporting the metric.
       * service: object-storage
       * url: the base URL of the REST service called

  - Value Class:

       This is the staus of the metric, reported as one of three states:
       ::

         0. Status is normal or ok
         1. Status is in a warning state
         2. Status is in a failed state
         3. The state is unknown cannot be determined or not applicable at the current time

       This metric does not report a value_meta on an 'ok' state. The failed
       or unknown state reports the http return error.

  - Description

       This metric reports the state of each component after N-iterations of checks.
       If the initial check succeeds, the checks move onto the next component until
       all components are queried, then the checks sleep for 'main_loop_interval'
       seconds.  If a check fails, it is retried every second for 'retries' number
       of times per component.  If the check fails 'retries' times, it is reported as
       a fail instance.

   - Troubleshooting/Resolution:

       The troubleshooting and resolution steps heavily depend on the nature
       of the failure.  The failing component should immediately report a
       failed state with the associated value_meta to give a hint to
       the root cause.  Therefore the resolution efforts for this metric
       will be focused upon the failing latency metric as described above.


* swiftlm.umon.target.val.avail_minute

   Reports whether the Object Store rest-api is responding.

   - Dimensions:

        * component: the API being checked
          * rest-api: The Swift object-storage API (object put, get, and delete)
        * hostname: Set to '_'
        * observer_host: The host reporting the metric.
        * service: object-storage
        * url: the base URL of the REST service called

   - Value Class:

        Either 100 for success, or 0 for fail.

   - Description

        A value of 100 indicates that swift-uptime-monitor was able to get a token
        from Keystone and was able to perform operations against the Swift API
        during the reported minute. A value of zero indicates that either
        Keystone or Swift failed to respond successfully.
        A metric is produced every minute that swift-uptime-monitor is running.

   - Troubleshooting/Resolution:

        This metric is reporting a summarized state of the uptime monitor
        metrics and therefore the troubleshooting and resolution of this
        metric is a by-product of the resolution of the latency and state
        troubleshooting and resolution root cause.


* swiftlm.umon.target.val.avail_day

   Reports the average of the last 24 hours of per-minute availability
   of Object Store rest-api.

   - Dimensions:

        * component: the API being checked
          * rest-api: The Swift object-storage API (object put, get, and delete)
        * hostname: Set to '_'
        * observer_host: The host reporting the metric.
        * service: object-storage
        * url: the base URL of the REST service called

   - Value Class:

        The average availability as reported by the per-minute metric
        throughout the last 24 hours of minutes.

   - Description

        This metric reports the average of all the collected records in the
        swiftlm.umon.target.val.avail_minute metric data.  This is a walking
        average data set of these approximately per-minute states of the
        Swift Object Store. The most basic case is a whole day of successful
        per-minute records, which will average to 100% availability.  If
        there is any downtime throughout the day resulting in gaps of data
        which are two minutes or longer, the per-minute availability data
        will be "back filled" with an assumption of a down state for all
        the per-minute records which did not exist during the non-reported time.
        Because this is a walking average of approximately 24 hours worth
        of data, any outtage will take 24 hours to be purged from the dataset.


   - Troubleshooting/Resolution:

        This metric is reporting a summarized state of the uptime monitor
        metrics and therefore the troubleshooting and resolution of this
        metric is a by-product of the resolution of the latency and state
        troubleshooting and resolution root cause.

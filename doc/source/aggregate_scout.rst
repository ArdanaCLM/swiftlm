
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


Scout and Aggregation Utility (swiftlm-aggregate)
=================================================

Introduction
------------

The swiftlm-aggregate program is run as a regular cron job. It gathers
data using the Swift recon mechanism from all nodes. It then aggregates
the data and generates appropriate metrics for the aggregated data.

The metrics are written as a json file. This file can then be consumed
by the Monasca Swiftlm Plugin.

.. _swiftlm-aggregate-metrics:

Metrics Produced by swiftlm-aggregate
-------------------------------------

The Monasca Agent will add additional dimensions such as:

* cluster
* control_plane

These are not listed in the dimensions below.

* swiftlm.async_pending.cp.total.queue_length

  - Reports the total length of the async pending queue of all object server
    nodes
  - Option: --async
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the total length of all async pending queues
    in the system.

    When a container update fails, the update is placed on the async pending
    queue. An update may fail becuase the container server is too busy or
    because the server is down or failed. Later the system will "replay"
    updates from the queue -- so eventually, the container listings
    will show all objects known to the system.

    If you know that container servers are down, it is normal to see the
    value of async pending increase. Once the server is restored, the
    value should return to zero.

    A non-zero value may also indicate that containers are too large. Look for
    "lock timeout" messages in /var/log/swift/swift.log. If you find such
    messages consider reducing the container size or enable rate limiting.


* swiftlm.diskusage.cp.total.size

  - Is the total raw size of all drives in the system.
  - Option: --diskusage
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    Is the size in bytes of raw size of all drives in the system.

* swiftlm.diskusage.cp.total.avail

  - Is the total available size of all drives in the system.
  - Option: --diskusage
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    Is the size in bytes of available (unused) space of all drives in
    the system. Only drives used by Swift are included.

* swiftlm.diskusage.cp.total.used

  - Is the total used size of all drives in the system.
  - Option: --diskusage
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    Is the size in bytes of used space of all drives in
    the system. Only drives used by Swift are included.

* swiftlm.diskusage.cp.avg.usage

  - Is the average utilization of all drives in the system
  - Option: --diskusage
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    Is the average utilization of all drives in the system. The value
    is a percentage (example: 30.0 means 30% of the total space is
    used).

* swiftlm.diskusage.cp.min.usage

  - Is the lowest utilization of all drives in the system
  - Option: --diskusage
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    Is the lowest utilization of all drives in the system. The value
    is a percentage (example: 10.0 means at least one drive is 10% utilized)

* swiftlm.diskusage.cp.max.usage

  - Is the highest utilization of all drives in the system
  - Option: --diskusage
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    Is the highest utilization of all drives in the system. The value
    is a percentage (example: 80.0 means at least one drive is 80% utilized).
    The value is just as important as swiftlm.diskusage.usage.avg. For example,
    if swiftlm.diskusage.usage.avg is 70% you might think that there is
    plenty of space available. However, if swiftlm.diskusage.usage.max is
    100%, this means that some objects cannot be stored on that drive. Swift
    will store replicas on other drives. However, this will create extra
    overhead.

* swiftlm.md5sum.cp.check.ring_checksums

  - Checks if rings are consistent
  - Option: --md5sum
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Status (value=0 is OK; 2 is Failed)
  - Value Meta: msg

    * Rings are consistent on all hosts

      Ok

    * Checksum or number of rings not the same on all hosts

      The same set of rings is not present on all hosts.

  - Description

    If you are in the middle of deploying new rings, it is normal for this to
    be in the failed state.

    However, if you are not in the middle of a deployment, you need to
    investigate the cause. Use "swift-recon --md5 -v" to identify the
    problem hosts.

* swiftlm.replication.cp.avg.account_duration

  - Is the average time for the account replicator to complete a scan
  - Option: --replication
  - Dimensions:

    * observer_host: name of host doing the aggregation
    * service: object-storage
    * component: account-replicator

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the average across all servers for the account replicator
    to complete a cycle. As the system becomes busy, the time to complete
    a cycle increases. The value is in seconds.

* swiftlm.replication.cp.avg.container_duration

  - Is the average time for the container replicator to complete a scan
  - Option: --replication
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage
    * component: container-replicator

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the average across all servers for the container replicator
    to complete a cycle. As the system becomes busy, the time to complete
    a cycle increases. The value is in seconds.

* swiftlm.replication.cp.avg.object_duration

  - Is the average time for the object replicator to complete a scan
  - Option: --replication
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage
    * component: object-replicator

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the average across all servers for the object replicator
    to complete a cycle. As the system becomes busy, the time to complete
    a cycle increases. The value is in seconds.

* swiftlm.replication.cp.max.account_last

  - Is the age of the oldest account replicator that completed a scan
  - Option: --replication
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage
    * component: account-replicator

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the number of seconds since the account replicator last completed
    a scan on the host that has the oldest completion time. Normally the
    replicators runs periodically and hence this value will decrease
    whenever a replicator completes. However, if a replicator is not
    completing a cycle, this value increases (by one second for each second
    that the replicator is not completing). If the value remains high and
    increasing for a long period of time, it indicates that one of the
    hosts is not completing the replication cycle.

* swiftlm.replication.cp.container_last

  - Is the age of the oldest container replicator that completed a scan
  - Option: --replication
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage
    * component: container-replicator

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the number of seconds since the container replicator last completed
    a scan on the host that has the oldest completion time. Normally the
    replicators runs periodically and hence this value will decrease
    whenever a replicator completes. However, if a replicator is not
    completing a cycle, this value increases (by one second for each second
    that the replicator is not completing). If the value remains high and
    increasing for a long period of time, it indicates that one of the
    hosts is not completing the replication cycle.

* swiftlm.replication.cp.object_last

  - Is the age of the oldest object replicator that completed a scan
  - Option: --replication
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the number of seconds since the object replicator last completed
    a scan on the host that has the oldest completion time. Normally the
    replicators runs periodically and hence this value will decrease
    whenever a replicator completes. However, if a replicator is not
    completing a cycle, this value increases (by one second for each second
    that the replicator is not completing). If the value remains high and
    increasing for a long period of time, it indicates that one of the
    hosts is not completing the replication cycle.

* swiftlm.load.cp.avg.five

  - Is the average five minute load average of all hosts in the system
  - Option: --load
  - Dimensions:

    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the averaged value of the five minutes system load average of all
    nodes in the Swift system.

* swiftlm.load.cp.max.five

  - Is the maximum five minute load average of all hosts in the system
  - Option: --load
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the five minute load average of the busiest host in the
    Swift system.

* swiftlm.load.cp.min.five

  - Is the minimum five minute load average of all hosts in the system
  - Option: --load
  - Dimensions:

    * hostname: set to "_"
    * observer_host: name of host doing the aggregation
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This is the five minute load average of the least loaded host in the
    Swift system.
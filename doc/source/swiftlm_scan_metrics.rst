
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

swiftlm-scan
============

Introduction
------------

The swiftlm-scan program is comprised a number of "checks". Each check
produces one or more metrics. This document describes the metrics.

The following information is organised as follows:

* Metric name

  This is the name of the metric being described. This is the name that
  Monasca receives.

* Check name

  This is the name of the check producing the metric.

* Value Class

  This is one the following. This is not a Monasca concept. We use it so that
  the table is less verbose.

  - Measurement -- this is used when the value of the metric reports a
    value. For example, the voltage of a 12V battery might be 11.98.

  - Status -- this is used when the value represents a state or status
    something in the system. The following values are used:

    0. Status is normal or ok
    1. Status is in a warning state
    2. Status is in a failed state
    3. The state is unknown (cannot be determined or not applicable at the
       current time

    Generally, a metric of this value class will also have a value_meta

* Dimensions. This is the dimensions as sent to Monasca Agent. Monasca
  agent adds other dimensions such as cloud and control plane. For
  most metrics, it also sets the hostname dimension (for some metrics,
  the checks set the hostname to '_').

* Value_meta. This is optional. When present, it contains additional data
  in addition to the value of the metric.

* Description. This provides a longer description of the values and
  meaning of the metric.

* Troubleshooting/Resolution. This provides some suggestions for using and
  interpreting the metric values to troubleshoot and resolve problems on
  your system.

.. _swiftlm-scan-metrics:

Metrics Produced By swiftlm-scan
--------------------------------

* swiftlm.diskusage.host.val.usage

  - Is the used % of a mounted filesystem
  - Check: --check-mounts
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * mount: the mountpoint of the filesystem

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the percent usage of a Swift filesystem. The
    value is a floating point number in range 0.0 to 100.0

* swiftlm.diskusage.host.max.usage

  - Is highest used % of mounted filesystems on a host
  - Check: --check-mounts
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the percent usage of a Swift filesystem that is
    most used (full) on a host. The value is the max of the
    percentage used of all Swift filesystems.

* swiftlm.diskusage.host.min.usage

  - Is lowest used % of mounted filesystems on a host
  - Check: --check-mounts
  - Dimensions:

    * hostname: name of host being reported
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the percent usage of a Swift filesystem that is
    least used (has free space) on a host. The value is the min of the
    percentage used of all Swift filesystems.

* swiftlm.diskusage.host.avg.usage

  - Is average used % of mounted filesystems on a host
  - Check: --check-mounts
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the average percent usage of all Swift filesystems
    on a host.

* swiftlm.diskusage.host.val.used

  - Is the number of bytes used in a mounted filesystem
  - Check: --check-mounts
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * mount: the mountpoint of the filesystem

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the the number of used bytes in a Swift filesystem. The
    value is an integer (units: Bytes)

* swiftlm.diskusage.host.val.size

  - Is the size in bytes of a mounted filesystem
  - Check: --check-mounts
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * mount: the mountpoint of the filesystem

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the the size in bytes of a Swift filesystem. The
    value is an integer (units: Bytes)

* swiftlm.diskusage.host.val.avail

  - Is the number of bytes available (free) in a mounted filesystem
  - Check: --check-mounts
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * mount: the mountpoint of the filesystem

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the the number of bytes available (free) in a
    Swift filesystem. The value is an integer (units: Bytes)


* swiftlm.systems.check_mounts

  - Reports the status of mounted Swift filesystems
  - Check: --check-mounts
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * mount: the mountpoint of the filesystem

  - Value Class: Status
  - Value Meta:

    * `{device} mounted at {mount} ok`

      Normal, ok, state, for example::

          /dev/sdc1 mounted at /srv/node/disk0 ok

    * `{device} not mounted at {mount}`

    * `{device} mounted at {mount} has permissions {permissions} not 755`

    * `{device} mounted at {mount} is not owned by swift, has user: {user}, group: {group}`

    * `{device} mounted at {mount} has invalid label {label}`

    * `{device} mounted at {mount} is not XFS`

    * `{device} mounted at {mount} is corrupt`

  - Description

    This metric reports the mount state of each drive that should be mounted
    on this node.

    You can attempt to remount by logging into the node and running the
    following command::

        sudo swiftlm-drive-provision --mount


* swiftlm.systems.connectivity.memcache_check

  - Reports if a proxy server can connect to memcached on other servers
  - Check: --connectivity
  - Dimensions:

      * observer_host: the host reporting the metric.
      * url: The network-name/port of the remote memcached
      * service: object-storage
      * hostname: set to '_'

  - Value Class: Status
  - Value Meta: See swiftlm.systems.connectivity.connect_check

  - Description

    This metric reports if memcached on the host as specified by the
    url dimension is accepting connections from the host running the
    check (observer_host). The following value_meta.msg are used:


* swiftlm.systems.connectivity.connect_check

  - Reports if a Swift server can connect to a VIP used by the Swift service
  - Check: --connectivity
  - Dimensions:

    * observer_host: the host that is able/unable to connect to the VIP
    * url: the URL of the endpoint being checked
    * service: object-storage
    * hostname: set to '_'

  - Value Class: Status
  - Value Meta:

    The following value_meta.msg are used:

    * `<vip>:<target_port> ok`

      We successfully connected to <vip> on port <target_port>

    * `<vip>:<target_port> [Errno -2] Name or service not known`

      This should not normally happen since endpoints are usually
      resolved in /etc/hosts.

    * `<vip>:<target_port> [Errno -2] timed out`

      Timed out connecting to the VIP. The service may be unresponsive or
      there may be a network connectivity problem.

    * `<vip>:<target_port> [Errno 111] Connection refused`

      Usually indicates that the service (or haproxy or load balancer)
      is not running.

    * `<vip>:<target_port> <message>`

      As per <message>

    * `<vip>:<target_port> check thread did not complete`

      This indicates that the thread connecting to the endpoint did not
      exit in time. There may by a problem with one of the other threads
      -- not necessarily a problem with this endpoint.

  - Description

    This metric reports if a server can connect to a VIPs. Currently
    the following VIPs are checked:

    * The Keystone VIP used to validate tokens (normally port 5000)

    The check simply connects to the <vip>:<target_port>. It does
    not attempt to send data.

  - Troubleshooting/Resolution

    If the Keystone service stops working, all Swift proxy servers will report
    a connection failure. Restoring the Keystone service will resume normal
    operations.

    If a single Swift proxy server is reporting a problem you should
    investigate the connectivity of that server. Since this server can no longer
    validate tokens, your users will get (apparently random) 401 responses.
    Consider stopping swift-proxy-server on that node until you determine why
    it cannot connect to the Keystone service.


* swiftlm.systems.connectivity.rsync_check

  - Reports if a proxy server can connect to rsyncd on other servers
  - Check: --connectivity
  - Dimensions:

      * observer_host: the host reporting the metric.
      * url: the network-name/port of the remote rsyncd
      * service: object-storage
      * hostname: set to '_'

  - Value Class: Status
  - Value Meta: See swiftlm.systems.connectivity.connect_check

  - Description

    This metric reports if rsyncd on the host as specified by the
    url dimension is accepting connections from the host running the
    check (observer_host).

* swiftlm.systems.ntp NOT IMPLEMENTED

  - Reports if NTP is running on the server.
  - Check: --ntp
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * error: Text of any error messages that occur

  - Description

    This metrics reports if NTP is running on the host. The host uses
    `systemctl status` to determine this.

  - Value Class: Status
  - Value Meta: The following value_meta.msg are used:

    * `OK`

      NTP is running.

    * `ntpd not running: <error>`

      NTP was not running. Error is the text returned by systemctl which may
      help diagnose the issue.

  - Troubleshooting/Resolution

    When NTP is not running XXX


* swiftlm.systems.ntp.stratum  NOT IMPLEMENTED

  - Reports the statum level of NTP
  - Check: --ntp
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Description

    This metric's value will be the stratum level of the current server.
    This is determined using the output of `ntpq -pcrv`.


  - Troubleshooting/Resolution

    When the stratum level increases this indicates that time is being
    recieved from less accurate sources.
    Ensure that the configured master NTP servers are up and that no other
    servers have been added to the time reference list. All servers should be
    within +/-1 stratum level of each other at most.


* swiftlm.systems.ntp.offset  NOT IMPLEMENTED

  - Reports the offset from the system clock and the reported NTP time.
  - Check: --ntp
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Description

    This metric's value will be the offset of the system clock and the NTP
    time.
    This is determined using the output of `ntpq -pcrv`.


  - Troubleshooting/Resolution

    A high offset means that the server isnt adjusting its time correctly or
    that its hardware clock is malfunctioning. If the clock is battery backed
    it could be at a low power level.


* swiftlm.swift.file_ownership.config

  - Reports if Swift configuration files have the appropriate owner
  - Check: --file-ownership
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Value Class: Status
  - Value Meta:

    If multiple errors are found, only the first error is shown in the
    value meta as follows:

    * `OK` - no errors
    * `Path: <path> is not owned by swift`
    * `Path: {path} should not be empty`
    * `Path: {path} is missing`

  - Description

    This metric reports if a directory or file has the appropriate owner
    and other attributes.

  - Troubleshooting/Resolution

    Improper ownership of configuration files may be due to manual editing
    or copy of files. Returning the configuration process may resolve the
    problem. If not, check that the file is a configuration file that is
    actually used by Swift. If not, consider deleting or moving it.

* swiftlm.swift.file_ownership.data

  - Reports if Swift mountpoint (/srv/node/disk<number>) have the appropriate owner
  - Check: --file-ownership
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Value Class: Status
  - Value Meta:

    If multiple errors are found, only the first error is shown in the
    value meta as follows:

    * `OK` - no errors
    * `Path: <path> is not owned by swift`
    * `Path: {path} is missing`

  - Description

    Improper ownership of top-level directories on mounted filesystems may
    be due to insertion of a disk drive that belongs to a different system.
    The Swift processes will be unable to write accounts, containers or objects
    to the filesystems. You should stop all Swift processes and perform
    a rename of all files on the filesystem to correct the problem.

    There is a special case: the directory /srv/node/disk<number> is owned by
    the root user. This happens when a filesystem fails to mount -- and
    so we see the ownership of the mount point -- not the mounted filesystem
    root directory.


* swiftlm.swift.replication.object.last_replication, swiftlm.swift.replication.container.last_replication, swiftlm.swift.replication.account.last_replication

  - Reports how long it has been since the replicator last finished a replication
    run. The replicator in question is indicated in the metric name.
  - Check: --replication
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * component: account-replicator or container-replicator or object-replicator

  - Value Class: Measurement
  - Value Meta:

    * None

  - Description

    This reports how long (in seconds) since the replicator process last
    finished a replication run. If the replicator is stuck, the time
    will keep increasing forever. The time a replicator normally takes
    depends on disk sizes and how much data needs to be replicated. However,
    a value over 24 hours is generally bad.

  - Troubleshooting/Resolution

    The replicator might be stuck (XFS filesystem hang or other issue).
    Restart the process in question. For example, to restart the object-replicator::

        sudo systemctl restart swift-object-replicator


* swiftlm.swift.drive_audit
  - Reports the status from the swift-drive-audit program
  - Check: --drive-audit
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * mount_point: the mountpoint of the filesystem

  - Value Class: Status
  - Value Meta:

    * `No errors found on device mounted at: /srv/node/disk0`

      No errors were found

    * `Errors found on device mounted at: /srv/node/disk0`

      Errors were found in the kernel log


  - Description

    If an unrecoverable read error (URE) occurs on a filesystem, the error is
    logged in the kernel log. The swift-drive-audit program scans the kernel log
    looking for patterns indicating possible UREs.

    To get more information, log onto the node in question and run::

        sudo swift-drive-audit  /etc/swift/drive-audit.conf

    UREs are common on large disk drives. They do not necessarily indicate that
    the drive is failed. You can use the xfs_repair command to attempt to repair
    the filesystem. Failing this, you may need to wipe the filesystem.

    If UREs occur very often on a specific drive, this may indicate that
    the drive is about to fail and should be replaced.

* swiftlm.swift.swift_services

  - Reports if a Swift process (daemon/server) is running or not
  - Check: --swift-services
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * component: the process (daemon/server) being reported

  - Value Class: Status
  - Value Meta:

    * `<name> is running`

      The named process is running.

    * `<name> is not running`

       The named process has stopped.

  - Description

    This metric reports of the process as named in the component dimension
    and the msg value_meta is running or not.

    Use the swift-start.yml playbook to attempt to restart the stopped
    process (it will start any process that has stopped -- you don't need
    to specifically name the process).

* swiftlm.swift.swift_services.check_ip_port

  - Reports if a service is listening to the correct ip and port
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * component: the process (daemon/server) being reported

  - Value Class: Status
  - Value Meta:

  * `ok`

    <name> is listening to the correct ip and port

  * `<name> is not listening to the correct ip or port`

    <name> is not listening to the correct ip or port

  - Description

    This metric reports whether or not rsync is listening to the correct ip or port

* swiftlm.load.host.val.five

  - Is the 5 minute load average of a host
  - Check: --system
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the 5 minute load average of a host. The value is
    derived from /proc/loadavg.

* swiftlm.hp_hardware.hpssacli.smart_array.firmware

  - Is the firmware version of a component of a Smart Array controller
  - Check: --hpssacli
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * component: Type of component this metric applies to. One of
      * controller: firmware version reported relates to the controller
    * model: The component model. Example: "Smart Array P410"
    * controller_slot: Slot number of controller

  - Value Class: Value
  - Value Meta: None

  - Description

    This metric reports the firmware version of a component of a Smart
    Array controller.

* swiftlm.hp_hardware.hpssacli.smart_array

  - Reports the status of a Smart Array component
  - Check: --hpssacli
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * component: Type of component this metric applies to. One of:
      * controller: The sub-component is a component of the controller
    * sub_component: Sub component this metric applies to.
      One of the following, where component is "controller":
      * controller_status: the status of controller is being reported
      * battery_capacitor_presence: the presence/absence of battery/capacitor is being reported
      * battery_capacitor_status: the status of battery/capacitor is being reported
      * cache_status: the status of the cache is being reported
      * controller_not_hba_mode: whether the controller is in HBA mode (hopefully, not)
    * model: The component model. Example: "Smart Array P410"
    * controller_slot: Slot number of controller

  - Value Class: Status
  - Value Meta:

    * `OK`

      No errors were found

    * `controller_status': <sub_component> status is <status>`

      The <sub-component> (controller, cache, etc) is in a failed/error
      status (as indicated by the <status> value)

    * Controller is in HBA mode; performance will be poor

      The controller is in HBA mode. This means that the cache is not used
      and hence performance of disk drives will be poor.

  - Description

    This reports the status of various sub-components of a Smart Array
    Controller. A failure is considered to have occured if:
    * Controller is failed
    * Cache is not enabled or has failed
    * Battery or capacitor is not installed
    * Battery or capacitor has failed

* swiftlm.hp_hardware.hpssacli.physical_drive

  - Reports the status of a Smart Array disk drive
  - Check: --hpssacli
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * component: Is "physical_drive"
    * controller_slot: Slot number of controller
    * box: Box number of the drive
    * bay: Bay number of the drive

  - Value Class: Status
  - Value Meta:

    * `OK`

      No errors were found

    * `Drive <serial_number>: <box>:<bay> has status: <status>`

      The disk drive identified by serial number, box and bay number has failed
      with a status as indicated by the <status> value.  On some Smart Arrays,
      the box/bay numbers are not deterministic so the serial number should be
      used to accurately determine the identity of a failed drive.

  - Description

    This reports the status of a disk drive attached to a Smart Array
    controller.

* swiftlm.hp_hardware.hpssacli.logical_drive

  - Reports the status of a Smart Array LUN
  - Check: --hpssacli
  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage
    * component: Is "logical_drive"
    * controller_slot: Slot number of controller
    * array: The name of the array of which this logical drive is a member
    * logical_drive: The identity of the logical drive
    * sub_component: One of:
      * lun_status: the metric reports the LUN status
      * cache_status: the metric reports the cache status of the LUN

  - Value Class: Status
  - Value Meta:

    * `OK`

      No errors were found

    * `Logical Drive <logical_drive> has status: <status>`

      The logical drive has failed with a status as indicated by the
      <status> value.

    * `Logical Drive <logical_drive> has cache status: <status>`

      The logical drive cache status is not enabled and working. Instead it has
      a status as indicated by the <status> value.

  - Description

    This reports the status of a LUN presented by a Smart Array
    controller. A LUN is considered failed if the LUN has failed or
    if the LUN cache is not enabled and working.

* swiftlm.swiftlm_check

  - Reports status of the Swiftlm Monasca-Agent Plug-in
  - Check: Generated by plug-in code

  - Dimensions:

    * hostname: set by Monasca Agent
    * service: object-storage

  - Value Class: Status
  - Value Meta:

    * `OK`

      The plug-in is working normally.

    * `file <file-name> stale metrics`

      The file contains old metrics i.e., the file does not appear to be
      updating. This can indicate that the program that generates the metrics
      has stopped running.

      The Swift Uptime Monitor is an example of such a program.

    * Other error messages

       The error message indicates the nature of the problem.

  - Description

    This indicates of the Swiftlm Monasca Agent Plug-in is running
    normally. If the status is failed, it probable that some or all metrics are
    no longer being reported.


* swiftlm.check.failure

  - Reports status of a swiftlm-scan check if an exception is raised
  - Check: Generated by plug-in code

  - Dimensions:

    * check: Name of the swiftlm-scan plugin
    * error: The error output from the plugin
    * component: swiftlm-scan
    * service: object-storage

  - Value Class: Status
  - Value Meta:

    * `OK`

      The plug-in is working normally.

    * `<check> failed with <error>`

      The check is the name of the swiftlm-scan plugin which was executing
      and raised an exception.  The error is the text of the exception.
      Examples of the hpssacli plugin expection message are:

      * `swiftlm.hp_hardware.hpssacli failed with: Traceback (most recent call last):...hpssacli ctrl all show detail failed with exit code: 123`

        The controller returned a non-zero exit code with error string of <error output>
        and an exit code of <exit code>

      * `swiftlm.hp_hardware.hpssacli failed with: Traceback (most recent call last):...hpssacli ctrl slot=<slot number> pd all show detail failed with exit code: 123`

        The controller returned a non-zero exit code with error string of <error output>
        and an exit code of <exit code>

      * `swiftlm.hp_hardware.hpssacli failed with: Traceback (most recent call last):...hpssacli ctrl slot=<slot number> ld all show detail failed with exit code: 123`

        The controller returned a non-zero exit code with error string of <error output>
        and an exit code of <exit code>

    * Other error messages

      The error output and exit code indicate the nature of the problem.

  - Description

    The total exception string is truncated if longer than 1919 characters and
    an ellipsis is prepended in the first three characters of the message.
    If there is more than one error reported, the list of errors is paired
    to the last reported error and the operator is expected to resolve
    failures until no more are reported.  Where there are no further reported
    errors, the Value Class is emitted as 'Ok'.

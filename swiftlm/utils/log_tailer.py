
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

from collections import defaultdict
import os
from stat import ST_INO


class LogTailer(object):
    """
    Read lines off tail end of a log file

    This class allows you to read lines at the end of a log file. If the
    file is closed and rotated, we reopen the file.
    """

    def __init__(self, log_file_name):
        self.log_file_name = log_file_name
        self.log_fd = open(log_file_name, 'r')
        self.log_fd.seek(0, os.SEEK_END)

    def lines(self):
        '''
        Read lines from end of file

        This generator returns lines that have been writen to the
        log file since the last time lines() was called.
        '''
        while True:
            line = self.log_fd.readline()
            if not line:
                # Get i-node number of the file descriptor and the
                # file on disk.
                stat_log_file = os.stat(self.log_file_name)
                stat_file_object = os.fstat(self.log_fd.fileno())
                if stat_log_file.st_ino != stat_file_object[ST_INO]:
                    # The i-node changed, so reopen log file
                    self.log_fd.close()
                    self.log_fd = open(self.log_file_name)
                    line = self.log_fd.readline()
                if not line:
                    break
            yield line

#
# Operation counting classes
#
# These classes are used to record stats for each access made. They count
# number of ops, bytes_put and bytes_get as a total, per-project and
# per-container (in a project)
#
# Notes:
#   - Any access counts as an operation (no matter verb/status)
#   - Only successful puts/gets are counted in the put/get bytes
#   - Only put/gets to an object are counted in put/get bytes
#   - PUT or POST is counted as a put bytes (COPY is server-side)
#


class HttpStatus(object):

    def __init__(self, http_status):
        self.status = int(http_status)

    def is_success(self):
        if self.status >= 200 and self.status < 300:
            return True
        return False


class OpsRecorder(object):
    def __init__(self):
        self.name = ''
        self.ops = 0
        self.bytes_put = 0
        self.bytes_get = 0

    def record_op(self, name, verb, http_status, bytes_transferred, obj):
        self.name = name
        if HttpStatus(http_status).is_success() and obj:
            if verb.lower() in ['put', 'post']:
                self.bytes_put += bytes_transferred
            elif verb.lower() in ['get']:
                self.bytes_get += bytes_transferred
            else:
                pass
        self.ops += 1

    def get_stats(self):
        return {'name': self.name, 'ops': self.ops,
                'bytes_put': self.bytes_put, 'bytes_get': self.bytes_get}

    def __repr__(self):
        return '%s' % self.get_stats()


class ProjectRecorder(object):

    def __init__(self):
        self.ops = OpsRecorder()
        self.containers = defaultdict(OpsRecorder)

    def record_op(self, project, verb, http_status, bytes_transferred,
                  container=None, obj=None):
        self.ops.record_op(project, verb, http_status, bytes_transferred, obj)
        if container:
            self.containers[container].record_op(container, verb, http_status,
                                                 bytes_transferred, obj)

    def get_stats(self):
        return self.ops.get_stats()

    def get_containers(self):
        for key in self.containers.keys():
            yield self.containers.get(key)

    def __repr__(self):
        repr = ''
        repr += '    stats: %s\n' % self.ops
        for container in self.get_containers():
            repr += '        container: %s' % container
        return repr


class AccessStatsRecorder(object):
    """
    Record stats for operations
    """
    def __init__(self):
        self.ops = OpsRecorder()
        self.projects = defaultdict(ProjectRecorder)

    def record_op(self, verb, http_status, bytes_transferred,
                  project=None, container=None, obj=None):
        self.ops.record_op('total', verb, http_status, bytes_transferred, obj)
        if project:
            self.projects[project].record_op(project, verb, http_status,
                                             bytes_transferred, container,
                                             obj)

    def get_stats(self):
        return self.ops.get_stats()

    def get_projects(self):
        for key in self.projects.keys():
            yield self.projects.get(key)

    def __repr__(self):
        repr = ''
        repr += 'stats: %s\n' % self.ops
        for project in self.get_projects():
            repr += '  project:\n %s\n' % project
        return repr


def split_path(path):
    """
    Splits path into component parts
    :param path: the path (e.g., /v1/AUTH_1234/c/o/sub)
    :return: a tuple containing account, container, obj
    """
    account = container = obj = None
    try:
        _, _, account = path.split('/', 2)
        _, _, account, container = path.split('/', 3)
        if not container:
            container = None
        _, _, account, container, obj = path.split('/', 4)
        if not obj:
            obj = None
    except ValueError:
        pass
    return account, container, obj


def parse_proxy_log_message(line, reseller_prefixes):
    """
    Extract proxy access record from a Swift log

    This function parses a Swift log looking for messages written by the
    proxy-logging middleware. Matching records result in a dict cotaining
    key information about the transaction. Otherwise a string type is returned
    for any ofthe following:

    - Not written by proxy-logging middleware
    - Where swift.source is not '-' (i.e., an internal request)
    - Where the account starts with '.' (e.g., reconciler account)

    :param line: a single line of text, describes a single transaction.

        A valid line from the proxy-logging middleware looks like the
        following:
            <log_date> <server> <server_type>: <client1> <client2>
            <server_date> <REST_operation> <account_path> HTTP/1.0
            <response_code> - <client_agent> <auth> <bytes-rcv> <bytes-sent> -
            <trans_id> - <time> <swift.source>

            where:
                <log_date>: stands for the date and time as writen
                    by rsylog;
                <server>: hostname of the server;
                <server_type>: is "proxy-server" if an access log
                <client1>: client - load balancer;
                <client2>: client - local;
                <server_date>: date and time as writen by proxy;
                <REST_operation>: one of the REST api methods eg. GET, PUT;
                <account_path>: account processing the transaction,
                    eg. /v1.0/AUTH_655a7b18-83cc-447a/...
                    where AUTH_... specifies the name of the account;
                <response_code>: server response:
                                    - 2xx - Success
                                    - 3xx - Redirection
                                    - 4xx - Client error
                                    - 5xx - Server error;
                <client_agent>: client library (e.g., curl, Java)
                <auth>: specifies authentication token (or '-');
                <bytes-rcv>: bytes received (in PUT, etc)
                <bytes-sent>: bytes sent (in GET, etc)
                <trans_id>: stands for the id of the single transaction;
                <time>: time to execute the transaction.
                <swift.source>: is '-' if the response sent to the user;
                    otherwise, it's a middleware internal request

    :param reseller_prefixes: Usually ["AUTH_"]. Accounts associated with a
        project must start with one of these prefixes.

    :return: A dict containing the following keys:
            http_status        HTTTP status code
            verb               One of "PUT", "GET", etc
            bytes_transferred  Size of PUT or GET object (or zero)
            project            Project id (or None if operation does not
                               involve a project)
            container          Container name (UTF-8 encoded). (or None if
                               operation does not involve a container)
            obj                Name of object (or None if operation does not
                               involve an object)
        or a string indicating why the line is not proxy-logging message (this
        is a debug aid)
    """
    try:
        pieces = line.split()
        if 'HTTP' not in pieces[10]:
            return 'HTTP not in expected place'
        if 'proxy-server' not in pieces[4]:
            return 'not proxt-server'
        swift_source = pieces[21]
        if swift_source is not '-':
            return 'is internal swift_source'

        path = pieces[9].split('%3F')[0]  # remove query string
        account, container, obj = split_path(path)
        project = None
        if account:
            for prefix in reseller_prefixes:
                if account.startswith(prefix):
                    project = account[len(prefix):]
        if account and account.startswith('.'):
            return 'internal/utility account'

        response = int(pieces[11])
        verb = pieces[8]
        if verb not in ['HEAD', 'GET', 'PUT', 'POST', 'COPY',
                        'DELETE', 'OPTIONS']:
            return 'did not find verb'

        content_size = 0
        bytes_received = pieces[15]
        bytes_sent = pieces[16]
        if not bytes_received == '-':
            content_size = int(bytes_received)
        if not bytes_sent == '-':
            content_size = int(bytes_sent)

        return {'http_status': response, 'verb': verb,
                'bytes_transferred': content_size, 'project': project,
                'container': container, 'obj': obj}

    except Exception:  # noqa
        # Line too short, missing information, not of interest.
        return 'not valid proxy-logging message'

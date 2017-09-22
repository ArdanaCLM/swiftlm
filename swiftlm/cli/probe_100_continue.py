
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

from httplib import HTTPSConnection, HTTPConnection, HTTPResponse, HTTPMessage
from httplib import CONTINUE, _UNKNOWN
from optparse import OptionParser
import os
import socket
import sys
from urlparse import urlparse


usage = """
Program to test a Swift system to see if it responds with a 100 Continue
response when the Expect:100-continue request header is specified.
The reason for testing is that if the system does not respond,
the client has to timeout before sending the body/content. As a result
such clients suffer lower performance when uploading objects. Not all
clients use Expect:100-continue. Libcurl is known to use the feature.

Swift itself responds to Expect:100-continue. However, front-ends have
been known not to respond. So this is really a test of the SSL termination
or load balancer that front-ends Swift.

Usage:

    probe_100_continue.py --os-auth-token=<token>
                          --os-storage-url=https://<endpoint>:8080/v1/<account>
"""


class ExpectHTTPResponse(HTTPResponse):

    def __init__(self, sock, debuglevel=0, strict=0, method=None):
        self.sock = sock
        self.fp = sock.makefile('rb')
        self.debuglevel = debuglevel
        self.strict = strict
        self._method = method

        self.msg = None

        # from the Status-Line of the response
        self.version = _UNKNOWN         # HTTP-Version
        self.status = _UNKNOWN          # Status-Code
        self.reason = _UNKNOWN          # Reason-Phrase

        self.chunked = _UNKNOWN         # is "chunked" being used?
        self.chunk_left = _UNKNOWN      # bytes left to read in current chunk
        self.length = _UNKNOWN          # number of bytes left in response
        self.will_close = _UNKNOWN      # conn will close at end of response

    def expect_response(self):
        if self.fp:
            self.fp.close()
            self.fp = None
        self.fp = self.sock.makefile('rb', 0)
        version, status, reason = self._read_status()
        if status != CONTINUE:
            self._read_status = lambda: (version, status, reason)
            self.begin()
        else:
            self.status = status
            self.reason = reason.strip()
            self.version = 11
            self.msg = HTTPMessage(self.fp, 0)
            self.msg.fp = None


class ExpectHTTPSConnection(HTTPSConnection):

    response_class = ExpectHTTPResponse

    def putrequest(self, method, url, skip_host=0, skip_accept_encoding=0):
        self._method = method
        self._path = url
        return HTTPSConnection.putrequest(self, method, url, skip_host,
                                          skip_accept_encoding)

    def getexpect(self):
        response = ExpectHTTPResponse(self.sock, strict=self.strict,
                                      method=self._method)
        response.expect_response()
        return response


class ExpectHTTPConnection(HTTPConnection):

    response_class = ExpectHTTPResponse

    def putrequest(self, method, url, skip_host=0, skip_accept_encoding=0):
        self._method = method
        self._path = url
        return HTTPConnection.putrequest(self, method, url, skip_host,
                                         skip_accept_encoding)

    def getexpect(self):
        response = ExpectHTTPResponse(self.sock, strict=self.strict,
                                      method=self._method)
        response.expect_response()
        return response


def http_connect(scheme, ipaddr, port, method, path, headers=None,
                 timeout=10):
    if scheme == 'https':
        conn = ExpectHTTPSConnection('%s:%s' % (ipaddr, port), timeout=timeout)
    else:
        conn = ExpectHTTPConnection('%s:%s' % (ipaddr, port), timeout=timeout)
    conn.path = path
    conn.putrequest(method, path, skip_host=(headers and 'Host' in headers))
    if headers:
        for header, value in headers.iteritems():
            conn.putheader(header, str(value))
    conn.endheaders()
    return conn


def probe_100_continue(url, token):
    """
    Test Expect: 100-continue
    """

    # Get endpoint IP address, port, etc.
    urlparts = urlparse(url)
    ipaddr = socket.gethostbyname(urlparts.hostname)
    port = urlparts.port
    scheme = urlparts.scheme
    if scheme == 'https' and not port:
        port = 443
    if scheme == 'http' and not port:
        port = 80

    # We first need to create a container
    try:
        headers = {}
        headers['X-Auth-Token'] = token
        path = urlparts.path + '/100-continue-test'
        print('Creating container: PUT %s' % path)
        conn = http_connect(scheme, ipaddr, port, 'PUT', path,
                            headers=headers, timeout=6)
    except Exception as err:
        print('Failed to connect to: %s:%s\nReason: %s' % (ipaddr, port, err))
        print('\nTest result: UNKNOWN')
        sys.exit(1)
    try:
        response = conn.getexpect()
    except Exception as err:
        print('Failed to get response: %s' % err)
        print('\nTest result: UNKNOWN')
        sys.exit(1)
    if response.status not in (200, 201, 202, 204):
        print('Received: HTTP %s %s' % (response.status, response.reason))
        print('%s' % response.msg)
        print(response.read())
        print('\nTest result: UNKNOWN')
        sys.exit(1)

    # Create object using expect:100-continue
    # The request must be a PUT on an object and must have a non-zero
    # Content-Length. We set Content-Length, but don't bother to actually
    # send data -- we only need to see the 100 response.
    try:
        headers = {}
        headers['X-Auth-Token'] = token
        headers['Expect'] = '100-continue'
        headers['Content-Length'] = 1200
        path = urlparts.path + '/100-continue-test/100-continue-test-obj'
        print('Connecting to ipaddr: %s port: %s' % (ipaddr, port))
        conn = http_connect(scheme, ipaddr, port, 'PUT', path,
                            headers=headers, timeout=3)
    except Exception as err:
        print('Failed to connect: %s' % err)
        print('\nTest result: UNKNOWN')
        sys.exit(1)

    # Wait for response and check it.
    try:
        print('Waiting for response...')
        response = conn.getexpect()
    except Exception as err:
        print('Failed to get response: %s' % err)
        print('\nTest result: UNKNOWN')
        sys.exit(1)

    if response.status == 100:
        print('Received: HTTP 100 Continue')
        print('\nTest result: PASSED')
        sys.exit(0)
    else:
        print('Received: HTTP %s %s' % (response.status,
                                        response.reason))
        try:
            print('%s' % response.msg)
            print(response.read())
        except Exception as err:
            print('Unable to read response body')
        print('\nTest result: FAILED')
        sys.exit(1)


def main():
    parser = OptionParser(usage=usage)
    parser.add_option('--os-storage-url', dest='os_storage_url', default=None)
    parser.add_option('--os-auth-token', dest='os_auth_token', default=None)
    (options, args) = parser.parse_args()

    url = None
    token = None
    url = options.os_storage_url
    token = options.os_auth_token
    if not (url and token):
        print('Please specify --os-storage-url and --os-auth-token\n'
              'Use --help to show usage.')
        sys.exit(1)

    probe_100_continue(url, token)

if __name__ == '__main__':
    main()

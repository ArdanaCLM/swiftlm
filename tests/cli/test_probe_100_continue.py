#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2017 SUSE LLC
# Copyright (c) 2010-2012 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import eventlet
from eventlet.green import subprocess
import os.path
import unittest


class WsgiServer(unittest.TestCase):

    def setUp(self):
        testdir = os.path.dirname(__file__)
        cmdpath = os.path.normpath(os.path.join(testdir, '../utils'))
        self.cmdname = os.path.join(cmdpath, 'probe_100_continue.py')

    def test_100_continue(self):
        running = True

        def handle(sock):
            put_container_done = False
            while running:
                try:
                    with eventlet.Timeout(0.1):
                        (conn, addr) = sock.accept()
                except eventlet.Timeout:
                    continue
                else:
                    if not put_container_done:
                        conn.send('HTTP/1.1 200 OK\n\n')
                        put_container_done = True
                    else:
                        conn.send('HTTP/1.1 100 Continue\n\n')
            sock.close()

        sock = eventlet.listen(('', 0))
        port = sock.getsockname()[1]
        url = 'http://127.0.0.1:%s' % port
        server = eventlet.spawn(handle, sock)

        try:
            args = ['python', self.cmdname,
                    '--os-storage-url', url, '--os-auth-token', 'dummy']
            process = subprocess.Popen(args,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            output, err = process.communicate()
            self.assertTrue('Test result: PASSED' in output,
                            'probe_100_continue: %s %s' % (output, err))
        except Exception as err:
            self.fail('python probe_100_continue: %s' % err)
        finally:
            running = False
        server.wait()

    def test_no_100_continue(self):
        running = True

        def handle(sock):
            while running:
                try:
                    with eventlet.Timeout(0.1):
                        (conn, addr) = sock.accept()
                except eventlet.Timeout:
                    continue
                else:
                    conn.send('HTTP/1.1 200 OK\n\n')
            sock.close()

        sock = eventlet.listen(('', 0))
        port = sock.getsockname()[1]
        url = 'http://127.0.0.1:%s' % port
        server = eventlet.spawn(handle, sock)

        try:
            args = ['python', self.cmdname,
                    '--os-storage-url', url, '--os-auth-token', 'dummy']
            process = subprocess.Popen(args,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            output, err = process.communicate()
            self.assertTrue('Test result: FAILED' in output,
                            'probe_100_continue: %s %s' % (output, err))
        except Exception as err:
            self.fail('python probe_100_continue: %s' % err)
        finally:
            running = False
        server.wait()

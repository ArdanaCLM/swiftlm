# Copyright (c) 2014 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
    Report status in program friendly format
"""

from __future__ import print_function


import json
import optparse
import sys
import yaml
from swiftlm.utils.scout import SwiftlmScout


def scout_main():
        """
        Gather data and print it.
        """
        usage = '''
        usage: {prog} [ --conf=<file>]
                      [--all]
                      [--aggregate]
                      [--path <path> [--ring_type=<ring_type>]]
                      [--timeout=<seconds>]
                      [--verbose]
                      [--outformat= yaml | json]

        Examples:
            {prog} --all --outformat=yaml
            {prog} --path diskusage --verbose
        '''.format(prog='swiftlm-scout')
        args = optparse.OptionParser(usage)
        args.add_option('--all', action='store_true', default=False,
                        help='Gather all known data')
        args.add_option('--aggregate', action='store_true', default=False,
                        help='Only gather data for aggregation')
        args.add_option('--path', default=None,
                        help='Gather a specific item. Typically used in'
                             ' testing')
        args.add_option('--ring_type', default=None,
                        help='Ring to use with --path')
        args.add_option('--outformat', type='string', metavar='FORMAT',
                        help='Format of output.'
                        ' Supported values are:'
                        ' "yaml" (default), "json"',
                        default='yaml')
        args.add_option('--timeout', type='int', metavar='SECONDS',
                        help='Time to wait for a response from a server',
                        default=5)
        args.add_option('--conf', default='/etc/swiftlm/scout.conf',
                        help='Reserved for future use')
        args.add_option('--verbose', action='store_true',
                        help='Print verbose info. Useful to troubleshoot.')
        args.add_option('--show_errors', action='store_true',
                        default=False,
                        help='Do not suppress errors')
        options, arguments = args.parse_args()
        actions = ['all']
        if options.all:
            actions = ['all']
        if options.aggregate:
            actions = ['aggregate']
        if options.path:
            actions = ['path']
            path_ring_type = 'all'
            recon_path = options.path
            if options.ring_type:
                path_ring_type = options.ring_type
        suppress_errors = True
        if options.show_errors:
            suppress_errors = False
        if options.verbose:
            suppress_errors = False

        recon_data = SwiftlmScout({},
                                  suppress_errors=suppress_errors,
                                  verbose=options.verbose,
                                  timeout=options.timeout)

        if 'all' in actions:
            recon_data.scout_all()
        if 'aggregate' in actions:
            recon_data.scout_aggregate()
        if 'path' in actions:
            recon_data.path(recon_path, path_ring_type)

        collected = recon_data.get_results()

        if options.outformat == 'json':
            print(json.dumps(collected))
        elif options.outformat == 'yaml':
            print(yaml.safe_dump(collected, allow_unicode=True,
                                 default_flow_style=False))
        else:
            print('Invalid value for --outformat')
            sys.exit(1)


def main():
    try:

        scout_main()
    except KeyboardInterrupt:
        print('\n')


if __name__ == '__main__':
    main()

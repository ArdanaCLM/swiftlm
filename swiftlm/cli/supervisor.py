# encoding: utf-8

# (c) Copyright 2015, 2016 Hewlett Packard Enterprise Development LP
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

from optparse import OptionParser
import sys
import os
from yaml import safe_load, scanner
from swiftlm.rings.ardana_model import Consumes, ServersModel
from swiftlm.rings.ring_builder import RingBuilder, RingDelta
from swiftlm.rings.ring_model import RingSpecifications, \
    SwiftModelException, DriveConfigurations, DriveConfiguration

DEFAULT_ETC = '/etc/swiftlm'
DEFAULT_CONFIG_DIR = 'config'
DEFAULT_INPUT_VARS = 'input-model.yml'
DEFAULT_CP_SERVERS = 'control_plane_servers.yml'
DEFAULT_BUILDER_DIR = 'builder_dir'
DEFAULT_SWIFT_RING_BUILDER_CONSUMES = 'swift_ring_builder_consumes.yml'
DEFAULT_DEPLOY_DIR = 'deploy_dir'
DEFAULT_RING_DELTA = 'ring-delta.yml'
DEFAULT_OSCONFIG = 'drive_configurations'
DEFAULT_CONFIGURATION_DATA = 'configuration_data.yml'

usage = '''

    % {cmd} --cloud <cloud-name> --control-plane <control-plane>
            [--make-delta [--weight-step <value> ] [--stop-on-warnings]]
            [--rebalance [--dry-run]]
            [--report [--detail=summary|full]]
            [--etc <dirname>]
            [--ring-delta <filename> [--format yaml|json]
            [--help]

Examples:

    Example 1:

    Create a ring-delta file given an input model and (possibly) existing
    rings. The results are written to the ./ring-delta.yml file. If a ring
    does not exist in ./builder_dir, the ring-delta file will contain
    directives to create the ring.

    % {cmd} --make-delta
            --ring-delta ./ring-delta.yml
            --cloud standard --control-plane ccp

    Example 2:

    Update and rebalance (usually existing) rings given a ring-delta file.
    The command reads the ./ring-delta.yml file and updates the rings.
    Add --dry-run to see what commands would be issued to swift-ring-builder:

    % {cmd} --cloud cld --control_plane ccp
            --rebalance
            --ring-delta ./ring-delta.yml
            --cloud standard --control-plane ccp

    Example 3:
    Rebalance existing rings. This is similar to the above command except
    the ring-delta defaults.

    % {cmd} --rebalance
            --builder_dir ./builder_dir
            --cloud standard --control-plane ccp

    Example 4:

    Build, update and rebalance rings given an input model and (possibly)
    existing rings. This command compresses examples 1 and 2 above into
    a single command.

    % {cmd} --make-delta --rebalance
            --cloud standard --control-plane ccp

    Example 5:

    Rebalance rings after adding or removing a number of servers
    The --weight-step option prevents weights being moved too
    quickly on the new servers. --weight-step is only needed if it
    is not present in the ring-specifications.

    % {cmd} --make-delta --rebalance --weight-step 4.0
            --cloud standard --control-plane ccp

    Example 6:

    Show  the actions that would be performed if a --rebalance is performed
    using a ring delta file as specified by the --ring-delta option (built
    using a prior --make-delta). These variants give different levels of
    detail:

    % {cmd} --report --detail summary
            --ring-delta /tmp/ring-delta.yaml
            --cloud standard --control-plane ccp

    % {cmd} --report --detail full
            --ring-delta /tmp/ring-delta.yaml
            --cloud standard --control-plane ccp

    % {cmd} --make-delta --rebalance --dry-run
            --ring-delta /tmp/ring-delta.yaml
            --cloud standard --control-plane ccp

    '''.format(cmd=os.path.basename(__file__))


class CloudMultiSite(object):
    """
    Manage multi-site aspects

    This class ties the models from several control planes into a coordinated
    view of the world. The purpose is to support Swift regions, where we've
    deployed two or more clouds independently. By copying data files from
    the "secondary" control planes, we can build rings on the "primary" control
    plane. We then copy the builder files/rings back to the secondary
    control planes.

    Most of the time, there is only one primary control plane (i.e.,
    the system we are running on now, so there will only be one set
    of input data).

    The cloud model data is structured as follows:

        /etc/swiftlm/<cloud>/<control-plane>/config/ - contains the model

        /etc/swiftlm/<cloud>/<control-plane>/builder_dir/ - where we store
        builder files and rings for this system (as specified by the
        --cloud and --control-plane options)

        /etc/swiftlm/<cloud>/<control-plane>ring-delta.yml - where we store
        the ring delta

    The files in the config directory are as follows:

        input-model.yml -- contains legacy list of servers
        control_plane_servers.yml -- list of servers in this control plane
        swift_ring_builder_consumes.yml -- the network relationships
        configuration_data.yml -- the Swift configuration-data object
        drive_configurations/ -- directory containing files named
                                 <hostname>/drive_configurations.yml
    """

    def __init__(self, options):
        '''
        Walk the etc structure to discover the control planes

        :param options: The options supplied to the swiftlm-ring-supervisor:
                        --cloud: this cloud name
                        --control_plane: this control plane
                        --etc: usually /etc/swiftlm
        '''

        self.my_cloud = options.cloud
        self.my_control_plane = options.control_plane
        self._paths = {}

        for cloud in [f for f in os.listdir(options.etc) if
                      os.path.isdir(os.path.join(options.etc, f))]:
            if cloud == 'legacy_builder_dir':
                # We will leave legacy builder files in /etc/swiftlm
                # we assume no cloud will be called "legacy_builder_dir"!
                continue
            cloud_path = os.path.join(options.etc, cloud)
            for control_plane in [f for f in os.listdir(cloud_path) if
                                  os.path.isdir(os.path.join(cloud_path,
                                                             f))]:
                control_plane_path = os.path.join(cloud_path,
                                                  control_plane)
                config_dir_path = os.path.join(control_plane_path,
                                               DEFAULT_CONFIG_DIR)
                self._paths[(cloud, control_plane)] = {
                    # Inputs
                    'input-model': os.path.join(config_dir_path,
                                                DEFAULT_INPUT_VARS),
                    'control_plane_servers': os.path.join(
                        config_dir_path, DEFAULT_CP_SERVERS),
                    'swift_ring_builder_consumes': os.path.join(
                        config_dir_path,
                        DEFAULT_SWIFT_RING_BUILDER_CONSUMES),
                    'osconfig': os.path.join(config_dir_path,
                                             DEFAULT_OSCONFIG),
                    'configuration_data': os.path.join(
                        config_dir_path, DEFAULT_CONFIGURATION_DATA),
                    # Outputs
                    'ring-delta': (options.ring_delta or
                                   os.path.join(control_plane_path,
                                                DEFAULT_RING_DELTA)),
                    'builder_dir': os.path.join(control_plane_path,
                                                DEFAULT_BUILDER_DIR)
                }

        # Validate that we found a directory for the control plane
        # we're running on.
        found = False
        for cloud, control_plane in self._paths.keys():
            if (cloud == self.my_cloud and
                    control_plane == self.my_control_plane):
                found = True
        if not found and not options.unittest:
            sys.exit('Cannot find configuration files in %s' %
                     os.path.join(options.etc, self.my_cloud,
                                  self.my_control_plane))

    def path(self, cloud, control_plane):
        return self._paths[(cloud, control_plane)]

    def control_planes(self):
        return self._paths.keys()


def main():
    parser = OptionParser(usage=usage)
    parser.add_option('--etc', dest='etc',
                      default=DEFAULT_ETC,
                      help='Overrides /etc/swiftlm (for testing)')
    parser.add_option('--cloud', dest='cloud', default=None,
                      help='The name of the cloud')
    parser.add_option('--control-plane', dest='control_plane', default=None,
                      help='The name of the control plane')
    parser.add_option('--ring-delta', dest='ring_delta', default=None,
                      help='Name of ring-delta file (as output or input'
                           ' A value of "-" (on output means to write'
                           ' to stdout')
    parser.add_option('--format', dest='fmt', default='yaml',
                      help='One of yaml or json.'
                           ' When used with --ring-delta, specifies the'
                           ' format of the file.')
    parser.add_option('--detail', dest='detail', default='summary',
                      help='Level of detail to use with --report.'
                           ' Use summary or full')
    parser.add_option('--report', dest='report', default=False,
                      action="store_true",
                      help='Explain what the ring delta represents.'
                           ' Optionally use --detail.')
    parser.add_option('--dry-run', dest='dry_run', default=False,
                      action="store_true",
                      help='Show the proposed swift-ring-builder commands')
    parser.add_option('--pretend-min-part-hours-passed',
                      dest='pretend_min_part_hours_passed', default=False,
                      action="store_true",
                      help='Executes the pretend_min_part_hours_passed command'
                           ' on each ring before running rebalance.'
                           ' Use with caution.')
    parser.add_option('--make-delta', dest='make_delta', default=False,
                      action="store_true",
                      help='Make a ring delta file')
    parser.add_option('--rebalance', dest='rebalance', default=False,
                      action="store_true",
                      help='Build (or rebalance) rings')
    parser.add_option('--limit-ring', dest='limit_ring', default=None,
                      help='Limits actions to given ring')
    parser.add_option('--size-to-weight', dest='size_to_weight',
                      default=float(1024 * 1024 * 1024),
                      help='Conversion factor for size to weight. Default is'
                           ' 1GB is weight of 1 (a 4Tb drive would be assigned'
                           ' a weight of 4096')
    parser.add_option('--weight-step', dest='weight_step',
                      default=None,
                      help='When set, weights are changed by at most this'
                           ' value. Overrides value in ring specification.')
    parser.add_option('--allow-partitions', dest='allow_partitions',
                      default=False, action='store_true',
                      help='Allow devices to be assigned to partitions.'
                           ' Default is to use a full disk drive.')
    parser.add_option('--stop-on-warnings', dest='stop_on_warnings',
                      default=False, action='store_true',
                      help='Used with --make-delta. Exit with error if there'
                           ' are model missmatch warnings.'
                           ' Default is to only exit with error for errors.')
    parser.add_option('--unittest', dest='unittest',
                      default=False, action='store_true',
                      help='Set by unittests. Never set on command line.')
    (options, args) = parser.parse_args()

    if not (options.cloud and options.control_plane):
        sys.exit('Must specify both --cloud and --control_plane')

    sites = CloudMultiSite(options)
    my_cloud = sites.my_cloud
    my_control_plane = sites.my_control_plane
    my_config = sites.path(my_cloud, my_control_plane)

    #
    # Work out what we need to do. Validate arguments needed by an action
    # are present.
    #
    actions = []
    if options.make_delta:
        actions.append('init-delta')
        actions.append('input-from-model')
        actions.append('read-builder-dir')
        actions.append('open-osconfig-dir')
        actions.append('make-delta')
        actions.append('write-to-delta')

        if options.fmt not in ['yaml', 'json']:
            print('Invalid value for --format')

    if options.report:
        actions.append('init-delta')
        actions.append('read-from-delta')
        actions.append('report')

        if options.detail not in ['summary', 'full']:
            sys.exit('Invalid value for --detail')

    if options.rebalance:
        actions.append('init-delta')
        actions.append('open-builder-dir')
        actions.append('read-from-delta')
        actions.append('rebalance')

        if options.fmt not in ['yaml', 'json']:
            print('Invalid value for --format')

    if len(actions) == 0:
        sys.exit('Missing an option to perform some action')
    if options.report and (options.make_delta or
                           options.rebalance):
        sys.exit('Do not mix --report with other actions')

    #
    # Perform actions
    #
    if 'init-delta' in actions:
        delta = RingDelta()

    if 'input-from-model' in actions:
        servers_model = ServersModel('unused', 'unused')
        consumes = Consumes()
        ring_model = RingSpecifications(my_cloud, my_control_plane)
        for cloud, control_plane in sites.control_planes():
            config = sites.path(cloud, control_plane)
            input_model_fd = None
            try:
                input_model_fd = open(config.get('input-model'), 'r')
            except IOError as err:
                pass  # File may not exist since its a legacy item
            try:
                cp_server_fd = None
                cp_server_fd = open(config.get('control_plane_servers'), 'r')
            except IOError as err:
                sys.exit('Error on control_plane_server.yml: %s' % err)
            try:
                control_plane_servers = None
                if cp_server_fd:
                    control_plane_servers = safe_load(cp_server_fd)
            except scanner.ScannerError as err:
                sys.exit('ERROR reading/parsing: %s' % err)
            try:
                consumes_fd = open(config.get('swift_ring_builder_consumes'),
                                   'r')
            except IOError as err:
                sys.exit('ERROR: %s' % err)
            try:
                input_vars = {'global': {}}
                if input_model_fd:
                    input_vars = safe_load(input_model_fd)
                consumes_model = safe_load(consumes_fd)
            except scanner.ScannerError as err:
                sys.exit('ERROR reading/parsing: %s' % err)
            try:
                if control_plane_servers:
                    servers = control_plane_servers.get(
                        'control_plane_servers')
                elif input_vars.get('global').get('all_servers'):
                    servers = input_vars.get('global').get('all_servers')
                else:
                    sys.exit('No servers found in control plane')
                servers_model.add_servers(cloud, control_plane, servers)
                consumes.load_model(consumes_model)
            except SwiftModelException as err:
                sys.exit(err)
        servers_model.register_consumes(consumes)

        try:
            config_data_fd = open(my_config.get('configuration_data'),
                                  'r')
            config_data = safe_load(config_data_fd)
        except (IOError, scanner.ScannerError) as err:
            sys.exit('Rings should be in configuration-data.'
                     ' Using old configuration processor?')
        try:
            rings_loaded = False
            if input_vars.get('global').get('all_ring_specifications'):
                # Model contains Ardana old-style rings
                ring_model = RingSpecifications(my_cloud, my_control_plane,
                                                model=input_vars)
                rings_loaded = True
            if config_data and config_data.get('control_plane_rings',
                                               config_data.get(
                                                   'control-plane-rings')):
                # Model contains new-style rings --- use instead
                ring_model.load_configuration(my_cloud, my_control_plane,
                                              config_data)
                rings_loaded = True
            if not rings_loaded:
                sys.exit('No ring specifications in input model')
        except SwiftModelException as err:
            sys.exit(err)

    if 'open-builder-dir' or 'read-builder-dir' in actions:
        try:
            read_rings = False
            if 'read-builder-dir' in actions:
                read_rings = True
            rings = RingBuilder(my_config.get('builder_dir'),
                                read_rings=read_rings)
        except IOError as err:
            sys.exit('ERROR: %s' % err)

    if 'open-osconfig-dir' in actions:
        drive_configurations = osconfig_load(sites)

    if 'make-delta' in actions:
        try:
            generate_delta(sites, servers_model, ring_model, rings,
                           drive_configurations, options, delta)
        except SwiftModelException as err:
            sys.exit('ERROR: %s' % err)

    if 'write-to-delta' in actions:
        if my_config.get('ring-delta') == '-':
            write_to_file_fd = sys.stdout
        else:
            write_to_file_fd = open(my_config.get('ring-delta'), 'w')
        delta.write_to_file(write_to_file_fd, options.fmt)

    if 'read-from-delta' in actions:
        if my_config.get('ring-delta') == '-':
            sys.exit('--ring-delta- is invalid (read from stdin'
                     'not supported)')
        try:
            delta = RingDelta()
            read_from_delta_fd = open(my_config.get('ring-delta'), 'r')
            delta.read_from_file(read_from_delta_fd, options.fmt)
        except IOError as err:
            sys.exit('ERROR: %s' % err)

    if 'report' in actions:
        print(delta.get_report(options))

    if 'rebalance' in actions:
        rebalance(delta, rings, options)


def osconfig_load(sites):
    """
    Load disk drive data

    :param sites: provides access to the config directory structure
    :return: the device size data
    """
    drive_configurations = DriveConfigurations()
    for cloud, control_plane in sites.control_planes():
        osconfig_dir = sites.path(cloud, control_plane).get('osconfig')
        for host in os.listdir(osconfig_dir):
            filename = os.path.join(osconfig_dir, host,
                                    'drive_configuration.yml')
            if os.path.exists(filename):
                try:
                    with open(filename) as fd:
                        model_in_file = safe_load(fd)
                        drive_configuration = DriveConfiguration()
                        items = model_in_file.get('ardana_drive_configuration',
                                                  [])
                        for item in items:
                            drive_configuration.load_model(item)
                            drive_configurations.add(drive_configuration)
                except (IOError, scanner.ScannerError) as err:
                    sys.exit('ERROR reading/parsing: %s' % err)
    return drive_configurations


def generate_delta(sites, servers_model, ring_model, rings,
                   drive_configurations, options, delta):
    """
    Generate delta between input model and existing rings

    This function compares the input model, the existing rings and device
    size data and works out what changes need to be made to the rings. The
    output is a ring delta data structure that for each ring and device
    contains instructions to either add, update or remove the ring or
    device.

    Major problems with the input data model will raise SwiftModelException.
    Minor problems are printed to stdout.

    :param sites: Access to (multi) site setup
    :param servers_model: The input vars describing the servers
    :param ring_model: Ring specifications (from input model)
    :param rings: The existing rings (or placeholder if not already created)
    :param drive_configurations: device size data from probing hardware
    :param options: options to control ring building
    :param delta: The delta to generate
    :return: Nothing -- the output is in the delta argument
    """

    model_errors = []
    model_warnings = []

    # Get ring specifications for this system
    my_cloud = sites.my_cloud
    my_control_plane = sites.my_control_plane
    control_plane_rings = ring_model.get_control_plane_rings(my_cloud,
                                                             my_control_plane)

    if not control_plane_rings.is_primary_control_plane():
        print('This is not the primary control_plane -- ring building is'
              ' not done on this system.')
        delta.register_primary(False)
        return

    #
    # Run through the rings in the model
    # Register them in the ring delta
    # If builder files do not exist, mark them to be created
    #
    for ringspec in control_plane_rings.rings:
        ring_name = ringspec.name
        delta.register_ring(ring_name, ringspec)
        if not rings.builder_rings.get(ring_name):
            # Ring is in input model, but no builder file exists
            delta.delta_ring_actions[ring_name] = ['add']
            # Override replica count if there are not enough devices
            count_overriden = override_replica_count(ringspec,
                                                     servers_model,
                                                     model_errors,
                                                     model_warnings)
            if count_overriden:
                ringspec.replica_count = count_overriden

    #
    # Cross check that we have ring specifications for each system
    # referenced by configuration files
    #
    try:
        for cl, cp in sites.control_planes():
            if not ring_model.get_control_plane_rings(cl, cp):
                model_errors.append('Model Mismatch:'
                                    ' Cannot find rings-specification for'
                                    ' cloud %s control-plane %s.'
                                    ' This error may cause many subsequent'
                                    ' errors.' % (cl, cp))
    except SwiftModelException as err:
        model_errors.append(err)

    #
    # Run through the builder files and match them against the model
    # Check if model and builder file attributes differ
    # If not in model anymore, mark the ring to be removed
    #
    for ring_name in rings.builder_rings.keys():
        if delta.delta_rings.get(ring_name):
            # Ring already exists
            delta.delta_ring_actions[ring_name] = ['present']
            model_ring = control_plane_rings.get_ringspec(ring_name)
            builder_ring = rings.get_ringspec(ring_name)
            # Handle replica_count upgrade to Mitaka
            delta_ring = delta.delta_rings.get(ring_name)
            count_overriden = override_replica_count(model_ring,
                                                     servers_model,
                                                     model_errors,
                                                     model_warnings)
            if count_overriden:
                delta_ring.replica_count = count_overriden
                model_ring.replica_count = count_overriden
            # See if replica count or min_part_hours in model has changed
            if model_ring.replica_count != builder_ring.replica_count:
                delta.delta_ring_actions[ring_name].append('set-replica-count')
            if model_ring.min_part_hours != builder_ring.min_part_hours:
                delta.delta_ring_actions[ring_name].append(
                    'set-min-part-hours')
            # Copy the min_part_hours remaining time to the delta file
            model_ring['remaining'] = builder_ring.remaining
        else:
            # Found builder file, but ring not in model anymore
            delta.register_ring(ring_name,
                                rings.builder_rings.get(ring_name))
            delta.delta_ring_actions[ring_name] = ['remove']

    #
    # Run through all devices in the input model
    # If already in ring, check if the weight should be changed
    # If not in ring, mark it to be added
    #
    try:
        for device_info in servers_model.iter_devices():

            # Update the device info with the region and zone id from the
            # ring specifications.
            region_id, zone_id = control_plane_rings.get_region_zone(
                device_info.ring_name, device_info.server_groups)
            not_found_in = ''
            if not region_id:
                not_found_in = 'swift-regions'
            if not zone_id:
                not_found_in = 'swift-zones'
            if not_found_in:
                model_errors.append('Model Mismatch:'
                                    ' Cannot find server-groups %s in'
                                    ' "ring-specifications". Check the "%s"'
                                    ' item for ring %s.'
                                    ' Server is'
                                    ' %s' % (','.join(
                                             device_info.server_groups),
                                             not_found_in,
                                             device_info.ring_name,
                                             device_info.server_name)
                                    )
                continue
            # -1 means not defined, default to 1
            if region_id == -1:
                region_id = 1
            if zone_id == -1:
                zone_id = 1
            device_info.region_id = region_id
            device_info.zone_id = zone_id

            # See if the device is in a builder file of an existing ring
            found = False
            for in_ring_device_info in rings.flat_device_list:
                if device_info.is_same_device(in_ring_device_info):
                    found = True
                    break

            # Attempt to get disk size information from the drive
            # configuration data
            hw_size, hw_fulldrive = drive_configurations.get_hw(
                device_info.server_name, device_info)

            if found:
                #
                # The device is already in the ring
                #

                #  Start by assuming no action needed
                device_info.presence = 'present'

                # What should the target weight be?
                if servers_model.server_draining(device_info.server_name):
                    # Draining -- should be 0
                    model_weight = '{:.2f}'.format(float(0.0))
                elif hw_size:
                    # Have drive size -- use drive size as target
                    model_weight = '{:.2f}'.format(
                        float(hw_size) / float(options.size_to_weight) or 1.0)
                else:
                    # Do not have size information for the drive. Lets assume
                    # the existing weight is ok
                    model_weight = '{:.2f}'.format(
                        float(in_ring_device_info.current_weight))

                # How much does model differ from current weight?
                current_weight = '{:.2f}'.format(
                    float(in_ring_device_info.current_weight))
                step = (options.weight_step or
                        control_plane_rings.get_ringspec(
                            ring_name).weight_step or
                        max(current_weight, model_weight))
                change = float(model_weight) - float(current_weight)
                if change > 0:
                    # Weight being changed upwards
                    target_weight = min(float(model_weight),
                                        float(current_weight) +
                                        float(step))
                    target_weight = '{:.2f}'.format(
                        float(target_weight))
                elif change < 0:
                    target_weight = max(float(model_weight),
                                        float(current_weight) -
                                        float(step))
                    target_weight = '{:.2f}'.format(
                        float(target_weight))
                else:
                    # Unchanged
                    target_weight = current_weight

                # Do we need to change the ring?
                if target_weight != current_weight:
                    # Yes -- ask for a weight change action
                    device_info.target_weight = target_weight
                    device_info.presence = 'set-weight'
                else:
                    # Unchanged
                    device_info.target_weight = current_weight
                device_info.model_weight = model_weight
                device_info.current_weight = current_weight

                # Is planned for removal?
                if servers_model.server_removing(device_info.server_name):
                    # Ask for device to be removed
                    device_info.presence = 'remove'
                    device_info.current_weight = current_weight
                    device_info.target_weight = '0.00'
                    device_info.model_weight = '0.00'

                # Check that model change did not attempt to change  zone, etc.
                changed_item = device_info.is_bad_change(in_ring_device_info)
                if changed_item:
                    model_errors.append('Model Mismatch:'
                                        ' Illegal change of %s for %s on'
                                        ' %s (%s)' % (changed_item,
                                                      device_info.device_name,
                                                      device_info.server_name,
                                                      device_info.server_ip))
            else:
                #
                # Device is not in the ring
                #
                if not control_plane_rings.get_ringspec(device_info.ring_name):
                    model_errors.append('Model Mismatch:'
                                        ' There is no specification for ring'
                                        ' %s. See disk model'
                                        ' for %s' % (device_info.ring_name,
                                                     device_info.server_name))
                    continue
                device_info.presence = 'add'
                if not hw_size:
                    model_errors.append('Model Mismatch:'
                                        ' Cannot find drive %s on'
                                        ' %s (%s)' % (device_info.device_name,
                                                      device_info.server_name,
                                                      device_info.server_ip))
                elif not hw_fulldrive and not options.allow_partitions:
                    model_errors.append('Model Mismatch:'
                                        ' Drive %s on %s (%s) has'
                                        ' several partitions' %
                                        (device_info.device_name,
                                         device_info.server_name,
                                         device_info.server_ip))
                else:
                    model_weight = '{:.2f}'.format(
                        float(hw_size) / float(options.size_to_weight) or 1.0)
                    weight_step = (options.weight_step or
                                   control_plane_rings.get_ringspec(
                                       device_info.ring_name).weight_step)
                    if weight_step:
                        if (float(model_weight) > float(weight_step)):
                            target_weight = '{:.2f}'.format(float(weight_step))
                        else:
                            target_weight = model_weight
                    else:
                        target_weight = model_weight
                    device_info.target_weight = target_weight
                    device_info.model_weight = model_weight
                    device_info.current_weight = '0.00'

                # However, do not add devices for a server marked for removal
                # or draining.
                if (servers_model.server_removing(device_info.server_name) or
                        servers_model.server_draining(
                            device_info.server_name)):
                    # Do not append to delta
                    continue

            delta.append_device(device_info)
        # end of looping though devices

    except SwiftModelException as err:
        model_errors.append(err)
    delta.sort()

    #
    # Run through all devices in builder files
    # If not in model anymore, mark device to be removed
    #
    for in_ring_device_info in rings.flat_device_list:
        found = False
        for device_info in servers_model.iter_devices():
            if device_info.is_same_device(in_ring_device_info):
                found = True
                break
        if not found:
            # Device is in the builder file, but has been removed from the
            # input model. Ask for device to be removed
            in_ring_device_info.presence = 'remove'
            delta.append_device(in_ring_device_info)

    if model_errors:
        for model_error in model_errors:
            print(model_error)
        raise SwiftModelException('There are errors or mismatches between'
                                  ' the input model and the configuration'
                                  ' of server(s).\n'
                                  ' Cannot proceed. Correct the errors'
                                  ' and try again')
    if model_warnings and options.stop_on_warnings:
        for model_warning in model_warnings:
            print(model_warning)
        raise SwiftModelException('There are minor mismatches between the'
                                  ' input model and the configuration of'
                                  ' servers. These are warning severity.'
                                  ' We recommend you correct the errors.')


def override_replica_count(ringspec, input_model,
                           model_errors, model_warnings):
    """
    The replica count cannot be greater than the number of devices

    This function works out a replica count of a ring if there are not
    enough devices. For replicated rings, we will warn the user (but build
    the ring anyway). For EC rings, we generate an error (which will stop
    the process). If the replica count is ok, we return None. We also
    return None for EC rings as the replica count is not directly
    settable.

    :param ringspec: the ring specification in the input model
    :param input_model: the input model
    :param model_errors: we append any errors here
    :param model_warnings: we append any warning here
    :return: the appropriate replica count or None if it should not be changed
    """
    replica_count = ringspec.replica_count
    ring_name = ringspec.name
    num_devices = input_model.get_num_devices(ring_name)
    if num_devices == 0:
        model_errors.append('There are no devices assigned to'
                            ' ring %s' % ring_name)
        return None
    if replica_count > num_devices:
        if ringspec.replication_policy:
            model_warnings.append('In ring %s there are not enough devices -- '
                                  ' changing the replica'
                                  ' count to %s' % (ring_name, num_devices))
            return num_devices
        else:
            model_errors.append('In ring %s there are not enough devices to'
                                ' support this number of data and parity'
                                ' fragments' % ring_name)
    # No change needed
    return None


def rebalance(delta, rings, options):
    """
    Run swift-ring-builder commands

    This function examines the ring delta and issues commands to create/add,
    modify or remove rings or devices. Finally, it executes a rebalance
    command.

    If the swift-ring-builder reports and error, we error-exit in this
    function (so that the playbook stops).

    :param delta: The ring delta
    :param rings: Existing rings (or placeholder if not already created)
    :param options: Options affecting this function (such as --dry-run)
    :return: Commands executed (unit tests emulate --dry-run)
    """

    if not delta.primary:
        if options.dry_run:
            print('Not primary site. No ring building occurs here')
        return

    for ring_name in delta.delta_rings.keys():
        if not os.path.isdir(rings.builder_dir):
            os.mkdir(rings.builder_dir)
    cmds = []
    for ring_name in delta.delta_rings.keys():
        if options.limit_ring and (options.limit_ring != ring_name):
            continue
        if 'add' in delta.delta_ring_actions.get(ring_name):
            ringspec = delta.delta_rings.get(ring_name)
            cmds.append(rings.command_ring_create(ringspec))
        if 'set-replica-count' in delta.delta_ring_actions.get(ring_name):
            ringspec = delta.delta_rings.get(ring_name)
            cmds.append(rings.command_set_replica_count(ringspec))
        if 'set-min-part-hours' in delta.delta_ring_actions.get(ring_name):
            ringspec = delta.delta_rings.get(ring_name)
            cmds.append(rings.command_set_min_part_hours(ringspec))

    for device_info in delta.delta_devices:
        ring_name = device_info.ring_name
        if options.limit_ring and (options.limit_ring != ring_name):
            continue
        if device_info.presence == 'add':
            cmds.append(rings.command_device_add(device_info))
        elif device_info.presence == 'remove':
            cmds.append(rings.command_device_remove(device_info))
        elif device_info.presence == 'set-weight':
            cmds.append(rings.command_device_set_weight(device_info))

    for ring_name in delta.delta_rings.keys():
        if options.limit_ring and (options.limit_ring != ring_name):
            continue
        ringspec = delta.delta_rings.get(ring_name)
        if 'add' not in delta.delta_ring_actions.get(ring_name):
            # pretend_min_part_hours can not be used on a newly created ring
            if options.pretend_min_part_hours_passed:
                cmds.append(rings.command_pretend_min_part_hours_passed(
                            ringspec))
        cmds.append(rings.command_rebalance(ringspec))

    if options.dry_run:
        for cmd in cmds:
            print('DRY-RUN: %s' % cmd)

    else:
        for cmd in cmds:
            print('Running: %s' % cmd)
            status, output = rings.run_cmd(cmd)
            if status > 0:
                sys.exit('ERROR: %s' % output)
            elif status < 0:
                print('NOTE: %s' % output)
    return cmds

if __name__ == '__main__':
    main()

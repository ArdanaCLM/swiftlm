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


import unittest
from yaml import safe_load
import os
import tempfile

from swiftlm.cli.supervisor import CloudMultiSite, generate_delta, rebalance
from swiftlm.rings.ring_model import RingSpecifications, \
    DriveConfiguration, DriveConfigurations, SwiftModelException
from swiftlm.rings.ardana_model import ServersModel
from swiftlm.rings.ring_builder import RingDelta, RingBuilder

from tests.data.ring_standard import standard_input_model, \
    standard_swf_rng_consumes, standard_drive_configurations, expected_cmds, \
    standard_configuration_data


class FakeRingBuilder(RingBuilder):

    def __init__(self, builder_dir, fake_rings, replica_count,
                 min_part_hours=24):
        super(FakeRingBuilder, self).__init__(builder_dir, False)
        for ring_name in fake_rings:
            self.register_ring(ring_name, replica_count,
                               balance=100, min_part_hours=min_part_hours)

    def load_fake_ring_data(self, delta):
        for device_info in delta.delta_devices:
            # Fake acts as through we made real ring match the target
            device_info.current_weight = device_info.target_weight
            # Builder file contains different data than input model.
            device_info.presence = 'present'
            device_info.balance = 0.0
            for key in ['server_groups', 'network_names', 'server_name',
                        'device_name', 'group_type', 'target_weight',
                        'model_weight', 'block_devices']:
                try:
                    del device_info[key]
                except KeyError:
                    pass
            self.flat_device_list.append(device_info)

    def fake_set_weights(self, new_weight):
        for device_info in self.flat_device_list:
            device_info.current_weight = new_weight

    def fake_set_replica_count(self, ring_name, replica_count):
        ringspec = self.get_ringspec(ring_name)
        ringspec['replication_policy']['replica_count'] = str(replica_count)


class DummyInputOptions(object):

    def __init__(self):
        self.unittest = True
        self.etc = tempfile.mkdtemp()
        self.size_to_weight = float(1024 * 1024 * 1024)
        self.allow_partitions = False
        self.stop_on_warnings = True
        self.weight_step = None
        self.dry_run = False
        self.limit_ring = None
        self.pretend_min_part_hours_passed = False
        self.cloud = 'standard'
        self.control_plane = 'ccp'


def dummy_osconfig_load(text):
    model = safe_load(text)
    drive_configurations = DriveConfigurations()
    for dc_model in model.get('ardana_drive_configuration'):
        drive_configuration = DriveConfiguration()
        drive_configuration.load_model(dc_model)
        drive_configurations.add(drive_configuration)
    return drive_configurations


def cmd_key(cmd):
    """ Sort key on builder file, then command, then args """
    verb, ringname, args = cmd
    return ringname + '.' + verb + '.' + '.'.join(args)


def cmd_parse(text):
    """ Get rid of spurious differences """
    if text == '':
        return None
    words = text.split()
    if len(words) == 0:
        return None
    ringname = os.path.basename(words[1])
    verb = words[2]
    args = words[3:]
    return (verb, ringname, args)


def assert_cmds_are_same(test_case, expected, actual):
    expected_args = []
    actual_args = []
    for cmd in expected:
        cmd_tuple = cmd_parse(cmd)
        if cmd_tuple:
            expected_args.append(cmd_tuple)

    for cmd in actual:
        cmd_tuple = cmd_parse(cmd)
        if cmd_tuple:
            actual_args.append(cmd_tuple)

    # test_case.maxDiff = None
    expected_args.sort(key=cmd_key)
    actual_args.sort(key=cmd_key)
    test_case.assertEquals(expected_args, actual_args)


def verb_ringname_args_in_cmds(verb, ringname, args, cmds):
    for cmd in cmds:
        cmdverb, cmdringname, cmdargs = cmd_parse(cmd)
        if cmdverb == verb and cmdringname == ringname:
            if not cmdargs:
                return True  # verb, ring match; don't care about args
            if cmdargs == args:
                return True  # verb, ring, args match
    return False


def cleanup(path):
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            cleanup(os.path.join(path, name))
        else:
            os.unlink(os.path.join(path, name))
    os.rmdir(path)


class TestPadawan(unittest.TestCase):

    def setUp(self):
        # Use to generate temporary name
        tf = tempfile.NamedTemporaryFile()
        self.builder_dir = os.path.basename(tf.name) + '-swiftlm-builder-dir'
        os.mkdir(self.builder_dir)

    def tearDown(self):
        cleanup(self.builder_dir)

    def test_build_rings(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        # Use rings from configuration-data object
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=None)
        ring_model.load_configuration('standard', 'ccp',
                                      safe_load(standard_configuration_data))
        rings = RingBuilder(self.builder_dir, False)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        # Validate pretend has no effect since all rings are new
        options.pretend_min_part_hours_passed = True
        cmds = rebalance(delta, rings, options)
        assert_cmds_are_same(self, expected_cmds, cmds)

    def test_build_limit_ring(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = RingBuilder(self.builder_dir, False)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        options.limit_ring = 'object-1'
        cmds = rebalance(delta, rings, options)
        self.assertEqual(len(cmds), 4)

    def test_change_replica_count_min_part_hours(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['container'], replica_count=4.0,
                                min_part_hours=6)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        # Fake container ring has replica-count of 4.0, check that we
        # change it to match the model (3.0)
        self.assertTrue(verb_ringname_args_in_cmds('set_replicas',
                                                   'container.builder',
                                                   ['3.0'], cmds))
        # Fake container ring has min-part-hours of 6, check that we
        # change it to match the model (24)
        self.assertTrue(verb_ringname_args_in_cmds('set_min_part_hours',
                                                   'container.builder',
                                                   ['24'], cmds))
        # Validate we don't attempt to re-create container
        self.assertTrue(not verb_ringname_args_in_cmds('create',
                                                       'container.builder',
                                                       None, cmds))
        # Validate other rings are created
        self.assertTrue(verb_ringname_args_in_cmds('create',
                                                   'account.builder',
                                                   ['17', '3.0', '24'], cmds))
        self.assertTrue(verb_ringname_args_in_cmds('create',
                                                   'object-0.builder',
                                                   ['17', '3.0', '24'], cmds))

    def test_noop(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0',
                                 'object-1'],
                                3.0)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        # Load the fake builder rings with the delta i.e., make it look as
        # though we had just done a rebalance() using input model
        rings.load_fake_ring_data(delta)

        # make a new delta and rebalance
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        # account, container, object-0:
        #     3 x rebalance (only) (which is point of this test)
        # object-1 has
        #     1 x set replica count
        #     1 x set min part hours
        #     2 x set weights
        #     1 x rebalance
        # total: 8
        self.assertTrue(len(cmds) == 8)

    def test_set_weight_no_step(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        # Load the fake builder rings with the delta i.e., make it look as
        # though we had just done a rebalance() using input model
        rings.load_fake_ring_data(delta)

        # Change the weights to a small value
        rings.fake_set_weights(1.0)

        # make a new delta and rebalance
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 18.63' in ' '.join(cmds))

    def test_set_weight_large_step(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        options.weight_step = 999999
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        # Load the fake builder rings with the delta i.e., make it look as
        # though we had just done a rebalance() using input model
        rings.load_fake_ring_data(delta)

        # Change the weights to a small value
        rings.fake_set_weights(1.0)

        # make a new delta and rebalance
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 18.63' in ' '.join(cmds))

    def test_set_weight_removing(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        # Load the fake builder rings with the delta i.e., make it look as
        # though we had just done a rebalance() using input model
        rings.load_fake_ring_data(delta)

        # Set standard-ccp-c1-m3 (92.168.245.2) to removing
        for server in input_model.servers:
            if server.get('ardana_ansible_host') == 'standard-ccp-c1-m3':
                server['pass_through'] = {'swift': {'remove': True}}
        self.assertTrue(input_model.server_removing('standard-ccp-c1-m3'))

        # make a new delta and rebalance
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  remove'
                        ' 192.168.245.2/disk0' in ' '.join(cmds))

    def test_set_weight_draining(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        options.weight_step = None
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        # Load the fake builder rings with the delta i.e., make it look as
        # though we had just done a rebalance() using input model
        rings.load_fake_ring_data(delta)

        # Set standard-ccp-c1-m3 (92.168.245.2) to draining
        for server in input_model.servers:
            if server.get('ardana_ansible_host') == 'standard-ccp-c1-m3':
                server['pass_through'] = {'swift': {'drain': True}}
        self.assertTrue(input_model.server_draining('standard-ccp-c1-m3'))

        # First cycle reduces weight
        options.weight_step = 1
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 17.63' in ' '.join(cmds))

        # Go through another cycle
        options.weight_step = None  # Weight can jump straight to zero
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 0.00' in ' '.join(cmds))

    def test_set_weight_with_step(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        # Load the fake builder rings with the delta i.e., make it look as
        # though we had just done a rebalance() using input model
        rings.load_fake_ring_data(delta)

        # Change the weights to a small value
        rings.fake_set_weights(1.0)

        # This make delta has a weight_step
        options.weight_step = '10.0'
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 11.00' in ' '.join(cmds))

        # Go through another cycle -- update as though last step built
        # the rings - use small step
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        rings.load_fake_ring_data(delta)
        options.weight_step = '1.0'
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 12.00' in ' '.join(cmds))

        # Go through another cycle -- the step is large enough that final
        # target weight is reached
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        rings.load_fake_ring_data(delta)
        options.weight_step = '10.0'
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 18.63' in ' '.join(cmds))

    def test_set_weight_down(self):

        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        # Load the fake builder rings with the delta i.e., make it look as
        # though we had just done a rebalance() using input model
        rings.load_fake_ring_data(delta)

        # Change the weights to a large value
        rings.fake_set_weights(30.0)

        # This make delta has a weight_step
        options.weight_step = '10.0'
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 20.00' in ' '.join(cmds))

        # Go through another cycle -- update as though last step built
        # the rings - use small step
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        rings.load_fake_ring_data(delta)
        options.weight_step = '1.0'
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 19.00' in ' '.join(cmds))

        # Go through another cycle -- the step is large enough that final
        # target weight is reached
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                3.0)
        rings.load_fake_ring_data(delta)
        options.weight_step = '10.0'
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder  set_weight'
                        ' 192.168.245.2/disk0 18.63' in ' '.join(cmds))

    def test_add_servers(self):
        # This test uses same process as test_build_rings() above -- so it
        # appears as though all servers are being added to an existing
        # system. With --weight-step=10, the resulting weights are limited
        # to 10.0
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        rings = RingBuilder(self.builder_dir, False)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        # Set limit to weight
        options.weight_step = '10'
        delta = RingDelta()
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('--device disk0'
                        ' --meta standard-ccp-c1-m3:disk0:/dev/sdc'
                        ' --weight 10.00' in ' '.join(cmds))
        self.assertTrue('--device lvm0 --meta'
                        ' standard-ccp-c1-m2:lvm0:/dev/ardana-vg/LV_SWFAC'
                        ' --weight 10.00' in ' '.join(cmds))

    def test_override_replica_count_on_install(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        num_devices = input_model.get_num_devices('account')
        # Change the model to have too high a replica count
        account_ring_model = ring_model.get_control_plane_rings(
            'standard', 'ccp').get_ringspec('account')
        account_ring_model['replication_policy']['replica_count'] = \
            num_devices + 1
        rings = RingBuilder(self.builder_dir, False)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        options.stop_on_warnings = False
        generate_delta(config_paths, input_model, ring_model, rings,
                       drive_configurations, options, delta)
        options.dry_run = True
        cmds = rebalance(delta, rings, options)
        self.assertTrue('account.builder'
                        ' create 17 %s 24' % float(num_devices) in
                        ' '.join(cmds))

    def test_override_replica_count_on_upgrade(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=safe_load(standard_input_model))
        num_devices = input_model.get_num_devices('account')
        # Change the model to have too high a replica count
        account_ring_model = ring_model.get_control_plane_rings(
            'standard', 'ccp').get_ringspec('account')
        account_ring_model['replication_policy']['replica_count'] = \
            num_devices + 1
        # The fake pre-mitaka rings also have a high replica count
        rings = FakeRingBuilder(self.builder_dir,
                                ['account', 'container', 'object-0'],
                                replica_count=num_devices + 1)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        try:
            # stop_on_warnings is True in unit tests
            generate_delta(config_paths, input_model, ring_model, rings,
                           drive_configurations, options, delta)
            self.assertTrue(False, msg='should not get here')
        except SwiftModelException:
            options.dry_run = True
            cmds = rebalance(delta, rings, options)
            self.assertTrue('account.builder'
                            ' set_replicas %s' % num_devices in
                            ' '.join(cmds))

    def test_missing_ring_specification(self):
        options = DummyInputOptions()
        config_paths = CloudMultiSite(options)
        input_model = ServersModel('standard', 'ccp',
                                   config=safe_load(standard_input_model),
                                   consumes_model=standard_swf_rng_consumes)
        # Change the disk model so a bad ring name is referenced
        for server in input_model.servers:
            disk_model = server.get('disk_model')
            for device_group in disk_model.get('device_groups', []):
                consumer = device_group.get('consumer')
                if consumer and consumer.get('name', 'other') == 'swift':
                    attrs = consumer.get('attrs')
                    attrs.get('rings').append({'name': 'object-99'})
        ring_model = RingSpecifications('standard', 'ccp',
                                        model=None)
        ring_model.load_configuration('standard', 'ccp',
                                      safe_load(standard_configuration_data))
        rings = RingBuilder(self.builder_dir, False)
        drive_configurations = dummy_osconfig_load(
            standard_drive_configurations)
        delta = RingDelta()
        try:
            generate_delta(config_paths, input_model, ring_model, rings,
                           drive_configurations, options, delta)
            self.assertTrue(False, msg='should not get here')
        except SwiftModelException as err:
            self.assertTrue('Cannot proceed' in str(err))

from copy import deepcopy
from unittest import (
    TestCase,
    mock)
from collections import (
    defaultdict,
    abc)

from ansitcontrib.vagrant import VagrantProvider
from ansit.drivers import ProviderError


class TestProvider(TestCase):

    class MockStdout(abc.Iterator):

        def __init__(self, ret):
            self._ret = ret

        def __next__(self):
            raise StopIteration()

        def __getattr__(self, key):
            return self

        def __call__(self):
            return self._ret

    SSH_CONFIG = {
       'default': {
            'address': '10.0.3.203',
                'user': 'vagrant',
                'port': 22,
                'private_key': '/home/jakub/dev/ansitcontrib-vagrant/tests/.vagrant/machines/default/lxc/private_key'
         }
    }

    @mock.patch('ansitcontrib.vagrant.VagrantProvider',
                autospec=True,
                instance=True)
    def test_ssh_config(self, provider):
        provider._ssh_config = defaultdict(dict)
        with open('tests/cfg', 'r') as src:
            VagrantProvider._parse_ssh_config(
                provider, src.read().splitlines())
            self.assertDictEqual(provider._ssh_config, self.SSH_CONFIG)

    @mock.patch('ansitcontrib.vagrant.VagrantProvider',
                autospec=True,
                instance=True)
    @mock.patch('paramiko.SSHClient.exec_command', autospec=True)
    @mock.patch('paramiko.SSHClient.connect', autospec=True)
    def test_successful_run(self, connect, exec_command, provider):
        exec_command.return_value = None, self.MockStdout(0), None
        provider._ssh_config = deepcopy(self.SSH_CONFIG)
        list(VagrantProvider.run(provider, 'default', 'pwd'))
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(exec_command.call_count, 1)
        self.assertEqual(exec_command.call_args[0][1], 'pwd')

    @mock.patch('ansitcontrib.vagrant.VagrantProvider',
                autospec=True,
                instance=True)
    @mock.patch('paramiko.SSHClient.exec_command', autospec=True)
    @mock.patch('paramiko.SSHClient.connect', autospec=True)
    def test_failed_run(self, connect, exec_command, provider):
        exec_command.return_value = None, self.MockStdout(1), None
        provider._ssh_config = deepcopy(self.SSH_CONFIG)
        try:
            list(VagrantProvider.run(provider, 'default', 'pwd'))
        except ProviderError as e:
            error = e


class TestVagrantInteraction(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.provider = VagrantProvider(
            'tests',
            {
                'test1': {
                    'driver': 'ansitcontrib.vagrant.VagrantProvider',
                },
                'test2': {
                    'driver': 'ansitcontrib.vagrant.VagrantProvider'
                }
            })
        list(cls.provider.up(['test1', 'test2']))

    @classmethod
    def tearDownClass(cls):
        list(cls.provider.destroy(['test1', 'test2']))

    def test_run(self):
        stdout = list(self.provider.run('test1', 'pwd'))
        self.assertEqual(stdout[0].rstrip(), '/home/vagrant')


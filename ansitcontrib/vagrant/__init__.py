import subprocess
import sys
import logging
import shutil
import shlex
from collections import defaultdict

import paramiko

from ansit.drivers import (
    Provider,
    ProviderError)


class KeyPolicy(paramiko.MissingHostKeyPolicy):

    def missing_host_key(*args, **kwargs):
        return


class VagrantProvider(Provider):

    def __init__(self, directory, machines):
        self._directory = directory
        self._machines = machines
        self._ssh_config = defaultdict(dict)
        self._vagrant = shutil.which('vagrant')
        if self._vagrant is None:
            raise ProviderError('vagrant executable not found')
        paramiko_logger = logging.getLogger('paramiko')
        paramiko_logger.setLevel(
            min(paramiko_logger.getEffectiveLevel() + 10, 50))

    def up(self, machines):
        cmd = [self._vagrant, 'up']
        cmd.extend(machines)
        for line in self._run_command(cmd):
            yield line
        cmd[1] = 'ssh-config'
        self._update_ssh_config(machines)

    def run(self, machine, cmd):
        cfg = self.ssh_config(machine)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(KeyPolicy)
        client.connect(
            cfg['address'],
            port=cfg['port'],
            username=cfg['user'],
            key_filename=cfg['private_key'])
        get_pty = False
        if sys.stdout.isatty():
            get_pty = True
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=get_pty)
        for line in stdout:
            yield line
        returncode = stdout.channel.recv_exit_status()
        if returncode != 0:
            raise ProviderError('Command \'%s\' returned code %s' % (
                cmd, returncode))

    def destroy(self, machines):
        cmd = [self._vagrant, 'destroy', '--force']
        cmd.extend(machines)
        for line in self._run_command(cmd):
            yield line

    def ssh_config(self, machine):
        if machine not in self._ssh_config.keys():
            self._update_ssh_config([machine])
        return self._ssh_config[machine]

    def _update_ssh_config(self, machines):
        cmd = [self._vagrant, 'ssh-config']
        cmd.extend(machines)
        self._parse_ssh_config(self._run_command(cmd))

    def _parse_ssh_config(self, lines):
        for line in lines:
            line = line.rstrip()
            if len(line) == 0:
                continue
            key, value = line.split(maxsplit=2)
            key = key.lower()
            if key == 'host':
                host = value
            elif key == 'hostname':
                self._ssh_config[host]['address'] = value
            elif key == 'user':
                self._ssh_config[host]['user'] = value
            elif key == 'port':
                self._ssh_config[host]['port'] = int(value)
            elif key == 'identityfile':
                self._ssh_config[host]['private_key'] = value

    def _run_command(self, cmd):
        process = subprocess.Popen(
            cmd,
            bufsize=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        for line in process.stdout:
            yield line
        process.communicate()
        if process.returncode != 0:
            raise ProviderError('Command %s returned code %s' % (
                cmd, str(process.returncode)))

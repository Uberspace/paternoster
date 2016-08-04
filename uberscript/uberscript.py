from __future__ import print_function

import argparse
import sys
import os
import os.path
import json
import re
from collections import namedtuple

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.plugins.callback import CallbackBase
import ansible.constants


class MinimalAnsibleCallback(CallbackBase):
  """ filters out all ansible messages except for playbook fails and debug-module-calls. """

  def v2_runner_on_failed(self, result, ignore_errors=False):
    msg = result._result.get('msg', None)
    if msg:
      print(msg, file=sys.stderr)

  def v2_runner_on_ok(self, result):
    result = result._result
    args = result['invocation']['module_args']
    if result['invocation']['module_name'] == 'debug':
      if 'var' in args:
        print(result[args['var']])
      if 'msg' in args:
        print(args['msg'])


class UberScript:

  def __init__(self, playbook, parameters, success_msg='executed successfully'):
    self.playbook = playbook
    self.parameters = parameters
    self.success_msg = success_msg
    self._sudouser = None

  def _find_param(self, fname):
    for name, short, param in self.parameters:
      if name == fname or short == fname:
        return (name, short, param)

  def _build_argparser(self):
    parser = argparse.ArgumentParser(add_help=False)
    requiredArgs = parser.add_argument_group('required arguments')
    optionalArgs = parser.add_argument_group('optional arguments')

    optionalArgs.add_argument(
      '-h', '--help', action='help', default=argparse.SUPPRESS,
      help='show this help message and exit'
    )

    for name, short, param in self.parameters:
      argParams = param.copy()
      argParams.pop('depends', None)

      if param.get('required', False):
        requiredArgs.add_argument('-' + short, '--' + name, **argParams)
      else:
        optionalArgs.add_argument('-' + short, '--' + name, **argParams)

    optionalArgs.add_argument(
      '-v', '--verbose', action='store_true',
      help='run with a lot of debugging output'
    )

    return parser

  def _check_arg_dependencies(self, parser, args):
    for name, short, param in self.parameters:
      if 'depends' in param and getattr(args, name, None) and not getattr(args, param['depends'], None):
        parser.error(
          'argument --{} (-{}) requires --{} (-{}) to be present.'.format(
            name, short, param['depends'], self._find_param(param['depends'])[1]
          )
        )

  def auto(self, root=True):
    if root:
      self.become_root()
    self.parse_args()
    self.execute_playbook()

  def become_root(self):
    if os.geteuid() != 0:
      # -n disables password prompt, when sudo isn't configured properly
      os.execvp('sudo', ['sudo', '-n', '--'] + sys.argv)
    else:
      sudouser = os.environ.get('SUDO_USER', None)
      if sudouser and re.match('[a-z][a-z0-9]{0,20}', sudouser):
        self._sudouser = sudouser
      else:
        print('invalid username', file=sys.stderr)
        sys.exit(1)

  def parse_args(self, args=None):
    parser = self._build_argparser()

    args = parser.parse_args(args)
    self._check_arg_dependencies(parser, args)

    self._parsed_args = args

  def _get_playbook_variables(self):
    if self._sudouser:
      yield ('sudouser', self._sudouser)
    yield ('scriptname', os.path.basename(sys.argv[0]))
    for name in vars(self._parsed_args):
      yield ('param_' + name, getattr(self._parsed_args, name))

  def _check_playbook(self):
    if not self.playbook:
      raise ValueError('no playbook given')
    if not os.path.isabs(self.playbook):
      raise ValueError('path to playbook must be absolute')
    if not os.path.isfile(self.playbook):
      raise ValueError('playbook must exist and must not be a link')

  def _get_playbook_executor(self):
    Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'listhosts', 'listtasks', 'listtags', 'syntax'])

    variable_manager = VariableManager()
    loader = DataLoader()
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=['localhost'])
    variable_manager.set_inventory(inventory)
    variable_manager.set_host_variable(inventory.localhost, 'ansible_python_interpreter', sys.executable)

    for name, value in self._get_playbook_variables():
      variable_manager.set_host_variable(inventory.localhost, name, value)

    pexec = PlaybookExecutor(
      playbooks=[self.playbook],
      inventory=inventory,
      variable_manager=variable_manager,
      loader=loader,
      options=Options(
        connection='local',
        module_path=None,
        forks=100,
        listhosts=False, listtasks=False, listtags=False, syntax=False,
        become=None, become_method=None, become_user=None, check=False
      ),
      passwords={},
    )

    ansible.constants.RETRY_FILES_ENABLED = False

    if not self._parsed_args.verbose:
      # ansible doesn't provide a proper API to overwrite this,
      # if you're using PlaybookExecutor instead of initializing
      # the TaskQueueManager (_tqm) yourself, like in the offical
      # example.
      pexec._tqm._stdout_callback = MinimalAnsibleCallback()

    return pexec

  def execute_playbook(self):
    self._check_playbook()
    status = self._get_playbook_executor().run()
    if status == 0:
      print(self.success_msg)
      return True
    else:
      return False

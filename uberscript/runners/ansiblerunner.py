from __future__ import print_function

import sys
from collections import namedtuple

import ansible.constants
import os.path
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.callback import CallbackBase
from ansible.vars import VariableManager


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


class AnsibleRunner:
  def __init__(self, playbook):
    self._playbook = playbook

  def _get_playbook_executor(self, variables, verbose):
    Options = namedtuple('Options',
                         ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check',
                          'listhosts', 'listtasks', 'listtags', 'syntax'])

    variable_manager = VariableManager()
    loader = DataLoader()
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=['localhost'])
    variable_manager.set_inventory(inventory)
    # force ansible to use the current python executable. Otherwise
    # it can end up choosing a python3 one (named python) or a different
    # python 2 version
    variable_manager.set_host_variable(inventory.localhost, 'ansible_python_interpreter', sys.executable)

    for name, value in variables:
      variable_manager.set_host_variable(inventory.localhost, name, value)

    pexec = PlaybookExecutor(
      playbooks=[self._playbook],
      inventory=inventory,
      variable_manager=variable_manager,
      loader=loader,
      options=Options(
        connection='local',
        module_path=None,
        forks=1,
        listhosts=False, listtasks=False, listtags=False, syntax=False,
        become=None, become_method=None, become_user=None, check=False
      ),
      passwords={},
    )

    ansible.constants.RETRY_FILES_ENABLED = False

    if not verbose:
      # ansible doesn't provide a proper API to overwrite this,
      # if you're using PlaybookExecutor instead of initializing
      # the TaskQueueManager (_tqm) yourself, like in the offical
      # example.
      pexec._tqm._stdout_callback = MinimalAnsibleCallback()

    return pexec

  def _check_playbook(self):
    if not self._playbook:
      raise ValueError('no playbook given')
    if not os.path.isabs(self._playbook):
      raise ValueError('path to playbook must be absolute')
    if not os.path.isfile(self._playbook):
      raise ValueError('playbook must exist and must not be a link')

  def run(self, variables, verbose):
    self._check_playbook()
    status = self._get_playbook_executor(variables, verbose).run()
    return True if status == 0 else False

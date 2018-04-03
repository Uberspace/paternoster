from __future__ import print_function

import sys
import os
import os.path
from collections import namedtuple
from distutils.version import LooseVersion

# Ansible loads the ansible.cfg in the following order. Each ansible.cfg
# automatically overwrites all values of the former ones.
#
#  1. Path given in $ANSIBLE_CONFIG
#  2. ansible.cfg file in the current directory
#  3. .ansible.cfg file in the home directory
#  4. /etc/ansible/ansible.cfg
#
# Since the current directory is controlled by the user and we don't
# want them to be able to load their own config and thus their own
# ansible modules, we need to counter them by setting the env-variable.
os.environ['ANSIBLE_CONFIG'] = '/etc/ansible/ansible.cfg'

# by default ansible uses "$HOME/.ansible/tmp" as the directory to drop
# its module files. For some reason $HOME is not resolved when using the
# python API directly resuling in a new directory called '$HOME' within
# the paternoster source. This forces the modules to be dropped in /tmp.
os.environ['ANSIBLE_REMOTE_TEMP'] = '/tmp'
os.environ['ANSIBLE_LOCAL_TEMP'] = '/tmp'

# Verbosity within ansbible is controlled by the Display-class. Each and
# every ansible-file creates their own instance of this class, like this:
#
#  try:
#     from __main__ import display
#   except ImportError:
#     from ansible.utils.display import Display
#     display = Display()
#
# This means that the verbosity-parameter of display _always_ default to
# zero. There is no sane way to overwrite this. Within a normal ansible
# setup __main__ corresponds to the current executable (e.g. "ansible-playbook"),
# which creates a Display instance based on the cli parameters (-v, -vv, ...).
#
# This has to happen before anything from ansible is imported!
import __main__
from ansible.utils.display import Display

__main__.display = Display()

import ansible.constants
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.callback import CallbackBase
import ansible.release

ANSIBLE_VERSION = LooseVersion(ansible.release.__version__)

if ANSIBLE_VERSION < LooseVersion('2.4.0'):
    from ansible.inventory import Inventory
    from ansible.vars import VariableManager
else:
    from ansible.inventory.manager import InventoryManager
    from ansible.vars.manager import VariableManager


class MinimalAnsibleCallback(CallbackBase):
    """ filters out all ansible messages except for playbook fails and debug-module-calls. """

    def v2_runner_on_failed(self, result, ignore_errors=False):
        msg = result._result.get('msg')
        taks_ignores_errors = getattr(result, '_task_fields', {}).get('ignore_errors', False)
        if (
            not ignore_errors and not taks_ignores_errors
            and msg is not None and msg != 'All items completed'
        ):
            print(msg, file=sys.stderr)

    def v2_runner_item_on_ok(self, result):
        self.v2_runner_on_ok(result)

    def v2_runner_item_on_failed(self, result):
        self.v2_runner_on_failed(result)

    def _get_action_args(self, result):
        if ANSIBLE_VERSION < LooseVersion('2.3'):
            result = result._result
            if 'invocation' in result:
                action = result['invocation'].get('module_name', None)
                args = result['invocation'].get('module_args', None)
            else:
                action = None
                args = {}

            isloop = False
        else:
            action = result._task_fields.get('action', None)
            args = result._task_fields.get('args', {})
            isloop = 'results' in result._result

        return (action, args, isloop)

    def v2_runner_on_ok(self, result):
        action, args, isloop = self._get_action_args(result)

        if isloop:
            # ansible 2.2+ calls runner_on_ok after all items have passed
            # older versions don't.
            return

        if action == 'debug':
            if 'var' in args:
                print(result._result[args['var']])
            if 'msg' in args:
                print(result._result['msg'])


class AnsibleRunner:
    def __init__(self, playbook):
        self._playbook = playbook

    def _get_playbook_executor(self, variables, verbosity):
        Options = namedtuple('Options',
                             ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check',
                              'listhosts', 'listtasks', 'listtags', 'syntax', 'diff'])

        # -v given to us enables ansibles non-debug output.
        # So -vv should become ansibles -v.
        __main__.display.verbosity = max(0, verbosity - 1)

        # make sure ansible does not output warnings for our paternoster pseudo-play
        __main__._real_warning = __main__.display.warning

        def display_warning(msg, *args, **kwargs):
            if not msg.startswith('Could not match supplied host pattern'):
                __main__._real_warning(msg, *args, **kwargs)
        __main__.display.warning = display_warning

        loader = DataLoader()
        if ANSIBLE_VERSION < LooseVersion('2.4.0'):
            from ansible.inventory import Inventory
            variable_manager = VariableManager()
            inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list='localhost,')
            variable_manager.set_inventory(inventory)
        else:
            from ansible.inventory.manager import InventoryManager
            inventory = InventoryManager(loader=loader, sources='localhost,')
            variable_manager = VariableManager(loader=loader, inventory=inventory)
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
                become=None, become_method=None, become_user=None, check=False,
                diff=False,
            ),
            passwords={},
        )

        ansible.constants.RETRY_FILES_ENABLED = False

        if not verbosity:
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
            raise ValueError('playbook must exist')

    def run(self, variables, verbosity):
        self._check_playbook()
        os.chdir(os.path.dirname(self._playbook))
        status = self._get_playbook_executor(variables, verbosity).run()
        return True if status == 0 else False

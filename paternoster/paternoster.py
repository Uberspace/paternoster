from __future__ import print_function
from __future__ import absolute_import

import argparse
import sys
import os.path
import inspect

import six

from .runners.ansiblerunner import AnsibleRunner
from .root import become_user, check_user
import paternoster.types


class Paternoster:
    def __init__(self,
                 runner_parameters,
                 parameters,
                 become_user=None, check_user=None,
                 success_msg=None,
                 runner_class=AnsibleRunner,
                 ):
        self._parameters = parameters
        self._become_user = become_user
        self._check_user = check_user
        self._success_msg = success_msg
        self._sudo_user = None
        self._runner = runner_class(**runner_parameters)

    def _find_param(self, fname):
        """ look for a parameter by either its short- or long-name """
        for param in self._parameters:
            if param['name'] == fname or param.get('short', None) == fname:
                return param

        raise KeyError('Parameter {0} could not be found'.format(fname))

    def _check_type(self, argParams):
        """ assert that an argument does not use a string type opposed to an restricted_str, else raise a ValueError """
        action_whitelist = ('store_true', 'store_false', 'store_const', 'append_const', 'count')
        action = argParams.get('action', 'store')

        if 'type' not in argParams and action not in action_whitelist:
            raise ValueError('a type must be specified for each user-supplied argument')

        type = argParams.get('type', str)
        is_str_type = inspect.isclass(type) and issubclass(type, six.string_types)

        if is_str_type and action not in action_whitelist:
            raise ValueError('restricted_str instead of str or unicode must be used for all string arguments')

    def _convert_type(sefl, argParams):
        param_type = argParams.pop('type', None)
        param_type_params = argParams.pop('type_params', {})

        if isinstance(param_type, str):
            if param_type == 'int':
                argParams['type'] = int
            elif param_type == 'str':
                argParams['type'] = str
            elif param_type.startswith('paternoster.types.'):
                type_clazz = getattr(sys.modules['paternoster.types'], param_type.rpartition('.')[2])
                argParams['type'] = type_clazz(**param_type_params)
            else:
                raise Exception('unknown type ' + param_type)
        elif param_type:
            argParams['type'] = param_type

    def _build_argparser(self):
        parser = argparse.ArgumentParser(add_help=False)
        requiredArgs = parser.add_argument_group('required arguments')
        optionalArgs = parser.add_argument_group('optional arguments')

        optionalArgs.add_argument(
            '-h', '--help', action='help', default=argparse.SUPPRESS,
            help='show this help message and exit'
        )

        for param in self._parameters:
            argParams = param.copy()
            argParams.pop('depends_on', None)
            argParams.pop('positional', None)
            argParams.pop('short', None)
            argParams.pop('name', None)

            self._convert_type(argParams)
            self._check_type(argParams)

            if param.get('positional', False):
                paramName = [param['name']]
            else:
                paramName = ['-' + param['short'], '--' + param['name']]

            if param.get('required', False) or param.get('positional', False):
                requiredArgs.add_argument(*paramName, **argParams)
            else:
                optionalArgs.add_argument(*paramName, **argParams)

        optionalArgs.add_argument(
            '-v', '--verbose', action='count', default=0,
            help='run with a lot of debugging output'
        )

        return parser

    def _check_arg_dependencies(self, parser, args):
        for param in self._parameters:
            param_given = getattr(args, param['name'], None)
            dependency_given = 'depends_on' not in param or getattr(args, param['depends_on'], None)

            if param_given and not dependency_given:
                parser.error(
                    'argument --{} requires --{} to be present.'.format(param['name'], param['depends_on'])
                )

    def check_user(self):
        if not self._check_user:
            return
        if not check_user(self._check_user):
            print('This script can only be used by the user ' + self._check_user, file=sys.stderr)
            sys.exit(1)

    def become_user(self):
        if not self._become_user:
            return

        try:
            self._sudo_user = become_user(self._become_user)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    def auto(self):
        self.check_user()
        self.become_user()
        self.parse_args()
        status = self.execute()
        sys.exit(0 if status else 1)

    def parse_args(self, args=None):
        parser = self._build_argparser()

        args = parser.parse_args(args)
        self._check_arg_dependencies(parser, args)

        self._parsed_args = args

    def _get_runner_variables(self):
        if self._sudo_user:
            yield ('sudo_user', self._sudo_user)

        yield ('script_name', os.path.basename(sys.argv[0]))

        for name in vars(self._parsed_args):
            yield ('param_' + name, getattr(self._parsed_args, name))

    def execute(self):
        status = self._runner.run(self._get_runner_variables(), self._parsed_args.verbose)
        if status and self._success_msg:
            print(self._success_msg)
        return status

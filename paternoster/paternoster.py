from __future__ import absolute_import
from __future__ import print_function

import argparse
import getpass
import inspect
import os.path
import sys

import six

from .runners.ansiblerunner import AnsibleRunner
from .root import become_user, check_user
import paternoster.types


class Paternoster:
    def __init__(self,
                 runner_parameters,
                 parameters=None,
                 mutually_exclusive=None,
                 required_one_of=None,
                 become_user=None, check_user=None,
                 success_msg=None,
                 description=None,
                 runner_class=AnsibleRunner,
                 ):
        if parameters is None:
            self._parameters = []
        else:
            self._parameters = parameters
        self._mutually_exclusive = mutually_exclusive or []
        self._required_one_of = required_one_of or []
        self._become_user = become_user
        self._check_user = check_user
        self._success_msg = success_msg
        self._description = description
        self._sudo_user = None
        self._runner = runner_class(**runner_parameters)

    def _find_param(self, fname):
        """ look for a parameter by either its short- or long-name """
        for param in self._parameters:
            if param['name'] == fname or param.get('short', None) == fname:
                return param

        raise KeyError('Parameter {0} could not be found'.format(fname))

    def _get_param_val(self, args, fname):
        """ get the value of a parameter, named by either its short- or long-name """
        param = self._find_param(fname)
        name = param['name'].replace('-', '_')
        return getattr(args, name)

    def _check_type(self, argParams):
        """ assert that given argument uses restricted_str in place of str/unicode, else raise ValueError """
        action_whitelist = ('store_true', 'store_false', 'store_const', 'append_const', 'count')
        action = argParams.get('action', 'store')

        has_choices = ('choices' in argParams)
        is_whitelist_action = (action in action_whitelist)

        if is_whitelist_action:  # the passed value is hardcoded by the dev
            return
        if has_choices:  # there is a whitelist of valid values
            return

        argtype = argParams.get('type', str)
        has_type = ('type' in argParams)
        is_raw_string = (inspect.isclass(argtype) and issubclass(argtype, six.string_types))

        if not has_type:
            raise ValueError('a type must be specified for each user-supplied argument')
        if is_raw_string:
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
        parser = argparse.ArgumentParser(
            add_help=False,
            description=self._description,
        )
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
            argParams.pop('prompt', None)
            argParams.pop('prompt_options', None)

            # remove dest here so the actual argument names are preserved
            argParams.pop('dest', None)

            self._convert_type(argParams)
            self._check_type(argParams)

            if 'name' not in param:
                raise Exception('Parameter without name given: {}'.format(param))

            if param.get('positional', False):
                paramName = [param['name']]
            else:
                if 'short' in param:
                    paramName = ['-' + param['short'], '--' + param['name']]
                else:
                    paramName = ['--' + param['name']]

            if param.get('required', False) or param.get('positional', False):
                if param.get('prompt'):
                    parser.error((
                        "'--{}' is required and can't be combined with prompt"
                    ).format(
                        param['name'],
                    ))
                requiredArgs.add_argument(*paramName, **argParams)
            else:
                optionalArgs.add_argument(*paramName, **argParams)

        optionalArgs.add_argument(
            '-v', '--verbose', action='count', default=0,
            help='run with a lot of debugging output'
        )

        return parser

    def _prompt_for_missing(self, argv, parser, args):
        """
        Return *args* after prompting the user for missing arguments.

        Prompts the user for arguments (`self._parameters`), that are missing
        from *args* (don't exist or are set to `None`). But only if they have
        the `prompt` key set to `True` or a non empty string.

        """
        # get parameter dictionaries for missing arguments
        missing_params = (
            param for param in self._parameters
            if param.get('prompt')
            and isinstance(param.get('prompt'), (bool, six.string_types))
            and self._get_param_val(args, param['name']) is None
        )

        # prompt for missing args
        prompt_data = {
            param['name']: self.get_input(param) for param in missing_params
        }

        # add prompt_data to new argv and return newly parsed arguments
        if prompt_data:
            argv = list(argv) if argv else sys.argv[1:]
            for name, value in prompt_data.items():
                argv.append('--{}'.format(name))
                argv.append(value)
            return parser.parse_args(argv)

        # return already parsed arguments
        else:
            return args

    def _argument_given(self, args, name):
        param = self._find_param(name)
        return self._get_param_val(args, param['name'])

    def _check_arg_dependencies(self, parser, args):
        for param in self._parameters:
            param_given = self._argument_given(args, param['name'])
            dependency_given = ('depends_on' not in param) or self._argument_given(args, param['depends_on'])

            if param_given and not dependency_given:
                parser.error(
                    'argument --{} requires --{} to be present.'.format(param['name'], param['depends_on'])
                )

    def _check_arg_mutually_exclusive(self, parser, args):
        for group in self._mutually_exclusive:
            given_args = ['--' + a for a in group if self._argument_given(args, a)]

            if len(given_args) > 1:
                parser.error(
                    'arguments {} are mutually exclusive.'.format(', '.join(given_args))
                )

    def _check_arg_required_one_of(self, parser, args):
        for group in self._required_one_of:
            given_args = [True for a in group if self._argument_given(args, a)]

            if len(given_args) == 0:
                parser.error(
                    'at least one of {} is needed.'.format(', '.join('--' + x for x in group))
                )

    def _apply_dest(self, args):
        """
        The dest attribute is removed earlier so the actual argument names are preserved for dependency checking.
        This renames all the arguments to their "dest" name, or leaves them as-is, if non is given.
        """

        for param in self._parameters:
            if not param.get('dest'):
                continue

            name = param['name']
            dest = param['dest']
            value = self._get_param_val(args, name)

            if value is not None or not hasattr(args, dest):
                setattr(args, dest, value)
                delattr(args, name)

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

    def parse_args(self, argv=None):
        parser = self._build_argparser()
        try:
            args = parser.parse_args(argv)
            args = self._prompt_for_missing(argv, parser, args)
            self._check_arg_dependencies(parser, args)
            self._check_arg_mutually_exclusive(parser, args)
            self._check_arg_required_one_of(parser, args)
            self._apply_dest(args)
            self._parsed_args = args
        except ValueError as exc:
            print(exc, file=sys.stderr)
            sys.exit(3)

    def _get_runner_variables(self):
        if self._sudo_user:
            yield ('sudo_user', self._sudo_user)

        yield ('script_name', os.path.basename(sys.argv[0]))

        for name in vars(self._parsed_args):
            value = getattr(self._parsed_args, name)
            if six.PY2 and isinstance(value, str):
                value = value.decode('utf-8')
            yield ('param_' + name, value)

    def execute(self):
        status = self._runner.run(self._get_runner_variables(), self._parsed_args.verbose)
        if status and self._success_msg:
            print(self._success_msg)
        return status

    @staticmethod
    def prompt(text, no_echo=False):
        """
        Return user input from a prompt with *text*.

        If *no_echo* is set, :func:`getpass.getpass` is used to prevent echoing
        of the user input. Exits gracefully on keyboard interrupts (with return
        code 3).

        """
        try:
            if no_echo:
                user_input = getpass.getpass(text)
            else:
                try:
                    user_input = raw_input(text)  # Python 2
                except NameError:
                    user_input = input(text)  # Python 3
            return user_input
        except KeyboardInterrupt:
            sys.exit(3)

    @staticmethod
    def get_input(param):
        """
        Return user input for *param*.

        The `param['name']` item needs to be set. The text for the prompt is
        taken from `param['prompt']`, if available and a non empty string.
        Otherwise `param['name']` is used. Also you can set additional
        arguments in `param['prompt_options']`:

        :accept_empty: if `True`: allows empty input
        :confirm: if `True` or string: prompt user for confirmation
        :confirm_error: if string: used as confirmation error message
        :no_echo: if `True`: don't echo the user input on the screen
        :strip: if `True`: strips user input

        Raises:
            KeyError: if no `name` item is set for *param*.
            ValueError: if input and confirmation do not match.

        """
        name = param['name']
        prompt = param.get('prompt')
        options = param.get('prompt_options', {})
        confirmation_prompt = options.get('confirm')
        accept_empty = options.get('accept_empty')
        no_echo = options.get('no_echo')
        strip = options.get('strip')

        # set prompt
        if not isinstance(prompt, six.string_types):
            prompt = '{}: '.format(name.title())

        # set confirmation prompt
        ask_confirmation = (
            confirmation_prompt
            and isinstance(confirmation_prompt, (bool, six.string_types))
        )
        if not isinstance(confirmation_prompt, six.string_types):
            confirmation_prompt = 'Please confirm: '

        # get input
        while True:
            value = Paternoster.prompt(prompt, no_echo)
            if strip:
                value = value.strip()
            if value or accept_empty:
                break

        # confirm
        if ask_confirmation:
            confirmed_value = Paternoster.prompt(confirmation_prompt, no_echo)
            if value != confirmed_value:
                confirm_error = (
                    options.get('confirm_error')
                    or 'ERROR: input does not match its confirmation'
                )
                raise ValueError(confirm_error)

        return value

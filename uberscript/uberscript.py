from __future__ import print_function

import argparse
import sys
import os.path

from .runners.ansiblerunner import AnsibleRunner
from .become_root import become_root


class UberScript:
  def __init__(self, runner_parameters, parameters, success_msg='executed successfully', runner_class=AnsibleRunner):
    self.parameters = parameters
    self.success_msg = success_msg
    self._sudo_user = None
    self._runner = runner_class(**runner_parameters)

  def _find_param(self, fname):
    """ look for a parameter by either its short- or long-name """
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

      if ('type' not in argParams or argParams['type'] in (str, unicode)) and \
          argParams.get('action', 'store') not in ('store_true', 'store_false', 'store_const', 'append_const', 'count'):
        raise ValueError('restricted_str must be used for all string arguments')

      if param.get('required', False):
        requiredArgs.add_argument('-' + short, '--' + name, **argParams)
      else:
        optionalArgs.add_argument('-' + short, '--' + name, **argParams)

    optionalArgs.add_argument(
      '-v', '--verbose', action='count', default=0,
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
      try:
        self._sudo_user = become_root()
      except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
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
    if status:
      print(self.success_msg)
    return status

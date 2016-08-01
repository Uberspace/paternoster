import argparse
import sys


class UberScript:

  def __init__(self, playbook, parameters):
    self.playbook = playbook
    self.parameters = parameters
  
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

    return parser

  def _check_arg_dependencies(self, parser, args):
    for name, short, param in self.parameters:
      if 'depends' in param and getattr(args, name, None) and not getattr(args, param['depends'], None):
        parser.error(
          'argument --{} (-{}) requires --{} (-{}) to be present.'.format(
            name, short, param['depends'], self._find_param(param['depends'])[1]
          )
        )

  def parse_args(self):
    parser = self._build_argparser()

    args = parser.parse_args()
    self._check_arg_dependencies(parser, args)

    self.args = args

  def execute_playbook(self):
    pass

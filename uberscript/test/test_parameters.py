import pytest

from .. import UberScript, types


@pytest.mark.parametrize("args,valid", [
  ([], True),
  (['-m'], True),
  (['-e', 'aa'], False),
  (['-m', '-e', 'aa'], True),
  (['-m', '--namespace', 'aa'], True),
  (['--mailserver', '-e', 'aa'], True),
  (['--namespace', 'a', '--mailserver'], True),
])
def test_parameter_depends(args, valid):
  s = UberScript(
    playbook='add_domain.yml',
    parameters=[
      ('mailserver', 'm', {
        'help': '', 'action': 'store_true'
      }),
      ('namespace', 'e', {
        'help': '', 'type': types.restricted_str('a'), 'depends': 'mailserver',
      }),
    ],
  )

  if not valid:
    with pytest.raises(SystemExit):
      s.parse_args(args)
  else:
    s.parse_args(args)


@pytest.mark.parametrize("param,valid", [
  ({}, False),
  ({'type': str}, False),
  ({'type': unicode}, False),
  ({'type': types.restricted_str('a')}, True),
  ({'action': 'store_true'}, True),
  ({'action': 'store_false'}, True),
  ({'action': 'store_const', 'const': 5}, True),
  ({'action': 'append'}, False),
  ({'action': 'append', 'type': str}, False),
  ({'action': 'append', 'type': types.restricted_str('a')}, True),
  ({'action': 'append_const', 'const': 5}, True),
])
def test_forced_restricted_str(param, valid):
  s = UberScript(
    playbook='add_domain.yml',
    parameters=[
      ('namespace', 'e', param),
    ],
  )

  if not valid:
    with pytest.raises(ValueError):
      s.parse_args([])
  else:
    s.parse_args([])

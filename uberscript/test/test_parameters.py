import pytest


@pytest.mark.parametrize("args,valid", [
    ([], True),
    (['-m'], True),
    (['-e', 'aa'], False),
    (['-m', '-e', 'aa'], True),
    (['-m', '--namespace', 'aa'], True),
    (['--mailserver', '-e', 'aa'], True),
    (['--namespace', '', '--mailserver'], True),
])
def test_parameter_depends(args, valid):
  from .. import UberScript, types

  s = UberScript(
    playbook='add_domain.yml',
    parameters=[
      ('mailserver', 'm', {
        'help': '', 'action': 'store_true'
      }),
      ('namespace', 'e', {
        'help': '', 'type': str, 'depends': 'mailserver',
      }),
    ],
  )

  if not valid:
    with pytest.raises(SystemExit):
      s.parse_args(args)
  else:
    s.parse_args(args)

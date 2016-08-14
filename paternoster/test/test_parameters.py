import pytest
import six

from .. import Paternoster, types


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
    s = Paternoster(
        runner_parameters={'playbook': ''},
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


def test_find_param():
    s = Paternoster(
        runner_parameters={},
        parameters=[
            ('namespace', 'e', {'type': types.restricted_str('a')}),
            ('mailserver', 'm', {'action': 'store_true'}),
        ],
        runner_class=MockRunner
    )

    assert s._find_param('e')[0] == 'namespace'
    assert s._find_param('m')[0] == 'mailserver'
    assert s._find_param('namespace')[1] == 'e'
    assert s._find_param('mailserver')[1] == 'm'

    with pytest.raises(KeyError):
        s._find_param('somethingelse')


@pytest.mark.parametrize("param,valid", filter(lambda x: x is not None, [
    ({}, False),
    ({'type': str}, False),
    ({'type': unicode}, False) if six.PY2 else None,
    ({'type': types.restricted_str('a')}, True),
    ({'type': lambda x: x}, True),
    ({'action': 'store_true'}, True),
    ({'action': 'store_false'}, True),
    ({'action': 'store_const', 'const': 5}, True),
    ({'action': 'append'}, False),
    ({'action': 'append', 'type': str}, False),
    ({'action': 'append', 'type': types.restricted_str('a')}, True),
    ({'action': 'append_const', 'const': 5}, True),
]))
def test_forced_restricted_str(param, valid):
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[
            ('namespace', 'e', param),
        ],
    )

    if not valid:
        with pytest.raises(ValueError):
            s.parse_args([])
    else:
        s.parse_args([])


@pytest.mark.parametrize("required,argv,valid", [
    (True, ['-e', 'aa'], True),
    (True, [], False),
    (False, ['-e', 'aa'], True),
    (False, [], True),
])
def test_parameter_required(required, argv, valid):
    s = Paternoster(
        runner_parameters={},
        parameters=[
            ('namespace', 'e', {'type': types.restricted_str('a'), 'required': required}),
        ],
        runner_class=MockRunner
    )

    if not valid:
        with pytest.raises(SystemExit):
            s.parse_args(argv)
    else:
        s.parse_args(argv)


class MockRunner:
    def run(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return True


def test_parameter_passing():
    s = Paternoster(
        runner_parameters={},
        parameters=[
            ('namespace', 'e', {'type': types.restricted_str('a')}),
        ],
        runner_class=MockRunner
    )
    s.parse_args(['-e', 'aaaa'])
    s.execute()

    assert dict(s._runner.args[0])['param_namespace'] == 'aaaa'


def test_success_msg(capsys):
    s = Paternoster(
        runner_parameters={},
        parameters=[],
        runner_class=MockRunner,
        success_msg='4242',
    )
    s.parse_args([])
    s.execute()

    out, err = capsys.readouterr()
    assert out == '4242\n'

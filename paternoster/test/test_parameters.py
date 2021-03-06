# -*- coding: utf-8 -*-
import pytest
import six

from .. import Paternoster
from .. import types
from .mockrunner import MockRunner


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
            {
                'name': 'mailserver', 'short': 'm',
                'help': '', 'action': 'store_true',
                'dest': 'bla',
            },
            {
                'name': 'namespace', 'short': 'e',
                'help': '', 'type': types.restricted_str('a'), 'depends_on': 'mailserver',
            },
        ],
    )

    if not valid:
        with pytest.raises(SystemExit):
            s.parse_args(args)
    else:
        s.parse_args(args)


@pytest.mark.parametrize("args,valid", [
    ([], True),
    (['--dummy'], True),
    (['--mailserver'], True),
    (['--webserver'], True),
    (['--mailserver', '--dummy'], True),
    (['--mailserver', '--webserver'], False),
    (['--webserver', '--dummy'], False),
    (['-w'], True),
    (['-m', '-w'], False),
    (['-m', '--webserver'], False),
])
def test_parameter_mutually_exclusive(args, valid):
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[
            {
                'name': 'mailserver', 'short': 'm',
                'help': '', 'action': 'store_true',
            },
            {
                'name': 'webserver', 'short': 'w',
                'help': '', 'action': 'store_true',
            },
            {
                'name': 'dummy', 'short': 'd',
                'help': '', 'action': 'store_true',
                'dest': 'foo',
            },
        ],
        mutually_exclusive=[
            ['mailserver', 'webserver'],
            ['dummy', 'webserver'],
        ]
    )

    if not valid:
        with pytest.raises(SystemExit):
            s.parse_args(args)
    else:
        s.parse_args(args)


@pytest.mark.parametrize("args,valid", [
    ([], True),
    (['--mailserver'], True),
    (['--webserver'], True),
    (['--webserver', '--mailserver'], False),
])
def test_parameter_mutually_exclusive_dest(args, valid):
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[
            {'name': 'mailserver', 'action': 'store_true', 'dest': 'server'},
            {'name': 'webserver', 'action': 'store_true', 'dest': 'server'},
        ],
        mutually_exclusive=[
            ['mailserver', 'webserver'],
        ]
    )

    if not valid:
        with pytest.raises(SystemExit):
            s.parse_args(args)
    else:
        s.parse_args(args)


def test_parameter_dest():
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[
            {'name': 'mailserver', 'action': 'store_const', 'const': 'mail', 'dest': 'server'},
            {'name': 'webserver', 'action': 'store_const', 'const': 'web', 'dest': 'server'},
        ],
    )

    s.parse_args([])
    assert hasattr(s._parsed_args, 'server')
    assert s._parsed_args.server is None
    assert not hasattr(s._parsed_args, 'mailserver')

    s.parse_args(['--webserver'])
    assert hasattr(s._parsed_args, 'server')
    assert s._parsed_args.server == 'web'
    assert not hasattr(s._parsed_args, 'mailserver')

    s.parse_args(['--mailserver'])
    assert hasattr(s._parsed_args, 'server')
    assert s._parsed_args.server == 'mail'
    assert not hasattr(s._parsed_args, 'mailserver')


def test_parameter_dashed():
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[
            {'name': 'mail-server', 'action': 'store_true'},
        ],
    )
    s.parse_args(['--mail-server'])


@pytest.mark.parametrize("args,valid", [
    ([], False),
    (['--dummy'], False),
    (['--mailserver'], True),
    (['--webserver'], True),
    (['--mailserver', '--webserver'], True),
    (['--mailserver', '--dummy'], True),
])
def test_parameter_required_one_of(args, valid):
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[
            {
                'name': 'mailserver', 'short': 'm',
                'help': '', 'action': 'store_true',
            },
            {
                'name': 'webserver', 'short': 'w',
                'help': '', 'action': 'store_true',
                'dest': 'foo',
            },
            {
                'name': 'dummy', 'short': 'd',
                'help': '', 'action': 'store_true',
            },
        ],
        required_one_of=[
            ['mailserver', 'webserver'],
        ]
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
            {'name': 'mailserver', 'short': 'm', 'type': types.restricted_str('a')},
            {'name': 'namespace', 'short': 'e', 'action': 'store_true'},
        ],
        runner_class=MockRunner
    )

    assert s._find_param('e')['name'] == 'namespace'
    assert s._find_param('m')['name'] == 'mailserver'
    assert s._find_param('namespace')['short'] == 'e'
    assert s._find_param('mailserver')['short'] == 'm'

    with pytest.raises(KeyError):
        s._find_param('somethingelse')


class FakeStr(str):
    pass


cases_mandatory_parameters = [
    # parameters, parses okay with empty args
    ({}, False),
    ({'type': str}, False),
    ({'type': FakeStr}, False),
    ({'type': types.restricted_str('a')}, True),
    ({'type': lambda x: x}, True),
    ({'choices': ['a', 'b']}, True),
    ({'action': 'store_true'}, True),
    ({'action': 'store_false'}, True),
    ({'action': 'store_const', 'const': 5}, True),
    ({'action': 'append'}, False),
    ({'action': 'append', 'type': str}, False),
    ({'action': 'append', 'type': types.restricted_str('a')}, True),
    ({'action': 'append_const', 'const': 5}, True),
]

if six.PY2:
    cases_mandatory_parameters += [
        ({'type': unicode}, False), # noqa F821
    ]


@pytest.mark.parametrize("param,valid", cases_mandatory_parameters)
def test_type_mandatory(param, valid):
    p = {'name': 'namespace', 'short': 'e'}
    p.update(param)
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[p],
    )

    if not valid:
        with pytest.raises(ValueError):
            s.parse_args([])
    else:
        s.parse_args([])


@pytest.mark.parametrize("param,valid", filter(lambda x: x is not None, [
    ({'positional': True, 'type': types.restricted_str('a')}, True),
    ({'positional': True, 'type': types.restricted_str('a'), 'required': True}, False),
    ({'positional': True, 'type': types.restricted_str('a'), 'required': False}, False),
]))
def test_positional(param, valid):
    p = {'name': 'namespace', 'short': 'e'}
    p.update(param)
    s = Paternoster(
        runner_parameters={'playbook': ''},
        parameters=[p],
    )

    if not valid:
        with pytest.raises(TypeError):
            s.parse_args(['aaa'])
    else:
        s.parse_args(['aaa'])


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
            {'name': 'namespace', 'short': 'e', 'type': types.restricted_str('a'), 'required': required},
        ],
        runner_class=MockRunner
    )

    if not valid:
        with pytest.raises(SystemExit):
            s.parse_args(argv)
    else:
        s.parse_args(argv)


def test_arg_parameter_no_short():
    s = Paternoster(
        runner_parameters={},
        parameters=[
            {'name': 'namespace', 'type': types.restricted_str('a')},
        ],
        runner_class=MockRunner,
    )
    s.parse_args(['--namespace', 'aa'])
    assert s._parsed_args.namespace == 'aa'


def test_parameter_passing():
    s = Paternoster(
        runner_parameters={},
        parameters=[
            {'name': 'namespace', 'short': 'e', 'type': types.restricted_str('a')},
        ],
        runner_class=MockRunner
    )
    s.parse_args(['-e', 'aaaa'])
    s.execute()

    assert dict(s._runner.args[0])['param_namespace'] == 'aaaa'


def test_parameter_passing_unicode():
    s = Paternoster(
        runner_parameters={},
        parameters=[
            {'name': 'namespace', 'short': 'e', 'type': types.restricted_str('ä')},
        ],
        runner_class=MockRunner
    )
    s.parse_args(['-e', 'ää'])
    s.execute()

    assert dict(s._runner.args[0])['param_namespace'] == u'ää'


@pytest.mark.parametrize("value,valid", [
    (1, True),
    (5, True),
    (60, True),
    (600, False),
    (6, False),
    (2, False),
    ("a", False),
])
def test_parameter_argparse(value, valid):
    s = Paternoster(
        runner_parameters={},
        parameters=[
            {'name': 'number', 'short': 'n', 'type': int, 'choices': [1, 5, 60]},
        ],
        runner_class=MockRunner
    )

    argv = ['-n', str(value)]

    if not valid:
        with pytest.raises(SystemExit):
            s.parse_args(argv)
    else:
        s.parse_args(argv)


@pytest.mark.parametrize("success_msg,expected", [
    ('4242', '4242\n'),
    ('', ''),
    (None, ''),
])
def test_success_msg(success_msg, expected, capsys):
    s = Paternoster(
        runner_parameters={},
        parameters=[],
        runner_class=MockRunner,
        success_msg=success_msg,
    )
    s.parse_args([])
    s.execute()

    out, err = capsys.readouterr()
    assert out == expected


@pytest.mark.parametrize("description,expected", [
    ('Do things with stuff', 'Do things with stuff\n\n'),
    ('', ''),
    (None, ''),
])
def test_description(description, expected, capsys):
    s = Paternoster(
        runner_parameters={},
        parameters=[],
        runner_class=MockRunner,
        description=description,
    )
    with pytest.raises(SystemExit):
        s.parse_args(['--help'])

    out, err = capsys.readouterr()
    exp_help_text = 'usage: py.test [-h] [-v]\n\n{expected}optional arguments:'
    assert out.startswith(exp_help_text.format(expected=expected))


def test_arg_parameters_none():
    s = Paternoster(
        runner_parameters={},
        parameters=None,
        runner_class=MockRunner,
    )
    assert s._parameters == []


def test_arg_parameters_missing():
    s = Paternoster(
        runner_parameters={},
        runner_class=MockRunner,
    )
    assert s._parameters == []

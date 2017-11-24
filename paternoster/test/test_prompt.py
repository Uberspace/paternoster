from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import sys
import io

import pytest

from paternoster import Paternoster, types

from .mockrunner import MockRunner


class InputBuffer(object):

    def setup_method(self):
        self.stdin_org = sys.stdin

    def teardown_method(self):
        sys.stdin = self.stdin_org

    def buffer(self, text):
        sys.stdin = io.StringIO(text)


class TestPrompt(InputBuffer):

    PROMPT_TEXT = 'Enter: '

    def test_prompt(self, capsys):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('\n')
        p.prompt(self.PROMPT_TEXT)
        out, err = capsys.readouterr()
        assert out == self.PROMPT_TEXT

    def test_input(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('hello world test')
        res = p.prompt(self.PROMPT_TEXT)
        assert res == 'hello world test'

    def test_input_newlines(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('hello\nworld\ntest')
        res = p.prompt(self.PROMPT_TEXT)
        assert res == 'hello'

    def test_input_empty(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('\n')
        res = p.prompt(self.PROMPT_TEXT)
        assert res == ''


class TestInput(InputBuffer):

    def test_prompt_not_set(self, capsys):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\n')
        p.get_input(dict())
        out, err = capsys.readouterr()
        assert out == 'Input: '

    @pytest.mark.parametrize('value', [
        None,
        True,
        False,
        0,
        1,
        [1, 2, 3],
    ])
    def test_prompt_not_string(self, value, capsys):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\n')
        p.get_input(dict(prompt=value))
        out, err = capsys.readouterr()
        assert out == 'Input: '

    def test_prompt_string(self, capsys):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\n')
        p.get_input(dict(prompt='foo'))
        out, err = capsys.readouterr()
        assert out == 'foo'

    def test_prompt_empty(self, capsys):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\n')
        p.get_input(dict(prompt=''))
        out, err = capsys.readouterr()
        assert out == ''

    @pytest.mark.parametrize('value,exp', [
        ('xxx\n', 'xxx'),
        (' xxx\n', ' xxx'),
        (' xxx  \n', ' xxx  '),
        ('tes xxx\n', 'tes xxx'),
        ('tes  xxx\n', 'tes  xxx'),
        (' \n', ' '),
        ('  \n', '  '),
        ('\n\nxtestx\n', 'xtestx'),
        ('\n\n\nxtestx\nol ol\n', 'xtestx'),
    ])
    def test_input(self, value, exp):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer(value)
        res = p.get_input(dict())
        assert res == exp

    def test_input_error_empty(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('\n')
        with pytest.raises(EOFError):
            p.get_input(dict())

    def test_input_error_strip_empty(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('    \n')
        with pytest.raises(EOFError):
            p.get_input(dict(prompt_options=dict(strip=True)))

    @pytest.mark.parametrize('value,exp', [
        ('xxx\n', 'xxx'),
        (' xxx\n', ' xxx'),
        (' xxx  \n', ' xxx  '),
        ('tes xxx\n', 'tes xxx'),
        ('tes  xxx\n', 'tes  xxx'),
        (' \n', ' '),
        ('  \n', '  '),
        ('\n\nxtestx\n', ''),
        ('\n\n\nxtestx\nolol\n', ''),
        ('\n', ''),
    ])
    def test_input_opt_empty(self, value, exp):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer(value)
        res = p.get_input(dict(prompt_options=dict(empty=True)))
        assert res == exp

    @pytest.mark.parametrize('value,exp', [
        ('xxx\n', 'xxx'),
        (' xxx\n', 'xxx'),
        (' xxx  \n', 'xxx'),
        ('tes xxx\n', 'tes xxx'),
        ('tes  xxx\n', 'tes  xxx'),
    ])
    def test_input_opt_strip(self, value, exp):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer(value)
        res = p.get_input(dict(prompt_options=dict(strip=True)))
        assert res == exp

    @pytest.mark.parametrize('value,exp', [
        ('xxx\n', 'xxx'),
        (' xxx\n', 'xxx'),
        (' xxx  \n', 'xxx'),
        ('tes xxx\n', 'tes xxx'),
        ('tes  xxx\n', 'tes  xxx'),
        (' \n', ''),
        ('  \n', ''),
        ('\n\nxtestx\n', ''),
        ('\n\n\nxtestx\nolol\n', ''),
        ('\n', ''),
    ])
    def test_input_opt_empty_strip(self, value, exp):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer(value)
        res = p.get_input(dict(prompt_options=dict(empty=True, strip=True)))
        assert res == exp

    def test_confirm_not_string(self, capsys):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\ntest\n')
        p.get_input(dict(prompt_options=dict(confirm=True)))
        out, err = capsys.readouterr()
        assert out == 'Input: Please confirm: '

    def test_confirm_string(self, capsys):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\ntest\n')
        p.get_input(dict(prompt_options=dict(confirm='lol:')))
        out, err = capsys.readouterr()
        assert out == 'Input: lol:'

    def test_confirm(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\ntest\n')
        res = p.get_input(dict(prompt_options=dict(confirm=True)))
        assert res == 'test'

    def test_confirm_fail(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\ntest2\n')
        with pytest.raises(ValueError):
            p.get_input(dict(prompt_options=dict(confirm=True)))

    def test_confirm_fail_msg(self):
        p = Paternoster(runner_parameters={}, runner_class=MockRunner)
        self.buffer('test\ntest2\n')
        with pytest.raises(ValueError) as excinfo:
            p.get_input({
                'prompt_options': {
                    'confirm': True,
                    'confirm_error': 'lol',
                },
            })
        assert str(excinfo.value) == u'lol'


class TestIntegration(InputBuffer):

    def test_no_prompt(self):
        p = Paternoster(
            runner_parameters={},
            parameters=[
                {
                    'name': 'username',
                    'short': 'u',
                    'type': types.restricted_str(allowed_chars='a-z'),
                },
                {
                    'name': 'password',
                    'short': 'p',
                    'type': types.restricted_str(allowed_chars='a-z'),
                },
            ],
            runner_class=MockRunner,
        )
        p.parse_args(argv=['--username', 'testor'])
        args = {k: v for (k, v) in p._get_runner_variables()}
        assert args['param_username'] == 'testor'
        assert args['param_password'] is None

    def test_prompt(self):
        p = Paternoster(
            runner_parameters={},
            parameters=[
                {
                    'name': 'username',
                    'short': 'u',
                    'type': types.restricted_str(allowed_chars='a-z'),
                },
                {
                    'name': 'password',
                    'short': 'p',
                    'type': types.restricted_str(allowed_chars='a-z'),
                    'prompt': True,
                },
            ],
            runner_class=MockRunner,
        )
        self.buffer('secret\n')
        p.parse_args(argv=['--username', 'testor'])
        args = {k: v for (k, v) in p._get_runner_variables()}
        assert args['param_username'] == 'testor'
        assert args['param_password'] == 'secret'

    def test_prompt_confirm(self):
        p = Paternoster(
            runner_parameters={},
            parameters=[
                {
                    'name': 'username',
                    'short': 'u',
                    'type': types.restricted_str(allowed_chars='a-z'),
                },
                {
                    'name': 'password',
                    'short': 'p',
                    'type': types.restricted_str(allowed_chars='a-z'),
                    'prompt': True,
                    'prompt_options': {
                        'confirm': True,
                    },
                },
            ],
            runner_class=MockRunner,
        )
        self.buffer('secret\nsecret\n')
        p.parse_args(argv=['--username', 'testor'])
        args = {k: v for (k, v) in p._get_runner_variables()}
        assert args['param_username'] == 'testor'
        assert args['param_password'] == 'secret'

    def test_prompt_confirm_failed(self):
        p = Paternoster(
            runner_parameters={},
            parameters=[
                {
                    'name': 'username',
                    'short': 'u',
                    'type': types.restricted_str(allowed_chars='a-z'),
                },
                {
                    'name': 'password',
                    'short': 'p',
                    'type': types.restricted_str(allowed_chars='a-z'),
                    'prompt': True,
                    'prompt_options': {
                        'confirm': True,
                    },
                },
            ],
            runner_class=MockRunner,
        )
        self.buffer('secret\nsecret2\n')
        with pytest.raises(SystemExit) as excinfo:
            p.parse_args(argv=['--username', 'testor'])
        assert str(excinfo.value) == '3'

    def test_prompt_required(self):
        p = Paternoster(
            runner_parameters={},
            parameters=[
                {
                    'name': 'username',
                    'short': 'u',
                    'type': types.restricted_str(allowed_chars='a-z'),
                    'required': True,
                },
                {
                    'name': 'password',
                    'short': 'p',
                    'type': types.restricted_str(allowed_chars='a-z'),
                    'prompt': True,
                    'required': True,
                },
            ],
            runner_class=MockRunner,
        )
        self.buffer('secret\n')
        with pytest.raises(SystemExit) as excinfo:
            p.parse_args(argv=['--username', 'testor'])
        assert str(excinfo.value) == '2'

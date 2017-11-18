from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import io
import sys

try:
    from unittest.mock import patch
except ImportError:
    try:
        from mock import patch
    except ImportError:
        patch = None

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


class PaternosterHelper(object):

    DEFAULT_PARAM_NAME = 'username'

    def get_param(self, prompt=None, options={}, name=None, **kwargs):
        param = {
            'name': name if (name is not None) else self.DEFAULT_PARAM_NAME,
        }
        if prompt:
            param['prompt'] = prompt
        if options:
            param['prompt_options'] = options
        if 'short' not in kwargs:
            param['short'] = param['name'][0]
        if 'type' not in kwargs:
            param['type'] = types.restricted_str(allowed_chars='a-z')
        param.update(kwargs)
        return param

    def get_paternoster(self, *parameters, **kwargs):
        defaults = {
            'runner_parameters': {},
            'runner_class': MockRunner,
            'parameters': parameters,
        }
        defaults.update(kwargs)
        return Paternoster(**defaults)


class TestPrompt(PaternosterHelper, InputBuffer):

    PROMPT_TEXT = 'Enter: '

    def test_prompt(self, capsys):
        p = self.get_paternoster()
        self.buffer('\n')
        p.prompt(self.PROMPT_TEXT)
        out, err = capsys.readouterr()
        assert out == self.PROMPT_TEXT

    @pytest.mark.skipif(patch is None, reason='test needs `mock`')
    def test_echo(self):
        """Check that `getpass` is called if *no_echo* is set."""
        with patch('paternoster.paternoster.getpass.getpass') as mockfunc:
            p = self.get_paternoster()
            self.buffer('\n')
            p.prompt(self.PROMPT_TEXT)
            mockfunc.assert_not_called()
        with patch('paternoster.paternoster.getpass.getpass') as mockfunc:
            p = self.get_paternoster()
            self.buffer('\n')
            p.prompt(self.PROMPT_TEXT, no_echo=True)
            mockfunc.assert_called()

    def test_input(self):
        p = self.get_paternoster()
        self.buffer('hello world test')
        res = p.prompt(self.PROMPT_TEXT)
        assert res == 'hello world test'

    def test_input_newlines(self):
        p = self.get_paternoster()
        self.buffer('hello\nworld\ntest')
        res = p.prompt(self.PROMPT_TEXT)
        assert res == 'hello'

    def test_input_empty(self):
        p = self.get_paternoster()
        self.buffer('\n')
        res = p.prompt(self.PROMPT_TEXT)
        assert res == ''


class TestInput(PaternosterHelper, InputBuffer):

    DEFAULT_PARAM_NAME = 'username'

    def test_prompt_not_set(self, capsys):
        p = self.get_paternoster()
        self.buffer('test\n')
        param = self.get_param()
        p.get_input(param)
        out, err = capsys.readouterr()
        assert out == 'Username: '

    def test_prompt_True(self, capsys):
        p = self.get_paternoster()
        self.buffer('test\n')
        param = self.get_param(prompt=True)
        p.get_input(param)
        out, err = capsys.readouterr()
        assert out == 'Username: '

    def test_prompt_string(self, capsys):
        p = self.get_paternoster()
        self.buffer('test\n')
        param = self.get_param(prompt='foo')
        p.get_input(param)
        out, err = capsys.readouterr()
        assert out == 'foo'

    @pytest.mark.parametrize('value', [
        None,
        False,
        0,
        1,
        [1, 2, 3],
    ])
    def test_prompt_object(self, value, capsys):
        p = self.get_paternoster()
        self.buffer('test\n')
        param = self.get_param(prompt=value)
        p.get_input(param)
        out, err = capsys.readouterr()
        assert out == 'Username: '

    def test_prompt_empty(self, capsys):
        p = self.get_paternoster()
        self.buffer('test\n')
        param = self.get_param(prompt='')
        p.get_input(param)
        out, err = capsys.readouterr()
        assert out == 'Username: '

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
        p = self.get_paternoster()
        self.buffer(value)
        param = self.get_param()
        res = p.get_input(param)
        assert res == exp

    def test_input_error_empty(self):
        p = self.get_paternoster()
        self.buffer('\n')
        with pytest.raises(EOFError):
            param = self.get_param()
            p.get_input(param)

    def test_input_error_empty_opt_strip(self):
        p = self.get_paternoster()
        self.buffer('    \n')
        with pytest.raises(EOFError):
            param = self.get_param(options=dict(strip=True))
            p.get_input(param)

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
    def test_input_opt_accept_empty(self, value, exp):
        p = self.get_paternoster()
        self.buffer(value)
        param = self.get_param(options=dict(accept_empty=True))
        res = p.get_input(param)
        assert res == exp

    @pytest.mark.parametrize('value,exp', [
        ('xxx\n', 'xxx'),
        (' xxx\n', 'xxx'),
        (' xxx  \n', 'xxx'),
        ('tes xxx\n', 'tes xxx'),
        ('tes  xxx\n', 'tes  xxx'),
    ])
    def test_input_opt_strip(self, value, exp):
        p = self.get_paternoster()
        self.buffer(value)
        param = self.get_param(options=dict(strip=True))
        res = p.get_input(param)
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
    def test_input_opt_accept_empty_strip(self, value, exp):
        p = self.get_paternoster()
        self.buffer(value)
        param = self.get_param(options=dict(accept_empty=True, strip=True))
        res = p.get_input(param)
        assert res == exp

    def test_confirm_not_string(self, capsys):
        p = self.get_paternoster()
        self.buffer('test\ntest\n')
        param = self.get_param(options=dict(confirm=True))
        p.get_input(param)
        out, err = capsys.readouterr()
        assert out == 'Username: Please confirm: '

    def test_confirm_string(self, capsys):
        p = self.get_paternoster()
        self.buffer('test\ntest\n')
        param = self.get_param(options=dict(confirm='lol:'))
        p.get_input(param)
        out, err = capsys.readouterr()
        assert out == 'Username: lol:'

    def test_confirm(self):
        p = self.get_paternoster()
        self.buffer('test\ntest\n')
        param = self.get_param(options=dict(confirm=True))
        res = p.get_input(param)
        assert res == 'test'

    def test_confirm_fail(self):
        p = self.get_paternoster()
        self.buffer('test\ntest2\n')
        with pytest.raises(ValueError):
            param = self.get_param(options=dict(confirm=True))
            p.get_input(param)

    def test_confirm_fail_msg(self):
        p = self.get_paternoster()
        self.buffer('test\ntest2\n')
        with pytest.raises(ValueError) as excinfo:
            param = self.get_param(options=dict(
                confirm=True, confirm_error='lol'
            ))
            p.get_input(param)
        assert str(excinfo.value) == u'lol'

    def test_echo(self):
        with patch('paternoster.paternoster.getpass.getpass') as mockfunc:
            p = self.get_paternoster()
            self.buffer('elo\n')
            param = self.get_param()
            p.get_input(param)
            mockfunc.assert_not_called()
        with patch('paternoster.paternoster.getpass.getpass') as mockfunc:
            p = self.get_paternoster()
            self.buffer('elo part two\n')
            param = self.get_param(options=dict(no_echo=True))
            p.get_input(param)
            mockfunc.assert_called()


class TestIntegrationParams(PaternosterHelper, InputBuffer):

    def test_no_prompt(self):
        para01 = self.get_param()
        para02 = self.get_param(name='password')
        p = self.get_paternoster(para01, para02)
        p.parse_args(argv=['--username', 'testor'])
        args = dict(p._get_runner_variables())
        assert args['param_username'] == 'testor'
        assert args['param_password'] is None

    def test_prompt(self):
        para01 = self.get_param()
        para02 = self.get_param(name='password', prompt=True)
        p = self.get_paternoster(para01, para02)
        self.buffer('secret\n')
        p.parse_args(argv=['--username', 'testor'])
        args = dict(p._get_runner_variables())
        assert args['param_username'] == 'testor'
        assert args['param_password'] == 'secret'

    def test_prompt_confirm(self):
        para01 = self.get_param()
        para02 = self.get_param(
            name='password', prompt=True, options={'confirm': True},
        )
        p = self.get_paternoster(para01, para02)
        self.buffer('secret\nsecret\n')
        p.parse_args(argv=['--username', 'testor'])
        args = dict(p._get_runner_variables())
        assert args['param_username'] == 'testor'
        assert args['param_password'] == 'secret'

    def test_prompt_confirm_failed(self):
        para01 = self.get_param()
        para02 = self.get_param(
            name='password', prompt=True, options={'confirm': True},
        )
        p = self.get_paternoster(para01, para02)
        self.buffer('secret\nsecretasd\n')
        with pytest.raises(SystemExit) as excinfo:
            p.parse_args(argv=['--username', 'testor'])
        assert str(excinfo.value) == '3'

    def test_prompt_required(self, capsys):
        para01 = self.get_param()
        para02 = self.get_param(
            name='password', prompt=True, required=True,
        )
        p = self.get_paternoster(para01, para02)
        self.buffer('secret\n')
        with pytest.raises(SystemExit) as excinfo:
            p.parse_args(argv=['--username', 'testor'])
        assert str(excinfo.value) == '2'
        out, err = capsys.readouterr()
        assert err.endswith("'--password' is required and can't be combined with prompt\n")

    @pytest.mark.parametrize('value', [
        None,
        False,
        0,
        1,
        [1, 2, 3],
    ])
    def test_prompt_error_wrong_type(self, value):
        para01 = self.get_param()
        para02 = self.get_param(name='password', prompt=value)
        p = self.get_paternoster(para01, para02)
        self.buffer('test\n')
        p.parse_args(argv=['--username', 'testor'])
        args = dict(p._get_runner_variables())
        assert args['param_username'] == 'testor'
        assert args['param_password'] is None

    def test_type_check(self, capsys):
        para01 = self.get_param()
        para02 = self.get_param(name='password', prompt=True)
        p = self.get_paternoster(para01, para02)
        self.buffer('secret2\n')
        with pytest.raises(SystemExit) as excinfo:
            p.parse_args(argv=['--username', 'testor'])
        assert str(excinfo.value) == '2'
        out, err = capsys.readouterr()
        assert (
            err.endswith("invalid string value: u'secret2'\n")  # Python 2
            or err.endswith("invalid string value: 'secret2'\n")  # Python 3
        )

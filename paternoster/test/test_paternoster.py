# -*- coding: utf-8 -*-

import pytest
import sys

from .mockrunner import MockRunner


@pytest.mark.parametrize("args,kwargs,valid", [
    [[], {'become_root': False, 'become_user': None, 'check_root': False}, True],
    [[], {'become_root': True, 'become_user': None, 'check_root': False}, True],
    [[], {'become_root': False, 'become_user': 'foo', 'check_root': False}, True],
    [[], {'become_root': False, 'become_user': None, 'check_root': True}, True],
    [[], {'become_root': True, 'become_user': None, 'check_root': True}, False],
    [[], {'become_root': True, 'become_user': 'foo', 'check_root': True}, False],
    [[], {'become_root': True, 'become_user': 'foo', 'check_root': False}, False],
])
def test_auto(args, kwargs, valid, monkeypatch):
    from ..paternoster import Paternoster

    class Runner:
        pass

    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)

    p = Paternoster(runner_parameters={}, parameters=[], runner_class=Runner)
    p.execute = lambda *args, **kwargs: True
    p.parse_args = lambda *args, **kwargs: True
    p.become_user = lambda *args, **kwargs: 'testy'
    p.check_root = lambda *args, **kwargs: True

    if not valid:
        with pytest.raises(ValueError):
            p.auto(*args, **kwargs)
    else:
        p.auto(*args, **kwargs)


@pytest.mark.parametrize("status,rc", [
    (True, 0),
    (False, 1),
])
def test_auto_returncode(status, rc):
    from ..paternoster import Paternoster

    p = Paternoster(
        runner_parameters={'result': status},
        parameters=[], runner_class=MockRunner
    )

    with pytest.raises(SystemExit) as excinfo:
        p.auto()

    assert excinfo.value[0] == rc

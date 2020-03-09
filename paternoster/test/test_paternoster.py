# -*- coding: utf-8 -*-
import sys

import pytest

from .mockrunner import MockRunner


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

    assert excinfo.value.code == rc

# -*- coding: utf-8 -*-
import os
import pwd

import pytest


@pytest.mark.parametrize("sudo_user,valid", [
    ('aa', True),
    ('b22', True),
    ('abbbbb4', True),
    ('ab_a', False),
    ('a' * 30, False),
    ('a' * 30 + '22', False),
    ('22', False),
    ('a22\n2', False),
    ('\x01aaa', False),
    ('aaa\x01', False),
])
def test_type_domain(sudo_user, valid):
    from ..root import become_user

    current_user = pwd.getpwuid(os.getuid()).pw_name
    os.environ['SUDO_USER'] = sudo_user

    if not valid:
        with pytest.raises(ValueError):
            become_user(current_user)
    else:
        rtn_sudo_user = become_user(current_user)
        assert rtn_sudo_user == sudo_user

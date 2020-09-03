import sys
from distutils.version import LooseVersion

import ansible.release
import pytest

ANSIBLE_VERSION = LooseVersion(ansible.release.__version__)
SKIP_ANSIBLE_TESTS = (sys.version_info >= (3, 0) and ANSIBLE_VERSION < LooseVersion('2.4.0'))


@pytest.mark.parametrize("args,kwargs,isfilertn,valid", [
    ([None], {}, None, False),
    (['../playbook.yml'], {}, True, False),
    (['/playbook.yml'], {}, True, True),
    (['/i/do/not/exist.yml'], {}, None, False),
])
def test_playbook_validation(args, kwargs, isfilertn, valid, monkeypatch):
    import os
    from ..runners.ansiblerunner import AnsibleRunner
    from ansible.errors import AnsibleFileNotFound

    if isfilertn is not None:
        monkeypatch.setattr(os.path, 'isfile', lambda *args, **kwargs: isfilertn)

    monkeypatch.setattr(os, 'chdir', lambda *args, **kwargs: None)

    try:
        if not valid:
            with pytest.raises(ValueError):
                AnsibleRunner(*args, **kwargs).run({}, False)
        else:
            AnsibleRunner(*args, **kwargs).run({}, False)
    except AnsibleFileNotFound:
        pass


@pytest.mark.skipif(SKIP_ANSIBLE_TESTS, reason="ansible <2.4 requires python2")
@pytest.mark.parametrize("verbosity,keywords,notkeywords", [
    (False, [], ["TASK [debug]", "PLAY RECAP"]),
    (True, ["TASK [debug]", "PLAY RECAP"], ["ESTABLISH LOCAL CONNECTION"]),
    (3, ["TASK [debug]", "PLAY RECAP", "task path"], []),
])
def test_verbose(verbosity, keywords, notkeywords, capsys, monkeypatch):
    import os
    from ..runners.ansiblerunner import AnsibleRunner

    playbook_path = '/tmp/paternoster-test-playbook.yml'
    playbook = """
    - hosts: all
      gather_facts: no
      tasks:
        - debug: msg=a
    """

    with open(playbook_path, 'w') as f:
        f.write(playbook)

    monkeypatch.setattr(os, 'chdir', lambda *args, **kwargs: None)
    AnsibleRunner(playbook_path).run([], verbosity)

    out, err = capsys.readouterr()

    for kw in keywords:
        assert (kw in out) or (kw in err)
    for kw in notkeywords:
        assert (kw not in out) and (kw not in err)


@pytest.mark.skipif(SKIP_ANSIBLE_TESTS, reason="ansible <2.4 requires python2")
@pytest.mark.parametrize("task,exp_out,exp_err,exp_status", [
    ("debug: msg=hi", "hi\n", "", True),
    # the list order is not defined in some ansible versions, so we just assert
    # that all items are present in whatever order.
    # https://github.com/ansible/ansible/issues/21008
    ("debug: var=item\n          with_items: ['a', 'b']", ["a", "b"], "", True),
    ("debug: msg='{{ item }}'\n          with_items: ['a', 'b']", ["a", "b"], "", True),
    ("debug: var=param_foo", "22\n", "", True),
    ("command: echo hi", "", "", True),
    ("fail: msg=42", "", "42\n", False),
    ("fail: msg=42\n          ignore_errors: yes", "", "", True),
    ("""fail: msg='{{ item }}'
          with_items:
            - /bin/true
            - /bin/maybe""", "", ["/bin/true", "/bin/maybe"], False),
    ("""command: '{{ item }}'
          with_items:
            - /bin/true
            - /bin/maybe""", "", ["No such file"], False)
])
def test_output(task, exp_out, exp_err, exp_status, capsys, monkeypatch):
    import os
    from ..runners.ansiblerunner import AnsibleRunner

    playbook_path = '/tmp/paternoster-test-playbook.yml'
    playbook = """
    - hosts: all
      gather_facts: no
      tasks:
        - """ + task

    with open(playbook_path, 'w') as f:
        f.write(playbook)

    monkeypatch.setattr(os, 'chdir', lambda *args, **kwargs: None)
    status = AnsibleRunner(playbook_path).run([('param_foo', 22)], False)

    out, err = capsys.readouterr()

    if isinstance(exp_out, list):
        for s in exp_out:
            assert s in out
    else:
        assert out == exp_out

    if isinstance(exp_err, list):
        for s in exp_err:
            assert s in err
    else:
        assert err == exp_err

    assert status == exp_status


@pytest.mark.skipif(SKIP_ANSIBLE_TESTS, reason="ansible <2.4 requires python2")
def test_paramater_passing(capsys, monkeypatch):
    import os
    from ..runners.ansiblerunner import AnsibleRunner

    playbook_path = '/tmp/paternoster-test-playbook.yml'
    playbook = """
    - hosts: all
      gather_facts: no
      tasks:
        - debug: var=param_foo
        - set_fact:
            param_foo: new value
        - debug: var=param_foo
    """

    with open(playbook_path, 'w') as f:
        f.write(playbook)

    monkeypatch.setattr(os, 'chdir', lambda *args, **kwargs: None)
    AnsibleRunner(playbook_path).run([('param_foo', 'param_foo value')], False)

    out, err = capsys.readouterr()

    assert 'param_foo value' in out
    assert 'new value' in out


@pytest.mark.skipif(SKIP_ANSIBLE_TESTS, reason="ansible <2.4 requires python2")
def test_msg_handling_hide_warnings(capsys, monkeypatch):
    """Don't display warning on missing `msg` key in `results`."""
    import os
    from ..runners.ansiblerunner import AnsibleRunner

    playbook_path = '/tmp/paternoster-test-playbook.yml'
    playbook = """
    - hosts: all
      gather_facts: no
      tasks:
      - debug:
          msg: start
      - assert:
          that: 1 == 0
        ignore_errors: yes
        with_items:
        - 1
        - 2
      - debug:
          msg: stop
    """

    with open(playbook_path, 'w') as f:
        f.write(playbook)

    monkeypatch.setattr(os, 'chdir', lambda *args, **kwargs: None)
    AnsibleRunner(playbook_path).run([], False)

    exp_stdout = "start\nstop\n"
    exp_stderr = ''

    out, err = capsys.readouterr()

    assert out == exp_stdout
    assert err == exp_stderr


@pytest.mark.skipif(SKIP_ANSIBLE_TESTS, reason="ansible <2.4 requires python2")
def test_msg_handling_hide_nonzero(capsys, monkeypatch):
    """Don't display `non-zero return code` on failing tasks if errors are ignored."""
    import os
    from ..runners.ansiblerunner import AnsibleRunner

    playbook_path = '/tmp/paternoster-test-playbook.yml'
    playbook = """
    - hosts: all
      gather_facts: no
      tasks:
      - debug:
          msg: start
      - shell: /bin/fail
        ignore_errors: yes
        with_items:
        - 1
        - 2
      - debug:
          msg: stop
    """

    with open(playbook_path, 'w') as f:
        f.write(playbook)

    monkeypatch.setattr(os, 'chdir', lambda *args, **kwargs: None)
    AnsibleRunner(playbook_path).run([], False)

    exp_stdout = "start\nstop\n"
    exp_stderr = ''

    out, err = capsys.readouterr()

    assert out == exp_stdout
    assert err == exp_stderr

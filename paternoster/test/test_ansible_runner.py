import pytest


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


@pytest.mark.parametrize("task,exp_out,exp_err,exp_status", [
    ("debug: msg=hi", "hi\n", "", True),
    ("debug: var=param_foo", "22\n", "", True),
    ("command: echo hi", "", "", True),
    ("fail: msg=42", "", "42\n", False),
])
def test_fail_output(task, exp_out, exp_err, exp_status, capsys, monkeypatch):
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
    assert out == exp_out
    assert err == exp_err
    assert status == exp_status

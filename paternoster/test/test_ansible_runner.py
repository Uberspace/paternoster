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

    try:
        if not valid:
            with pytest.raises(ValueError):
                AnsibleRunner(*args, **kwargs).run({}, False)
        else:
            AnsibleRunner(*args, **kwargs).run({}, False)
    except AnsibleFileNotFound:
        pass

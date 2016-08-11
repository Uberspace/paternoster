import pytest


@pytest.mark.parametrize("args,kwargs,valid", [
  ([None], {}, False),
  (['../playbook.yml'], {}, False),
  (['/playbook.yml'], {}, True),
])
def test_playbook_validation(args, kwargs, valid, monkeypatch):
  import os
  from ..runners.ansiblerunner import AnsibleRunner
  from ansible.errors import AnsibleFileNotFound

  def alwaystrue(*args, **kwargs):
    return True

  monkeypatch.setattr(os.path, 'isfile', alwaystrue)

  try:
    if not valid:
      with pytest.raises(ValueError):
        AnsibleRunner(*args, **kwargs).run({}, False)
    else:
      AnsibleRunner(*args, **kwargs).run({}, False)
  except AnsibleFileNotFound:
    pass

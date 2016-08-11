# Paternoster

Paternoster provides users with the ability to run certain tasks as
root or another user, while ensuring safety by providing a common
interface and battle tested parameter parsing/checking.

# Theory of Operation

The developer writes a small python script (10-30 lines, most of which
is a `dict`) which initializes Paternoster. Following a method call the
library takes over, parses user-given arguments, validates their
contents and passes them on to a given ansible playbook via the ansible
python module. All parameters are checked for proper types (including
more complicated checks like domain-validity).

## Security

This library is a small-ish wrapper around pythons battle-tested [argparse](https://docs.python.org/2/library/argparse.html)
and the ansible api. Arguments are passed to argparse for evaluation.
All standard-types like integers are handled by the python standard
library. Special types like domains are implemented within Paternoster.
Once argparse has finished Paternoster relies on the ansible API to
execute the given playbook. All parameters are passed safely as variables.

Before parsing parameters Paternoster executes itself as root via sudo.
Combined with a proper sudoers-config this ensures that the script has
not been copied somewhere else and is unmodified.

# Script-Development

A typical boilerplate for Paternoster looks like this:

```python
#!/bin/env python2.7

import paternoster
import paternoster.types

paternoster.Paternoster(
  runner_parameters={'playbook': '/opt/uberspace/playbooks/uberspace-add-domain.yml'},
  parameters=[
    ('domain', 'd', {
      'help': 'this is the domain to add to your uberspace',
      'type': paternoster.types.domain,
    }),
  ],
  success_msg='Your domain has been added successfully.',
).auto(become_root=True)
```

Please refer to the corresponding sub-document on how to develop scripts
using Paternoster: [`doc/script_development.md`](doc/script_development.md).

# Library-Development

Most tasks (including adding new types) can be achieved by writing
scripts only. Therefore, the library does not need to be changed in most
cases. Sometimes it might be desirable to provide a new type or feature
to all other scripts. To fulfill these needs, the following section
outlines the setup and development process for library.

## Setup
To get a basic environment up and running, use the following commands:

```bash
virtualenv venv --python python2.7
source venv/bin/activate
python setup.py develop
```

This project uses python 2.7, because python 3.x is not yet supported by
ansible. All non-ansible code is tested with python 3.5 as well.

### Vagrant

Most features, where unit tests suffice can be tested using a virtualenv only. If your development
relies on the sudo-mechanism, you can spin up a [vagrant VM](https://vagrantup.com) which provides
a dummy `uberspace-add-domain`-script as well as the library-code in the
`/vagrant`-directory.

```bash
vagrant up
vagrant ssh
```

inside the host:

```
Last login: Wed Aug  3 17:23:02 2016 from 10.0.2.2
[vagrant@localhost ~]$ uberspace-add-domain -d a.com -v

PLAY [test play] ************** (...)
```

If you want to add your own scripts, just add the corresponding files in
`vagrant/files/playbooks` and `vagrant/files/scripts`. You can deploy it
using the `ansible-playbook vagrant/site.yml --tags scripts` command.
Once your script has been deployed, you can just edit the source file
to make further changes, as the file is symlinked, not copied.

## Tests

### Unit Tests

The core functionality of this library can be tested using the `tox`-
command. If only python 2.x or 3.x should be tested, the `-e` parameter
can be used, like so: `tox -e py35`, `tox -e py27`. New tests should be
added to the `paternoster/test`-directory.
Please refer to the [pytest-documentation](http://doc.pytest.org/) for
further details.

### System Tests

Some features (like the `become_root` function) require a correctly
setup linux environment. They can be tested using the provided ansible
playbooks in `vagrant/tests`.

The playbooks can be invoked using the `ansible-playbook`-command:

```
$ ansible-playbook vagrant/tests/test_variables.yml

PLAY [test script_name and sudo_user variables] ********************************

(...)

PLAY RECAP *********************************************************************
default                    : ok=7    changed=5    unreachable=0    failed=0
```

It is also possible to run all playbooks by executing `ansible-playbook vagrant/tests/test_*.yml`.
At some later point in development, the tests will be run automatically by
pytest or some other mechanism.

#### Boilerplate

A typical [ansible playbook](http://docs.ansible.com/ansible/playbooks.html)
for a system-test might look like this:

```yaml
- name: give this test a proper name
  hosts: all
  tasks:
    - include: drop_script.yml
      vars:
        ignore_script_errors: yes
        script_params: --some-parameter
        playbook: |
          - hosts: all
            tasks:
              - debug: msg="hello world"
        script: |
          #!/bin/env python2.7
          # some python code to test

    - assert:
        that:
          - "script.stdout_lines[0] == 'something'"
```

Most of the heavy lifting is done by the included `drop_script.yml`-file. It
creates the required python-script & playbook, executes it and stores the result
in the `script`-variable. After the execution, all created files are removed.
After the script has been executed, the [`assert`-module](http://docs.ansible.com/ansible/assert_module.html)
can be used to check the results.

There are several parameters to control the behaviour of `drop_script.yml`:

| Name | Optional | Description |
| ---- | -------- | ----------- |
| `script` | no | the **content** of a python script to save as `/usr/local/bin/uberspace-unittest` and execute |
| `playbook` | yes (default: empty) | the **content** of a playbook to save as `/opt/uberspace/playbooks/uberspace-unittest.yml` |
| `ignore_script_errors` | yes (default: `false`) | whether to continue even if python script has a non-zero exitcode |
| `script_params` | yes (default: empty) | command line parameters for the script (e.g. `"--domain foo.com"`) |

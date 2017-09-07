# Paternoster [![Build Status](https://travis-ci.org/Uberspace/paternoster.svg?branch=master)](https://travis-ci.org/Uberspace/paternoster)

<img align="left" height="150" src="logo.png">

Paternoster enables ansible playbooks to be run like normal bash or python
scripts. It parses the given parameters using python's [argparse](https://docs.python.org/2/library/argparse.html)
and the passes them on to the actual playbook via the ansible API. In addition
it provides an automated way to run commands as another user, which can be used
to give normal shell users special privileges, while still having a sleek and
easy to understand user interface.

Once everything is set up, a paternoster script can be used like this:

```
$ create-user --help
usage: create-user [-h] -u USERNAME [-v]

Create a user.

required arguments:
  -u USERNAME, --username USERNAME
                        name of the user to create

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         run with a lot of debugging output
$ create-user -u luto
creating user luto
```

The script looks like a normal ansible playbook, except for a few additions.
Firstly, it uses a different shebang-line, which kicks off paternoster instead
of ansible. Secondly, there is a special play at the beginning of the playbook,
which contains the configuration for parameter parsing and other features.

```yaml
#!/usr/bin/env paternoster

- hosts: paternoster
  vars:
    description: Create a user.
    parameters:
      - name: username
        short: u
        help: "name of the user to create"
        type: paternoster.types.restricted_str
        required: yes
        type_params:
          regex: '^[a-z]+$'

- hosts: localhost
  tasks:
    - debug: msg="creating user {{ param_username }}"
```

For more information on how to develop scripts using paternoster, please refer
the the corresponding sub-document: [`doc/script_development.md`](doc/script_development.md).

## Privilege Escalation

Paternoster also provides an automated way to run commands as another user. To
use this feature, set the `become_user` to the desired username. This causes
paternoster to execute itself as the given user using sudo. For this to work a
sudoers-config has to be created by the developer.

Please refer to the Deployment section of this document for further details.

# Deployment

## Python-Module

The python module can be installed using pip: `pip install paternoster`.

## sudo

If you are planning to let users execute certain commands as root,
a few changes to your `sudo`-configuration are needed. boils down to:

```
ALL ALL = NOPASSWD: /usr/local/bin/your-script-name
```

This line allows *any* user to execute the given command as root.

Please refer to the [`sudoers(5)`-manpage](https://www.sudo.ws/man/1.8.17/sudoers.man.html) for details.

## Notes

* this library makes use of the `tldextract`-module. Internally this
  relies on a list of top level domains, which changes every so often.
  Execute the `tldextract --update`-command as root in a cronjob or
  similar to keep the list up to date.

# Library-Development

Most tasks can be achieved by writing
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
pip install -r dev-requirements.txt
```

This project uses python 2.7, because python 3.x is not yet supported by
ansible. All non-ansible code is tested with python 3 as well.

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
`vagrant/files/scripts`. You can deploy it using the following command:
`ansible-playbook vagrant/site.yml --tags scripts`.
Once your script has been deployed, you can just edit the source file
to make further changes, as the file is symlinked, not copied.

## Tests

### Unit Tests

The core functionality of this library can be tested using the `tox`-
command. If only python 2.x or 3.x should be tested, the `-e` parameter
can be used, like so: `tox -e py36-ansible23`, `tox -e py27-ansible22`.
New tests should be added to the `paternoster/test`-directory.
Please refer to the [pytest-documentation](http://doc.pytest.org/) for
further details.

### Integration Tests

Some features (like the `become_root` function) require a correctly
setup linux environment. They can be tested using the provided ansible
playbooks in `vagrant/tests`.

The playbooks can be invoked using the `run_integration_tests.py`-utility:

```
$ ./vagrant/run_integration_tests.py --file test_variables.yml
=== running test_variables.yml with ansible>=2.1,<2.2
=== running test_variables.yml with ansible>=2.2,<2.3
=== running test_variables.yml with ansible>=2.3,<2.4
$ ./vagrant/run_integration_tests.py ansible22 --file test_variables.yml
=== running test_variables.yml with ansible>=2.2,<2.3
$ ./vagrant/run_integration_tests.py --help
usage: run_integration_tests.py [-h] [--file FILE]
                                [{ansible21,ansible22,ansible23,all}]

Run paternoster integration tests.

(...)
```

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

## Releasing a new version

Assuming you have been handed the required credentials, a new version
can be released as follows.

1. adapt the version in `setup.py`, according to [semver](http://semver.org/)
2. commit this change as `Version 1.2.3`
3. tag the resulting commit as `v1.2.3`
4. push the new tag as well as the `master` branch
5. update the package on PyPI:

```
rm dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
```

# License

All code in this repository (including this document) is licensed under
the MIT license. The logo (both the png and svg versions) is licensed
unter the [CC-BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) license.

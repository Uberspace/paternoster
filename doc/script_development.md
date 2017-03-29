# Script Development

A typical boilerplate for Paternoster looks like this:

```yml
#!/usr/bin/env paternoster

- hosts: paternoster
  vars:
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

Inside `vars` the following values can be set:

* `parameters`: command line parameters to parse, check and pass on to ansible
* `become_user`: use `sudo` to execute the playbook as the given user (e.g. `root`)
* `check_user`: check that the user running the script is the one given here
* `success_msg`: print this message once the script as exited successfully

## Parameters

Each parameter is represented by a dictionary within the `patermeters` list.
The values supplied there are passed onto pythons [`add_argument()`-function](https://docs.python.org/2/library/argparse.html#the-add-argument-method),
except for a few special ones:

| Name | Description |
| ---- | ----------- |
| `name` | `--long` name on the command line |
| `short` | `-s`hort name on the command line |
| `type` | a class, which is parse and validate the value given by the user |
| `type_params` | optional parameters for the type class |
| `depends_on` | makes this argument depend on the presence of another one |
| `positional` | indicates whether the argument is a `--keyword` one (default) or positional. Must not be supplied together with `required'. |

All arguments to the script are passed to ansible as variables with the
`param_`-prefix. This means that `--domain foo.com` becomes the variable
`param_domain` with value `foo.com`.

There are a few special variables to provide the playbook further
details about the environment it's in:

| Name | Description |
| ---- | ----------- |
| `sudo_user` | the user who executed the script originally. If the script is not configured to run as root, this variable does not exist. |
| `script_name` | the filename of the script, which is currently executed (e.g. `uberspace-add-domain`) |

### Types

In general the type-argument is mostly identical to the one supplied to
the python function [`add_argument()`](https://docs.python.org/2/library/argparse.html#type).
To enforce a certain level of security, **all strings must be of the type
`restricted_str`**. It is not possible to add an string argument, which
does not have a defined set of characters. In addtion to `restricted_str`
Paternosters adds a couple of other special types, which can be used by
referencing them as `paternoster.types.<name>`, after importing
`paternoster.types`.

| Name | Category | Description |
| ---- | -------- | ----------- |
| `domain` | factory | a domain with valid length, format and tld |
| `restricted_str` | factory | string which only allows certain characters given in regex-format (e.g. `a-z0-9`). Alternatively a regex can be supplied using the `regex`-parameter. This regex must be anchored. Additonally a `minlen` (default `1`) and `maxlen` (default `255`) can be passed to restrict the strings length. |
| `restricted_int` | factory | integer which can be restricted by a `minimum` and `maximum`-value, both of which are inclusive |

All custom types fall into one of two categories: "normal" or "factory":

* Normal types can be supplied just as they are: `'type': paternoster.types.domain`.
* Factory types require additional parameters to work properly: `'type': paternoster.types.restricted_str('a-z0-9')`.

### Dependencies

In some cases a parameter may need another one to function correctly. A
real-life example of this might be the `--namespace` parameter, which
depends on the `--mailserver` parameter in `uberspace-add-domain`. Such
a dependency can be expressed using the `depends`-option of a pararmeter:

```yml
parameters:
  - name: mailserver
    short: m
    help: add domain to the mailserver configuration
    action: store_true
  - name: namespace
    short: e
    help: use this namespace when adding a mail domain
    type: paternoster.types.restricted_str
    type_params:
      allowed_chars: a-z0-9
    depends_on: mailserver
```

## Status Reporting

There are multiple ways to let the user know, what's going on:

### Failure

You can use the [`fail`-module](http://docs.ansible.com/ansible/fail_module.html)
to display a error message to the user. The `msg` option will be written
to stderr as-is, followed by an immediate exit of the script with exit-
code `1`.

### Success

To display a customized message when the playbook executes successfully
just set the `success_msg`-attribute of `Paternoster`, just as demonstrated
in the boilerplate above. The message will be written to stdout as-is.
This behavior can be disabled by passing `""` or `None` as the `success_msg`.

### Progress Messages

If you want to inform the user about the current task your playbook is
executing, you can use the [`debug`-module](http://docs.ansible.com/ansible/debug_module.html).
All messages sent by this module are written to stdout as-is. Note that
only messages with the default `verbosity` value will be shown. All
other verbosity-levels can be used for actual debugging.

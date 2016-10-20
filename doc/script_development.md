# Script Development

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

In this case the `auto()`-method-call executes all neccesary steps (become
root, parse arguments, execute playbook) at once. Which user should ultimately
execute the script is determined by these three parameters:

* `become_user`: string; execute as the given user, e.g. `nginx`
* `become_root`: boolean; execute as root, alias for `become_user='root'`
* `check_root`: boolean; abort, if the user is not already root

Note that these parameters are mutually exclusive.

## Parameters

All parameters are represented by a tuple of `('longname', 'shortname', {})`.
Long- and shortname are the respective `--long` and `-s`hort command line
arguments, followed by a dictionary supplying addtional values. Within
the dict all parameters to pythons [`add_argument()`-function](https://docs.python.org/2/library/argparse.html#the-add-argument-method) can be used.
Only the most important ones are listed here:

| Name | Description |
| ---- | ----------- |
| `help` | short text to describe the parameter in more detail |
| `type` | used to sanity-check the given value (e.g. "is this really a domain?") |
| `action` | can be used to create flag-arguments, when set to `store_true` or `store_false` |
| `required` | enforce the presence of certain argments |

There is a small number of arguments added by Paternoster:

| Name | Description |
| ---- | ----------- |
| `depends` | makes this argument depend on the presence of another one |

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

### Custom Types

Just like Paternosters implemets a couple custom types, the developer of
a script can do the same. The argparse library is very flexible in this
regard, so it should even be possible to parse and validate x.509-certificates,
before passing their content to ansible, instead of their path.

For further details refer to the `types.py`-file within Paternoster or
the [documentation of argparse itself](https://docs.python.org/2/library/argparse.html#type).

### Dependencies

In some cases a parameter may need another one to function correctly. A
real-life example of this might be the `--namespace` parameter, which
depends on the `--mailserver` parameter in `uberspace-add-domain`. Such
a dependency can be expressed using the `depends`-option of a pararmeter:

```
parameters=[
  ('mailserver', 'm', {
    'help': 'add domain to the mailserver configuration',
    'action': 'store_true'
  }),
  ('namespace', 'e', {
    'help': 'use this namespace when adding a mail domain',
    'type': paternoster.types.restricted_str('a-z0-9'),
    'depends': 'mailserver',
  }),
]
```

At the moment there can only be a single dependency.

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

## Variables

All arguments to the script are passed to ansible as variables with the
`param_`-prefix. This means that `--domain foo.com` becomes the variable
`param_domain` with value `foo.com`.

There are a few special variables to provide the playbook further
details about the environment it's in:

| Name | Description |
| ---- | ----------- |
| `sudo_user` | the user who executed the script originally. If the script is not configured to run as root, this variable does not exist. |
| `script_name` | the filename of the script, which is currently executed (e.g. `uberspace-add-domain`) |

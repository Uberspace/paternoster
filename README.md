# UberScript

This python library provides an easy and safe way to let ordinary users
execute ansible playbooks as root.

# Theory of Operation

The developer writes a small python script (10-30 lines, mostly
definitions) which initializes UberScript. Following a method call the
library takes over, parses user-given arguments, validates their
contents and passes them on to a given ansible playbook via the ansible
python module. All parameters are checked for proper types (including
more complicated checks like domain-validity).

## Security

This library is a small-ish wrapper around pythons battle-tested [argparse](https://docs.python.org/2/library/argparse.html)
and the ansible api. Arguments are passed to argparse for evaluation.
All standard-types like integers are handled by the python standard
library. Special types like domains are implemented within UberScript.
Once argparse has finished UberScript relies on the ansible API to
execute the given playbook. All parameters are passed safely as variables.

Before parsing parameters UberScript executes itself as root via sudo.
Combined with a proper sudoers-config this ensures that the script has
not been copied somewhere else is unmodified.

# Script-Development

A typical boilerplate for UberScript looks like this:

```python
#!/bin/env python2

import uberscript
import uberscript.types

uberscript.UberScript(
  playbook='/opt/uberspace/playbooks/user/add_domain.yml',
  parameters=[
    ('domain', 'd', {
      'help': 'this is the domain to add to your uberspace',
      'type': uberscript.types.domain,
    }),
  ],
).auto()
```

The `auto()`-method-call executes all neccesary steps (become root, parse
arguments, execute playbook) at once. Becoming root can be skipped by
calling the method like `auto(root=False)`.

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

There is a small number of arguments added by UberScript:

| Name | Description |
| ---- | ----------- |
| `depends` | makes this argument depend on the presence of another one |

### Types

In general the type-argument is identical to the one supplied to the
python function [`add_argument()`](https://docs.python.org/2/library/argparse.html#type).
UberScript only adds a couple of special types, which can be used by
referencing the as `uberscript.types.<name>`.

| Name | Category | Description |
| ---- | -------- | ----------- |
| `domain` | normal | a domain with valid length, format and tld |
| `restricted_str` | factory | string which only allows certain characters given in regex-format (e.g. `a-z0-9`) |

All custom types fall into one of two categories: "normal" or "factory".
Normal types can be supplied just as they are: `'type': uberscript.types.domain`.
Factory types require additional parameters to work properly: `'type': uberscript.types.restricted_str('a-z0-9')`.

### Custom Types

Just like UberScripts implemets a couple custom types, the developer of
a script can do the same. The argparse library is very flexible in this
regard, so it should even be possible to parse and validate x509-certificates,
before passing their content to ansible, instead of their path.

For further details refer to the `types.py`-file within UberScript or
the [documentation of argparse itself](https://docs.python.org/2/library/argparse.html#type).

# Library-Development

This project uses python 2.7, because python 3.x is not supported by
ansible. It is tested using pytest. There are both unit and end-to-end
tests.

## Setup
To get a basic environment up and running, use the following commands:

```bash
virtualenv venv --python python2
source venv/bin/activate
python setup.py develop
```

Most features can be tested using a virtualenv only. If your development
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
[vagrant@localhost ~]$ uberspace-add-domain -d a.com

PLAY [test play] ************** (...)
```

If you want to add your own scripts, just add the corresponding files in
`vagrant/files/playbooks` and `vagrant/files/scripts`. You can deploy it
using the `ansible-playbook vagrant/site.yml --tags scripts` command.

## Tests
The functionality of this library can be tested using pytest:
`py.test uberscript`. New tests should be added to the `uberscript/test`-
directory.

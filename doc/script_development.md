# Script Development

A typical boilerplate for Paternoster looks like this:

```yml
#!/usr/bin/env paternoster

- hosts: paternoster
  vars:
    success_msg: "all good!"
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
* `success_msg`: print this message once the script has exited successfully
* `description`: a short description of the script's purpose (for `--help` output)

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
| `positional` | indicates whether the argument is a `--keyword` one (default) or positional. Must not be supplied together with `required`. |
| `prompt` | prompt the user for input, if the argument is not supplied. If the argument is `required`, it has to be set on the command line though. You can set this to _True_ to use the default prompt, or to a (non empty) _string_ to supply your own. |
| `prompt_options` | dictionary conatining optional settings for the prompt |

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
This means that all standard python types (e.g. `int`) can be used. Since
the input validation is quite weak on these types, paternoster supplies
a number of additional types. They can be referenced like `paternoster.types.<name>`.

#### `restricted_string`

To enforce a certain level of security, all strings must be of the type
`restricted_str`. This standard python `str` or `unicode` types may not
be used. This forces the developer the make a choice about the characters,
length and format of the given input.

```yml
type: paternoster.types.restricted_str
type_params:
  # Either `regex` or `allowed_chars` must be supplied, but not both.
  # anchored regular expression, which user input must match
  regex: "^[a-z][a-z0-9]+$"
  # regex character class, which contains all valid characters
  allowed_chars: a-zab
  # minimum length of a given input (defaults to 1), optional
  minlen: 5
  # maximum length of a given input (defaults to 255), optional
  maxlen: 30
```

#### `restricted_int`

Integer which can optionally be restricted by a minimum as well as a maximum
value. Both of these values are inclusive.

```yml
type: paternoster.types.restricted_int
type_params:
  minimum: 0
  maximum: 30
```

#### `domain`

A fully qualified domain name with valid length, format and TLD.

```yml
type: paternoster.types.domain
type_params:
  # whether to allow domains like "*.domain.com", defaults to false
  wildcard: true
```

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

### Prompt Options

| Name | Description |
| ---- | ----------- |
| `strip` | if _True_, remove whitespace at the start and end of the user input. |
| `empty` | if _True_, allow empty input. The default is to keep prompting until a non empty input is recieved. |
| `confirm` | ask for input confirmation (user has to repeat the entry). You can set this to _True_ to use the default prompt, or to a (non empty) _string_ to supply your own.
| `confirm_error` | use this (non empty) _string_ as error message if confirmation fails, instead of the default. |

## Status Reporting

There are multiple ways to let the user know, what's going on:

### Failure

You can use the [`fail`-module](http://docs.ansible.com/ansible/fail_module.html)
to display a error message to the user. The `msg` option will be written
to stderr as-is, followed by an immediate exit of the script with exit-
code `1`.

### Success

To display a customized message when the playbook executes successfully
just set the `success_msg`-variable, as demonstrated in the boilerplate above.
The message will be written to stdout as-is.

### Progress Messages

If you want to inform the user about the current task your playbook is
executing, you can use the [`debug`-module](http://docs.ansible.com/ansible/debug_module.html).
All messages sent by this module are written to stdout as-is. Note that
only messages with the default `verbosity` value will be shown. All
other verbosity-levels can be used for actual debugging.

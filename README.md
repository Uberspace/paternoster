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

# Development

This project uses python 2.7, because python 3.x is not supported by
ansible. It is tested using pytest. There are both unit and end-to-end
tests.

## Setup
To get a basic environment up and running, use the following commands:

```
virtualenv venv --python python2
source venv/bin/activate
pip install -r requirements.txt
```

## Tests
The functionality of this library can be tested using pytest:

```
```

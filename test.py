#!/bin/env python

import uberscript
import uberscript.types

s = uberscript.UberScript(
  playbook='add_domain.yml',
  parameters=[
    ('domain', 'd', {
      'help': 'this is the domain to add to your uberspace',
      'type': uberscript.types.domain,
      'required': True,
    }),
    ('webserver', 'w', {
      'help': 'add domain to the webserver configuration',
      'action': 'store_true',  # https://docs.python.org/3/library/argparse.html#action
    }),
    ('mailserver', 'm', {
      'help': 'add domain to the mailserver configuration',
      'action': 'store_true'
    }),
    ('namespace', 'e', {
      'help': 'use this namespace when adding a mail domain',
      'type': uberscript.types.restricted_str('a-z0-9'),
      'depends': 'mailserver',
    }),
    ('quiet', 'q', {
      'help': 'quiet (no output)',
      'action': 'store_true',
    }),
  ],
)

s.become_root()
s.parse_args()
s.execute_playbook()

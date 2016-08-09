import os
import sys
import re


def become_root():
  if os.geteuid() != 0:
    # flush output buffers. Otherwise the output before the
    # become_root()-call might be never shown to the user
    sys.stdout.flush()
    sys.stderr.flush()
    # -n disables password prompt, when sudo isn't configured properly
    os.execv('/usr/bin/sudo', ['/usr/bin/sudo', '-n', '--'] + sys.argv)
  else:
    sudouser = os.environ.get('SUDO_USER', None)
    # $SUDO_USER is set directly by sudo, so users should not be alble
    # to trick here. Better be safe, than sorry, though.
    if sudouser and re.match('[a-z][a-z0-9]{0,20}', sudouser):
      return sudouser
    else:
      raise ValueError('invalid username: "{}"'.format(sudouser))


def check_root():
  return os.geteuid() == 0

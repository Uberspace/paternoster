import os
import os.path
import sys
import pwd
import re


def become_user(user):
    if os.geteuid() != pwd.getpwnam(user).pw_uid:
        # flush output buffers. Otherwise the output before the
        # become_root()-call might be never shown to the user
        sys.stdout.flush()
        sys.stderr.flush()

        # resolve symlinks, so the path given in sudo-config matches
        realme = os.path.realpath(sys.argv[0])

        # -n disables password prompt, when sudo isn't configured properly
        os.execv('/usr/bin/sudo', ['/usr/bin/sudo', '-u', user, '-n', '--', realme] + sys.argv[1:])
    else:
        sudouser = os.environ.get('SUDO_USER', None)
        # $SUDO_USER is set directly by sudo, so users should not be alble
        # to trick here. Better be safe, than sorry, though.
        if sudouser and re.match('^[a-z][a-z0-9]{0,20}$', sudouser):
            return sudouser
        else:
            raise ValueError('invalid username: "{}"'.format(sudouser))


def check_user(user):
    return os.geteuid() == pwd.getpwnam(user).pw_uid

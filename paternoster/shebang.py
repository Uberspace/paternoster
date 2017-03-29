# this code is executed when paternoster is used as
# part of a shebang line, at the beginning of a script.

from __future__ import absolute_import

import sys
import os.path
import yaml
import argparse

import paternoster
import paternoster.types
from paternoster.runners.ansiblerunner import AnsibleRunner


def _load_playbook(path):
    with open(path) as f:
        playbook = yaml.load(f)

    assert type(playbook) == list
    return playbook


def _find_paternoster_config(playbook):
    assert len(playbook) > 0, "no plays found in playbook"
    play = playbook[0]
    assert type(play) == dict
    assert play.get('hosts', None) == 'paternoster', "paternoster play could not be found"
    assert 'vars' in play
    return play['vars']


def main():
    playbookpath = os.path.abspath(sys.argv[1])
    playbook = _load_playbook(playbookpath)
    config = _find_paternoster_config(playbook)

    sys.argv = [playbookpath] + sys.argv[2:]

    s = paternoster.Paternoster(
        runner_parameters={'playbook': playbookpath},
        **config
    ).auto()

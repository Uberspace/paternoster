#!/usr/bin/env python

import argparse
import os.path
import subprocess
try:
    from ConfigParser import ConfigParser as ConfigParser
except:
    from configparser import ConfigParser as ConfigParser


TOX_INI_PATH = '../tox.ini'
TESTS_DIR = 'tests'
IGNORED_TESTS = ['drop_script.yml']


def _abs_path(path):
    if os.path.isabs(path):
        return path
    here = os.path.dirname(__file__)
    toxini = os.path.join(here, path)
    return os.path.abspath(toxini)


def _ansible_versions():
    p = ConfigParser()
    p.read(_abs_path(TOX_INI_PATH))
    deps = p.get('testenv', 'deps').split('\n')
    deps = [d.split(':') for d in deps if d.startswith('ansible') and ':' in d]
    deps = [(d[0], d[1].strip()[len('ansible'):]) for d in deps]
    return dict(deps)


def _run_command(cmd):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = proc.communicate()
    return (proc.returncode, out)


def _run_file(path, ansible_versions):
    orig_path = path
    testpath = os.path.join(_abs_path(TESTS_DIR), path)
    if not os.path.exists(path) and os.path.exists(testpath):
        path = testpath

    path = _abs_path(path)

    os.chdir(_abs_path('..'))

    for v in ansible_versions:
        print('=== running {} with ansible{}'.format(orig_path, v))
        cmd = "ansible-playbook {} -e install_ansible_version='{}'".format(path, v)
        rc, out = _run_command(cmd)
        if rc != 0:
            print(out)


def _run_all(ansible_versions):
    tests = _abs_path(TESTS_DIR)
    for f in os.listdir(tests):
        if f not in IGNORED_TESTS:
            _run_file(f, ansible_versions)


def main():
    ansible_versions = _ansible_versions()
  
    parser = argparse.ArgumentParser(description='Run paternoster integration tests.')
    parser.add_argument('ansible', nargs='?', choices=list(ansible_versions.keys()) + ['all'], default='all')
    parser.add_argument('--file', help='test file to run, otherwise run all')
    args = parser.parse_args()
    
    if args.ansible == 'all':
        ansible_versions = _ansible_versions().values()
    else:
        ansible_versions = [_ansible_versions()[args.ansible]]

    if args.file:
        _run_file(args.file, ansible_versions)
    else:
        _run_all(ansible_versions)

if __name__ == '__main__':
    main()

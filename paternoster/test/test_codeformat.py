import os
import os.path
import pep8


def test_pep8_conformance():
    pep8style = pep8.StyleGuide(quiet=True, config_file=os.path.join(os.path.dirname(__file__), '../../tox.ini'))
    source_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    assert pep8style.check_files([source_path]).total_errors == 0

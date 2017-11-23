import os
import os.path

import pycodestyle


def test_pep8_conformance():
    test_path = os.path.dirname(__file__)
    styleguide = pycodestyle.StyleGuide(
        config_file=os.path.join(test_path, '../../tox.ini'),
        quiet=True,
    )
    source_path = os.path.realpath(os.path.join(test_path, '..'))
    assert styleguide.check_files([source_path]).total_errors == 0

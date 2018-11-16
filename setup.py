from __future__ import print_function
import sys

try:
    from setuptools import setup
except ImportError:
    print("Paternoster needs setuptools.", file=sys.stderr)
    print("Please install it using your package-manager or pip.", file=sys.stderr)
    sys.exit(1)

setup(name='paternoster',
      version='2.5.6',
      description='Paternoster provides users with the ability to run certain tasks as '
                  'root or another user, while ensuring safety by providing a common '
                  'interface and battle tested parameter parsing/checking.',
      author='uberspace.de',
      author_email='hallo@uberspace.de',
      url='https://github.com/uberspace/paternoster',
      packages=[
          'paternoster',
          'paternoster.runners',
          'paternoster.types',
      ],
      entry_points = {
          'console_scripts': ['paternoster=paternoster.shebang:main'],
      },
      install_requires=[
          'tldextract>=2.0.1',
          'six',
      ],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'Topic :: System :: Systems Administration',
          'Topic :: Security',
          'Topic :: Utilities',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.6',
      ],
      zip_safe=True,
      )

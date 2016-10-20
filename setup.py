from __future__ import print_function
import sys

try:
    from setuptools import setup
except ImportError:
    print("Paternoster needs setuptools.", file=sys.stderr)
    print("Please install it using your package-manager or pip.", file=sys.stderr)
    sys.exit(1)

setup(name='paternoster',
      version='0.2.0',
      description='Paternoster provides users with the ability to run certain tasks as '
                  'root or another user, while ensuring safety by providing a common '
                  'interface and battle tested parameter parsing/checking.',
      author='uberspace.de',
      author_email='hallo@uberspace.de',
      url='https://github.com/uberspace/paternoster',
      packages=[
          'paternoster',
          'paternoster.runners',
      ],
      install_requires=[
          'tldextract>=2.0.1',
          'ansible==2.1.1.0',
          'six',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'Topic :: System :: Systems Administration',
          'Topic :: Security',
          'Topic :: Utilities',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 2 :: Only',
      ],
      zip_safe=True,
      )

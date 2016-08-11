from setuptools import setup

setup(name='paternoster',
      version='0.1',
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
        'pytest>=2.9.2',
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
      zip_safe=False,
      )

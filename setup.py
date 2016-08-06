from setuptools import setup

setup(name='uberscript',
      version='0.1',
      description='',
      author='Michael Lutonsky',
      author_email='ml@jonaspasche.com',
      packages=[
        'uberscript',
        'uberscript.runners',
      ],
      install_requires=[
        'tldextract>=2.0.1',
        'ansible==2.1.1.0',
        'pytest>=2.9.2',
      ],
      zip_safe=False)

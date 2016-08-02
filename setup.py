from setuptools import setup

setup(name='uberscript',
      version='0.1',
      description='',
      author='Michael Lutonsky',
      author_email='ml@jonaspasche.com',
      packages=['uberscript'],
      install_requires=[
        'tldextract==2.0.1',
        'ansible==2.1.1.0',
      ],
      zip_safe=False)

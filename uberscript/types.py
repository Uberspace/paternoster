import re

import tldextract


def domain(val):
  val = val.encode('idna').decode('ascii')

  if any(map(lambda p: len(p) > 63, val.split('.'))) or len(val) > 255:
    raise ValueError('domain too long')
  if not re.match(r'^([a-zA-Z0-9](?:(?:[a-zA-Z0-9-]*|(?<!-)\.(?![-.]))*[a-zA-Z0-9]+)?)$', val):
    raise ValueError('invalid domain')
  if not tldextract.extract(val).suffix:
    raise ValueError('invalid domain suffix')

  return val

class restricted_str:
  __name__ = 'string'

  def __init__(self, allowed_chars):
    self.regex = re.compile('^[{}]+$'.format(allowed_chars))

  def __call__(self, val):
    if not self.regex.match(val):
      raise ValueError('invalid value')
    return val

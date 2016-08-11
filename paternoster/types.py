import re

import tldextract


class domain:
  __name__ = 'domain'
  DOMAIN_REGEX = r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'

  def __init__(self, wildcard=False):
    self._wildcard = wildcard

  def __call__(self, val):
    val = val.encode('idna').decode('ascii')
    domain = val

    if self._wildcard and val.startswith('*.'):
      val = val[2:]

    if any(map(lambda p: len(p) > 63, val.split('.'))) or len(val) > 255:
      raise ValueError('domain too long')
    if not re.match(self.DOMAIN_REGEX, val):
      raise ValueError('invalid domain')
    if not tldextract.extract(val).suffix:
      raise ValueError('invalid domain suffix')

    return domain


class restricted_str:
  __name__ = 'string'

  def __init__(self, allowed_chars, minlen=1, maxlen=255):
    if minlen is not None and maxlen is not None and minlen > maxlen:
      raise ValueError('minlen must be smaller than maxlen')

    # construct a regex matching a arbitrary number of characters within
    # the given set.
    self.regex = re.compile('^[{}]+$'.format(allowed_chars))
    self.minlen = minlen
    self.maxlen = maxlen

  def __call__(self, val):
    if self.maxlen is not None and len(val) > self.maxlen:
      raise ValueError('string is too long (must be <= {})'.format(self.maxlen))
    if self.minlen is not None and len(val) < self.minlen:
      raise ValueError('string is too short (must be >= {})'.format(self.minlen))
    if not self.regex.match(val):
      raise ValueError('invalid value')
    return val


class restricted_int:
  __name__ = 'integer'

  def __init__(self, minimum=None, maximum=None):
    if minimum is not None and maximum is not None and minimum > maximum:
      raise ValueError('minimum must be smaller than maximum')

    self.minimum = minimum
    self.maximum = maximum

  def __call__(self, val):
    try:
      val = int(val)
    except TypeError:
      raise ValueError('invalid integer')

    if self.minimum is not None and val < self.minimum:
      raise ValueError('value too small (must be >= {})'.format(self.minimum))
    if self.maximum is not None and val > self.maximum:
      raise ValueError('value too big (must be <= {})'.format(self.maximum))

    return val

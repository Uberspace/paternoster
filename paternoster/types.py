import re
import tldextract


class domain:
    __name__ = 'domain'
    DOMAIN_REGEX = r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'  # noqa

    def __init__(self, wildcard=False):
        self._wildcard = wildcard

    def __call__(self, val):
        val = val.encode('idna').decode('ascii')
        domain = val

        if self._wildcard and val.startswith('*.'):
            val = val[2:]

        extracted = tldextract.TLDExtract(suffix_list_urls=[])(val)

        if any(map(lambda p: len(p) > 63, val.split('.'))) or len(val) > 255:
            raise ValueError('domain too long')
        if val.count('.') < 1:
            raise ValueError('domain has too few components')
        if not re.match(self.DOMAIN_REGEX, val):
            raise ValueError('invalid domain')
        if not extracted.suffix:
            raise ValueError('invalid domain suffix')
        if not extracted.domain:
            raise ValueError('invalid domain')

        return domain


class restricted_str:
    __name__ = 'string'

    def __init__(self, allowed_chars=None, regex=None, minlen=1, maxlen=255):
        if minlen is not None and maxlen is not None and minlen > maxlen:
            raise ValueError('minlen must be smaller than maxlen')
        if not allowed_chars and not regex:
            raise ValueError('either allowed_chars or regex must be supplied')
        if allowed_chars and regex:
            raise ValueError('allowed_chars or regex are mutally exclusive')

        if allowed_chars:
            # construct a regex matching a arbitrary number of characters within
            # the given set.
            self._regex = re.compile('^[{}]+$'.format(allowed_chars))
        elif regex:
            if not regex.startswith('^') or not regex.endswith('$'):
                raise ValueError('regex must be anchored')

            self._regex = re.compile(regex)

        self._minlen = minlen
        self._maxlen = maxlen

    def __call__(self, val):
        if self._maxlen is not None and len(val) > self._maxlen:
            raise ValueError('string is too long (must be <= {})'.format(self._maxlen))
        if self._minlen is not None and len(val) < self._minlen:
            raise ValueError('string is too short (must be >= {})'.format(self._minlen))
        if not self._regex.match(val):
            raise ValueError('invalid value')
        return val


class restricted_int:
    __name__ = 'integer'

    def __init__(self, minimum=None, maximum=None):
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError('minimum must be smaller than maximum')

        self._minimum = minimum
        self._maximum = maximum

    def __call__(self, val):
        try:
            val = int(val)
        except TypeError:
            raise ValueError('invalid integer')

        if self._minimum is not None and val < self._minimum:
            raise ValueError('value too small (must be >= {})'.format(self._minimum))
        if self._maximum is not None and val > self._maximum:
            raise ValueError('value too big (must be <= {})'.format(self._maximum))

        return val

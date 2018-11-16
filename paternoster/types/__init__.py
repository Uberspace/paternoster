# -*- encoding: utf8 -*-

import re
import tldextract
import six.moves.urllib as urllib
import os.path


class domain:
    __name__ = 'domain'

    DOMAIN_REGEX = r'\A(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])\Z'  # noqa

    def __init__(self, wildcard=False):
        self._wildcard = wildcard

    def __call__(self, val):
        val = val.encode('idna').decode('ascii')
        domain = val

        if '@' in domain:
            raise ValueError(
                "this looks like an email-adress, "
                "try only supplying the part after the @"
            )

        if val.endswith('.'):
            domain = val = val[:-1]

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


class uri:
    __name__ = 'URI'

    SCHEME_REGEX = r'\A[a-z][a-z0-9+.-]*\Z'
    SCHEME_MAX_LEN = 255

    PATH_REGEX = u'\\A/([a-zA-ZüäöÜÄÖß0-9._=-]+/?)*\\Z'
    PATH_MAX_LEN = 512

    def __init__(self, optional_scheme=True, optional_domain=True, domain_options={}):
        self._required = filter(bool, [
            'scheme' if not optional_scheme else None,
            'domain' if not optional_domain else None,
        ])
        self._domaincheck = domain(domain_options)

    def __call__(self, val):
        parsed = urllib.parse.urlsplit(val)

        result = {
            'scheme': parsed.scheme,
            'domain': parsed.netloc,
            'path': parsed.path,
        }

        # correctly parse scheme-less URIs like "google.com/foobar"
        if not result['domain']:
            maybedomain, _, maybepath = result['path'].partition('/')

            if '.' in maybedomain:
                result['domain'] = maybedomain
                result['path'] = maybepath

        # === check scheme
        if result['scheme']:
            if len(result['scheme']) > self.SCHEME_MAX_LEN:
                raise ValueError('scheme too long')
            elif not re.match(self.SCHEME_REGEX, result['scheme']):
                raise ValueError('invalid scheme')

            result['scheme'] = result['scheme'].lower()

        # === check domain
        if result['domain']:
            result['domain'] = self._domaincheck(result['domain'])

        # === check path
        result['path'] = '/' + result['path'].lstrip('/')
        if len(result['path']) > self.PATH_MAX_LEN:
            raise ValueError('path too long')
        elif not re.match(self.PATH_REGEX, result['path']):
            raise ValueError('invalid path')

        # normalize falsy values
        result = {k: v if v else '' for k, v in result.items()}

        missing = [k for k in self._required if not result[k]]
        if missing:
            raise ValueError('missing ' + ', '.join(missing))

        if result['scheme']:
            result['full'] = u'{scheme}://{domain}{path}'.format(**result)
        else:
            result['full'] = u'{domain}{path}'.format(**result)

        return result


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
            self._regex = re.compile(r'\A[{}]+\Z'.format(allowed_chars))
        elif regex:
            if not regex.startswith('^') or not regex.endswith('$'):
                raise ValueError('regex must be anchored')

            # replace $ at the end with \Z, so we can't match "a\n" for "^a$"
            regex = r'\A' + regex[1:-1] + r'\Z'
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
        if minimum is not None:
            try:
                minimum = int(minimum)
            except (ValueError, TypeError):
                raise ValueError('minimum is not a integer')

        if maximum is not None:
            try:
                maximum = int(maximum)
            except (ValueError, TypeError):
                raise ValueError('maximum is not a integer')

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


__all__ = [
    'domain',
    'restricted_int',
    'restricted_str',
]

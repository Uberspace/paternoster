# -*- coding: utf-8 -*-

import pytest


@pytest.mark.parametrize("value,wildcard,valid", [
    ("uberspace.de", False, True),
    ("foo.google", False, True),
    ("foo.de\n", False, False),
    ("foo.de\nbar.com", False, False),
    (u"foobär.com", False, True),
    ("uberspace.deee", False, False),
    ("-bla.com", False, False),
    ("a42'.com", False, False),
    ('some"thing.com', False, False),
    ("*.google.at", False, False),
    ("*.google.at", True, True),
    ("foo.*.google.at", True, False),
    ("foo.*", True, False),
    ('someth\x00ing.com', False, False),
    ('something', False, False),
    ('*.de', True, False),
    ('*', True, False),
    ('*.*.de', True, False),
    ('*.', True, False),
    ("a" * 65 + ".com", False, False),
    (("a" * 40 + '.') * 8 + "com", False, False),
    ('', False, False),
])
def test_type_domain(value, wildcard, valid):
    from ..types import domain

    check = domain(wildcard)

    if not valid:
        with pytest.raises(ValueError):
            check(value)
    else:
        check(value)


@pytest.mark.parametrize("allowed_chars,regex,minlen,maxlen,value,valid", [
    ("a-z", None, None, None, "aaaaaabb", True),
    ("a-z", None, None, None, "aaaaaabb2", False),
    ("a-z", None, None, None, "aaaa\n", False),
    ("a-z", None, None, None, "aaaa\nbb", False),
    ("b", None, None, None, "bbbb", True),
    ("b", None, None, None, "a", False),
    ("a-z0-9", None, None, None, "aaaaaabb2", True),
    ("a", None, 3, None, "a" * 2, False),
    ("a", None, None, 5, "a" * 5, True),
    ("a", None, None, 5, "a" * 6, False),
    ("a", None, 3, 5, "a" * 4, True),
    ("a-z", None, None, None, "aaaaaabb", True),
    (None, '^[a-z]$', None, None, "a", True),
    (None, '^[a-z]$', None, None, "aa", False),
    (None, '^a$', None, None, "a\n", False),
])
def test_type_restricted_str(allowed_chars, regex, minlen, maxlen, value, valid):
    from ..types import restricted_str

    check = restricted_str(allowed_chars=allowed_chars, regex=regex, minlen=minlen, maxlen=maxlen)

    if not valid:
        with pytest.raises(ValueError):
            check(value)
    else:
        check(value)


@pytest.mark.parametrize('allowed_chars,regex,minlen,maxlen,valid', [
    ("a", None, 100, 0, False),
    ("a", "^aa$", None, None, False),
    (None, "a", None, None, False),
    (None, "^a", None, None, False),
    (None, "a$", None, None, False),
])
def test_type_restricted_str_ctor(allowed_chars, regex, minlen, maxlen, valid):
    from ..types import restricted_str

    if not valid:
        with pytest.raises(ValueError):
            restricted_str(allowed_chars=allowed_chars, regex=regex, minlen=minlen, maxlen=maxlen)
    else:
        restricted_str(allowed_chars=allowed_chars, regex=regex, minlen=minlen, maxlen=maxlen)


def test_type_restricted_str_minlen_default():
    from ..types import restricted_str

    with pytest.raises(ValueError):
        restricted_str("a")("")


def test_type_restricted_str_maxlen_default():
    from ..types import restricted_str

    with pytest.raises(ValueError):
        restricted_str("a")("a" * 256)


@pytest.mark.parametrize("minimum,maximum,value,valid", [
    (0, 100, "a", False),
    (0, 100, "", False),
    (0, 100, None, False),
    (0, 100, "50", True),
    (0, 100, "50.5", False),
    (0, 100, 50, True),
    (0, 100, 50, True),
    (0, 100, 0, True),
    (0, 100, -1, False),
    (0, 100, 100, True),
    (0, 100, 101, False),
    (None, 100, 101, False),
    (0, None, -1, False),
    (None, 100, 99, True),
    (0, None, 1, True),
    (None, 100, -1000, True),
    (0, None, 1000, True),
])
def test_restricted_int(minimum, maximum, value, valid):
    from ..types import restricted_int

    check = restricted_int(minimum, maximum)

    if not valid:
        with pytest.raises(ValueError):
            check(value)
    else:
        check(value)


def test_range_int_ctor():
    from ..types import restricted_int

    with pytest.raises(ValueError):
        restricted_int(100, 0)


def test_range_int_ctor_types_min():
    from ..types import restricted_int

    with pytest.raises(ValueError):
        restricted_int(minimum="foo")


def test_range_int_ctor_types_max():
    from ..types import restricted_int

    with pytest.raises(ValueError):
        restricted_int(maximum="bar")

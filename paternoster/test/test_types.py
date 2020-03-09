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
    ('example.com.', False, True),
    ('example.com..', False, False),
    ('*.example.com.', True, True),
    ('.', False, False),
])
def test_type_domain(value, wildcard, valid):
    from ..types import domain

    check = domain(wildcard)

    if not valid:
        with pytest.raises(ValueError):
            check(value)
    else:
        check(value)


def test_type_domain_detect_email():
    from ..types import domain

    with pytest.raises(ValueError) as exc:
        domain()('foo@bar.com')
    assert 'this looks like an email-adress' in str(exc.value)


def test_type_domain_maxlen():
    from ..types import domain

    d_name = (
        'abc.def.ghi.klmn.opq.rst.uvw.xyz.now.you.know.my.abc.next.time.just.'
        'sing.the.xxxx.with.me.because.if.you.dont.i.will.literally.xxxx.xxx.'
        'you.xxxxxxx.xxxxx.lets.try.again.shall.we.abc.def.ghi.klmn.opq.rst.'
        'uvw.xyz.xxxx.were.missing.a.letter.there.someth.co'
    )

    d = domain()(d_name)
    assert d == d_name

    with pytest.raises(ValueError) as exc:
        domain(maxlen=64)(d_name)
        assert 'domain too long' in str(exc.value)


@pytest.mark.parametrize("value,wildcard,expected", [
    ("uberspace.de", False, "uberspace.de"),
    ("ubERspaCE.dE", False, "uberspace.de"),
    ("uberspace.de.", False, "uberspace.de"),
    ("*.uberspace.de", True, "*.uberspace.de"),
    ("*.uberspace.de.", True, "*.uberspace.de"),
])
def test_type_domain_return(value, wildcard, expected):
    from ..types import domain

    check = domain(wildcard)
    actual = check(value)

    assert actual == expected


@pytest.mark.parametrize("value,expected", [
    ("", {'path': '/', 'full': '/'}),
    ("/foo", {'path': '/foo', 'full': '/foo'}),
    ("/foo/", {'path': '/foo', 'full': '/foo'}),
    (u"/föö", {'path': u'/föö', 'full': u'/föö'}),
    ("/0a0", {'path': '/0a0'}),
    ("/bla.foo", {'path': '/bla.foo'}),
    ("/bla_foo", {'path': '/bla_foo'}),
    ("/bla-foo", {'path': '/bla-foo'}),
    ("/bla/foo", {'path': '/bla/foo'}),
    ("/foo bar", False),
    ('a' * 511, {'path': '/' + 'a' * 511}),
    ('a' * 512, False),
    ("uberspace.de", {'domain': 'uberspace.de'}),
    ("uberspace.de/", {'domain': 'uberspace.de', 'full': 'uberspace.de/'}),
    ("uberspace.de/bla", {'domain': 'uberspace.de', 'path': '/bla'}),
    (
        "https://uberspace.de/bla",
        {'scheme': 'https', 'domain': 'uberspace.de', 'path': '/bla', 'full': 'https://uberspace.de/bla'}
    ),
    ("https://*.uberspace.de/bla", False),
    ("uberspace.deee", False),
    ("https://", {'scheme': 'https', 'path': '/'}),
    ("https://uberspace.deee", False),
    ("https://uberspac" + "e" * 56 + ".de", False),
    ("äää://uberspace.de", False),
    ("://uberspace.de", False),
    ('a' * 255 + "://uberspace.de", {'scheme': 'a' * 255, 'domain': 'uberspace.de'}),
    ('a' * 256 + "://uberspace.de", False),
    ("https://foo://", False),
    ("https://foo://a", False),
])
def test_type_uri(value, expected):
    from ..types import uri

    check = uri()

    if expected:
        actual = check(value)

        assert 'scheme' in actual
        assert 'domain' in actual
        assert 'path' in actual

        for k, v in expected.items():
            assert actual.pop(k, None) == v, k

        assert not actual.get('schema')
        assert not actual.get('domain')
        assert 'path' not in actual or actual['path'] == '/'
    else:
        try:
            with pytest.raises(ValueError):
                x = check(value)
        finally:
            try:
                print('invalid return: {}'.format(x))
            except:  # noqa
                pass


@pytest.mark.parametrize("value,required,expected", [
    ("", ["scheme", "domain"], ["scheme", "domain"]),
    ("http://", ["scheme", "domain"], ["domain"]),
    ("google.com", ["scheme", "domain"], ["scheme"]),
    ("", ["scheme"], ["scheme"]),
    ("google.com", ["scheme"], ["scheme"]),
    ("", ["domain"], ["domain"]),
    ("https://", ["domain"], ["domain"]),
])
def test_type_uri_optional(value, required, expected):
    from ..types import uri

    args = {'optional_' + k: False for k in required}
    check = uri(**args)

    with pytest.raises(ValueError) as excinfo:
        check(value)

    msg = str(excinfo)
    assert 'missing' in msg
    for e in expected:
        assert e in msg


def test_type_uri_domain_options():
    from ..types import uri

    check = uri(domain_options={'wildcard': True})
    check('https://*.foo.com')


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

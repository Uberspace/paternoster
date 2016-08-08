# -*- coding: utf-8 -*-

import pytest


@pytest.mark.parametrize("value,valid", [
  ("uberspace.de", True),
  ("foo.google", True),
  (u"foobär.com", True),
  ("uberspace.deee", False),
  ("-bla.com", False),
  ("a42'.com", False),
  ("*.google.at", False),
  ("a" * 65 + ".com", False),
  (("a" * 40 + '.') * 8 + "com", False),
])
def test_type_domain(value, valid):
  from ..types import domain

  if not valid:
    with pytest.raises(ValueError):
      domain(value)
  else:
    domain(value)


@pytest.mark.parametrize("allowed_chars,minlen,maxlen,value,valid", [
  ("a-z", None, None, "aaaaaabb", True),
  ("a-z", None, None, "aaaaaabb2", False),
  ("b", None, None, "bbbb", True),
  ("b", None, None, "a", False),
  ("a-z0-9", None, None, "aaaaaabb2", True),
  ("a", 3, None, "a" * 2, False),
  ("a", None, 5, "a" * 5, True),
  ("a", None, 5, "a" * 6, False),
  ("a", 3, 5, "a" * 4, True),
])
def test_type_restricted_str(allowed_chars, minlen, maxlen, value, valid):
  from ..types import restricted_str

  check = restricted_str(allowed_chars, minlen, maxlen)

  if not valid:
    with pytest.raises(ValueError):
      check(value)
  else:
    check(value)


def test_type_restricted_str_ctor():
  from ..types import restricted_str

  with pytest.raises(ValueError):
    restricted_str("a", 100, 0)


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

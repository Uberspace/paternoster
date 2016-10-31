import base64
import os
from tempfile import NamedTemporaryFile

import pytest


LOCALHOST_CERT = """-----BEGIN CERTIFICATE-----
MIIFNjCCAx6gAwIBAgICA+gwDQYJKoZIhvcNAQELBQAwSzELMAkGA1UEBhMCREUx
DjAMBgNVBAgTBU1haW56MRUwEwYDVQQKEwx1YmVyc3BhY2UuZGUxFTATBgNVBAsT
DHViZXJzcGFjZS5kZTAeFw0xNjEwMjgwODU1MDZaFw0xNjExMjgwODU1MDZaMEsx
CzAJBgNVBAYTAkRFMQ4wDAYDVQQIEwVNYWluejEVMBMGA1UEChMMdWJlcnNwYWNl
LmRlMRUwEwYDVQQLEwx1YmVyc3BhY2UuZGUwggIiMA0GCSqGSIb3DQEBAQUAA4IC
DwAwggIKAoICAQDQPlhdqi9TduK4vE41TGEj/NTUOupN+m3aq/e+hmKyz/f78QpS
RmMMX7tW2j92MMWFW/R6aUl+KDM4NQM7DFLlNWhV6QUMMPCGMe26qcYm43vrczaV
dtrpZHKA0jUtaJKWKnlZ2+fU35NGRzehvShW8kFvP9hNqBjxh2AaV6hjTv64nKUI
VGgc+UkFsXlG6m48TQcsVrf05UfJ0uB+Op0smwzrA/Pu5/CfLWoCGVIwXRPC/CMW
qRs9qgQ05mUCvVJOrSYjhy+kOF4j7TovI0u4c5jEPXl9O5D6gtVRb/LAcHyyY8/y
LGJQCLlEX7mI5s4L5mtSh6UF+4GbrarU1AlSkKOIZMP8jwyuOPqHIWPNG4ALIEU8
Pbzr6cP8jlmbO16TAU9jPY3ZriDBq2/iHwPcdEDK2IVZNoc9BBM7Z92nNtIiYjRk
yQt/WGkxjmHYOIuHhEqjlnmLr+U5AwxTqJ+QvTweMGoCjP3K1qe7kJK4K+ZB4tJU
ercaNfX7rOTAwlwWh+zorgrR1VsBWnOYLAVolDQWi+c24uRG66EYy58+55snnZnb
ZVjfXMLDidcJfCaOpMqZEULOSHbHfqD8ErnjVfvr3nQ6eA+pN+EuaxzECg7h71Nk
kRRripPzfWFOKd3RHN6HZ2PhwL32F/zPq7ffAzLP5mBY5qXhTUhYyanR1wIDAQAB
oyQwIjAgBgNVHREEGTAXghVsb2NhbGhvc3QubG9jYWxkb21haW4wDQYJKoZIhvcN
AQELBQADggIBAGAGM7V0u93h096x3w2YG2QNIvsa/Zi1IGzqEA3mDZe4aWheWVjX
m4aD+iOENKX20K2n0Bu5RQr2D3/hImbPUCM2u19VmnscmaT67TBpe6dQUBz+B2Z2
LdgeHvt0mSgixPC/tNPz47PMcsLzdjPPsJWh68OicSQcbu6qR7h4/eiKH0n+TEkD
7dssDIydDVbntqUVFpnoBXys+Vx596npMw4qHSWLNcjO70Iq8hyho/8KtGaasaid
NKV5TR1KMzX0/RaweJz71eNd3f7aLYdTrRI0mOGpgOOkUG9xojF40ifsEjM2AovU
Gw+mCfGq8FLx1uK0B8jcxE0vbc9N2uOuVtyC2Uu0jxAqrjSnGpSjDQnDR6nBULbC
OnPZFeOs8+luie3d+6j4za0TezQrXfrZNMjvvNd3aFN99xj9pT8imUCxQg7J+May
HaEDVek/l/SOD+2+x890Xcq7PLW9La1jS4r+g8wiFtCewfyDdrwyO2ZHVFoUGse0
ciyGOmKfi4AtSqy89emLOkBxMcBE+2wYDaiEkLtBhF+IOrSfiqA6fTWWj8IYVYJQ
NJgCwqey7t5mAPps/zTtiS5siKWAIfBMURjiavx9+lFatWtWkkFCntP7rr7N9xkj
xo5KZaBxJUq1ns3+082UgR5NbHd1/Z5sxTfk6uqPIhxxnANmTDrX9rsT
-----END CERTIFICATE-----"""


# hey dear "BEGIN PRIVATE KEY"-greppers. Nothing to see here. :)
LOCALHOST_KEY = """-----BEGIN PRIVATE KEY-----
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
b7SP620GlNbmWazRQc51KgYnIbTbO/U=
-----END PRIVATE KEY-----"""


def _wrap_cert(val):
    return "-----BEGIN CERTIFICATE-----\n" + str(val).strip() + "\n-----END CERTIFICATE-----\n"


def _wrap_key(val):
    return "-----BEGIN PRIVATE KEY-----\n" + str(val).strip() + "\n-----END PRIVATE KEY-----\n"


@pytest.mark.parametrize("pem,opts,valid", [
    ("", {}, False),
    (_wrap_cert(""), {}, False),
    ("\0", {}, False),
    (_wrap_cert("\0"), {}, False),
    (_wrap_cert(base64.b64encode(b"a" * 512000)), {}, False),
    ("a", {}, False),
    (_wrap_cert("a"), {}, False),
    ("-----BEGIN CERTIFICATE-----", {}, False),
    ("-----BEGIN CERTIFICATE-----\n", {}, False),
    (LOCALHOST_CERT, {'not_expired': False}, True),
])
def test_x509_cert(pem, opts, valid):
    from ..types import x509_certificate

    f = NamedTemporaryFile(delete=False, mode='w')

    try:
        f.write(pem)
        f.close()

        check = x509_certificate(**opts)

        if not valid:
            with pytest.raises(ValueError):
                check(f.name)
        else:
            check(f.name)
    finally:
        f.close()
        os.unlink(f.name)


@pytest.mark.parametrize("pem,valid", [
    ("", False),
    (_wrap_key(""), False),
    ("\0", False),
    (_wrap_key("\0"), False),
    (_wrap_key(base64.b64encode(b"a" * 512000)), False),
    ("a", False),
    (_wrap_key("a"), False),
    ("-----BEGIN PRIVATE KEY-----", False),
    ("-----BEGIN PRIVATE KEY-----\n", False),
    (LOCALHOST_KEY, True),
])
def test_x509_key(pem, valid):
    from ..types import x509_privatekey

    f = NamedTemporaryFile(delete=False, mode='w')

    try:
        f.write(pem)
        f.close()

        check = x509_privatekey()

        if not valid:
            with pytest.raises(ValueError):
                check(f.name)
        else:
            check(f.name)
    finally:
        f.close()
        os.unlink(f.name)

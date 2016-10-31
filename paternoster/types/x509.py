import datetime
import logging

import OpenSSL
import pyasn1.codec.der.decoder
import pyasn1_modules.rfc2459


class EasyPrivateKey:
    def __init__(self, content):
        """ parses a given private key in PEM format """
        self.key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, content)

    @classmethod
    def load_from_file(cls, key_path):
        """ load a private key in PEM format from the disk """
        with open(key_path, 'r') as f:
            return cls(f.read())

    @property
    def pem(self):
        """ export the certificate as PEM format and return it as bytes """
        return OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, self.key)


class EasyCertificate:
    def __init__(self, content):
        """ parses a given certificate in PEM format """
        self.cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, content)
        self.logger = logging.Logger('EasyCertificate')

    @classmethod
    def load_from_file(cls, cert_path):
        """ load a certificate in PEM format from the disk """
        with open(cert_path, 'r') as f:
            return cls(f.read())

    @property
    def _commonname(self):
        """ get the commonname (if any) """
        try:
            return dict(self.cert.get_subject().get_components())[b'CN'].decode('ascii')
        except KeyError as e:
            # certificate does not contain a CN
            return None

    @property
    def _altnames(self):
        """ get the alternative names (if any) as an generator """
        for ext in map(lambda i: self.cert.get_extension(i), range(0, self.cert.get_extension_count())):
            if ext.get_short_name() != b'subjectAltName':
                continue

            names = pyasn1.codec.der.decoder.decode(ext.get_data(), asn1Spec=pyasn1_modules.rfc2459.SubjectAltName())

            return map(
                lambda n: str(n['dNSName']),
                filter(lambda n: n['dNSName'], names[0])
            )

    @property
    def domains(self):
        """ get all domains this certificate is valid for (if any) as a list """
        domains = []

        try:
            if self._commonname:
                domains.append(self._commonname)
        except:
            self.logger.exception('could not parse commonnanme')

        try:
            domains.extend(self._altnames)
        except:
            self.logger.exception('could not parse subjectAltNames')

        return domains

    @property
    def notafter(self):
        """ get the last day this certificate is valid """
        date_str = self.cert.get_notAfter().decode('ascii')
        return datetime.datetime.strptime(date_str, '%Y%m%d%H%M%SZ')

    @property
    def expired(self):
        """ determine whether this certificate is still valid """
        return datetime.datetime.now() > self.notafter

    @property
    def pem(self):
        """ export the certificate as PEM format and return it as bytes """
        return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, self.cert)


class x509_privatekey:
    def __init__(self):
        pass

    def __call__(self, val):
        try:
            key = EasyPrivateKey.load_from_file(val)
        except:
            raise ValueError('invalid key')

        return key


class x509_certificate:
    def __init__(self, needs_domain=True, not_expired=True):
        self.needs_domain = needs_domain
        self.not_expired = not_expired

    def __call__(self, val):
        try:
            cert = EasyCertificate.load_from_file(val)
        except:
            raise ValueError('invalid certificate')

        if self.needs_domain and not len(cert.domains):
            raise ValueError('certificate is not valid for a single domain')
        if self.not_expired and cert.expired:
            raise ValueError('certificate is no longer valid')

        return cert

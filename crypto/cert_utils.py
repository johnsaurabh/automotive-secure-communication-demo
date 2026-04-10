from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from config import (
    CA_CERT_PATH,
    CA_KEY_PATH,
    CLIENT_CERT_PATH,
    CLIENT_KEY_PATH,
    SERVER_CERT_PATH,
    SERVER_KEY_PATH,
)


def ensure_certificates() -> None:
    required = [
        CA_CERT_PATH,
        CA_KEY_PATH,
        SERVER_CERT_PATH,
        SERVER_KEY_PATH,
        CLIENT_CERT_PATH,
        CLIENT_KEY_PATH,
    ]
    if all(path.exists() for path in required):
        return

    CA_CERT_PATH.parent.mkdir(parents=True, exist_ok=True)

    ca_key = _generate_private_key()
    ca_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Local Automotive Security Lab"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Automotive Secure Comm Root CA"),
        ]
    )
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(ca_subject)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_now())
        .not_valid_after(_now() + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )
    _write_key(CA_KEY_PATH, ca_key)
    _write_cert(CA_CERT_PATH, ca_cert)

    _issue_leaf_certificate(
        common_name="secure-server.local",
        san_entries=[x509.DNSName("localhost"), x509.IPAddress(_loopback_ip())],
        eku=ExtendedKeyUsageOID.SERVER_AUTH,
        cert_path=SERVER_CERT_PATH,
        key_path=SERVER_KEY_PATH,
        ca_cert=ca_cert,
        ca_key=ca_key,
    )
    _issue_leaf_certificate(
        common_name="secure-client.local",
        san_entries=[x509.DNSName("secure-client.local")],
        eku=ExtendedKeyUsageOID.CLIENT_AUTH,
        cert_path=CLIENT_CERT_PATH,
        key_path=CLIENT_KEY_PATH,
        ca_cert=ca_cert,
        ca_key=ca_key,
    )


def _issue_leaf_certificate(
    common_name: str,
    san_entries: list[x509.GeneralName],
    eku: ExtendedKeyUsageOID,
    cert_path,
    key_path,
    ca_cert: x509.Certificate,
    ca_key,
) -> None:
    private_key = _generate_private_key()
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Local Automotive Security Lab"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_now())
        .not_valid_after(_now() + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .add_extension(x509.ExtendedKeyUsage([eku]), critical=False)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )
    _write_key(key_path, private_key)
    _write_cert(cert_path, certificate)


def _generate_private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _write_key(path, key) -> None:
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def _write_cert(path, cert) -> None:
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def _loopback_ip():
    import ipaddress

    return ipaddress.IPv4Address("127.0.0.1")


def _now() -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=1)

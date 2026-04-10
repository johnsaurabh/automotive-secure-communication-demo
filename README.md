# Automotive Secure Communication Demo for ADAS and Embedded Security

## Overview

This repository contains a local, end-to-end secure communication system designed to demonstrate the kind of technical depth expected in an automotive cybersecurity engineering role. The project models a simplified telemetry exchange between an ADAS domain controller and a backend validation service, with emphasis on transport security, payload confidentiality, integrity protection, certificate-based authentication, security logging, and threat modeling.

The implementation is intentionally practical:

- It runs locally with Python.
- It uses standard TCP sockets and TLS 1.3.
- It adds a separate AES-GCM application encryption layer above TLS.
- It uses a self-managed local PKI to demonstrate certificate issuance and trust.
- It produces sanitized audit logs for security-relevant activity.
- It includes architecture, threat modeling, and verification guidance suitable for a public GitHub portfolio project.

This project is not presented as a production automotive stack. It is a focused security engineering demonstration that makes design choices explicit and easy to explain in interviews.

## Objectives

The project was built to demonstrate the following capabilities:

- Secure communication over TCP with TLS 1.3
- Mutual certificate-based authentication using PKI concepts
- Application-layer encryption using AES-256-GCM
- Integrity checking using SHA-256
- Secure event logging without exposing sensitive telemetry
- Threat modeling using STRIDE
- Risk assessment using likelihood and impact
- System-level security reasoning relevant to ADAS, ECUs, gateways, and backend communication

## Why This Is Relevant for Automotive Cybersecurity

Modern vehicles increasingly rely on Ethernet backbones, service-oriented architectures, connected ECUs, telematics services, backend diagnostics, and software-defined control domains. That creates several security requirements:

- Nodes must authenticate each other before exchanging sensitive data.
- In-transit messages must be protected from interception and tampering.
- Security events must be logged for incident response and diagnostics.
- Trust anchors and certificates must be managed carefully.
- Security controls must be evaluated at both the network and system levels.

This project demonstrates those concepts using a small and understandable system that can be discussed clearly on a resume, in an interview, or in a technical review.

## Security Features

### 1. TLS 1.3 Secure Transport

The client and server establish a TLS 1.3 session before any application messages are exchanged. This provides:

- Confidentiality for traffic on the socket
- Integrity protection for the transport channel
- Stronger resistance to passive interception
- A realistic representation of secure service communication over IP-based networks

### 2. Mutual Authentication with Certificates

The implementation uses a local root CA to sign both server and client certificates. This allows both endpoints to verify the identity of the other side during the TLS handshake.

This maps directly to PKI concepts commonly discussed in automotive and embedded security:

- trust anchor
- certificate chain validation
- server authentication
- client authentication
- private key protection

### 3. Application-Level AES Encryption

After TLS is established, the server generates an ephemeral AES-256 session key and sends it through the TLS-protected channel. The client then encrypts the JSON payload using AES-GCM before transmission.

This is deliberate. The project is showing layered security:

- TLS protects the transport
- AES-GCM protects the application data itself

This makes it easy to explain the difference between channel security and payload security.

### 4. Integrity Verification with SHA-256

The plaintext payload is hashed before transmission, and the receiving side recomputes the hash after decryption. This provides a clean demonstration of integrity validation at the application layer.

### 5. Secure Logging

Security-relevant events are logged in structured JSON format, including:

- connection attempts
- authentication success or failure
- session-key issuance
- message send and receive events
- integrity verification status

Sensitive values such as raw payloads and cryptographic keys are not logged.

## Repository Structure

```text
AutomotiveSecureComm/
|-- client/
|   |-- __init__.py
|   `-- client.py
|-- server/
|   |-- __init__.py
|   `-- server.py
|-- crypto/
|   |-- __init__.py
|   |-- aes_utils.py
|   |-- cert_utils.py
|   `-- hash_utils.py
|-- certs/
|   `-- .gitkeep
|-- docs/
|   |-- architecture.md
|   |-- threat_model.md
|   `-- validation.md
|-- logs/
|   `-- .gitkeep
|-- tests/
|   `-- integration_test.py
|-- .gitignore
|-- config.py
|-- logging_utils.py
|-- protocol.py
`-- README.md
```

## Component Summary

### [client/client.py](client/client.py)

Implements the TLS client. Responsibilities:

- establish a TCP connection
- validate the server certificate
- present the client certificate
- receive the AES session key over TLS
- build a JSON telemetry payload
- encrypt the payload with AES-GCM
- compute a SHA-256 digest
- transmit the protected message
- decrypt and verify the server response

### [server/server.py](server/server.py)

Implements the secure TLS server. Responsibilities:

- accept incoming TCP connections
- require client certificate authentication
- validate the client certificate against the local CA
- generate an ephemeral AES-256 session key
- receive and decrypt the protected message
- validate message integrity
- log security events
- return an encrypted acknowledgement

### [crypto/cert_utils.py](crypto/cert_utils.py)

Generates the local PKI assets if they do not already exist:

- root CA key and certificate
- server key and certificate
- client key and certificate

This removes the dependency on the OpenSSL CLI and keeps the project easy to run on a clean machine.

### [crypto/aes_utils.py](crypto/aes_utils.py)

Provides AES-GCM encryption and decryption helpers.

### [crypto/hash_utils.py](crypto/hash_utils.py)

Provides SHA-256 hashing for application-layer integrity verification.

### [logging_utils.py](logging_utils.py)

Builds structured JSON loggers and supports simple message redaction.

### [protocol.py](protocol.py)

Implements framed JSON message handling and base64 encoding helpers for binary fields.

## Architecture and Security Flow

The high-level sequence is:

1. The local PKI is created if certificates do not exist.
2. The client opens a TCP connection to the server.
3. TLS 1.3 is negotiated.
4. The client validates the server certificate.
5. The server validates the client certificate.
6. The server generates an AES-256 session key and sends it inside the TLS channel.
7. The client creates a structured telemetry JSON payload.
8. The payload is hashed with SHA-256.
9. The payload is encrypted with AES-GCM.
10. The encrypted message is transmitted to the server.
11. The server decrypts the message and verifies the SHA-256 digest.
12. The server returns an encrypted acknowledgement.
13. Both sides write sanitized audit logs.

For a deeper system breakdown, see [docs/architecture.md](docs/architecture.md).

## Threat Modeling and Risk Assessment

The repository includes a formal threat model in [docs/threat_model.md](docs/threat_model.md). It documents:

- system assets
- trust boundaries
- STRIDE threat categories
- likelihood and impact scoring
- mitigation strategies
- residual risk discussion
- production hardening recommendations

This is a core part of the project because automotive security work is not just about implementing controls. It also requires structured security reasoning and defensible risk decisions.

## Cryptography Mapping

This project demonstrates several concepts expected in security interviews:

- AES: AES-256-GCM for payload confidentiality and authenticated encryption
- RSA: RSA-2048 private/public keys for certificate-backed trust establishment
- SHA: SHA-256 for application-layer integrity validation
- PKI: local CA, certificate issuance, certificate verification, trust anchor model
- TLS: TLS 1.3 for secure transport over TCP

## Environment Requirements

- Windows, Linux, or macOS with Python 3.11+
- Python package: `cryptography`

Install dependency if needed:

```powershell
python -m pip install cryptography
```

## Quick Start

### Start the server

```powershell
cd D:\Cybersec\AutomotiveSecureComm
python -m server.server
```

Expected output:

```text
Secure server listening on 127.0.0.1:8443
```

### Run the client

Open a second terminal:

```powershell
cd D:\Cybersec\AutomotiveSecureComm
python -m client.client --message "ADAS lane-state message"
```

Expected output:

```json
{
  "integrity_verified": true,
  "message_id": "...",
  "received_at": "...",
  "status": "accepted"
}
```

## Local Test Procedure

### Option 1: Manual functional test

1. Start the server in one terminal.
2. Start the client in another terminal.
3. Confirm the client receives an `accepted` response.
4. Review audit logs in the `logs/` directory.
5. Confirm the raw telemetry text is not logged.

### Option 2: Automated integration test

Run:

```powershell
cd D:\Cybersec\AutomotiveSecureComm
python tests\integration_test.py
```

The test starts the server, runs the client against it on a separate local port, and prints the validated response.

## Certificate Generation

On the first execution, the project automatically generates:

- `certs/ca_cert.pem`
- `certs/ca_key.pem`
- `certs/server_cert.pem`
- `certs/server_key.pem`
- `certs/client_cert.pem`
- `certs/client_key.pem`

These files are excluded from version control through `.gitignore`.

This approach demonstrates PKI fundamentals while keeping local execution simple.

## Logging Model

Audit logs are stored in:

- `logs/server_audit.log`
- `logs/client_audit.log`

Examples of logged events:

- `connection_attempt`
- `authentication_success`
- `authentication_failure`
- `session_key_issued`
- `message_sent`
- `message_received`
- `server_error`

The logging design intentionally avoids:

- plaintext telemetry logging
- cryptographic key logging
- full sensitive message body storage

This demonstrates secure observability without creating a secondary data-exposure problem.

## Wireshark Validation

The repository includes a traffic-validation guide in [docs/validation.md](docs/validation.md). The short version is:

1. Start the server.
2. Start a packet capture on the loopback adapter in Wireshark.
3. Run the client.
4. Filter traffic with `tcp.port == 8443`.
5. Confirm that application data is visible only as TLS-protected traffic.
6. Verify that the plaintext telemetry string does not appear in captured packets.

Because the application payload is also encrypted with AES-GCM, the design illustrates defense in depth beyond transport encryption alone.

## Design Limitations

This project is intentionally scoped for clarity. It does not attempt to be a production automotive implementation. Current limitations include:

- single-threaded server model
- local CA and local key storage only
- no certificate revocation support
- no hardware-backed key protection
- no rate limiting or DoS protection controls
- no secure boot or firmware-chain integration
- no direct CAN or SOME/IP stack integration

These limitations are discussed further in the threat model and are useful talking points in an interview because they show awareness of the gap between a demonstrator and a deployable system.

## Future Improvements

Reasonable next steps for expanding the project:

- add rate limiting and connection throttling
- add certificate rotation or short-lived certificates
- add CRL or OCSP-style validation concepts
- integrate signed command messages
- simulate gateway segmentation between vehicle domains
- add replay protection with timestamps and nonce tracking
- model backend fleet telemetry ingestion
- extend to a C-based client or embedded-side prototype

## Resume-Ready Project Bullets

- Built a Python-based secure telemetry communication platform that modeled ADAS-to-backend messaging using TCP sockets, TLS 1.3, mutual certificate authentication, and structured JSON messaging.
- Implemented layered cryptographic protections with PKI-backed transport security, ephemeral AES-256-GCM application encryption, and SHA-256 integrity verification to demonstrate defense-in-depth for embedded and automotive data flows.
- Produced a complete security engineering package including structured audit logging, architecture documentation, STRIDE-based threat modeling, and risk assessment with practical mitigation recommendations.

## Documentation Index

- [docs/architecture.md](docs/architecture.md)
- [docs/threat_model.md](docs/threat_model.md)
- [docs/validation.md](docs/validation.md)

## License and Usage

This repository is intended for educational, demonstration, and portfolio use. Review and adapt the design before using any part of it in a production or safety-critical environment.

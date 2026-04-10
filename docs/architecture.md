# System Architecture

## Purpose

This document explains the technical architecture of the secure communication demo and the security reasoning behind its main design decisions.

## System Context

The project models a simplified communication path between:

- an in-vehicle ADAS or ECU-like client
- a backend-facing validation server

The objective is to represent a realistic secure telemetry exchange in a form that is small enough to run locally and easy enough to explain during technical discussion.

## Architectural Goals

The system is designed to demonstrate:

- authenticated communication over IP
- confidentiality at both transport and application layers
- integrity verification at the message layer
- trust establishment using certificates
- secure event logging
- clear separation of responsibilities across modules

## High-Level Components

### 1. Client Endpoint

The client represents a vehicle-side software component such as:

- an ADAS controller
- a gateway ECU
- a telematics application
- a diagnostics-capable embedded node

It is responsible for:

- connecting to the server over TCP
- authenticating the server certificate
- presenting its own client certificate
- receiving the AES session key over the TLS session
- constructing structured telemetry as JSON
- encrypting the payload with AES-GCM
- attaching a SHA-256 digest
- handling the protected acknowledgement from the server

### 2. Secure Validation Server

The server represents a backend or trusted validation service. It is responsible for:

- accepting incoming TCP connections
- terminating TLS 1.3
- requiring mutual TLS authentication
- validating the client certificate chain
- generating an ephemeral AES session key
- decrypting the application-layer message
- verifying message integrity
- returning an encrypted acknowledgement
- writing security-relevant audit logs

### 3. Local PKI

The PKI component issues and manages local development certificates:

- root CA certificate and key
- server certificate and key
- client certificate and key

This models basic trust-anchor and certificate-chain concepts without requiring external infrastructure.

### 4. Crypto Support Layer

The crypto package isolates cryptographic operations from transport logic:

- AES-GCM encryption and decryption
- SHA-256 hashing
- certificate generation and signing

This separation keeps the system modular and easier to explain or extend.

### 5. Logging Layer

The logging subsystem records structured security events while avoiding sensitive data exposure. It captures:

- connection attempts
- authentication outcomes
- session-key issuance events
- message send and receive activity
- error conditions

## Data Flow

The end-to-end flow is:

1. The server starts and ensures certificates exist.
2. The client starts and ensures certificates exist.
3. The client opens a TCP connection to the server.
4. TLS 1.3 handshake begins.
5. The server presents its certificate.
6. The client validates the server certificate against the local CA.
7. The client presents its certificate.
8. The server validates the client certificate.
9. The server generates an ephemeral AES-256 session key.
10. The AES key is sent to the client inside the already-established TLS channel.
11. The client creates a telemetry JSON payload.
12. The client computes a SHA-256 digest of the plaintext payload.
13. The client encrypts the payload with AES-GCM.
14. The encrypted payload, nonce, and digest are sent to the server.
15. The server decrypts the payload.
16. The server recomputes the SHA-256 digest and verifies integrity.
17. The server logs the event using sanitized metadata only.
18. The server builds an acknowledgement, encrypts it, and sends it back.
19. The client decrypts and validates the acknowledgement.

## Text Diagram

```text
+---------------------------+                      +---------------------------+
| Vehicle-Side Client       |                      | Backend Validation Server |
|---------------------------|                      |---------------------------|
| TCP socket                |                      | TCP listener              |
| TLS 1.3 client            |<==== mTLS over IP =>| TLS 1.3 server            |
| Server cert validation    |                      | Client cert validation    |
| JSON telemetry builder    |                      | Payload verification      |
| AES-256-GCM encryptor     |                      | AES-256-GCM decryptor     |
| SHA-256 digest generator  |                      | SHA-256 digest checker    |
| Sanitized event logging   |                      | Sanitized event logging   |
+-------------+-------------+                      +-------------+-------------+
              |                                                    |
              v                                                    v
       +------+--------------------+                    +----------+-----------+
       | Local Root CA / Trust PKI |                    | Security Audit Logs  |
       | RSA-2048 signing          |                    | JSON event records   |
       +---------------------------+                    +----------------------+
```

## Trust Boundaries

### Network Boundary

The link between client and server is untrusted. An attacker may observe, replay, or tamper with traffic at this boundary.

### Certificate Trust Boundary

Only certificates signed by the local CA are trusted. Any node outside that trust chain must be rejected.

### Data Sensitivity Boundary

Plaintext telemetry exists only at the endpoint before encryption and after decryption. It is not meant to be exposed in transit or in logs.

### Logging Boundary

Logs are useful for monitoring and forensic review, but they must not become a source of sensitive-data leakage. The system therefore records identifiers, digests, and event metadata instead of raw message content.

## Security Design Decisions

### Why Use TLS and AES-GCM Together

TLS is enough to protect transport for many systems, but this project intentionally adds application-level encryption to show defense in depth and to clarify the distinction between:

- protecting a communication channel
- protecting the data object itself

This is useful in interviews because it shows system-level thinking rather than tool-level thinking.

### Why Use Mutual TLS

Automotive systems increasingly rely on authenticated machine-to-machine communication. Mutual TLS allows both endpoints to prove identity instead of authenticating only the server side.

### Why Use SHA-256 in Addition to AES-GCM

AES-GCM already provides authentication and integrity for ciphertext, but SHA-256 is included to explicitly demonstrate message-digest handling and integrity verification concepts that appear frequently in embedded and automotive security discussions.

### Why Structured Logging Matters

Security engineering includes observability. Logging is not only about debugging. It supports:

- incident response
- anomaly detection
- diagnostics
- compliance evidence
- security monitoring

## Module Mapping

| File | Role |
|---|---|
| `client/client.py` | Client connection, TLS setup, payload protection, response handling |
| `server/server.py` | TLS listener, client authentication, session handling, integrity verification |
| `crypto/aes_utils.py` | AES-GCM encryption and decryption |
| `crypto/hash_utils.py` | SHA-256 hashing |
| `crypto/cert_utils.py` | Local PKI generation and certificate issuance |
| `protocol.py` | Length-prefixed JSON framing and base64 helpers |
| `logging_utils.py` | Structured JSON audit logging |

## Operational Assumptions

- the client and server run locally for demonstration
- the local CA is trusted only for this demo
- the host system is not already compromised
- certificate storage is file-based rather than hardware-backed

## Architecture Limitations

- single-threaded server
- no certificate revocation
- no replay cache
- no HSM-backed key storage
- no direct vehicle-bus integration
- no hardware root of trust

## Recommended Production Extensions

- secure key storage using TPM or HSM-backed services
- certificate revocation or short-lived certificates
- replay protection and nonce reuse tracking
- segmented network deployment across gateway boundaries
- signed firmware and secure boot chain integration
- backend monitoring and SIEM integration

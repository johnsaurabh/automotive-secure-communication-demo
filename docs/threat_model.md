# Threat Model and Risk Assessment

## Purpose

This document identifies threats against the secure communication demo, evaluates their risk, and maps them to mitigation strategies. The goal is to show structured security reasoning, not just implementation of cryptographic primitives.

## Methodology

The threat model uses STRIDE:

- Spoofing
- Tampering
- Repudiation
- Information Disclosure
- Denial of Service
- Elevation of Privilege

Risk is evaluated using:

- Likelihood: Low, Medium, High
- Impact: Low, Medium, High
- Overall Risk: derived qualitatively from likelihood and impact

## Scope

In scope:

- client-server communication
- certificate-based trust
- application payload protection
- audit logging
- local key and certificate handling

Out of scope:

- operating system compromise
- hardware attacks
- secure boot chain
- firmware signing infrastructure
- vehicle bus-specific exploitation

## Protected Assets

- telemetry payload confidentiality
- telemetry payload integrity
- endpoint identity and trust relationship
- AES session keys
- TLS private keys
- CA private key
- service availability
- security audit history

## Assumptions

- the attacker can inspect and inject network traffic
- the attacker does not initially control both endpoints
- the local root CA is trusted for demo purposes
- private keys are stored locally without hardware-backed protection
- the system is executed in a local development environment

## Entry Points

- TCP connection to the server
- TLS handshake and certificate validation logic
- application-layer secure message exchange
- file-based certificate and key material
- log files

## Trust Boundaries

- untrusted network between client and server
- trusted local certificate authority
- client endpoint trust boundary
- server endpoint trust boundary
- log storage boundary

## STRIDE Threat Analysis

| STRIDE Category | Threat Scenario | Likelihood | Impact | Overall Risk | Current Mitigation |
|---|---|---:|---:|---:|---|
| Spoofing | An attacker presents a rogue client and attempts to impersonate a trusted ECU | Medium | High | High | Mutual TLS with CA-signed client certificates and required certificate validation |
| Spoofing | An attacker presents a fake server to intercept telemetry | Medium | High | High | Client validates the server certificate against the trusted CA and checks hostname |
| Tampering | A network attacker modifies payload content during transmission | Medium | High | High | TLS channel integrity, AES-GCM authenticated encryption, and SHA-256 digest verification |
| Tampering | An attacker modifies acknowledgement data returned by the server | Low | Medium | Medium | AES-GCM decryption validation and SHA-256 response integrity verification |
| Repudiation | A client disputes having sent a message | Low | Medium | Medium | Audit logs record certificate identity, message ID, timestamp, and outcome |
| Information Disclosure | Telemetry is exposed in plaintext on the wire | Medium | High | High | TLS 1.3 for transport encryption and AES-GCM for application payload confidentiality |
| Information Disclosure | Sensitive data is leaked through logs | Medium | Medium | Medium | Sanitized metadata-only logs and message redaction |
| Denial of Service | Repeated connection attempts consume server resources | Medium | Medium | Medium | Required TLS authentication, bounded request handling, and production recommendation for rate limiting |
| Elevation of Privilege | A compromised or unauthorized certificate is used to enter the trust domain | Low | High | High | CA-controlled issuance, certificate chain validation, and production recommendation for stronger key governance |

## Detailed Threat Discussion

### Spoofing

The primary spoofing risk is unauthorized endpoint participation. If the client or server accepts an untrusted certificate, the attacker can join the communication flow and either inject telemetry or intercept sensitive data.

Mitigation:

- mutual TLS
- CA-based trust anchor
- certificate chain validation
- client-side hostname checking

### Tampering

An attacker on the network may attempt to modify ciphertext, hashes, or framed JSON messages.

Mitigation:

- TLS integrity protection
- AES-GCM authenticated decryption
- SHA-256 digest comparison after decryption
- strict message type handling

### Repudiation

Without event logs, it becomes difficult to reconstruct what happened during a security incident or failed communication sequence.

Mitigation:

- structured JSON audit records
- timestamps
- peer identity metadata
- message identifiers

### Information Disclosure

Telemetry content, status messages, or security metadata could be exposed on the network or in logs if confidentiality controls are weak.

Mitigation:

- TLS 1.3 encrypted channel
- AES-GCM encrypted application payload
- sanitized logging with no raw payload storage

### Denial of Service

An attacker may repeatedly connect or attempt handshake abuse to exhaust server resources.

Current posture:

- acceptable for a local demonstrator

Production mitigation ideas:

- connection quotas
- rate limiting
- worker pool isolation
- resource caps
- upstream filtering

### Elevation of Privilege

If the CA private key is compromised or issuance policy is weak, an attacker can mint trusted certificates and gain access as a seemingly authorized node.

Mitigation:

- protect CA key material
- restrict issuance workflow
- rotate credentials
- use hardware-backed signing in production

## Residual Risks

The project intentionally leaves several residual risks in place because they are beyond the scope of a local demonstrator:

- no certificate revocation mechanism
- no HSM or TPM-backed key protection
- no replay detection database
- no rate limiting
- no hardened deployment pipeline
- no remote log integrity guarantees

These are documented rather than hidden because security engineering quality depends on clarity about what has and has not been addressed.

## Risk Summary

Highest-priority risks in this design are:

1. unauthorized endpoint participation
2. network tampering with protected messages
3. exposure of sensitive telemetry
4. compromise of the trust anchor

The implemented controls reduce those risks meaningfully for a local demonstration, but do not eliminate the need for stronger operational controls in a real deployment.

## Mitigation Summary Table

| Risk Area | Implemented Control | Additional Production Control |
|---|---|---|
| Endpoint authentication | Mutual TLS | Certificate lifecycle management and revocation |
| Transport confidentiality | TLS 1.3 | Strict cipher policy and monitored trust store |
| Payload confidentiality | AES-256-GCM | Key rotation and secure session establishment improvements |
| Payload integrity | AES-GCM plus SHA-256 | Anti-replay protections and stricter schema validation |
| Logging exposure | Sanitized structured logs | Centralized append-only or remote-protected logging |
| Trust anchor abuse | Local CA controls | HSM-backed CA operations and issuance governance |
| Availability | Basic bounded handling | Rate limiting, queueing, and service isolation |

## Automotive Security Relevance

This threat model reflects the kind of reasoning expected when evaluating:

- ECU-to-backend telemetry paths
- diagnostics communication
- secure vehicle gateways
- service-oriented in-vehicle network designs
- backend-connected automotive data flows

It is intentionally structured so it can support:

- design reviews
- portfolio discussion
- cybersecurity interview walkthroughs
- resume project explanation

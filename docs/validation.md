# Validation and Test Guide

## Purpose

This document explains how to verify that the project works correctly and how to demonstrate its security properties in a way that is useful for GitHub readers, interview discussions, and portfolio reviews.

## Validation Goals

The testing process should show the following:

- the client and server establish a TLS 1.3 session successfully
- both peers validate certificates signed by the local CA
- application payloads are encrypted and decrypted correctly with AES-GCM
- SHA-256 integrity checks succeed
- the server returns a protected acknowledgement
- audit logs capture relevant events without exposing plaintext telemetry
- packet capture does not reveal plaintext application data

## Prerequisites

- Python 3.11+
- `cryptography` installed
- Wireshark installed if network inspection is required

## Functional Test

### Start the server

```powershell
cd D:\Cybersec\AutomotiveSecureComm
python -m server.server
```

Expected result:

- the server starts successfully
- certificates are generated if they do not already exist
- the server listens on `127.0.0.1:8443`

### Run the client

In a separate terminal:

```powershell
cd D:\Cybersec\AutomotiveSecureComm
python -m client.client --message "ADAS telemetry validation message"
```

Expected result:

- TLS handshake completes
- server certificate is accepted by the client
- client certificate is accepted by the server
- the client prints a JSON acknowledgement with `integrity_verified: true`

## Automated Integration Test

Run:

```powershell
cd D:\Cybersec\AutomotiveSecureComm
python tests\integration_test.py
```

What this does:

- launches the server as a subprocess
- waits briefly for the listener to come up
- launches the client
- verifies that the end-to-end exchange completes without error
- shuts the server down

## Log Verification

After a test run, inspect:

- `logs/server_audit.log`
- `logs/client_audit.log`

What to look for:

- connection attempts recorded
- authentication success entries present
- message send and receive entries present
- message identifiers and digests recorded
- plaintext telemetry not present in log lines
- no AES key material present in log lines

## Wireshark Procedure

### Capture Steps

1. Open Wireshark.
2. Select the loopback interface.
3. Start capture.
4. Launch the server.
5. Launch the client.
6. Stop capture after the exchange completes.

### Display Filters

Use:

```text
tcp.port == 8443
```

You can also inspect TLS records with:

```text
tls
```

### What You Should Observe

- TCP handshake
- TLS handshake records
- encrypted application data records
- no readable JSON telemetry string in the packet payload

### What This Demonstrates

- transport-level confidentiality is active
- session establishment is certificate-backed
- the message is not exposed in plaintext on the wire

## Negative Test Ideas

If you want to extend the project, these are useful validation experiments:

- remove or alter the trusted CA and confirm certificate validation fails
- tamper with the transmitted digest and confirm integrity verification fails
- modify the ciphertext and confirm AES-GCM decryption fails
- replace the client certificate with an untrusted certificate and confirm the server rejects the connection

## Evidence for GitHub or Interview Discussion

Useful artifacts to mention or screenshot:

- successful client acknowledgement output
- excerpts from sanitized audit logs
- Wireshark capture showing TLS traffic only
- the threat model risk table
- the architecture data-flow diagram

## Expected Security Outcome

By the end of validation, you should be able to demonstrate:

- authenticated endpoints
- encrypted transport
- encrypted application payloads
- integrity verification
- controlled logging
- structured security design documentation

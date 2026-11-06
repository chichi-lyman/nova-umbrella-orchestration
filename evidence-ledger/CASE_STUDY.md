# Case Study: Translating CRJS 355 Evidence Concepts into a Software Ledger

**Author:** Chelsea Megan Woods  
**Status:** Prototype implementation added on a feature branch; CI evidence pending execution.  
**Data:** Synthetic examples only.

## Problem framing

Evidence-handling workflows depend on identifying items consistently, recording custody changes, restricting operations to authorized roles, and preserving a reviewable history. This project demonstrates how those domain concepts can be represented in a small software service.

This is an educational portfolio exercise. It is not an agency system, a certified LIMS, or a legal determination about admissibility.

## Requirements

- R1: Register evidence with stable ID, case reference, category, intake source, current custodian, and state.
- R2: Capture an initial registration event.
- R3: Record transfer requests as events; do not rewrite prior events.
- R4: Require the designated receiver to acknowledge a pending transfer.
- R5: Restrict custody operations by role and current custodian.
- R6: Record audit outcomes, including denied actions.
- R7: Optionally record SHA-256 digest for digital payloads and compare later supplied bytes.
- R8: Use only synthetic examples in demos and tests.

## Architecture

The domain/service module is standard-library Python with SQLite persistence. An optional FastAPI adapter exposes the service as HTTP. The local demo identity is supplied by request headers and explicitly marked insecure for production.

## Implementation evidence

- Core service: [evidence_ledger.py](./evidence_ledger.py)
- HTTP adapter: [api.py](./api.py)
- API contract: [openapi.yaml](./openapi.yaml)
- Automated tests: [tests](./tests/)
- Demo: [demo.py](./demo.py)
- Security boundaries: [SECURITY_AND_LIMITATIONS.md](./SECURITY_AND_LIMITATIONS.md)

## Verification plan

The test suite covers registration, initial event creation, custody transfer acceptance, receiver-only authorization, duplicate transfer acceptance, duplicate evidence IDs, digest match/mismatch, missing items, role rejection, and audit of rejected actions. GitHub Actions is configured to compile the package and run these tests on pushes and pull requests.

**Do not report a passing test count until a workflow run or local test output confirms it.**

## Limitations and next iteration

The prototype does not provide cryptographic signatures for event records, tamper-resistant external audit storage, robust identity federation, agency policy configuration, concurrency hardening, formal validation, or production monitoring. Next engineering iterations should add signed/event-hash chaining with key management, explicit case-scoped authorization, migrations, integration tests, and a qualified domain/security review.

**By Chelsea Megan Woods**

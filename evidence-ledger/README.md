# CRJS 355 Evidence Ledger — Portfolio Prototype

A small, runnable, synthetic-data-only reference implementation for evidence intake and chain-of-custody event tracking. This is a portfolio engineering demonstration, **not** a certified forensic/LIMS product, legal advice, or a claim of legal admissibility.

## Scope implemented

- SQLite persistence with transaction boundaries.
- Evidence item registration with unique IDs.
- Append-only custody events (no endpoint or method to overwrite prior custody records).
- Transfer request and receiver acknowledgment workflow.
- SHA-256 digest capture and verification for digital evidence.
- Role-gated operations in the demonstration service.
- Audit records for successful and rejected actions.
- Synthetic demo, API contract, and automated tests.

## Run

Python 3.11+ recommended. Core and tests use only the Python standard library.

```bash
cd evidence-ledger
python -m unittest discover -s tests -v
python demo.py
```

Optional HTTP API (FastAPI adapter):

```bash
python -m pip install -r requirements.txt
uvicorn api:app --reload
```

Then visit `http://127.0.0.1:8000/docs`. The API's demo authentication accepts an `X-Actor-Id` and `X-Actor-Role` header. **This is intentionally a local demo identity mechanism, not production authentication.** Never expose it publicly.

## Design

- `evidence_ledger.py`: domain/service layer, SQLite repository, event and audit model.
- `api.py`: optional HTTP interface.
- `openapi.yaml`: concise contract.
- `demo.py`: deterministic synthetic walkthrough.
- `tests/`: behavior and invariant checks.

## Key invariants

1. Evidence IDs are unique.
2. Custody history is append-only; a transfer is represented by a request event and a separate acceptance event.
3. A transfer can only be accepted by its designated recipient.
4. Transfer request and acceptance actors must have a custody role.
5. SHA-256 is stored as an integrity aid; digest match does not establish source authenticity or admissibility.
6. Every attempted service operation is audit logged, including rejected requests.
7. Demo records contain fictional names and IDs only.

## Workflow

`REGISTERED → IN_CUSTODY → TRANSFER_PENDING → IN_CUSTODY`

This is a simplified teaching workflow. Actual evidence processes vary by jurisdiction, agency, evidence type, policy, and qualified domain review. Production use would require formal identity, authorization, threat modeling, retention, backup, key management, audit protection, and independent validation.

## Portfolio mapping

See [Portfolio Inversion Protocol](../docs/PORTFOLIO_INVERSION_PROTOCOL.md). This module is an engineering demonstration derived from coursework concepts, not a statement that the system is used by an agency or has been legally validated.

**By Chelsea Megan Woods**

# Security, Safety, and Limitations

This project is a portfolio prototype using synthetic data. It is not approved for real evidence, investigations, agency operations, or court use.

## Known boundaries

- The FastAPI adapter accepts caller-supplied identity headers for a local demo. These headers are trivially spoofable and are not authentication. Do not deploy publicly.
- SQLite is suitable for this demonstration only. Production needs an appropriate transactional datastore, concurrency design, backups, retention controls, and disaster recovery.
- Application-level role checks are not a substitute for a verified identity provider, fine-grained policy enforcement, and independent authorization review.
- Audit records are stored in the same local database and are not tamper-proof against a database administrator. Production needs protected, externally monitored audit storage.
- This demo records an optional SHA-256 digest of byte payloads. Hash equality indicates byte equality against the recorded digest; it does not prove provenance, acquisition correctness, chain-of-custody completeness, or legal admissibility.
- The simplified states and events are not a universal legal procedure. Agency policy, evidence type, jurisdiction, and qualified domain review govern actual handling.
- No real names, case records, personal data, or evidence files should be added to public demo fixtures.

## Before any production consideration

Require threat modeling, legal/domain review, policy mapping, real authentication, strong authorization, signed or otherwise protected audit records, key management, encryption at rest/in transit, retention and deletion policy, secure backups, monitoring, penetration testing, accessibility review, independent validation, and documented operational ownership.

**By Chelsea Megan Woods**

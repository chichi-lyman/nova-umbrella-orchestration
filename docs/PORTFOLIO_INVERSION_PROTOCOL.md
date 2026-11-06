# Portfolio Inversion Protocol
## Translating Criminal Justice & Forensic Science Coursework into Engineering Evidence

**Portfolio owner:** Chelsea Megan Woods  
**Context:** B.S. Criminal Justice candidate, American InterContinental University (AIU), Forensic Science specialization reported; anticipated graduation 2027. AI Software Engineering track reported.  
**Purpose:** Turn domain learning into traceable software requirements, architecture, verification, and portfolio evidence in the Nova Umbrella ecosystem.

> This is a portfolio engineering framework, not an assertion that every mapped module has been implemented, deployed, or validated. Each work item must be labeled **proposed**, **in progress**, **implemented**, **tested**, or **operationally verified** based on repository evidence. Private academic records and student identifiers do not belong in this public document.

## 1. Protocol

The inversion process works from domain concepts toward engineering artifacts:

1. **Extract domain concept:** Identify the concept, process, actors, and constraints from coursework.
2. **Define operational scenario:** Describe a realistic but non-sensitive example and its system boundary.
3. **Derive requirements:** Write functional, data, security, audit, and usability requirements.
4. **Model the workflow:** Specify states, events, entities, invariants, and failure conditions.
5. **Design the module:** Document interfaces, storage, permissions, and architecture decisions.
6. **Implement incrementally:** Build a narrow vertical slice with explicit scope.
7. **Verify:** Add unit, integration, negative, authorization, and property/invariant tests.
8. **Document evidence:** Link commits, tests, ADRs, sample data, and a demonstration.
9. **Review claims:** Distinguish implemented behavior from proposed design and measured outcomes from hypotheses.

## 2. Example course-to-module mappings

| Coursework / domain area (reported) | Engineering translation | Candidate module / artifact | Verification focus |
|---|---|---|---|
| CRJS 355 — Evidence | Chain-of-custody lifecycle, evidence identity, custody transfers, audit events | Evidence ledger service; data model; API contract; ADR | No silent custody edits; append-only event history; authorized transfer; integrity check; complete audit trail |
| CRJS 365 — Criminalistics | Evidence classification and lab workflow | Case/evidence taxonomy and workflow rules | Valid classifications; required metadata; controlled transitions |
| CRJS 478 — Forensic Biology | Sensitive biological evidence metadata and handling constraints | Restricted metadata schema and access policy | Data minimization; least privilege; access audit; no unnecessary real personal data |
| CRJS 475 — Cybercrimes | Digital evidence intake, preservation, and incident workflow | Digital evidence intake and preservation record | Hash capture; source provenance; acquisition metadata; reproducible verification |
| SCIE 208 — Life Science | Scientific method, observation, hypothesis, and measurement | Evaluation methodology and experiment records | Clear hypothesis; reproducible measurements; documented limitations |
| CRJS 499 — Senior Capstone | End-to-end applied project and communication | Capstone-aligned architecture, demo, and technical report | Requirements traceability; quality gates; honest results and limitations |

These mappings are design candidates derived from the course labels provided by the portfolio owner. Confirm course descriptions and learning outcomes before representing them as formal curriculum mappings.

## 3. Chain-of-custody reference design

### Core entities

- **Case:** Case reference, status, authorized participants, created timestamp.
- **EvidenceItem:** Stable evidence ID, case reference, category, description, intake source, current state.
- **CustodyEvent:** Event ID, evidence ID, event type, actor, event timestamp, location/context, prior and resulting custody holder, authorization reference, event metadata.
- **IntegrityRecord:** Evidence ID, algorithm, digest, calculation time, tool/version, verification result (for digital objects).
- **AuditEvent:** Actor, action, resource, outcome, timestamp, correlation ID, and reason where applicable.

### Candidate state model

`RECEIVED → REGISTERED → IN_CUSTODY → TRANSFER_PENDING → IN_CUSTODY → ANALYSIS → SEALED / STORED → RELEASED / DISPOSED`

This is an illustrative workflow, not a universal legal procedure. Real deployments must adapt to jurisdiction, agency policy, evidence type, and qualified domain review.

### Invariants to encode and test

- Every evidence item has a stable unique identifier.
- Custody changes are recorded as new events; prior custody events are not silently overwritten.
- A transfer requires an authorized initiating actor and an explicit receiving acknowledgment where policy requires it.
- Event timestamps, actor identity, and action outcome are captured consistently.
- Access to sensitive case and evidence data follows least privilege.
- Digital evidence integrity checks record algorithm and digest; a matching digest supports integrity verification but does not independently prove authenticity or legal admissibility.
- Failed or rejected actions are auditable without exposing sensitive payloads.
- Corrections use a documented amendment event with actor, reason, and reference to the corrected record.

## 4. Architecture and governance alignment

For Nova Umbrella, proposed boundaries include:

- **Domain layer:** Evidence, custody, case, transfer, and policy invariants.
- **Application layer:** Intake, transfer, review, search, and verification use cases.
- **Persistence layer:** Transactional records and append-only audit/event history.
- **Authorization layer:** Role and case-based permission checks; deny by default.
- **Integration layer:** Provider-neutral adapters, explicit timeouts, retries, and failure isolation.
- **Observability layer:** Correlation IDs, structured audit logs, metrics, and alerting without logging sensitive evidence content by default.

For consequential actions, apply the ecosystem's authorization lifecycle where relevant:

`PROPOSE → VALIDATE → AUTHORIZE → RESERVE → EXECUTE → VERIFY → COMMIT / ROLLBACK`

A policy decision should be explicit: `ALLOW`, `REQUIRE_APPROVAL`, or `DENY`. Human review and auditability are essential for consequential case/evidence operations.

## 5. Required portfolio evidence per module

Each module should have:

- Domain concept and source/course mapping (with exact syllabus reference if available).
- Problem statement, stakeholder, scope, and non-goals.
- Requirements and acceptance criteria.
- Data model, workflow/state diagram, and API contract.
- Security/privacy threat model and authorization rules.
- Architecture decision record and trade-offs.
- Implementation links and reproducible setup.
- Automated tests, including invalid and unauthorized scenarios.
- Demo using synthetic data only.
- Known limitations, review needs, and measured results (if any).

## 6. Safe demonstration data

Use synthetic case IDs, synthetic people, and fabricated evidence records. Never publish real case files, student records, personal identifiers, private appeals, or confidential academic documents. Do not represent a prototype as an official forensic, law-enforcement, or legally admissible system.

## 7. Maturity labels

- **Proposed:** Concept and scope documented; implementation not established.
- **In progress:** Work underway; not yet complete.
- **Implemented:** Source code exists for the stated scope.
- **Tested:** Relevant automated/manual checks have run; include command and results.
- **Operationally verified:** Deployed or operated in a stated environment with observable evidence.
- **Measured:** Outcome has a baseline, metric definition, observation window, and source.

**By Chelsea Megan Woods**
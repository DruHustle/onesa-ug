# Delivery roadmap

Updated **5 November 2026**. Sequence is based on evidence and dependencies, not a promised launch date.

Deliver this application under `onesa-mobile/` in the existing `DruHustle/onesa-ug` repository.

| Phase | Deliverables | Completion condition |
| --- | --- | --- |
| 0. Development foundation | Public concept website, customer demo, synthetic `/internal/` operations preview, native projects, read-only API and decision documents | Build/test evidence recorded; fictional data and absence of authentication/live operations unmistakable |
| 1. Commercial discovery | First customer segment, host/MVNE proposals, POTRAZ route, entity/ownership confirmation, wholesale economics | Written viable terms and responsibility matrix |
| 2. Identity and operations | Separate authenticated customer/staff surfaces, product-scoped Onesa identity, customer/support/billing/agent/operations/admin roles, staff MFA, registration design, approved storage and audit | Backend denies ungranted actions and cross-account access; role, registration and audit acceptance passes |
| 3. Carrier integration | Provider sandbox, SIM/eSIM inventory, orders, activation, suspension, replacement, usage import | Provider-confirmed successes/failures; idempotent retries; no mistaken activation |
| 4. Payments and invoicing | Direct approved payment providers, agent cash sales/settlements, billing reconciliation, invoices, reversals, scoped refunds and optional renewal | End-to-end ledger reconciliation, approval limits and correct receipts under failure/retry conditions |
| 5. Device and service qualification | Signed builds, physical device tests, accessibility, terrestrial voice/SMS/data and support escalation | Agreed pilot matrix passed and limitations published |
| 6. Satellite capability | Written Zimbabwe entitlement, approved devices/services, constrained-network optimization, real radio tests | Evidence supports each enabled capability and customer claim |
| 7. Controlled launch | Small consented cohort, incident ownership, billing audit, restore/rollback and customer remedy | Reliable service and positive measured contribution before scaling |

Phases 2–5 can progress while satellite discussions continue. Satellite access is not a prerequisite for evaluating the customer platform, but it is a prerequisite for selling a satellite-enabled plan.

## Public, customer and internal delivery

Plan `mobile.onesa.eu` for the public website and authenticated customer portal, and `ops.mobile.onesa.eu` for staff operations. These domains remain proposed and unconfigured. The current `/internal/` route is a synthetic preview with no staff authentication, live records or operational authority.

Develop staff modules for subscribers/registration/provisioning, subscriptions, billing/reconciliation/invoices/refunds, agent cash settlements, support, provider/service readiness, reports, staff permissions and audit. Production protection requires backend-enforced scopes and staff MFA in addition to separate deployment and navigation. The customer portal and native apps must expose only the customer's authorized data and actions.

## First implementation backlog after partner discovery

1. Define one approved base plan and its renewal/expiry rules.
2. Select the host's documented interfaces and a provider sandbox.
3. Agree the separation between payer, account holder, registered subscriber and SIM; family funding grants no right to communications or ID documents.
4. Implement separate customer/staff identity clients, product scopes, backend role/object authorization, staff MFA and KYC evidence/retention boundaries.
5. Implement provisioning as a durable state machine with compensation on failure.
6. Implement usage import with provenance, timestamps and settlement reconciliation.
7. Integrate direct payment providers; add amount/currency checks, authenticated events and duplicate prevention.
8. Issue invoices/credit notes from confirmed financial events and define tax treatment with an adviser.
9. Add scoped staff queues for support, registration, provisioning and agent settlements, with approval limits and audited changes.
10. Add provider-readiness reporting, operational/financial reports and staff-access administration with least privilege.
11. Test customers against another account, agents against another agent, and staff against actions outside their role; verify audit evidence and MFA enforcement.
12. Build signed mobile binaries and qualify supported handset variants on the actual provider service.

## Explicitly not completed by the foundation

No regulatory application, host contract, satellite entitlement, licence, merchant integration, authenticated customer/staff portal, production RBAC/MFA/audit system, live identity deployment, real SIM profile, telephone number, native voice capability, customer onboarding, public production deployment or app-store release is created by this repository. The internal preview is not a production company-operations system.

The next decisive deliverable is a viable partner offer with a defined licence and data-handling model. That determines the actual APIs, service entitlements, prices and launch acceptance tests.

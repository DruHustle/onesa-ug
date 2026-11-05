# Onesa Mobile — partner due diligence

**Decision date and source check: 5 November 2026.**

Source location: `DruHustle/onesa-ug`, application directory `onesa-mobile/`.

Use this checklist to obtain reviewable answers before committing to a live pilot. It records questions and proposed responsibilities; it does not represent an existing agreement. No outreach, application or customer onboarding was performed in preparing it.

Plan for a public website, authenticated customer portal and staff operations portal. Proposed hosts are `mobile.onesa.eu` for the public/customer surfaces and `ops.mobile.onesa.eu` for staff; neither is configured by this plan. The `/internal/` preview uses synthetic records and has no staff authentication or live authority.

## 1. POTRAZ and corporate structure

- Confirm the licence scope for Onesa-branded mobile service, the intended host relationship and prospective direct-to-cell access.
- Obtain current application requirements, fees, levies, tariff process and licence conditions in writing.
- Confirm the Zimbabwean operating entity, ownership requirements and relationship with any overseas Onesa company.
- Establish whether the host's satellite authorization can cover Onesa subscribers, and what further permissions apply.

POTRAZ's published guidance recognizes Full, Light and Branded/Reseller MVNO categories, plus MVNEs. A licence route does not establish a willing wholesale partner. [Licence guidance](https://www.potraz.gov.zw/wp-content/uploads/2025/06/Licence-Application-General-Guidelines.pdf).

Check current ownership law rather than relying on older summaries: ZimLII records the repeal of SI 101/2026 by SI 111/2026 on 3 July 2026. [Repeal record](https://zimlii.org/akn/zw/act/si/2026/111/eng%402026-07-03).

## 2. Host operator or MVNE

- Which commercial model is available, and who owns the subscriber relationship, SIMs and billing records?
- What setup fees, deposits, minimum commitments, per-SIM charges and usage rates apply? How are disputes and refunds settled?
- Which documented interfaces support eligibility, provisioning, usage, suspension, renewals, SIM replacement and incident escalation?
- Are physical SIM and eSIM both available? Who operates profile issuance and handles installation failures?
- Who supplies numbers, handles any available number transfer, and provides voice, messaging, emergency access and interconnection?
- What evidence confirms charges, activation and usage? How are duplicate requests, delayed events and reversals handled?
- What happens to customers and records when either party exits?
- Which staff and agent actions can Onesa perform, and which require host approval? Establish scopes for registration, provisioning, subscriptions, reconciliation, invoices, refunds, cash settlements, support, readiness and reports.

## 3. Satellite capability

Ask the host and relevant Starlink commercial team whether Onesa is eligible for direct contracting or must obtain access through the host. Request written confirmation of Zimbabwe availability, regulatory scope, permitted branding, supported devices, services, locations and commercial entitlements.

Agree outdoor/obstruction test conditions, fallback behavior, incident ownership and the evidence needed to enable each advertised feature. Confirm native calls, app-based calls, SMS, application data and emergency functions individually. Record absent or unconfirmed functions as unavailable. Dish-based Wi-Fi resale requires a separate review of the applicable Zimbabwe Starlink contract.

## 4. Responsibility matrix

These assignments are proposed starting points for contract negotiation.

| Function | Proposed lead | Evidence needed before pilot |
| --- | --- | --- |
| Licence and tariffs | Onesa with host and adviser | Confirmed scope, approvals and accountable entity |
| Network, spectrum and satellite entitlement | Host/operator partners | Contracted capability and authorization |
| Subscriber registration | Agreed licensed entity | Approved process and activation gate |
| Numbers and emergency service | Host | Documented service and escalation arrangements |
| Payments and invoices | Onesa with approved providers | Reconciliation, refunds and audit evidence |
| Subscriber-data protection | Agreed controller(s) | Hosting design, contracts and key custody |
| Customer support | Onesa, with host escalation | Service levels, ownership and incident handover |
| Staff and agent access | Onesa with host scope agreement | Backend permissions, staff MFA and audit records |
| Agent cash settlements | Onesa with authorized agents | Sale attribution, balances, reconciliation and approval limits |
| Exit and continuity | Both parties | Customer transition and data-handling provisions |

## 5. Data and activation controls

Confirm the required identity evidence, verification process, retention and reporting. Registration must precede activation under the published subscriber regulations. [SI 95/2014](https://www.potraz.gov.zw/wp-content/uploads/2015/04/SI_95_of_2014_Subscriber_Registration_Regulations.pdf).

Foreign cloud storage needs a specific design review. SI 250/2019 qualifies the earlier transfer restriction with encryption unreadable by the foreign host, locally retained keys, advance submission of safeguards/agreements, affirmative written consent and restrictions on onward use. Ordinary overseas hosting should not be assumed compliant. [SI 250/2019](https://www.veritaszim.net/sites/veritas_d/files/SI%202019-250%20Postal%20and%20Telecommunications%20%28Subscriber%20Registration%29%20%28Amendment%29%20Regulations%2C%202019%20%28No.%201%29.pdf).

Settle controller licensing, DPO responsibility, processor agreements and transfer notifications under the applicable data-protection framework. [SI 155/2024](https://www.potraz.gov.zw/wp-content/uploads/2025/02/sI-155-of-2024-Cyber-and-Data-Protection-Normal_240913_1250178.pdf).

Agree least-privilege scopes for customer, support, billing, agent, operations and admin roles. Require backend enforcement, product-scoped identity and staff MFA before real records are exposed. A family payer's financial permission gives no right to the subscriber's communications or ID documents.

## 6. Pilot approval record

For each answer, record the accountable organization, named owner, document reference, conditions, unresolved questions and verification date. Require reconciled test transactions, confirmed service entitlement, support escalation and an agreed rollback/customer-remedy process before real sales. Keep live activation and public satellite claims disabled until the corresponding evidence is approved.

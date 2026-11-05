# Hardware-pilot software validation

Date: **5 November 2026**. Scope: the persistent Onesa Mobile hardware-pilot and customer/staff control plane, its native clients, and the additive Company Portal identity integration. This is software qualification with synthetic records. It is not evidence of an operating mobile network or commissioned equipment.

## Local results

| Area | Observed result | What the check establishes |
| --- | --- | --- |
| Mobile API | Strict TypeScript and **78 tests passed** | Domain transitions, authenticated HTTP, role/owner isolation, retry/revision handling, evidence review, lab receipts, current OpenAPI and identity failure boundaries |
| Public/customer/staff web | TypeScript, production build and **11 tests passed** | Buildable application; preview rules, money parsing, retry identity, truthful pilot states and cursor merging |
| Native application | TypeScript and **8 tests passed** | Pilot/demo state, API configuration, real private-IP development origins and scoped pagination |
| Native JavaScript | Metro/Hermes production exports completed for iOS and Android | Compilable source and JavaScript bundles; native compilers are a separate gate below |
| Native generation and artwork | Expo prebuild completed; deterministic SVG-to-PNG generation and visual icon inspection passed | iOS/Android source/configuration and consistent installed artwork; iPhone/iPad support enabled |
| Encrypted recovery | **6 tests passed** against actual platform/authentication schemas | Online WAL capture, integrity/audit/idempotency preservation, tamper/wrong-key refusal, no overwrite, mode isolation and recovered-access invalidation |
| API schema | **41 paths / 87 operations**; freshness and formal OpenAPI 3.1 validation passed | Requests, responses, authorization and route inventory agree with implementation |
| Portal integration | Backend types/build/lint/contracts passed; frontend generated types/types/lint and **26 domain/callback tests passed** | Additive Mobile product/client/role support and existing-product compatibility |
| Portal local identity exercise | Migrations 001–015 and **7 focused cases passed** using disposable PGlite | Selected migration/protocol behavior; not PostgreSQL concurrency |
| Dependency review | API and native production audits reported **zero advisories**; Expo fingerprint completed | Inspected lockfiles and audit snapshot; not a guarantee against future advisories |

The API, web, native logic and recovery suites contain **103 passing tests** in total. Portal results are separate. Generated OpenAPI tests are included in the backend count. Repeated checkpoints are not counted as independent coverage.

The legacy Portal hygiene command rejected the ancestor monorepo because it expects a standalone repository root. It is not reported as passed. Publication uses a scoped monorepo diff, artifact and secret review instead.

## Authenticated HTTP and recovery evidence

HTTP tests start the actual server against temporary SQLite databases and generated identities. They cover cookie/CSRF and bearer sessions, customer denial of staff access, cross-customer record/receipt denial, least-privilege staff, independent evidence acceptance, idempotent mutations, stale revisions, immutable completed observations and unavailable provider operations.

Pagination tests create more than one page, apply owner/role scope before pagination, retrieve subsequent pages and verify complete owner export. Bulk equipment responses omit history; the protected detail endpoint retains it. Readiness aggregates include older evidence and never enable service.

Identity tests exercise signed OIDC, PKCE/state/nonce, the Portal opaque-token contract, live role/MFA changes, replay/expiry, secure native handoff, TOTP replay, restart persistence and logout during issuer outage. Encoded HTTPS issuer query parameters reach the callback; encoded path separators remain rejected. Production does not inherit localhost browser trust.

Recovery rejects corrupt archives and wrong keys, clears historical sessions/flows/handoffs, preserves idempotency/audit continuity and disables all restored lab identities. Reissue tests require explicit current-role confirmation, password/TOTP rotation and private output persistence before committing.

These are synthetic protocol tests. They do not establish a configured live Portal, carrier or payment provider.

## Browser and visual review

Reviewed the actual public page and customer/staff sign-in routes in Chromium at phone and desktop sizes. Corrected a hidden mobile account link and a workspace footer contrast/style collision. At the inspected 360px frame, document width remained within available CSS width after the scrollbar.

Reviewed actual customer components for summary, application/correction, support, lab billing and requests; staff components for overview, equipment, trials, evidence, applications, support, ledger and audit. An ignored local harness supplied prominently labelled synthetic props at 360, 390, 768 and 1280px widths. It had no authentication, credentials or business API calls, was not imported by the application and is not shipped.

Checks covered mobile navigation, readable labels, contained tables, equipment details, seven commissioning states, custody/serial/supplier references and the protected-history control. A correction form preserved its values and produced the expected local fixture submission; no real application was saved. Authenticated browser login and production transactions were not performed. Real authorization was exercised through the HTTP suite.

The [hardware workspace screenshot](screenshots/hardware-workspace.png) shows actual components with synthetic review data. It is not operational inventory or a network measurement. This focused review is not WCAG certification or a Zimbabwe subscriber usability study. Native styling and artwork were inspected; physical screens, text scaling, VoiceOver and TalkBack require hardware acceptance.

## Hosted qualification

Two workflows provide exact-source gates:

- [Software, container and PostgreSQL qualification](../../.github/workflows/onesa-mobile-ci.yml): package checks, container build/start/restart, encrypted recovery and Portal identity tests against disposable PostgreSQL.
- [Native compilation](../../.github/workflows/onesa-mobile-native-compile.yml): Android arm64 debug application and unsigned iPhone/iPad simulator build. No signing keys are uploaded and no app is published.

Initial source: [`f95059f4`](https://github.com/DruHustle/onesa-ug/commit/f95059f4e1bb711b00057acf7233b431686f8336). [Qualification run](https://github.com/DruHustle/onesa-ug/actions/runs/42076695029): web, API and native JavaScript passed; **35 Portal identity tests passed against actual PostgreSQL**, including the existing concurrent-flow cases. Container images built and became healthy, but the first smoke test found an unpublished gateway port caused by its internal-only network. The gateway now has a separate ingress bridge; the API remains internal-only. [Native run](https://github.com/DruHustle/onesa-ug/actions/runs/42076694933): Android found an SDK-manager PATH error before compilation, which is corrected to the exact installed tool path. Follow-up container/native runs must pass before these gates are closed.

## Physical and commercial acceptance

No site, router, UPS, phone, SIM, eSIM or terminal was commissioned. No real subscriber, payment, number, tax invoice or emergency call was created. No live Portal migration, production service, DNS change, partner outreach, regulatory submission or app-store release occurred.

The [hardware runbook](HARDWARE_PILOT.md) defines 14 acceptance cases. The [regulatory matrix](REGULATORY_MATRIX.md) and [resolution register](reviews/RESOLUTION_REGISTER.md) identify external evidence. Physical installs, provider sandbox/reconciliation, approved hosting, identity/TLS/key custody, operational recovery, licensing and host/satellite entitlement remain necessary before real service.

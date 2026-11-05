# Principal telecommunications engineering review

Review date: **5 November 2026**. Baseline inspected: commit `1e53a20f5cfbb8f589de1191a6005bc0e1a658b7`, scoped to `onesa-mobile/`. This is a role-based engineering review of the repository and public source material. No physical site, host network, SIM, satellite entitlement or regulatory application was inspected or commissioned.

## Decision

Continue with a **Light MVNO negotiating position**, using a licensed host's mobile network and developing Onesa's customer and operating systems. Start the physical work with a small **device and IP acceptance bench**. A purchased Starlink terminal does not establish a handset-to-satellite mobile service.

POTRAZ's published guidance distinguishes a Light MVNO from branded resale; the latter does not confer ownership of subscribers, infrastructure or SIMs. The actual host agreement must settle customer control and migration rights. [POTRAZ converged licensing guidance](https://www.potraz.gov.zw/wp-content/uploads/2025/06/Licence-Application-General-Guidelines.pdf).

There is currently no repository evidence of an Onesa host agreement, assigned mobile numbering, network credentials, a qualified handset list or authorized Zimbabwe Starlink Mobile service. Public source research did not establish such an entitlement. That is an unresolved commercial/regulatory dependency, not proof that negotiations cannot succeed.

## What the baseline actually implements

| Inspected component | Observed implementation | Engineering implication |
| --- | --- | --- |
| `onesa-mobile-backend/src/app.ts` | Four static read resources; activation, payment and identity mutations return unavailable | No subscriber lifecycle or network command is executed |
| `onesa-mobile-backend/src/fixtures.ts` | Fictional account, proposed catalogue and static readiness | API availability is not radio coverage or commercial readiness |
| `onesa-mobile-backend/src/contracts/providers.ts` | TypeScript interfaces with no carrier or satellite implementation | There is no integration endpoint to configure or test against |
| `onesa-mobile-backend/Dockerfile` | Single non-root HTTP API image definition | No deployment, database, private provider connectivity, recovery or production operation is established by this file |
| `scripts/dev.mjs` | Starts local API and Vite development processes | Development orchestration is not a carrier operations environment |
| Web customer and internal interfaces | Local synthetic workflow state | A reviewed row or matched sample payment cannot prove a provisioned line |
| Native package and generated platforms | Source projects and JavaScript export qualification | Device install, carrier behavior and native release acceptance remain separate |
| Physical infrastructure | No commissioned inventory or measured site evidence in baseline | Nothing in this review establishes that hardware is installed, powered or reachable |

## Findings and required closure evidence

These findings describe the inspected baseline. Later implementation must be evaluated against the closure evidence; a document or UI label alone does not close a network dependency.

| ID | Priority | Finding | Required remediation and closure evidence |
| --- | --- | --- | --- |
| TEL-01 | Launch blocker | No contracted and authorized host/satellite service | Written scope and responsibility schedule, approved service territory and features, host test access, commercial terms and provider acceptance. Until then, provisioning remains unavailable. |
| TEL-02 | High | No physical pilot inventory or commissioning record | Persistent sites, assets, serial/model references, firmware, custodian, approval evidence, power and connectivity tests. Planning rows must be distinguishable from received and commissioned assets. |
| TEL-03 | High | Static readiness cannot represent evidence expiry or revocation | Store readiness evidence with scope, issuer, reviewer, observation date and validity. Missing, expired, rejected or out-of-scope evidence must block the relevant service. An ordinary app setting must not enable a live provider. |
| TEL-04 | High | No device/service eligibility model | Separate country, host, offer, device SKU, software/carrier profile, SIM format and feature. Keep SMS, app data, app voice, native voice, emergency and roaming distinct. Every approved combination needs evidence. |
| TEL-05 | High | No authoritative subscription lifecycle | Separate account access, subscriber registration, payment, provisioning and network state. Persist pending/failed/confirmed transitions; protect duplicate requests and reconcile provider outcomes before declaring service active. |
| TEL-06 | High | No usage ingestion or freshness contract | Validate provider identity and event identifiers, retain measurement intervals, units and source timestamps, reject duplicate events, reconcile corrections and show stale/unavailable data honestly. |
| TEL-07 | High | No approved-offer and tariff control | Retain proposed concepts separately from sellable offers. Approval evidence, currency, tax treatment, allowances, validity and billing rules must be versioned before a price becomes public or purchasable. See the regulatory matrix. |
| TEL-08 | High | API health does not measure network health | Monitor application, database, provider API, provisioning backlog, reconciliation lag and radio-service incidents separately. Give each exception an owner and escalation path. |
| TEL-09 | High | Physical and native acceptance not performed | Install signed test builds on representative phones/tablets; verify slow/offline behavior, SIM/eSIM lifecycle, real usage and approved radio functions in a recorded pilot. |
| TEL-10 | High | No agreed emergency, numbering and interconnection responsibility | Obtain host/regulator acceptance for the offered service. Test using an agreed test facility or test numbers; do not place unsolicited calls to emergency centers. |
| TEL-11 | High | No qualified data-hosting and recovery design | Establish controller/processor responsibilities, authorized data locations and key custody, protected operational access, tested backups and restore evidence before real subscriber information is stored. |
| TEL-12 | Medium | No reproducible physical change and rollback process | Record configuration version, verified pre-change backup, access method, maintenance owner, acceptance results and rollback outcome for each commissioned asset. |

## Three distinct connectivity products

| Product | Access path | What Onesa would operate or contract |
| --- | --- | --- |
| Mobile with satellite extension | Handset/SIM uses contracted terrestrial access and, where entitled, a satellite-enabled mobile network | Host provisioning, commercial entitlement, qualified device/service combinations, customer operations and support |
| Dish-based internet | User device uses Wi-Fi/Ethernet behind a satellite terminal | A separately authorized broadband installation and its local network; retail or resale terms must match its use |
| Satellite backhaul | Handset uses a terrestrial radio site whose upstream link is satellite | A licensed radio/access-network project with a host, site engineering and a specific backhaul design |

Starlink's technical release describes operator spectrum and roaming-style integration. Its current Mobile page distinguishes supported app/data/messaging capabilities from future native calling and expanded broadband. Neither a dish order nor a generic eSIM creates the missing host entitlement. [Starlink technical release](https://starlink.com/public-files/DIRECT_TO_CELL_SERVICE_FEB_25.pdf); [Starlink Mobile](https://starlink.com/mobile).

Do not create a local eNodeB/gNodeB, buy spectrum-capable transmitters, or deploy a software mobile core as a substitute for the commercial and regulatory route. A Light MVNO acceptance lab needs interfaces to an authorized host, not an unlicensed broadcast network.

## Reference operators: lessons to implement

The references below are product and engineering benchmarks, not prospective Onesa partners unless an agreement is obtained.

| Reference | Verified pattern | Onesa engineering decision |
| --- | --- | --- |
| [fraenk](https://fraenk.de/hol-dir-fraenk) | App-managed plan, SIM/eSIM, usage and support | Keep the core account journey short; show the offer's full conditions with its price |
| [My Econet](https://www.econet.co.zw/my-econet-app/) | Registration, physical SIM/eSIM, suspension/reactivation and account self-service | Model lifecycle actions explicitly and require provider-confirmed outcomes; introduce recovery and assisted service paths |
| [NetOne](https://www.netone.co.zw/which-bundles-does-netone-have) | Separate data, voice, SMS and combo bundles, with self-service/support entry points | Represent allowance types and validity independently, rather than a single ambiguous balance |
| [Vodacom eSIM](https://www.vodacom.co.za/vodacom/terms/esim) and [VoLTE](https://www.vodacom.co.za/vodacom/terms/vodacom-volte) | Compatibility involves device/region, software and provisioned service | Qualify exact device and network combinations; eSIM support alone does not establish voice or satellite support |
| [T-Mobile T-Satellite](https://www.t-mobile.com/coverage/satellite-phone-service) | Automatic network attachment, supported devices/apps, and stated outdoor/availability limitations | Show entitlement and limitations; never present an app control as a radio attachment switch |

T-Mobile is the verified US Starlink direct-to-cell benchmark used here. Its ability to sell an add-on to some other carriers' customers is not evidence that every such carrier has its own Starlink integration. US prices, emergency numbers, roaming arrangements and approvals must not be copied into Zimbabwe's product.

## Acceptance responsibilities

| Owner to appoint | Responsibility | Evidence to retain |
| --- | --- | --- |
| Onesa commercial lead | Host/MVNE agreement, service scope, supplier commitments and exit rights | Executed agreement references and authorized product scope |
| Onesa regulatory lead with Zimbabwe adviser | Applicable licence, tariff, equipment, data and numbering requirements | Written authority/host determinations and current approvals |
| Host network team | SIM profiles, network registration, numbering, voice/SMS/data, satellite entitlement and network incidents | Test accounts, approved interface specification, device list and signed acceptance results |
| Onesa engineering | Account/order state, provider integration, persistence, idempotency, usage and operational tooling | Reproducible tests and linked provider event evidence |
| Onesa operations | Asset custody, commissioning, support, maintenance and incident handling | Inventory, check results, configuration/restore history and trained owners |

The physical sequence and procurement controls are in [Hardware pilot](../HARDWARE_PILOT.md). The applicable policy evidence is in [Regulatory matrix](../REGULATORY_MATRIX.md). All assets and checks in the [pilot template](../../infra/hardware/pilot-template.json) start as planned or not run. They are not evidence of installed equipment or authorization.

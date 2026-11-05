# Senior telecom UI/UX review

Reviewed **5 November 2026**. Scope: Onesa Mobile's public website, customer experience, staff operations and native app. This is a role-based engineering review of the available source and published operator references; it does not claim a field trial or a usability study with Zimbabwean subscribers.

## Product conclusion

The customer needs to understand **what service they have, what is waiting, and what they can do next**. The staff member needs an owned queue and the evidence needed to resolve it. These are separate experiences. Neither an app login, an accepted form nor a recorded payment proves that a SIM or satellite service is active.

The initial prototype communicates the concept clearly, but its account and operations interactions are session-only demonstrations. Building an operating pilot requires authenticated access, persistent records, explicit lifecycle states, recoverable failures and supported customer/staff journeys. The coordinated platform changes implement those application workflows while preserving uncommissioned network and commercial boundaries.

## Findings and acceptance

| ID | Priority | Finding | Correction / acceptance |
| --- | --- | --- | --- |
| UX-01 | Critical for operations | Staff actions in the initial internal preview disappear on refresh; its navigation is not an access boundary. | Serve the operational workspace at `/internal/` behind real backend authentication and per-action permissions. Preserve the clearly labelled old demonstration at `/preview/internal/`. Refresh and a new session must retrieve saved records. Customer roles must receive no staff collections. |
| UX-02 | High | A prospective customer has no persistent application, review response, support conversation or service-request journey. | Add an authenticated `/account/` experience with owned applications, status, next actions, support and requests. A reviewer asking for information must give the customer a way to respond. Staff must be able to triage requests. Do not use a successful screen transition as activation evidence. |
| UX-03 | High | Concept selection, registration review, payment and network eligibility could be mistaken for one combined approval. | Show those states independently. Display missing network usage as unavailable, never as zero. State the last successful workspace refresh separately from the time of any network measurement. |
| UX-04 | High | Hardware has no operational journey and a stored asset can easily acquire an unjustified “online” label. | Provide site and asset creation, receipt, commissioning checks and field-trial records. Label manual observations and lab simulations; show measurement time/source. Preserve the distinctions between terrestrial, direct-to-cell and dish/Wi-Fi paths. |
| UX-05 | High | A retry after a slow connection can duplicate an operation if the client generates a new request identity. | Preserve the same idempotency key for retrying the same attempted mutation; change it when the operation/input changes. Disable repeat submission while pending. Do not silently queue payments or activation. On revision conflicts, keep entered values and ask the user to refresh/review. |
| UX-06 | High | Sample financial amounts and confirmations can resemble purchasable tariffs or legal invoices. | Label lab ledger entries and PDFs as test records. Show currency and refunded amount explicitly. Keep real charging and approved-offer purchase unavailable until the contracted workflow exists. A download must be subject to backend account/role scope. |
| UX-07 | High | Long staff navigation and very small labels make mobile tasks difficult to discover and complete. | Use a labelled mobile section selector and readable 14px operational text, 16px inputs and 44px controls. Use compact summaries, contained wide tables and forms that expand only when needed. Every permission-visible action must have a working result/error state. |
| UX-08 | Medium | The native opening screen prioritises a promotional hero over a returning customer's state. | Lead with account/service status and the next task. Use the common Onesa mark and semantic status treatment. Retain font scaling, show offline freshness and avoid persisting credentials in ordinary storage. Native implementation and physical-device acceptance are assigned separately. |
| UX-09 | High | Central login, local lab credentials and commercial onboarding have different purposes. | Show the actual authentication mode returned by the backend. Offer Onesa sign-in only when configured. Label lab access and explain how pilot accounts are issued. Do not add a decorative signup/reset button with no implemented flow, and never ask for a production password in the lab form. |
| UX-10 | High | Readiness checkboxes can conceal country, host, service, device and expiry constraints. | Present scoped evidence records, a separate reviewer, expiry/revocation and the decision reason. Internal evidence acceptance must not turn on radio service or commercial sales. |

## Reference findings

The following are observed product patterns and Onesa-specific design inferences. No competitor assets, tariffs, availability claims or emergency-service promises are copied.

| Primary reference | Observed pattern | Onesa application |
| --- | --- | --- |
| [fraenk](https://fraenk.de/hol-dir-fraenk) | A simple plan and app-managed SIM, usage and support tasks are central to the offer. | Keep public acquisition concise; give returning customers a small set of familiar account tasks. |
| [Econet Zimbabwe](https://www.econet.co.zw/) | Bundles, tariffs, eSIM and self-care have distinct entry points, with currencies identified. | Separate plan information from service state and make currency explicit. Do not hide eligibility inside a generic “buy” action. |
| [NetOne self-service guide](https://www.netone.co.zw/posts/your-guide-to-the-netone-web-self-service-platform) | Balance, usage, bundle purchase, PUK recovery and query tickets are ordinary self-service jobs. | Put status, history and service recovery ahead of marketing in the account. Provide persistent support tracking. PUK display requires an authorized host integration; it is not fabricated in this pilot. |
| [Vodacom self-service](https://www.vodacom.co.za/vodacom/services/my-vodacom) and [billing help](https://www.vodacom.co.za/vodacom/help/balances-usage-and-billing) | Account/balance/billing tasks work across channels, with help for delayed or missing top-ups. | Keep web/native task names aligned and make pending transactions and recovery states visible. Do not infer zero-rated Onesa access from another operator's offering. |
| [T-Mobile T-Satellite](https://www.t-mobile.com/coverage/satellite-phone-service) | Compatibility, outdoor/sky conditions, supported apps and possible delays or gaps are stated beside the service. Attachment is described as automatic for entitled customers. | Put verified eligibility beside any future satellite offer. Never present a manual app switch as network attachment. US product availability and emergency arrangements do not establish Zimbabwe entitlement. |

## Implementation boundary and release evidence

The new web workspace uses its own frontend types and documented HTTP endpoints; it does not import backend source. Cookies and CSRF controls remain backend-enforced. In-memory client retry keys are operational metadata, not credentials or a queued financial system.

Acceptance must cover successful and failed sign-in; a customer denied staff access; application creation/review/recovery; ticket replies and status; asset commissioning; a field observation with source/time; independent evidence review; test receipt ownership; duplicate-safe retry; stale-record conflicts; expired-session recovery; narrow layouts and keyboard focus. The repository's final validation document should record which of these were actually tested. This review does not pre-claim those results.

## Implemented web corrections

The web implementation is in `onesa-mobile-frontend/web/src/workspace/`, with entry routing in `web/src/main.tsx`.

| Area | Implemented behavior |
| --- | --- |
| Authenticated surfaces | `/account/` loads owned customer records. `/internal/` loads permission-filtered staff records. `/preview/internal/` retains the synthetic staff preview, and `/#demo` retains the customer preview. The API remains the access-control boundary. |
| Authentication | The sign-in screen reads the actual lab/Onesa mode. Staff lab access includes an authenticator code. Session cookies stay HTTP-only; the client uses an in-memory CSRF value. Business fetches reject redirects, while the explicit Onesa link starts SSO. Session expiry clears the private view. |
| Customer recovery | Customers can submit a lab application, update and resend requested details, open support cases, reply to reopen them, review staff responses, request account/service handling and download owned records or test receipts. |
| Hardware | Staff can register sites/assets, record equipment receipt, save commissioning evidence and plan/record a trial. Custodian, internal serial-record reference and supplier reference can be recorded and updated. Full asset/history JSON can be downloaded through the protected record endpoint. The UI distinguishes manual observations from lab simulations and reports network measurements as unobserved. Serial-reference, firmware and approval changes call out the need to repeat affected checks. |
| Review and support | Staff can review applications, assign/reply/resolve cases, handle account requests and independently review scoped readiness evidence. Evidence includes its issuer, document issue date and expiry. Expired acceptance has a distinct label. Request resolution is described as a staff response, without claiming automatic deletion or SIM work. |
| Financial controls | Lab entries and refunds use exact integer USD minor units. Screens and downloads explicitly state that no money moved and that a test receipt is not a tax invoice. Agents see their own permitted entries; the UI does not expose a refund control to agents. |
| Recovery and history | Mutations retain a request key for an uncertain retry of the same payload. A confirmed save is not re-sent when its follow-up refresh fails. Stale revisions preserve form input and require review after refresh. Cursor controls load older records, deduplicate overlapping pages and retain the loaded range across refreshes. |
| Readability | Essential text is at least 14px, inputs are 16px and controls are at least 44px. Mobile navigation has a labelled section selector. Tables scroll within their own region. A visual check found public-footer CSS bleeding into the workspace and tight sign-in field spacing; both were corrected with scoped workspace styles. |

### Validation recorded by this reviewer

`npm run build` passes TypeScript checking and the Vite production build. `npm test` includes **11 passing tests**: the seven existing tests and four workspace checks for exact money input, uncertain-retry request identity, truthful pilot labels and cursor-page identity/revision preservation. These tests verify those specific behaviors; they do not constitute a browser end-to-end test or an accessibility audit.

The coordinated browser review uses the real public/sign-in surfaces and an ignored local component harness at `web/.validation/review.html` for authenticated-layout inspection. The harness renders actual components at 360, 390, 768 and 1280 pixel iframe widths with prominently labelled synthetic props. It has no authentication, credentials or business API calls, is not imported by the application, and is not included in the production bundle. Its local form handler does not save operational records. This distinction avoids misrepresenting a visual fixture as an authenticated browser test. The root validation report separately records the actual browser and authenticated HTTP integration results.

Native device behavior, radio/hardware performance, emergency-service arrangements, host activation and production payment acceptance require their separately assigned verification and external commissioning. They are not established by this web review.

## Final session-transition follow-up

A late private download could previously finish after sign-out or a new login. The web now gives each download an abortable session scope, checks it after the response and Blob conversion, and discards both stale success and stale errors. Sign-out, identity/role/source/CSRF changes, expiry, page exit and unmount invalidate downloads. An old 401 cannot sign out the next user. Hardware history, customer export and receipt downloads all use this guarded path. Three asynchronous regressions were added; the complete web suite now has **14 passing tests**, and its production build passes. This closes the observed client race without claiming a full browser end-to-end sign-in test.

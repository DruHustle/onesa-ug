# Foundation validation

Date: **5 November 2026**. Scope: the repository's development preview, not a live telecommunications service.

## Passed locally

| Area | Evidence |
| --- | --- |
| Website | TypeScript check, Vite production build and 7 readiness/operations tests passed |
| Backend | Strict TypeScript and 27 HTTP/configuration tests passed |
| Mobile | TypeScript and 3 preview-isolation/reset tests passed |
| iOS JavaScript | Metro/Hermes production export completed, 629 modules |
| Android JavaScript | Metro/Hermes production export completed, 627 modules |
| Native project generation | Expo generated actual iOS and Android projects; iPhone/iPad device family is enabled |
| OpenAPI | All 69 local references resolve and 27 operation IDs are unique; this is a consistency check, not independent full-schema certification |
| Development integration | Root launcher started web and API together; browser readiness request displayed the expected connected development status while keeping customer activation unavailable |

Total focused automated tests: **37**. These checks verify the implemented preview boundary and contracts. They do not demonstrate any carrier, payment or subscriber integration.

## Browser checks

Checked the local website in Chromium, including 360 px and 390 px phone frames, a 768 px tablet frame and a 1440 px desktop frame. Layout measurements showed no horizontal document overflow in the inspected views. The browser's scrollbars reduce the inner CSS content width by 15 px in these frames.

Verified the connectivity-path explanations, landing-to-demo navigation, proposed-plan selection retained across demo tabs, billing explanation, Help navigation and the API's connected/unavailable states. The skip link now preserves the demo route and focuses the content. Connectivity selectors use a labelled button group with pressed states, and low-contrast secondary text/focus colors identified during review were corrected.

Desktop internal-operations checks covered fictional subscriber search and reviews, matching a synthetic payment, and assigning and resolving sample support cases. Derived queues changed as expected: reviews **4 → 3**, open support cases **3 → 2**, and unmatched entries **2 → 1**. Four local audit events were recorded, and reset restored the baseline. The internal overview at **360 px** and the proposed role matrix at **360 px** and **768 px** showed no document overflow; horizontal scrolling stayed contained within the role table. Two missing arrow glyphs were replaced. These checks used synthetic records in an unauthenticated preview and do not establish live staff authentication or authorisation.

This was focused browser review, not an exhaustive accessibility or browser-compatibility certification. The ignored local responsive-review harness is not part of the shipped website.

## Native limits

JavaScript/Hermes exports are **not** signed native binaries. Xcode/Gradle native compilation, simulators, physical phones/tablets, VoiceOver/TalkBack, store signing and submissions have not been verified. No IPA, APK or AAB is supplied.

## Service and infrastructure limits

No real SIM, eSIM, mobile number, satellite link, payment, subscriber identity or invoice was created. Docker configuration exists, but its image was not built or run during this foundation task. No production service, DNS change, regulator application, partner outreach or customer-data collection took place.

The GitHub workflow repeats the package checks on repository changes. Consult the check result for the exact commit; this document does not predict a future CI outcome.

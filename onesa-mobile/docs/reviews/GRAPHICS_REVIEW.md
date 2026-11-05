# Senior graphics design review

Reviewed **5 November 2026**. Scope: Onesa Mobile public website, customer preview, internal operations preview, and iOS/Android interface source in `DruHustle/onesa-ug/onesa-mobile`.

This is a role-based design review, not a claim of an external professional certification. Initial findings were established from the component structure and style definitions. The closure pass inspected the integrated source, regenerated native artwork and local build/test results. Responsive browser checks of the new workspaces were performed by the integration owner; native device validation remains separate acceptance work.

## Assessment

The forest-and-mint identity, restrained surfaces, clear plan concepts and explicit network limitations provide a useful starting point. The main visual gap is **readability at useful information density**. Several phone styles reduce essential type to around 9–12 CSS pixels. Compact interfaces should remove duplication and excess spacing, while retaining legible text and sufficiently large controls.

The public site can use an expressive introduction. Customer and company workspaces should begin with the current account or work state, its freshness, and the next meaningful action. Marketing, administrative tasks and network eligibility need distinct visual priorities.

## Findings and acceptance criteria

| ID | Priority | Evidence in the initial implementation | Required correction and acceptance |
| --- | --- | --- | --- |
| GFX-01 | High | `web/src/styles.css` phone rules set `.balance .secondary` to `.59rem`, `.billing-details > div` to `.67rem`, `.workspace-nav button` to `.69rem`, and `.status-label` to `.53rem`. With a 16px root, those values are approximately 9.4, 10.7, 11 and 8.5px. | Use at least 14px for operational body text, labels and navigation. Keep nonessential captions at least 12px. Preserve wrapping and compact padding. Verify 320/360/390/768/1440 CSS-pixel layouts and enlarged text; do not shrink type to make a card fit. |
| GFX-02 | High | `web/src/internal/internal.css` uses `.61rem` record IDs, `.74rem` action labels and `.77rem` form controls. A number of status, payment and audit details are below 12px. | Apply the same operational type scale to staff screens. Inputs use 16px text. Essential IDs and amounts remain legible and selectable. Dense grids may scroll within a labelled table region; the document must reflow. |
| GFX-03 | Medium | Web and operations use three rising bars, forest `#103C35` and mint `#C7F5B5`. Native `src/ui.tsx` uses a circular mark, forest `#102B29` and mint `#78E6B9`. | Use the three-bar mark and common core color values across all surfaces, implemented independently in each package. Match the installed icon in a subsequent native asset regeneration if its artwork differs. No shared frontend/backend runtime is required. |
| GFX-04 | High | Web `.button.small` and operations `.ops-button` have a 40px minimum; several inline action rows have no explicit minimum. Phone connectivity selectors combine small labels and tight spacing. | Set a product target of at least 44px for touch controls. Keep adjacent actions separated. Use the visible full row as the action target where suitable. This product target is deliberately larger than WCAG 2.2's 24px minimum/spacing rule and is not presented as that rule's wording. |
| GFX-05 | Medium | Native `HomeScreen` starts with a promotional hero before the account/service state. The public/customer web experiences also share a large marketing header. | Returning-customer screens lead with a compact account summary and one next action. Reserve the larger hero for acquisition pages. The initial demo's lack of a live account must remain explicit. |
| GFX-06 | Medium | At widths below 900px, operations navigation is a horizontal scrolling strip. Later modules are outside the initial visible portion. | Use a discoverable mobile navigation pattern in the operational workspace: a labelled section selector or an explicit overflow affordance. Keep the active section visible. Do not solve the problem with smaller text. |
| GFX-07 | Medium | The native `Tag` defaults to green even for `DEMO` and `CONCEPT`. Availability prose and decorative emphasis are not governed by a common semantic status system. | Distinguish neutral concepts, pending work, confirmed results, failure, and unavailable actions. Every state needs a text label; green is reserved for a confirmed successful or approved state. Never style a plan selection as a live activation. |
| GFX-08 | Medium | Public controls have a light focus override in the forest header. The initial operations header uses a generic `#368960` ring against `#103C35`, a calculated contrast of approximately 2.85:1. | Use a light mint focus ring on dark surfaces and a dark green ring on light surfaces. Check the visible focus of each interactive header and toolbar control. |
| GFX-09 | High for the pilot | Existing interfaces do not yet present physical device inventory, site readiness or field-test evidence. The system has no basis for a visual “online” or coverage badge. | Hardware records distinguish manual inventory state, measured telemetry, and acceptance results. Show source and time beside measurements. Inventory entry and approved equipment status are separate; a saved record is not a working radio link. |

GFX-02, GFX-05, GFX-06 and GFX-09 required the coordinated functional workspace/mobile implementation. The closure evidence below records the implementing source and distinguishes software corrections from device and network acceptance.

## What to adopt from the requested references

These are design recommendations inferred from each operator's published customer tasks and product presentation. They are not endorsements of all aspects of the reference sites, nor permission to reuse their assets.

| Reference | Observed pattern | Application to Onesa |
| --- | --- | --- |
| [fraenk](https://fraenk.de/hol-dir-fraenk) | One clear mobile offer and repeated app-oriented entry points; usage, SIM/eSIM and support are described as everyday app tasks. | Give each screen one principal action. Put plan terms together. Use a recognisable app preview, without borrowing German prices or launch claims. |
| [Econet Zimbabwe](https://www.econet.co.zw/) | Bundles, tariffs, eSIM, self-care and help are distinct entry points. USD and ZWG information are separated. | Make the selected currency explicit next to every amount; keep account service and product exploration easy to distinguish. |
| [NetOne self-service guide](https://www.netone.co.zw/posts/your-guide-to-the-netone-web-self-service-platform) | Balance, bundle purchase, usage, PUK recovery and support tickets are prominent self-service tasks. | Prioritise current service information and service recovery. Use a small set of familiar task labels. |
| [Vodacom self-service](https://www.vodacom.co.za/vodacom/services/my-vodacom) and [balance/billing help](https://www.vodacom.co.za/vodacom/help/balances-usage-and-billing) | Account management, balances, bundle buying and billing are available across customer channels, with help for delayed or missing top-ups. | Use a consistent account summary across web and mobile, with visible pending/error states for transactions and helpful next steps. |
| [T-Mobile T-Satellite](https://www.t-mobile.com/coverage/satellite-phone-service) | Device compatibility and outdoor/sky conditions are stated with the service offer; limited supported apps and possible gaps are explained. | Place eligibility and limitations beside the relevant satellite feature. Avoid a universal-coverage map or a decorative “connected” animation that implies measured service. |

No competitor logo, illustration, screenshot or product imagery was copied into Onesa. Code-native diagrams, progress indicators and service-state visuals are sufficient for the first pilot.

## Corrections in this graphics pass

- Raised public/customer essential type to at least 14px at the default root size; limited the 12px exception to decorative brand/caption/eyebrow roles. Added wrapping to summaries and mobile account navigation.
- Raised the existing public/customer small actions to a 44px minimum, gave busy controls an explicit busy state, and distinguished unavailable from waiting cursors.
- Scoped marketing navigation rules to the site header, so its phone rule no longer hides anchors in other navigation components.
- Reduced the phone hero heading and removed the rotated phone illustration on narrow screens. Simplified the customer availability heading and consolidated the demo disclosure.
- Aligned native color tokens with the web identity, raised operational labels and navigation to 14px, and reduced card/hero padding and corner radii. Exported a decorative three-bar `BrandMark` for integration by the native app owner; the reserved `mobile/App.tsx` was not modified in this pass.
- Web TypeScript and production build passed. Native TypeScript passed. The review did not compile or inspect a native binary. Final responsive browser and device acceptance belongs to the combined release validation.

The first graphics pass left internal functionality and new operational flows to their assigned implementation owner. The subsequent closure pass checked that integration and corrected the preserved operations preview and installed native artwork.

## Closure review — 5 November 2026

| Finding | Implemented correction | Evidence and remaining acceptance |
| --- | --- | --- |
| GFX-01 | Public/customer operational text, compact phone heading and action sizes corrected. | `web/src/styles.css` and `web/src/App.tsx`; web build passed. Integration owner reported responsive browser checks at 360, 390, 768 and desktop widths. |
| GFX-02 | New protected workspace uses 14px operational text and 16px inputs. Preserved preview now has the same operational minimums, wrapping IDs and tabular amounts. | `web/src/workspace/workspace.css` and `web/src/internal/internal.css`; web tests and build passed. Optional brand qualifiers, decorative symbols and eyebrows retain the documented 12px minimum. |
| GFX-03 | Native headers adopt `BrandMark`; core tokens use forest/mint. The old circular installed icon was replaced with vector-derived three-bar artwork. | `mobile/App.tsx`, `mobile/src/ui.tsx`, `mobile/assets/brand-mark.svg`, and regenerated iOS/Android resources. New icon visually inspected; generated dimensions and transparency checked. Device launcher and launch-screen inspection remains a native release check. |
| GFX-04 | Web touch controls meet the 44px product minimum; preview search/select inputs and header links now also have 44px targets. | Public, protected workspace and preserved preview styles; source inspection and successful web build. |
| GFX-05 | Protected native home leads with the signed-in account state and next step; the fictional product preview is explicitly separate. | `mobile/App.tsx` account summary and next-step sections; native TypeScript and tests passed. |
| GFX-06 | New protected workspace exposes a phone section selector. Preserved operations preview now exposes a labelled native select below 900px instead of hiding later modules in a horizontal strip. | `web/src/workspace/WorkspaceApp.tsx`, `workspace.css`, and `web/src/internal/InternalApp.tsx`. The legacy selector keeps keyboard focus while changing sections. |
| GFX-07 | Native `Tag` defaults to a neutral tone; demo/concept disclosure stays explicit. Workspaces distinguish recorded observations from network availability. | `mobile/src/ui.tsx`, native account source, and workspace hardware copy. No plan selection becomes a live activation. |
| GFX-08 | Preserved operations preview uses mint focus rings in the forest header and dark green focus on light surfaces. | Scoped `:focus-visible` rules in `web/src/internal/internal.css`; no global focus removal. Integration owner also corrected the new workspace footer contrast. |
| GFX-09 | Hardware inventory, commissioning and field-trial evidence now have dedicated screens. Network state stays “Unobserved”; recorded results show source and observation time. | `web/src/workspace/Hardware.tsx`; manual field observations and lab simulations are explicitly named. No authenticated network telemetry or physical field result is claimed by this graphics review. |

All nine source/design implementation findings have corresponding corrections. Native screen-reader, text-scaling and launcher behavior still require a simulator or physical device; those are release validation, not inferred from a JavaScript build.

### Installed artwork and regeneration evidence

The inspected original `mobile/assets/icon.png` used a circular mint ring and white dot, which differed from the three-bar identity. The replacement `assets/brand-mark.svg` contains the original bar geometry and the agreed colors. `scripts/build-brand-assets.mjs` renders it with the pinned `sharp` 0.34.5 dependency; `npm run assets:build` generates an opaque 1024px icon, transparent 1024px adaptive foreground and transparent 1024px splash artwork. Two consecutive runs produced identical SHA-256 hashes for all three PNGs. The opaque icon and transparent foreground dimensions were checked, and the new icon was visually inspected.

`npm run prebuild` completed and propagated the new artwork into the committed native projects. A hash comparison against the native files immediately before regeneration found exactly 27 changed files: 20 Android image resources plus `values/colors.xml`, four iOS image resources, the iOS splash background color catalog and splash storyboard. No native manifest, signing configuration or project code changed during that regeneration. The existing blocked permissions, disabled Android backup, `faceIDPermission: false`, and unsigned release configuration were preserved. Generated trailing whitespace in `android/settings.gradle` was removed.

Closure verification: **11 web tests passed**, the web TypeScript/production build passed, native TypeScript passed, **8 native JavaScript tests passed**, and the scoped whitespace check passed. No signed binary, physical device, live operator or satellite link was used for these checks.

## Visual acceptance

1. Public pages retain a recognisable Onesa identity and a clear principal action. They disclose the actual launch state adjacent to the offer.
2. Account and operations screens show useful summary information above secondary explanations. Panels expand to their contents rather than imposing oversized minimum heights.
3. Essential content remains readable at 200% text size, and ordinary page content reflows at 320 CSS pixels. Wide evidence tables have contained, keyboard-accessible scrolling and descriptive captions.
4. Primary text combinations reach at least 4.5:1 contrast. State labels include words; focus remains visible on both light and dark surfaces. Measure real component combinations, including hover and disabled states.
5. Touch controls target 44px or more. Test error messages, long labels, missing values and busy states as well as populated happy paths.
6. The native app must be checked on a physical phone or simulator with larger text and a screen reader. TypeScript and JavaScript exports do not constitute that visual acceptance.

Relevant accessibility references: [W3C contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) and [text resizing](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html). The 14px/16px/44px design choices above are Onesa product targets, not a claim that WCAG sets those particular text sizes.

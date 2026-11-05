# Onesa Mobile

**A simpler mobile experience for Zimbabwe, with a planned satellite extension.**

Canonical source: [`DruHustle/onesa-ug`](https://github.com/DruHustle/onesa-ug), in the **`onesa-mobile/`** product directory.

This product folder is a working **development foundation**, not an operating mobile network. It contains a public website, customer account demo, internal operations preview, an iOS/iPadOS and Android app, a read-only backend and the business/technical brief needed to develop the service. No carrier or Starlink partnership is claimed. Proposed plans are not for sale; identity, payments, SIM activation and satellite service remain unavailable.

## Recommended business model

Start negotiations as a Light MVNO using a licensed Zimbabwean host operator, with Onesa providing the brand and customer experience. Evaluate branded resale as an alternative with clear subscriber and exit rights. Negotiate satellite eligibility explicitly; it must not be assumed to come with normal mobile wholesale access. See the [business brief](docs/BUSINESS_BRIEF.md) and [partner questions](docs/PARTNER_DUE_DILIGENCE.md).

## Repository map

| Path | Purpose |
| --- | --- |
| `onesa-mobile-frontend/web/` | React/TypeScript public website and customer-account demo |
| `onesa-mobile-frontend/web/src/internal/` | Internal company operations preview, independently loaded at `/internal/` |
| `onesa-mobile-frontend/mobile/` | Independent Expo/React Native app |
| `onesa-mobile-frontend/mobile/ios/` | Generated native Xcode project for iPhone and iPad |
| `onesa-mobile-frontend/mobile/android/` | Generated native Android project |
| `onesa-mobile-backend/` | Independent Node.js/TypeScript development API, OpenAPI contract and container definition |
| `docs/` | Business brief, architecture, roadmap, due diligence and dated validation |
| `../.github/workflows/onesa-mobile-ci.yml` | Monorepo-root workflow with independent Mobile web, backend and native qualification jobs |

There is no shared runtime or cross-import between frontend and backend. Each package has its own dependencies and lockfile. iPad uses the iOS project with tablet support enabled.

## Start developing

Install Node.js **24.12 or newer in the 24 LTS line** and Git, then clone the Onesa UG repository:

```sh
git clone https://github.com/DruHustle/onesa-ug.git
cd onesa-ug/onesa-mobile
```

Open separate terminals for the packages you need.

For a single development command that runs both web and API after installing the web dependencies, run `npm run dev` from the `onesa-mobile` product folder. This launches independent processes and shuts them down together. It exposes the web development server to your local network; use only in a trusted development environment. The mobile package remains separate.

### Website

```sh
cd onesa-mobile-frontend/web
npm ci
npm run dev
```

Open **http://localhost:5173**. The demo works independently. The Help screen can check the backend through a local Vite proxy when that backend is running.

Open **http://localhost:5173/internal/** for the internal operations preview. It uses synthetic records and local demo state, with no staff authentication or real customer records. It is a separate interface, not a security boundary. Live company operations require server-enforced staff roles, MFA and audit storage before deployment; the proposed production operations hostname is documented but not configured.

### Backend

```sh
cd onesa-mobile-backend
npm ci
npm run check
npm start
```

The API listens at **http://127.0.0.1:4000**. Start with `/healthz` or `/v1/readiness`. It exposes proposed plans and fictional usage; unavailable mutations return an explicit error. See its [README](onesa-mobile-backend/README.md) for configuration and Docker commands.

### Native app

```sh
cd onesa-mobile-frontend/mobile
npm ci
npm start
```

Use a compatible Expo development environment. `npm run ios` requires macOS/Xcode; `npm run android` requires an Android development environment. Native signing and developer/store accounts must be configured for distribution. The [mobile README](onesa-mobile-frontend/mobile/README.md) explains generation, local builds and limitations. This repository does not include a signed IPA, APK or AAB.

## What the preview does

- Explains ordinary mobile access, direct-to-cell satellite access and dish-based Wi-Fi separately.
- Lets a visitor explore Everyday, Reach and Family & Farm concepts.
- Shows compact fictional account information and realistic pending service states.
- Provides independent mobile navigation, concept selection and reset.
- Provides a separate internal operations preview for subscriber reviews, billing, support, partners and team/audit planning.
- Exposes documented backend contracts and rejects unimplemented service activation, identity and payment operations.

## What comes next

Host agreement and applicable licence; confirmed satellite access; approved subscriber-registration process; identity and authorization; database/retention design; carrier provisioning; payment reconciliation and invoices; support operations; signed native builds; physical-device and provider acceptance; controlled customer pilot.

The business and roadmap documents describe those as future work. They are not claims of implemented integrations. Existing Onesa hosting must not receive live subscriber records until its jurisdiction, encryption and key-custody design is qualified.

## Checks

| Package | Command |
| --- | --- |
| Web | `npm test && npm run build` |
| Backend | `npm run check` |
| Mobile | `npm run verify` |

Run each in its package directory after `npm ci`. Read [validation](docs/VALIDATION.md) for exactly what was and was not tested.

No blanket open-source licence is granted for original Onesa source. Third-party framework/native-template files retain their respective licences and notices.

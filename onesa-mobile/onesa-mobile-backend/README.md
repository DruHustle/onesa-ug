# Onesa Mobile backend starter

This is a **read-only demonstration**, not a mobile operator, payment service or customer identity system. It runs independently of the website and native app and imports no shared frontend code. Node.js 24 executes the TypeScript using its built-in type stripping; TypeScript is a development dependency for checking types. There are no runtime npm dependencies.

## Run locally

Use Node.js 24.12 or newer within the Node.js 24 release line.

```bash
cd onesa-mobile-backend
npm ci
npm run check
npm start
```

The API listens on `http://127.0.0.1:4000` by default. The code runs without `npm ci` if Node.js 24 is already installed; installing dependencies is needed for type checking. `npm run dev` enables file watching. Environment files are not loaded automatically. Export environment variables yourself, or use `node --env-file=.env src/server.ts` after copying `.env.example` to a local, uncommitted `.env` file.

| Setting | Default | Meaning |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Listening interface. Use `0.0.0.0` inside a container or for deliberate local-device testing. |
| `PORT` | `4000` | Integer from 1 to 65535. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated exact HTTP(S) origins, with no wildcard, path or trailing slash. An empty value allows no browser origins. |

There is deliberately **no configuration switch to activate payments, identity, SIMs or satellite service**. These capabilities require real implementations and qualified commercial/regulatory arrangements. `NODE_ENV=production` does not change this behavior.

## API

| Method and resource | Result |
| --- | --- |
| `GET /healthz` | Process health. `productionReady: false` remains explicit. |
| `GET /v1/catalog` | Proposed Everyday, Reach and Family & Farm concepts. Prices and allowances are `null`. |
| `GET /v1/readiness` | Every production feature is unavailable and awaiting providers/approvals. |
| `GET /v1/demo/account` | Clearly fictional identity and usage with no phone number, email or live measurement. |
| `POST`, `PUT`, `PATCH`, `DELETE /v1/activations` | `503 SERVICE_NOT_READY`; no provisioning takes place. |
| `POST`, `PUT`, `PATCH`, `DELETE /v1/payments` | `503 SERVICE_NOT_READY`; no money is collected. |
| `POST`, `PUT`, `PATCH`, `DELETE /v1/auth` | `503 SERVICE_NOT_READY`; no customer account or login is created. |

The four read resources also support `HEAD` and restricted `OPTIONS`. Mutation preflights return `503`. Unknown resources return `404`, unsupported methods return `405`, and malformed targets, any query parameters or bodies on read resources return `400`. The API accepts only exact static paths. See [`openapi.json`](openapi.json) for the OpenAPI 3.1 contract.

JSON responses identify `mode: "demo"` and `serviceStatus: "prelaunch"`. Usage figures on the demo account are an illustration of a future screen, not a commercial allowance. There is no database, disk write, account registration, email/SMS delivery, payment collection or carrier call. Submitted bodies are never parsed, logged, echoed or persisted; unavailable operations are rejected and their connections closed. Do not send personal information to this starter. A hosting proxy may have its own logging configuration and must be reviewed separately before deployment.

An allowed browser origin is not authentication. Origin-free requests can read the public demonstration. The starter has no private customer API. Do not add real account data until authentication, authorization and storage have been implemented and verified.

## Integration boundaries

[`src/contracts/providers.ts`](src/contracts/providers.ts) defines future typed boundaries for carrier provisioning/usage, satellite eligibility, OIDC identity verification and payment processing/webhook verification. They are interfaces, not working integrations. No Starlink or carrier API endpoint is assumed. An account or eSIM alone does not establish satellite eligibility.

Future integrations must obtain live capability and provenance from the contracted provider. Keep the account holder/subscriber separate from a payer who funds a family member. Verify amount and currency, authenticate provider webhooks, enforce idempotency and reconcile provider records before treating any payment as paid. Production PostgreSQL, customer identity, authorization, migrations and operational services are intentionally outside this demonstration.

## Container

```bash
docker build -t onesa-mobile-backend .
docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  -p 127.0.0.1:4000:4000 \
  -e CORS_ALLOWED_ORIGINS=http://localhost:5173 \
  onesa-mobile-backend
```

The image runs as the unprivileged `node` user, installs no runtime dependencies and checks `/healthz`. Its Node 24 Alpine base is a moving major-version tag; pin a reviewed image digest during release qualification. HTTP is intended for local use or behind a configured HTTPS reverse proxy. The image exposes demonstration APIs only and cannot sell or activate service.

## Verification

`npm run check` checks types and exercises real local HTTP requests: the proposal/catalog contract, fictional data labeling, fail-closed activation/payment/auth operations, exact CORS allowlisting, method routing, body/target validation and environment flags that cannot enable providers. These checks do not establish real satellite, payment, identity or carrier functionality.

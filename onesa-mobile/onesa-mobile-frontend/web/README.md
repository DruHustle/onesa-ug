# Onesa Mobile web

Responsive concept website and customer-account demo. All plans are proposed; all balances are fictional. No identity document, payment or subscriber information is collected. Nothing activates a SIM or satellite service.

## Run

Use Node.js 24 LTS. From this directory:

```sh
npm ci
npm run dev
```

Open http://localhost:5173. `npm run build` runs TypeScript checks and creates `dist/`; `npm test` verifies that a successful API response cannot be displayed as live carrier readiness. `npm run preview` serves a production build locally.

The demo works without the API. For the Help screen's development connection check, run the backend on port 4000. The Vite development server proxies `/api` to it; production hosting needs an explicit same-origin reverse proxy if this check is retained.

## What works

- Responsive concept page, connectivity-path explorer, plan selection and FAQs.
- Compact account demo with overview, proposed plans, billing explanation and readiness help.
- Keyboard navigation, visible focus, reduced-motion support and status announcements.
- A bounded, read-only API readiness check with a clear unavailable state.

## Internal operations

`/internal/` loads a separate operations interface from `src/internal/`. All records and actions are synthetic local demonstrations. The public website does not link to this route. Its absence from public navigation is not access control: staff authentication, backend authorization, MFA and durable audit records must be implemented before real company/customer data is connected. A proposed production separation uses `mobile.onesa.eu` for public/customer experiences and `ops.mobile.onesa.eu` for staff; neither hostname is configured by this starter.

## Before customer use

Replace demo fixtures through documented backend endpoints. Integrate approved identity, provisioning, billing and support workflows. Add end-to-end acceptance coverage for those live flows and validate device-specific accessibility. This starter is not a complete telecom self-service portal.

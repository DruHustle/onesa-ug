# Mobile website deployment

The first hosted scope is the prelaunch website and its clearly labelled synthetic previews. Customer and staff route shells are included, but account, authentication, record, payment and network APIs are unavailable until the actual Mobile backend and shared identity are commissioned. A website deployment does not establish a working mobile network.

## Target and build

| Setting | Value |
| --- | --- |
| Public target | `https://mobile.onesa.eu` |
| Vercel project | `onesa-mobile` / `prj_VsgXltJg2z5BKPadggrKqZEBAOZ0` |
| Vercel team | `team_ZCFijEEeYUAKYka9HEyEeyGm` |
| Repository | `DruHustle/onesa-ug` |
| Project root | `onesa-mobile/onesa-mobile-frontend/web` |
| Runtime / framework | Node.js 24 / Vite |
| Install / build / output | `npm ci` / `npm run build` / `dist` |

The project and domain attachment were created and domain ownership verified during the deployment preparation. The provider-confirmed DNS record is CNAME **`mobile` → `b57a37bb0ba6b30a.vercel-dns-017.com.`**, managed in the existing Cloudflare `onesa.eu` zone. DNS publication, certificate readiness and actual serving behavior require readback; project creation and ownership verification do not establish a live website. Use DNS-only initially for this target. Existing Vercel deployment protection remains enabled for URLs other than custom domains.

Project settings select the web root; `vercel.json` intentionally contains no `rootDirectory` key. This deployment needs no backend URL, identity client secret, authentication key or database credential. Do not upload private environment files or the rest of the monorepo as standalone web assets.

## Routing and availability

The root serves the public application, including its `#demo` synthetic customer preview. `/account/`, `/internal/` and `/preview/internal/` support direct navigation and refresh through explicit SPA rewrites. Existing static assets retain their actual paths; unknown routes are not rewritten into a successful homepage. Account, staff and preview shells carry `noindex` response headers. HTML and API responses are non-cacheable; content-hashed `/assets/` files can be cached.

Every `/api` and `/api/...` path resolves to one dependency-free Vercel Node function in `api/unavailable.mjs`. It returns HTTP **503** and a JSON `BACKEND_NOT_CONNECTED` error, including health, session, sign-in, callback and mutation paths. HEAD has the same status and no body. It reads no credentials, query strings or request bodies, performs no upstream request, sets no cookie and does not emulate an authenticated or healthy API. The workspace displays the explicit unavailable response and does not open a functional account. The local Vite development proxy and the Docker gateway remain separate runtime paths.

Security headers restrict scripts and connections to the same origin, prohibit framing, suppress referrers and disable camera, microphone and geolocation access. The public canonical and Open Graph URL are exactly `https://mobile.onesa.eu/`. No wildcard upstream, cross-origin credential forwarding or new external script is configured.

## Verification and later integration

Run `npm test` and `npm run build` from the web package. The deployment tests exercise the real holding handler and check the configured route/cache boundaries. These local checks do not substitute for Vercel's deployed router. Before reporting the website live, verify the exact deployed source, HTTPS certificate, public/custom-domain visibility, direct SPA paths, asset MIME types, security headers, and JSON 503 responses for both GET and POST under `/api`. Verify health also returns 503 and no session cookie is issued. Preserve the prior deployment for ordinary website rollback.

Replacing the holding response requires the real persistent API, exact-origin/CSRF/proxy qualification, approved secret custody, and a separately commissioned Onesa Mobile identity client with callback `https://mobile.onesa.eu/api/v1/auth/onesa/callback`. The Portal application includes migration 015, but its existing owner identity release tooling is still pinned to migration 014 and three products; it needs its own reviewed release extension. See the [runtime and recovery guide](../infra/runtime/README.md). Production subscriber registration, charging, provisioning and satellite access remain blocked by the actual provider and regulatory dependencies.

Official routing/runtime references: [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite), [vercel.json configuration](https://vercel.com/docs/project-configuration/vercel-json), and [Node.js functions](https://vercel.com/docs/functions/runtimes/node-js).

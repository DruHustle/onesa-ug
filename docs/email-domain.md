# Onesa email domain and sender policy

Use the visible sending domain `onesa.eu` for all product email, as requested on
2026-11-04. Product names live in the address's local part and the friendly sender
name. This policy does not create mailboxes, enable a delivery integration or
establish that the new domain has completed provider verification.

## Product senders

| Product | Friendly sender and primary address | Operational alerts |
| --- | --- | --- |
| Onesa Logistics | `Onesa Logistics <notifications-logistics@onesa.eu>` | `alerts-logistics@onesa.eu` |
| Smart Farmer | `Smart Farmer <notifications-farmer@onesa.eu>` | `alerts-farmer@onesa.eu` |
| Smart Factory | `Smart Factory <notifications-factory@onesa.eu>` | `alerts-factory@onesa.eu` |
| Onesa Robot | `Onesa Robot <notifications-robot@onesa.eu>` | `alerts-robot@onesa.eu` |
| Onesa Drone | `Onesa Drone <notifications-drone@onesa.eu>` | `alerts-drone@onesa.eu` |
| Pasofi | `Pasofi <notifications-pasofi@onesa.eu>` | `alerts-pasofi@onesa.eu` |
| Onesa Portal | `Onesa Portal <notifications-portal@onesa.eu>` | `alerts-portal@onesa.eu` |
| Onesa AI | `Onesa AI <notifications-ai@onesa.eu>` | `alerts-ai@onesa.eu` |

`notifications-` identifies normal system messages. Reserve `alerts-` for
actionable operational events with the existing deduplication, backoff and
production/staging notification controls. The `pasofi` spelling follows the
current product repository and the owner's exact requested suffix.

One shared Onesa account continues to serve the enabled products. Registration,
verification, password recovery and cross-product access remain the Portal
identity service's responsibility. Reserve `Onesa Accounts <accounts@onesa.eu>`
for a dedicated shared identity channel; do not create separate product accounts
or credentials to introduce product notification addresses. The current Portal
outbox has one `MAIL_FROM` for its existing mail types, so the reserved account
sender does not imply automatic category-based routing.

Portal and AI source examples select their primary addresses above. Robot and
Drone have no independent mail transport in the consolidated source. The other
products have separate source repositories and retain independent releases;
listing their addresses here does not change their runtime configuration.

## Provider responsibilities

Resend delivers application messages over HTTPS. Render and Oracle host
applications and store their private mail configuration. A Render web custom
domain is independent of Resend email-domain verification. Verify `onesa.eu` once
in the intended Resend account, then send from the product local parts above.
Resend does not require a separately registered sender identity for each address.

Cloudflare holds the current authoritative DNS. Preserve existing Zoho MX records
for staff inboxes and replies. The sender addresses are not newly provisioned
inboxes; `MAIL_REPLY_TO=info@onesa.eu` reuses the existing approved contact mailbox.
If product-specific support replies are later needed, create and verify the
corresponding Zoho aliases before advertising them or changing Reply-To.

Read the exact DKIM and Return-Path records from the selected Resend domain.
Depending on when the domain was created, Resend can provide CNAME pairs or
MX/TXT records. Its technical Return-Path subdomain can coexist with the single
visible `@onesa.eu` sender domain. Do not replace Zoho root MX, invent record
values, duplicate SPF records at one hostname or weaken existing DMARC policy.

Use separate send-only credentials for the intended product/environment where
supported, scoped to `onesa.eu`. Do not assume a key scoped to `mail.onesa.eu`
authorizes the parent domain. Domain scoping does not by itself enforce a
per-address restriction within that domain. Keys stay server-side in existing
secret custody, never frontend/public environment variables, Git or logs.

## Configuration contract

Portal worker:

```dotenv
MAIL_PROVIDER=resend
RESEND_API_KEY=<private-send-only-key>
MAIL_FROM=Onesa Portal <notifications-portal@onesa.eu>
MAIL_REPLY_TO=info@onesa.eu
```

AI API and its existing identity-mail worker:

```dotenv
ONESA_MAIL_PROVIDER=disabled
ONESA_RESEND_API_KEY=<private-ai-send-only-key>
ONESA_MAIL_FROM=Onesa AI <notifications-ai@onesa.eu>
ONESA_MAIL_REPLY_TO=info@onesa.eu
```

Keep AI delivery disabled until its sender, private delivery key, provider
credential and worker have been qualified. Setting the sender name alone must
not enable mail. Shared identity remains controlled by its existing feature flag;
this email policy neither enables native AI registration nor duplicates accounts.

Sender validation rejects control characters, malformed addresses and address
lists before transport use. Valid explicit values are preserved byte for byte.
An existing verified `mail.onesa.eu` sender remains accepted during migration;
the application never silently rewrites it to `onesa.eu`.

## Runtime migration and verification

### Observed setup on 2026-11-04

The root domain `onesa.eu` is now created in Resend's Ireland (`eu-west-1`)
region. Its exact provider-issued DKIM TXT record and the `rsend.onesa.eu` and
`send.onesa.eu` DNS-only CNAME records were saved and read back in Cloudflare.
Resend subsequently reported the domain as **Verified**, with DKIM and both
`rsend` and `send` records also **Verified**. Its domain event recorded completed
verification at 00:53 UTC. Sending is enabled; receiving through Resend remains
disabled so the existing Zoho inbox routing stays authoritative.

No test message was sent. No live runtime sender, sending credential or worker
configuration was changed. Existing mail domains remain in place while migration
and pending-delivery reconciliation are outstanding; the address policy above
does not claim that deployed workers have switched to the root domain.

### Worker cutover

Before changing a deployed sender or Reply-To, inspect the effective configuration
in its actual hosting environment and verify the new domain/key. Finish or
reconcile pending, leased/running and ambiguously accepted mail under its original
configuration. Resend binds idempotency to a request body; changing the sender
while retrying an old key can fail. Do not reset attempts, recreate jobs, delete
delivery evidence or remove the old domain merely to force retry success.

Change only the selected mail settings and retain unrelated values and secrets.
Deploy through the product's existing release process. Validate provider
acceptance, delivery/bounce state and actual inbox receipt separately using an
approved recipient. Fake transport tests do not send real email and do not prove
DNS verification or external delivery. No automatic email test sends are included
in these changes.

Render Free blocks the usual SMTP ports; its applications should use Resend's
HTTPS API. All Render services observed during this review are suspended staging
services, so changing them would not update the active Oracle workloads. The
sender configuration must be applied to the worker that actually sends mail.

## References

- [Resend sender addresses](https://resend.com/docs/knowledge-base/how-do-I-create-an-email-address-or-sender-in-resend)
- [Resend verified domains](https://resend.com/docs/dashboard/domains/introduction)
- [Resend sending records and existing MX](https://resend.com/docs/knowledge-base/how-do-i-avoid-conflicting-with-my-mx-records)
- [Render environment variables and deployment behavior](https://render.com/docs/configure-environment-variables)
- [Render Free networking limits](https://render.com/docs/free)

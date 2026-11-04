# Repository consolidation and retirement

`DruHustle/onesa-ug` preserves the four Onesa product source trees and their
original Git ancestry. Sharing a checkout does not merge product runtime
authority, configuration, databases, signing identities, safety decisions, or
release evidence.

## Imported source boundaries

The original public main revisions used for the imports are fixed in
`scripts/ci/config.py`. These are historical scan boundaries, not deployment
approvals.

| Product directory | Original repository | Imported main commit |
| --- | --- | --- |
| `onesa-company-portal` | `DruHustle/onesa-company-portal` | `dbd59ed292d29a96a99af5fb45e28b429cf9bea2` |
| `onesa-ai-platform` | `DruHustle/onesa-ai-platform` | `4d4222e3b549eb78dcf817c6cf13a8aa91087415` |
| `onesa-robot` | `DruHustle/onesa-robot` | `26240cbdc20eea520cdb816d75247b87ae860fa4` |
| `onesa-drone` | `DruHustle/onesa-drone` | `005a92fe687756d8552fd64284bc88866742a9f9` |

Before subsequent fixes, each imported subtree matched the original main tree by
path, file mode, and Git object ID. The imported main histories do not include
every unmerged branch, pull request, issue, release attachment, repository
setting, or external deployment dependency. Preserve those separately before
retirement.

## Active verification

GitHub discovers workflows at the root. The product workflow copies are reviewed
source inputs; nested workflow files do not execute independently from this
checkout. `scripts/ci/generate_workflows.py` generates the following active files:

| Generated workflow | Source or responsibility |
| --- | --- |
| `verify.yml` | Conservative selection, root publication/security checks, required aggregate result |
| `_verify-portal.yml` | Portal `.github/workflows/verify.yml` |
| `_verify-platform.yml` | AI Platform `.github/workflows/ci.yml` |
| `_verify-robot.yml` | Robot `.github/workflows/scaffold.yml` |
| `_verify-drone.yml` | Drone `.github/workflows/verify.yml` |
| `_pipeline-portal.yml` | Portal `.github/workflows/_pipeline-review.yml` |
| `_pipeline-platform.yml` | AI Platform `.github/workflows/_pipeline-review.yml` |
| `_pipeline-robot.yml` | Robot `.github/workflows/_pipeline-review.yml` |

Each generated product file records the SHA256 of its source workflow. Generation
retains jobs, dependencies, conditions, services, matrices, timeouts, browser and
container checks, audits, and security thresholds. It translates shell working
directories, cache dependencies, artifact paths, workspace references, and local
reusable workflows. Pre-checkout policy/database preparation runs at the root,
where a product directory does not yet exist. Artifact names include the product
to prevent collisions across reusable workflows.

Push, schedule, and dispatch events select all products. Pull requests use Git
changes only when the base is a full resolvable commit and every path is
canonical. Changes to root files, workflow controls, shared identity, contract
snapshots, migrations, and product scripts select every product. Rename detection
is disabled for selection so a cross-product move selects both its old and new
locations. A selected product executes its whole original suite, including
previously conditional components.

The aggregate **Onesa required verification** result always runs. It requires
successful root preparation and security, plus success for every selected
product. Missing outputs, malformed selection, cancellation, failure, and
unexpected skips cannot produce a passing aggregate result. Configure branch
protections for this exact check after confirming its hosted run. Retain the
review and environment controls required by each product's release policy.

The jobs retain hosted-runner and private-repository included-allowance guards.
Their permissions are read-only. No deployment secrets are passed to reusable
verification workflows. Browser package preparation and Portal recovery fixtures
accept the exact consolidated repository identity while retaining their Linux,
disposable hosted-runner, privilege, revision, and host-safety checks.

## Pinned contracts and verification provenance

AI Platform's public documentation pipeline previously checked out two sibling
repositories. It now reads the exact allowlisted files from the preserved local
Git ancestry using `scripts/ci/materialize_docs_source.py`. The existing
`onesa-ai-platform/docs/ecosystem/source-revisions.json` retains its original
historical repository identities, full commits, and individual SHA256 digests.
The materializer validates ancestry, paths, file limits, and every digest before
writing any source file. It refuses aliases and nonempty destinations. It uses
no mutable branch, sibling checkout, private document discovery, or network
fetch.

Portal, AI Platform, and Robot runtime image records now use the consolidated
repository identity, verified candidate commit, product path, and product tree.
They require the expected Git origin, the exact workflow revision, and clean
product source. Drone's manifest producer independently validates its checkout
identity and records both the root tree and product tree. Consolidated records
explicitly set `verification_only: true` and `release_authorized: false`.
Existing release consumers retain their original repository and evidence
validation. Migration of those consumers requires a separately reviewed schema
and authority transition; a passing consolidated record cannot stand in for an
old repository's release approval.

## Publication boundaries

The root publication scanner inspects the consolidated Git index and publishable
working files. Scanning staged blobs separately prevents a secret staged earlier
from being hidden by a later clean working copy. Each product uses its own
path/credential rules. Root files are checked against all product rules. Symlinks,
submodule aliases, unresolved index stages, private/generated paths, and detected
credentials fail the gate. Diagnostics include paths and rule names only.

Each nested scanner preserves standalone behavior. Consolidated use requires
`--monorepo-root ..`; the product must be an expected direct child of the actual
Git root with the reviewed root scanner. `--history` covers the product's
original imported ancestry and subsequent product changes. It does not relabel
another product's history under the wrong policy.

Root actionlint and offline zizmor inspect the active workflows. Gitleaks scans
all publishable source, using each product's existing configuration for its own
scope. Only bounded security result metadata is uploaded. Product pipeline
security tests and scans remain required alongside these root checks.

Original product workflow scans run in disposable exports of their publishable
source, each with its own temporary Git root. This keeps actionlint's local
reusable-workflow resolution within the original product namespace. The exact
product security script and scanner thresholds are preserved; historical deploy
workflows are analyzed without activating them at the consolidated root.

## Retiring an old repository

Deletion is the last migration operation. For each repository:

1. Verify the expected old main and its complete reachable history are preserved
   by object identity. Inventory every other branch and tag; preserve or review
   all commits that are not reachable from the imported main.
2. Resolve or explicitly preserve open pull requests and issues. Keep review
   discussions, required decisions, and unmerged source changes accessible.
3. Preserve release attachments and operational evidence in their approved
   private locations. A public source import is not a destination for private
   release evidence, credentials, mailbox data, or corporate records.
4. Migrate hosting repository URLs, product root directories, branch mappings,
   webhooks, deploy keys, environment/secret bindings, protection rules, and
   release consumers. Verify each service's source and runtime behavior against
   the new revision. Keep suspended services suspended until deployment is
   explicitly authorized.
5. Obtain successful consolidated hosted verification and the product's required
   deployment/hardware qualification evidence. Install the replacement required
   checks and review controls. Preserve rollback and recovery access.
6. Confirm that no active service, source consumer, workflow, branch, or release
   attachment still depends on the old repository. Verify archival custody and
   checksums, then perform the authorized retirement.

The migration audit on 2026-11-04 found non-main source work and open reviews in
the Portal, AI Platform, and Robot repositories; open Drone safeguard work; and
draft AI Platform release attachments requiring private preservation. Render
staging service definitions still referenced three old Onesa repositories and
were suspended. Those facts require rechecking at retirement time. They are not
resolved merely by importing main or enabling this verification workflow.

Smart Factory and IMSOP are separate consolidated products. Their private source,
release evidence, and retirement decisions remain outside this public Onesa
repository. Do not import them here to simplify repository cleanup.

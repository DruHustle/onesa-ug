# Onesa UG

Onesa UG contains the public software for the Company Portal, AI Platform, Robot,
and Drone. Each product keeps its own application, configuration, dependency
locks, tests, container builds, and release policy.

| Folder | Project | Development instructions |
| --- | --- | --- |
| `onesa-company-portal` | Company Portal and shared identity | [Build and test](onesa-company-portal/docs/engineering/BUILD_AND_TEST.md) |
| `onesa-ai-platform` | AI Platform | [Product README](onesa-ai-platform/README.md) |
| `onesa-robot` | Robot | [Build and test](onesa-robot/docs/engineering/BUILD_AND_TEST.md) |
| `onesa-drone` | Drone | [Local development](onesa-drone/docs/engineering/local-development.md) |

## Verification

The root `Onesa verification` workflow runs on pull requests and pushes to `dev`,
`staging`, and `main`, on a weekly schedule, and by manual dispatch. Pushes,
scheduled runs, and manual runs execute every product suite. Pull requests may
select affected products; repository controls, shared identity, contract changes,
and ambiguous Git evidence select all products. Every selected product runs its
complete existing verification, including its browser, database, container,
security, and release-contract tests.

The required aggregate result is **Onesa required verification**. It fails when
any selected product or repository gate fails, is cancelled, is missing, or is
unexpectedly skipped. Configure this check in branch protection after its first
successful hosted run. The workflow uses read permissions and synthetic fixtures;
it does not deploy services or grant hardware or release authorization.

Root workflow files are generated from the reviewed product verification
workflows. To verify a workflow edit locally:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --no-deps -r scripts/ci/requirements.lock
.venv/bin/python scripts/ci/generate_workflows.py
.venv/bin/python scripts/ci/generate_workflows.py --check
.venv/bin/python -m unittest discover -s scripts/ci -p 'test_*.py'
.venv/bin/python scripts/repository_hygiene.py
```

Run application tests and builds from the relevant product directory using its
instructions and locked dependencies. Product publication checks require the
explicit consolidated boundary, for example:

```sh
cd onesa-drone
python3 scripts/repository_hygiene.py --monorepo-root .. --history
```

This preserves the standalone scanners' refusal to scan an arbitrary ancestor
repository. The root scanner checks both staged blobs and publishable working
files, with each product's restrictions and all product restrictions for root
files. Passing a software check establishes only the behavior that check covers.
Hardware qualification still requires the product's reviewed physical safety,
operator, device, and integration evidence.

## Domains and migration

[Email domain conventions](docs/email-domain.md) define the shared `onesa.eu`
sender addresses and the remaining provider/DNS requirements. Secrets, mailbox
data, deployment evidence, and corporate records belong in their approved private
locations, outside this public repository.

[Repository migration](docs/repository-migration.md) describes the imported
history, workflow generation, source provenance, and prerequisites for retiring
the old repositories. Existing deployments and release consumers must be migrated
and qualified before their source repositories are removed. Legacy deployment
workflows remain historical inputs inside product folders; no root deployment
workflow is enabled by this consolidation.

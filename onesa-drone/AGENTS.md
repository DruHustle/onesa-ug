# Onesa Drone engineering policy

This product lives at `onesa-drone/` in `DruHustle/onesa-ug`. Preserve independent
builds, releases, authentication, data and runtime dependencies within the consolidated
repository; do not recreate nested Git repositories or sibling submodules. Run product
commands from this directory. Root workflows execute CI; nested legacy workflows are
specifications only. Use dev → staging → main with PRs and exact-source checks.
Preserve concurrent work and data. No paid resources without budget approval.
No license is assigned. Credentials, customer records and private deployment bundles
must never enter Git or CI artifacts. Use synthetic fixtures and inspect staged diffs.

Simulation is the only permitted execution mode. Do not enable physical flight,
network MAVLink, hardware serial, ROS actuation or generative AI mission authorization.
The separate safety supervisor must validate every launch. Simulation, replay and
real observations must remain distinct. A visual twin is not validated flight physics.

Use Node 24 and Python 3.11. Run backend tests, frontend typecheck/build, browser
checks and `python3 scripts/repository_hygiene.py --monorepo-root ..` before staging. Record actual results and
unverified gates. Pin dependencies and design artifacts; no runtime sibling imports.
Appearance follows prefers-color-scheme only. Respect reduced motion and forced colors.

Production requires checked source, staging acceptance, provider readback, rollback,
privacy review and owner authorization. Never bypass protection or invent approval.

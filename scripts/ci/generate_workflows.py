"""Adapt complete product verification to the consolidated checkout deterministically.

The product workflows remain reviewed source inputs. This generator translates
paths and source provenance; it does not enable any deployment workflow.
"""

import argparse
import copy
import hashlib
import re
from pathlib import Path

import yaml
from config import (
    CHECKOUT,
    MOBILE_WORKFLOW_SOURCES,
    PRODUCTS,
    ROOT,
    SETUP_PYTHON,
    SOURCE_WORKFLOWS,
    UPLOAD_ARTIFACT,
)
from oracle_request import ALLOWED_REFS, OWNER, REPOSITORY, REPOSITORY_ID, WORKFLOW_PATH


class WorkflowLoader(yaml.SafeLoader):
    """GitHub uses YAML 1.2: `on` is a key, never the YAML 1.1 boolean True."""


WorkflowLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in values if tag != "tag:yaml.org,2002:bool"]
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
WorkflowLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|false|True|False|TRUE|FALSE)$"),
    list("tTfF"),
)


class WorkflowDumper(yaml.SafeDumper):
    def ignore_aliases(self, _data):
        return True


def represent_string(dumper, value):
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None
    )


WorkflowDumper.add_representer(str, represent_string)


def load(path):
    return yaml.load(path.read_text(), Loader=WorkflowLoader)


def hosted_policy_step():
    """The same read-only visibility and allowance guard for every entry point."""
    return {
        "name": "Verify hosted execution, visibility and included-allowance policy",
        "env": {
            "GH_TOKEN": "${{ github.token }}",
            "EXPECTED_PRIVATE": "${{ github.event.repository.private }}",
            "PRIVATE_VALIDATION_ENABLED": "${{ vars.ONESA_PRIVATE_HOSTED_VALIDATION_ENABLED }}",
        },
        "run": (
            'test "$RUNNER_ENVIRONMENT" = github-hosted\n'
            'actual=$(gh api "repos/$GITHUB_REPOSITORY" --jq ".private")\n'
            'test "$actual" = "$EXPECTED_PRIVATE" || { echo "Repository visibility changed"; exit 1; }\n'
            'if [ "$actual" = true ] && [ "$PRIVATE_VALIDATION_ENABLED" != true ]; then\n'
            '  echo "Private hosted verification requires explicit included-allowance opt-in"\n'
            "  exit 1\nfi\n"
        ),
    }


def mobile_workflow(source):
    """Keep Mobile's complete root-relative graph with the shared runner guard."""
    document = copy.deepcopy(source)
    if document.get("permissions") != {"contents": "read"}:
        raise ValueError("Mobile verification permissions require migration review")
    for job in document["jobs"].values():
        if "uses" in job or not isinstance(job.get("steps"), list):
            raise ValueError("Mobile reusable workflow changes require migration review")
        # The native and matrix jobs have product-level defaults. This guard
        # runs before checkout, while those directories do not yet exist.
        job["steps"].insert(0, {**hosted_policy_step(), "working-directory": "."})
    return document


def workspace_strings(value, product):
    if isinstance(value, dict):
        return {key: workspace_strings(item, product) for key, item in value.items()}
    if isinstance(value, list):
        return [workspace_strings(item, product) for item in value]
    if isinstance(value, str):
        value = value.replace(
            "${{ github.workspace }}", "${{ github.workspace }}/" + product
        )
        return re.sub(
            r"\$(?:GITHUB_WORKSPACE\b|\{GITHUB_WORKSPACE\})",
            "$GITHUB_WORKSPACE/" + product,
            value,
        )
    return value


def prefix_paths(value, product):
    result = []
    for line in value.splitlines():
        if not line:
            result.append(line)
            continue
        negate = "!" if line.startswith("!") else ""
        path = line[len(negate) :]
        if path.startswith(("/", "~", "${{", "$RUNNER_TEMP", "$GITHUB_WORKSPACE")):
            result.append(line)
        else:
            result.append(negate + product + "/" + path.removeprefix("./"))
    return "\n".join(result) + ("\n" if value.endswith("\n") else "")


def adapt_steps(steps, key):
    product = PRODUCTS[key]
    result = []
    checked_out = False
    for original in steps:
        step = workspace_strings(copy.deepcopy(original), product)
        uses = step.get("uses", "")
        if uses.startswith("actions/checkout@"):
            repository = step.get("with", {}).get("repository")
            if repository:
                peers = {
                    "DruHustle/onesa-company-portal": "portal",
                    "DruHustle/onesa-ai-robot": "robot",
                }
                if key != "platform" or repository not in peers:
                    raise ValueError(
                        "Unexpected external source checkout; review required"
                    )
                # Only the manifest's public files are materialized. Original
                # revision and SHA256 pinning remain in force after retirement.
                step.pop("uses")
                step.pop("with")
                step["name"] = (
                    "Materialize pinned "
                    + peers[repository]
                    + " contracts from imported history"
                )
                step["run"] = (
                    "python3 ../scripts/ci/materialize_docs_source.py --source "
                    + peers[repository]
                )
                step["working-directory"] = product
            else:
                step.setdefault("with", {})["persist-credentials"] = False
                step["with"]["fetch-depth"] = 0
                checked_out = True
        elif "run" in step:
            if not checked_out:
                # GitHub starts pre-checkout policy/database preparation at an
                # empty workspace; product defaults would fail before checkout.
                step["working-directory"] = "."
            else:
                directory = step.get("working-directory", ".")
                if (
                    directory.startswith(("/", "${{", "$"))
                    or ".." in Path(directory).parts
                ):
                    raise ValueError(
                        "Unexpected shell working directory; review required"
                    )
                step["working-directory"] = product + (
                    "/" + directory.removeprefix("./") if directory != "." else ""
                )
            if original.get("run") == "python3 scripts/ci/paths.py":
                step["run"] = "python3 ../scripts/ci/selection.py --product " + key
                step.pop("env", None)
            step["run"] = step["run"].replace(
                "scripts/repository_hygiene.py",
                "scripts/repository_hygiene.py --monorepo-root ..",
            )
            step["run"] = step["run"].replace(
                "python3 scripts/release/evidence.py manifest",
                "python3 ../scripts/ci/runtime_manifest.py --product " + key,
            )
            step["run"] = step["run"].replace(
                "python3 scripts/ci/security.py --output",
                "python3 ../scripts/ci/product_security.py --product "
                + key
                + " --output",
            )
            if (
                step["run"]
                == "python3 -m unittest discover -s scripts/ci -p 'test_*.py'"
            ):
                step["run"] = (
                    "python3 ../scripts/ci/product_security.py --product "
                    + key
                    + " --tests"
                )
        if "with" in step:
            for field in ("cache-dependency-path", "path"):
                if field in step["with"]:
                    step["with"][field] = prefix_paths(step["with"][field], product)
            if uses.startswith("actions/upload-artifact@"):
                step["with"]["name"] = key + "-" + step["with"]["name"]
        result.append(step)
    return result


def adapt(source, key, pipeline=False):
    product = PRODUCTS[key]
    jobs = workspace_strings(copy.deepcopy(source["jobs"]), product)
    for name, job in jobs.items():
        if "uses" in job:
            if job["uses"] != "./.github/workflows/_pipeline-review.yml":
                raise ValueError("Unexpected reusable workflow dependency")
            job["uses"] = "./.github/workflows/_pipeline-" + key + ".yml"
        else:
            # adapt_steps starts from original values to apply workspace prefixes once.
            job["steps"] = adapt_steps(source["jobs"][name].get("steps", []), key)
            if "defaults" in job:
                raise ValueError(
                    "Source workflow defaults need explicit migration review"
                )
    return {
        "name": "Onesa "
        + key
        + (" pipeline security" if pipeline else " verification"),
        "on": {"workflow_call": {}},
        "permissions": copy.deepcopy(source.get("permissions", {"contents": "read"})),
        "jobs": jobs,
    }


def publication_hygiene(root=ROOT):
    """Preserve independent source gates and coalesce their complete history scan."""
    steps = []
    policies = []
    history_command = "python scripts/repository_hygiene.py --history"
    for key in ("portal", "platform", "robot"):
        source = load(root / PRODUCTS[key] / ".github/workflows/repository-hygiene.yml")
        if source.get("permissions") != {"contents": "read"} or set(source["jobs"]) != {
            "publication-hygiene"
        }:
            raise ValueError("Publication workflow authority requires migration review")
        job = source["jobs"]["publication-hygiene"]
        if set(job) != {"if", "runs-on", "steps", "timeout-minutes"}:
            raise ValueError("Publication workflow structure requires migration review")
        if job["steps"][-1].get("run") != history_command:
            raise ValueError("The complete source-history gate must remain mandatory")
        policies.append(
            {name: job[name] for name in ("if", "runs-on", "timeout-minutes")}
        )
        adapted = adapt_steps(job["steps"], key)
        for step in adapted[:-1]:
            if "uses" in step:
                if step["uses"] not in {CHECKOUT, SETUP_PYTHON}:
                    raise ValueError(
                        "New publication tool setup requires migration review"
                    )
                options = step.get("with", {})
                if step["uses"] == SETUP_PYTHON and options != {
                    "python-version": "3.11"
                }:
                    raise ValueError("Changed publication Python setup requires review")
                if step["uses"] == CHECKOUT and (
                    set(options) - {"persist-credentials", "fetch-depth", "ref"}
                    or options.get("ref") not in {None, "${{ github.sha }}"}
                ):
                    raise ValueError("Changed publication checkout requires review")
                if key != "portal":
                    # The same pinned checkout and Python environment already
                    # serve each product. Preserve all actual policy/test steps.
                    continue
            steps.append(step)
    if any(policy != policies[0] for policy in policies[1:]):
        raise ValueError(
            "Distinct publication runner policies require migration review"
        )
    steps.append(
        {
            "name": "Scan every product and root path through preserved source history",
            "run": "python3 scripts/repository_hygiene.py --history",
            "working-directory": ".",
        }
    )
    return {**policies[0], "permissions": {"contents": "read"}, "steps": steps}


def orchestrator(root=ROOT):
    outputs = {key: "${{ steps.paths.outputs." + key + " }}" for key in PRODUCTS}
    jobs = {
        "prepare": {
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": 15,
            "permissions": {"contents": "read"},
            "outputs": outputs,
            "steps": [
                hosted_policy_step(),
                {
                    "uses": CHECKOUT,
                    "with": {"persist-credentials": False, "fetch-depth": 0},
                },
                {"uses": SETUP_PYTHON, "with": {"python-version": "3.11"}},
                {
                    "name": "Install the existing hash-locked workflow parser",
                    "run": "python -m pip install --require-hashes --no-deps -r scripts/ci/requirements.lock",
                },
                {
                    "name": "Check generated verification and regression boundaries",
                    "run": "python scripts/ci/generate_workflows.py --check\npython -m unittest discover -s scripts/ci -p 'test_*.py'\n",
                },
                {
                    "name": "Scan the consolidated index and publishable working files",
                    "run": "python scripts/repository_hygiene.py",
                },
                {
                    "id": "paths",
                    "env": {
                        "BASE_SHA": "${{ github.event.pull_request.base.sha || github.event.before }}"
                    },
                    "run": "python scripts/ci/selection.py",
                },
            ],
        },
        "pipeline-security": {
            "needs": ["prepare"],
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": 20,
            "permissions": {"contents": "read"},
            "steps": [
                {
                    "uses": CHECKOUT,
                    "with": {"persist-credentials": False, "fetch-depth": 0},
                },
                {"uses": SETUP_PYTHON, "with": {"python-version": "3.11"}},
                {
                    "name": "Install checksum-locked offline security tools",
                    "run": "python3 onesa-company-portal/scripts/ci/install_tools.py --only actionlint zizmor gitleaks",
                },
                {
                    "name": "Check active root workflows and repository secrets",
                    "run": 'python3 scripts/ci/security.py --output "$RUNNER_TEMP/monorepo-security/record.json"',
                },
                {
                    "uses": UPLOAD_ARTIFACT,
                    "if": "always()",
                    "with": {
                        "name": "monorepo-pipeline-security",
                        "path": "${{ runner.temp }}/monorepo-security/record.json",
                        "retention-days": 3,
                        "if-no-files-found": "error",
                    },
                },
            ],
        },
    }
    jobs["publication-hygiene"] = publication_hygiene(root)
    for key in PRODUCTS:
        jobs[key] = {
            "needs": ["prepare"],
            "if": "needs.prepare.result == 'success' && needs.prepare.outputs."
            + key
            + " == 'true'",
            "uses": "./.github/workflows/_verify-" + key + ".yml",
            "permissions": {"contents": "read", "pull-requests": "read"},
        }
    jobs["ci-summary"] = {
        "name": "Onesa required verification",
        "if": "always()",
        "needs": ["prepare", "pipeline-security", "publication-hygiene", *PRODUCTS],
        "runs-on": "ubuntu-24.04",
        "timeout-minutes": 5,
        "permissions": {"contents": "read"},
        "steps": [
            {"uses": CHECKOUT, "with": {"persist-credentials": False}},
            {
                "name": "Reject failed, missing, cancelled or unexpectedly skipped gates",
                "env": {"CI_RESULTS": "${{ toJSON(needs) }}"},
                "run": "python3 scripts/ci/summary.py",
            },
        ],
    }
    return {
        "name": "Onesa verification",
        "on": {
            "push": {"branches": ["dev", "staging", "main"]},
            "pull_request": {"branches": ["dev", "staging", "main"]},
            "schedule": [{"cron": "17 6 * * 1"}],
            "workflow_dispatch": {},
        },
        "permissions": {"contents": "read", "pull-requests": "read"},
        "concurrency": {
            "group": "onesa-verify-${{ github.event.pull_request.number || github.ref }}",
            "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
        },
        "jobs": jobs,
    }


def capability_request():
    """A manual metadata publisher; no host credential, command, or release gate."""
    branches = " || ".join("github.ref == '" + ref + "'" for ref in sorted(ALLOWED_REFS))
    return {
        "name": "Oracle capability request",
        "on": {"workflow_dispatch": {}},
        "permissions": {"contents": "read"},
        "concurrency": {
            "group": "onesa-oracle-capability-request",
            "cancel-in-progress": False,
        },
        "jobs": {
            "request": {
                "name": "Publish fixed read-only request",
                "if": (
                    "github.event_name == 'workflow_dispatch' && "
                    f"github.repository == '{REPOSITORY}' && "
                    f"github.repository_id == '{REPOSITORY_ID}' && "
                    f"github.actor == '{OWNER}' && github.triggering_actor == '{OWNER}' && "
                    "github.run_attempt == 1 && (" + branches + ")"
                ),
                "runs-on": "ubuntu-24.04",
                "timeout-minutes": 5,
                "steps": [
                    hosted_policy_step(),
                    {
                        "uses": CHECKOUT,
                        "with": {"persist-credentials": False, "ref": "${{ github.sha }}"},
                    },
                    {"uses": SETUP_PYTHON, "with": {"python-version": "3.11"}},
                    {
                        "name": "Bind the fixed probe to this dispatch without executing it",
                        "run": 'python3 scripts/ci/oracle_request.py --output "$RUNNER_TEMP/oracle-capability-request.json"',
                    },
                    {
                        "uses": UPLOAD_ARTIFACT,
                        "with": {
                            "name": "oracle-capability-request-${{ github.run_id }}-${{ github.run_attempt }}",
                            "path": "${{ runner.temp }}/oracle-capability-request.json",
                            "if-no-files-found": "error",
                            "retention-days": 1,
                        },
                    },
                ],
            },
        },
    }


def rendered(root=ROOT):
    files = {}
    for key, product in PRODUCTS.items():
        source_path = Path(product) / ".github/workflows" / SOURCE_WORKFLOWS[key]
        source = load(root / source_path)
        files["_verify-" + key + ".yml"] = (adapt(source, key), source_path)
        if "pipeline-security" in source["jobs"]:
            pipeline_path = Path(product) / ".github/workflows/_pipeline-review.yml"
            files["_pipeline-" + key + ".yml"] = (
                adapt(load(root / pipeline_path), key, pipeline=True),
                pipeline_path,
            )
    files["verify.yml"] = (orchestrator(root), None)
    files[Path(WORKFLOW_PATH).name] = (capability_request(), None)
    for filename, source_path in MOBILE_WORKFLOW_SOURCES.items():
        files[filename] = (mobile_workflow(load(root / source_path)), source_path)
    result = {}
    for filename, (document, source_path) in files.items():
        text = yaml.dump(
            document,
            Dumper=WorkflowDumper,
            sort_keys=False,
            width=110,
            allow_unicode=True,
        )
        if (
            re.search(r"\$\{\{[^}]*\bsecrets\.", text)
            or "secrets: inherit" in text
            or "pull_request_target" in document["on"]
        ):
            raise ValueError(
                "Verification cannot acquire deployment secrets or privileged PR triggers"
            )
        header = "# Generated by scripts/ci/generate_workflows.py; edit source inputs and regenerate.\n"
        if source_path:
            header += "# Source: " + source_path.as_posix() + "\n"
            header += (
                "# Source SHA256: "
                + hashlib.sha256((root / source_path).read_bytes()).hexdigest()
                + "\n"
            )
        elif filename == "verify.yml":
            for key in ("portal", "platform", "robot"):
                source = (
                    Path(PRODUCTS[key]) / ".github/workflows/repository-hygiene.yml"
                )
                header += "# Publication source: " + source.as_posix() + "\n"
                header += (
                    "# Source SHA256: "
                    + hashlib.sha256((root / source).read_bytes()).hexdigest()
                    + "\n"
                )
        result[filename] = header + text
    return result


def unexpected_workflows(directory, expected):
    return {
        path.name for suffix in ("*.yml", "*.yaml") for path in directory.glob(suffix)
    } - set(expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    directory = ROOT / ".github/workflows"
    expected = rendered()
    drift = [
        name
        for name, content in expected.items()
        if not (directory / name).is_file() or (directory / name).read_text() != content
    ]
    extra = unexpected_workflows(directory, expected)
    if args.check:
        if drift or extra:
            raise SystemExit(
                "Generated workflow drift: " + ", ".join(sorted([*drift, *extra]))
            )
        print(f"All {len(expected)} generated workflows match their reviewed inputs")
        return
    if extra:
        raise SystemExit(
            "Preserve and review unexpected root workflows: " + ", ".join(sorted(extra))
        )
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in expected.items():
        (directory / name).write_text(content)
    print(f"Generated {len(expected)} credential-free workflows")


if __name__ == "__main__":
    main()

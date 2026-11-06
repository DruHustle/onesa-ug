"""The consolidation must retain every original verification job and safety gate."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import generate_workflows as workflows
from config import FIELDS, MOBILE_WORKFLOW_SOURCES, PRODUCTS, ROOT, SOURCE_WORKFLOWS


class WorkflowTests(unittest.TestCase):
    def test_additional_active_workflows_are_rejected_for_both_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("verify.yml", "unexpected.yaml", "other.yml", "inactive.txt"):
                (root / name).write_text("synthetic fixture\n")
            self.assertEqual(
                workflows.unexpected_workflows(root, {"verify.yml": "expected"}),
                {"unexpected.yaml", "other.yml"},
            )

    def test_generated_files_match_reviewed_inputs(self):
        expected = workflows.rendered()
        self.assertEqual(len(expected), 11)
        for name, text in expected.items():
            self.assertEqual((ROOT / ".github/workflows" / name).read_text(), text)

    def test_mobile_sources_preserve_every_job_and_trigger_with_only_shared_guard(self):
        generated = workflows.rendered()
        for filename, source_path in MOBILE_WORKFLOW_SOURCES.items():
            source = workflows.load(ROOT / source_path)
            before = copy.deepcopy(source)
            result = workflows.mobile_workflow(source)
            for job in result["jobs"].values():
                self.assertEqual(
                    job["steps"].pop(0),
                    {**workflows.hosted_policy_step(), "working-directory": "."},
                )
            self.assertEqual(result, source)
            self.assertEqual(source, before, "Generating workflows must not mutate source")
            self.assertIn("# Source: " + source_path.as_posix(), generated[filename])
            self.assertIn(
                "# Source SHA256: " + hashlib.sha256((ROOT / source_path).read_bytes()).hexdigest(),
                generated[filename],
            )

    def test_mobile_requires_review_for_new_authority_or_reusable_jobs(self):
        source = workflows.load(ROOT / MOBILE_WORKFLOW_SOURCES["onesa-mobile-ci.yml"])
        source["permissions"] = {"contents": "write"}
        with self.assertRaises(ValueError):
            workflows.mobile_workflow(source)
        source["permissions"] = {"contents": "read"}
        source["jobs"]["verify"] = {"uses": "./.github/workflows/unreviewed.yml"}
        with self.assertRaises(ValueError):
            workflows.mobile_workflow(source)

    def test_mobile_xcode_template_is_materialized_without_replacing_local_configuration(self):
        native = ROOT / "onesa-mobile/onesa-mobile-frontend/mobile"
        scripts = json.loads((native / "package.json").read_text())["scripts"]
        self.assertEqual(scripts["preios"], "npm run prepare:ios")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ios").mkdir()
            template = (native / "ios/.xcode.env.example").read_bytes()
            (root / "ios/.xcode.env.example").write_bytes(template)
            subprocess.run(["sh", "-ec", scripts["prepare:ios"]], cwd=root, check=True)
            destination = root / "ios/.xcode.env"
            self.assertEqual(destination.read_bytes(), template)
            destination.write_text("# Existing local Node configuration\n")
            subprocess.run(["sh", "-ec", scripts["prepare:ios"]], cwd=root, check=True)
            self.assertEqual(destination.read_text(), "# Existing local Node configuration\n")
        source = workflows.load(ROOT / MOBILE_WORKFLOW_SOURCES["onesa-mobile-native-compile.yml"])
        steps = source["jobs"]["ios"]["steps"]
        prepare = next(i for i, step in enumerate(steps) if step.get("run") == "npm run prepare:ios")
        pods = next(i for i, step in enumerate(steps) if step.get("run") == "pod install --project-directory=ios")
        self.assertLess(prepare, pods)

    def test_all_original_jobs_dependencies_conditions_and_steps_survive(self):
        for key, product in PRODUCTS.items():
            source = workflows.load(
                ROOT / product / ".github/workflows" / SOURCE_WORKFLOWS[key]
            )
            result = workflows.adapt(source, key)
            self.assertEqual(set(source["jobs"]), set(result["jobs"]))
            self.assertEqual(result["on"], {"workflow_call": {}})
            self.assertNotIn("concurrency", result)
            for name, original in source["jobs"].items():
                adapted = result["jobs"][name]
                for field in (
                    "needs",
                    "if",
                    "timeout-minutes",
                    "runs-on",
                    "strategy",
                    "permissions",
                    "services",
                ):
                    self.assertEqual(
                        adapted.get(field),
                        workflows.workspace_strings(original.get(field), product),
                    )
                if "steps" in original:
                    self.assertEqual(len(original["steps"]), len(adapted["steps"]))
                    for before, after in zip(original["steps"], adapted["steps"]):
                        for field in ("if", "continue-on-error", "timeout-minutes"):
                            self.assertEqual(before.get(field), after.get(field))

    def test_no_precheckout_step_uses_missing_product_directory(self):
        for key, product in PRODUCTS.items():
            source = workflows.load(
                ROOT / product / ".github/workflows" / SOURCE_WORKFLOWS[key]
            )
            for job in workflows.adapt(source, key)["jobs"].values():
                checkout = False
                for step in job.get("steps", []):
                    if step.get("uses", "").startswith("actions/checkout@"):
                        self.assertNotIn("repository", step.get("with", {}))
                        self.assertIs(step["with"]["persist-credentials"], False)
                        checkout = True
                    elif "run" in step:
                        self.assertEqual(
                            step["working-directory"].split("/")[0],
                            product if checkout else ".",
                        )

    def test_root_summary_is_always_required_and_secret_free(self):
        root = workflows.orchestrator()
        summary = root["jobs"]["ci-summary"]
        self.assertEqual(summary["if"], "always()")
        self.assertEqual(
            set(summary["needs"]),
            {"prepare", "pipeline-security", "publication-hygiene", *PRODUCTS},
        )
        self.assertEqual(summary["name"], "Onesa required verification")
        for text in workflows.rendered().values():
            document = workflows.yaml.load(text, Loader=workflows.WorkflowLoader)
            self.assertNotIn("pull_request_target", document["on"])
            self.assertNotRegex(text, r"\$\{\{[^}]*\bsecrets\.")
            self.assertNotIn("secrets: inherit", text)
            for job in document["jobs"].values():
                for step in job.get("steps", []):
                    uses = step.get("uses")
                    if uses:
                        self.assertRegex(uses, r"^[^@]+@[a-f0-9]{40}$")

    def test_selected_products_cannot_skip_internal_suites(self):
        for key in PRODUCTS:
            result = subprocess.check_output(
                [
                    sys.executable,
                    str(ROOT / "scripts/ci/selection.py"),
                    "--product",
                    key,
                ],
                text=True,
            )
            for field in FIELDS:
                self.assertIn('"' + field + '": true', result)
            self.assertIn('"applications": ["frontend", "backend"]', result)

    def test_product_paths_caches_and_artifacts_are_translated_once(self):
        steps = [
            {"run": "echo policy"},
            {"uses": "actions/checkout@" + "a" * 40},
            {
                "uses": "actions/setup-node@" + "b" * 40,
                "with": {
                    "cache-dependency-path": "frontend/package-lock.json\nbackend/package-lock.json\n"
                },
            },
            {
                "run": 'echo "$GITHUB_WORKSPACE/x" "${GITHUB_WORKSPACE}/y" "${{ github.workspace }}/z"',
                "working-directory": "frontend",
            },
            {
                "uses": "actions/upload-artifact@" + "c" * 40,
                "with": {
                    "name": "evidence",
                    "path": "data/report.json\n!data/private.json\n${{ runner.temp }}/safe.json\n",
                },
            },
        ]
        result = workflows.adapt_steps(steps, "robot")
        self.assertEqual(result[0]["working-directory"], ".")
        self.assertEqual(result[3]["working-directory"], "onesa-robot/frontend")
        self.assertEqual(
            result[2]["with"]["cache-dependency-path"].count("onesa-robot/"), 2
        )
        self.assertEqual(result[3]["run"].count("/onesa-robot/"), 3)
        self.assertEqual(result[4]["with"]["name"], "robot-evidence")
        self.assertIn("!onesa-robot/data/private.json", result[4]["with"]["path"])
        self.assertIn("${{ runner.temp }}/safe.json", result[4]["with"]["path"])

    def test_contract_sources_remain_pinned_without_old_repo_checkout(self):
        text = workflows.rendered()["_verify-platform.yml"]
        self.assertEqual(text.count("materialize_docs_source.py --source"), 2)
        self.assertNotIn("repository: DruHustle/onesa-company-portal", text)
        self.assertNotIn("repository: DruHustle/onesa-ai-robot", text)
        self.assertNotIn("scripts/release/evidence.py manifest", text)
        self.assertIn("runtime_manifest.py --product platform", text)

    def test_pipeline_security_and_negative_tests_keep_product_namespace(self):
        generated = workflows.rendered()
        for key in ("portal", "platform", "robot"):
            text = generated["_pipeline-" + key + ".yml"]
            self.assertIn("product_security.py --product " + key + " --output", text)
            self.assertIn("product_security.py --product " + key + " --tests", text)

    def test_independent_history_and_documentation_gates_remain_required(self):
        job = workflows.orchestrator()["jobs"]["publication-hygiene"]
        self.assertEqual(job["permissions"], {"contents": "read"})
        self.assertEqual(job["timeout-minutes"], 45)
        self.assertNotIn("needs", job)
        scans = [
            step
            for step in job["steps"]
            if "repository_hygiene.py" in step.get("run", "")
        ]
        self.assertEqual(len(scans), 1)
        self.assertEqual(
            scans[0]["run"], "python3 scripts/repository_hygiene.py --history"
        )
        self.assertEqual(scans[0]["working-directory"], ".")
        for key in ("portal", "platform", "robot"):
            source = workflows.load(
                ROOT / PRODUCTS[key] / ".github/workflows/repository-hygiene.yml"
            )
            original = source["jobs"]["publication-hygiene"]
            for field in ("if", "runs-on", "timeout-minutes"):
                self.assertEqual(job[field], original[field])
            for step in workflows.adapt_steps(original["steps"], key):
                if "run" in step and "repository_hygiene.py" not in step["run"]:
                    self.assertIn(
                        step,
                        job["steps"],
                        "A source publication policy or documentation test was dropped",
                    )
        self.assertIn(
            "publication-hygiene",
            workflows.orchestrator()["jobs"]["ci-summary"]["needs"],
        )


if __name__ == "__main__":
    unittest.main()

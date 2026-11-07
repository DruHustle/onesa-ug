"""Consolidated source evidence boundaries; no network, provider or host operations."""

import base64
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4
import zipfile


ROOT = Path(__file__).resolve().parents[2]
PRODUCTS = ("onesa-company-portal", "onesa-ai-platform", "onesa-robot")
MODULES = []
for product in PRODUCTS:
    path = ROOT / product / "scripts/release/oracle_owner.py"
    specification = importlib.util.spec_from_file_location(product.replace("-", "_") + "_source_owner", path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    MODULES.append(module)


class SourceFixture:
    def __init__(self, module, product="portal", branch="staging"):
        self.module = module
        self.now = datetime.now(timezone.utc)
        self.source = {
            "schema_version": 2, "repository": module.CONSOLIDATED_REPOSITORY,
            "repository_id": module.CONSOLIDATED_REPOSITORY_ID, "product": product,
            "source_path": module.CONSOLIDATED_PRODUCTS[product], "candidate_commit": "a" * 40,
            "source_tree": "b" * 40, "product_source_tree": "c" * 40, "branch": branch,
        }
        self.policy = {"consolidated_sources": {product: {
            "repository": self.source["repository"], "repository_id": self.source["repository_id"],
            "source_path": self.source["source_path"], "branches": ["staging", "main"],
        }}}
        repository = {"id": self.source["repository_id"], "full_name": self.source["repository"]}
        sha = self.source["candidate_commit"]
        self.prefix = "repos/" + self.source["repository"] + "/"
        self.run = {
            "id": 123, "repository": repository, "head_repository": repository,
            "head_sha": sha, "head_branch": branch, "event": "push",
            "actor": {"login": module.OWNER}, "triggering_actor": {"login": module.OWNER},
            "path": ".github/workflows/verify.yml", "run_attempt": 1,
            "created_at": (self.now - timedelta(hours=1)).isoformat(),
            "status": "completed", "conclusion": "success", "updated_at": self.now.isoformat(),
            "referenced_workflows": [
                {"path": self.source["repository"] + "/.github/workflows/" + name + "@" + sha,
                 "sha": sha, "ref": "refs/heads/" + branch}
                for name in sorted(module.CONSOLIDATED_WORKFLOWS)
            ],
        }
        self.review = {
            "number": 1, "merged": True, "state": "closed", "draft": False,
            "merged_at": self.now.isoformat(), "merge_commit_sha": sha, "merged_by": {"login": module.OWNER},
            "base": {"ref": branch, "repo": repository},
            "head": {"ref": "dev" if branch == "staging" else "staging", "repo": repository},
        }
        jobs = []
        for index, (name, required) in enumerate(module.CONSOLIDATED_JOB_STEPS.items(), 1):
            jobs.append({
                "id": index, "name": name, "run_id": self.run["id"], "head_sha": sha,
                "head_branch": branch, "run_attempt": 1, "status": "completed", "conclusion": "success",
                "steps": [
                    {"name": step, "status": "completed", "conclusion": "success"}
                    for step in (required or ["Observed hosted job"])
                ],
            })
        self.jobs = {"total_count": len(jobs), "jobs": jobs}
        self.runs = {"total_count": 1, "workflow_runs": [copy.deepcopy(self.run)]}
        self.tree = {
            "sha": self.source["source_tree"], "truncated": False,
            "tree": [{"path": self.source["source_path"], "mode": "040000", "type": "tree",
                      "sha": self.source["product_source_tree"]}],
        }
        self.archives = {}
        self.manifests = {}
        self.artifacts = {"total_count": 0, "artifacts": []}
        for index, (name, member) in enumerate(module.CONSOLIDATED_ARTIFACTS[product].items(), 1):
            record = {key: self.source[key] for key in ("repository", "source_path", "product_source_tree")}
            record.update(verification_only=True, release_authorized=False)
            if product == "drone":
                component = member.removesuffix(".json")
                record.update(source_commit=sha, source_tree=self.source["source_tree"],
                              component=component, mode="simulation")
                if component == "backend":
                    record.update(image_id="sha256:" + "d" * 64,
                                  runtime_image_id="sha256:" + "e" * 64, architecture="amd64")
                else:
                    record["files"] = {"index.html": "f" * 64, "assets/app.js": "0" * 64}
            else:
                record.update(schema_version=2, candidate_commit=sha,
                              image_digest="sha256:" + "d" * 64, security="PASS")
            self.manifests[name] = record
            self.artifacts["artifacts"].append({
                "id": index, "name": name, "expired": False,
                "workflow_run": {
                    "id": self.run["id"], "repository_id": self.source["repository_id"],
                    "head_repository_id": self.source["repository_id"], "head_branch": branch, "head_sha": sha,
                },
            })
            self.repack(name)
        self.artifacts["total_count"] = len(self.artifacts["artifacts"])
        self.api_values = {
            "user": {"login": module.OWNER},
            self.prefix.rstrip("/"): repository,
            self.prefix + "branches/" + branch: {"commit": {"sha": sha}},
            self.prefix + "git/commits/" + sha: {"sha": sha, "tree": {"sha": self.source["source_tree"]}},
            self.prefix + "git/trees/" + self.source["source_tree"]: self.tree,
            self.prefix + "commits/" + sha + "/pulls?per_page=100": [copy.deepcopy(self.review)],
            self.prefix + "pulls/1": self.review,
            self.prefix + "actions/workflows/verify.yml/runs?head_sha=" + sha + "&per_page=100": self.runs,
            self.prefix + "actions/runs/123": self.run,
            self.prefix + "actions/runs/123/jobs?filter=latest&per_page=100": self.jobs,
            self.prefix + "actions/runs/123/artifacts?per_page=100": self.artifacts,
        }
        self.calls = []
        self.github = module.GitHub("synthetic-source-fixture")
        self.github.api = self.api

    def api(self, path):
        self.calls.append(path)
        if path not in self.api_values:
            raise AssertionError("Unexpected network request in synthetic source fixture: " + path)
        return copy.deepcopy(self.api_values[path])

    def repack(self, name, *, member=None, raw=None, extra=None, mode=None):
        target = next(row for row in self.artifacts["artifacts"] if row["name"] == name)
        member = member or self.module.CONSOLIDATED_ARTIFACTS[self.source["product"]][name]
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            info = zipfile.ZipInfo(member)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ((stat.S_IFREG | 0o600) if mode is None else mode) << 16
            archive.writestr(info, json.dumps(self.manifests[name]).encode() if raw is None else raw)
            if extra is not None:
                archive.writestr(extra, b"untrusted extra artifact member")
        contents = buffer.getvalue()
        self.archives[name] = base64.b64encode(contents).decode()
        target.update(size_in_bytes=len(contents), digest="sha256:" + hashlib.sha256(contents).hexdigest())

    def verify(self):
        self.module.consolidated_source_profile(self.source, self.policy)
        with patch.object(self.module, "timestamp", side_effect=lambda: self.now):
            return self.github.verify_source(self.source, self.archives)


class SourceVerificationTests(unittest.TestCase):
    def test_all_products_and_both_promoted_branches_have_bounded_source_proof(self):
        for module in MODULES:
            for product in module.CONSOLIDATED_PRODUCTS:
                for branch in ("staging", "main"):
                    with self.subTest(module=module.__name__, product=product, branch=branch):
                        fixture = SourceFixture(module, product, branch)
                        result = fixture.verify()
                        self.assertEqual(result["source"], fixture.source)
                        self.assertTrue(result["verification_only"])
                        self.assertFalse(result["release_authorized"])
                        self.assertEqual(len(result["artifacts"]), len(fixture.archives))
                        self.assertNotIn("signature", result)
                        self.assertNotIn("record", result)
                        self.assertNotIn("id", result)
                        self.assertEqual(len(module.CONSOLIDATED_JOB_STEPS), 31)
                        with self.assertRaises(module.Rejected):
                            module.binding_valid(result["source"], fixture.policy)

    def test_product_scope_requires_new_explicit_configuration(self):
        for module in MODULES:
            cases = (
                lambda f: f.policy.clear(),
                lambda f: f.policy["consolidated_sources"]["portal"].update(source_path="onesa-robot"),
                lambda f: f.policy["consolidated_sources"]["portal"].update(repository_id=1),
                lambda f: f.policy["consolidated_sources"]["portal"].update(branches=["main"]),
                lambda f: f.policy["consolidated_sources"]["portal"].update(branches=["staging", "staging"]),
                lambda f: f.source.update(repository="DruHustle/onesa-company-portal"),
                lambda f: f.source.update(repository_id=True),
                lambda f: f.source.update(product="unknown"),
                lambda f: f.source.update(source_path="../onesa-company-portal"),
                lambda f: f.source.update(product_source_tree="c" * 39),
                lambda f: f.source.update(branch="dev"),
                lambda f: f.source.update(branch=["staging"]),
                lambda f: f.source.update(release_authorized=True),
            )
            for index, change in enumerate(cases):
                with self.subTest(module=module.__name__, case=index):
                    fixture = SourceFixture(module)
                    change(fixture)
                    with self.assertRaises(module.Rejected):
                        fixture.verify()
                    self.assertEqual(fixture.calls, [])

    def test_root_subtree_and_owner_promotion_are_independent_required_proofs(self):
        cases = (
            lambda f: f.api_values[f.prefix.rstrip("/")].update(id=1),
            lambda f: f.api_values[f.prefix + "branches/staging"]["commit"].update(sha="e" * 40),
            lambda f: f.api_values[f.prefix + "git/commits/" + "a" * 40]["tree"].update(sha="e" * 40),
            lambda f: f.tree.update(truncated=True),
            lambda f: f.tree["tree"][0].update(sha="e" * 40),
            lambda f: f.tree["tree"][0].update(mode="160000", type="commit"),
            lambda f: f.tree["tree"].append(copy.deepcopy(f.tree["tree"][0])),
            lambda f: f.review.update(merged=False),
            lambda f: f.review.update(draft=True),
            lambda f: f.review["head"].update(ref="main"),
            lambda f: f.review["head"].update(repo={"id": 1, "full_name": "untrusted/fork"}),
            lambda f: f.review["merged_by"].update(login="untrusted"),
        )
        self.assert_rejected(cases)

    def assert_rejected(self, cases):
        for module in MODULES:
            for index, change in enumerate(cases):
                with self.subTest(module=module.__name__, case=index):
                    fixture = SourceFixture(module)
                    change(fixture)
                    with self.assertRaises(module.Rejected):
                        fixture.verify()

    def test_latest_ci_cannot_fall_back_to_an_earlier_success(self):
        for module in MODULES:
            fixture = SourceFixture(module)
            fixture.run["updated_at"] = (fixture.now - timedelta(seconds=10)).isoformat()
            fixture.runs["workflow_runs"][0]["updated_at"] = fixture.run["updated_at"]
            failed = {
                **copy.deepcopy(fixture.run), "id": 124, "conclusion": "failure",
                "created_at": (fixture.now - timedelta(seconds=5)).isoformat(),
                "updated_at": fixture.now.isoformat(),
            }
            fixture.runs["workflow_runs"].append(failed)
            fixture.runs["total_count"] = 2
            fixture.api_values[fixture.prefix + "actions/runs/124"] = failed
            with self.subTest(module=module.__name__), self.assertRaises(module.Rejected):
                fixture.verify()
            self.assertNotIn(fixture.prefix + "actions/runs/123", fixture.calls)

    def test_older_run_id_with_later_attempt_cannot_hide_behind_newer_success(self):
        for module in MODULES:
            for during_artifact_read in (False, True):
                with self.subTest(module=module.__name__, during_read=during_artifact_read):
                    fixture = SourceFixture(module)
                    older = {
                        **copy.deepcopy(fixture.run), "id": 122, "run_attempt": 2, "conclusion": "failure",
                        "created_at": (fixture.now - timedelta(hours=2)).isoformat(),
                        "updated_at": (fixture.now - timedelta(seconds=1)).isoformat(),
                    }

                    def later_attempt():
                        fixture.runs["workflow_runs"].append(older)
                        fixture.runs["total_count"] = 2

                    if during_artifact_read:
                        api = fixture.github.api

                        def race(path):
                            response = api(path)
                            if path.endswith("/artifacts?per_page=100"):
                                later_attempt()
                            return response

                        fixture.github.api = race
                    else:
                        later_attempt()
                    with self.assertRaisesRegex(module.Rejected, "Overlapping or repeated"):
                        fixture.verify()
            # An older failure that settled before this fresh run remains in
            # history and does not lend authority to the new source proof.
            fixture = SourceFixture(module)
            fixture.runs["workflow_runs"].append({
                **copy.deepcopy(fixture.run), "id": 122, "conclusion": "failure",
                "created_at": (fixture.now - timedelta(hours=2)).isoformat(),
                "updated_at": (fixture.now - timedelta(hours=1, seconds=1)).isoformat(),
            })
            fixture.runs["total_count"] = 2
            self.assertFalse(fixture.verify()["release_authorized"])

    def test_run_activity_requires_unambiguous_aware_timestamps(self):
        for module in MODULES:
            for changes in (
                {"created_at": "2026-11-04T00:00:00"},
                {"created_at": "not-a-date"},
                {"updated_at": "2020-01-01T00:00:00+00:00"},
                {"updated_at": "2999-01-01T00:00:00+00:00"},
                {"run_attempt": True},
            ):
                fixture = SourceFixture(module)
                fixture.runs["workflow_runs"][0].update(changes)
                with self.subTest(module=module.__name__, changes=changes), \
                        self.assertRaisesRegex(module.Rejected, "chronology invalid"):
                    fixture.verify()

    def test_source_or_run_changes_after_artifact_read_invalidate_proof(self):
        for module in MODULES:
            for changed in ("branch", "attempt", "newer-run", "repository", "expired"):
                with self.subTest(module=module.__name__, changed=changed):
                    fixture = SourceFixture(module)
                    api = fixture.github.api

                    def race(path):
                        response = api(path)
                        if path.endswith("/artifacts?per_page=100"):
                            if changed == "branch":
                                fixture.api_values[fixture.prefix + "branches/staging"]["commit"]["sha"] = "e" * 40
                            elif changed == "attempt":
                                fixture.run.update(run_attempt=2, status="in_progress", conclusion=None)
                            elif changed == "repository":
                                fixture.run["repository"].update(id=1)
                            elif changed == "expired":
                                fixture.now += timedelta(days=1)
                            else:
                                fixture.runs["workflow_runs"].append({**copy.deepcopy(fixture.run), "id": 124})
                                fixture.runs["total_count"] = 2
                        return response

                    fixture.github.api = race
                    with self.assertRaises(module.Rejected):
                        fixture.verify()

    def test_listing_attempt_state_cannot_be_overruled_by_stale_run_details(self):
        for module in MODULES:
            for during_artifact_read in (False, True):
                fixture = SourceFixture(module)

                def change_listing():
                    fixture.runs["workflow_runs"][0].update(
                        run_attempt=2, status="in_progress", conclusion=None,
                    )

                if during_artifact_read:
                    api = fixture.github.api

                    def race(path):
                        response = api(path)
                        if path.endswith("/artifacts?per_page=100"):
                            change_listing()
                        return response

                    fixture.github.api = race
                else:
                    change_listing()
                with self.subTest(module=module.__name__, during_read=during_artifact_read), \
                        self.assertRaises(module.Rejected):
                    fixture.verify()

    def test_ci_attempt_freshness_repository_jobs_and_steps_fail_closed(self):
        cases = (
            lambda f: f.runs.update(total_count=2),
            lambda f: f.run.update(run_attempt=2),
            lambda f: f.run.update(status="in_progress"),
            lambda f: f.run.update(conclusion="failure"),
            lambda f: f.run.update(updated_at=(f.now - timedelta(days=1)).isoformat()),
            lambda f: f.run.update(updated_at=(f.now + timedelta(seconds=1)).isoformat()),
            lambda f: f.run.update(updated_at=f.now.replace(tzinfo=None).isoformat()),
            lambda f: f.run.update(path=".github/workflows/old-verify.yml"),
            lambda f: f.run["head_repository"].update(id=1),
            lambda f: f.run["triggering_actor"].update(login="untrusted"),
            lambda f: f.run["referenced_workflows"][0].update(sha="d" * 40),
            lambda f: f.run["referenced_workflows"].pop(),
            lambda f: f.jobs.update(total_count=32),
            lambda f: f.jobs["jobs"][0].update(name="renamed-required-gate"),
            lambda f: f.jobs["jobs"][0].update(head_sha="e" * 40),
            lambda f: f.jobs["jobs"][0].update(conclusion="skipped"),
            lambda f: f.jobs["jobs"][0]["steps"][0].update(conclusion="skipped"),
            lambda f: f.jobs["jobs"][0]["steps"].clear(),
            lambda f: f.jobs["jobs"][0]["steps"].append(copy.deepcopy(f.jobs["jobs"][0]["steps"][0])),
            lambda f: f.jobs["jobs"][0]["steps"].append(
                {"name": "continued-on-error", "status": "completed", "conclusion": "failure"}),
        )
        self.assert_rejected(cases)

    def test_artifact_metadata_and_supplied_bytes_are_both_required(self):
        cases = (
            lambda f: f.archives.clear(),
            lambda f: f.archives.update({"sibling-runtime": next(iter(f.archives.values()))}),
            lambda f: f.artifacts.update(total_count=4),
            lambda f: f.artifacts["artifacts"][0].update(expired=True),
            lambda f: f.artifacts["artifacts"][0].update(digest="sha256:" + "0" * 64),
            lambda f: f.artifacts["artifacts"][0].update(size_in_bytes=1),
            lambda f: f.artifacts["artifacts"][0]["workflow_run"].update(head_sha="e" * 40),
            lambda f: f.artifacts["artifacts"][0]["workflow_run"].update(id=124),
            lambda f: f.archives.update({next(iter(f.archives)): "invalid base64 bytes!"}),
        )
        self.assert_rejected(cases)

    def test_genuine_artifact_digest_does_not_approve_wrong_manifest_or_executable_member(self):
        for module in MODULES:
            changes = (
                lambda f, name: f.manifests[name].update(repository="DruHustle/onesa-company-portal"),
                lambda f, name: f.manifests[name].update(source_path="onesa-robot"),
                lambda f, name: f.manifests[name].update(product_source_tree="e" * 40),
                lambda f, name: f.manifests[name].update(candidate_commit="e" * 40),
                lambda f, name: f.manifests[name].update(verification_only=False),
                lambda f, name: f.manifests[name].update(release_authorized=True),
                lambda f, name: f.manifests[name].update(security="FAIL"),
                lambda f, name: f.manifests[name].update(image_digest="mutable:latest"),
                lambda f, name: f.manifests[name].update(schema_version=True),
            )
            for index, change in enumerate(changes):
                with self.subTest(module=module.__name__, case=index):
                    fixture = SourceFixture(module)
                    name = next(iter(fixture.archives))
                    change(fixture, name)
                    fixture.repack(name)
                    with self.assertRaises(module.Rejected):
                        fixture.verify()
            for mutation in (
                {"member": "../record.json"}, {"extra": "run.py"},
                {"mode": stat.S_IFLNK | 0o777},
                {"raw": b'{"repository":"first","repository":"duplicate"}'},
                {"raw": b'{"value":NaN}'},
                {"raw": b" " * (module.SOURCE_MANIFEST_LIMIT + 1)},
            ):
                with self.subTest(module=module.__name__, mutation=next(iter(mutation))):
                    fixture = SourceFixture(module)
                    fixture.repack(next(iter(fixture.archives)), **mutation)
                    with self.assertRaises(module.Rejected):
                        fixture.verify()

    def test_drone_source_proof_remains_simulation_only(self):
        for module in MODULES:
            for field, value in (("mode", "live"), ("source_tree", "e" * 40),
                                 ("runtime_image_id", "latest"), ("architecture", "unknown")):
                fixture = SourceFixture(module, "drone")
                name = "drone-runtime-onesa-drone-backend"
                fixture.manifests[name][field] = value
                fixture.repack(name)
                with self.subTest(module=module.__name__, field=field), self.assertRaises(module.Rejected):
                    fixture.verify()
            fixture = SourceFixture(module, "drone")
            name = "drone-runtime-onesa-drone-frontend"
            fixture.manifests[name]["files"]["../outside"] = "d" * 64
            fixture.repack(name)
            with self.subTest(module=module.__name__, field="files"), self.assertRaises(module.Rejected):
                fixture.verify()


class CommissionedEntryPointTests(unittest.TestCase):
    def create_store(self, module, fixture, root):
        key = root / "signing.pem"
        subprocess.run([module.OPENSSL, "genpkey", "-algorithm", "ED25519", "-out", str(key)],
                       check=True, capture_output=True)
        public = subprocess.check_output([module.OPENSSL, "pkey", "-in", str(key), "-pubout"])
        (root / "public.pem").write_bytes(public)
        (root / "policy.json").write_bytes(module.canonical(fixture.policy))
        trust = {
            "installation_id": str(uuid4()), "verifier_sha256": module.file_digest(module.__file__),
            "policy_sha256": module.file_digest(root / "policy.json"),
            "key_id": module.file_digest(root / "public.pem"), "openssl_sha256": module.file_digest(module.OPENSSL),
        }
        (root / "trust.json").write_bytes(module.canonical(trust))
        with sqlite3.connect(root / "records.sqlite") as database:
            database.execute("CREATE TABLE records(id TEXT PRIMARY KEY)")
        anchor = root / "fixture-anchor.json"
        anchor.write_bytes(module.canonical({
            "schema_version": 1, "installations": {str(root): {**trust, "active": True}},
        }))
        root.chmod(0o700)
        for path in root.iterdir():
            path.chmod(0o600)
        return anchor

    def test_real_commissioned_store_and_cli_verify_without_signing_or_records(self):
        for module in MODULES:
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory(
                dir=Path.home() if os.getuid() == 0 else None
            ) as raw:
                root = Path(raw).resolve()
                fixture = SourceFixture(module)
                anchor = self.create_store(module, fixture, root)
                with patch.object(module, "ANCHOR", anchor), patch.dict(os.environ, {}, clear=True):
                    store = module.Store(root, fixture.github, uid=os.getuid())
                    try:
                        with patch.object(store, "put", side_effect=AssertionError("No signed record")), \
                                patch.object(store, "runner", side_effect=AssertionError("No runtime runner")):
                            result = store.verify_source(fixture.source, fixture.archives)
                            self.assertFalse(result["release_authorized"])
                            self.assertEqual(store.db.execute("SELECT COUNT(*) FROM records").fetchone()[0], 0)
                            request = {
                                "owner_token": "synthetic-private-input", "source": fixture.source,
                                "artifact_archives": fixture.archives,
                            }
                            stdin = io.TextIOWrapper(io.BytesIO(json.dumps(request).encode()))
                            output = io.StringIO()
                            with patch.object(module, "Store", return_value=store) as construct, \
                                    patch.object(module.os, "geteuid", return_value=0), \
                                    patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", output), \
                                    patch.object(sys, "argv", ["oracle_owner", "verify-source", "--store", str(root)]):
                                module.main()
                            self.assertEqual(construct.call_args.args[0], root)
                            self.assertFalse(json.loads(output.getvalue())["release_authorized"])
                            self.assertNotIn("synthetic-private-input", output.getvalue())
                    finally:
                        store.db.close()
                    registry = json.loads(anchor.read_bytes())
                    registry["installations"][str(root)]["active"] = False
                    anchor.write_bytes(module.canonical(registry))
                    if os.getuid() == 0:
                        with self.assertRaisesRegex(module.Rejected, "commissioned"):
                            module.Store(root, fixture.github, uid=0)
                    (root / "policy.json").write_bytes(module.canonical({"consolidated_sources": {}}))
                    with self.assertRaisesRegex(module.Rejected, "pin changed"):
                        module.Store(root, fixture.github, uid=os.getuid())

    def test_source_entrypoint_rejects_operational_record_input_and_actions(self):
        for module in MODULES:
            fixture = SourceFixture(module)
            request = {"owner_token": "synthetic-private-input", "source": fixture.source,
                       "artifact_archives": fixture.archives}
            with self.subTest(module=module.__name__), patch.object(module.os, "geteuid", return_value=0):
                with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(sys, "argv", [
                    "oracle_owner", "verify-source", "--store", "/synthetic/custody",
                ]), self.assertRaises(module.Rejected):
                    module.main()
                with patch.dict(os.environ, {}, clear=True), patch.object(module, "Store") as construct, \
                        patch.object(sys, "stdin", io.TextIOWrapper(io.BytesIO(json.dumps(request).encode()))), \
                        patch.object(sys, "argv", [
                            "oracle_owner", "verify-source", "--store", "/synthetic/custody", "--record", str(uuid4()),
                        ]), self.assertRaises(module.Rejected):
                    module.main()
                construct.return_value.verify_source.assert_not_called()

    def test_new_cli_request_rejects_duplicate_keys_before_owner_custody(self):
        for module in MODULES:
            for raw in (
                b'{"owner_token":"first","owner_token":"second"}',
                b'{"source":{"branch":"staging","branch":"main"}}',
                b'{"source":NaN}',
                b'[]',
            ):
                with self.subTest(module=module.__name__, request=raw), \
                        patch.object(module.os, "geteuid", return_value=0), \
                        patch.dict(os.environ, {}, clear=True), \
                        patch.object(module, "Store") as construct, \
                        patch.object(sys, "stdin", io.TextIOWrapper(io.BytesIO(raw))), \
                        patch.object(sys, "argv", ["oracle_owner", "verify-source", "--store", "/synthetic/custody"]), \
                        self.assertRaises(module.Rejected):
                    module.main()
                construct.assert_not_called()


if __name__ == "__main__":
    unittest.main()

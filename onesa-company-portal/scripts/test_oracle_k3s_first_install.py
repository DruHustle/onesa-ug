"""Synthetic first-install/recovery tests; never contact IMDS, Docker or systemd."""

import contextlib
import copy
import io
import ipaddress
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra/oracle"))
import k3s_first_install as installer


def plan():
    return {"instance_id": "ocid1.instance.oc1.test." + "a" * 32,
            "machine_id_sha256": installer.digest(b"synthetic-machine"),
            "private_ip": "10.12.0.3", "pod_cidr": "10.120.0.0/16", "service_cidr": "10.121.0.0/16",
            "reserved_cidrs": ["10.12.0.0/16", "172.18.0.0/16", "100.64.0.0/10"],
            "workload_memory_mib": 0, "workload_disk_gib": 0}


def firewall():
    text = """*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
:ONESA_WORKER_INPUT - [0:0]
:DOCKER-USER - [0:0]
-A INPUT -j ONESA_WORKER_INPUT
-A FORWARD -i tailscale0 -j DROP
-A FORWARD -j DOCKER-USER
-A ONESA_WORKER_INPUT -i lo -j ACCEPT
-A ONESA_WORKER_INPUT -i tailscale0 -j DROP
-A ONESA_WORKER_INPUT -j DROP
-A DOCKER-USER -i eth0 -m conntrack --ctstate NEW -j DROP
-A DOCKER-USER -j RETURN
COMMIT
"""
    return {family: installer.parse_rules(text) for family in ("iptables", "ip6tables")}


def installed_rules():
    result = firewall()
    for family, chains in installer.firewall_rules(plan(), ["172.18.0.0/16"]).items():
        current = result[family]["filter"]
        for name, rules in chains.items():
            current["chains"][name] = "-"
            current["rules"].extend([["-A", name, *rule] for rule in rules])
            parent = "INPUT" if name == installer.INPUT_CHAIN else "FORWARD"
            current["rules"].insert(0, ["-A", parent, "-j", name])
    return result


class PlanTests(unittest.TestCase):
    def test_requires_exact_private_target_and_excludes_source_even_if_id_matches(self):
        data = installer.validate_plan(plan())
        identity = {"id": data["instance_id"], "displayName": "Onesa UG Backend"}
        installer.match_identity(data, identity, data["machine_id_sha256"])
        for field, value, expected in (("id", data["instance_id"] + "b", "WRONG_OCI_INSTANCE"),
                                       ("displayName", "Software Engineering Backend", "ONESA_DESTINATION_IDENTITY_REQUIRED")):
            bad = {**identity, field: value}
            with self.assertRaisesRegex(installer.Refused, expected):
                installer.match_identity(data, bad, data["machine_id_sha256"])
        with self.assertRaisesRegex(installer.Refused, "WRONG_MACHINE_IDENTITY"):
            installer.match_identity(data, identity, "b" * 64)

    def test_network_and_schema_refusals(self):
        cases = [{"private_ip": "203.0.113.9"}, {"pod_cidr": "10.12.0.0/16"},
                 {"service_cidr": "10.120.1.0/24"}, {"reserved_cidrs": []},
                 {"reserved_cidrs": ["172.18.0.0/16"]}, {"workload_memory_mib": True}, {"extra": True}]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(installer.Refused):
                installer.validate_plan({**plan(), **changes})

    def test_private_configuration_preserves_compose_ingress_and_uses_containerd(self):
        settings = installer.configuration(plan(), "onesa-test", "ens3")
        self.assertEqual(settings["bind-address"], plan()["private_ip"])
        self.assertEqual(settings["advertise-address"], settings["bind-address"])
        self.assertEqual(settings["node-ip"], settings["bind-address"])
        self.assertEqual(settings["disable"], ["traefik", "servicelb", "local-storage"])
        self.assertEqual(settings["flannel-backend"], "host-gw")
        self.assertEqual(settings["write-kubeconfig-mode"], "0600")
        self.assertNotIn("docker", settings)
        self.assertNotIn("flannel-external-ip", settings)
        self.assertIn("nodeport-addresses=127.0.0.0/8", settings["kube-proxy-arg"])

    def test_release_lock_excludes_prerelease_and_has_real_architecture_hashes(self):
        lock = installer.releases()
        self.assertFalse(lock["k3s"]["prerelease"])
        self.assertEqual(lock["k3s"]["version"], "v1.36.5+k3s1")
        for platform in lock["k3s"]["platforms"].values():
            for artifact in platform.values():
                self.assertRegex(artifact["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(artifact["size"], 1000000)
                self.assertTrue(artifact["url"].startswith("https://github.com/k3s-io/k3s/releases/download/"))
        self.assertEqual(set(lock["portainer"]["platforms"]), {"arm64", "amd64"})

    def test_storage_is_retained_local_and_never_mounts_docker(self):
        base, full = installer.manifests(installer.releases(), "onesa-test")
        storage, volume = full["items"][:2]
        self.assertEqual(storage["reclaimPolicy"], "Retain")
        self.assertEqual(volume["spec"]["persistentVolumeReclaimPolicy"], "Retain")
        self.assertEqual(volume["spec"]["local"]["path"], str(installer.STATE / "portainer"))
        self.assertNotIn("docker.sock", json.dumps(full))
        self.assertNotIn("NodePort", json.dumps(full))
        self.assertEqual(installer.portainer.by_kind(base["items"], "Service")["spec"]["type"], "ClusterIP")

    def test_server_launcher_excludes_ambient_credentials_and_proxy_settings(self):
        ambient = {"NOTIFY_SOCKET": "/run/systemd/notify", "K3S_URL": "https://unexpected.example.test",
                   "K3S_TOKEN": "synthetic-token", "HTTP_PROXY": "http://unexpected.example.test"}
        with patch.dict(installer.os.environ, ambient, clear=True), patch.object(installer.os, "execve") as execute:
            installer.clean_server_exec()
        binary, arguments, environment = execute.call_args.args
        self.assertEqual(binary, installer.BINARY)
        self.assertEqual(arguments, [str(installer.BINARY), "server", "--config", str(installer.CONFIG)])
        self.assertEqual(set(environment), {"PATH", "LANG", "LC_ALL", "NOTIFY_SOCKET"})
        self.assertNotIn("synthetic-token", repr(environment))


class FirewallTests(unittest.TestCase):
    def test_pods_cannot_inherit_existing_docker_accepts(self):
        docker_policy = [["-s", "10.0.0.0/8", "-j", "ACCEPT"], ["-j", "RETURN"]]
        original_policy = copy.deepcopy(docker_policy)
        chains = installer.firewall_rules(plan(), ["172.18.0.0/16", "192.168.40.0/24"])["iptables"]
        chains["DOCKER-USER"] = docker_policy

        def verdict(chain, interface, source, destination):
            for rule in chains[chain]:
                if "-i" in rule and rule[rule.index("-i") + 1] != interface:
                    continue
                if any(flag in rule and ipaddress.ip_address(address) not in
                       ipaddress.ip_network(rule[rule.index(flag) + 1])
                       for flag, address in (("-s", source), ("-d", destination))):
                    continue
                target = rule[rule.index("-j") + 1]
                if target in {"ACCEPT", "DROP", "RETURN"}:
                    return target
                result = verdict(target, interface, source, destination)
                if result != "RETURN":
                    return result
            return "RETURN"

        for destination in ("172.18.0.2", "192.168.40.2"):
            self.assertEqual(verdict(installer.FORWARD_CHAIN, "cni0", "10.120.0.2", destination), "DROP")
        self.assertEqual(verdict(installer.FORWARD_CHAIN, "tailscale0", "10.120.0.2", "203.0.113.2"), "DROP")
        self.assertEqual(verdict(installer.FORWARD_CHAIN, "br-existing", "10.12.0.2", "172.18.0.2"), "ACCEPT")
        self.assertEqual(verdict(installer.FORWARD_CHAIN, "cni0", "10.120.0.2", "203.0.113.2"), "ACCEPT")
        self.assertEqual(verdict(installer.FORWARD_CHAIN, "br-existing", "192.0.2.2", "172.18.0.2"), "RETURN")
        self.assertEqual(docker_policy, original_policy)

    def test_existing_policy_survives_and_docker_edits_are_rejected(self):
        before, after = firewall(), installed_rules()
        installer.require_existing_firewall(before)
        installer.preserved_firewall(before, after)
        changed = copy.deepcopy(after)
        changed["iptables"]["filter"]["rules"].remove(["-A", "DOCKER-USER", "-j", "RETURN"])
        with self.assertRaisesRegex(installer.Refused, "EXISTING_FIREWALL_CHANGED"):
            installer.preserved_firewall(before, changed)
        changed = copy.deepcopy(after)
        changed["iptables"]["filter"]["chains"]["FORWARD"] = "ACCEPT"
        with self.assertRaisesRegex(installer.Refused, "EXISTING_FIREWALL_CHANGED"):
            installer.preserved_firewall(before, changed)

    def test_api_and_kubelet_accept_only_loopback_or_local_pods(self):
        desired = installer.firewall_rules(plan(), ["172.18.0.0/16"])
        v4 = desired["iptables"][installer.INPUT_CHAIN]
        accepts = [row for row in v4 if row[-1] == "ACCEPT"]
        self.assertEqual(len(accepts), 2)
        self.assertTrue(all(row[:6] == ["-s", plan()["pod_cidr"], "-d", plan()["private_ip"] + "/32", "-i", "cni0"] for row in accepts))
        forward = desired["iptables"][installer.FORWARD_CHAIN]
        self.assertEqual(forward[0], ["-i", "tailscale0", "-j", "DROP"])
        self.assertEqual(forward[-2:], [["-j", "DOCKER-USER"], ["-j", "RETURN"]])
        self.assertIn(["-d", "172.18.0.0/16", "-i", "cni0", "-j", "DROP"], forward)
        self.assertFalse(any(row[-1] == "ACCEPT" for row in forward))
        self.assertNotIn("51820", json.dumps(desired))

    def test_saved_rule_serialization_matches_private_rule_readback(self):
        saved = """*filter
:ONESA_K3S_INPUT - [0:0]
-A ONESA_K3S_INPUT -s 10.120.0.0/16 -d 10.12.0.3/32 -i cni0 -p tcp -m tcp --dport 6443 -j ACCEPT
COMMIT
"""
        observed = installer.parse_rules(saved)["filter"]["rules"][0][2:]
        desired = installer.firewall_rules(plan(), ["172.18.0.0/16"])["iptables"][installer.INPUT_CHAIN]
        self.assertIn(observed, desired)

    def test_firewall_application_never_flushes_or_edits_docker_rules(self):
        calls = []
        def fake_run(args, **kwargs):
            calls.append(args)
            return (1, "") if "-C" in args else (0, "")
        with patch.object(installer, "snapshot_firewall", return_value=firewall()), patch.object(installer, "run", side_effect=fake_run):
            installer.apply_private_firewall(plan(), ["172.18.0.0/16"])
        self.assertFalse(any("-F" in call or "-X" in call or "iptables-restore" in call for call in calls))
        self.assertFalse(any("DOCKER-USER" in call and call.index("DOCKER-USER") == call.index("-A") + 1
                             for call in calls if "-A" in call))
        self.assertTrue(any("-I" in call and "INPUT" in call and installer.INPUT_CHAIN in call for call in calls))

    def test_guard_must_precede_kubernetes_forwarding(self):
        state = installed_rules()
        with patch.object(installer, "snapshot_firewall", return_value=state):
            installer.verify_firewall(plan(), ["172.18.0.0/16"], firewall())
        state["iptables"]["filter"]["chains"]["KUBE-FORWARD"] = "-"
        state["iptables"]["filter"]["rules"].insert(0, ["-A", "FORWARD", "-j", "KUBE-FORWARD"])
        with patch.object(installer, "snapshot_firewall", return_value=state), self.assertRaisesRegex(installer.Refused, "ORDER_CHANGED"):
            installer.verify_firewall(plan(), ["172.18.0.0/16"], firewall())


class FileAndLifecycleTests(unittest.TestCase):
    def setUp(self):
        # Production correctly rejects writable ancestors such as /tmp (1777).
        # Keep synthetic custody files beneath the test user's private home.
        self.temporary = tempfile.TemporaryDirectory(prefix="onesa-k3s-test-", dir=Path.home())
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        paths = {"STATE": self.root / "state", "RECEIPT": self.root / "state/installation.json",
                 "CONFIG_DIR": self.root / "config", "CONFIG": self.root / "config/config.yaml",
                 "KUBECONFIG": self.root / "config/k3s.yaml", "DATA": self.root / "data",
                 "LIB": self.root / "lib", "BINARY": self.root / "bin/k3s", "UNIT_DIR": self.root / "units",
                 "LOCK": self.root / "install.lock"}
        for key, value in paths.items():
            active = patch.object(installer, key, value)
            active.start()
            self.addCleanup(active.stop)
        active = patch.object(installer, "ROOT_UID", os.getuid())
        active.start()
        self.addCleanup(active.stop)
        installer.UNIT_DIR.mkdir()
        installer.BINARY.parent.mkdir()
        artifact_dir = self.root / "artifacts"
        artifact_dir.mkdir()
        self.lock = copy.deepcopy(installer.releases())
        source = {}
        for kind, name in (("binary", "k3s-arm64"), ("airgap", "k3s-airgap-images-arm64.tar.zst")):
            value = ("synthetic release " + kind).encode()
            path = artifact_dir / name
            path.write_bytes(value)
            source[kind] = path
            self.lock["k3s"]["platforms"]["arm64"][kind] = {"name": name, "size": len(value), "sha256": installer.digest(value)}
        self.facts = {"node": "onesa-test", "interface": "ens3", "observation": {"architecture": "aarch64"},
                      "firewall": firewall(), "docker_subnets": ["172.18.0.0/16"], "sources": source}
        self.commands = []

    def shared_lifecycle(self):
        module = installer.lifecycle_module(self.lock)
        module.OWNER_UID = os.getuid()
        module.STATE = self.root / "shared-lifecycle"
        module.STATE.mkdir(mode=0o700)
        module.LOCK = module.STATE / "lifecycle.lock"
        module.HOLD = module.STATE / "maintenance.json"
        module.CONFIG = self.root / "absent-recovery-config.json"
        return module

    @contextlib.contextmanager
    def mocked_host(self, failure=None):
        def fake_command(args, **kwargs):
            self.commands.append(args)
            if failure and failure(args):
                raise installer.Refused("SYNTHETIC_STAGE_FAILURE")
            if args[:2] == ["systemctl", "show"]:
                return "LoadState=loaded\nFragmentPath=" + str(installer.UNIT_DIR / args[2]) + "\nDropInPaths=\nTransient=no\n"
            return ""
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(installer, "command", side_effect=fake_command))
            stack.enter_context(patch.object(installer, "run", side_effect=lambda args, **kwargs: (self.commands.append(args) or (0, ""))))
            stack.enter_context(patch.object(installer.preflight, "docker_snapshot", return_value={"count": 2, "fingerprint": "synthetic"}))
            for function in ("apply_private_firewall", "verify_firewall", "verify_node", "verify_portainer"):
                stack.enter_context(patch.object(installer, function))
            stack.enter_context(patch.object(installer, "verify_installation", return_value={"status": "SYNTHETIC_PASS"}))
            yield

    def test_artifact_hash_and_symlink_are_rejected(self):
        directory = self.facts["sources"]["binary"].parent
        installer.artifacts(directory, "aarch64", self.lock)
        self.facts["sources"]["binary"].write_bytes(b"x" * self.lock["k3s"]["platforms"]["arm64"]["binary"]["size"])
        with self.assertRaisesRegex(installer.Refused, "HASH_MISMATCH"):
            installer.artifacts(directory, "aarch64", self.lock)
        self.facts["sources"]["binary"].unlink()
        self.facts["sources"]["binary"].symlink_to(self.facts["sources"]["airgap"])
        with self.assertRaisesRegex(installer.Refused, "FILE_INVALID"):
            installer.artifacts(directory, "aarch64", self.lock)

    def test_artifact_replacement_after_open_cannot_supply_unverified_copy(self):
        original = self.facts["sources"]["binary"]
        replacement = original.with_suffix(".replacement")
        replacement.write_bytes(b"X" * original.stat().st_size)
        original_fdopen = os.fdopen
        def replace_before_read(fd, mode, *args, **kwargs):
            if mode == "rb" and replacement.exists():
                replacement.replace(original)
            return original_fdopen(fd, mode, *args, **kwargs)
        with patch.object(installer.os, "fdopen", side_effect=replace_before_read), \
                self.assertRaisesRegex(installer.Refused, "ARTIFACT_REPLACED_DURING_READ"):
            installer.verified_artifact_bytes(original, self.lock["k3s"]["platforms"]["arm64"]["binary"])

    def test_writable_artifact_parent_is_refused(self):
        original = self.facts["sources"]["binary"]
        original.parent.chmod(0o777)
        with self.assertRaisesRegex(installer.Refused, "UNSAFE_PARENT_CUSTODY"):
            installer.verified_artifact_bytes(original, self.lock["k3s"]["platforms"]["arm64"]["binary"])

    def test_private_plan_refuses_other_users_and_symlinks(self):
        path = self.root / "private.json"
        path.write_bytes(installer.encoded(plan()))
        path.chmod(0o600)
        installer.private_file(path)
        path.chmod(0o644)
        with self.assertRaisesRegex(installer.Refused, "PRIVATE_ROOT_OWNED"):
            installer.private_file(path)
        alias = self.root / "alias"
        alias.symlink_to(path)
        with self.assertRaisesRegex(installer.Refused, "PRIVATE_ROOT_OWNED"):
            installer.private_file(alias)

    def test_first_install_journals_and_retains_dedicated_data(self):
        with self.mocked_host():
            result = installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
        self.assertEqual(result["status"], "SYNTHETIC_PASS")
        receipt = installer.load_receipt(plan())
        self.assertEqual(receipt["phase"], "READY_OWNER_QUALIFICATION_REQUIRED")
        installer.verify_owned_files(receipt)
        self.assertEqual(stat.S_IMODE(installer.RECEIPT.stat().st_mode), 0o600)
        self.assertTrue((installer.STATE / "portainer").is_dir())
        start = [call for call in self.commands if call[:2] == ["systemctl", "start"]]
        self.assertEqual(start, [["systemctl", "start", installer.UNIT]])
        self.assertFalse(any("docker" in call or "restart" in call for call in self.commands))

    def test_start_failure_holds_only_owned_unit_and_preserves_files(self):
        with self.mocked_host(failure=lambda args: args[:2] == ["systemctl", "start"]):
            result = installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
        self.assertEqual(result["status"], "HELD_REVIEW_REQUIRED")
        self.assertTrue(result["runtime_cleanup_requires_review"])
        self.assertEqual(installer.load_receipt(plan())["phase"], "HELD_REVIEW_REQUIRED")
        self.assertTrue(installer.BINARY.exists())
        self.assertTrue((installer.STATE / "portainer").exists())
        self.assertIn(["systemctl", "disable", "--now", installer.UNIT], self.commands)
        self.assertFalse(any("killall" in " ".join(call) or "uninstall" in " ".join(call) for call in self.commands))

    def test_hold_never_stops_unit_whose_contents_changed(self):
        with self.mocked_host():
            installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
            receipt = installer.load_receipt(plan())
            (installer.UNIT_DIR / installer.UNIT).write_text("unrelated unit\n")
            self.commands.clear()
            installer.hold_installation(receipt, "SYNTHETIC_DRIFT")
        self.assertEqual(self.commands, [])

    def test_stale_temporary_receipt_does_not_prevent_durable_hold(self):
        with self.mocked_host():
            installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
            stale = installer.RECEIPT.with_suffix(".new")
            stale.write_bytes(b"retained interrupted evidence")
            result = installer.hold_installation(installer.load_receipt(plan()), "SYNTHETIC_INTERRUPT")
        self.assertTrue(result["hold_persisted"])
        self.assertTrue(result["owned_unit_stop_attempted"])
        self.assertEqual(stale.read_bytes(), b"retained interrupted evidence")

    def test_hold_stops_proven_unit_even_when_receipt_storage_fails(self):
        with self.mocked_host():
            installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
            receipt = installer.load_receipt(plan())
            self.commands.clear()
            with patch.object(installer, "save_receipt", side_effect=OSError("synthetic storage failure")):
                result = installer.hold_installation(receipt, "SYNTHETIC_INTERRUPT")
        self.assertEqual(result["status"], "HOLD_PERSISTENCE_FAILED")
        self.assertFalse(result["hold_persisted"])
        self.assertTrue(result["owned_unit_stop_attempted"])
        self.assertIn(["systemctl", "disable", "--now", installer.UNIT], self.commands)

    def test_hold_refuses_effective_systemd_override(self):
        with self.mocked_host():
            installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
            receipt = installer.load_receipt(plan())
            self.commands.clear()
            with patch.object(installer, "unit_metadata", return_value={"LoadState": "loaded", "Transient": "no",
                              "FragmentPath": str(installer.UNIT_DIR / installer.UNIT), "DropInPaths": "/etc/systemd/system/service.d/extra.conf"}):
                result = installer.hold_installation(receipt, "SYNTHETIC_OVERRIDE")
        self.assertFalse(result["owned_unit_stop_attempted"])
        self.assertNotIn(["systemctl", "disable", "--now", installer.UNIT], self.commands)

    def test_successful_reinvocation_is_verification_only(self):
        with self.mocked_host():
            installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
        private_plan = installer.STATE / "plan.json"
        args = ["installer", "install", "--plan", str(private_plan)]
        lifecycle = self.shared_lifecycle()
        with patch.object(sys, "argv", args), patch.object(installer, "current_identity"), \
                patch.object(installer, "releases", return_value=self.lock), \
                patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                patch.object(installer, "verify_installation", return_value={"status": "VERIFIED_PASS"}) as verify, \
                patch.object(installer, "collect_first_install") as collect, \
                patch.object(installer, "install") as install, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(installer.main(), 0)
        self.assertTrue(json.loads(output.getvalue())["already_installed"])
        verify.assert_called_once()
        collect.assert_not_called()
        install.assert_not_called()

    def test_interrupted_receipt_cannot_restart(self):
        with self.mocked_host(failure=lambda args: args[:2] == ["systemctl", "start"]):
            installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
        args = ["installer", "install", "--plan", str(installer.STATE / "plan.json")]
        with patch.object(sys, "argv", args), patch.object(installer, "current_identity"), \
                patch.object(installer, "releases", return_value=self.lock), \
                patch.object(installer, "install") as install, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(installer.main(), 2)
        self.assertEqual(json.loads(output.getvalue())["reason"], "INTERRUPTED_INSTALLATION_REQUIRES_REVIEW")
        install.assert_not_called()

    def test_existing_shared_maintenance_blocks_install_before_any_host_mutation(self):
        lifecycle = self.shared_lifecycle()
        with lifecycle.lifecycle_lock() as guard:
            guard.begin_hold("owner-deploy", "synthetic-application", "synthetic-existing-operation")
        private_plan = self.root / "private-plan.json"
        installer.write_new(private_plan, installer.encoded(plan()))
        args = ["installer", "install", "--plan", str(private_plan), "--artifacts", str(self.facts["sources"]["binary"].parent)]
        with patch.object(sys, "argv", args), patch.object(installer, "current_identity"), \
                patch.object(installer, "releases", return_value=self.lock), \
                patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                patch.object(installer, "collect_first_install", return_value=self.facts), \
                patch.object(installer, "install") as install, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(installer.main(), 2)
        self.assertEqual(json.loads(output.getvalue())["reason"], "SHARED_HOST_MAINTENANCE_IN_PROGRESS")
        install.assert_not_called()
        self.assertFalse(installer.STATE.exists())

    def test_install_uses_real_shared_hold_then_releases_only_on_success(self):
        lifecycle = self.shared_lifecycle()
        private_plan = self.root / "private-plan.json"
        installer.write_new(private_plan, installer.encoded(plan()))
        args = ["installer", "install", "--plan", str(private_plan), "--artifacts", str(self.facts["sources"]["binary"].parent)]
        def check_hold(actual_plan, facts, lock, token):
            hold = lifecycle.read_private_json(lifecycle.HOLD)
            self.assertEqual(hold["token"], token)
            self.assertEqual(hold["kind"], installer.LEASE_KIND)
            self.assertEqual(hold["reference"], installer.digest(installer.encoded(actual_plan)))
            self.assertTrue(installer.LOCK.exists())
            return {"status": "SYNTHETIC_PASS"}
        with patch.object(sys, "argv", args), patch.object(installer, "current_identity"), \
                patch.object(installer, "releases", return_value=self.lock), \
                patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                patch.object(installer, "collect_first_install", return_value=self.facts), \
                patch.object(installer, "install", side_effect=check_hold), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(installer.main(), 0)
        self.assertFalse(lifecycle.HOLD.exists())

    def test_failed_install_keeps_real_shared_maintenance_hold(self):
        lifecycle = self.shared_lifecycle()
        private_plan = self.root / "private-plan.json"
        installer.write_new(private_plan, installer.encoded(plan()))
        args = ["installer", "install", "--plan", str(private_plan), "--artifacts", str(self.facts["sources"]["binary"].parent)]
        with patch.object(sys, "argv", args), patch.object(installer, "current_identity"), \
                patch.object(installer, "releases", return_value=self.lock), \
                patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                patch.object(installer, "collect_first_install", return_value=self.facts), \
                patch.object(installer, "install", return_value={"status": "HELD_REVIEW_REQUIRED"}), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(installer.main(), 2)
        self.assertEqual(lifecycle.read_private_json(lifecycle.HOLD)["kind"], installer.LEASE_KIND)

    def test_matching_revoked_service_hold_cannot_launch_or_change_firewall(self):
        lifecycle = self.shared_lifecycle()
        with lifecycle.lifecycle_lock() as guard:
            token = guard.begin_hold(installer.LEASE_KIND, installer.LEASE_SCOPE, installer.digest(installer.encoded(plan())))
            guard.mark_revocation("synthetic-application", "synthetic-owner-revocation")
        with self.mocked_host():
            installer.install(plan(), self.facts, self.lock, token)
        private_plan = installer.STATE / "plan.json"
        for action in ("serve", "firewall"):
            args = ["installer", action, "--plan", str(private_plan)]
            with patch.object(sys, "argv", args), patch.object(installer, "current_identity"), \
                    patch.object(installer, "releases", return_value=self.lock), \
                    patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                    patch.object(installer, "clean_server_exec") as execute, \
                    patch.object(installer, "apply_private_firewall") as firewall_apply, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(installer.main(), 2)
            self.assertEqual(json.loads(output.getvalue())["reason"], "SHARED_HOST_REVOCATION_REQUIRES_REVIEW")
            execute.assert_not_called()
            firewall_apply.assert_not_called()

    def test_matching_fields_do_not_bypass_existing_hold_schema_validation(self):
        lifecycle = self.shared_lifecycle()
        with lifecycle.lifecycle_lock() as guard:
            token = guard.begin_hold(installer.LEASE_KIND, installer.LEASE_SCOPE, installer.digest(installer.encoded(plan())))
        receipt = {"phase": "STARTING", "maintenance_token": token}
        hold = lifecycle.read_private_json(lifecycle.HOLD)
        del hold["created_at"]
        lifecycle.write_private_json(lifecycle.HOLD, hold)
        with patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                self.assertRaisesRegex(installer.Refused, "LIFECYCLE_HOLD_INVALID"):
            installer.check_service_lease(plan(), receipt, self.lock)

    def test_stale_matching_service_hold_cannot_launch_or_change_firewall(self):
        lifecycle = self.shared_lifecycle()
        with lifecycle.lifecycle_lock() as guard:
            token = guard.begin_hold(installer.LEASE_KIND, installer.LEASE_SCOPE, installer.digest(installer.encoded(plan())))
        with self.mocked_host():
            installer.install(plan(), self.facts, self.lock, token)
        receipt = installer.load_receipt(plan())
        for phase in ("FILES_PREPARED", "STARTING", "APPLYING_PORTAINER"):
            receipt["phase"] = phase
            installer.save_receipt(receipt)
            for action in ("serve", "firewall"):
                args = ["installer", action, "--plan", str(installer.STATE / "plan.json")]
                with self.subTest(phase=phase, action=action), patch.object(sys, "argv", args), \
                        patch.object(installer, "current_identity"), patch.object(installer, "releases", return_value=self.lock), \
                        patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                        patch.object(installer, "effective_owned_unit"), \
                        patch.object(installer, "clean_server_exec") as execute, \
                        patch.object(installer, "apply_private_firewall") as firewall_apply, \
                        patch.object(installer, "verify_firewall"), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(installer.main(), 2)
                    self.assertEqual(json.loads(output.getvalue())["reason"], "INSTALLATION_GLOBAL_LOCK_INACTIVE")
                execute.assert_not_called()
                firewall_apply.assert_not_called()

    def test_service_child_requires_both_active_installer_locks(self):
        lifecycle = self.shared_lifecycle()
        installer.write_new(installer.LOCK, b"")
        with lifecycle.lifecycle_lock() as guard:
            token = guard.begin_hold(installer.LEASE_KIND, installer.LEASE_SCOPE, installer.digest(installer.encoded(plan())))
            receipt = {"phase": "STARTING", "maintenance_token": token}
            with patch.object(installer, "lifecycle_module", return_value=lifecycle):
                with self.assertRaisesRegex(installer.Refused, "INSTALLATION_COMPONENT_LOCK_INACTIVE"):
                    installer.check_service_lease(plan(), receipt, self.lock)
                with installer.LOCK.open("rb") as component:
                    installer.fcntl.flock(component, installer.fcntl.LOCK_EX | installer.fcntl.LOCK_NB)
                    for phase in ("FILES_PREPARED", "STARTING", "APPLYING_PORTAINER"):
                        installer.check_service_lease(plan(), {**receipt, "phase": phase}, self.lock)
                with self.assertRaisesRegex(installer.Refused, "INSTALLATION_COMPONENT_LOCK_INACTIVE"):
                    installer.check_service_lease(plan(), receipt, self.lock)
        with patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                self.assertRaisesRegex(installer.Refused, "INSTALLATION_GLOBAL_LOCK_INACTIVE"):
            installer.check_service_lease(plan(), receipt, self.lock)

    def test_ready_service_restart_requires_completed_hold(self):
        lifecycle = self.shared_lifecycle()
        installer.write_new(installer.LOCK, b"")
        with lifecycle.lifecycle_lock() as guard:
            token = guard.begin_hold(installer.LEASE_KIND, installer.LEASE_SCOPE, installer.digest(installer.encoded(plan())))
            receipt = {"phase": "READY_OWNER_QUALIFICATION_REQUIRED", "maintenance_token": token}
            with installer.LOCK.open("rb") as component:
                installer.fcntl.flock(component, installer.fcntl.LOCK_EX | installer.fcntl.LOCK_NB)
                with patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                        self.assertRaisesRegex(installer.Refused, "SHARED_HOST_MAINTENANCE_RECONCILIATION_REQUIRED"):
                    installer.check_service_lease(plan(), receipt, self.lock)
            guard.complete_hold(token)
        with patch.object(installer, "lifecycle_module", return_value=lifecycle):
            installer.check_service_lease(plan(), receipt, self.lock)
            with lifecycle.LOCK.open("rb") as probe:
                installer.fcntl.flock(probe, installer.fcntl.LOCK_EX | installer.fcntl.LOCK_NB)

    def test_service_child_rejects_component_lock_custody_drift(self):
        lifecycle = self.shared_lifecycle()
        installer.write_new(installer.LOCK, b"")
        with lifecycle.lifecycle_lock() as guard, installer.LOCK.open("rb") as component:
            token = guard.begin_hold(installer.LEASE_KIND, installer.LEASE_SCOPE, installer.digest(installer.encoded(plan())))
            receipt = {"phase": "STARTING", "maintenance_token": token}
            installer.fcntl.flock(component, installer.fcntl.LOCK_EX | installer.fcntl.LOCK_NB)
            installer.LOCK.chmod(0o644)
            with patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                    self.assertRaisesRegex(installer.Refused, "LIFECYCLE_PRIVATE_CUSTODY"):
                installer.check_service_lease(plan(), receipt, self.lock)

    def test_service_child_rejects_component_lock_replacement_during_probe(self):
        lifecycle = self.shared_lifecycle()
        installer.write_new(installer.LOCK, b"")
        real_probe = installer.require_contended_lock
        def replace_after_probe(fd, code):
            real_probe(fd, code)
            if code == "INSTALLATION_COMPONENT_LOCK_INACTIVE":
                replacement = self.root / "replacement.lock"
                installer.write_new(replacement, b"")
                replacement.replace(installer.LOCK)
        with lifecycle.lifecycle_lock() as guard, installer.LOCK.open("rb") as component:
            token = guard.begin_hold(installer.LEASE_KIND, installer.LEASE_SCOPE, installer.digest(installer.encoded(plan())))
            receipt = {"phase": "STARTING", "maintenance_token": token}
            installer.fcntl.flock(component, installer.fcntl.LOCK_EX | installer.fcntl.LOCK_NB)
            with patch.object(installer, "lifecycle_module", return_value=lifecycle), \
                    patch.object(installer, "require_contended_lock", side_effect=replace_after_probe), \
                    self.assertRaisesRegex(installer.Refused, "LIFECYCLE_FILE_REPLACED"):
                installer.check_service_lease(plan(), receipt, self.lock)

    def test_ready_receipt_is_durable_before_units_are_enabled(self):
        observed = []
        def observe_enable(arguments):
            if arguments[:2] == ["systemctl", "enable"]:
                observed.append(installer.load_receipt(plan())["phase"])
            return False
        with self.mocked_host(failure=observe_enable):
            result = installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
        self.assertEqual(result["status"], "SYNTHETIC_PASS")
        self.assertEqual(observed, ["READY_OWNER_QUALIFICATION_REQUIRED"])

    def test_failed_ready_receipt_never_enables_units(self):
        real_save = installer.save_receipt
        def fail_ready(receipt):
            if receipt["phase"] == "READY_OWNER_QUALIFICATION_REQUIRED":
                raise OSError("synthetic ready receipt failure")
            real_save(receipt)
        with self.mocked_host(), patch.object(installer, "save_receipt", side_effect=fail_ready):
            result = installer.install(plan(), self.facts, self.lock, "synthetic-maintenance-token")
        self.assertEqual(result["status"], "HELD_REVIEW_REQUIRED")
        self.assertFalse(any(call[:2] == ["systemctl", "enable"] for call in self.commands))
        self.assertIn(["systemctl", "disable", "--now", installer.UNIT], self.commands)


if __name__ == "__main__":
    unittest.main()

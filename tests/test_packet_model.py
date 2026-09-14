"""Portable packet-contract checks; opt-in checks exercise the real native model."""

import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class PacketContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = importlib.import_module("packet_model")

    def metadata(self):
        return {
            "format": "netmambaplus-packet-v1",
            "schema_version": 1,
            "architecture": copy.deepcopy(self.packet.ARCHITECTURE),
            "input_contract": copy.deepcopy(self.packet.INPUT_CONTRACT),
            "class_mapping": {"benign": 0, "attack": 1},
            "provenance": {
                "upstream": {
                    "commit": "eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2",
                    "model_files_sha256": dict(self.packet.SOURCE_SHA256),
                    "tracked_files_verified": 47,
                },
                "initialization": {
                    "kind": "scratch", "sha256": None,
                    "position_indices": [20, 41, *range(42, 417), 442],
                    "position_table": {
                        "parameterization": "learned", "trainable": True,
                        "source_shape": [1, 443, 256], "target_shape": [1, 378, 256],
                        "origin": "fresh_native_pretrain_initialization",
                        "source_architecture": {
                            "model": "fuse3_mamba_pretrain", "arr_length": 1600,
                            "stride_size": 4, "seq_len": 20, "drop_path_rate": 0.1,
                            "size_key": "signed_sizes",
                        },
                    },
                    "copied_state_names": [],
                    "excluded_state_names": [],
                    "new_state_names": sorted(self.packet.STATE_SHAPES),
                },
                "seed": 17,
                "parameter_count": 1852416,
                "runtime": {"torch": "2.9.1+cu130", "cuda": "13.0"},
            },
            "study_metadata": {
                "data_manifest_sha256": "a" * 64,
                "protocol_sha256": "b" * 64,
                "source_sha256": {"cic": "c" * 64, "unsw": "d" * 64},
                "arm": "joint_scratch", "sources": ["cic", "unsw"],
                "seed": 17, "step": 1, "validation_selection": {"loss": 0.7},
            },
        }

    def test_import_works_without_loading_ml_packages(self):
        code = (
            "import sys, packet_model; "
            "assert not {'torch', 'numpy', 'timm', 'mamba_ssm'}.intersection(sys.modules)"
        )
        result = subprocess.run([sys.executable, "-S", "-c", code], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_flow_checkpoint_metadata_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "packet"):
            self.packet._validate_metadata({"model": {}, "epoch": 120})

    def test_valid_metadata_preserves_exact_study_binding(self):
        metadata = self.metadata()
        validated = self.packet._validate_metadata(metadata)
        self.assertEqual(validated["study_metadata"], metadata["study_metadata"])
        validated["study_metadata"]["step"] = 99
        self.assertEqual(metadata["study_metadata"]["step"], 1)

    def test_changed_packet_semantics_or_class_order_is_rejected(self):
        changes = [
            ("architecture", "arr_length", 1600),
            ("architecture", "seq_len", 20),
            ("architecture", "num_classes", 6),
            ("architecture", "drop_path_rate", 0.0),
            ("input_contract", "normalization", "payload / 255"),
            ("input_contract", "learned_input_independent_prefixes", 0),
            ("class_mapping", "benign", 1),
            ("class_mapping", "benign", False),
        ]
        for section, key, value in changes:
            with self.subTest(section=section, key=key):
                metadata = self.metadata()
                metadata[section][key] = value
                with self.assertRaises(ValueError):
                    self.packet._validate_metadata(metadata)

    def test_missing_or_malformed_data_identities_are_rejected(self):
        for key in ("data_manifest_sha256", "protocol_sha256", "source_sha256"):
            with self.subTest(key=key):
                metadata = self.metadata()
                del metadata["study_metadata"][key]
                with self.assertRaisesRegex(ValueError, "study_metadata"):
                    self.packet._validate_metadata(metadata)
        for invalid in ("bad", "A" * 64, None, True):
            metadata = self.metadata()
            metadata["study_metadata"]["protocol_sha256"] = invalid
            with self.assertRaisesRegex(ValueError, "study_metadata"):
                self.packet._validate_metadata(metadata)
        metadata = self.metadata()
        del metadata["study_metadata"]["source_sha256"]["unsw"]
        with self.assertRaisesRegex(ValueError, "study_metadata"):
            self.packet._validate_metadata(metadata)

    def test_non_json_or_nonfinite_metadata_is_rejected(self):
        for invalid in (float("nan"), float("inf"), Path("somewhere"), (1, 2), {1: "x"}):
            with self.subTest(invalid=invalid):
                metadata = self.metadata()
                metadata["study_metadata"]["extra"] = invalid
                with self.assertRaises(ValueError):
                    self.packet._validate_metadata(metadata)

    def test_changed_source_and_false_initialization_claims_are_rejected(self):
        for key, value in (("commit", "0" * 40), ("tracked_files_verified", True),
                           ("model_files_sha256", {})):
            metadata = self.metadata()
            metadata["provenance"]["upstream"][key] = value
            with self.assertRaisesRegex(ValueError, "provenance"):
                self.packet._validate_metadata(metadata)
        for key, value in (("sha256", "0" * 64), ("position_indices", [20, 41]),
                           ("copied_state_names", ["head.weight"]),
                           ("new_state_names", ["head.weight"])):
            metadata = self.metadata()
            metadata["provenance"]["initialization"][key] = value
            with self.assertRaisesRegex(ValueError, "initialization"):
                self.packet._validate_metadata(metadata)

    def test_existing_checkpoint_is_preserved_before_runtime_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "previous.pth"
            path.write_bytes(b"previous checkpoint")
            with self.assertRaises(FileExistsError):
                self.packet.save_checkpoint(path, object(), {}, {})
            self.assertEqual(path.read_bytes(), b"previous checkpoint")

    def test_old_compact_scratch_positions_and_fixed_position_claims_are_rejected(self):
        for key, value in (("position_indices", []), ("position_table", None)):
            metadata = self.metadata()
            metadata["provenance"]["initialization"][key] = value
            with self.assertRaisesRegex(ValueError, "initialization"):
                self.packet._validate_metadata(metadata)
        for key, value in (("trainable", False), ("parameterization", "fixed"),
                           ("source_shape", [1, 378, 256])):
            metadata = self.metadata()
            metadata["provenance"]["initialization"]["position_table"][key] = value
            with self.assertRaisesRegex(ValueError, "initialization"):
                self.packet._validate_metadata(metadata)

    def test_unknown_initialization_fails_before_source_or_torch_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "flow.pth"
            checkpoint.write_bytes(b"unregistered flow weights")
            with self.assertRaisesRegex(ValueError, "initialization.*SHA-256"):
                self.packet.build_model(Path(temporary) / "missing", initialization=checkpoint)

    def test_missing_source_fails_before_torch_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "checkout"):
                self.packet.build_model(Path(temporary) / "missing")


@unittest.skipUnless(os.environ.get("PACKET_MODEL_NATIVE_TESTS") == "1",
                     "set PACKET_MODEL_NATIVE_TESTS=1 for the checked CUDA environment")
class NativePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        import numpy as np
        cls.torch = torch
        cls.packet = importlib.import_module("packet_model")
        cls.upstream = Path(os.environ["PACKET_MODEL_UPSTREAM"])
        cls.pretrain = Path(os.environ["PACKET_MODEL_PRETRAIN"])
        cache = Path(os.environ["PACKET_MODEL_PAYLOAD_CACHE"])
        rows = np.concatenate([np.load(cache / f"{name}-payload.npy", mmap_mode="r",
                                       allow_pickle=False)[:2] for name in ("cic", "unsw")])
        cls.payload = torch.tensor(rows, dtype=torch.uint8, device="cuda")
        cls.study = {
            "data_manifest_sha256": "a" * 64,
            "protocol_sha256": "b" * 64,
            "source_sha256": {"cic": "c" * 64, "unsw": "d" * 64},
            "scope": "mechanical check with synthetic targets; not measured training",
        }

    def test_pretrain_maps_all_trunk_states_and_keeps_fresh_binary_head(self):
        import argparse
        torch = self.torch
        scratch, _ = self.packet.build_model(self.upstream, seed=17, device="cpu")
        transferred, provenance = self.packet.build_model(
            self.upstream, initialization=self.pretrain, seed=17, device="cpu")
        with torch.serialization.safe_globals([argparse.Namespace]):
            source = torch.load(self.pretrain, map_location="cpu", weights_only=True)["model"]
        states = transferred.state_dict()
        for name, value in states.items():
            if name == "head.weight":
                self.assertTrue(torch.equal(value, scratch.state_dict()[name]))
            else:
                expected = (source[name][:, [20, 41, *range(42, 417), 442], :]
                            if name == "pos_embed" else source[name])
                self.assertTrue(torch.equal(value, expected), name)
        init = provenance["initialization"]
        self.assertEqual(len(init["copied_state_names"]), 50)
        self.assertEqual(set(init["excluded_state_names"]), set(source) - set(states))
        self.assertEqual(len(init["excluded_state_names"]), 31)
        self.assertEqual(init["new_state_names"], ["head.weight"])
        self.assertEqual(sum(p.numel() for p in transferred.parameters()), 1852416)

    def test_scratch_positions_equal_fresh_native_full_table_after_same_mapping(self):
        torch = self.torch
        scratch, scratch_provenance = self.packet.build_model(self.upstream, seed=17, device="cpu")
        scratch_rng = torch.get_rng_state().clone()
        scratch_cuda_rng = torch.cuda.get_rng_state_all()
        transferred, transferred_provenance = self.packet.build_model(
            self.upstream, initialization=self.pretrain, seed=17, device="cpu")
        self.assertTrue(torch.equal(scratch_rng, torch.get_rng_state()))
        self.assertTrue(all(torch.equal(before, after) for before, after in
                            zip(scratch_cuda_rng, torch.cuda.get_rng_state_all())))
        native = importlib.import_module("models_net_mamba_fuse3")
        torch.manual_seed(17)
        fresh = native.fuse3_mamba_pretrain(arr_length=1600, stride_size=4, seq_len=20,
                                           drop_path_rate=0.1, size_key="signed_sizes")
        expected = fresh.pos_embed[:, [20, 41, *range(42, 417), 442], :]
        self.assertTrue(torch.equal(scratch.pos_embed, expected),
                        "scratch must select from the fresh native 443-position table")
        self.assertTrue(torch.equal(scratch.head.weight, transferred.head.weight))
        self.assertFalse(torch.equal(scratch.pos_embed, transferred.pos_embed),
                         "the learned pretrained position values are part of the transfer treatment")
        self.assertTrue(scratch.pos_embed.requires_grad)
        self.assertTrue(transferred.pos_embed.requires_grad)
        self.assertEqual(scratch_provenance["initialization"]["position_indices"],
                         transferred_provenance["initialization"]["position_indices"])

    def test_pretrain_checks_every_loaded_and_excluded_tensor_shape(self):
        import argparse
        torch = self.torch
        self.assertEqual(self.packet.repro.sha256_file(self.pretrain), self.packet.PRETRAIN_SHA256)
        with torch.serialization.safe_globals([argparse.Namespace]):
            source = torch.load(self.pretrain, map_location="cpu", weights_only=True)["model"]
        native = self.packet._native_module(self.upstream)
        fresh = native.fuse3_mamba_pretrain(arr_length=1600, stride_size=4, seq_len=20,
                                           drop_path_rate=0.1, size_key="signed_sizes")
        self.assertEqual({name: tuple(value.shape) for name, value in source.items()},
                         {name: tuple(value.shape) for name, value in fresh.state_dict().items()})
        self.packet._check_state(source, torch, pretrain=True)
        for name in source:
            with self.subTest(name=name):
                malformed = dict(source)
                malformed[name] = source[name].unsqueeze(0)
                with self.assertRaisesRegex(ValueError, "shape mismatch"):
                    self.packet._check_state(malformed, torch, pretrain=True)

    def test_real_payload_gradients_and_safe_checkpoint_roundtrip(self):
        torch = self.torch
        model, provenance = self.packet.build_model(
            self.upstream, initialization=self.pretrain, seed=23)
        inputs = []
        hook = model.register_forward_pre_hook(lambda _, args: inputs.append(args))
        model.train()
        result = self.packet.forward_payload(model, self.payload)
        hook.remove()
        self.assertEqual(tuple(result["logits"].shape), (4, 2))
        self.assertEqual([tuple(x.shape) for x in inputs[0]], [(4, 1, 1, 1500), (4, 0), (4, 0)])
        self.assertTrue(torch.equal(inputs[0][0].reshape(4, 1500), self.payload.float() / 127.5 - 1))
        loss = torch.nn.functional.cross_entropy(result["logits"],
                                                 torch.tensor([0, 1, 0, 1], device="cuda"))
        loss.backward()
        for name, parameter in model.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
            self.assertTrue(torch.isfinite(parameter.grad).all(), name)
            self.assertGreater(float(parameter.grad.norm()), 0, name)
        before = model.head.weight.detach().clone()
        torch.optim.AdamW(model.parameters(), lr=1e-4).step()
        self.assertFalse(torch.equal(before, model.head.weight))
        model.eval()
        with torch.no_grad():
            expected = self.packet.forward_payload(model, self.payload)["logits"]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "packet.pth"
            saved = self.packet.save_checkpoint(path, model, provenance, self.study)
            raw = torch.load(path, map_location="cpu", weights_only=True)
            self.assertEqual(set(raw), {"metadata", "model"})
            self.assertEqual(raw["metadata"]["study_metadata"], self.study)
            loaded, recovered = self.packet.load_checkpoint(path, self.upstream)
            self.assertFalse(loaded.training)
            self.assertEqual(saved, recovered)
            with torch.no_grad():
                actual = self.packet.forward_payload(loaded, self.payload)["logits"]
            self.assertTrue(torch.equal(expected, actual))
            report = {
                "status": "passed", "scope": self.study["scope"],
                "real_payloads_per_source": 2, "device": torch.cuda.get_device_name(),
                "torch": str(torch.__version__), "loss": float(loss.detach()),
                "gradient_norms": {name: float(parameter.grad.norm())
                                   for name, parameter in model.named_parameters()},
                "checkpoint_roundtrip_exact": True,
                "checkpoint_sha256": saved["checkpoint"]["sha256"],
                "provenance": provenance,
            }
            if os.environ.get("PACKET_MODEL_PROBE_REPORT"):
                report_path = Path(os.environ["PACKET_MODEL_PROBE_REPORT"])
                with report_path.open("x", encoding="utf-8") as stream:
                    json.dump(report, stream, indent=2, allow_nan=False)
                    stream.write("\n")

    def test_forward_rejects_wrong_dtype_shape_and_device(self):
        torch = self.torch
        model, _ = self.packet.build_model(self.upstream, seed=3)
        for invalid in (self.payload.float(), self.payload[:, :-1], self.payload[0],
                        self.payload[:0], self.payload.cpu(), [[0] * 1500]):
            with self.subTest(type=type(invalid)):
                with self.assertRaises((TypeError, ValueError)):
                    self.packet.forward_payload(model, invalid)

    def test_saved_checkpoint_rejects_flow_contract_state_and_provenance_drift(self):
        torch = self.torch
        model, provenance = self.packet.build_model(self.upstream, seed=5, device="cpu")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            path = base / "packet.pth"
            self.packet.save_checkpoint(path, model, provenance, self.study)
            good = torch.load(path, map_location="cpu", weights_only=True)
            invalids = []
            invalids.append({"model": model.state_dict(), "epoch": 120})
            changed = copy.deepcopy(good)
            changed["metadata"]["architecture"]["seq_len"] = 20
            invalids.append(changed)
            changed = copy.deepcopy(good)
            del changed["model"]["encoder_blocks.0.mixer.A_log"]
            invalids.append(changed)
            changed = copy.deepcopy(good)
            changed["model"]["head.weight"] = torch.zeros(6, 256)
            invalids.append(changed)
            changed = copy.deepcopy(good)
            changed["model"]["head.weight"] = changed["model"]["head.weight"].half()
            invalids.append(changed)
            changed = copy.deepcopy(good)
            changed["model"]["head.weight"][0, 0] = float("nan")
            invalids.append(changed)
            for index, raw in enumerate(invalids):
                with self.subTest(index=index):
                    invalid = base / f"invalid-{index}.pth"
                    torch.save(raw, invalid)
                    with self.assertRaises(ValueError):
                        self.packet.load_checkpoint(invalid, self.upstream, device="cpu")
            changed_provenance = copy.deepcopy(provenance)
            changed_provenance["seed"] += 1
            with self.assertRaisesRegex(ValueError, "provenance"):
                self.packet.save_checkpoint(base / "false-init.pth", model,
                                            changed_provenance, self.study)
            self.assertFalse((base / "false-init.pth").exists())


if __name__ == "__main__":
    unittest.main()

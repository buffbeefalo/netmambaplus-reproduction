"""The pinned native NetMamba+ encoder adapted to one stored packet payload.

Torch and native CUDA dependencies are loaded only by runtime operations. The
two numeric streams contain no observations; the native model retains their
two learned, input-independent summary prefixes. This is an experimental
packet adaptation, not the original flow experiment.

Positions are learned native parameters. Both arms select the same 378 indices
from a 443-position table: scratch uses a fresh, seeded native pretraining
constructor; transfer uses the registered learned table. The learned values
are part of the transfer treatment. Paired arms keep identical fresh heads
and the extra scratch constructor preserves the caller's Torch RNG state.

``study_metadata`` must bind ``data_manifest_sha256``, ``protocol_sha256`` and
``source_sha256={"cic": ..., "unsw": ...}``. Other basic JSON study fields are
preserved. The caller verifies the referenced data/protocol files. Save/load
return the serialized metadata plus an external ``checkpoint`` object with
path, SHA-256 and bytes; a file cannot contain its own final digest.
"""

import argparse
from collections.abc import Mapping
import importlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

import repro


SOURCE_COMMIT = "eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2"
SOURCE_SHA256 = {
    "src/models/models_net_mamba_fuse3.py": "f6703590c857dd30bf0bd7522b6fbefd1f2356a4048fe8b0fc01fe9c7e94ea8d",
    "src/models/models_mamba.py": "c59dcc8375ad54ed9295f92c902019022cdf53b6fe4f0fb911311284872c3841",
    "src/models/common.py": "9a32879a50fb8139dc89ffcd63d3e174b927684bf09f800cebe85f1730997470",
}
PRETRAIN_SHA256 = "16e5a7f61c55a5be7a3feb535a59cbb780817f42f29a5840ea34841da243b5d9"
POSITION_INDICES = (20, 41, *range(42, 417), 442)
POSITION_SOURCE_ARCHITECTURE = {
    "model": "fuse3_mamba_pretrain", "arr_length": 1600,
    "stride_size": 4, "seq_len": 20, "drop_path_rate": 0.1, "size_key": "signed_sizes",
}
CLASS_MAPPING = {"benign": 0, "attack": 1}
ARCHITECTURE = {
    "model": "fuse3_mamba_classifier", "arr_length": 1500, "stride_size": 4,
    "seq_len": 0, "num_classes": 2, "drop_path_rate": 0.1,
    "embed_dim": 256, "encoder_depth": 4, "cls_fusion": "add", "head_bias": False,
}
INPUT_CONTRACT = {
    "unit": "stored_packet_payload", "dtype": "uint8", "shape": ["B", 1500],
    "normalization": "float32(payload)/127.5-1",
    "numeric_sequence_lengths": {"size": 0, "iat": 0},
    "learned_input_independent_prefixes": 2,
    "retained_zero_bytes": True, "metadata_used": [],
}

# Exact exclusions from the registered pretraining file. No prefix filtering:
# any unlisted extra tensor, absent trunk tensor or shape drift is an error.
DECODER_EXCLUSIONS = (
    "byte_mask_token", "byte_decoder_pos_embed",
    "byte_decoder_embed.weight", "byte_decoder_embed.bias",
    "byte_decoder_blocks.0.mixer.A_log", "byte_decoder_blocks.0.mixer.D",
    "byte_decoder_blocks.0.mixer.in_proj.weight",
    "byte_decoder_blocks.0.mixer.conv1d.weight", "byte_decoder_blocks.0.mixer.conv1d.bias",
    "byte_decoder_blocks.0.mixer.x_proj.weight",
    "byte_decoder_blocks.0.mixer.dt_proj.weight", "byte_decoder_blocks.0.mixer.dt_proj.bias",
    "byte_decoder_blocks.0.mixer.out_proj.weight", "byte_decoder_blocks.0.norm.weight",
    "byte_decoder_blocks.1.mixer.A_log", "byte_decoder_blocks.1.mixer.D",
    "byte_decoder_blocks.1.mixer.in_proj.weight",
    "byte_decoder_blocks.1.mixer.conv1d.weight", "byte_decoder_blocks.1.mixer.conv1d.bias",
    "byte_decoder_blocks.1.mixer.x_proj.weight",
    "byte_decoder_blocks.1.mixer.dt_proj.weight", "byte_decoder_blocks.1.mixer.dt_proj.bias",
    "byte_decoder_blocks.1.mixer.out_proj.weight", "byte_decoder_blocks.1.norm.weight",
    "decoder_norm_f.weight", "byte_decoder_pred.weight", "byte_decoder_pred.bias",
    "size_decoder_pred.weight", "size_decoder_pred.bias",
    "iat_decoder_pred.weight", "iat_decoder_pred.bias",
)
STATE_SHAPES = {
    "byte_cls_token": (1, 1, 256), "size_cls_token": (1, 1, 256),
    "iat_cls_token": (1, 1, 256), "byte_indicator": (1, 1, 256),
    "size_indicator": (1, 1, 256), "iat_indicator": (1, 1, 256),
    "pos_embed": (1, 378, 256), "byte_embed.proj.weight": (256, 1, 4),
    "byte_embed.proj.bias": (256,), "norm_f.weight": (256,), "head.weight": (2, 256),
}
for _block in range(4):
    for _name, _shape in {
        "mixer.A_log": (512, 16), "mixer.D": (512,),
        "mixer.in_proj.weight": (1024, 256), "mixer.conv1d.weight": (512, 1, 4),
        "mixer.conv1d.bias": (512,), "mixer.x_proj.weight": (48, 512),
        "mixer.dt_proj.weight": (512, 16), "mixer.dt_proj.bias": (512,),
        "mixer.out_proj.weight": (256, 512), "norm.weight": (256,),
    }.items():
        STATE_SHAPES[f"encoder_blocks.{_block}.{_name}"] = _shape
del _block, _name, _shape
PRETRAIN_STATE_SHAPES = {name: shape for name, shape in STATE_SHAPES.items() if name != "head.weight"}
PRETRAIN_STATE_SHAPES.update({
    "pos_embed": (1, 443, 256),
    "byte_mask_token": (1, 1, 128), "byte_decoder_pos_embed": (1, 401, 128),
    "byte_decoder_embed.weight": (128, 256), "byte_decoder_embed.bias": (128,),
    "decoder_norm_f.weight": (128,),
    "byte_decoder_pred.weight": (4, 128), "byte_decoder_pred.bias": (4,),
    "size_decoder_pred.weight": (3003, 256), "size_decoder_pred.bias": (3003,),
    "iat_decoder_pred.weight": (1, 256), "iat_decoder_pred.bias": (1,),
})
for _block in range(2):
    for _name, _shape in {
        "mixer.A_log": (256, 16), "mixer.D": (256,),
        "mixer.in_proj.weight": (512, 128), "mixer.conv1d.weight": (256, 1, 4),
        "mixer.conv1d.bias": (256,), "mixer.x_proj.weight": (40, 256),
        "mixer.dt_proj.weight": (256, 8), "mixer.dt_proj.bias": (256,),
        "mixer.out_proj.weight": (128, 256), "norm.weight": (128,),
    }.items():
        PRETRAIN_STATE_SHAPES[f"byte_decoder_blocks.{_block}.{_name}"] = _shape
del _block, _name, _shape


def _json_copy(value, location="metadata"):
    """Reject executable/ambiguous metadata types before serialization."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is list:
        return [_json_copy(child, f"{location}[{index}]") for index, child in enumerate(value)]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: _json_copy(child, f"{location}.{key}") for key, child in value.items()}
    raise ValueError(f"{location} must contain only finite, basic JSON values")


def _same_json(actual, expected):
    # Ordinary equality treats False as 0; input/class contracts must not.
    return json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(
        expected, sort_keys=True, allow_nan=False)


def _digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _initialization_metadata(pretrained):
    return {
        "kind": "registered_pretrain" if pretrained else "scratch",
        "sha256": PRETRAIN_SHA256 if pretrained else None,
        "position_indices": list(POSITION_INDICES),
        "position_table": {
            "parameterization": "learned", "trainable": True,
            "source_shape": [1, 443, 256], "target_shape": [1, 378, 256],
            "origin": "registered_pretrain" if pretrained else "fresh_native_pretrain_initialization",
            "source_architecture": dict(POSITION_SOURCE_ARCHITECTURE),
        },
        "copied_state_names": sorted(set(STATE_SHAPES) - {"head.weight"}) if pretrained else [],
        "excluded_state_names": sorted(DECODER_EXCLUSIONS) if pretrained else [],
        "new_state_names": ["head.weight"] if pretrained else sorted(STATE_SHAPES),
    }


def _validate_provenance(provenance):
    if type(provenance) is not dict or set(provenance) != {
        "upstream", "initialization", "seed", "parameter_count", "runtime"
    }:
        raise ValueError("Invalid packet provenance fields")
    source = provenance["upstream"]
    if (type(source) is not dict or set(source) != {
            "commit", "model_files_sha256", "tracked_files_verified"}
            or source["commit"] != SOURCE_COMMIT
            or not _same_json(source["model_files_sha256"], SOURCE_SHA256)
            or type(source["tracked_files_verified"]) is not int
            or source["tracked_files_verified"] <= 0):
        raise ValueError("Packet provenance does not match the pinned upstream source")
    if type(provenance["seed"]) is not int or not 0 <= provenance["seed"] < 2**63:
        raise ValueError("Packet provenance seed must be an integer in [0, 2**63)")
    if type(provenance["parameter_count"]) is not int or provenance["parameter_count"] != 1852416:
        raise ValueError("Packet provenance parameter count is incompatible")
    runtime = provenance["runtime"]
    if (type(runtime) is not dict or set(runtime) != {"torch", "cuda"}
            or type(runtime["torch"]) is not str or not runtime["torch"]
            or (runtime["cuda"] is not None and type(runtime["cuda"]) is not str)):
        raise ValueError("Packet provenance runtime must name Torch and CUDA versions")
    initialization = provenance["initialization"]
    if type(initialization) is not dict or not any(
            _same_json(initialization, _initialization_metadata(pretrained))
            for pretrained in (False, True)):
        raise ValueError("Packet initialization has an unregistered hash, position map or state mapping")


def _validate_metadata(value):
    metadata = _json_copy(value)
    if type(metadata) is not dict or set(metadata) != {
            "format", "schema_version", "architecture", "input_contract",
            "class_mapping", "provenance", "study_metadata"}:
        raise ValueError("Require packet checkpoint metadata, not an original flow checkpoint")
    if (metadata["format"] != "netmambaplus-packet-v1"
            or type(metadata["schema_version"]) is not int or metadata["schema_version"] != 1):
        raise ValueError("Unsupported packet checkpoint format or schema version")
    for name, expected in (("architecture", ARCHITECTURE), ("input_contract", INPUT_CONTRACT),
                           ("class_mapping", CLASS_MAPPING)):
        if not _same_json(metadata[name], expected):
            raise ValueError(f"Incompatible packet {name}")
    _validate_provenance(metadata["provenance"])
    study = metadata["study_metadata"]
    if (type(study) is not dict or not _digest(study.get("data_manifest_sha256"))
            or not _digest(study.get("protocol_sha256"))):
        raise ValueError("study_metadata requires data_manifest_sha256 and protocol_sha256")
    sources = study.get("source_sha256")
    if (type(sources) is not dict or set(sources) != {"cic", "unsw"}
            or not all(_digest(value) for value in sources.values())):
        raise ValueError("study_metadata source_sha256 must identify both cic and unsw files")
    return metadata


def _verify_source(upstream):
    # Existing verification checks every tracked Git blob and rejects added
    # importable files, even when Git's status ignores an on-disk change.
    verified = repro.verify_upstream(upstream, {
        "upstream": {"commit": SOURCE_COMMIT, "sha256": SOURCE_SHA256}})
    return {"commit": verified["commit"], "model_files_sha256": verified["core_sha256"],
            "tracked_files_verified": verified["tracked_files_verified"]}


def _native_module(upstream):
    directory = Path(upstream).resolve() / "src/models"
    names = ("common", "models_mamba", "models_net_mamba_fuse3")
    for name in names:
        loaded = sys.modules.get(name)
        if loaded is not None and Path(getattr(loaded, "__file__", "")).resolve() != directory / f"{name}.py":
            raise ValueError(f"Native module {name} is already imported from incompatible source")
    previous_path = list(sys.path)
    previous_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(directory))
        module = importlib.import_module("models_net_mamba_fuse3")
    finally:
        sys.path[:] = previous_path
        sys.dont_write_bytecode = previous_bytecode
    for name in names:
        if Path(sys.modules[name].__file__).resolve() != directory / f"{name}.py":
            raise ValueError(f"Native module {name} was imported from incompatible source")
    return module


def _check_state(state, torch, *, pretrain=False):
    if not isinstance(state, Mapping) or any(type(name) is not str for name in state):
        raise ValueError("Packet model state must be a tensor dictionary")
    shapes = PRETRAIN_STATE_SHAPES if pretrain else STATE_SHAPES
    expected = set(shapes)
    if set(state) != expected:
        raise ValueError(f"Model state mismatch: missing={sorted(expected - set(state))}; "
                         f"unexpected={sorted(set(state) - expected)}")
    for name, value in state.items():
        if not isinstance(value, torch.Tensor) or value.dtype != torch.float32:
            raise ValueError(f"Model state {name} must be a float32 tensor")
        if tuple(value.shape) != shapes[name]:
            raise ValueError(f"Model state shape mismatch for {name}: {tuple(value.shape)} != {shapes[name]}")
        if value.layout != torch.strided or not bool(torch.isfinite(value).all()):
            raise ValueError(f"Model state {name} must be dense and finite")


def _check_model_contract(model):
    if not hasattr(model, "_packet_provenance"):
        raise ValueError("Require a model built or loaded by the packet adapter")
    expected = {"num_classes": 2, "stride_size": 4, "num_byte_patches": 375,
                "num_size_patches": 0, "num_iat_patches": 0, "embed_dim": 256,
                "is_pretrain": False, "cls_fusion": "add"}
    if any(getattr(model, key, None) != value for key, value in expected.items()):
        raise ValueError("Model architecture no longer matches the packet contract")
    if len(model.encoder_blocks) != 4 or model.head.bias is not None:
        raise ValueError("Model encoder or binary head no longer matches the packet contract")
    if model.drop_path.drop_prob != 0.1:
        raise ValueError("Model drop path no longer matches the packet contract")
    if not model.pos_embed.requires_grad:
        raise ValueError("Packet positions must remain learned, trainable parameters")


def build_model(upstream, *, initialization=None, seed=0, device="cuda"):
    """Construct the unchanged native classifier and optionally transfer its trunk."""
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in [0, 2**63)")
    initialization = None if initialization is None else Path(initialization).resolve()
    if initialization is not None and repro.sha256_file(initialization) != PRETRAIN_SHA256:
        raise ValueError("Unregistered initialization SHA-256; require original fuse3 pretraining weights")
    source = _verify_source(upstream)
    native = _native_module(upstream)
    import torch
    torch.manual_seed(seed)
    model = native.fuse3_mamba_classifier(
        arr_length=1500, stride_size=4, seq_len=0, num_classes=2, drop_path_rate=0.1)
    state = model.state_dict()
    _check_state(state, torch)
    if initialization is None:
        # Match the source table's geometry and native initialization before
        # selecting positions. Seed only the CPU generator inside its saved
        # context; the fresh constructor must not change paired dropout RNG.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(seed)
            fresh = native.fuse3_mamba_pretrain(
                arr_length=1600, stride_size=4, seq_len=20, drop_path_rate=0.1,
                size_key="signed_sizes")
            state["pos_embed"] = fresh.pos_embed.detach()[:, list(POSITION_INDICES), :].clone()
        del fresh
    else:
        # The registered historical file may use Namespace; no arbitrary global
        # or unsafe pickle fallback is permitted, even for local checkpoints.
        with torch.serialization.safe_globals([argparse.Namespace]):
            checkpoint = torch.load(initialization, map_location="cpu", weights_only=True)
        if repro.sha256_file(initialization) != PRETRAIN_SHA256:
            raise ValueError("Initialization SHA-256 changed while loading")
        if not isinstance(checkpoint, Mapping) or "model" not in checkpoint:
            raise ValueError("Registered initialization must contain its model state")
        pretrained = checkpoint["model"]
        _check_state(pretrained, torch, pretrain=True)
        for name in state:
            if name != "head.weight":
                value = (pretrained[name][:, list(POSITION_INDICES), :]
                         if name == "pos_embed" else pretrained[name])
                state[name] = value.clone()
    model.load_state_dict(state, strict=True)
    provenance = {
        "upstream": source, "initialization": _initialization_metadata(initialization is not None),
        "seed": seed, "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "runtime": {"torch": str(torch.__version__), "cuda": torch.version.cuda},
    }
    _validate_provenance(provenance)
    model._packet_provenance = _json_copy(provenance)
    _check_model_contract(model)
    return model.to(device), _json_copy(provenance)


def forward_payload(model, payload_tensor):
    """Normalize only uint8 payloads, pass empty numeric streams to native forward."""
    import torch
    if not isinstance(payload_tensor, torch.Tensor) or payload_tensor.dtype != torch.uint8:
        raise TypeError("payload must be a uint8 tensor with shape (B, 1500)")
    if payload_tensor.ndim != 2 or payload_tensor.shape[1] != 1500 or payload_tensor.shape[0] == 0:
        raise ValueError("payload must have nonempty shape (B, 1500)")
    _check_model_contract(model)
    if payload_tensor.device != next(model.parameters()).device:
        raise ValueError("payload and model must be on the same device")
    batch = payload_tensor.shape[0]
    byte_stream = (payload_tensor.to(dtype=torch.float32) / 127.5 - 1).reshape(batch, 1, 1, 1500)
    empty_size = torch.empty((batch, 0), device=payload_tensor.device, dtype=torch.float32)
    empty_iat = torch.empty((batch, 0), device=payload_tensor.device, dtype=torch.float32)
    return model(byte_stream, empty_size, empty_iat)


def _file_metadata(path):
    return {"path": str(path.resolve()), "sha256": repro.sha256_file(path), "bytes": path.stat().st_size}


def save_checkpoint(path, model, provenance, study_metadata):
    """Atomically create a safe packet checkpoint; never overwrite any existing path."""
    path = Path(path).absolute()
    if os.path.lexists(path):
        raise FileExistsError(f"Refusing to overwrite existing packet checkpoint: {path}")
    metadata = _validate_metadata({
        "format": "netmambaplus-packet-v1", "schema_version": 1,
        "architecture": ARCHITECTURE, "input_contract": INPUT_CONTRACT,
        "class_mapping": CLASS_MAPPING, "provenance": provenance, "study_metadata": study_metadata,
    })
    _check_model_contract(model)
    if not _same_json(metadata["provenance"], model._packet_provenance):
        raise ValueError("Supplied provenance does not match this model's initialization")
    import torch
    state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
    _check_state(state, torch)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            torch.save({"metadata": metadata, "model": state}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        # link is exclusive, including races and dangling destination symlinks.
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {**metadata, "checkpoint": _file_metadata(path)}


def load_checkpoint(path, upstream, *, device="cuda"):
    """Require the exact packet contract, then strictly restore tensors in eval mode."""
    path = Path(path).resolve()
    binding = _file_metadata(path)
    import torch
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if repro.sha256_file(path) != binding["sha256"]:
        raise ValueError("Packet checkpoint changed while loading")
    if type(checkpoint) is not dict or set(checkpoint) != {"metadata", "model"}:
        raise ValueError("Require a packet checkpoint, not original flow weights")
    metadata = _validate_metadata(checkpoint["metadata"])
    _check_state(checkpoint["model"], torch)
    model, current = build_model(upstream, seed=metadata["provenance"]["seed"], device="cpu")
    if not _same_json(current["upstream"], metadata["provenance"]["upstream"]):
        raise ValueError("Packet checkpoint upstream provenance does not match verified source")
    model.load_state_dict(checkpoint["model"], strict=True)
    model._packet_provenance = _json_copy(metadata["provenance"])
    model.to(device).eval()
    return model, {**metadata, "checkpoint": binding}

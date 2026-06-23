from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTAINERS_DIR = ROOT / "containers"

REQUIRED_TOP_LEVEL = {
    "model_id",
    "image_model",
    "name",
    "version",
    "owner",
    "source",
    "task_type",
    "accelerator",
    "host_runtime",
    "image",
    "input_types",
    "output_format",
    "api_endpoints",
    "hardware_minimum",
    "weights",
    "labels",
}

REQUIRED_LABELS = {
    "aihub.package.kind",
    "aihub.model.id",
    "aihub.model.name",
    "aihub.model.version",
    "aihub.model.owner",
    "aihub.accelerator",
    "aihub.hardware.minimum",
    "aihub.host.runtime",
    "aihub.input.types",
    "aihub.task.type",
    "aihub.entry.gateway",
    "aihub.entry.api",
    "aihub.entry.cli",
    "aihub.license.required",
    "aihub.license.env",
}

TASK_ENDPOINTS = {
    "vlm": "/v1/chat/completions",
    "chat": "/v1/chat/completions",
    "segment": "/v1/segment",
}


def _fail(message: str) -> None:
    raise AssertionError(message)


def _load_spec(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(f"{path}: invalid JSON: {exc}")


def _validate_spec(path: Path, seen_model_ids: set[str], seen_images: set[str]) -> None:
    spec = _load_spec(path)
    missing = REQUIRED_TOP_LEVEL - set(spec)
    if missing:
        _fail(f"{path}: missing top-level fields: {sorted(missing)}")

    model_id = spec["model_id"]
    image = spec["image"]
    task_type = spec["task_type"]
    labels = spec["labels"]

    if model_id in seen_model_ids:
        _fail(f"{path}: duplicated model_id {model_id!r}")
    seen_model_ids.add(model_id)

    if image in seen_images:
        _fail(f"{path}: duplicated image {image!r}")
    seen_images.add(image)

    if not isinstance(spec["input_types"], list) or not spec["input_types"]:
        _fail(f"{path}: input_types must be a non-empty list")

    if not isinstance(spec["api_endpoints"], list) or "/healthz" not in spec["api_endpoints"] or "/v1/models" not in spec["api_endpoints"]:
        _fail(f"{path}: api_endpoints must include /healthz and /v1/models")

    expected_endpoint = TASK_ENDPOINTS.get(task_type)
    if expected_endpoint is None:
        _fail(f"{path}: unsupported task_type {task_type!r}")
    if expected_endpoint not in spec["api_endpoints"]:
        _fail(f"{path}: task_type {task_type!r} requires {expected_endpoint}")

    missing_labels = REQUIRED_LABELS - set(labels)
    if missing_labels:
        _fail(f"{path}: missing labels: {sorted(missing_labels)}")

    expected_label_values = {
        "aihub.package.kind": "single-model-accelerator",
        "aihub.model.id": model_id,
        "aihub.model.name": spec["name"],
        "aihub.model.version": spec["version"],
        "aihub.model.owner": spec["owner"],
        "aihub.accelerator": spec["accelerator"],
        "aihub.hardware.minimum": spec["hardware_minimum"],
        "aihub.host.runtime": spec["host_runtime"],
        "aihub.input.types": ",".join(spec["input_types"]),
        "aihub.task.type": task_type,
        "aihub.license.required": "true",
        "aihub.license.env": "AIHUB_LICENSE_KEY",
    }
    for label, expected in expected_label_values.items():
        actual = labels.get(label)
        if actual != expected:
            _fail(f"{path}: label {label} expected {expected!r}, got {actual!r}")

    if task_type == "segment":
        if labels.get("aihub.output.format") != spec["output_format"]:
            _fail(f"{path}: segment labels must include matching aihub.output.format")
        if labels.get("aihub.entry.segment") is None:
            _fail(f"{path}: segment labels must include aihub.entry.segment")
        if spec["accelerator"] == "rocm-igpu":
            _fail(f"{path}: SAM/segmentation DirectML specs must not use rocm-igpu")


def main() -> int:
    specs = sorted(CONTAINERS_DIR.glob("*/model.json"))
    if not specs:
        print("No model specs found under containers/*/model.json", file=sys.stderr)
        return 1

    seen_model_ids: set[str] = set()
    seen_images: set[str] = set()
    for spec in specs:
        _validate_spec(spec, seen_model_ids, seen_images)
        print(f"validated {spec.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
import importlib
from ryzenai.registry import _REGISTRY, _VISION_REGISTRY


_ALL_REGISTRY_ENTRIES = [*_REGISTRY.values(), *_VISION_REGISTRY.values()]


def __getattr__(name: str):
    for module_path, class_name, *_ in _ALL_REGISTRY_ENTRIES:
        if class_name == name:
            return getattr(importlib.import_module(module_path), name)
    raise AttributeError(f"module 'ryzenai.modules' has no attribute {name!r}")


__all__ = [entry[1] for entry in _ALL_REGISTRY_ENTRIES]

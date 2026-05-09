import importlib
from ryzenai.registry import _REGISTRY


def __getattr__(name: str):
    for module_path, class_name, *_ in _REGISTRY.values():
        if class_name == name:
            return getattr(importlib.import_module(module_path), name)
    raise AttributeError(f"module 'ryzenai.modules' has no attribute {name!r}")


__all__ = [entry[1] for entry in _REGISTRY.values()]

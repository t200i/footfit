import sys
from types import SimpleNamespace

from ryzenai.backend.directml import PyTorchDirectMLBackend


def test_directml_backend_accepts_explicit_cpu_fallback():
    backend = PyTorchDirectMLBackend(device="cpu", allow_cpu=True)
    assert backend.device == "cpu"


def test_directml_backend_detects_dml(monkeypatch):
    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(
            is_available=lambda: False,
            get_device_name=lambda index: "fake-gpu",
        )
    )
    fake_torch_directml = SimpleNamespace(device=lambda: "privateuseone:0")
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "torch_directml", fake_torch_directml)

    backend = PyTorchDirectMLBackend(device="auto")

    assert backend.device == "dml"
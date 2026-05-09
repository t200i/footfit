"""
Crash scenario: Backend.validate() doesn't raise on missing hardware.
If validate() silently succeeds when EP/GPU is unavailable, downstream
model loading will crash with cryptic errors instead of a clear RuntimeError.
"""
import pytest
from unittest.mock import patch, MagicMock
from ryzenai.backend.base import Backend


class TestBackendValidationContract:
    def test_backend_is_abstract(self):
        """Backend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Backend()

    def test_onnx_vitisai_raises_without_ep(self):
        """ONNXVitisAIBackend must raise RuntimeError when EP is missing."""
        with patch.dict("sys.modules", {"onnxruntime": MagicMock()}):
            import importlib
            import ryzenai.backend.onnx as onnx_mod
            importlib.reload(onnx_mod)
            onnx_mod.ort.get_available_providers = MagicMock(
                return_value=["CPUExecutionProvider"]
            )
            with pytest.raises(RuntimeError, match="VitisAI EP not found"):
                onnx_mod.ONNXVitisAIBackend()

    def test_onnx_directml_raises_without_ep(self):
        """ONNXDirectMLBackend must raise RuntimeError when EP is missing."""
        with patch.dict("sys.modules", {"onnxruntime": MagicMock()}):
            import importlib
            import ryzenai.backend.onnx as onnx_mod
            importlib.reload(onnx_mod)
            onnx_mod.ort.get_available_providers = MagicMock(
                return_value=["CPUExecutionProvider"]
            )
            with pytest.raises(RuntimeError, match="DirectML EP not found"):
                onnx_mod.ONNXDirectMLBackend()

    def test_pytorch_raises_without_cuda(self):
        """PyTorchROCmBackend must raise RuntimeError when CUDA unavailable."""
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            import importlib
            import ryzenai.backend.pytorch as pt_mod
            importlib.reload(pt_mod)
            pt_mod.torch.cuda.is_available = MagicMock(return_value=False)
            with pytest.raises(RuntimeError, match="no CUDA/ROCm GPU available"):
                pt_mod.PyTorchROCmBackend()

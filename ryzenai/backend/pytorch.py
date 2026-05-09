from ryzenai.backend.base import Backend, logger


class PyTorchROCmBackend(Backend):
    """iGPU — PyTorch + ROCm（conda: rocm-pytorch）"""

    name = "PyTorchROCm"

    def __init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError(
                "PyTorch: no CUDA/ROCm GPU available (torch.cuda.is_available() = False)"
            )
        logger.info("Backend: PyTorch — ROCm GPU (%s)", torch.cuda.get_device_name(0))

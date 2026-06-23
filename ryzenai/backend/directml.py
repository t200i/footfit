from ryzenai.backend.base import Backend, logger


class PyTorchDirectMLBackend(Backend):
    """iGPU — PyTorch + DirectML for Ultralytics/SAM workloads."""

    name = "PyTorchDirectML"

    def __init__(self, device: str = "auto", allow_cpu: bool = False) -> None:
        self.requested_device = device
        self.allow_cpu = allow_cpu
        self.device = "cpu"
        self.torch_device_type = "cpu"
        self.validate()

    def validate(self) -> None:
        requested = self.requested_device.strip().lower()
        if requested not in {"auto", "cuda", "dml", "directml", "privateuseone", "cpu"}:
            raise RuntimeError(
                f"Unsupported DirectML backend device: {self.requested_device!r}. "
                "Expected one of: auto, cuda, dml, directml, privateuseone, cpu."
            )

        if requested in {"auto", "cuda"}:
            try:
                import torch

                if torch.cuda.is_available():
                    self.device = "cuda"
                    self.torch_device_type = "cuda"
                    logger.info("Backend: PyTorch — CUDA/ROCm GPU (%s)", torch.cuda.get_device_name(0))
                    return
            except Exception as exc:
                if requested == "cuda":
                    raise RuntimeError(f"PyTorch CUDA/ROCm GPU validation failed: {exc}") from exc

            if requested == "cuda":
                raise RuntimeError("PyTorch: no CUDA/ROCm GPU available")

        if requested in {"auto", "dml", "directml", "privateuseone"}:
            try:
                import torch_directml

                device = torch_directml.device()
                self.device = "dml"
                self.torch_device_type = getattr(device, "type", "privateuseone")
                logger.info("Backend: PyTorch — DirectML GPU (iGPU, %s)", self.torch_device_type)
                return
            except Exception as exc:
                if requested in {"dml", "directml", "privateuseone"}:
                    raise RuntimeError(f"PyTorch DirectML GPU validation failed: {exc}") from exc

        if requested == "cpu" or self.allow_cpu:
            self.device = "cpu"
            self.torch_device_type = "cpu"
            logger.info("Backend: PyTorch — CPU fallback")
            return

        raise RuntimeError("PyTorch DirectML backend unavailable: no CUDA/ROCm or DirectML GPU detected")
from ryzenai.backend.base import Backend, logger


class PyTorchDirectMLBackend(Backend):
    """iGPU — PyTorch + DirectML for Ultralytics/SAM workloads."""

    name = "PyTorchDirectML"

    def __init__(self, device: str = "auto", allow_cpu: bool = False) -> None:
        self.requested_device = device
        self.allow_cpu = allow_cpu
        self.device = "cpu"
        self.validate()

    def validate(self) -> None:
        requested = self.requested_device.strip().lower()
        if requested not in {"auto", "cuda", "dml", "cpu"}:
            raise RuntimeError(
                f"Unsupported DirectML backend device: {self.requested_device!r}. "
                "Expected one of: auto, cuda, dml, cpu."
            )

        if requested in {"auto", "cuda"}:
            try:
                import torch

                if torch.cuda.is_available():
                    self.device = "cuda"
                    logger.info("Backend: PyTorch — CUDA/ROCm GPU (%s)", torch.cuda.get_device_name(0))
                    return
            except Exception as exc:
                if requested == "cuda":
                    raise RuntimeError(f"PyTorch CUDA/ROCm GPU validation failed: {exc}") from exc

            if requested == "cuda":
                raise RuntimeError("PyTorch: no CUDA/ROCm GPU available")

        if requested in {"auto", "dml"}:
            try:
                import torch_directml

                torch_directml.device()
                self.device = "dml"
                logger.info("Backend: PyTorch — DirectML GPU (iGPU)")
                return
            except Exception as exc:
                if requested == "dml":
                    raise RuntimeError(f"PyTorch DirectML GPU validation failed: {exc}") from exc

        if requested == "cpu" or self.allow_cpu:
            self.device = "cpu"
            logger.info("Backend: PyTorch — CPU fallback")
            return

        raise RuntimeError("PyTorch DirectML backend unavailable: no CUDA/ROCm or DirectML GPU detected")
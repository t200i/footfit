from pathlib import Path
import sys
from typing import Any

from ryzenai.backend.directml import PyTorchDirectMLBackend
from ryzenai.model import SegmentationModel


_DEFAULT_TEXT_PROMPT = "a single pill"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ROOT_ULTRALYTICS_PACKAGE = _PROJECT_ROOT / "ultralytics"


def use_root_ultralytics() -> Path:
    if not _ROOT_ULTRALYTICS_PACKAGE.exists():
        raise FileNotFoundError(
            f"Root Ultralytics fork not found: {_ROOT_ULTRALYTICS_PACKAGE}"
        )

    loaded = sys.modules.get("ultralytics")
    if loaded is not None:
        loaded_file = Path(getattr(loaded, "__file__", "")).resolve()
        if _ROOT_ULTRALYTICS_PACKAGE.resolve() not in loaded_file.parents:
            raise RuntimeError(
                "SAM3 requires the root Ultralytics fork under "
                f"{_ROOT_ULTRALYTICS_PACKAGE}, but another ultralytics package "
                f"is already loaded from {loaded_file}."
            )

    project_root = str(_PROJECT_ROOT)
    if sys.path[:1] != [project_root]:
        sys.path = [path for path in sys.path if path != project_root]
        sys.path.insert(0, project_root)
    return _ROOT_ULTRALYTICS_PACKAGE


class SAM3SegmentatorModel(SegmentationModel):
    """Ultralytics SAM3 text-prompted segmentation model."""

    def __init__(
        self,
        model_path: str,
        text_prompt: str = _DEFAULT_TEXT_PROMPT,
        device: str = "auto",
        allow_cpu: bool = False,
        predictor_cls: type | None = None,
    ) -> None:
        backend = PyTorchDirectMLBackend(device=device, allow_cpu=allow_cpu)
        super().__init__(backend)
        self.model_path = Path(model_path)
        self.text_prompt = text_prompt
        self._predictor_cls = predictor_cls
        self._predictor = None

    @property
    def device(self) -> str:
        return getattr(self.backend, "device", "cpu")

    @property
    def torch_device_type(self) -> str:
        return getattr(self.backend, "torch_device_type", "cpu")

    @property
    def ultralytics_version(self) -> str:
        try:
            use_root_ultralytics()
            import ultralytics

            return getattr(ultralytics, "__version__", "unknown")
        except Exception:
            return "unknown"

    def _load_predictor_class(self) -> type:
        if self._predictor_cls is not None:
            return self._predictor_cls

        use_root_ultralytics()
        from ultralytics.models.sam import SAM3SemanticPredictor

        return SAM3SemanticPredictor

    def _load_predictor(self, conf: float, iou: float, half: bool) -> Any:
        if not self.model_path.exists():
            raise FileNotFoundError(f"SAM3 model file not found: {self.model_path}")

        predictor_cls = self._load_predictor_class()
        overrides = {
            "task": "segment",
            "mode": "predict",
            "model": str(self.model_path),
            "conf": conf,
            "iou": iou,
            "half": half,
            "save": False,
            "verbose": False,
        }
        if self.device:
            overrides["device"] = self.device
        return predictor_cls(overrides=overrides)

    def _ensure_predictor(self, conf: float, iou: float, half: bool) -> Any:
        args = getattr(self._predictor, "args", None)
        cur_conf = getattr(args, "conf", None)
        cur_iou = getattr(args, "iou", None)
        cur_half = getattr(args, "half", None)
        if self._predictor is None or cur_conf != conf or cur_iou != iou or cur_half != half:
            self._predictor = self._load_predictor(conf=conf, iou=iou, half=half)
        return self._predictor

    def warmup(self, image_size: int = 512, text: str | list[str] | None = None) -> None:
        import numpy as np

        dummy = np.zeros((image_size, image_size, 3), dtype=np.uint8)
        self.predict(dummy, text=text)

    def predict(
        self,
        image: Any,
        text: str | list[str] | None = None,
        conf: float = 0.25,
        iou: float = 0.7,
        half: bool = True,
        **predict_kwargs: Any,
    ) -> list[Any]:
        predictor = self._ensure_predictor(conf=conf, iou=iou, half=half)
        prompts = self._normalize_text(text)
        return predictor(source=image, text=prompts, **predict_kwargs)

    def _normalize_text(self, text: str | list[str] | None) -> list[str]:
        if text is None:
            return [self.text_prompt]
        if isinstance(text, str):
            return [text]
        return text


def summarize_results(results: list[Any], normalize: bool = False, decimals: int = 5) -> list[dict]:
    summaries: list[dict] = []
    for result in results:
        summaries.extend(result.summary(normalize=normalize, decimals=decimals))
    return summaries
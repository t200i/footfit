import sys
from types import SimpleNamespace

from ryzenai.modules.sam3_segmentator import (
    SAM3SegmentatorModel,
    summarize_results,
    use_root_ultralytics,
)


class FakeResult:
    def summary(self, normalize=False, decimals=5):
        return [
            {
                "name": "pill",
                "class": 0,
                "confidence": round(0.87654, decimals),
                "normalized": normalize,
            }
        ]


class FakePredictor:
    def __init__(self, overrides):
        self.overrides = overrides
        self.args = SimpleNamespace(
            conf=overrides["conf"],
            iou=overrides["iou"],
            half=overrides["half"],
        )

    def __call__(self, source, text):
        self.source = source
        self.text = text
        return [FakeResult()]


def test_sam3_segmentator_returns_results_compatible_objects(tmp_path):
    weights = tmp_path / "sam3.pt"
    weights.write_bytes(b"fake")
    model = SAM3SegmentatorModel(
        str(weights),
        device="cpu",
        allow_cpu=True,
        predictor_cls=FakePredictor,
    )

    results = model.predict(object(), text="a round pill", conf=0.3, iou=0.6)

    assert isinstance(results[0], FakeResult)
    assert summarize_results(results, normalize=True)[0]["normalized"] is True
    assert model._predictor.text == ["a round pill"]
    assert model._predictor.overrides["device"] == "cpu"


def test_root_ultralytics_path_takes_priority():
    package_path = use_root_ultralytics()

    assert package_path.name == "ultralytics"
    assert str(package_path.parent) == sys.path[0]
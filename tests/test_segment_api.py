import base64

import pytest
from fastapi.testclient import TestClient

from api import build
from ryzenai.model import SegmentationModel
from tests.conftest import MockBackend


cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")


class FakeResult:
    def summary(self, normalize=False, decimals=5):
        return [{"name": "pill", "class": 0, "confidence": 0.9}]


class FakeSegmentationModel(SegmentationModel):
    device = "dml"

    def __init__(self):
        super().__init__(MockBackend())

    def predict(self, image, *args, **kwargs):
        assert image.shape[:2] == (8, 8)
        assert kwargs["text"] == ["pill"]
        return [FakeResult()]


def test_segment_endpoint_returns_results_summary():
    app = build(None, None, vision_model=FakeSegmentationModel(), vision_model_name="sam3-test")
    client = TestClient(app)
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", image)
    assert ok

    resp = client.post(
        "/v1/segment",
        files={"file": ("pill.png", encoded.tobytes(), "image/png")},
        data={"text": "pill"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "segment.result"
    assert data["model"] == "sam3-test"
    assert data["device"] == "dml"
    assert data["image"] == {"width": 8, "height": 8}
    assert data["count"] == 1
    assert data["detections"][0]["name"] == "pill"


def test_predict_endpoint_projects_ultralytics_results_for_client():
    class FakeTensor:
        def __init__(self, data):
            self._data = data

        def detach(self):
            return self

        def cpu(self):
            return self

        def tolist(self):
            return self._data

    class FakeBoxes:
        def __init__(self, data):
            self.data = FakeTensor(data)

    class FakeUltralyticsResult:
        orig_shape = (8, 8)
        names = {0: "object"}
        path = "cat.jpg"
        boxes = FakeBoxes([[1.0, 2.0, 3.0, 4.0, 0.9, 0.0]])
        masks = None

    class BatchSegmentationModel(SegmentationModel):
        device = "dml"

        def __init__(self):
            super().__init__(MockBackend())

        def predict(self, image, *args, **kwargs):
            assert isinstance(image, list)
            assert kwargs.get("text") == "a cat"
            return [FakeUltralyticsResult()]

    app = build(None, None, vision_model=BatchSegmentationModel(), vision_model_name="sam3-igpu")
    client = TestClient(app)
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    payload = {
        "images": [
            {
                "shape": [8, 8, 3],
                "dtype": "uint8",
                "data": base64.b64encode(image.tobytes()).decode("utf-8"),
            }
        ],
        "kwargs": {"text": "a cat", "conf": 0.25, "iou": 0.7},
    }

    resp = client.post("/v1/models/sam3-igpu/predict", json=payload)

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["orig_shape"] == [8, 8]
    assert results[0]["names"] == {"0": "object"}
    assert results[0]["boxes"] == [[1.0, 2.0, 3.0, 4.0, 0.9, 0.0]]
    assert results[0]["path"] == "cat.jpg"


def test_healthz_reports_vision_model_ultralytics_version():
    class VersionedModel(FakeSegmentationModel):
        ultralytics_version = "8.4.37"

    app = build(None, None, vision_model=VersionedModel(), vision_model_name="sam3-test")
    client = TestClient(app)

    resp = client.get("/healthz")

    assert resp.status_code == 200
    entry = resp.json()["models"][0]
    assert entry["id"] == "sam3-test"
    assert entry["ultralytics_version"] == "8.4.37"
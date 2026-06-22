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
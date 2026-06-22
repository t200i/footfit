import pytest

from ryzenai.registry import available_vision_models, build_vision_model


def test_available_vision_models_includes_sam3():
    assert "sam3-igpu" in available_vision_models()


def test_build_vision_model_unknown_raises_valueerror():
    with pytest.raises(ValueError, match="Unknown vision model"):
        build_vision_model("missing-vision-model")
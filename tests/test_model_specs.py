from scripts.validate_model_specs import main


def test_model_specs_are_valid():
    assert main() == 0
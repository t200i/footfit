"""
Test suite for ryzenai framework.

Each test targets an independent critical crash scenario that could break
the system in production. Tests use mocks to avoid hardware dependencies
(no NPU/GPU/ONNX/PyTorch required in CI).

Test naming: test_<crash_scenario>
"""

# AI Hub Model Container Design

This project is moving toward one AI Hub Model Card image per model. The runtime code in `ryzenai/` remains reusable, while `containers/<model>/model.json` describes each publishable image.

## Image Families

| Model | Task | Accelerator | Runtime |
|---|---|---|---|
| `gemma3-4b-npu` | VLM | `ryzen-ai-npu` | Ryzen AI Software / Vitis AI EP |
| `gemma4-2b-gpu` | VLM | `rocm-igpu` | ROCm iGPU |
| `gemma4-4b-gpu` | VLM | `rocm-igpu` | ROCm iGPU |
| `sam3-igpu` | Segmentation | `directml-privateuseone-igpu` | torch-directml / privateuseone |

## SAM3 DirectML Base

SAM3 is not a ROCm image. Its container base follows the torch-directml stack:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LD_LIBRARY_PATH=/usr/lib/wsl/lib

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install torch==2.4.1 torchvision \
        --index-url https://download.pytorch.org/whl/cpu \
 && pip install torch-directml==0.2.4.dev240913
```

The root `ultralytics/` package is the authoritative custom SAM3 framework. The deprecated `sam3-ryzen-ai/` subproject must not be copied into new image definitions.

## Automation Boundary

AI Hub automation is implemented as GitHub Actions validation templates, not as a product runtime package. The first validation layer checks model specs, required `aihub.*` labels, task endpoints, and SAM3 DirectML Dockerfile constraints. Hardware and licensed container smoke tests should later run on self-hosted runners that have the corresponding accelerator runtime.
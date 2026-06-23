FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LD_LIBRARY_PATH=/usr/lib/wsl/lib \
    AIHUB_MODEL_ID=sam3-igpu \
    AIHUB_PORT=80 \
    MODEL_PATH=/app/weights/sam3.pt

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install torch==2.4.1 torchvision \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install torch-directml==0.2.4.dev240913

WORKDIR /app

COPY requirements-ultralytics.txt ./
RUN pip install -r requirements-ultralytics.txt

COPY api.py cli.py ./
COPY ryzenai/ ./ryzenai/
COPY ultralytics/ ./ultralytics/
COPY containers/sam3-directml-igpu/model.json ./model.json

VOLUME ["/app/weights"]
EXPOSE 80

LABEL aihub.package.kind="single-model-accelerator" \
      aihub.model.id="sam3-igpu" \
      aihub.model.name="SAM3 Segmentation" \
      aihub.model.version="0.1.0" \
      aihub.model.owner="team-amd-ryzenai" \
      aihub.accelerator="directml-privateuseone-igpu" \
      aihub.hardware.minimum="AMD Ryzen AI iGPU exposed to WSL with torch-directml privateuseone support" \
      aihub.host.runtime="torch-directml-wsl" \
      aihub.input.types="image,text" \
      aihub.task.type="segment" \
      aihub.output.format="ultralytics-results" \
      aihub.entry.gateway="http://127.0.0.1:8080" \
      aihub.entry.api="http://127.0.0.1:8080/v1" \
      aihub.entry.segment="http://127.0.0.1:8080/v1/segment" \
      aihub.entry.cli="aihub-cli --base-url http://127.0.0.1:8080 --task segment" \
      aihub.license.required="true" \
      aihub.license.env="AIHUB_LICENSE_KEY"

CMD ["python", "api.py", "--vision-model", "sam3-igpu", "--host", "0.0.0.0", "--port", "80"]
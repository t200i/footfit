---
license: apache-2.0
base_model:
- mistralai/Mistral-7B-Instruct-v0.3
tags:
- ryzenai-npu
---


# Mistral-7B-Instruct-v0.3-onnx-ryzenai-npu
- ## Introduction
  This model was created using Quark Quantization, followed by OGA Model Builder, and finalized with post-processing for NPU deployment.
- ## Quantization Strategy
  - AWQ / Group 128 / Asymmetric / BFP16 activations / UINT4 Weights
- ## Quick Start
  For quickstart, refer to [Ryzen AI documentation](https://ryzenai.docs.amd.com/en/latest/hybrid_oga.html)

## Evaluation scores
  - The perplexity measurement is run on the wikitext-2-raw-v1 (raw data) dataset provided by Hugging Face. Perplexity score measured for prompt length 2k is 5.64895.

  - The average MMLU scores are astronomy - 66.45, philosophy - 67.2 and management - 79.61.

#### License
Modifications copyright(c) 2024 Advanced Micro Devices,Inc. All rights reserved.

MIT License

Copyright (c) 2024 Advanced Micro Devices, Inc 

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
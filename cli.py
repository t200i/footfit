import argparse
import base64
import json
import logging
from typing import Generator

logging.basicConfig(format="[%(name)s] %(message)s")
logging.getLogger("ryzenai").setLevel(logging.INFO)

from ryzenai.model import Model
from ryzenai.registry import build_model, build_vision_model
from ryzenai.modules.sam3_segmentator import summarize_results
from ryzenai.session import SingleSession, InteractiveSession


# ── Helpers ──────────────────────────────────────────────────────────────────


def _print_stream(tokens: Generator[str, None, None]) -> None:
    """逐 token 即時輸出至 stdout，串流結束後換行。"""
    for token in tokens:
        print(token, end="", flush=True)
    print()


def _load_image(image_path: str) -> list:
    """將影像檔案編碼為 OpenAI multimodal content list。"""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = image_path.rsplit(".", 1)[-1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
        ext, "image/jpeg"
    )
    return [
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
    ]


# ── Session Delegates ────────────────────────────────────────────────────────


def run_single(model: Model, user_input: str | list, stream: bool = False) -> None:
    tokens = SingleSession(model).run(user_input)
    _print_stream(tokens) if stream else print("".join(tokens))


def run_interactive(model: Model, stream: bool = True) -> None:
    """互動 REPL：Ctrl+C 或 Ctrl+D 離開。互動模式預設啟用串流。"""
    session = InteractiveSession(model)
    print("Ryzen AI CLI  —  輸入訊息後按 Enter，Ctrl+C 離開\n")
    try:
        while True:
            user_input = input("> ").strip()
            if not user_input:
                continue
            tokens = session.send(user_input)
            _print_stream(tokens) if stream else print("".join(tokens))
    except (KeyboardInterrupt, EOFError):
        print("\n再見。")


def run_segment(
    model_id: str,
    image_path: str,
    text: str | None = None,
    conf: float = 0.25,
    iou: float = 0.7,
    normalize: bool = False,
    save_annotated: str | None = None,
) -> None:
    try:
        import cv2
    except Exception as exc:
        raise RuntimeError(f"Segmentation dependencies unavailable: {exc}") from exc

    image = cv2.imread(image_path)
    if image is None:
        raise RuntimeError(f"Invalid image: {image_path}")

    model = build_vision_model(model_id)
    results = model.predict(image, text=text, conf=conf, iou=iou)
    print(json.dumps(summarize_results(results, normalize=normalize), ensure_ascii=False))

    if save_annotated:
        if not results:
            raise RuntimeError("No results returned; annotated image was not saved")
        annotated = results[0].plot()
        cv2.imwrite(save_annotated, annotated)


# ── Composition Root ─────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Ryzen AI CLI — 本地 LLM/VLM 推論介面",
    )
    parser.add_argument("-m", "--model", required=True, help="模型識別名稱（見 registry）")
    parser.add_argument("--task", choices=["chat", "segment"], default="chat", help="推論任務類型")
    parser.add_argument(
        "-p", "--prompt", default=None, help="單次推論 prompt；省略則進入互動模式"
    )
    parser.add_argument("--image", default=None, help="影像檔案路徑（僅 VLM 模型支援）")
    parser.add_argument("--stream", action="store_true", help="啟用逐 token 串流輸出")
    parser.add_argument("--conf", type=float, default=0.25, help="segmentation confidence threshold")
    parser.add_argument("--iou", type=float, default=0.7, help="segmentation IoU threshold")
    parser.add_argument("--normalize", action="store_true", help="segmentation output 使用正規化座標")
    parser.add_argument("--save-annotated", default=None, help="儲存 segmentation 標註影像")
    args = parser.parse_args()

    if args.task == "segment":
        if args.image is None:
            parser.error("--task segment 需要 --image")
        run_segment(
            model_id=args.model,
            image_path=args.image,
            text=args.prompt,
            conf=args.conf,
            iou=args.iou,
            normalize=args.normalize,
            save_annotated=args.save_annotated,
        )
        raise SystemExit(0)

    model = build_model(args.model)

    if args.prompt is not None:
        content: str | list = args.prompt
        if args.image:
            content = _load_image(args.image) + [{"type": "text", "text": args.prompt}]
        run_single(model, content, stream=args.stream)
    else:
        if args.image:
            parser.error("--image 僅可與 --prompt 搭配使用（單次模式）")
        run_interactive(model, stream=True)

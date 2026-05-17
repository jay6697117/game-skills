#!/usr/bin/env python3
"""
Generate an image through the Responses-compatible gateway configured for Codex.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import ssl
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


DEFAULT_MODEL = "gpt-5.5"
DEFAULT_TIMEOUT = 600
DEFAULT_SIZE = "1024x1024"
DEFAULT_MAX_RETRIES = 5
DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_INSTRUCTIONS = (
    "You are an image generation assistant. Use the image_generation tool to create the requested image "
    "and return the generated result. If image generation is rate-limited, do not rewrite, shorten, "
    "or simplify the user's prompt. Retry the same request after the rate-limit delay."
)


class StreamRateLimitError(RuntimeError):
    def __init__(self, message: str, retry_after_seconds: float | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class StreamError(RuntimeError):
    pass


def load_config() -> tuple[str, str]:
    config_path = Path.home() / ".codex" / "config.toml"
    auth_path = Path.home() / ".codex" / "auth.json"

    if not config_path.exists():
        raise RuntimeError(f"Missing config file: {config_path}")
    if not auth_path.exists():
        raise RuntimeError(f"Missing auth file: {auth_path}")

    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    base_url = (
        config.get("model_providers", {})
        .get(config.get("model_provider", ""), {})
        .get("base_url")
    )

    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    api_key = auth.get("OPENAI_API_KEY")
    if api_key:
        if not base_url:
            raise RuntimeError("Could not find model provider base_url in ~/.codex/config.toml")
        return str(base_url).rstrip("/"), str(api_key)

    access_token = auth.get("tokens", {}).get("access_token")
    if access_token:
        return DEFAULT_CODEX_BASE_URL, str(access_token)

    raise RuntimeError("Could not find OPENAI_API_KEY or tokens.access_token in ~/.codex/auth.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an image via the configured Responses gateway.")
    parser.add_argument("--prompt", required=True, help="Image generation prompt.")
    parser.add_argument("--out", required=True, help="Output image path.")
    parser.add_argument("--size", default=DEFAULT_SIZE, help="Image size, e.g. 1024x1024 or 1024x1536.")
    parser.add_argument(
        "--action",
        choices=("auto", "generate", "edit"),
        default="auto",
        help="Image tool action. Use edit when providing a reference image or mask.",
    )
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Reference image path. Repeat the flag to include multiple images.",
    )
    parser.add_argument(
        "--image-url",
        action="append",
        default=[],
        help="Reference image URL. Repeat the flag to include multiple images.",
    )
    parser.add_argument(
        "--mask",
        help="Optional mask image path for edit workflows.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Responses model to call.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help="Maximum retries for image rate-limit errors. Retries keep the original prompt and inputs.",
    )
    return parser.parse_args()


def encode_image_data_url(image_path: str) -> str:
    path = Path(image_path).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"Image file does not exist: {path}")

    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "application/octet-stream"

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_payload(args: argparse.Namespace) -> bytes:
    input_content: list[dict[str, str]] = [
        {
            "type": "input_text",
            "text": args.prompt,
        }
    ]

    for image_path in args.image:
        input_content.append(
            {
                "type": "input_image",
                "image_url": encode_image_data_url(image_path),
            }
        )

    for image_url in args.image_url:
        input_content.append(
            {
                "type": "input_image",
                "image_url": image_url,
            }
        )

    if args.mask:
        input_content.append(
            {
                "type": "input_image_mask",
                "image_url": encode_image_data_url(args.mask),
            }
        )

    payload = {
        "model": args.model,
        "instructions": DEFAULT_INSTRUCTIONS,
        "input": [
            {
                "role": "user",
                "content": input_content,
            }
        ],
        "store": False,
        "stream": True,
        "tools": [
            {
                "type": "image_generation",
                "size": args.size,
                "action": args.action,
            }
        ],
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def extract_image_base64(data: dict) -> str:
    for item in data.get("output", []):
        if item.get("type") == "image_generation_call" and item.get("result"):
            return item["result"]
    raise RuntimeError("No image_generation_call result returned")


def parse_retry_after_seconds(message: str) -> float | None:
    match = re.search(r"try again in\s+(\d+(?:\.\d+)?)\s*(ms|s)", message, re.IGNORECASE)
    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "ms":
        return value / 1000
    return value


def get_stream_error(event: dict) -> dict | None:
    error = event.get("error")
    if isinstance(error, dict):
        return error
    if event.get("type") == "error":
        return {"message": json.dumps(event, ensure_ascii=False)}
    return None


def is_image_rate_limit_error(error: dict) -> bool:
    return error.get("code") == "rate_limit_exceeded" and error.get("type") in {
        "input-images",
        "image_generation",
        "rate_limit_error",
    }


def parse_http_error_body(message: str) -> dict | None:
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return None

    error = data.get("error")
    if isinstance(error, dict):
        return error
    return None


def collect_sse_output_items(response) -> list[dict]:
    output_items: list[dict] = []

    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data: "):
            continue

        payload = line[6:]
        if payload == "[DONE]":
            break

        event = json.loads(payload)
        error = get_stream_error(event)
        if error:
            message = str(error.get("message") or json.dumps(error, ensure_ascii=False))
            if is_image_rate_limit_error(error):
                raise StreamRateLimitError(message, parse_retry_after_seconds(message))
            raise StreamError(message)

        if event.get("type") == "response.output_item.done" and isinstance(event.get("item"), dict):
            output_items.append(event["item"])

    return output_items


def extract_image_base64_from_items(items: list[dict]) -> str:
    for item in items:
        if item.get("type") == "image_generation_call" and item.get("result"):
            return item["result"]
    raise RuntimeError("No image_generation_call result returned")


def request_image(base_url: str, api_key: str, body: bytes, timeout: int) -> list[dict]:
    request = Request(
        f"{base_url}/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    try:
        with urlopen(request, context=ssl.create_default_context(), timeout=timeout) as response:
            return collect_sse_output_items(response)
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        error = parse_http_error_body(message)
        if error and is_image_rate_limit_error(error):
            retry_message = str(error.get("message") or message)
            raise StreamRateLimitError(retry_message, parse_retry_after_seconds(retry_message)) from exc
        raise


def retry_delay_seconds(exc: StreamRateLimitError, attempt: int) -> float:
    if exc.retry_after_seconds is not None:
        return max(exc.retry_after_seconds, 0.25)
    return min(2 ** (attempt - 1), 8)


def main() -> int:
    args = parse_args()

    try:
        base_url, api_key = load_config()
        body = build_payload(args)
        output_items = []

        for attempt in range(1, args.max_retries + 2):
            try:
                output_items = request_image(base_url, api_key, body, args.timeout)
                break
            except StreamRateLimitError as exc:
                if attempt > args.max_retries:
                    raise
                delay = retry_delay_seconds(exc, attempt)
                print(
                    json.dumps(
                        {
                            "warning": "rate_limited_retrying_original_request",
                            "attempt": attempt,
                            "max_retries": args.max_retries,
                            "delay_seconds": delay,
                            "message": str(exc),
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                time.sleep(delay)

        image_base64 = extract_image_base64_from_items(output_items)
        output_path = Path(args.out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(base64.b64decode(image_base64))
        print(json.dumps({"saved": str(output_path), "bytes": output_path.stat().st_size}, ensure_ascii=False))
        return 0
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        print(
            json.dumps(
                {
                    "error": "http_error",
                    "status": exc.code,
                    "body": message,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    except StreamRateLimitError as exc:
        print(
            json.dumps(
                {
                    "error": "rate_limit_exceeded",
                    "message": str(exc),
                    "note": "Retried with the original prompt and inputs; no prompt simplification was applied.",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    except StreamError as exc:
        print(json.dumps({"error": "stream_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except URLError as exc:
        print(json.dumps({"error": "network_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except TimeoutError as exc:
        print(json.dumps({"error": "timeout", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except Exception as exc:
        print(json.dumps({"error": "runtime_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

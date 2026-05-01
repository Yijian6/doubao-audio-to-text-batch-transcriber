#!/usr/bin/env python3
"""
Batch transcribe local audio files with Volcengine/Doubao ASR flash API.

Supports both auth styles:
1. New console: X-Api-Key
2. Old console: X-Api-App-Key + X-Api-Access-Key
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
import time
import uuid
from pathlib import Path
from typing import Iterable
from urllib import error, request


API_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
DEFAULT_RESOURCE_ID = "volc.bigasr.auc_turbo"
DEFAULT_CONFIG_NAME = "config.json"
SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".opus",
    ".mp4",
    ".flac",
    ".aac",
    ".wma",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch transcribe a folder of local audio files with Doubao ASR."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        type=Path,
        help="Folder containing audio files",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        help="Folder to write .txt files into",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(DEFAULT_CONFIG_NAME),
        help=f"Config file path, default: {DEFAULT_CONFIG_NAME}",
    )
    parser.add_argument("--api-key", default=None, help="New console API key (X-Api-Key)")
    parser.add_argument("--app-key", default=None, help="Old console app key (X-Api-App-Key)")
    parser.add_argument(
        "--access-key",
        default=None,
        help="Old console access key (X-Api-Access-Key)",
    )
    parser.add_argument(
        "--resource-id",
        default=None,
        help=f"Volcengine resource id, default: {DEFAULT_RESOURCE_ID}",
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=None,
        help="Audio file extensions to include, e.g. .mp3 .wav .m4a",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=None,
        help="Scan input directory recursively",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=None,
        help="Overwrite existing .txt outputs",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help="Retry count for failed requests, default: 2",
    )
    parser.add_argument(
        "--retry-wait",
        type=float,
        default=None,
        help="Seconds to wait between retries, default: 3",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=None,
        help="HTTP timeout in seconds, default: 600",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language hint, e.g. zh-CN, en-US, ja-JP",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        default=None,
        help="Also save the raw JSON response beside the txt file",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in config file {config_path}: {exc}") from exc


def get_setting(args: argparse.Namespace, config: dict, arg_name: str, config_name: str, default):
    value = getattr(args, arg_name)
    if value is not None:
        return value
    if config_name in config:
        return config[config_name]
    return default


def apply_config(args: argparse.Namespace, config: dict) -> argparse.Namespace:
    args.input_dir = args.input_dir or (
        Path(config["input_dir"]) if config.get("input_dir") else None
    )
    args.output_dir = args.output_dir or (
        Path(config["output_dir"]) if config.get("output_dir") else None
    )
    args.api_key = get_setting(args, config, "api_key", "api_key", None)
    args.app_key = get_setting(args, config, "app_key", "app_key", None)
    args.access_key = get_setting(args, config, "access_key", "access_key", None)
    args.resource_id = get_setting(
        args, config, "resource_id", "resource_id", DEFAULT_RESOURCE_ID
    )
    args.extensions = get_setting(
        args, config, "extensions", "extensions", sorted(SUPPORTED_EXTENSIONS)
    )
    args.recursive = bool(get_setting(args, config, "recursive", "recursive", False))
    args.overwrite = bool(get_setting(args, config, "overwrite", "overwrite", False))
    args.retries = int(get_setting(args, config, "retries", "retries", 2))
    args.retry_wait = float(get_setting(args, config, "retry_wait", "retry_wait", 3.0))
    args.request_timeout = int(
        get_setting(args, config, "request_timeout", "request_timeout", 600)
    )
    args.language = get_setting(args, config, "language", "language", "") or ""
    args.save_json = bool(get_setting(args, config, "save_json", "save_json", False))
    return args


def normalized_extensions(values: Iterable[str]) -> set[str]:
    result: set[str] = set()
    for value in values:
        ext = value.lower().strip()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        result.add(ext)
    return result


def ensure_auth(args: argparse.Namespace) -> dict[str, str]:
    if args.api_key:
        return {"X-Api-Key": args.api_key}
    if args.app_key and args.access_key:
        return {
            "X-Api-App-Key": args.app_key,
            "X-Api-Access-Key": args.access_key,
        }
    raise SystemExit(
        "Missing auth. Use either --api-key, or both --app-key and --access-key."
    )


def guess_format(audio_path: Path) -> str:
    ext = audio_path.suffix.lower()
    if ext == ".m4a":
        return "mp4"
    if ext == ".opus":
        return "ogg"
    if ext.startswith("."):
        return ext[1:]
    mime, _ = mimetypes.guess_type(audio_path.name)
    if mime and "/" in mime:
        return mime.split("/", 1)[1]
    return "mp3"


def iter_audio_files(input_dir: Path, recursive: bool, extensions: set[str]) -> list[Path]:
    iterator = input_dir.rglob("*") if recursive else input_dir.glob("*")
    return sorted(
        path for path in iterator if path.is_file() and path.suffix.lower() in extensions
    )


def read_as_base64(audio_path: Path) -> str:
    with audio_path.open("rb") as handle:
        return base64.b64encode(handle.read()).decode("utf-8")


def build_payload(audio_path: Path, language: str) -> bytes:
    audio = {
        "format": guess_format(audio_path),
        "data": read_as_base64(audio_path),
    }
    if language:
        audio["language"] = language

    payload = {
        "audio": audio,
        "request": {
            "model_name": "bigmodel",
        },
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def post_json(
    url: str,
    headers: dict[str, str],
    payload: bytes,
    timeout: int,
) -> tuple[int, dict[str, str], dict]:
    req = request.Request(
        url=url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            **headers,
        },
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, dict(resp.headers.items()), json.loads(body or "{}")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        headers_dict = dict(exc.headers.items())
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw_body": body}
        return exc.code, headers_dict, parsed
    except error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        return 0, {}, {"network_error": str(reason)}
    except OSError as exc:
        return 0, {}, {"network_error": str(exc)}


def extract_text(response_json: dict) -> str:
    result = response_json.get("result")
    if isinstance(result, dict):
        text = result.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
        utterances = result.get("utterances")
        if isinstance(utterances, list):
            parts = []
            for item in utterances:
                if isinstance(item, dict):
                    piece = item.get("text")
                    if isinstance(piece, str) and piece.strip():
                        parts.append(piece.strip())
            if parts:
                return "\n".join(parts)
    text = response_json.get("text")
    if isinstance(text, str):
        return text.strip()
    raise ValueError(f"Could not extract transcript text from response: {response_json}")


def transcribe_file(
    audio_path: Path,
    args: argparse.Namespace,
    auth_headers: dict[str, str],
) -> tuple[bool, str, dict | None]:
    headers = {
        **auth_headers,
        "X-Api-Resource-Id": args.resource_id,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "X-Api-Sequence": "-1",
    }
    payload = build_payload(audio_path, args.language)

    last_error = "unknown error"
    last_json: dict | None = None

    for attempt in range(args.retries + 1):
        status, response_headers, response_json = post_json(
            API_URL, headers, payload, args.request_timeout
        )
        last_json = response_json
        api_code = response_headers.get("X-Api-Status-Code", "")
        api_message = response_headers.get("X-Api-Message", "")
        log_id = response_headers.get("X-Tt-Logid", "")

        if status == 200 and api_code == "20000000":
            try:
                text = extract_text(response_json)
                return True, text, response_json
            except Exception as exc:  # noqa: BLE001
                last_error = f"response parse failed: {exc}; log_id={log_id}"
        else:
            last_error = (
                f"http_status={status}, api_code={api_code}, api_message={api_message}, "
                f"log_id={log_id}, body={json.dumps(response_json, ensure_ascii=False)}"
            )

        if attempt < args.retries:
            time.sleep(args.retry_wait)

    return False, last_error, last_json


def make_output_path(audio_path: Path, input_dir: Path, output_dir: Path) -> Path:
    relative = audio_path.relative_to(input_dir)
    return output_dir / relative.with_suffix(".txt")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    config = load_config(args.config.resolve())
    args = apply_config(args, config)

    if args.input_dir is None or args.output_dir is None:
        print(
            "Missing input/output directory. Provide them in command line or config.json.",
            file=sys.stderr,
        )
        return 2

    auth_headers = ensure_auth(args)

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    extensions = normalized_extensions(args.extensions)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        return 2

    audio_files = iter_audio_files(input_dir, args.recursive, extensions)
    if not audio_files:
        print("No matching audio files found.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "transcribe_results.jsonl"

    total = len(audio_files)
    success_count = 0
    skipped_count = 0
    failed_count = 0

    with log_path.open("a", encoding="utf-8") as log_handle:
        for index, audio_path in enumerate(audio_files, start=1):
            output_path = make_output_path(audio_path, input_dir, output_dir)
            json_path = output_path.with_suffix(".json")

            if output_path.exists() and not args.overwrite:
                skipped_count += 1
                print(f"[{index}/{total}] SKIP {audio_path.name} -> existing output")
                continue

            print(f"[{index}/{total}] TRANSCRIBE {audio_path}")
            ok, result, raw_json = transcribe_file(audio_path, args, auth_headers)

            log_record = {
                "audio_path": str(audio_path),
                "output_path": str(output_path),
                "ok": ok,
                "timestamp": int(time.time()),
            }

            if ok:
                write_text(output_path, result)
                if args.save_json and raw_json is not None:
                    write_text(json_path, json.dumps(raw_json, ensure_ascii=False, indent=2))
                success_count += 1
                log_record["text_length"] = len(result)
                print(f"[{index}/{total}] DONE {output_path}")
            else:
                failed_count += 1
                log_record["error"] = result
                print(f"[{index}/{total}] FAIL {audio_path.name}: {result}", file=sys.stderr)

            log_handle.write(json.dumps(log_record, ensure_ascii=False) + "\n")
            log_handle.flush()

    print(
        f"Finished. success={success_count}, skipped={skipped_count}, failed={failed_count}, "
        f"log={log_path}"
    )
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())

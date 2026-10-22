"""Local Chat Completions adapter for fixed sampling and text-form tool calls."""

from __future__ import annotations

from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from urllib.parse import urlsplit
import json
import re
import time
import uuid


def _tool_calls(content: str, allowed: set[str]) -> list[dict]:
    content = content.strip()
    candidates = []
    for piece in re.findall(r"<tool_call>(.*?)</tool_call>", content, re.S | re.I):
        piece = piece.strip()
        if piece.startswith(("{", "[")):
            try:
                candidates.append(json.loads(piece))
            except json.JSONDecodeError:
                continue
        else:
            function = re.search(r"<function=([\w.-]+)>", piece)
            if not function:
                continue
            params = {}
            for key, value in re.findall(r"<parameter=([\w.-]+)>\s*(.*?)\s*</parameter>", piece, re.S):
                params[key] = value.strip()
            candidates.append({"name": function.group(1), "parameters": params})
    if not candidates and content.startswith(("{", "[")):
        try:
            candidates.append(json.loads(content))
        except json.JSONDecodeError:
            pass
    flat = []
    for item in candidates:
        flat.extend(item if isinstance(item, list) else [item])
    calls = []
    for item in flat:
        if not isinstance(item, dict):
            continue
        function = item.get("function") if isinstance(item.get("function"), dict) else item
        name = function.get("name")
        arguments = function.get("arguments", function.get("parameters", {}))
        if name not in allowed:
            continue
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                continue
        if not isinstance(arguments, dict):
            continue
        calls.append({"id": "call_" + uuid.uuid4().hex[:20], "type": "function",
                      "function": {"name": name,
                                   "arguments": json.dumps(arguments, ensure_ascii=False)}})
    return calls


CONTEXT_LIMIT = 32768
CONTEXT_MARGIN = 512
CONTEXT_ERROR = re.compile(
    r"(\d+) tokens from the input messages and (\d+) tokens for the completion",
    re.I,
)


def _retry_output_limit(status: int, raw: bytes, current: int) -> int | None:
    if status != 400:
        return None
    try:
        payload = json.loads(raw)
        error = payload.get("error") or payload
        message = error.get("message", "") if isinstance(error, dict) else str(error)
    except (ValueError, AttributeError):
        return None
    match = CONTEXT_ERROR.search(message)
    if not match:
        return None
    remaining = CONTEXT_LIMIT - int(match.group(1)) - CONTEXT_MARGIN
    return remaining if 256 <= remaining < current else None


def start_proxy(base_url: str, model: str, log_path: Path, timeout: int,
                output_cap: int = 16384):
    upstream = urlsplit(base_url)
    if upstream.scheme != "http" or upstream.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("The model endpoint must be local HTTP")
    log_lock = Lock()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, *_args):
            pass

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length < 20_000_000:
                    raise ValueError("Invalid request length")
                body = json.loads(self.rfile.read(length))
                if body.get("model") != model:
                    raise ValueError("Unexpected model ID")
                requested_stream = bool(body.get("stream"))
                body["temperature"] = 0
                body["chat_template_kwargs"] = {"enable_thinking": False}
                body["max_tokens"] = min(int(body.get("max_tokens") or output_cap), output_cap)
                body["stream"] = False
                body.pop("stream_options", None)
                initial_max_tokens = body["max_tokens"]
                retries = 0
                while True:
                    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
                    target = HTTPConnection(upstream.hostname, upstream.port or 80,
                                            timeout=timeout + 30)
                    try:
                        target.request("POST", "/v1/chat/completions", body=data,
                                       headers={"Content-Type": "application/json"})
                        response = target.getresponse()
                        status = response.status
                        raw = response.read()
                    finally:
                        target.close()
                    retry_limit = _retry_output_limit(status, raw, body["max_tokens"])
                    if retries == 0 and retry_limit is not None:
                        body["max_tokens"] = retry_limit
                        retries += 1
                        continue
                    break
                if status != 200:
                    with log_lock:
                        with log_path.open("a", encoding="utf-8") as handle:
                            handle.write(json.dumps({"model": body["model"],
                                                     "initial_max_tokens": initial_max_tokens,
                                                     "max_tokens": body["max_tokens"],
                                                     "context_retries": retries,
                                                     "upstream_status": status}) + "\n")
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                    return
                result = json.loads(raw)
                message = result["choices"][0]["message"]
                content = message.get("content") or ""
                allowed = {tool.get("function", {}).get("name") for tool in body.get("tools", [])}
                native_calls = message.get("tool_calls")
                calls = native_calls or _tool_calls(content, allowed)
                if calls:
                    message["tool_calls"] = calls
                    message["content"] = None
                with log_lock:
                    with log_path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({"model": body["model"],
                                                 "temperature": body["temperature"],
                                                 "chat_template_kwargs": body["chat_template_kwargs"],
                                                 "initial_max_tokens": initial_max_tokens,
                                                 "max_tokens": body["max_tokens"],
                                                 "context_retries": retries,
                                                 "client_stream": requested_stream,
                                                 "upstream_status": status,
                                                 "finish_reason": result["choices"][0].get("finish_reason"),
                                                 "completion_tokens": (result.get("usage") or {}).get("completion_tokens"),
                                                 "tool_calls": len(calls),
                                                 "translated_text_tools": bool(calls and not native_calls)},
                                                ensure_ascii=False) + "\n")
                if not requested_stream:
                    output = json.dumps(result, ensure_ascii=False).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(output)))
                    self.end_headers()
                    self.wfile.write(output)
                    return
                request_id = result.get("id") or "chatcmpl-" + uuid.uuid4().hex
                created = result.get("created") or int(time.time())

                def event(delta, reason=None, choices=True):
                    item = {"id": request_id, "object": "chat.completion.chunk",
                            "created": created, "model": model,
                            "choices": [{"index": 0, "delta": delta,
                                         "finish_reason": reason}] if choices else []}
                    if not choices and result.get("usage"):
                        item["usage"] = result["usage"]
                    self.wfile.write(("data: " + json.dumps(item, ensure_ascii=False) + "\n\n").encode("utf-8"))
                    self.wfile.flush()

                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()
                event({"role": "assistant"})
                if calls:
                    event({"tool_calls": [{"index": index, **call} for index, call in enumerate(calls)]})
                    event({}, "tool_calls")
                else:
                    event({"content": content})
                    event({}, result["choices"][0].get("finish_reason") or "stop")
                if result.get("usage"):
                    event({}, choices=False)
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as exc:
                try:
                    self.send_error(502, str(exc))
                except OSError:
                    pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"

"""Ollama → Anthropic API 경량 프록시

litellm 대신 직접 구현. Ollama /api/chat ↔ Anthropic /v1/messages 변환.
Claude Code가 Anthropic API로 요청하면 이 프록시가 Ollama로 변환.
"""
import os
import sys
import json
import httpx
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

OLLAMA_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("LLM_MANAGER_MODEL", "gpt-oss:120b")


class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/v1/messages":
            self._handle_messages()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_messages(self):
        """Anthropic /v1/messages → Ollama /api/chat 변환"""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        model = body.get("model", DEFAULT_MODEL)
        # Anthropic 모델명 → Ollama 모델명
        if model.startswith("claude"):
            model = DEFAULT_MODEL

        messages = []
        # system prompt
        if body.get("system"):
            sys_text = body["system"]
            if isinstance(sys_text, list):
                sys_text = "\n".join(b.get("text", "") for b in sys_text if b.get("type") == "text")
            messages.append({"role": "system", "content": sys_text})

        # 대화 메시지 변환
        for msg in body.get("messages", []):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                # Anthropic content blocks → 텍스트 추출
                texts = []
                for block in content:
                    if block.get("type") == "text":
                        texts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        texts.append(f"[Tool call: {block.get('name', '')}({json.dumps(block.get('input', {}))})]")
                    elif block.get("type") == "tool_result":
                        texts.append(f"[Tool result: {block.get('content', '')}]")
                content = "\n".join(texts)
            if role == "assistant" and not content:
                content = "(thinking...)"
            messages.append({"role": role, "content": content})

        stream = body.get("stream", False)
        max_tokens = body.get("max_tokens", 4096)

        # Ollama 호출
        ollama_body = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": body.get("temperature", 0.1),
            },
        }

        # tools 변환 (Anthropic → Ollama)
        if body.get("tools"):
            ollama_tools = []
            for tool in body["tools"]:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {}),
                    }
                })
            ollama_body["tools"] = ollama_tools

        if stream:
            self._stream_response(ollama_body, model)
        else:
            self._sync_response(ollama_body, model)

    def _sync_response(self, ollama_body: dict, model: str):
        """동기 응답"""
        try:
            r = httpx.post(f"{OLLAMA_URL}/api/chat", json=ollama_body, timeout=120.0)
            data = r.json()
            msg = data.get("message", {})

            # Anthropic Messages API 형식으로 변환
            content = []
            text = msg.get("content", "")
            if text:
                content.append({"type": "text", "text": text})

            # tool calls 변환
            for tc in msg.get("tool_calls", []):
                fn = tc.get("function", {})
                content.append({
                    "type": "tool_use",
                    "id": f"toolu_{os.urandom(8).hex()}",
                    "name": fn.get("name", ""),
                    "input": fn.get("arguments", {}),
                })

            stop = "tool_use" if msg.get("tool_calls") else "end_turn"
            resp = {
                "id": f"msg_{os.urandom(8).hex()}",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": content,
                "stop_reason": stop,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _stream_response(self, ollama_body: dict, model: str):
        """SSE 스트리밍 응답 — Anthropic streaming events 형식"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        msg_id = f"msg_{os.urandom(8).hex()}"

        # message_start
        self._sse({"type": "message_start", "message": {
            "id": msg_id, "type": "message", "role": "assistant", "model": model,
            "content": [], "stop_reason": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }})

        # content_block_start
        self._sse({"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}})

        try:
            with httpx.stream("POST", f"{OLLAMA_URL}/api/chat", json=ollama_body, timeout=120.0) as r:
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            self._sse({"type": "content_block_delta", "index": 0,
                                       "delta": {"type": "text_delta", "text": token}})
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self._sse({"type": "content_block_delta", "index": 0,
                       "delta": {"type": "text_delta", "text": f"\n[Error: {e}]"}})

        # content_block_stop + message_stop
        self._sse({"type": "content_block_stop", "index": 0})
        self._sse({"type": "message_delta", "delta": {"stop_reason": "end_turn"},
                   "usage": {"output_tokens": 0}})
        self._sse({"type": "message_stop"})

    def _sse(self, data: dict):
        line = f"event: {data['type']}\ndata: {json.dumps(data)}\n\n"
        self.wfile.write(line.encode())
        self.wfile.flush()

    def log_message(self, format, *args):
        pass  # suppress logs


def run(port: int = 4100):
    print(f"[proxy] Ollama→Anthropic proxy on :{port} (model: {DEFAULT_MODEL})")
    HTTPServer(("127.0.0.1", port), ProxyHandler).serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4100
    run(port)

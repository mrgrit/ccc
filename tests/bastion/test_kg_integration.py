"""KG 통합 테스트 — agent._stream_llm hook + _persist_react_run KG 기록.

실제 Ollama / DB 없이 monkeypatch 로 회로 검증.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── Fake graph / history ───────────────────────────────────────────────


class FakeGraph:
    def __init__(self, results=None):
        self._results = results or []

    def search_fts(self, query, type=None, limit=20):
        if type:
            return [n for n in self._results if n.get("type") == type][:limit]
        return self._results[:limit]


class FakeHistory:
    def __init__(self, anchors=None):
        self._anchors = list(anchors or [])
        self.added: list[dict] = []
        self._anchored_keys: set[str] = set()

    def find_anchors(self, *, kind="", label_like="", limit=50):
        out = []
        for a in self._anchors:
            if kind and a.get("kind") != kind:
                continue
            if label_like and label_like not in a.get("label", ""):
                continue
            out.append(a)
        return out[:limit]

    def is_anchored(self, label_or_body):
        return label_or_body in self._anchored_keys

    def add_anchor(self, kind, label, body, *, related_ids=None,
                   valid_from="", valid_until=""):
        aid = f"anc-{len(self._anchors)}"
        rec = {"id": aid, "kind": kind, "label": label, "body": body,
               "related_ids": related_ids or []}
        self._anchors.append(rec)
        self.added.append(rec)
        try:
            doc = json.loads(body)
            dk = doc.get("dedup_key")
            if dk:
                self._anchored_keys.add(dk)
        except Exception:
            pass
        return aid


# ── Tests for _inject_kg_context ───────────────────────────────────────


def test_inject_kg_context_appends_to_existing_system(monkeypatch):
    from packages.bastion import kg_context
    from packages.bastion.agent import BastionAgent

    g = FakeGraph(results=[
        {"id": "c1", "type": "Concept", "name": "SQLi",
         "content": {"description": "SQL injection"}},
    ])
    h = FakeHistory(anchors=[
        {"id": "anc-1", "kind": "external", "label": "SQLi notes",
         "body": "OWASP A03"},
    ])
    builder = kg_context.KGContextBuilder(graph=g, history=h)
    monkeypatch.setattr(kg_context, "_BUILDER", builder)
    monkeypatch.setattr(kg_context, "get_builder", lambda: builder)

    # BastionAgent 의 __init__ 우회 — _inject_kg_context 만 테스트
    agent = BastionAgent.__new__(BastionAgent)
    agent.model = "gemma3:4b"

    msgs = [
        {"role": "system", "content": "You are a helper."},
        {"role": "user", "content": "How to detect SQL injection?"},
    ]
    out = agent._inject_kg_context(msgs)
    assert out[0]["role"] == "system"
    assert "You are a helper." in out[0]["content"]
    assert "KG 컨텍스트" in out[0]["content"]
    assert "SQLi" in out[0]["content"]
    # 원본 messages 변형 안 됨 (불변성)
    assert msgs[0]["content"] == "You are a helper."


def test_inject_kg_context_prepends_when_no_system(monkeypatch):
    from packages.bastion import kg_context
    from packages.bastion.agent import BastionAgent

    g = FakeGraph(results=[
        {"id": "c1", "type": "Concept", "name": "SQLi",
         "content": {"description": "SQL injection"}},
    ])
    builder = kg_context.KGContextBuilder(graph=g, history=FakeHistory())
    monkeypatch.setattr(kg_context, "_BUILDER", builder)
    monkeypatch.setattr(kg_context, "get_builder", lambda: builder)

    agent = BastionAgent.__new__(BastionAgent)
    agent.model = "gemma3:4b"

    msgs = [{"role": "user", "content": "SQL injection"}]
    out = agent._inject_kg_context(msgs)
    assert out[0]["role"] == "system"
    assert "KG 컨텍스트" in out[0]["content"]
    assert out[1]["role"] == "user"


def test_inject_kg_context_no_user_returns_unchanged():
    from packages.bastion.agent import BastionAgent
    agent = BastionAgent.__new__(BastionAgent)
    agent.model = "gemma3:4b"
    msgs = [{"role": "system", "content": "sys only"}]
    out = agent._inject_kg_context(msgs)
    assert out == msgs


def test_inject_kg_context_silent_on_empty():
    from packages.bastion.agent import BastionAgent
    agent = BastionAgent.__new__(BastionAgent)
    agent.model = "gemma3:4b"
    assert agent._inject_kg_context([]) == []


def test_inject_kg_context_silent_on_kg_failure(monkeypatch):
    from packages.bastion import kg_context
    from packages.bastion.agent import BastionAgent

    class BoomBuilder:
        def build(self, *a, **kw):
            raise RuntimeError("boom")

        def format(self, *a, **kw):
            return ""

    monkeypatch.setattr(kg_context, "get_builder", lambda: BoomBuilder())

    agent = BastionAgent.__new__(BastionAgent)
    agent.model = "gemma3:4b"
    msgs = [{"role": "user", "content": "anything"}]
    out = agent._inject_kg_context(msgs)
    assert out == msgs


def test_inject_kg_context_no_block_when_no_results(monkeypatch):
    from packages.bastion import kg_context
    from packages.bastion.agent import BastionAgent

    builder = kg_context.KGContextBuilder(graph=FakeGraph(), history=FakeHistory())
    monkeypatch.setattr(kg_context, "_BUILDER", builder)
    monkeypatch.setattr(kg_context, "get_builder", lambda: builder)

    agent = BastionAgent.__new__(BastionAgent)
    agent.model = "gemma3:4b"
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "no results query"},
    ]
    out = agent._inject_kg_context(msgs)
    # KG 결과 0건 → 원본 그대로
    assert out == msgs

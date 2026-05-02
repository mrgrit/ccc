"""KGContextBuilder 단위 테스트."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from packages.bastion.kg_context import (
    KGContextBuilder, _budget_for, _hash_key, _short_keywords,
)


# ── Fakes ──────────────────────────────────────────────────────────────


class FakeGraph:
    def __init__(self, results=None):
        self._results = results or []
        self.calls: list = []

    def search_fts(self, query, type=None, limit=20):
        self.calls.append((query, type, limit))
        if type:
            return [n for n in self._results if n.get("type") == type][:limit]
        return self._results[:limit]


class FakeHistory:
    def __init__(self, anchors=None):
        self._anchors = anchors or []
        self.calls: list = []

    def find_anchors(self, *, kind="", label_like="", limit=50):
        self.calls.append((kind, label_like, limit))
        out = []
        for a in self._anchors:
            if kind and a.get("kind") != kind:
                continue
            if label_like and label_like not in a.get("label", ""):
                continue
            out.append(a)
        return out[:limit]


class BoomGraph:
    def search_fts(self, *a, **kw):
        raise RuntimeError("boom")


class BoomHistory:
    def find_anchors(self, **kw):
        raise RuntimeError("boom")


# ── 단위 테스트 ─────────────────────────────────────────────────────────


def test_budget_for_gemma():
    b = _budget_for("gemma3:4b")
    assert b["total"] == 1500
    assert b["anchor"] == 600


def test_budget_for_gpt_oss():
    b = _budget_for("gpt-oss:120b")
    assert b["total"] == 4000
    assert b["anchor"] == 1500


def test_budget_for_unknown_falls_back_to_default():
    b = _budget_for("unknown-model")
    assert b["total"] == 1500


def test_hash_key_stable_and_case_insensitive():
    assert _hash_key("Hello") == _hash_key("hello")
    assert _hash_key(" Hello ") == _hash_key("hello")
    assert _hash_key("a") != _hash_key("b")


def test_short_keywords_extracts_meaningful():
    kws = _short_keywords("How to detect SQL injection on web?")
    assert "How" in kws or "detect" in kws or "SQL" in kws
    # 짧은 단어 (≤2자) 는 제외 — 'on' 있는지 확인
    assert "on" not in kws


def test_build_returns_empty_when_no_message():
    b = KGContextBuilder(graph=FakeGraph(), history=FakeHistory())
    r = b.build("")
    assert r["concepts"] == []
    assert r["anchors"] == []
    assert r["_metrics"]["hits"] == 0


def test_build_collects_concepts_and_anchors():
    g = FakeGraph(results=[
        {"id": "c1", "type": "Concept", "name": "SQLi",
         "content": {"description": "SQL injection technique"}},
        {"id": "p1", "type": "Policy", "name": "auth-mfa",
         "content": {"summary": "MFA required"}},
        {"id": "pb1", "type": "Playbook", "name": "fw-audit",
         "content": {"intent": "firewall audit"}},
    ])
    h = FakeHistory(anchors=[
        {"id": "anc-1", "kind": "external", "label": "SQL injection notes",
         "body": "OWASP A03:2021"},
    ])
    b = KGContextBuilder(graph=g, history=h)
    r = b.build("how to detect SQL injection on web?")
    ids_concept = [c["id"] for c in r["concepts"]]
    ids_policy = [p["id"] for p in r["policies"]]
    assert "c1" in ids_concept
    assert "p1" in ids_policy
    # anchor: label_like fallback 으로 "SQL" 키워드 매칭
    ids_anchor = [a["id"] for a in r["anchors"]]
    assert "anc-1" in ids_anchor


def test_build_cache_hit():
    g = FakeGraph(results=[])
    h = FakeHistory(anchors=[])
    b = KGContextBuilder(graph=g, history=h)
    b.build("hello world cache")
    g_calls_before = len(g.calls)
    r2 = b.build("hello world cache")
    assert len(g.calls) == g_calls_before
    assert r2["_metrics"]["cache"] == "hit"


def test_build_silent_fallback_on_graph_error():
    b = KGContextBuilder(graph=BoomGraph(), history=FakeHistory())
    r = b.build("anything")
    assert r["concepts"] == []
    assert r["_metrics"]["hits"] == 0


def test_build_silent_fallback_on_history_error():
    b = KGContextBuilder(graph=FakeGraph(), history=BoomHistory())
    r = b.build("anything")
    assert r["anchors"] == []


def test_format_outputs_markdown():
    g = FakeGraph(results=[
        {"id": "c1", "type": "Concept", "name": "SQLi",
         "content": {"description": "SQL injection technique"}},
    ])
    h = FakeHistory(anchors=[
        {"id": "anc-1", "kind": "external", "label": "SQLi external",
         "body": "OWASP A03"},
    ])
    b = KGContextBuilder(graph=g, history=h)
    r = b.build("SQL injection")
    s = b.format(r)
    assert "KG 컨텍스트" in s
    assert "Concept" in s
    assert "SQLi" in s
    assert "Anchor" in s


def test_format_returns_empty_when_no_data():
    b = KGContextBuilder(graph=FakeGraph(), history=FakeHistory())
    r = b.build("nothing matches")
    assert b.format(r) == ""


def test_apply_budget_truncates_long_summary():
    long_text = "x" * 5000
    g = FakeGraph(results=[
        {"id": "c1", "type": "Concept", "name": "Big",
         "content": {"description": long_text}},
    ])
    b = KGContextBuilder(graph=g, history=FakeHistory())
    r = b.build("Big")
    assert len(r["concepts"][0]["summary"]) < len(long_text)


def test_format_respects_char_budget():
    g = FakeGraph(results=[
        {"id": f"c{i}", "type": "Concept", "name": f"Item{i}",
         "content": {"description": "text " * 50}}
        for i in range(5)
    ])
    b = KGContextBuilder(graph=g, history=FakeHistory())
    r = b.build("item")
    s = b.format(r, char_budget=200)
    assert len(s) <= 200


def test_node_with_non_dict_content_does_not_crash():
    g = FakeGraph(results=[
        {"id": "c1", "type": "Concept", "name": "Weird", "content": None},
    ])
    b = KGContextBuilder(graph=g, history=FakeHistory())
    r = b.build("Weird")
    assert r["concepts"][0]["id"] == "c1"

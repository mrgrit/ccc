"""KGRecorder 단위 테스트."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from packages.bastion.kg_recorder import (
    KGRecorder, extract_mitre_ids, _semantic_hash,
    KIND_TASK_OUTCOME, KIND_FINDING, KIND_OBSERVATION,
    KIND_ASSET_STATE, KIND_PLAYBOOK_EXEC,
)


# ── Fakes ──────────────────────────────────────────────────────────────


class FakeHistory:
    def __init__(self):
        self.anchors: list[dict] = []
        self._anchored_keys: set[str] = set()

    def is_anchored(self, label_or_body):
        return label_or_body in self._anchored_keys

    def add_anchor(self, kind, label, body, *, related_ids=None,
                   valid_from="", valid_until=""):
        aid = f"anc-{len(self.anchors)}"
        self.anchors.append({
            "id": aid, "kind": kind, "label": label, "body": body,
            "related_ids": related_ids or [],
        })
        try:
            doc = json.loads(body)
            dk = doc.get("dedup_key")
            if dk:
                self._anchored_keys.add(dk)
        except Exception:
            pass
        return aid


class BoomHistory:
    def is_anchored(self, *a, **kw):
        raise RuntimeError("boom")

    def add_anchor(self, *a, **kw):
        raise RuntimeError("boom")


# ── 단위 테스트 ─────────────────────────────────────────────────────────


def test_extract_mitre_ids():
    text = "Used T1190 and T1078.003 to compromise. Also T9999 unknown."
    ids = extract_mitre_ids(text)
    assert "T1190" in ids
    assert "T1078.003" in ids
    assert "T9999" in ids


def test_extract_mitre_ids_empty():
    assert extract_mitre_ids("") == []
    assert extract_mitre_ids("no codes here") == []


def test_semantic_hash_stable():
    h1 = _semantic_hash("a", 1, True)
    h2 = _semantic_hash("a", 1, True)
    h3 = _semantic_hash("a", 1, False)
    assert h1 == h2
    assert h1 != h3


def test_record_task_outcome_creates_anchor():
    h = FakeHistory()
    r = KGRecorder(history=h)
    aid = r.record_task_outcome(
        task_message="exploit web SQLi",
        skills_used=["shell", "probe_all"],
        mitre_ids=["T1190"],
        success=True,
        score=0.85,
        evidence_excerpt="UNION SELECT ... returned 5 users",
        source="r4-driver",
        session_id="s1",
        asset_ids=["asset:web"],
    )
    assert aid is not None
    assert len(h.anchors) == 1
    a = h.anchors[0]
    assert a["kind"] == KIND_TASK_OUTCOME
    assert "exploit web SQLi" in a["label"]
    doc = json.loads(a["body"])
    assert doc["schema_version"] == 1
    assert doc["mitre_ids"] == ["T1190"]
    assert doc["outcome"]["success"] is True
    assert doc["outcome"]["score"] == 0.85
    assert "asset:web" in a["related_ids"]
    assert "T1190" in a["related_ids"]


def test_record_dedupes_same_input():
    h = FakeHistory()
    r = KGRecorder(history=h)
    a1 = r.record_task_outcome(
        task_message="task A", skills_used=["s1"], mitre_ids=["T1"], success=True,
    )
    a2 = r.record_task_outcome(
        task_message="task A", skills_used=["s1"], mitre_ids=["T1"], success=True,
    )
    assert a1 is not None
    assert a2 is None
    assert len(h.anchors) == 1


def test_record_does_not_dedupe_different_outcome():
    h = FakeHistory()
    r = KGRecorder(history=h)
    a1 = r.record_task_outcome(
        task_message="task A", skills_used=["s1"], mitre_ids=["T1"], success=True,
    )
    a2 = r.record_task_outcome(
        task_message="task A", skills_used=["s1"], mitre_ids=["T1"], success=False,
    )
    assert a1 is not None
    assert a2 is not None
    assert len(h.anchors) == 2


def test_record_finding():
    h = FakeHistory()
    r = KGRecorder(history=h)
    aid = r.record_finding(
        category="sqli", severity="critical",
        evidence="UNION SELECT bypass", mitre_id="T1190",
        suggested_action="parameterize queries",
    )
    assert aid is not None
    a = h.anchors[0]
    assert a["kind"] == KIND_FINDING
    assert "T1190" in a["label"]
    doc = json.loads(a["body"])
    assert doc["mitre_id"] == "T1190"
    assert doc["suggested_action"] == "parameterize queries"


def test_record_observation():
    h = FakeHistory()
    r = KGRecorder(history=h)
    aid = r.record_observation(
        asset_id="asset:web",
        observation_type="port_open",
        evidence="port 22 open",
    )
    assert aid is not None
    a = h.anchors[0]
    assert a["kind"] == KIND_OBSERVATION
    assert "asset:web" in a["label"]


def test_record_asset_state():
    h = FakeHistory()
    r = KGRecorder(history=h)
    aid = r.record_asset_state(
        asset_id="asset:web", state="compromised",
        evidence="webshell.php uploaded",
    )
    assert aid is not None
    assert h.anchors[0]["kind"] == KIND_ASSET_STATE


def test_record_playbook_exec():
    h = FakeHistory()
    r = KGRecorder(history=h)
    aid = r.record_playbook_exec(
        playbook_id="pb-firewall-audit",
        success=True, steps_total=5, steps_passed=5,
        elapsed_ms=12000,
    )
    assert aid is not None
    assert h.anchors[0]["kind"] == KIND_PLAYBOOK_EXEC


def test_record_skips_invalid_inputs():
    h = FakeHistory()
    r = KGRecorder(history=h)
    assert r.record_task_outcome(
        task_message="", skills_used=[], mitre_ids=[], success=True,
    ) is None
    assert r.record_observation(
        asset_id="", observation_type="x", evidence="y",
    ) is None
    assert r.record_finding(category="", severity="low", evidence="x") is None
    assert r.record_asset_state(asset_id="", state="x") is None
    assert r.record_playbook_exec(
        playbook_id="", success=True, steps_total=0, steps_passed=0,
    ) is None
    assert len(h.anchors) == 0


def test_record_silent_on_history_error():
    h = BoomHistory()
    r = KGRecorder(history=h)
    aid = r.record_task_outcome(
        task_message="x", skills_used=["a"], mitre_ids=[], success=True,
    )
    assert aid is None  # 예외 없이 None 반환


def test_schema_version_present():
    h = FakeHistory()
    r = KGRecorder(history=h)
    r.record_task_outcome(
        task_message="x", skills_used=[], mitre_ids=[], success=True,
    )
    doc = json.loads(h.anchors[0]["body"])
    assert doc["schema_version"] == 1
    assert "dedup_key" in doc

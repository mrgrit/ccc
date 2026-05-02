"""KGMetrics 단위 테스트."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from packages.bastion.kg_metrics import KGMetrics


def test_inc_counter():
    m = KGMetrics()
    m.inc("foo", labels={"kind": "a"})
    m.inc("foo", labels={"kind": "a"})
    m.inc("foo", labels={"kind": "b"})
    snap = m.snapshot()
    by_label = {(c["name"], c["labels"]): c["value"] for c in snap["counters"]}
    assert by_label[("foo", "kind=a")] == 2
    assert by_label[("foo", "kind=b")] == 1


def test_inc_no_labels():
    m = KGMetrics()
    m.inc("plain")
    m.inc("plain")
    snap = m.snapshot()
    by_label = {(c["name"], c["labels"]): c["value"] for c in snap["counters"]}
    assert by_label[("plain", "")] == 2


def test_observe_distribution():
    m = KGMetrics()
    for v in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        m.observe("latency_ms", v)
    snap = m.snapshot()
    obs = snap["observations"]
    assert len(obs) == 1
    assert obs[0]["count"] == 10
    assert obs[0]["max"] == 100.0
    assert obs[0]["avg"] == 55.0
    assert 50.0 <= obs[0]["p50"] <= 60.0
    assert obs[0]["p95"] == 100.0


def test_reset():
    m = KGMetrics()
    m.inc("x")
    m.observe("y", 1)
    m.reset()
    snap = m.snapshot()
    assert snap["counters"] == []
    assert snap["observations"] == []


def test_max_obs_truncation():
    m = KGMetrics()
    m._max_obs = 5
    for i in range(10):
        m.observe("z", float(i))
    snap = m.snapshot()
    assert snap["observations"][0]["count"] == 5

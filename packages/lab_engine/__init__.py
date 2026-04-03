"""lab_engine — 실습 엔진 (YAML 시나리오, 검증, 블록체인 기록)

Non-AI 시나리오: instruction + hint + verify (script 없음)
AI 시나리오: instruction + script + verify (자동 실행)
"""
from __future__ import annotations
import os
import re
import hashlib
import time
import glob
from dataclasses import dataclass, field, asdict
from typing import Any
from pathlib import Path

import yaml

# ── Data Models ────────────────────────────────────

@dataclass
class VerifyRule:
    type: str          # output_contains | output_regex | exit_code | file_exists | service_running
    expect: str = ""
    field: str = "stdout"  # stdout | stderr | exit_code

@dataclass
class LabStep:
    order: int
    instruction: str
    hint: str = ""
    category: str = ""         # recon | exploit | defense | analysis | response
    points: int = 10
    verify: VerifyRule | None = None
    # AI 버전 전용
    script: str = ""           # Non-AI에는 비어 있어야 함
    risk_level: str = "low"

@dataclass
class Lab:
    lab_id: str
    title: str
    version: str = "non-ai"   # non-ai | ai
    course: str = ""
    week: int = 0
    description: str = ""
    objectives: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    duration_minutes: int = 90
    difficulty: str = "medium"  # easy | medium | hard
    infra_requirements: list[str] = field(default_factory=list)
    steps: list[LabStep] = field(default_factory=list)
    total_points: int = 0
    pass_threshold: float = 0.6   # 60% 이상이면 통과

    def __post_init__(self):
        if self.total_points == 0 and self.steps:
            self.total_points = sum(s.points for s in self.steps)


@dataclass
class StepResult:
    order: int
    passed: bool = False
    points_earned: int = 0
    evidence: dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class LabResult:
    lab_id: str
    student_id: str
    passed: bool = False
    total_points: int = 0
    earned_points: int = 0
    step_results: list[StepResult] = field(default_factory=list)
    block_hash: str = ""
    error: str = ""


# ── YAML Parser ───────────────────────────────────

def load_lab(yaml_path: str) -> Lab:
    """YAML 파일에서 Lab 로드"""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    steps = []
    for s in data.get("steps", []):
        verify = None
        if "verify" in s and s["verify"]:
            v = s["verify"]
            verify = VerifyRule(
                type=v.get("type", "output_contains"),
                expect=str(v.get("expect", "")),
                field=v.get("field", "stdout"),
            )
        steps.append(LabStep(
            order=s.get("order", 0),
            instruction=s.get("instruction", ""),
            hint=s.get("hint", ""),
            category=s.get("category", ""),
            points=s.get("points", 10),
            verify=verify,
            script=s.get("script", ""),
            risk_level=s.get("risk_level", "low"),
        ))

    return Lab(
        lab_id=data.get("lab_id", ""),
        title=data.get("title", ""),
        version=data.get("version", "non-ai"),
        course=data.get("course", ""),
        week=data.get("week", 0),
        description=data.get("description", ""),
        objectives=data.get("objectives", []),
        prerequisites=data.get("prerequisites", []),
        duration_minutes=data.get("duration_minutes", 90),
        difficulty=data.get("difficulty", "medium"),
        infra_requirements=data.get("infra_requirements", []),
        steps=steps,
        total_points=data.get("total_points", 0),
        pass_threshold=data.get("pass_threshold", 0.6),
    )


def load_all_labs(labs_dir: str) -> list[Lab]:
    """디렉토리에서 모든 YAML 실습 로드"""
    labs = []
    for p in sorted(glob.glob(os.path.join(labs_dir, "**/*.yaml"), recursive=True)):
        try:
            labs.append(load_lab(p))
        except Exception as e:
            print(f"[lab_engine] Failed to load {p}: {e}")
    return labs


# ── Verification ──────────────────────────────────

def verify_step(rule: VerifyRule, evidence: dict[str, Any]) -> tuple[bool, str]:
    """단일 스텝 검증"""
    if not rule:
        return True, "No verification rule (auto-pass)"

    value = str(evidence.get(rule.field, ""))

    if rule.type == "output_contains":
        if rule.expect.lower() in value.lower():
            return True, f"Found '{rule.expect}' in {rule.field}"
        return False, f"'{rule.expect}' not found in {rule.field}"

    elif rule.type == "output_regex":
        if re.search(rule.expect, value, re.IGNORECASE | re.MULTILINE):
            return True, f"Regex '{rule.expect}' matched in {rule.field}"
        return False, f"Regex '{rule.expect}' not matched in {rule.field}"

    elif rule.type == "exit_code":
        code = evidence.get("exit_code", -1)
        expected = int(rule.expect) if rule.expect else 0
        if code == expected:
            return True, f"exit_code={code} (expected {expected})"
        return False, f"exit_code={code} (expected {expected})"

    elif rule.type == "file_exists":
        # evidence에 file_check 결과가 있어야 함
        exists = evidence.get("file_exists", False)
        if exists:
            return True, f"File exists: {rule.expect}"
        return False, f"File not found: {rule.expect}"

    elif rule.type == "service_running":
        running = evidence.get("service_running", False)
        if running:
            return True, f"Service running: {rule.expect}"
        return False, f"Service not running: {rule.expect}"

    return False, f"Unknown verify type: {rule.type}"


def evaluate_lab(lab: Lab, submissions: list[dict[str, Any]], student_id: str = "") -> LabResult:
    """
    실습 전체 평가.
    submissions: 각 스텝의 evidence dict 리스트.
      [{"stdout": "...", "exit_code": 0}, ...]
    """
    result = LabResult(
        lab_id=lab.lab_id,
        student_id=student_id,
        total_points=lab.total_points,
    )

    for i, step in enumerate(lab.steps):
        evidence = submissions[i] if i < len(submissions) else {}
        sr = StepResult(order=step.order, evidence=evidence)

        if step.verify:
            passed, msg = verify_step(step.verify, evidence)
            sr.passed = passed
            sr.points_earned = step.points if passed else 0
            sr.message = msg
        else:
            # 검증 없는 스텝은 evidence가 있으면 통과
            sr.passed = bool(evidence)
            sr.points_earned = step.points if sr.passed else 0
            sr.message = "Evidence submitted" if sr.passed else "No evidence"

        result.step_results.append(sr)

    result.earned_points = sum(sr.points_earned for sr in result.step_results)
    result.passed = (result.earned_points / max(result.total_points, 1)) >= lab.pass_threshold
    return result


# ── Validation (YAML 무결성 검증) ──────────────────

def validate_lab(lab: Lab) -> list[str]:
    """Lab YAML 무결성 검증. 오류 목록 반환 (빈 리스트 = 정상)"""
    errors = []

    if not lab.lab_id:
        errors.append("lab_id is empty")
    if not lab.title:
        errors.append("title is empty")
    if not lab.steps:
        errors.append("no steps defined")

    for i, step in enumerate(lab.steps):
        prefix = f"step[{i}]"
        if not step.instruction:
            errors.append(f"{prefix}: instruction is empty")

        # Non-AI 검증: script가 있으면 안 됨
        if lab.version == "non-ai" and step.script:
            errors.append(f"{prefix}: Non-AI lab must NOT have 'script' field")

        # AI 검증: script가 있어야 함
        if lab.version == "ai" and not step.script:
            errors.append(f"{prefix}: AI lab must have 'script' field")

        if step.verify:
            if step.verify.type not in ("output_contains", "output_regex", "exit_code", "file_exists", "service_running"):
                errors.append(f"{prefix}: unknown verify type '{step.verify.type}'")

    if lab.total_points <= 0 and lab.steps:
        errors.append("total_points is 0 or negative")

    return errors


# ── Utility ───────────────────────────────────────

def lab_summary(lab: Lab) -> dict:
    """Lab 요약 정보"""
    return {
        "lab_id": lab.lab_id,
        "title": lab.title,
        "version": lab.version,
        "course": lab.course,
        "week": lab.week,
        "difficulty": lab.difficulty,
        "steps": len(lab.steps),
        "total_points": lab.total_points,
        "pass_threshold": lab.pass_threshold,
        "has_scripts": any(s.script for s in lab.steps),
    }

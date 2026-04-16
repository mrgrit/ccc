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
    # 정답 (admin만 볼 수 있음)
    answer: str = ""           # 정답/풀이 (명령어, 설명, 예상 결과 등)
    answer_detail: str = ""    # 상세 해설
    # AI 버전 전용
    script: str = ""           # Non-AI에는 비어 있어야 함
    risk_level: str = "low"
    # 실행 대상 VM (auto_verify에서 해당 VM의 SubAgent로 실행)
    target_vm: str = ""        # attacker | secu | web | siem | manager (비어있으면 기본 VM)
    # AI 실습용 Bastion 프롬프트
    bastion_prompt: str = ""   # Bastion에 입력할 프롬프트 (AI 버전 전용)

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
            answer=s.get("answer", ""),
            answer_detail=s.get("answer_detail", ""),
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


# ── SubAgent 자동 검증 ─────────────────────────────

def _run_on_subagent(subagent_url: str, command: str, timeout: int = 30) -> dict[str, Any]:
    """SubAgent에서 명령 실행 후 결과 반환"""
    import httpx
    import uuid as _uuid
    try:
        r = httpx.post(
            f"{subagent_url}/a2a/run_script",
            json={
                "project_id": f"lab-verify-{_uuid.uuid4().hex[:8]}",
                "job_run_id": _uuid.uuid4().hex[:8],
                "script": command,
                "timeout_s": timeout,
            },
            timeout=float(timeout + 10),
        )
        r.raise_for_status()
        raw = r.json()
        data = raw.get("detail", raw)
        return {
            "stdout": data.get("stdout", ""),
            "stderr": data.get("stderr", ""),
            "exit_code": data.get("exit_code", -1),
        }
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1}


def _build_verify_command(step: LabStep) -> str | None:
    """스텝의 verify 규칙을 검증할 수 있는 명령어 생성.

    시스템 상태 검증 타입:
      file_exists       — 파일 존재 확인
      file_contains     — 파일 안에 패턴 존재 (expect="pattern|/path/to/file")
      service_active    — systemctl is-active
      service_running   — (alias) systemctl is-active
      port_open         — ss -tlnp 에서 포트 확인
      nft_rule_exists   — nftables 룰셋에서 패턴 검색
      log_contains      — 로그 파일에서 패턴 검색
      command_output    — 임의 명령 실행 후 expect 가 stdout 에 있는지
      output_contains   — (기존) answer 명령 실행 후 expect 문자열 포함 확인
      output_regex      — (기존) answer 명령 실행 후 정규식 매치
      exit_code         — (기존) answer 명령 실행 후 exit code 확인
      exit_code_zero    — (alias) exit code == 0
    """
    if not step.verify:
        return None

    vr = step.verify

    # ── 시스템 상태 검증 (학생 제출 불필요, SubAgent 가 직접 확인) ──

    if vr.type == "file_exists":
        return f"test -f {vr.expect} && echo 'FILE_EXISTS_YES' || echo 'FILE_EXISTS_NO'"

    if vr.type == "file_contains":
        # expect 형식: "pattern|/path/to/file" 또는 "pattern" (field 가 path)
        if "|" in vr.expect:
            pat, fpath = vr.expect.split("|", 1)
        elif vr.field and vr.field.startswith("/"):
            pat, fpath = vr.expect, vr.field
        else:
            pat, fpath = vr.expect, ""
        if not fpath:
            return None
        return f"grep -q {_shq(pat)} {_shq(fpath)} && echo 'FILE_CONTAINS_YES' || echo 'FILE_CONTAINS_NO'"

    if vr.type in ("service_running", "service_active"):
        return f"systemctl is-active {vr.expect} 2>/dev/null && echo 'SERVICE_RUNNING_YES' || echo 'SERVICE_RUNNING_NO'"

    if vr.type == "port_open":
        return f"ss -tlnp 2>/dev/null | grep -q ':{vr.expect}' && echo 'PORT_OPEN_YES' || echo 'PORT_OPEN_NO'"

    if vr.type == "nft_rule_exists":
        return f"nft list ruleset 2>/dev/null | grep -qi {_shq(vr.expect)} && echo 'NFT_RULE_YES' || echo 'NFT_RULE_NO'"

    if vr.type == "log_contains":
        if "|" in vr.expect:
            pat, lpath = vr.expect.split("|", 1)
        elif vr.field and vr.field.startswith("/"):
            pat, lpath = vr.expect, vr.field
        else:
            return None
        return f"grep -qi {_shq(pat)} {_shq(lpath)} && echo 'LOG_CONTAINS_YES' || echo 'LOG_CONTAINS_NO'"

    if vr.type == "command_output":
        # expect = "expected_text", field = "command to run"
        cmd = vr.field if vr.field and not vr.field.startswith("std") else step.answer
        return cmd if cmd else None

    # ── 기존 타입 (answer 명령 실행 기반) ──

    if vr.type == "output_contains" and step.answer:
        return step.answer

    if vr.type == "output_regex" and step.answer:
        return step.answer

    if vr.type in ("exit_code", "exit_code_zero") and step.answer:
        return step.answer

    if step.answer:
        return step.answer

    return None


def _shq(s: str) -> str:
    """셸 인자 싱글쿼트 래핑 (인젝션 방지)."""
    return "'" + s.replace("'", "'\\''") + "'"


def auto_verify_step(step: LabStep, subagent_url: str) -> StepResult:
    """SubAgent에서 자동으로 스텝 검증 (학생 인프라에 직접 확인)"""
    sr = StepResult(order=step.order)

    cmd = _build_verify_command(step)
    if not cmd:
        sr.message = "No auto-verify command available"
        return sr

    result = _run_on_subagent(subagent_url, cmd)
    sr.evidence = result

    if not step.verify:
        sr.passed = result.get("exit_code") == 0
        sr.points_earned = step.points if sr.passed else 0
        sr.message = f"exit_code={result.get('exit_code')}"
        return sr

    vr = step.verify
    stdout = result.get("stdout", "")

    if vr.type == "output_contains":
        if vr.expect.lower() in stdout.lower():
            sr.passed = True
            sr.message = f"Auto-verified: '{vr.expect}' found"
        else:
            sr.passed = False
            sr.message = f"Auto-verify failed: '{vr.expect}' not found in output"

    elif vr.type == "output_regex":
        if re.search(vr.expect, stdout, re.IGNORECASE | re.MULTILINE):
            sr.passed = True
            sr.message = f"Auto-verified: regex matched"
        else:
            sr.passed = False
            sr.message = f"Auto-verify failed: regex not matched"

    elif vr.type == "exit_code":
        expected = int(vr.expect) if vr.expect else 0
        actual = result.get("exit_code", -1)
        sr.passed = actual == expected
        sr.message = f"Auto-verified: exit_code={actual} (expected {expected})"

    elif vr.type == "file_exists":
        sr.passed = "FILE_EXISTS_YES" in stdout
        sr.message = f"Auto-verified: file {'exists' if sr.passed else 'not found'}"

    elif vr.type in ("service_running", "service_active"):
        sr.passed = "SERVICE_RUNNING_YES" in stdout
        sr.message = f"Auto-verified: service {'active' if sr.passed else 'not active'}"

    elif vr.type == "file_contains":
        sr.passed = "FILE_CONTAINS_YES" in stdout
        sr.message = f"Auto-verified: pattern {'found' if sr.passed else 'not found'} in file"

    elif vr.type == "port_open":
        sr.passed = "PORT_OPEN_YES" in stdout
        sr.message = f"Auto-verified: port {vr.expect} {'open' if sr.passed else 'closed'}"

    elif vr.type == "nft_rule_exists":
        sr.passed = "NFT_RULE_YES" in stdout
        sr.message = f"Auto-verified: nftables rule {'found' if sr.passed else 'not found'}"

    elif vr.type == "log_contains":
        sr.passed = "LOG_CONTAINS_YES" in stdout
        sr.message = f"Auto-verified: pattern {'found' if sr.passed else 'not found'} in log"

    elif vr.type == "command_output":
        if vr.expect and vr.expect.lower() in stdout.lower():
            sr.passed = True
            sr.message = f"Auto-verified: '{vr.expect}' found in command output"
        else:
            sr.passed = False
            sr.message = f"Auto-verify failed: '{vr.expect}' not in command output"

    elif vr.type == "exit_code_zero":
        sr.passed = result.get("exit_code") == 0
        sr.message = f"Auto-verified: exit_code={result.get('exit_code')}"

    sr.points_earned = step.points if sr.passed else 0
    return sr


def auto_verify_lab(lab: Lab, subagent_url: str, student_id: str = "",
                    vm_subagents: dict[str, str] | None = None) -> LabResult:
    """전체 실습을 SubAgent를 통해 자동 검증 (학생 인프라에 직접)
    vm_subagents: role → SubAgent URL 매핑 (e.g., {"attacker": "http://ip:8002", "siem": "http://ip:8002"})
    """
    result = LabResult(
        lab_id=lab.lab_id,
        student_id=student_id,
        total_points=lab.total_points,
    )

    for step in lab.steps:
        # step에 target_vm이 지정되어 있으면 해당 VM의 SubAgent 사용
        url = subagent_url
        if step.target_vm and vm_subagents and step.target_vm in vm_subagents:
            url = vm_subagents[step.target_vm]
        sr = auto_verify_step(step, url)
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

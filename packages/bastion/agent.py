"""Bastion Agent 코어 — 자연어 대화 + Skill/Playbook 실행

학생/관리자가 자연어로 보안 작업을 지시하면:
1. LLM이 적절한 skill 또는 playbook을 선택
2. SubAgent A2A로 실제 실행
3. 결과를 요약하여 반환
"""
from __future__ import annotations
import os
import json
import re
from typing import Any, Generator

import httpx

from packages.bastion.skills import SKILLS, skills_to_ollama_tools, execute_skill
from packages.bastion.playbook import list_playbooks, run_playbook, load_playbook
from packages.bastion.prompt import build_system_prompt


class BastionAgent:
    """Bastion 에이전트 — 대화형 보안 운영 에이전트"""

    def __init__(self, vm_ips: dict[str, str],
                 ollama_url: str = "", model: str = ""):
        self.vm_ips = vm_ips
        self.ollama_url = ollama_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("LLM_SUBAGENT_MODEL", os.getenv("LLM_MODEL", "gemma3:4b"))
        self.history: list[dict] = []
        self.evidence: list[dict] = []

    def chat(self, message: str, approval_callback=None) -> Generator[dict, None, None]:
        """자연어 메시지 처리 → skill/playbook 실행 → 결과 스트리밍

        approval_callback: 위험 작업 시 호출. (step_name, skill, params) → bool
        """
        self.history.append({"role": "user", "content": message})

        # Playbook 직접 요청 감지
        pb_match = re.search(r'playbook[:\s]+(\w+)', message, re.IGNORECASE)
        if pb_match:
            pb_id = pb_match.group(1)
            pb = load_playbook(pb_id)
            if pb:
                yield {"event": "message", "content": f"Playbook '{pb['title']}' 실행합니다."}
                yield from run_playbook(pb_id, self.vm_ips, ollama_url=self.ollama_url,
                                        model=self.model, approval_callback=approval_callback)
                return

        # LLM에게 skill 선택 요청
        system_prompt = build_system_prompt(self.vm_ips)
        tools = skills_to_ollama_tools()

        try:
            response = self._call_llm(system_prompt, tools)
        except Exception as e:
            yield {"event": "error", "content": f"LLM 연결 실패: {e}"}
            return

        # tool_call 응답 처리
        tool_calls = response.get("message", {}).get("tool_calls", [])
        if tool_calls:
            for call in tool_calls:
                func = call.get("function", {})
                skill_name = func.get("name", "")
                params = func.get("arguments", {})

                # 승인 필요 체크
                skill_def = SKILLS.get(skill_name, {})
                if skill_def.get("requires_approval") and approval_callback:
                    approved = approval_callback(skill_name, skill_name, params)
                    if not approved:
                        yield {"event": "skill_skip", "skill": skill_name, "reason": "User denied"}
                        continue

                yield {"event": "skill_start", "skill": skill_name, "params": params}

                result = execute_skill(skill_name, params, self.vm_ips,
                                       self.ollama_url, self.model)
                self.evidence.append({"skill": skill_name, "params": params, "result": result})

                yield {"event": "skill_result", "skill": skill_name,
                       "success": result.get("success", False),
                       "output": str(result.get("output", ""))[:1000]}

            # 결과 요약 요청
            summary = self._summarize_results()
            if summary:
                yield {"event": "message", "content": summary}
        else:
            # 텍스트 응답
            content = response.get("message", {}).get("content", "응답 없음")
            yield {"event": "message", "content": content}

        self.history.append({"role": "assistant", "content": response.get("message", {}).get("content", "")})

    def _call_llm(self, system_prompt: str, tools: list[dict] = None) -> dict:
        """Ollama API 호출"""
        messages = [{"role": "system", "content": system_prompt}] + self.history

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 800},
        }
        if tools:
            body["tools"] = tools

        r = httpx.post(f"{self.ollama_url}/api/chat", json=body, timeout=60.0)
        return r.json()

    def _summarize_results(self) -> str:
        """최근 실행 결과 요약"""
        if not self.evidence:
            return ""
        recent = self.evidence[-3:]  # 최근 3개
        summary_parts = []
        for e in recent:
            status = "성공" if e["result"].get("success") else "실패"
            output = str(e["result"].get("output", ""))[:200]
            summary_parts.append(f"[{e['skill']}] {status}: {output}")
        return "\n".join(summary_parts)

    def get_skills(self) -> list[dict]:
        """사용 가능한 skill 목록"""
        return [{"name": k, **{kk: vv for kk, vv in v.items() if kk != "params"}}
                for k, v in SKILLS.items()]

    def get_playbooks(self) -> list[dict]:
        """등록된 playbook 목록"""
        return list_playbooks()

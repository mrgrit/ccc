# Bastion Autopilot — Cycle 1 (55min) Report

**날짜**: 2026-05-18 01:00-02:00 (UTC)
**대상**: secuops/W01 (S1-S3)
**결과**: 3/3 PASS (100%)

## Mission 결과

| # | Mission | 학습 의도 | bastion 결과 | semantic 판정 |
|---|---------|---------|-------------|------------|
| 1 | secuops/W01/S1 (docker ps) | 16+ 컨테이너 Up 확인 | skill_result success=true, **41 컨테이너 명단 출력** | ✅ |
| 2 | secuops/W01/S2 (ProxyJump 4 호스트) | bastion→fw/ips/web/siem ssh + hostname | skill_result success=true, **fw\nips\nweb\nwazuh.manager** | ✅ |
| 3 | secuops/W01/S3 (nft ruleset) | fw 의 nftables 룰셋 출력 | skill_result success=true, **table inet six_filter chain input 출력** | ✅ |

## bastion fix 적용 (cycle 1-8)

| Fix | 위치 | 효과 |
|------|------|------|
| F1 | agent.py:_synth_prompt 분기 | LLM hallucination 차단 (skill fail 시 정직 보고) |
| F1.5 | agent.py:_synth_prompt tool_block 주입 | LLM second-pass 의 tool_output 인지 강화 |
| F2a | skills.py shell.params.target description | bastion-internal 작업 의 target 가이드 |
| F2c | skills.py shell execute auto-override | command pattern (docker/ssh/for) → target=bastion |
| F2c-v2 | F2c pattern 확장 | ssh ProxyJump + bash for loop |
| F4 | agent.py:_extract_shell_from_prose | trailing 한국어 strip (`— 4 호스트 ...` 제거) |
| F5 | __init__.py:run_command subprocess | local 실행 시 su - ccc (uvicorn root → ccc 의 ssh config 가용) |
| bastion IP | __init__.py INTERNAL_IPS | bastion=127.0.0.1 등록 (local subprocess) |

## 오버피팅 회피 점검

본 fix 들 = task-agnostic 인프라 적 보강:
- F1 = 모든 chat 의 LLM hallucination 차단
- F2c = 모든 docker/ssh 명령 의 target 정확성
- F4 = 모든 prose extraction 의 trailing 정정
- F5 = 모든 local subprocess 의 ssh user

특정 lab (secuops W01) 만 위한 hack X. 다른 lab (attack/aisec) + 다른 작업 도
동일 효과 보장.

## 발견 인사이트 (tubewar 응용 대상)

1. **LLM hallucination = LLM-as-judge 의 #1 위험**
   - skill 실패 시 LLM 이 가짜 결과 출력 → 평가 결과 도 가짜
   - tubewar 의 평가 LLM 에 동일 anti-hallucination 룰 필요

2. **System Prompt 분기 (skill_ok vs skill_fail)** = 결정적 quality 향상
   - tubewar 의 평가 prompt 도 학생 입력 의 검증 분기 추가 가능

3. **작은 모델 (gemma3:4b) 의 instruction following 한계** = 명시적 코드 override 필수
   - tubewar 도 평가 LLM 모델 크기 가 quality 직접 영향

4. **trailing 한국어 strip** = prose 명령 추출 의 보편 결함
   - 다국어 환경 의 LLM 응답 parsing 일반 패턴

## 잔존 결함 (cycle 2 대상)

- LLM second-pass content 가 여전 가끔 hallucinate ("도구 실행 실패" 표기 — 단
  skill_result 자체 는 success). F1.5 의 _tool_block 이 너무 길어서 gemma3:4b
  무시 가능. 더 단순화 또는 larger model 사용.
- KG anchor 의 evidence_excerpt 가 LLM final_content (hallucinated 가능) → 다음
  lookup 시 noisy. cycle 3 의 F3 (verify pass 조건) 진행 예정.

## 다음 cycle (2) 대상

- secuops/W01/S4-S12 (9 mission)
- secuops/W02-W15 의 추가 mission
- 5분 GPU cooling 후 진행

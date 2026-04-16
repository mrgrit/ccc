# Bastion — 보안 운영 AI 에이전트

## 한 줄 소개

**Bastion**은 프롬프트 하나로 서버 점검, 방화벽 설정, 침입 탐지, 로그 분석, 인시던트 대응까지 수행하는 **보안 운영 특화 AI 에이전트**입니다.

---

## 왜 Bastion인가?

| 기존 방식 | Bastion |
|-----------|---------|
| 명령어 10줄 외워서 입력 | "Suricata 상태 확인해줘" 한 마디 |
| VM마다 SSH 접속해서 작업 | 에이전트가 알아서 대상 VM 선택·실행 |
| 결과 해석은 사람이 | LLM이 실행 결과를 분석·요약·권고 |
| 반복 작업을 매번 수동 | Experience Layer가 학습하고 Playbook으로 자동화 |

---

## 아키텍처

```
                    ┌─────────────────────────────────┐
                    │         Bastion Agent            │
                    │  Planning → Executing → Analysis │
                    └────────┬───────────┬────────────┘
                             │           │
          ┌──────────────────┤           ├──────────────────┐
          ▼                  ▼           ▼                  ▼
   ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────┐
   │ SubAgent    │  │ SubAgent     │  │ SubAgent    │  │ SubAgent   │
   │ (secu)      │  │ (web)        │  │ (siem)      │  │ (attacker) │
   │ nftables    │  │ Apache       │  │ Wazuh       │  │ nmap       │
   │ Suricata    │  │ ModSecurity  │  │ OpenCTI     │  │ hydra      │
   └─────────────┘  └──────────────┘  └─────────────┘  └────────────┘
```

---

## 핵심 구성 요소

### 1. Skill System (12종)
보안 운영에 필요한 기능이 모듈화되어 있습니다.

| Skill | 역할 |
|-------|------|
| `shell` | 임의 셸 명령 실행 (최후 수단) |
| `configure_nftables` | 방화벽 테이블/체인/룰/set 구조화 관리 |
| `check_suricata` | IDS 상태·최근 알림 조회 |
| `check_wazuh` | SIEM 매니저·에이전트·알림 조회 |
| `check_modsecurity` | WAF 상태·차단 로그 조회 |
| `deploy_rule` | Suricata/Wazuh 탐지 룰 배포 |
| `analyze_logs` | 로그 수집 + LLM 분석 (이상 징후·패턴·요약) |
| `scan_ports` | nmap 포트 스캔 |
| `web_scan` | 웹 취약점 점검 (nikto/curl) |
| `probe_host` | 호스트 상태 점검 (uptime/disk/memory) |
| `probe_all` | 전체 인프라 일괄 점검 |
| `enroll_wazuh_agent` | Wazuh 에이전트 자동 등록 |

### 2. Playbook Engine
검증된 절차를 YAML로 정의해 **재현 가능하게** 실행합니다.

```yaml
# 예: 인시던트 대응 플레이북
playbook_id: incident_response
title: 인시던트 대응 절차
steps:
  - name: 현황 파악
    skill: probe_all
  - name: 알림 확인
    skill: check_wazuh
  - name: 공격자 차단
    skill: configure_nftables
    params:
      action: add_element
      set: blocklist_ips
      element: "{{attacker_ip}}"
```

### 3. Experience Layer
같은 유형의 요청이 반복되면 성공 패턴을 자동으로 학습하고, 충분히 검증되면 Playbook으로 승격합니다.

```
요청 → 실행 → 성공 → 경험 기록 → 반복 성공 → Playbook 승격
                                                    ↑
                                        동일 패턴 3회 이상 성공 시
```

### 4. LLM Intent Classifier
프롬프트를 분석해 **실행(인프라 작업)** vs **답변(지식 질문)**을 LLM 자체가 판단합니다. 특정 키워드에 의존하지 않으므로 모델이 바뀌어도 동작합니다.

### 5. Multi-task Splitter
"다음 작업들을 순서대로 수행해줘: 1) ... 2) ... 3) ..." 형식의 복합 요청을 자동 감지해 서브태스크별로 개별 라우팅합니다.

---

## 사용 방법

### API
```bash
# 프롬프트 전송
curl -X POST http://bastion:8003/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Suricata 상태 확인해줘", "auto_approve": true}'

# 헬스체크
curl http://bastion:8003/health
```

### TUI (대화형 터미널)
```bash
python3 -m apps.bastion.main
```

### CCC 웹 UI
Training → AI 실습에서 bastion_prompt 입력란에 프롬프트를 넣으면 Bastion이 실행하고 결과를 반환합니다.

---

## 폐쇄망·개별 GPU 환경 지원

| 항목 | 설정 |
|------|------|
| LLM 서버 | Ollama (로컬 GPU) |
| Manager 모델 | gpt-oss:120b (DGX Spark) |
| SubAgent 모델 | qwen3:8b (경량 판단) |
| 외부 의존성 | 없음 (완전 오프라인 동작) |

프롬프트만 입력하면 모든 보안 운영 작업을 수행합니다.
외부 API 호출 없이 조직 내부 GPU 서버만으로 동작하므로 **폐쇄망 환경에 적합**합니다.

---

## 실증 테스트 현황

| 항목 | 수치 |
|------|------|
| 총 테스트 케이스 | 2,570개 (15개 과정, 15주차) |
| 고유 보안 과제 유형 | 162개 (25개 대분류) |
| 현재 pass rate | 38% (628/1,644 완료) |
| 등록된 Playbook | 27개 (4 정적 + 23 자동 승격) |
| 누적 Experience | 48개 패턴 (15개 카테고리) |

> 테스트 진행 중. secops(72%), soc-adv(65%), compliance(52%) 등 인프라 실습 과정에서 높은 성공률 확인.

---

*Bastion은 CCC(Cyber Combat Commander) 교육 플랫폼의 핵심 컴포넌트입니다.*

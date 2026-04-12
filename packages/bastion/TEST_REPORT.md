# Bastion 테스트 리포트

**테스트 일자**: 2026-04-12  
**테스트 방식**: Claude → `agent.chat()` 직접 호출 (bastion LLM 플래닝 → SubAgent A2A 실행)  
**LLM**: gpt-oss:120b @ http://211.170.162.139:10534  
**대상 VM**: secu(10.20.30.1), web(10.20.30.80), siem(10.20.30.100), attacker(10.20.30.201)

---

## 테스트 결과 요약

| # | 테스트 | 결과 | 이슈 | 패치 |
|---|--------|------|------|------|
| 1 | probe_host (secu) | ✅ | LLM이 메모리 출력 누락 오탐 | 섹션 헤더 추가, 출력 한도 300→2000자 |
| 2 | probe_all (전체) | ✅ | - | - |
| 3 | scan_ports (web) | ✅ | LLM이 4개 포트 중 2개만 인식 | 포트 요약 파싱 추가 |
| 4 | check_suricata (secu) | ✅ | - | - |
| 5 | probe_all 재확인 | ✅ | - | - |
| 6 | analyze_logs auth.log (secu) | ✅ | - | - |
| 7 | check_suricata 알럿 확인 | ✅ | eve.json 알럿 없음 (정상) | - |
| 8 | check_wazuh 에이전트 목록 | ⚠️ | siem(000)만 등록, 다른 VM 미등록 | enroll_wazuh_agent 스킬 추가 |
| 9 | check_modsecurity (web) | ✅ | - | - |
| 10 | configure_nftables list (secu) | ✅ | - | - |
| 11 | scan_ports (web) | ✅ | - | - |
| 12 | scan_ports 재확인 (개선 후) | ✅ | - | - |
| 13 | probe_host (web) | ✅ | - | - |
| 14 | Wazuh 에이전트 등록 | ✅ | 버전 불일치(4.14.4 vs 4.10.3) | 버전 고정 설치 로직 추가 |

---

## 발견된 이슈 및 패치

### 이슈 1: LLM 분석 출력 잘림 (probe_host)
- **증상**: probe_host 결과에서 메모리/실패서비스 섹션이 있는데 LLM이 "누락"이라고 오탐
- **원인**: `agent.py` L482에서 스킬 결과를 LLM에 전달할 때 `[:300]`으로 잘림
- **패치**: `packages/bastion/agent.py` — 전달 한도 300→2000자, max_tokens 400→600

### 이슈 2: LLM 분석 프롬프트 품질
- **증상**: 데이터가 있는데 없다고 하거나, 수치를 포함하지 않는 분석
- **원인**: 시스템 프롬프트가 "3줄 이내 요약"만 요구, 정확성 강제 없음
- **패치**: `packages/bastion/agent.py` — 프롬프트 개선 (수치 포함 의무화, 데이터 있으면 누락 금지 명시)

### 이슈 3: probe_host에 CPU % 없음
- **증상**: LLM이 "CPU 사용량: 제공되지 않음" 출력
- **원인**: `uptime`은 load average만 제공, CPU % 없음
- **패치**: `packages/bastion/skills.py` — `top -bn1` 추가

### 이슈 4: scan_ports LLM 분석 오류
- **증상**: 4개 포트 중 2개만 인식 (raw nmap 출력이 너무 길어 LLM이 중간에서 중단)
- **원인**: nmap raw 출력이 LLM 컨텍스트를 소모
- **패치**: greppable format + 파싱 요약으로 변환 (`Open ports on X: 4 found\n22/tcp ssh\n...`)

### 이슈 5: Wazuh 에이전트 미등록
- **증상**: siem에 server(000)만 등록, secu/web/attacker 미등록
- **원인**: 온보딩 시 wazuh-agent 설치/등록 미포함
- **패치**: 
  - `enroll_wazuh_agent` 스킬 추가 (SKILLS 정의 + 실행 로직)
  - 자동 설치, Manager IP 설정, agent-auth 등록, 서비스 시작 포함
  - 버전 불일치 이슈: Manager 4.10.3, 기본 설치 4.14.4 → 버전 고정(=4.10.3-1)

### 이슈 6: enroll_wazuh_agent 버전 감지 로직 버그
- **증상**: 잘못된 버전이 설치돼 있어도 `installed=True`로 판단, 버전 교체 안 함
- **원인**: `/var/ossec` 디렉토리 존재 여부로 확인했으나 부정확
- **패치**: `dpkg -l wazuh-agent | grep -q '^ii'`로 변경

---

## 현재 인프라 상태

### Wazuh 에이전트 등록 현황 (테스트 완료 후)
```
ID: 000, Name: siem (server), IP: 127.0.0.1, Active/Local
ID: 001, Name: secu,          IP: any,        Active
ID: 002, Name: web,           IP: any,        Active
ID: 003, Name: attacker,      IP: any,        Active
```

### 각 VM 상태 (테스트 완료 시점)
| VM | CPU | 메모리 | 디스크 | 서비스 |
|----|-----|--------|--------|--------|
| secu | 0% (idle 95.5%) | 822Mi / 1.9Gi (43%) | 37% | 정상 |
| web | 0% (idle 95.5%) | 834Mi / 1.9Gi (44%) | 51% | 정상 |
| siem | - | - | - | Wazuh Manager active |

### nftables (secu)
- input chain: policy drop
- 허용: 내부망(10.20.30.0/24), SSH(22), SubAgent(8002), ICMP
- forward/output: policy accept

### Suricata (secu)
- 상태: active
- eve.json 알럿: 없음 (실제 공격 없는 정상)

### ModSecurity (web)
- 상태: 모듈 로드됨 (security2_module)
- 차단 로그: 없음

---

## 잔여 이슈

1. **onboarding 개선**: 온보딩 시 wazuh-agent 자동 등록 미포함 — `/onboard` 엔드포인트에 `enroll_wazuh_agent` 호출 추가 필요
2. **버전 매핑**: wazuh-agent 설치 시 manager 버전 자동 조회 후 일치 버전 설치 필요
3. **테스트 #15-20**: web_scan, deploy_rule, analyze_logs(siem), attacker 상태, 모의 공격+탐지 미완료

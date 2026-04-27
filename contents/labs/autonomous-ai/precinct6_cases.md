# Real-world Cases — autonomous-ai

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

이 코스의 lab 들이 다루는 위협 카테고리에서 가장 자주 일어나는 *실제* incident 1 건. 각 lab 시작 전 해당 사례를 읽고 어떤 패턴을 *재현·탐지·대응* 할지 가늠하세요.

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


---

## 학습 활용

1. **Red 입장 재현**: 위 IoC + MITRE technique 을 자기 환경 (실습 인프라) 에서 시뮬레이션.
2. **Blue 입장 탐지**: 학습 포인트의 탐지 룰을 자기 SIEM/IDS 에 적용 → false positive 측정.
3. **자기 인프라 검색**: 위 사례의 IoC 를 자기 access.log / DNS log / cron.d 에서 grep — 0건이라야 정상.

각 lab 의 verify.semantic 의 success_criteria 가 위 패턴과 직접 매칭되도록 작성됨 (semantic_first_judge).
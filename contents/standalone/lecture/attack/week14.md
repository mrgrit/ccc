# Week 14 — Caldera + Wazuh Purple Team (신규)

> Caldera 의 adversary 캠페인을 Wazuh / Suricata / ModSec 가 어떻게 detection 하는지
> 측정 + Purple Team (red+blue 협업) 운영 + Coverage Matrix.

## 학습 목표

1. Purple Team 의 정의 + Red / Blue 협업
2. Caldera operation 의 detection 측정
3. ATT&CK Navigator 의 coverage matrix
4. Atomic Red Team (별 도구) 비교
5. AAR (After-Action Report) 작성
6. 운영 가치 — detection gap 분석

## 1. Purple Team 정의

```
Red Team   : 공격 (Caldera, sandcat, ...)
Blue Team  : 방어 (Wazuh, Suricata, ...)
Purple Team: 두 팀 협업 + detection 측정 + 룰 개선
```

목적: detection gap 식별 + 룰 작성 + 재시험.

## 2. Coverage Matrix

```
ATT&CK Technique  | Red executed | Blue detected | Coverage
T1083 File Disc   |  ✓           |  ✗            |  0%
T1057 Process     |  ✓           |  ✓ (osquery)  |  100%
T1018 Network     |  ✓           |  ✓ (Suricata) |  100%
T1190 Public-App  |  ✓           |  ✓ (ModSec)   |  100%
T1078 Valid Acc   |  ✓           |  ✗            |  0%
```

전체 coverage = detected / executed.

## 3. Caldera + Wazuh 통합 흐름

```
[Caldera] → ability 실행 → [agent] → [target host]
                                          │
                                          ▼ syscall / file / network
                                       [osquery / sysmon] → [Wazuh agent]
                                                                   │
                                                                   ▼
                                                            [Wazuh manager]
                                                                   │
                                                                   ▼
                                                            [alerts.json]
                                                                   │
                                                                   ▼
                                             [Caldera] ← detection 비교 ← [Purple Team]
```

## 4. Atomic Red Team 비교

| 측면 | Caldera | Atomic Red Team |
|------|---------|------------------|
| 출시 | 2018 MITRE | 2017 Red Canary |
| 구성 | server + agent | bash / powershell scripts |
| ATT&CK 매핑 | yaml | json |
| 자동화 | full | semi (manual run) |
| GUI | yes | no |
| 운영 권장 | enterprise | quick test |

## 5. AAR (After-Action Report)

```
# AAR — 6v6 Purple Team Cycle #1
## 1. Operation 요약
- 시작: 2026-05-11 14:00
- 종료: 2026-05-11 14:30
- adversary: 6v6 Recon Adversary
- abilities: T1083 / T1057 / T1018
- target: 6v6-web

## 2. Coverage Matrix
| TTP | Red | Blue | %
| T1083 | ✓ | ✗ | 0
| T1057 | ✓ | ✓ | 100
| T1018 | ✓ | ✓ | 100

총 coverage: 67% (2/3)

## 3. Detection Gap 분석
T1083 File Discovery 가 미탐지. 이유:
- osquery 의 file_events 가 /etc 만 감시 (T1083 의 find /etc 매치 안 함)
- 새 룰 필요

## 4. 권장 조치
- osquery file_paths 확장: /etc/* 추가
- Wazuh rule 100400: file enumeration > 50 in 60s
- 재시험: 1주일 후

## 5. 다음 사이클 목표
- Coverage 90%+
```

## 6. 실습 1~4

### 1 — adversary 시뮬 + Wazuh 매트릭스

(Caldera 미설치 시 수동 ability 실행 + alerts.json 매칭)

```
# T1083 시뮬
ssh 6v6-web 'find /etc -name "*.conf" | head -5'
sleep 3
ssh 6v6-siem 'sudo grep -i "file" /var/ossec/logs/alerts/alerts.json | tail -3'

# T1057 시뮬
ssh 6v6-web 'ps -ef | head -20'
sleep 3
ssh 6v6-siem 'sudo grep -i "process" /var/ossec/logs/alerts/alerts.json | tail -3'

# T1018 시뮬
ssh 6v6-attacker 'nmap -sT -p 22,80,443 10.20.32.0/24 2>&1 | tail -10'
sleep 5
ssh 6v6-ips 'sudo grep -i "scan" /var/log/suricata/eve.json | tail -3'
```

### 2 — Coverage Matrix 작성

(위 결과 분석)

### 3 — Detection Gap 분석

(미탐지 TTP 의 원인)

### 4 — 권장 룰 작성

(W13 osquery / Suricata 룰 응용)

## 7. 과제

A. Coverage Matrix (필수) — 5 TTP × Red/Blue
B. Detection Gap 분석 (심화) — 미탐지 TTP 의 원인 + 룰 추가
C. AAR 작성 (정성) — 1페이지 보고서

## 8. W15 (기말) 예고

PTES 종합 + 보고서 (3시간).

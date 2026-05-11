# Week 14 — OpenCTI (3) — Threat Hunting (Sightings + Reports)

> 본 주차는 OpenCTI 의 **위협 헌팅 워크플로** 실습. Hypothesis → Investigation →
> Sightings 등록 → Report 작성 → 공유의 한 사이클. 단순 IOC 매칭 (W13) 에서 한
> 단계 더 나아가 능동적 헌팅.

## 학습 목표

1. Threat Hunting 의 4 단계 (Hypothesis / Investigation / Outcome / Sharing)
2. OpenCTI 의 Sightings (관측 결과) 등록 + 분석
3. Report / Note / Opinion 의 차이 + 활용
4. MITRE ATT&CK 매핑 + Killchain 시각화
5. ISMS-P 2.12 (보안위반 사고 대응) 표준 매핑
6. 한국 KISA 보호나라 사례 분석 패턴

## 1. Threat Hunting 4 단계

### 1.1 Hypothesis (가설)

CTI 데이터 (TTP / IOC) 를 기반으로 "본 환경에 이런 공격이 있을 수도 있다" 가설 수립.

예: "APT29 의 표적 캠페인 보고 → 우리 환경에 같은 IOC 가 있는가?"

### 1.2 Investigation (조사)

기존 데이터 (Wazuh alerts.json, Suricata eve.json, osquery snapshot) 에 가설 검증.

```
# Wazuh alerts 에 APT29 의 IOC 매치 검색
sudo grep "1.2.3.4" /var/ossec/logs/alerts/alerts.json

# Suricata eve.json 의 dest_ip 매치
sudo grep "5.6.7.8" /var/log/suricata/eve.json
```

### 1.3 Outcome (결론)

가설 검증 결과:
- 매치 → 침해 사실 확인 → IR (Incident Response) 시작
- 미매치 → 가설 기각 + 추가 데이터 수집 / 다른 가설

### 1.4 Sharing (공유)

OpenCTI 에 Report / Sighting 등록 + 팀 / 산업 group 공유.

## 2. OpenCTI 의 Sightings

**Sightings = "본 환경에서 IOC 가 관측됨"** 의 기록. STIX 의 sighting-of relationship.

### 2.1 등록 방법

OpenCTI UI: Indicator 선택 → "Add sighting" → 시간 / 위치 / 도구 / 횟수 입력.

API:
```
curl -sk -X POST "https://opencti/api/...sightings" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
      "indicator_id": "...",
      "first_seen": "...",
      "last_seen": "...",
      "count": 3,
      "source_organization": "6v6 학교"
    }'
```

### 2.2 가치

같은 IOC 가 여러 조직에서 sighting 등록 → **신뢰도 (confidence) 자동 상승**. 한 조직만 보고
하면 false-positive 가능성, 10 조직 보고 시 신뢰도 95%+.

## 3. Report / Note / Opinion

| Object | 의미 |
|--------|------|
| Report | 공식 보고서 (IR 결과, 분석 산출물) |
| Note | 개인 메모 (조사 중) |
| Opinion | 동료의 의견 (peer review) |

Report 는 정식 산출물, Note 는 임시, Opinion 은 다중 분석가의 시각.

## 4. MITRE ATT&CK + Killchain 매핑

각 Threat Actor / Attack Pattern 에 MITRE ATT&CK Tactic / Technique 매핑. OpenCTI 가
시각화.

예: "APT29 의 Spearphishing Attachment (T1566.001) → 사용자가 첨부 파일 클릭 → C2 통신
(T1071.001) → Lateral Movement (T1021.001)"

Cyber Kill Chain 7 단계 (Lockheed Martin) 와 ATT&CK 매핑:

| Kill Chain | ATT&CK Tactic |
|------------|---------------|
| Reconnaissance | TA0043 |
| Weaponization | (Pre-ATT&CK) |
| Delivery | TA0042 |
| Exploitation | TA0001 (Initial Access) |
| Installation | TA0003 (Persistence) |
| Command & Control | TA0011 |
| Actions on Objectives | TA0009 (Collection), TA0010 (Exfiltration) |

## 5. ISMS-P 2.12 (보안위반 사고 대응)

한국 ISMS-P 의 2.12 통제:
- 2.12.1 사고 인지·신고 절차
- 2.12.2 사고 대응 체계
- 2.12.3 사고 분석·복구
- 2.12.4 사고 사후 관리

OpenCTI 의 Report / Sighting 가 이 4 sub-control 모두에 입증 자료.

## 6. KISA 보호나라 사례 분석 패턴

KISA 의 침해사고 분석 보고서 1건 선택 → 본 환경의 데이터로 동일 시나리오 시뮬 →
OpenCTI 에 가상 Report 작성.

```
보고서 제목: "2024 Q3 한국 금융권 SQLi 공격 캠페인 대응"
요약: APT 그룹이 한국 은행 5곳 대상 SQLi 시도, 우리 환경의 ModSec 가 차단
IOC: 1.2.3.4 (C2), sqlmap UA (도구)
TTP: T1190 (Exploit Public-Facing Application)
Sightings: 5건 (2024-09-01 ~ 2024-09-15)
Outcome: 차단 100%, 침해 0
```

## 7. 실습 1~5

### 1 — 가설 수립 + Wazuh 검색

```
# 가설: "최근 SSH brute force 가 있었는가?"
ssh 6v6-siem 'sudo grep "5712\|sshd.*Failed" /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5'
```

### 2 — Suricata eve.json 매칭

```
ssh 6v6-ips 'sudo tail -500 /var/log/suricata/eve.json | grep "alert" | jq -r .src_ip | sort | uniq -c | sort -rn | head'
```

### 3 — osquery 의 sshd login history

```
ssh 6v6-bastion 'sudo osqueryi --json "SELECT user, host, time FROM last LIMIT 10;"'
```

### 4 — 통합 timeline 작성

(3 source 의 데이터를 시간순 정렬)

### 5 — Report 작성 (Markdown)

가상 보고서 작성: 가설 + 조사 + 결과 + 권장.

## 8. 과제

A. 헌팅 사례 (필수) — 본 환경의 데이터로 1 시나리오 헌팅 + 가설→조사→결론 1페이지
B. KISA 사례 매핑 (심화) — 2024 KISA 사례 1건 + 본 환경 적용 가설
C. ISMS-P 2.12 매핑 (정성) — 본 주차의 헌팅이 2.12 sub-control 어느 만족하는가

## 9. W15 (기말) 예고

전체 5 종 솔루션 + 호스트 가시화 + CTI 통합의 종합 시험. APT 대응 1 사이클
시나리오.

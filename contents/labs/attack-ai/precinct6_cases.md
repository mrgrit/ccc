# Real-world Cases — attack-ai

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화

이 코스의 lab 들이 다루는 위협 카테고리와 연관된 실제 incident 기록입니다.
각 lab 시작 전 해당 케이스를 참고해 어떤 패턴을 재현·탐지·대응할지 미리 가늠하세요.

---

## Technique 별 사례

### `T1041` 패턴

```
src=100.64.4.210 dst=172.22.195.168 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.84
lifecycle=complete-mission
```

### `T1041` 패턴

```
src=172.22.36.156 dst=100.64.9.98 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.92
lifecycle=complete-mission
```

### `T1041` 패턴

```
src=100.64.14.197 dst=172.17.54.63 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.84
lifecycle=complete-mission
```

## Red ↔ Blue 공격 쌍 (실제 incident 기반)

아래는 실제 보안 운영 환경에서 관찰된 공격자(Exploiting Host) → 피해자(Exploiting Target) 쌍입니다.
battle 시나리오 또는 attack/defense lab 에서 동일 구조로 재현 가능합니다.

- `breach_pair:p6:172.25.238.143→100.64.5.119:Data Theft`
  > incident_id=d45fc680-cb9b-11ee-9d8c-014a3c92d0a7 mo_name=Data Theft
  > red=172.25.238.143 blue=100.64.5.119 suspicion=0.25

- `breach_pair:p6:100.64.3.190→100.64.3.183:Data Theft`
  > incident_id=c6f8acf0-df14-11ee-9778-4184b1db151c mo_name=Data Theft
  > red=100.64.3.190 blue=100.64.3.183 suspicion=0.25

- `breach_pair:p6:100.64.3.249→100.64.4.3:Data Theft`
  > incident_id=f8a04b30-a79e-11ee-a7c6-8CRED-25275a38b323 mo_name=Data Theft
  > red=100.64.3.249 blue=100.64.4.3 suspicion=0.92

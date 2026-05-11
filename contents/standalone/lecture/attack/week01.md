# Week 01 — 보안 개론 + 6v6 실습 환경 (Attacker)

> 본 과목은 사이버 공격·침투 테스트 (Offensive Security) 의 합법적·교육적 학습. 모든
> 실습은 6v6 환경 (`6v6-attacker` 컨테이너 → fw/web 의 8 vuln 사이트) 안에서만
> 진행. 외부 시스템 공격은 RoE (Rules of Engagement) 위반이며 법적 책임 발생.

## 학습 목표

1. 침투 테스트의 윤리 + 법적 한계 (정통망법 / 개인정보보호법) 이해
2. PTES (Penetration Testing Execution Standard) 7 단계 개관
3. MITRE ATT&CK 14 Tactic + Phase 매핑
4. 6v6-attacker 컨테이너의 13 도구 가시화 (nmap, sqlmap, hydra, msfconsole, ...)
5. 8 vuln 사이트 (juice / dvwa / neobank / govportal / mediforum / admin / aicompanion / 랜딩) 의 카테고리
6. 자신의 침투 테스트 학습 계획 작성

## 1. 침투 테스트의 윤리·법적 한계

### 1.1 합법 범위

- **본인이 소유한 시스템 + 명시적 허가받은 시스템만** 공격 가능
- 6v6 환경의 8 vuln 사이트 + bastion + attacker = OK
- 외부 인터넷 + 다른 학생의 환경 = 금지

### 1.2 한국 법적 근거

- **정보통신망법 48조** — 침입·교란·파괴 행위 처벌
- **개인정보보호법 71조** — 정보주체 동의 없는 처리 처벌
- **형법 314조** — 컴퓨터등업무방해
- 처벌 : 5년 이하 징역 / 5천만원 이하 벌금 (최저)

### 1.3 RoE (Rules of Engagement)

침투 테스트 전 다음 합의:
- 대상 (IP / domain / 시간대)
- 허용 도구 (DoS 제외 등)
- 보고 수신처 (CISO / 보안 담당)
- 비상 연락 (시스템 다운 시 즉시 중지)

본 과목 RoE: 6v6 환경 + 24시간 + 모든 도구 + 결과 강사 제출.

## 2. PTES 7 단계

PTES = Penetration Testing Execution Standard.

```
1. Pre-engagement (RoE / scope)
2. Intelligence Gathering (recon, OSINT)
3. Threat Modeling
4. Vulnerability Analysis
5. Exploitation
6. Post Exploitation (privilege escalation, lateral)
7. Reporting
```

각 단계 학습 주차:
- W01 (현재): 1 단계
- W02: 2 단계 (recon)
- W03-07: 4-5 단계 (web 취약점)
- W09-10: 5 단계 (네트워크 + 우회)
- W11-12: 6 단계 (권한 상승 + 지속성)
- W15: 7 단계 (보고서)

## 3. MITRE ATT&CK 14 Tactic

| Tactic | 설명 |
|--------|------|
| TA0001 Initial Access | 첫 진입 |
| TA0002 Execution | 명령 실행 |
| TA0003 Persistence | 지속성 |
| TA0004 Privilege Escalation | 권한 상승 |
| TA0005 Defense Evasion | 우회 |
| TA0006 Credential Access | 자격증명 |
| TA0007 Discovery | 정찰 |
| TA0008 Lateral Movement | 측면 이동 |
| TA0009 Collection | 수집 |
| TA0010 Exfiltration | 유출 |
| TA0011 C2 | 명령·통제 |
| TA0040 Impact | 영향 |
| TA0042 Resource Development | 자원 개발 |
| TA0043 Reconnaissance | 정찰 (외부) |

각 Tactic 아래 200+ Technique. 본 과목 모든 실습이 ATT&CK Technique ID 명시.

## 4. 6v6-attacker 의 13 도구

| 도구 | 카테고리 | 주차 |
|------|---------|------|
| nmap | 정찰·스캐닝 | W02, W09 |
| recon-ng | OSINT | W02 |
| sqlmap | SQLi 자동화 | W04 |
| hydra | brute force | W06 |
| nikto | 웹 스캐너 | W03 |
| dirb | 디렉토리 brute | W02 |
| wfuzz / ffuf | fuzzing | W07 |
| burpsuite | 프록시 | W03 |
| metasploit | 익스플로잇 프레임워크 | W11 |
| john / hashcat | 비밀번호 크래킹 | W06 |
| scapy | packet 작성 | W09 |
| tcpdump | 패킷 캡처 | W09 |
| LinPEAS | 권한 상승 | W11 |

## 5. 8 vuln 사이트 카테고리

| vuln | 카테고리 | 주차 |
|------|---------|------|
| juice.6v6.lab (Juice Shop) | OWASP Top 10 종합 | W03-07 |
| dvwa.6v6.lab (DVWA) | 수준별 (low/medium/high) | W04-05 |
| neobank.6v6.lab (NeoBank) | 가상 은행 (인증 + IDOR) | W06 |
| govportal.6v6.lab (GovPortal) | 가상 정부 (auth + LFI) | W07 |
| mediforum.6v6.lab (MediForum) | 의료 데이터 (XSS) | W05 |
| admin.6v6.lab (AdminConsole) | RCE + XXE | W07, W11 |
| ai.6v6.lab (AICompanion) | LLM prompt injection | (별 과정) |
| 6v6.lab (랜딩) | 정상 — 베이스라인 비교 | W01 |

## 6. 본 주차 실습 1~5

### 1 — attacker 진입

```
ssh ccc@<VM_IP> -p 2202     # 직접 진입
# 또는
ssh 6v6-attacker             # bastion 경유 (학생 PC ssh_config)
```

### 2 — 13 도구 가시화

```
which nmap nikto sqlmap hydra john hashcat scapy ffuf
which msfconsole searchsploit
```

### 3 — 8 vuln 사이트 응답 확인

```
for h in juice dvwa neobank govportal mediforum admin ai 6v6; do
    echo -n "$h.6v6.lab: "
    curl -s -o /dev/null -w "%{http_code}\n" -H "Host: $h.6v6.lab" http://10.20.30.1/
done
```

### 4 — bastion API 호출 (방어 측 도구 인지)

```
curl -s -H "Host: bastion.6v6.lab" -H "X-API-Key: ccc-api-key-2026" http://10.20.30.1/health
```

### 5 — 자신의 학습 계획 작성

15 주차 학습 계획 + 본인의 강점/약점 자가 진단.

## 7. 과제

A. 환경 점검 보고서 (필수) — 13 도구 + 8 vuln 모두 동작 확인
B. PTES 7 단계 매핑 (심화) — 본 과목 15주차가 어느 단계에 해당하는지
C. 본인 학습 계획 (정성) — 15주차 단계별 학습 + 자가 평가

## 8. W02 (정찰) 예고

nmap / recon-ng / theHarvester 로 6v6 환경의 자산 가시화 + OSINT 시뮬.

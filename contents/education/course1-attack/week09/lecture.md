# Week 09: 네트워크 공격 기초 + 패킷 분석

## 학습 목표
- TCP/IP 4계층 모델과 각 계층 주요 프로토콜을 설명한다
- TCP 3-Way Handshake를 이해하고 스캔 기법(SYN/Connect/UDP)과의 관계를 파악한다
- tcpdump로 실제 패킷을 캡처하고 nmap 스캔 트래픽을 해석한다
- Wireshark 오프라인 분석으로 HTTP 세션을 재구성한다
- ARP의 동작 원리와 ARP 스푸핑이 왜 가능한지 이해한다
- IPS/IDS가 스캔을 탐지하는 관점을 설명한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 공격 수행 (nmap·tcpdump·Bastion API :8003) |
| secu | 10.20.30.1 | 경로상 패킷 캡처 (방화벽/IPS) |
| web | 10.20.30.80 | 대상 서버 |
| siem | 10.20.30.100 | Wazuh — 탐지 로그 확인 |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | TCP/IP 모델·3-Way Handshake (Part 1) | 강의 |
| 0:30-1:00 | 포트 스캔 3유형 이론 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | tcpdump 패킷 캡처 실습 (Part 3) | 실습 |
| 1:50-2:30 | Wireshark 오프라인 분석 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | ARP 스푸핑·Suricata 탐지 (Part 5~6) | 실습 |
| 3:10-3:30 | Bastion 자동화 (Part 7) | 실습 |
| 3:30-3:40 | 정리 + 과제 | 정리 |

---

# Part 1: TCP/IP 모델

## 1.1 OSI 7계층 vs TCP/IP 4계층

```
OSI 7계층                          TCP/IP 4계층
-------------------------------    -------------------
7. 응용 (Application)    ]
6. 표현 (Presentation)   ]--->     응용 계층  (HTTP, DNS, SSH)
5. 세션 (Session)        ]
4. 전송 (Transport)      --->      전송 계층  (TCP, UDP)
3. 네트워크 (Network)    --->      인터넷 계층 (IP, ICMP, ARP)
2. 데이터링크 (Link)     ]
1. 물리 (Physical)       ]--->     네트워크 접근 계층 (Ethernet)
```

## 1.2 핵심 프로토콜 정리

| 프로토콜 | 계층 | 역할 | 포트 |
|----------|------|------|------|
| TCP | 전송 | 연결 지향, 신뢰성 보장 | (포트는 서비스별) |
| UDP | 전송 | 비연결, 빠름, 비신뢰 | (포트는 서비스별) |
| IP | 인터넷 | 주소 지정, 라우팅 | - |
| ARP | 인터넷 | IP → MAC 주소 변환 | - |
| ICMP | 인터넷 | 오류 보고, ping | - |
| HTTP | 응용 | 웹 통신 | 80/443 |
| SSH | 응용 | 암호화 원격 접속 | 22 |
| DNS | 응용 | 도메인 → IP 변환 | 53 (TCP/UDP) |

## 1.3 TCP 3-Way Handshake

TCP 연결 수립 절차. 공격자의 스캔 기법들은 이 절차를 어떻게 변형하느냐로 구분된다.

```
클라이언트                             서버
  ---- SYN (seq=100) ------------>     "연결 원함"
  <--- SYN+ACK (seq=200, ack=101) --   "준비됨, 시작 번호 200"
  ---- ACK (ack=201) -------------->   "확인. 통신 시작"
       [연결 수립]
```

**세 플래그의 역할:**
- `SYN`: 시퀀스 번호 동기화 (SYNchronize)
- `ACK`: 상대의 시퀀스 번호 확인 (ACKnowledge)
- `RST`: 즉시 연결 중단 (ReSeT)

## 1.4 ARP (Address Resolution Protocol)

같은 네트워크 내에서 IP → MAC 주소를 매핑하는 2계층 프로토콜.

```
ARP 요청 (브로드캐스트, FF:FF:FF:FF:FF:FF):
  "10.20.30.80의 MAC 주소가 뭐야?"

ARP 응답 (유니캐스트):
  "나다. 내 MAC은 aa:bb:cc:dd:ee:ff"
```

**근본 결함:** ARP에는 인증이 없다. 누구나 거짓 응답으로 "내가 그 IP다"라고 주장 가능 → ARP 스푸핑의 원인.

---

# Part 2: 포트 스캐닝 3유형

## 2.1 SYN 스캔 (Half-Open, `-sS`)

```
공격자                               대상
  ---- SYN --------------------->
  <--- SYN+ACK (포트 열림) ------      → 열림
  ---- RST --------------------->      → 연결 완료하지 않고 끊음

  <--- RST (포트 닫힘) ----------      → 닫힘
```

- 3-Way를 완료하지 **않음** → 서버 애플리케이션 로그에 연결 기록 안 남을 수 있음
- **root 권한 필요** (raw socket)
- 빠르고 은밀

## 2.2 Connect 스캔 (`-sT`)

```
공격자                               대상
  ---- SYN --------------------->
  <--- SYN+ACK ------------------      → 열림
  ---- ACK --------------------->      → 완전한 연결
  ---- FIN/RST ------------------>     → 연결 종료
```

- 완전한 TCP 연결 수립 → **애플리케이션 로그에 기록됨**
- 일반 사용자 권한으로 실행 가능
- 느리고 눈에 띔

## 2.3 UDP 스캔 (`-sU`)

```
공격자                               대상
  ---- UDP 패킷 ----------------->
  <--- ICMP Port Unreachable -----     → 닫힘
       (응답 없음)                     → 열림 또는 필터
```

- UDP는 연결 없음 → "응답 없음"을 "열림"과 "필터"로 구분 불가
- ICMP rate limiting 때문에 매우 느림

## 2.4 nmap 스캔 기본 명령

```bash
nmap -sT -F 10.20.30.80          # Connect 스캔, 상위 100 포트
sudo nmap -sS -p 22,80,3000 10.20.30.80    # SYN 스캔, 지정 포트
nmap -sV -p 22,80,3000 10.20.30.80         # 서비스 버전 탐지
sudo nmap -sU -p 53 10.20.30.80            # UDP 스캔
sudo nmap -O 10.20.30.80                   # OS 탐지
```

Week 02에서 상세 학습. 이번 주는 **탐지 관점**으로 보는 차이를 추가.

---

# Part 3: tcpdump로 패킷 캡처

## 3.1 tcpdump 기초

**이것은 무엇인가?** 네트워크 인터페이스를 통과하는 패킷을 실시간 캡처하는 CLI 도구. Linux 표준 장착.

**왜 필요한가:** nmap이 "무엇"을 보내는지를 실제 바이트로 확인할 수 있는 것이 tcpdump. 추상적 설명을 **실체**로 만든다.

## 3.2 기본 옵션

| 옵션 | 의미 |
|------|------|
| `-i <iface>` | 캡처할 인터페이스 (`any`는 전부) |
| `-nn` | DNS/포트 이름 변환 안 함 (속도·혼동 방지) |
| `-c <N>` | N개 패킷 캡처 후 종료 |
| `-w <file>` | pcap 파일로 저장 (Wireshark 분석용) |
| `-r <file>` | 저장된 pcap 읽기 |
| `-v`/`-vv`/`-vvv` | 상세도 |
| `-X` | 16진수 + ASCII 내용 출력 |
| `-s 0` | 잘림 없이 전체 패킷 |

## 3.3 BPF 필터식

tcpdump는 Berkeley Packet Filter(BPF) 구문으로 조건 필터링.

| 필터식 | 의미 |
|--------|------|
| `host 10.20.30.80` | 특정 호스트가 송신/수신 |
| `src 10.20.30.80` / `dst 10.20.30.80` | 방향 구분 |
| `port 80` | 포트 (TCP/UDP) |
| `tcp port 80` | TCP 80만 |
| `tcp[tcpflags] & tcp-syn != 0` | SYN 플래그 세워진 패킷만 |
| `not arp` | ARP 제외 |
| 조합: `host X and (port 80 or port 443)` | AND/OR |

## 3.4 실습 — nmap 스캔을 실시간 관찰

**Step 1: 터미널 1 (secu 서버에서 캡처 시작)**

```bash
ssh ccc@10.20.30.1

# 인터페이스 확인
ip addr show | grep inet

# 10.20.30.80 대상 TCP 패킷 캡처
sudo tcpdump -i any host 10.20.30.80 -nn -c 50
```

**Step 2: 터미널 2 (manager에서 스캔)**

```bash
# ICMP ping 3회
ping -c 3 10.20.30.80

# TCP Connect 스캔 (sudo 없이)
nmap -sT -p 22,80,3000 10.20.30.80

# SYN 스캔 (sudo)
sudo nmap -sS -p 22,80,3000 10.20.30.80
```

**Step 3: 터미널 1에서 캡처된 패킷 관찰**

**예상 출력 (Connect 스캔 중):**
```
14:30:01.123  IP 10.20.30.200.45678 > 10.20.30.80.22: Flags [S], seq 1234
14:30:01.124  IP 10.20.30.80.22 > 10.20.30.200.45678: Flags [S.], seq 5678, ack 1235
14:30:01.125  IP 10.20.30.200.45678 > 10.20.30.80.22: Flags [.], ack 5679
14:30:01.126  IP 10.20.30.200.45678 > 10.20.30.80.22: Flags [F.], seq 1235
14:30:01.127  IP 10.20.30.80.22 > 10.20.30.200.45678: Flags [F.], seq 5679
14:30:01.128  IP 10.20.30.200.45678 > 10.20.30.80.22: Flags [.], ack 5680
```

**결과 해석:**
- `Flags [S]` → SYN만, `Flags [S.]` → SYN+ACK, `Flags [.]` → ACK만
- Connect 스캔은 `S → S. → . → F. → F. → .` 6개 패킷으로 완전한 연결+종료
- SYN 스캔은 `S → S. → R` 3개로 끝남 → 실습해서 직접 비교

## 3.5 SYN 패킷만 필터링

```bash
ssh ccc@10.20.30.1 "sudo tcpdump -i any 'tcp[tcpflags] & tcp-syn != 0' -nn -c 30" &
# 동시에 manager에서
sudo nmap -sS -p 1-100 10.20.30.80
```

**결과 해석:** 1-100 포트 스캔 시 100개의 SYN 패킷이 빠르게(수백 ms 내) 잡힘. **이 밀집도가 Suricata에게 "포트 스캔" 지문**.

---

# Part 4: Wireshark 오프라인 분석

## 4.1 pcap 파일로 저장

**이것은 무엇인가?** tcpdump는 콘솔 출력이 흐른다. 깊이 분석하려면 pcap 파일로 저장 후 Wireshark GUI로 본다.

```bash
# secu에서 저장
ssh ccc@10.20.30.1 "sudo tcpdump -i any -w /tmp/scan.pcap host 10.20.30.80 -c 200"

# manager에서 스캔 실행
sudo nmap -sS -p 1-1000 10.20.30.80

# pcap 가져오기
scp ccc@10.20.30.1:/tmp/scan.pcap /tmp/
```

## 4.2 tshark로 CLI 분석

**Wireshark가 없어도 CLI로 같은 분석 가능:**

```bash
# HTTP 요청만 추출
tshark -r /tmp/scan.pcap -Y http 2>/dev/null | head -10

# SYN 패킷 수
tshark -r /tmp/scan.pcap -Y 'tcp.flags.syn == 1 and tcp.flags.ack == 0' | wc -l

# 패킷별 시간 분포
tshark -r /tmp/scan.pcap -T fields -e frame.time_relative -e tcp.dstport 2>/dev/null | head -20
```

**결과 해석:**
- SYN 개수 = 스캔된 포트 수
- 시간 분포로 스캔 속도(패킷/초) 측정 → IPS 회피 시 참고

## 4.3 Wireshark GUI 사용 (학생 PC에서)

학생 PC에 Wireshark 설치 후 pcap 열기.

**주요 필터:**
- `http.request.method == POST`: POST 요청만
- `tcp.flags.syn == 1 and tcp.flags.ack == 0`: SYN 스캔 패킷
- `ip.addr == 10.20.30.80`: 특정 IP 관련 전부
- `tcp.port == 3000`: JuiceShop 통신만

**Follow TCP Stream:** 오른쪽 클릭 → Follow → TCP Stream → 한 세션의 전체 주고받음 재구성. HTTP 평문이면 JSON 요청·응답 읽을 수 있음.

---

# Part 5: ARP 스푸핑 (개념 + 관찰)

## 5.1 정상 vs 공격 상태

```
[정상]
  PC-A ─ ARP ─ "10.20.30.1 MAC은?"
         ← GW가 자기 MAC 응답
  PC-A ARP 테이블: 10.20.30.1 → GW_MAC

[ARP 스푸핑]
  공격자 → PC-A에게 계속 가짜 ARP 전송:
         "10.20.30.1 MAC은 내 MAC(공격자_MAC)이야"
  PC-A ARP 테이블: 10.20.30.1 → 공격자_MAC  ← 조작
  이제 PC-A → GW 트래픽이 공격자를 거쳐 감 (MITM)
```

## 5.2 ARP 테이블 확인

```bash
# 현재 ARP 캐시
arp -a
# 또는
ip neigh show
```

**예상 출력:**
```
10.20.30.1 dev eth0 lladdr 52:54:00:xx:xx:xx REACHABLE
10.20.30.80 dev eth0 lladdr 52:54:00:yy:yy:yy REACHABLE
10.20.30.100 dev eth0 lladdr 52:54:00:zz:zz:zz STALE
```

**결과 해석:**
- `52:54:00:` 프리픽스 → KVM/QEMU 가상머신의 OUI
- `REACHABLE` / `STALE` → 최근 통신 여부
- 동일 MAC이 여러 IP에 붙어 있으면 **ARP 스푸핑 의심**

## 5.3 공격의 영향

| 피해 | 설명 |
|------|------|
| **도청 (Sniffing)** | 중간에서 평문 트래픽 관찰 |
| **변조** | 요청·응답 내용 수정 |
| **세션 하이재킹** | 쿠키·토큰 탈취 |
| **DoS** | 트래픽 전달 안 함 → 통신 불가 |

## 5.4 방어

- **정적 ARP 엔트리**: `arp -s 10.20.30.1 <실제_GW_MAC>`
- **DAI (Dynamic ARP Inspection)**: 스위치 레벨 검증 (실제 스위치 필요)
- **arpwatch** / **arpalert**: ARP 변화 감지 → 관리자 알림
- **암호화 트래픽**: HTTPS·SSH 일관성 (평문이면 스푸핑 피해 큼)

> **주의:** 실습 환경 외 네트워크에서 ARP 스푸핑은 **불법**. 이 섹션은 이해·탐지를 위한 것.

---

# Part 6: Suricata IPS의 스캔 탐지

## 6.1 secu의 Suricata 룰 확인

```bash
ssh ccc@10.20.30.1 "sudo ls /etc/suricata/rules/ | head -20"
```

## 6.2 스캔 탐지 시도

**Step 1: 스캔 실행 (manager)**

```bash
sudo nmap -sS -p 1-1000 10.20.30.80
```

**Step 2: Suricata alert 확인 (secu)**

```bash
ssh ccc@10.20.30.1 "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

**예상 alert:**
```
04/23/2026-14:35:01.123456 [**] [1:2010935:3] ET SCAN Possible Nmap Scan (tcp syn) [**]
04/23/2026-14:35:01.234567 [**] [1:2002920:3] ET SCAN Unusual number of SYNs from external [**]
```

**결과 해석:**
- SID 2010935 / 2002920 → Emerging Threats 룰셋의 스캔 탐지 룰
- Week 10에서 이 룰들을 어떻게 **우회**할지 배움 (타이밍 조절, 단편화, 디코이 IP 등)

## 6.3 Wazuh에서도 확인

```bash
ssh ccc@10.20.30.100 \
  "sudo grep -iE 'scan|nmap' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5"
```

Wazuh는 Suricata alert 파일을 감시하여 자체 알림으로 변환. 단일 창구에서 전체 이벤트 관리.

---

# Part 7: Bastion 자연어 패킷 분석

Bastion이 manager에 있으므로 로컬 tcpdump와 연동 가능.

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "10.20.30.80에 nmap -sS -p 22,80,3000 스캔을 실행하고, 스캔 중 secu(10.20.30.1)에서 /var/log/suricata/fast.log를 모니터링해서 어떤 alert가 생성되는지 요약해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

Evidence 확인:

```bash
curl -s "http://10.20.30.200:8003/evidence?limit=5" | python3 -c "
import sys, json
for e in json.load(sys.stdin)[:5]:
    msg = e.get('user_message','')[:70]
    ok = '✓' if e.get('success') else '✗'
    print(f'  {ok} {msg}')
"
```

---

## 과제 (다음 주까지)

### 과제 1: 스캔 기법 비교 보고서 (50점)

1. secu에서 tcpdump 캡처 후 다음 3스캔 실행 → 각각의 pcap을 30패킷 이상 수집 (15점)
   - `nmap -sT -p 22,80,3000 10.20.30.80`
   - `sudo nmap -sS -p 22,80,3000 10.20.30.80`
   - `sudo nmap -sU -p 53,123 10.20.30.80`
2. 각 pcap에서 관찰되는 플래그 시퀀스 정리 (10점)
3. 같은 포트 3개를 스캔할 때 **패킷 수**·**완료 시간** 비교 (10점)
4. Suricata `fast.log`에서 생성된 alert 정리 (10점)
5. 어떤 스캔이 IPS 탐지를 가장 잘 회피했는가 분석 (5점)

### 과제 2: Wireshark 분석 (30점)

1. HTTP 세션 1건을 Wireshark Follow TCP Stream으로 재구성 (10점)
2. JuiceShop 로그인 요청·응답의 헤더·본문 추출 (10점)
3. `tshark`로 CLI에서 SYN 패킷 수 카운트 (10점)

### 과제 3: ARP 테이블 수집 (20점)

1. 4개 VM(manager, secu, web, siem)의 ARP 테이블을 수집 (10점)
2. OUI(`52:54:00:`)로 VM 환경 판단 (5점)
3. ARP 스푸핑 시 PC-A에서 관찰 가능한 변화 서술 (5점)

---

## 다음 주 예고

**Week 10: IPS·방화벽 우회**
- nftables 룰 읽기
- Suricata 룰 우회 (타이밍, 단편화, 디코이)
- `--tamper` 옵션으로 sqlmap WAF 우회
- User-Agent 조작

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **TCP 3-Way Handshake** | - | SYN → SYN+ACK → ACK 로 연결 수립 |
| **SYN 스캔** | Half-Open | 3-Way 완료 안 하는 은밀 스캔 |
| **Connect 스캔** | Full Connect | 완전 연결 후 종료 |
| **pcap** | Packet Capture | 패킷 저장 표준 포맷 |
| **BPF** | Berkeley Packet Filter | 커널 레벨 패킷 필터 구문 |
| **OUI** | Organizationally Unique Identifier | MAC 주소 앞 3바이트로 제조사 식별 |
| **ARP 스푸핑** | ARP Spoofing | 거짓 ARP 응답으로 MITM 수행 |
| **Emerging Threats** | ET 룰셋 | Suricata의 대표적 공개 룰 집합 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실제로 사용하는 도구만.

### Nmap — 이번 주는 탐지 관점 복습

| 옵션 | 이번 주 사용 |
|------|---------------|
| `-sT` | Connect 스캔 (로그 남음 확인용) |
| `-sS` | SYN 스캔 (sudo) |
| `-sU` | UDP 스캔 |
| `-p 22,80,3000` | 제한적 스캔 (속도·노이즈 줄임) |
| `-F` | 상위 100 포트 (빠른 확인) |

### tcpdump

| 옵션 | 이번 주 사용 |
|------|---------------|
| `-i any` | 전 인터페이스 (secu의 양방향 캡처) |
| `-nn` | 이름 변환 안 함 |
| `-c N` | N개만 |
| `-w 파일` | pcap 저장 |
| `-r 파일` | pcap 읽기 |
| BPF: `host IP` | 특정 호스트 |
| BPF: `tcp[tcpflags] & tcp-syn != 0` | SYN만 |

### Wireshark / tshark

| 도구 | 용도 |
|------|------|
| `wireshark 파일.pcap` | GUI 분석 |
| `tshark -r 파일 -Y 'filter'` | CLI 분석 |
| Wireshark "Follow TCP Stream" | 세션 재구성 |
| Wireshark 필터: `http.request.method == POST` | POST만 |
| Wireshark 필터: `tcp.flags.syn == 1 and tcp.flags.ack == 0` | SYN 스캔 |

### Suricata (secu:10.20.30.1)

| 경로 | 역할 |
|------|------|
| `/etc/suricata/rules/` | 룰 파일 디렉토리 |
| `/var/log/suricata/fast.log` | 단순 alert 텍스트 로그 |
| `/var/log/suricata/eve.json` | 구조화 JSON 로그 |

**이번 주 확인 대상 SID:**
- `2010935` ET SCAN Nmap SYN scan
- `2002920` ET SCAN Unusual SYN number

### Bastion API

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 스캔+모니터링 자동화 |
| GET | `/evidence?limit=N` | 기록 조회 |

---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab

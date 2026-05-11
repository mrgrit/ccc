# Week 01 — 보안 솔루션 개론 + 6v6 4-tier 인프라 소개

> 본 주차는 **6v6 4-tier 토폴로지** 위에서 진행한다. 학생 PC 의 VMware Bridge VM 1대 안에
> 16개 docker 컨테이너로 기업급 보안 아키텍처 (방화벽 + IPS + WAF + SIEM + 호스트 가시화)
> 를 구성한다. 외부에 노출된 호스트 포트는 단 5개 (HTTP 80, HTTPS 443, Bastion SSH 2204,
> Attacker SSH 2202, Bastion API 9100) 다.

## 학습 목표

학습자는 본 주차 종료 시 다음을 수행할 수 있어야 한다.

1. 기업·기관에서 사용하는 5종 핵심 보안 솔루션 (방화벽 / IPS / WAF / SIEM / 호스트 가시화)
   의 개념·역할·차이점을 설명한다.
2. Defense in Depth (다층 방어) 원리에 따른 4-tier 토폴로지 (`ext → pipe → dmz → int`) 의
   필요성을 설명한다.
3. 6v6 16개 컨테이너의 IP·역할·라우팅 경로를 화이트보드에 재현한다.
4. bastion ProxyJump 모델로 모든 내부 컨테이너에 SSH 접속하고 헬스체크한다.
5. fw HAProxy 의 운영 트래픽 우회 라우팅 (siem/portal/bastion) 과 학생 트래픽 (취약 웹 8종)
   의 차이를 구별한다.
6. Wazuh manager 의 16 daemon 가시화 + 등록된 agent 3대 (fw/ips/web) 확인.

## 강의 시간 배분 (3시간 40분)

| 시간        | 내용                                                                      | 유형     |
|-------------|---------------------------------------------------------------------------|----------|
| 0:00–0:30   | 이론 — 보안 솔루션이 왜 필요한가? Defense in Depth 원리                    | 강의     |
| 0:30–1:00   | 이론 — 5종 보안 솔루션 (방화벽 / IPS / WAF / SIEM / 호스트 가시화) 상세    | 강의     |
| 1:00–1:10   | 휴식                                                                       | —        |
| 1:10–1:35   | 6v6 4-tier 토폴로지 + 패킷 흐름 + HAProxy 우회 라우팅                       | 강의/토론|
| 1:35–2:00   | 실습 1 — bastion SSH + ProxyJump 설정 + 16 컨테이너 가시화                  | 실습     |
| 2:00–2:30   | 실습 2, 3 — fw (nftables/HAProxy) + ips (Suricata) 헬스체크                | 실습     |
| 2:30–2:40   | 휴식                                                                       | —        |
| 2:40–3:00   | 실습 4, 5 — web (Apache+ModSec) + siem (Wazuh manager 16 daemon)           | 실습     |
| 3:00–3:20   | 실습 6 — Wazuh agent 3대 등록 확인 + portal 운영 대시보드                   | 실습     |
| 3:20–3:40   | 정리 + 과제 안내 + 다음 주차 (nftables 기초) 예고                          | 정리     |

---

## 1. 보안 솔루션은 왜 필요한가? — Defense in Depth

### 1.1 단층 방어의 한계

단일 방어선 (예: 방화벽 하나) 만 두면 그 방어선이 우회되거나 무력화되는 순간 내부 자산은
무방비 노출된다. 실제 침해 사례의 대다수는 다음 패턴을 따른다.

- **2017 Equifax**: 방화벽 통과 + Apache Struts CVE-2017-5638 (RCE) 단일 익스플로잇으로
  1.45억 명 PII 유출. WAF·IPS 시그니처 미배포·미패치가 누적된 결과.
- **2020 SolarWinds Orion**: 빌드 파이프라인 침해 → 정상 서명된 업데이트로 18,000 고객
  배포. 네트워크 방화벽은 정상 outbound 로 인식 → SIEM·EDR 의 행위 분석이 유일한 탐지선.
- **2021 한국 인터파크**: SQLi → 권한 상승 → 17,011건 개인정보 유출. WAF 가 있었으나 룰
  미튜닝, Wazuh급 SIEM 부재로 IDS alert 가 빠르게 묻혔다.

### 1.2 Defense in Depth (DiD) 원리

**다층 방어** 는 NIST SP 800-160 v2 + ISMS-P 통제 2.6 (네트워크 접근) / 2.8 (정보시스템
도입) 의 핵심 원칙으로, 다음 4 레이어로 정의한다.

| 레이어 | 위치 | 통제 도구 (6v6 매핑) | 우회되면? |
|--------|------|---------------------|---------|
| L1 Perimeter | 망 경계 | 방화벽 (`6v6-fw` nftables) | L2 에서 차단 |
| L2 Inline detection | 내부 망 진입 | IPS (`6v6-ips` Suricata) | L3 에서 차단 |
| L3 Application | 응용 계층 | WAF (`6v6-web` ModSecurity) | L4 에서 탐지 |
| L4 Host | 엔드포인트 | SIEM (`6v6-siem` Wazuh) + 호스트 가시화 (osquery/sysmon) | DLP·격리 대응 |

각 레이어는 **독립적** 으로 동작하며, 단일 우회로는 전 자산을 노출시키지 못한다. 이것이
6v6 가 4-tier (`ext → pipe → dmz → int`) 로 강제 분리된 이유다.

### 1.3 6v6 가 단일 VM 인데 왜 4-tier 인가?

학습 환경의 제약 (단일 VM, 6GB RAM) 안에서도 **패킷 흐름의 강제** 를 통해 실제 기업
DiD 를 모사한다. fw 와 ips 는 두 인터페이스 사이의 라우터로 동작하며, 컨테이너 default
route 와 nftables masquerade 가 흐름을 강제한다. 학생이 직접 흐름을 위반할 수 없도록
docker network 의 cross-bridge 차단 + DOCKER-USER ACCEPT 룰로 화이트리스트 한다.

---

## 2. 5종 보안 솔루션 상세

### 2.1 방화벽 (Firewall) — `6v6-fw`

**역할**: 패킷 헤더 (L3/L4) 기반 허용·차단. "출입 통제" 비유.

**6v6 구현**:
- nftables (Linux 커널 4.x 이후 표준, iptables 후속)
- 외부 ext NIC (10.20.30.1) ↔ 내부 pipe NIC (10.20.31.1) 사이 forward
- `net.ipv4.ip_forward=1` + nftables FORWARD chain accept rule + masquerade
- HAProxy 가 사용자 단위 frontend 80/443 을 받아 L7 로 라우팅 (운영 트래픽 우회 + 학생
  트래픽 WAF 경유)

**nftables 핵심 명령** (W02 에서 심화):
```
sudo nft list ruleset                 # 전체 룰 출력
sudo nft list table ip filter         # filter 테이블만
sudo nft add rule ip filter forward \
    ct state established,related accept
```

**한계**: L3/L4 헤더만 본다 → SQLi·XSS 같은 L7 페이로드 공격은 통과시킨다 → WAF 필요.

### 2.2 IDS / IPS (Intrusion Detection / Prevention) — `6v6-ips`

**역할**: 트래픽 페이로드를 시그니처·이상행위 기반으로 검사. "보안 카메라 + 자동 잠금" 비유.

| 구분 | 동작 | 6v6 |
|------|------|-----|
| IDS  | 탐지 + alert (passive sniff) | Suricata 기본 모드 (af-packet) |
| IPS  | 탐지 + 자동 차단 (inline) | Suricata `-q 0` (NFQUEUE) 또는 nftables drop |

**6v6 구현**:
- Suricata 7.x af-packet on `pipe` + `dmz` 두 인터페이스 동시 스니핑
- ETOpen 룰셋 (오픈소스 IDS 룰 70,000+ 개) + custom local rules
- alert → `/var/log/suricata/eve.json` → Wazuh agent → manager → dashboard

**Suricata 핵심 명령** (W04 에서 심화):
```
sudo suricata --build-info             # 빌드 옵션
sudo systemctl status suricata
sudo tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'
```

**한계**: 암호화 트래픽 (TLS) 내부 페이로드는 보지 못한다 → SSL/TLS 인터셉트 (MITM 모드)
필요하지만 신뢰 체인 깨짐 → 6v6 는 HTTP 만 inline 검사.

### 2.3 WAF (Web Application Firewall) — `6v6-web`

**역할**: HTTP/HTTPS 요청·응답을 L7 페이로드 단위로 검사. "응용 계층 전용 검문소" 비유.

**6v6 구현**:
- Apache 2.4 + libapache2-mod-security2 + modsecurity-crs (OWASP CRS v3.x)
- ModSecurity v2 (현재 v3 도 있으나 Apache + v2 가 안정적, Nginx + libmodsecurity 가 v3)
- `SecRuleEngine On` + `SecAuditLogFormat JSON` → `/var/log/apache2/modsec_audit.log`
- 7 vuln 사이트 reverse proxy (`*.6v6.lab` → int 백엔드 8종)

**ModSecurity 핵심 명령** (W06 에서 심화):
```
sudo apache2ctl -M | grep security
sudo cat /etc/modsecurity/modsecurity.conf | head -30
sudo tail -f /var/log/apache2/modsec_audit.log | jq .transaction.id
```

**한계**: 비즈니스 로직 결함 (BOLA, BFLA) 은 시그니처로 잡기 어렵다 → SIEM 행위 분석 보완.

### 2.4 SIEM (Security Information & Event Management) — `6v6-siem`

**역할**: 다 소스 로그 통합 수집·정규화·상관 분석·알림. "CCTV 관제실 + 분석실" 비유.

**6v6 구현 — Wazuh 4.10 stack 3 컨테이너**:
- `6v6-siem` (wazuh-manager:4.10.0) — `wazuh-control status` 가 보고하는 daemon 16종 중
  단일 노드 기본 구성에서 항상 running:
  modulesd, monitord, logcollector, remoted, syscheckd, analysisd, execd, db, authd, apid
  (총 10 + 자체 control). 옵트인 (default off): clusterd, maild, agentlessd, integratord,
  dbd, csyslogd. 단일 노드라 clusterd 가 비활성 정상.
- `6v6-wazuh-indexer` (OpenSearch 기반 백엔드, 색인)
- `6v6-wazuh-dashboard` (시각화 UI)

**입력 paradigm 2종** (W09–W11 에서 심화):
- **Agent paradigm**: Wazuh agent 가 호스트에 설치되어 자체 디코딩 후 1514/tcp 로 전송.
  6v6 에서 `6v6-fw / 6v6-ips / 6v6-web` 3 대.
- **Syslog paradigm**: rsyslog 가 raw 로그를 514/udp 로 forward. manager 의 logcollector
  + decoder 가 파싱. 외부 네트워크 장비 (스위치/라우터) 통합에 사용.

**Wazuh 핵심 명령**:
```
docker exec 6v6-siem /var/ossec/bin/wazuh-control status
docker exec 6v6-siem /var/ossec/bin/agent_control -l    # 등록 agent 목록
docker exec 6v6-siem cat /var/ossec/etc/ossec.conf | grep -A2 '<remote>'
```

**한계**: 룰·디코더가 사전 정의되지 않은 새 로그 형식은 raw 로 적재됨 → 사용자 정의 디코더
작성 (W09).

### 2.5 호스트 가시화 — osquery + sysmon-for-linux (W07, W11 심화)

**역할**: 네트워크 시그니처로 잡히지 않는 호스트 내부 행위 (프로세스, 파일, 사용자, 소켓)
를 구조화된 형태로 가시화. "건물 내부 모든 방의 입실 기록" 비유.

**도구**:
- **osquery** (Facebook 2014): OS 를 SQL 테이블로 추상화 → `SELECT name, pid FROM
  processes WHERE on_disk=0;` 같은 헌팅 쿼리.
- **sysmonforlinux** (Microsoft 2021): Windows Sysmon 의 Linux 포팅. eBPF + auditd
  기반 process create / network connect / file create 등 30+ 이벤트 종류.

**6v6 에서의 배치 (W07/W11)**:
- osquery: bastion + fw + ips + web 4 호스트에서 daemon 모드. 결과는 Wazuh agent 의
  `localfile` 로 ship.
- sysmon-for-linux: web + fw + ips 3 호스트. eBPF probe + `/var/log/sysmonforlinux.log`
  → Wazuh agent 가 수집 → manager 의 sysmon decoder 가 파싱.

**왜 추가했나?** 네트워크 시그니처 (Suricata) + 로그 상관 (Wazuh 룰) 만으로는 정상 binary
의 악성 사용 (LOLBins, Living-off-the-Land Binaries) 을 잡지 못한다. 호스트 가시화는 침해
대응의 마지막 안전망이다.

---

## 3. 6v6 4-tier 토폴로지 상세

### 3.1 Tier 별 컨테이너 (총 16개)

| Tier | 컨테이너 | IP | 보안 솔루션 / 역할 |
|------|----------|-----|-------------------|
| **ext** (10.20.30.0/24) | `6v6-bastion` | .201 | SSH 점프 + Bastion API + KG |
| **ext** | `6v6-attacker` | .202 | nmap, hydra, sqlmap, msfconsole 등 13 도구 |
| **fw (ext↔pipe)** | `6v6-fw` | .1 (ext) / .1 (pipe) | nftables + HAProxy + Wazuh agent |
| **ips (pipe↔dmz)** | `6v6-ips` | .2 (pipe) / .1 (dmz) | Suricata + nftables masq + Wazuh agent |
| **dmz** (10.20.32.0/24) | `6v6-web` | .80 (dmz) / .80 (int) | Apache + ModSecurity + 11 vhost + Wazuh agent |
| **dmz** | `6v6-siem` | .100 | Wazuh manager (16 daemon) |
| **dmz** | `6v6-wazuh-indexer` | .110 | OpenSearch 색인 |
| **dmz** | `6v6-wazuh-dashboard` | .120 | Wazuh Web UI (HTTPS 5601) |
| **dmz** | `6v6-portal` | .50 | 운영 포털 (FastAPI + HTMX) |
| **int** (10.20.40.0/24) | `6v6-juiceshop` | .81 | OWASP Juice Shop |
| **int** | `6v6-dvwa` | .82 | DVWA |
| **int** | `6v6-neobank` | .83 | NeoBank (가상 은행) |
| **int** | `6v6-govportal` | .84 | GovPortal (가상 정부 포털) |
| **int** | `6v6-mediforum` | .85 | MediForum (가상 의료 포털) |
| **int** | `6v6-adminconsole` | .86 | AdminConsole (RCE / XXE) |
| **int** | `6v6-aicompanion` | .87 | AI 대화 백엔드 (LLM 취약점) |

### 3.2 외부 노출 (호스트 포트)

```
+----------------------------+-----------------------------------+
| Host port                  | Container target                  |
+----------------------------+-----------------------------------+
| 80                         | fw:80   (HAProxy frontend)        |
| 443                        | fw:443  (HAProxy frontend TLS)    |
| 2204                       | bastion:22  (SSH 점프 호스트)     |
| 2202                       | attacker:22 (SSH 직접 진입)       |
| 9100                       | fw:9100 → bastion API HAProxy    |
+----------------------------+-----------------------------------+
```

### 3.3 학생 PC 접속 패턴

**브라우저** — 학생 PC `/etc/hosts` (윈도우는 `C:\Windows\System32\drivers\etc\hosts`)
에 1줄 추가:

```
<VM_IP> 6v6.lab juice.6v6.lab dvwa.6v6.lab neobank.6v6.lab govportal.6v6.lab mediforum.6v6.lab admin.6v6.lab ai.6v6.lab portal.6v6.lab siem.6v6.lab bastion.6v6.lab
```

그 후 `<VM_IP>` 를 brower 의 hosts 로 인식 → 11 vhost 자동 라우팅.

**HTTPS** — fw 가 self-signed cert 사용. 학생 PC 에 `http://<VM_IP>/6v6-ca.crt` 다운로드 후
신뢰 체인에 import 하거나, 강의 시간엔 경고 무시 진행.

**SSH ProxyJump** — 학생 PC `~/.ssh/config` 에 한 번 추가:

```
Host 6v6-bastion
  HostName <VM_IP>
  Port 2204
  User ccc

Host 6v6-attacker
  HostName <VM_IP>
  Port 2202
  User ccc

Host 6v6-*
  ProxyJump 6v6-bastion
  User ccc
```

그 후 `ssh 6v6-fw`, `ssh 6v6-ips`, `ssh 6v6-web`, `ssh 6v6-siem` — 모두 bastion 경유. 비밀번호 `ccc`.

### 3.4 패킷 흐름 (강제)

**학생 트래픽 (취약 웹) — 4 hop**:

```
학생 PC 브라우저
  → http://juice.6v6.lab/
  → VM_IP:80
  → fw HAProxy (default_backend waf)
  → ips Suricata inline
  → web Apache (ModSec WAF 적용)
  → int juiceshop:3000
```

**운영 트래픽 (siem/portal/bastion API) — 3 hop, WAF 우회**:

```
학생 PC 브라우저
  → http://siem.6v6.lab/
  → VM_IP:80
  → fw HAProxy (use_backend dashboard)
  → ips Suricata inline (관찰만)
  → dmz wazuh-dashboard:5601 (TLS)
```

운영 트래픽은 web 의 WAF 를 거치지 않는다. 운영자가 SIEM dashboard 를 켜는 행위가 ModSec
룰에 false-positive 로 잡혀서는 안 되기 때문. 그러나 ips 의 Suricata 는 모든 dmz inbound 를
sniff 하므로 alert 자체는 발생할 수 있다.

### 3.5 fw HAProxy 라우팅 규칙

fw HAProxy 는 호스트 포트 3종 (80 / 443 / 9100) 을 각각 다른 frontend 로 받고,
총 **6 backend** 로 라우팅한다.

```
# HTTP 80 frontend
frontend http_in
    bind *:80
    acl is_siem    hdr(host) -i siem.6v6.lab
    acl is_portal  hdr(host) -i portal.6v6.lab
    acl is_bastion hdr(host) -i bastion.6v6.lab
    use_backend dashboard if is_siem
    use_backend portal    if is_portal
    use_backend bastion   if is_bastion
    default_backend waf

# HTTPS 443 frontend
frontend https_in
    bind *:443 ssl crt /etc/haproxy/certs/6v6.pem
    acl is_siem    hdr(host) -i siem.6v6.lab
    acl is_portal  hdr(host) -i portal.6v6.lab
    acl is_bastion hdr(host) -i bastion.6v6.lab
    use_backend dashboard if is_siem
    use_backend portal    if is_portal
    use_backend bastion   if is_bastion
    default_backend waf_tls

# Bastion API 9100 frontend
frontend bastion_api_in
    bind *:9100
    default_backend bastion_api

# Backends (6종)
backend waf
    server web 10.20.32.80:80 check          # 학생 트래픽 HTTP → web ModSec
backend waf_tls
    server web 10.20.32.80:443 check ssl verify none  # 학생 트래픽 HTTPS
backend dashboard
    server dashboard 10.20.32.120:5601 check ssl verify none
backend portal
    server portal 10.20.32.50:8000 check
backend bastion
    server bastion 10.20.30.201:9100 check
backend bastion_api
    server bastion 10.20.30.201:9100 check
```

---

## 4. 용어 해설 (Glossary)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단 | 건물 출입 통제 |
| **테이블/체인** | Table / Chain (nftables) | 룰 묶음의 컨테이너 / 처리 단계 (input, forward, output) | 캐비넷 / 심사 단계 |
| **DNAT/SNAT** | Destination/Source NAT | 패킷의 목적지/출발지 IP 변환 | 대표번호 안내 / 회사 대표번호 |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 | 수배범 얼굴 사진 |
| **IDS** | Intrusion Detection System | 악성 트래픽 탐지·알림 | 경보기 |
| **IPS** | Intrusion Prevention System | 탐지 + 자동 차단 | 경보 + 자동 잠금 |
| **NFQUEUE** | Netfilter Queue | 커널에서 user-space 로 패킷을 넘기는 큐 (Suricata IPS 모드) | 의심 택배 별도 검사대 |
| **WAF** | Web Application Firewall | HTTP/HTTPS 전용 방화벽 (SQLi/XSS 차단) | 입구 금속탐지기 |
| **CRS** | OWASP Core Rule Set | ModSecurity 의 표준 룰셋 (OWASP Top 10 자동 탐지) | 표준 보안 검사 매뉴얼 |
| **SIEM** | Security Information & Event Management | 로그 통합 수집·분석·알림 플랫폼 | CCTV 관제실 + 분석실 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV 로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 원시 로그를 구조화된 필드로 파싱 | 외국어 통역사 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인) | 수배범 지문, 차량번호 |
| **STIX/TAXII** | Structured Threat Information eXpression / Trusted Automated eXchange | CTI 표준 포맷·교환 프로토콜 | 범죄 보고서 표준 / 경찰서 간 공유 |
| **Bastion** | Bastion host | 외부에서 내부망 SSH 의 유일한 진입점 | 정문 안내데스크 |
| **Reverse Proxy** | — | 외부 요청을 받아 내부 백엔드로 전달 | 호텔 컨시어지 |
| **vhost** | Virtual Host | 같은 IP/포트에서 도메인별 다른 사이트 서비스 | 한 건물 안 여러 매장 |
| **HAProxy** | High Availability Proxy | L7 reverse proxy / load balancer | 호텔 안내 데스크 (방 번호 라우팅) |
| **osquery** | osquery | OS 를 SQL 테이블로 추상화한 호스트 가시화 도구 | 건물 내 모든 방 입실 기록 SQL |
| **sysmon** | System Monitor (for Linux) | 프로세스·네트워크·파일 이벤트 추적 (eBPF 기반) | 정밀 동선 추적 카메라 |
| **eBPF** | extended Berkeley Packet Filter | 커널 내부에서 안전하게 사용자 정의 코드 실행 | 빌딩 내부에 가벼운 임시 검사실 설치 |

---

## 5. 전제 조건

- Linux 기본 명령어 (systemctl, cat, grep, ps, ss 수준)
- Docker 기본 (`docker ps`, `docker logs`) 사용 경험
- VMware Workstation 또는 VirtualBox 로 Linux VM 부팅 가능
- 학생 PC 에 OpenSSH client + 브라우저 (Chrome / Firefox)

---

## 6. 실습 시나리오 (실습 1~6 — Step by Step)

### 실습 1 — bastion SSH + ProxyJump 설정 + 16 컨테이너 가시화

**목표**: 학생 PC 에서 단일 진입점 (bastion:2204) 으로 16개 컨테이너 전부에 접근.

```
# 학생 PC ~/.ssh/config 편집
ssh 6v6-bastion docker ps --format '{{.Names}}\t{{.Status}}' | head -20
# 출력: 16개 컨테이너 모두 Up 상태 확인

# fw 접속
ssh 6v6-fw ip -4 addr show
# eth0: 10.20.30.1/24 (ext), eth1: 10.20.31.1/24 (pipe)
```

**검증 포인트**:
1. bastion 에서 `docker ps` 가 16건 (또는 그 이상) Up
2. `ssh 6v6-fw` 로 fw 컨테이너 진입, 2개 NIC 확인
3. `ssh 6v6-ips`, `ssh 6v6-web`, `ssh 6v6-siem` 모두 성공

### 실습 2 — fw nftables / HAProxy 헬스체크

**목표**: 방화벽 동작 확인 + HAProxy backend health.

```
ssh 6v6-fw sudo nft list table ip filter
ssh 6v6-fw sudo ss -tlnp | grep -E ':(80|443|9100|22)'
ssh 6v6-fw cat /var/log/haproxy.log 2>/dev/null | tail -5
```

**검증 포인트**:
1. nftables ruleset 에 forward chain accept rule 존재
2. HAProxy 가 80/443 listen
3. HAProxy frontend / backend health 모두 UP

### 실습 3 — ips Suricata 헬스체크

```
ssh 6v6-ips sudo systemctl status suricata
ssh 6v6-ips sudo suricata --build-info | head -10
ssh 6v6-ips sudo tail -20 /var/log/suricata/eve.json
```

**검증 포인트**:
1. suricata.service Active
2. eve.json 에 최근 event_type 기록 존재 (alert, http, dns, flow 등)

### 실습 4 — web Apache + ModSecurity 헬스체크

```
ssh 6v6-web sudo apache2ctl -M | grep -iE 'security|proxy|ssl'
ssh 6v6-web cat /etc/modsecurity/modsecurity.conf | grep -E '^SecRuleEngine|^SecAuditLog'
ssh 6v6-web sudo tail -10 /var/log/apache2/modsec_audit.log
```

**검증 포인트**:
1. mod_security2 + mod_proxy + mod_ssl 로드
2. SecRuleEngine On
3. modsec_audit.log JSON 형식 출력

### 실습 5 — siem Wazuh manager 16 daemon

```
ssh 6v6-siem sudo /var/ossec/bin/wazuh-control status
# 출력: wazuh-analysisd, wazuh-remoted, wazuh-monitord, ... 16개 모두 running
ssh 6v6-siem sudo /var/ossec/bin/agent_control -l
# 출력: ID 001 fw / 002 ips / 003 web 모두 Active
```

**검증 포인트**:
1. 16 daemon 전부 running
2. Active agent 3대 (fw / ips / web)

### 실습 6 — portal 운영 대시보드

```
# 브라우저 http://portal.6v6.lab/
# 또는 학생 PC 셸에서:
curl -s -H 'Host: portal.6v6.lab' http://<VM_IP>/ | head -20
```

**검증 포인트**:
1. portal 메인 페이지 (HTMX 기반) 출력
2. 컨테이너 상태 위젯, Wazuh alert 위젯, Suricata flow 위젯 표시

---

## 7. 사례 분석 — 한국 사례 + 표준 인용

### 7.1 KISA 침해사고 대응 시나리오

KISA (보호나라) 의 "2024 침해사고 분석 보고서" 에 따르면 국내 사고의 67% 는 다음 패턴.

- L1 (방화벽): 정상 포트 (80/443) 허용 → 침해 막지 못함
- L2 (IDS): 시그니처 부재로 0-day 탐지 실패
- L3 (WAF): 룰 미튜닝 → false-positive 회피로 비활성화
- L4 (SIEM): 로그는 쌓였으나 분석 인력 부재로 alert fatigue

**6v6 가 본 사례에서 배우는 점**:
- 5종 솔루션을 모두 갖추되, **튜닝과 운영** 이 핵심 (W04–W11 에서 심화).
- alert fatigue 방지를 위해 W09 에서 Wazuh 룰 우선순위 (level 12+ alert 만 dashboard
  filter) 학습.

### 7.2 ISMS-P 통제 매핑

본 과목 15주가 ISMS-P (정보보호 및 개인정보보호 관리체계) 의 어떤 통제에 해당하는가?

| ISMS-P 통제 | 본 과목 주차 | 비고 |
|------------|--------------|------|
| 2.6 (네트워크 접근) | W02–W03 (nftables) | 방화벽 정책 |
| 2.6.4 (네트워크 침입탐지) | W04–W05 (Suricata) | IDS/IPS |
| 2.10.7 (보안위협 대응) | W06 (ModSec WAF) | 웹 응용 보안 |
| 2.5 (인증 및 권한관리) | W07 (osquery sudo log) | 사용자 행위 추적 |
| 2.9 (시스템 및 서비스 운영관리) | W09–W11 (Wazuh + sysmon) | 로그 관리 |
| 2.12 (보안위반 사고 대응) | W12–W14 (OpenCTI) | CTI 기반 사전 대응 |
| 종합 | W15 (기말) | APT 대응 1 사이클 |

### 7.3 NIST CSF (Cybersecurity Framework) 매핑

| NIST CSF Function | 6v6 솔루션 |
|--------------------|-----------|
| Identify           | osquery 자산·구성 인벤토리 (W07) |
| Protect            | nftables / ModSecurity (W02–W06) |
| Detect             | Suricata / Wazuh / sysmon (W04, W09–W11) |
| Respond            | Wazuh Active Response (W10) |
| Recover            | OpenCTI 기반 사후 분석 (W14) |

---

## 8. 과제 + 다음 주차 예고

### 8.1 과제 (1주차)

**A. 토폴로지 재현 (필수)**

A4 한 장에 6v6 의 16개 컨테이너 + 4-tier + 패킷 흐름 (학생 / 운영 트래픽 각 1개) 을 손으로
그려 제출. 다음 정보 포함:

- 컨테이너 이름·IP·역할
- ext / pipe / dmz / int 4 bridge 영역 표시
- HAProxy 의 4가지 backend 라우팅 (waf/dashboard/portal/bastion) 화살표
- 호스트 노출 포트 5개 (80/443/2204/2202/9100) 매핑

**B. 헬스체크 보고서 (필수)**

실습 1~6 의 출력을 모아서 1페이지 보고서. 다음 항목 포함:

- `ssh 6v6-bastion docker ps` 16건 출력 캡처
- `nft list table ip filter` 출력 캡처
- `wazuh-control status` 출력 캡처 (16 daemon running)
- `agent_control -l` 출력 캡처 (3 agent Active)
- 본인이 발견한 비정상 상태 / 의문점 1건 (없으면 "정상" + 근거)

**C. 사례 조사 (심화, 선택)**

KISA 보호나라에서 2025년 침해사고 1건 선택, 다음 분석:

- 해당 사고에서 L1–L4 중 어느 레이어가 무력화되었는가
- 6v6 의 어떤 솔루션이 사전에 탐지·차단할 수 있었는가
- 본인 답을 W02–W06 에서 다시 확인할 것

### 8.2 다음 주차 (W02) 예고

- **주제**: nftables 방화벽 (1) — 기초
- **실습 환경**: `6v6-fw` 단독
- **핵심 도구**: `nft`, `iptables-translate`, `tcpdump`
- **선수 학습 권장**:
  - nftables wiki 의 "Quick reference" 한 번 통독
  - tcpdump 의 BPF expression (`tcp port 80 and host 10.20.30.202` 같은) 1개 예제 실행

---

## 9. 평가 기준 (1주차)

| 항목 | 비중 | 평가 방법 |
|------|------|----------|
| 토폴로지 재현 (과제 A) | 30% | IP·라우팅 정확도 + 4-tier 분리 명확성 |
| 헬스체크 보고서 (과제 B) | 50% | 6개 실습 모두 통과 출력 첨부 + 의문점 분석 |
| 사례 조사 (과제 C) | 20% | KISA 사례 1건 + L1–L4 매핑 논리성 |

총점 100점 만점. 60점 미만은 재실습 후 재제출.

---

## 10. 핵심 정리

1. **Defense in Depth** 는 4 레이어 (Perimeter/Inline/Application/Host) 의 독립적 방어선
   으로 단일 우회를 막는 원리다.
2. **6v6 4-tier** (`ext → pipe → dmz → int`) 는 단일 VM 안에서 DiD 를 강제하는 토폴로지로,
   fw / ips 가 라우터로 동작한다.
3. **5종 보안 솔루션** 은 각각 다른 레이어에서 동작하며 (방화벽 L3/4, IPS L3/4 + payload,
   WAF L7 HTTP, SIEM 로그·행위, 호스트 가시화 OS 내부), 한 종류로는 충분치 않다.
4. **운영 트래픽과 학생 트래픽 분리** — HAProxy 의 host header ACL 로 운영 (siem/portal/
   bastion API) 은 WAF 우회, 학생 (취약 웹 8종) 은 WAF 경유.
5. **bastion ProxyJump** — 16개 컨테이너 전부 단일 SSH 진입점 + 비밀번호 `ccc`. 직접 접속
   금지 (attacker 제외).

다음 주부터 각 레이어를 한 솔루션씩 깊이 들어간다. W02 nftables 부터 시작.

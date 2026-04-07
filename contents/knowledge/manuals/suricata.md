# Suricata IDS/IPS 레퍼런스

## 개요

Suricata는 오픈소스 네트워크 위협 탐지 엔진으로, IDS(침입 탐지), IPS(침입 방지), NSM(네트워크 보안 모니터링) 기능을 제공한다. 멀티스레드 아키텍처로 높은 성능을 지원한다.

---

## 1. 설치 및 기본 설정

### 설치

```bash
# Ubuntu/Debian
apt install suricata suricata-update

# 버전 확인
suricata --build-info
suricata -V
```

### 핵심 설정 파일: suricata.yaml

경로: `/etc/suricata/suricata.yaml`

```yaml
# 홈 네트워크 정의
vars:
  address-groups:
    HOME_NET: "[10.20.30.0/24]"
    EXTERNAL_NET: "!$HOME_NET"
  port-groups:
    HTTP_PORTS: "80"
    SSH_PORTS: "22"

# 캡처 인터페이스
af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes

# 로그 출력 설정
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert:
            payload: yes
            payload-printable: yes
        - http:
            extended: yes
        - dns:
        - tls:
        - files:
        - smtp:
        - flow:

# IPS 모드 설정 (NFQ 사용)
# nfq:
#   mode: accept
#   repeat-mark: 1
#   repeat-mask: 1
```

### 실행 모드

```bash
# IDS 모드 (수동 모니터링)
suricata -c /etc/suricata/suricata.yaml -i eth0

# IPS 모드 (NFQ — nftables와 연동)
suricata -c /etc/suricata/suricata.yaml -q 0

# pcap 파일 분석
suricata -c /etc/suricata/suricata.yaml -r capture.pcap

# 데몬 모드
suricata -c /etc/suricata/suricata.yaml -i eth0 -D

# 설정 검증
suricata -T -c /etc/suricata/suricata.yaml
```

---

## 2. 룰 문법

### 기본 구조

```
action protocol src_ip src_port -> dst_ip dst_port (options;)
```

### 액션 (Action)

| 액션     | 설명                                    |
|----------|-----------------------------------------|
| `alert`  | 경고 생성 (IDS)                         |
| `drop`   | 패킷 폐기 + 경고 (IPS 모드)            |
| `reject` | 패킷 거부 (RST/ICMP unreachable 전송)  |
| `pass`   | 패킷 허용 (이후 룰 무시)               |

### 프로토콜

`tcp`, `udp`, `icmp`, `ip`, `http`, `dns`, `tls`, `ssh`, `ftp`, `smtp`, `smb`, `dhcp`

### 방향

```
->    단방향 (출발지 → 목적지)
<>    양방향
```

### 룰 예시

```
alert tcp $EXTERNAL_NET any -> $HOME_NET 22 (
  msg:"SSH Brute Force Attempt";
  flow:to_server,established;
  threshold:type both, track by_src, count 5, seconds 60;
  sid:1000001; rev:1;
  classtype:attempted-admin;
)
```

---

## 3. 주요 룰 옵션

### 메타 옵션

| 옵션         | 설명                          | 예시                              |
|--------------|-------------------------------|-----------------------------------|
| `msg`        | 경고 메시지                   | `msg:"SQL Injection";`           |
| `sid`        | 시그니처 ID (고유)            | `sid:1000001;`                   |
| `rev`        | 룰 리비전 번호                | `rev:3;`                         |
| `classtype`  | 분류                          | `classtype:web-application-attack;` |
| `priority`   | 우선순위 (1=높음)             | `priority:1;`                    |
| `reference`  | 외부 참조                     | `reference:cve,2024-1234;`       |
| `metadata`   | 추가 메타데이터               | `metadata:created_at 2024-01-01;` |

### 페이로드 탐지

| 옵션         | 설명                          | 예시                                |
|--------------|-------------------------------|-------------------------------------|
| `content`    | 바이트 패턴 매칭              | `content:"GET /admin";`            |
| `nocase`     | 대소문자 무시                 | `content:"select"; nocase;`        |
| `depth`      | 검색 범위 시작부터 N바이트    | `depth:50;`                        |
| `offset`     | 검색 시작 위치                | `offset:4;`                        |
| `distance`   | 이전 매칭 이후 거리           | `distance:0;`                      |
| `within`     | 이전 매칭 이후 범위 내        | `within:10;`                       |
| `pcre`       | 정규표현식                    | `pcre:"/union\s+select/i";`        |
| `byte_test`  | 바이트 비교                   | `byte_test:4,>,1000,0;`           |

### 흐름 옵션

| 옵션         | 설명                          |
|--------------|-------------------------------|
| `flow:to_server` | 클라이언트 → 서버 방향    |
| `flow:to_client` | 서버 → 클라이언트 방향    |
| `flow:established` | 연결 수립된 세션         |
| `flowbits`   | 세션 내 상태 플래그           |

### HTTP 키워드

```
http.method         HTTP 메서드 (GET, POST 등)
http.uri            요청 URI
http.header         HTTP 헤더 전체
http.host           Host 헤더
http.user_agent     User-Agent 헤더
http.request_body   요청 본문
http.response_body  응답 본문
http.stat_code      응답 상태 코드
```

### 임계값 (Threshold)

```
# 60초 내 5회 이상이면 1회 경고
threshold:type both, track by_src, count 5, seconds 60;

# 매 10번째 이벤트에 경고
threshold:type threshold, track by_src, count 10, seconds 60;

# 60초 내 1회만 경고 (반복 억제)
threshold:type limit, track by_src, count 1, seconds 60;
```

---

## 4. 룰 관리: suricata-update

```bash
# 룰 소스 목록 확인
suricata-update list-sources

# 기본 ET Open 룰 다운로드/업데이트
suricata-update

# 특정 소스 활성화
suricata-update enable-source et/open
suricata-update enable-source oisf/trafficid

# 룰 활성화/비활성화 파일
# /etc/suricata/enable.conf
# /etc/suricata/disable.conf

# 특정 SID 비활성화 (disable.conf)
echo "1:2024897" >> /etc/suricata/disable.conf

# 업데이트 후 Suricata 리로드
suricata-update
kill -USR2 $(pidof suricata)
```

### 로컬 룰 파일

```bash
# /etc/suricata/rules/local.rules 에 커스텀 룰 작성
# suricata.yaml에서 참조:
# rule-files:
#   - local.rules
```

---

## 5. 로그: eve.json

EVE(Extensible Event Format)는 Suricata의 JSON 기반 통합 로그이다.

### 경로

```
/var/log/suricata/eve.json
```

### 경고 로그 구조

```json
{
  "timestamp": "2024-12-15T10:30:45.123456+0900",
  "flow_id": 1234567890,
  "event_type": "alert",
  "src_ip": "192.168.1.100",
  "src_port": 54321,
  "dest_ip": "10.20.30.10",
  "dest_port": 80,
  "proto": "TCP",
  "alert": {
    "action": "allowed",
    "gid": 1,
    "signature_id": 1000001,
    "rev": 1,
    "signature": "Possible SQL Injection",
    "category": "Web Application Attack",
    "severity": 1
  },
  "payload_printable": "GET /search?q=1' OR '1'='1 HTTP/1.1",
  "http": {
    "hostname": "10.20.30.10",
    "url": "/search?q=1' OR '1'='1",
    "http_method": "GET",
    "status": 200
  }
}
```

### 로그 분석

```bash
# 경고만 필터
jq 'select(.event_type=="alert")' /var/log/suricata/eve.json

# 심각도 1 경고
jq 'select(.event_type=="alert" and .alert.severity==1)' /var/log/suricata/eve.json

# 특정 SID 필터
jq 'select(.alert.signature_id==1000001)' /var/log/suricata/eve.json

# 출발지 IP별 경고 수
jq -r 'select(.event_type=="alert") | .src_ip' /var/log/suricata/eve.json \
  | sort | uniq -c | sort -rn | head -20

# HTTP 요청 로그
jq 'select(.event_type=="http")' /var/log/suricata/eve.json

# DNS 쿼리 로그
jq 'select(.event_type=="dns")' /var/log/suricata/eve.json
```

---

## 6. IPS 모드 연동 (nftables + NFQ)

```bash
# nftables에서 NFQ로 패킷 전달
nft add rule inet filter forward \
  ip saddr 10.20.30.0/24 queue num 0

# suricata.yaml 설정
# nfq:
#   mode: repeat
#   repeat-mark: 1
#   repeat-mask: 1

# IPS 모드 실행
suricata -c /etc/suricata/suricata.yaml -q 0
```

---

## 7. 실습 예제

### 예제 1: SQL Injection 탐지

```
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS (
  msg:"CCC - SQL Injection Attempt (UNION SELECT)";
  flow:to_server,established;
  http.uri;
  content:"union"; nocase;
  content:"select"; nocase; distance:0; within:20;
  sid:2000001; rev:1;
  classtype:web-application-attack;
  priority:1;
)
```

### 예제 2: 웹쉘 업로드 탐지

```
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS (
  msg:"CCC - PHP Webshell Upload Detected";
  flow:to_server,established;
  http.method; content:"POST";
  http.request_body;
  content:"<?php"; nocase;
  pcre:"/(?:eval|exec|system|passthru|shell_exec)\s*\(/i";
  sid:2000002; rev:1;
  classtype:web-application-attack;
  priority:1;
)
```

### 예제 3: 내부 네트워크 포트 스캔 탐지

```
alert tcp $HOME_NET any -> $HOME_NET any (
  msg:"CCC - Internal Port Scan Detected";
  flow:to_server;
  flags:S,12;
  threshold:type both, track by_src, count 20, seconds 10;
  sid:2000003; rev:1;
  classtype:attempted-recon;
  priority:2;
)
```

### 예제 4: Reverse Shell 탐지

```
alert tcp $HOME_NET any -> $EXTERNAL_NET any (
  msg:"CCC - Possible Reverse Shell (bash)";
  flow:established;
  content:"/bin/bash"; nocase;
  pcre:"/\/bin\/(ba)?sh\s+-i/";
  sid:2000004; rev:1;
  classtype:trojan-activity;
  priority:1;
)
```

### 예제 5: DNS 터널링 탐지

```
alert dns any any -> any any (
  msg:"CCC - Suspicious Long DNS Query (possible tunneling)";
  dns.query;
  pcre:"/^[a-zA-Z0-9]{50,}\./";
  threshold:type both, track by_src, count 10, seconds 60;
  sid:2000005; rev:1;
  classtype:policy-violation;
  priority:2;
)
```

---

## 8. 운영 명령어

```bash
# Suricata 상태 확인
systemctl status suricata

# 설정 리로드 (재시작 없이)
kill -USR2 $(pidof suricata)

# 통계 확인
suricatasc -c uptime
suricatasc -c dump-counters

# 룰 카운트
grep -c "^alert\|^drop" /var/lib/suricata/rules/suricata.rules

# 로그 실시간 모니터링
tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'
```

---

## 참고

- 공식 문서: https://docs.suricata.io
- ET Open 룰셋: https://rules.emergingthreats.net
- Suricata 룰 작성 가이드: https://docs.suricata.io/en/latest/rules/

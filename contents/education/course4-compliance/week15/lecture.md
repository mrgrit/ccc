# Week 15: 기말고사 - 모의 인증 심사

## 학습 목표

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

## 용어 해설 (보안 표준/컴플라이언스 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **컴플라이언스** | Compliance | 법/규정/표준을 준수하는 것 | 교통법규 준수 |
| **인증** | Certification | 외부 심사 기관이 표준 준수를 확인하는 절차 | 운전면허 시험 합격 |
| **통제 항목** | Control | 보안 목표를 달성하기 위한 구체적 조치 | 건물 소방 설비 하나하나 |
| **SoA** | Statement of Applicability | 적용 가능한 통제 항목 선언서 | "우리 건물에 필요한 소방 설비 목록" |
| **리스크 평가** | Risk Assessment | 위험을 식별·분석·평가하는 과정 | 건물의 화재/지진 위험도 평가 |
| **리스크 처리** | Risk Treatment | 평가된 위험에 대한 대응 결정 (수용/회피/감소/전가) | 보험 가입, 소방 설비 설치 |
| **PDCA** | Plan-Do-Check-Act | ISO 표준의 지속적 개선 사이클 | 계획→실행→점검→개선 반복 |
| **ISMS** | Information Security Management System | 정보보안 관리 체계 | 회사의 보안 관리 시스템 전체 |
| **ISMS-P** | ISMS + Privacy | 한국의 정보보호 + 개인정보보호 인증 | 한국판 ISO 27001 + 개인정보 |
| **ISO 27001** | ISO/IEC 27001 | 국제 정보보안 관리체계 표준 | 국제 보안 면허증 |
| **ISO 27002** | ISO/IEC 27002 | ISO 27001의 통제 항목 상세 가이드 | 면허 시험 교재 |
| **NIST CSF** | NIST Cybersecurity Framework | 미국 국립표준기술연구소의 사이버보안 프레임워크 | 미국판 보안 가이드 |
| **GDPR** | General Data Protection Regulation | EU 개인정보보호 규정 | EU의 개인정보 보호법 |
| **SOC 2** | Service Organization Control 2 | 클라우드 서비스 보안 인증 (미국) | 클라우드 업체의 보안 성적표 |
| **증적** | Evidence (Audit) | 통제가 실행되었음을 증명하는 자료 | 출석부, 영수증 |
| **심사원** | Auditor | 인증 심사를 수행하는 전문가 | 감독관, 시험관 |
| **부적합** | Non-conformity | 심사에서 표준 미충족 판정 | 시험 불합격 항목 |
| **GAP 분석** | Gap Analysis | 현재 상태와 목표 기준의 차이 분석 | 현재 실력과 합격선의 차이 |

---

# Week 15: 기말고사 - 모의 인증 심사

## 시험 개요

- **유형**: 팀 실기 시험 (2~3인 1조)
- **시간**: 180분
- **배점**: 100점
- **역할**: 심사팀(1조) / 피심사 조직(1조)을 번갈아 수행
- **기준**: ISO 27001:2022 + ISMS-P 통합

---

## 시험 구성

| 파트 | 내용 | 배점 | 시간 |
|------|------|------|------|
| Part A | 심사 준비 (피심사 역할) | 30점 | 60분 |
| Part B | 모의 심사 실시 | 40점 | 80분 |
| Part C | 심사 보고서 작성 | 30점 | 40분 |

---

## Part A: 심사 준비 - 피심사 조직 역할 (30점)

### 과제

실습 환경 4개 서버에 대해 인증 심사를 받을 준비를 하시오.

### A-1. SoA 완성 (10점)

A.8 기술적 통제 34개 항목에 대한 적용성 보고서를 작성하시오.

> **실습 목적**: 기말고사로 4개 서버에 대한 모의 인증 심사를 수행하여 전체 과정을 종합 실습한다
>
> **배우는 것**: SoA 작성, 기술 점검, 증적 수집, 심사 보고서 작성까지 인증 심사 전 과정을 경험한다
>
> **결과 해석**: 각 통제 항목의 적합/부적합 판정과 증적이 보고서에 포함되면 모의 심사가 완료된 것이다
>
> **실전 활용**: ISO 27001/ISMS-P 인증 컨설턴트는 이 전 과정을 반복적으로 수행하는 것이 핵심 업무이다

```bash
# 점검을 위한 기본 정보 수집
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  # 서버별 사용자 매핑
  case $ip in 10.20.30.201) srv="opsclaw@$ip";; 10.20.30.1) srv="secu@$ip";; 10.20.30.80) srv="web@$ip";; 10.20.30.100) srv="siem@$ip";; esac
  echo "= $ip =========="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "   # 비밀번호 자동입력 SSH
    hostname
    echo '--- 서비스 ---'
    systemctl list-units --type=service --state=running --no-pager | wc -l  # 서비스 관리
    echo '--- 포트 ---'
    ss -tlnp 2>/dev/null | grep LISTEN | wc -l         # 소켓 상태: TCP/리스닝 포트
  " 2>/dev/null
done
```

### A-2. 증적 수집 (10점)

최소 10개 통제 항목에 대한 증적을 수집하시오.

```bash
# 증적 수집 가이드
EVIDENCE="/tmp/exam_evidence"
mkdir -p $EVIDENCE                                     # 디렉터리 생성

# [A.8.2] 특수접근권한 증적
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "   # 비밀번호 자동입력 SSH
    echo 'Server: $ip'
    echo 'PermitRootLogin:'
    grep PermitRootLogin /etc/ssh/sshd_config | grep -v '^#'  # 패턴 검색
    echo 'sudo users:'
    getent group sudo
  " 2>/dev/null >> $EVIDENCE/A8.2_evidence.txt
done

# [A.8.5] 보안인증 증적
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "   # 비밀번호 자동입력 SSH
    echo 'Server: $ip'
    grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS' /etc/login.defs | grep -v '^#'  # 패턴 검색
    echo 'MaxAuthTries:'
    grep MaxAuthTries /etc/ssh/sshd_config | grep -v '^#'  # 패턴 검색
  " 2>/dev/null >> $EVIDENCE/A8.5_evidence.txt
done

# [A.8.15] 로깅 증적
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "   # 비밀번호 자동입력 SSH
    echo 'Server: $ip'
    echo 'rsyslog:'
    systemctl is-active rsyslog                        # 서비스 관리
    echo 'log files:'
    ls -lh /var/log/syslog /var/log/auth.log 2>/dev/null
  " 2>/dev/null >> $EVIDENCE/A8.15_evidence.txt
done

# [A.8.16] 모니터링 증적
sshpass -p1 ssh siem@10.20.30.100 "                    # 비밀번호 자동입력 SSH
  echo 'Wazuh Manager:'
  systemctl is-active wazuh-manager                    # 서비스 관리
  echo 'Agent count:'
  /var/ossec/bin/agent_control -l 2>/dev/null | wc -l
  echo 'Recent alerts:'
  wc -l /var/ossec/logs/alerts/alerts.json             # 줄/단어/바이트 수 카운트
" 2>/dev/null > $EVIDENCE/A8.16_evidence.txt

# [A.8.20] 네트워크보안 증적
sshpass -p1 ssh secu@10.20.30.1 "                      # 비밀번호 자동입력 SSH
  echo 'Firewall rules:'
  sudo nft list ruleset                                # nftables 규칙 조회
  echo 'Suricata:'
  systemctl is-active suricata                         # 서비스 관리
" 2>/dev/null > $EVIDENCE/A8.20_evidence.txt

# [A.8.24] 암호화 증적
sshpass -p1 ssh siem@10.20.30.100 "                    # 비밀번호 자동입력 SSH
  echo 'TLS version:'
  echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol
" 2>/dev/null > $EVIDENCE/A8.24_evidence.txt

echo "=== 수집된 증적 ==="
ls -la $EVIDENCE/
```

### A-3. 심사 답변 준비 (10점)

다음 질문에 대한 답변을 준비하시오:

1. "정보보안 관리체계의 범위는 어디까지입니까?"
2. "리스크 평가 결과를 보여주십시오."
3. "접근통제 정책과 실제 구현이 일치합니까?"
4. "보안 사고 탐지 및 대응 체계를 설명해 주십시오."
5. "변경 관리 절차는 어떻게 운영됩니까?"
6. "패치 관리 현황을 보여주십시오."
7. "백업 및 복구 절차가 있습니까?"
8. "로그 보관 기간은 얼마입니까?"

---

## Part B: 모의 심사 실시 (40점)

### B-1. 심사팀 역할 (20점)

상대 조의 환경을 심사한다.

**심사 영역 (택 5개)**:

#### 영역 1: 접근통제 심사

```bash
# 심사 명령어
echo "=== 접근통제 심사 ==="

# 1. 사용자 계정 관리
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip: 계정 ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "awk -F: '\$3>=1000 && \$3<65534 {print \$1,\$3,\$7}' /etc/passwd"  # 비밀번호 자동입력 SSH
done

# 2. 권한 관리
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip: sudo ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "getent group sudo"  # 비밀번호 자동입력 SSH
done

# 3. SSH 설정
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip: SSH ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries|AllowUsers' /etc/ssh/sshd_config | grep -v '^#'"  # 비밀번호 자동입력 SSH
done
```

#### 영역 2: 로깅 및 모니터링 심사

```bash
echo "=== 로깅/모니터링 심사 ==="

# 1. 로그 서비스 동작 여부
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "systemctl is-active rsyslog auditd 2>/dev/null; ls -lh /var/log/auth.log /var/log/syslog 2>/dev/null"  # 비밀번호 자동입력 SSH
done

# 2. SIEM 통합 모니터링
sshpass -p1 ssh siem@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null"  # 비밀번호 자동입력 SSH
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | wc -l"  # 비밀번호 자동입력 SSH

# 3. 로그 보관 기간
sshpass -p1 ssh opsclaw@10.20.30.201 "cat /etc/logrotate.conf | grep -E 'rotate|weekly'"  # 비밀번호 자동입력 SSH
```

#### 영역 3: 네트워크 보안 심사

```bash
echo "=== 네트워크 보안 심사 ==="

# 방화벽 규칙
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null"  # 비밀번호 자동입력 SSH

# IPS 상태
sshpass -p1 ssh secu@10.20.30.1 "systemctl is-active suricata 2>/dev/null"  # 비밀번호 자동입력 SSH

# 열린 포트 (불필요 서비스)
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "ss -tlnp | grep LISTEN"  # 비밀번호 자동입력 SSH
done
```

#### 영역 4: 암호화 심사

```bash
echo "=== 암호화 심사 ==="

# TLS 버전
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep -E 'Protocol|Cipher'"

# SSH 알고리즘
sshpass -p1 ssh opsclaw@10.20.30.201 "grep -E 'Ciphers|MACs|KexAlgorithms' /etc/ssh/sshd_config | grep -v '^#'"

# 파일 권한
sshpass -p1 ssh opsclaw@10.20.30.201 "stat -c '%a %n' /etc/shadow /etc/ssh/ssh_host_*_key 2>/dev/null"
```

#### 영역 5: 사고 대응 심사

```bash
echo "=== 사고 대응 심사 ==="

# 탐지 체계
sshpass -p1 ssh siem@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null"  # 비밀번호 자동입력 SSH
sshpass -p1 ssh secu@10.20.30.1 "systemctl is-active suricata 2>/dev/null"  # 비밀번호 자동입력 SSH

# 격리/차단 능력
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep -c 'drop'"  # 비밀번호 자동입력 SSH

# 최근 고위험 이벤트 대응 기록
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 12:
            print(f'{a.get(\"timestamp\",\"\")} Level {r[\"level\"]}: {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -5"
```

### B-2. 피심사 조직 역할 (20점)

심사팀의 질문에 답변하고, 요청받은 증적을 즉시 제시한다.

**평가 기준**:
- 질문에 대한 정확한 답변 (5점)
- 증적의 즉시 제시 (5점)
- 기술적 설명의 정확성 (5점)
- 부적합 사항에 대한 인정과 개선 의지 (5점)

---

## Part C: 심사 보고서 작성 (30점)

### 보고서 양식

```
================================================================
모의 인증 심사 보고서
================================================================

1. 심사 개요
   - 심사일: 2026-XX-XX
   - 심사 기준: ISO 27001:2022, ISMS-P
   - 심사 범위: 서버 4대 (opsclaw, secu, web, siem)
   - 심사팀: (이름)
   - 피심사 조직: (팀명)

2. 심사 결과 요약
   | 구분 | 건수 |
   |------|------|
   | 중대 부적합 (Major) | ? |
   | 경미 부적합 (Minor) | ? |
   | 관찰 사항 (OFI) | ? |
   | 적합 | ? |

3. 상세 발견사항

   [부적합 NC-001]
   - 통제 항목: A.X.XX
   - 발견 내용: (구체적 기술)
   - 증거: (명령어 실행 결과)
   - 심각도: Major / Minor
   - 권고 조치: (구체적 개선 방안)

   [부적합 NC-002]
   ...

   [관찰사항 OFI-001]
   ...

4. 영역별 평가

   | 영역 | 점검 항목 수 | 적합 | 부적합 | 평가 |
   |------|------------|------|--------|------|
   | 접근통제 | ? | ? | ? | 양호/미흡 |
   | 로깅 | ? | ? | ? | 양호/미흡 |
   | 네트워크 | ? | ? | ? | 양호/미흡 |
   | 암호화 | ? | ? | ? | 양호/미흡 |
   | 사고대응 | ? | ? | ? | 양호/미흡 |

5. 종합 의견
   (인증 가능/조건부 인증/인증 불가 판정과 사유)

6. 시정 조치 계획 (피심사 조직 작성)
   | NC 번호 | 시정 조치 | 담당 | 완료 예정일 |
   |---------|----------|------|-----------|
   | NC-001 | ... | ... | ... |
================================================================
```

---

## 채점 기준

### Part A: 심사 준비 (30점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| SoA 완성도 | 34개 항목 전체, 사유 충분 | 20개 이상 | 20개 미만 |
| 증적 수집 | 10개 이상 항목, 해시 포함 | 7개 이상 | 7개 미만 |
| 답변 준비 | 8개 질문 모두 준비 | 5개 이상 | 5개 미만 |

### Part B: 모의 심사 (40점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| 심사 수행 | 5개 영역, 적절한 질문 | 3개 영역 | 2개 이하 |
| 발견사항 도출 | 정확한 부적합 도출 | 일부 정확 | 부정확 |
| 피심사 대응 | 즉시 증적 제시, 정확한 답변 | 부분적 | 미흡 |

### Part C: 보고서 (30점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| 구조 | 양식 완비 | 일부 누락 | 구조 미흡 |
| 정확성 | 증거 기반 판정 | 일부 주관적 | 근거 없음 |
| 실용성 | 구체적 시정조치 제시 | 추상적 | 미제시 |

---

## 시험 전 체크리스트

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 서버 접속 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 $srv "hostname" 2>/dev/null \
    && echo "$ip: OK" || echo "$ip: FAIL"
done

# Wazuh 상태 확인
sshpass -p1 ssh siem@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null"  # 비밀번호 자동입력 SSH
```

---

## 참고

- 오픈 북 시험: Week 02~14 강의 자료, 인터넷 검색 가능
- 팀 구성: 수업 시작 시 발표
- 제출물: 심사 보고서 (md 또는 txt 파일)
- 이 시험은 학기 전체 내용을 종합하는 실전 연습이다

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 내용을 점검한다. 이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** ISO 27001 Annex A의 통제 항목 수(2022 개정)는?
- (a) 114개  (b) **93개**  (c) 42개  (d) 14개

**Q2.** PDCA에서 'Check' 단계에 해당하는 활동은?
- (a) 정책 수립  (b) **내부 감사 및 모니터링**  (c) 통제 구현  (d) 부적합 시정

**Q3.** ISMS-P와 ISO 27001의 가장 큰 차이는?
- (a) ISO가 더 쉬움  (b) **ISMS-P는 개인정보보호를 포함**  (c) ISMS-P는 국제 표준  (d) 차이 없음

**Q4.** 리스크 처리에서 '보험 가입'은 어떤 옵션인가?
- (a) 감소(Mitigate)  (b) **전가(Transfer)**  (c) 회피(Avoid)  (d) 수용(Accept)

**Q5.** 심사에서 '부적합(Non-conformity)'이 발견되면?
- (a) 인증 즉시 취소  (b) **시정 조치 계획을 수립하고 기한 내 이행**  (c) 벌금 부과  (d) 재심사 없음

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): PASS_MAX_DAYS=99999, pam_pwquality, auditd, SSH 설정, nftables 점검

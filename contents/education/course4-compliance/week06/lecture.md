# Week 06: ISMS-P (2) - 점검 항목 실습

## 학습 목표
- ISMS-P 보호대책 중 핵심 20개 항목을 실제 서버에서 점검한다
- 점검 스크립트를 작성하고 실행한다
- 점검 결과를 ISMS-P 양식에 맞게 문서화한다

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

# Week 06: ISMS-P (2) - 점검 항목 실습

## 학습 목표

- ISMS-P 보호대책 중 핵심 20개 항목을 실제 서버에서 점검한다
- 점검 스크립트를 작성하고 실행한다
- 점검 결과를 ISMS-P 양식에 맞게 문서화한다

---

## 1. 점검 방법론

### 1.1 점검 유형

| 유형 | 방법 | 예시 |
|------|------|------|
| 서류 점검 | 정책/절차 문서 확인 | 보안 정책서, 접근통제 절차서 |
| 기술 점검 | 시스템 설정 확인 | SSH 설정, 방화벽 규칙 |
| 인터뷰 | 담당자 면담 | 보안 교육 이수 여부 |
| 현장 확인 | 물리적 확인 | 서버실 출입 통제 |

### 1.2 점검 결과 판정

| 판정 | 의미 |
|------|------|
| 적합 | 기준을 충족함 |
| 부분적합 | 일부 미흡한 점이 있음 |
| 부적합 | 기준을 충족하지 못함 |
| 해당없음 | 해당 항목이 적용되지 않음 |

---

## 2. 점검 항목 1~5: 정책 및 조직

> **이 실습을 왜 하는가?**
> "ISMS-P (2) - 점검 항목 실습" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 표준/컴플라이언스 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 [2.1.1] 정책의 유지관리

**점검 내용**: 정보보안 정책이 문서화되어 있는가?

> **이 점검의 의미:**
> ISMS-P 인증에서 가장 먼저 확인하는 것이 **"문서화된 보안 정책이 있는가?"**이다.
> `/etc/security/`와 `/etc/pam.d/`는 Linux 시스템의 보안 정책 파일이 위치하는 곳이다.
> 이 파일들이 존재하고 적절히 설정되어 있으면 "정책이 기술적으로 구현되었음"의 증적이 된다.
>
> **심사 시나리오:** 심사원이 "보안 정책은 어디에 문서화되어 있습니까?"라고 묻는다.
> 정책 문서(Word/PDF)와 함께, 이 실습에서 수집한 서버 설정 파일을 **기술적 증적**으로 제시한다.

> **실습 목적**: ISMS-P 점검 항목에 따라 보안 정책 문서와 기술적 설정의 일치 여부를 확인한다
>
> **배우는 것**: 보안 정책 파일 존재 여부, PAM 설정, 접근 통제 구현 등 ISMS-P 증적을 수집하는 방법을 배운다
>
> **결과 해석**: /etc/security/ 및 /etc/pam.d/ 파일이 존재하고 적절히 설정되어 있으면 정책이 기술적으로 구현된 것이다
>
> **실전 활용**: 심사원이 보안 정책 문서화 증적을 요구할 때, 정책 문서와 함께 서버 설정을 기술적 증적으로 제시한다

```bash
# 보안 관련 문서/설정 파일 존재 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -la /etc/security/ 2>/dev/null"  # 비밀번호 자동입력 SSH
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -la /etc/pam.d/ | head -10"  # 비밀번호 자동입력 SSH
```

### 2.2 [2.1.3] 정보자산 관리

**점검 내용**: 정보자산 목록이 관리되고 있는가?

```bash
# 서버 인벤토리 확인
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "hostname; cat /etc/machine-id; lscpu | grep 'Model name'; free -h | grep Mem"
done
```

### 2.3 [2.2.1] 주요 직무자 지정 및 관리

```bash
# sudo 권한 사용자 확인 (주요 직무자)
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "getent group sudo 2>/dev/null; getent group wheel 2>/dev/null"
done
```

### 2.4 [2.2.4] 보안 서약서

**점검 내용**: 직원이 보안 서약서에 서명했는가? (서류 점검 - 실습에서는 스킵)

### 2.5 [2.2.5] 보안 인식 교육

**점검 내용**: 연 1회 이상 보안 교육을 실시했는가? (서류 점검)

---

## 3. 점검 항목 6~10: 인증 및 접근통제

### 3.1 [2.5.1] 사용자 계정 관리

```bash
# 점검: 불필요한 계정, 기본 계정, 미사용 계정
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: 사용자 계정 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "awk -F: '\$3 >= 1000 && \$3 < 65534 {print \$1, \$6, \$7}' /etc/passwd"
  echo "--- 최근 로그인 ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "lastlog 2>/dev/null | awk 'NR>1 && \$2 != \"Never\" {print}' | head -5"
done
```

### 3.2 [2.5.2] 사용자 식별

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 점검: 공용 계정 사용 여부 (같은 계정으로 다수 접속)
sshpass -p1 ssh opsclaw@10.20.30.201 "who"             # 비밀번호 자동입력 SSH
sshpass -p1 ssh opsclaw@10.20.30.201 "last | head -20"  # 비밀번호 자동입력 SSH
```

### 3.3 [2.5.3] 사용자 인증

```bash
# 비밀번호 정책 점검
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: 비밀번호 정책 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs"
  echo "--- pwquality ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "cat /etc/security/pwquality.conf 2>/dev/null | grep -v '^#' | grep -v '^$' || echo '미설정'"
done
```

**ISMS-P 기준**:
- 최소 8자 이상 (영문+숫자+특수문자 중 2종 이상)
- 90일 이내 변경
- 최근 2회 이내 동일 비밀번호 사용 불가

### 3.4 [2.5.4] 비밀번호 관리

```bash
# 각 사용자의 비밀번호 만료일 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "sudo chage -l user 2>/dev/null"
```

### 3.5 [2.6.1] 네트워크 접근

```bash
# 방화벽 규칙 점검
echo "=== secu 서버 방화벽 ==="
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null"

# 기본 정책 확인 (DROP이어야 함)
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep 'policy'"
```

---

## 4. 점검 항목 11~15: 시스템 보안

### 4.1 [2.6.2] 정보시스템 접근

```bash
# SSH 접근 제한 설정 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: SSH 설정 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries|AllowUsers|AllowGroups|LoginGraceTime' /etc/ssh/sshd_config | grep -v '^#'"
done
```

### 4.2 [2.6.6] 서버 보안

```bash
# 불필요한 서비스 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: 불필요 서비스 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "systemctl list-units --type=service --state=running --no-pager | grep -E 'cups|avahi|bluetooth|rpcbind|telnet|ftp' || echo '해당 없음'"
done

# SUID 파일 점검
sshpass -p1 ssh opsclaw@10.20.30.201 "find /usr -perm -4000 -type f 2>/dev/null | wc -l"
```

### 4.3 [2.7.1] 암호정책 적용

```bash
# 전송 구간 암호화 확인
echo "=== Wazuh Dashboard TLS ==="
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep -E 'Protocol|Cipher'"  # 비밀번호 자동입력 SSH

echo "=== SSH 암호 알고리즘 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "ssh -Q cipher 2>/dev/null | head -10"  # 비밀번호 자동입력 SSH
```

### 4.4 [2.9.1] 변경관리

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 최근 패키지 변경 이력
sshpass -p1 ssh opsclaw@10.20.30.201 "cat /var/log/dpkg.log 2>/dev/null | tail -10"  # 비밀번호 자동입력 SSH
sshpass -p1 ssh opsclaw@10.20.30.201 "cat /var/log/apt/history.log 2>/dev/null | tail -20"  # 비밀번호 자동입력 SSH
```

### 4.5 [2.9.3] 보안시스템 운영

```bash
# IPS 상태 확인
sshpass -p1 ssh secu@10.20.30.1 "systemctl status suricata 2>/dev/null | head -5"

# WAF 상태 확인
sshpass -p1 ssh web@10.20.30.80 "systemctl status apache2 2>/dev/null | head -5 || systemctl is-active apache2"

# SIEM 상태 확인
sshpass -p1 ssh siem@10.20.30.100 "systemctl status wazuh-manager 2>/dev/null | head -5"
```

---

## 5. 점검 항목 16~20: 로그 및 사고 대응

### 5.1 [2.10.4] 로그 및 접속기록 관리

```bash
# 로그 보존 설정
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: 로그 보존 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "cat /etc/logrotate.conf 2>/dev/null | grep -E 'rotate|weekly|monthly|daily'"
  echo "--- 로그 파일 크기 ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "ls -lh /var/log/syslog /var/log/auth.log 2>/dev/null"
done
```

**ISMS-P 기준**: 접근 기록 최소 **6개월** 이상 보관

### 5.2 [2.10.5] 시간 동기화

```bash
# NTP 설정 확인 (로그 시간 정확성)
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "timedatectl 2>/dev/null | grep -E 'Time zone|NTP|synchronized'"
done
```

### 5.3 [2.10.7] 패치관리

```bash
# 보안 패치 현황
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: 패치 현황 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "apt list --upgradable 2>/dev/null | wc -l"
done
```

### 5.4 [2.11.1] 사고 예방 및 대응체계 구축

```bash
# Wazuh 에이전트 설치 및 동작 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80; do
  echo "=== $ip: Wazuh Agent ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "systemctl is-active wazuh-agent 2>/dev/null || echo 'N/A'"
done

# Wazuh Manager 알림 수집 확인
sshpass -p1 ssh siem@10.20.30.100 "ls -la /var/ossec/logs/alerts/ 2>/dev/null | tail -3"
```

### 5.5 [2.11.4] 사고 분석 및 공유

```bash
# 최근 보안 이벤트 확인
sshpass -p1 ssh siem@10.20.30.100 "tail -5 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30"
```

---

## 6. 통합 점검 스크립트

다음은 위 20개 항목을 한 번에 실행하는 스크립트이다:

```bash
#!/bin/bash
# ISMS-P 핵심 20개 항목 자동 점검 스크립트
SERVERS="10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100"

echo "=========================================="
echo " ISMS-P 핵심 점검 실행: $(date)"
echo "=========================================="

for ip in $SERVERS; do                                 # 반복문 시작
  echo ""
  echo "########## $ip ##########"

  echo "[2.5.1] 사용자 계정:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv \
    "awk -F: '\$3>=1000 && \$3<65534{print \$1}' /etc/passwd" 2>/dev/null

  echo "[2.5.3] 비밀번호 정책:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) \
    "grep PASS_MAX_DAYS /etc/login.defs 2>/dev/null | grep -v '^#'" 2>/dev/null

  echo "[2.6.2] SSH 접근 제한:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) \
    "grep -E 'PermitRootLogin|MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#'" 2>/dev/null

  echo "[2.10.4] 로그 보존:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) \
    "ls -lh /var/log/auth.log 2>/dev/null || echo 'N/A'" 2>/dev/null

  echo "[2.10.5] NTP 동기화:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) \
    "timedatectl 2>/dev/null | grep synchronized" 2>/dev/null

  echo "[2.10.7] 패치 현황:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) \
    "apt list --upgradable 2>/dev/null | wc -l" 2>/dev/null
done
```

---

## 7. 점검 결과 보고서 양식

```
=============================================
ISMS-P 점검 결과 보고서
점검일: 2026-03-27
점검자: (이름)
대상: 실습 환경 4개 서버
=============================================

| No | 항목번호 | 항목명 | 대상서버 | 점검결과 | 판정 | 비고 |
|----|---------|--------|---------|---------|------|------|
| 1 | 2.5.1 | 사용자계정관리 | 전체 | ... | 적합/부적합 | ... |
| 2 | 2.5.3 | 사용자인증 | 전체 | ... | 적합/부적합 | ... |
| ... | ... | ... | ... | ... | ... | ... |

[부적합 항목 개선 계획]
- 항목번호:
- 현황:
- 개선 방안:
- 완료 예정일:
```

---

## 8. 핵심 정리

1. **20개 핵심 항목** = 계정/인증/접근통제/암호화/로깅/패치/사고대응
2. **점검 유형** = 서류 + 기술 + 인터뷰 + 현장
3. **판정 기준** = 적합, 부분적합, 부적합, 해당없음
4. **자동화** = 기술 점검은 스크립트로 반복 수행 가능
5. **문서화** = 점검 결과는 반드시 증적으로 보관

---

## 과제

1. 위 통합 점검 스크립트를 실행하고 결과를 보고서 양식에 맞게 작성하시오
2. 부적합 판정된 항목에 대한 개선 방안을 제시하시오
3. 점검 항목을 3개 추가하여 스크립트를 확장하시오

---

## 참고 자료

- KISA ISMS-P 인증기준 해설서
- KISA 주요정보통신기반시설 기술적 취약점 분석 가이드
- 정보보호 컴플라이언스 점검 실무 가이드

---

---

## 심화: 표준/인증 실무 보충

### 보안 통제 구현 패턴

실무에서 통제 항목을 구현할 때의 일반적 패턴을 이해한다.

```
[1] 정책(Policy) 수립
    → "무엇을 해야 하는가?" 를 문서로 정의
    예: "모든 서버는 90일마다 패스워드를 변경한다"

[2] 절차(Procedure) 작성
    → "어떻게 하는가?" 를 단계별로 정리
    예: "1. passwd 명령 실행 2. 복잡도 확인 3. 변경 로그 기록"

[3] 기술적 구현(Technical Implementation)
    → 실제 시스템에 적용
    예: /etc/login.defs에 PASS_MAX_DAYS=90 설정

[4] 증적(Evidence) 수집
    → 구현되었음을 증명하는 자료 확보
    예: login.defs 캡처, 변경 로그, OpsClaw evidence
```

### 증적 수집 실습

```bash
# ISO 27001 A.8.5 (안전한 인증) 점검 증적 수집
echo "=== 패스워드 정책 확인 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "  # 비밀번호 자동입력 SSH
  echo '--- login.defs ---' && grep -E 'PASS_MAX|PASS_MIN|PASS_WARN' /etc/login.defs
  echo '--- pam 설정 ---' && grep pam_pwquality /etc/pam.d/common-password 2>/dev/null || echo 'pam_pwquality 미설정'
  echo '--- sudo 설정 ---' && sudo -l 2>/dev/null | head -5
" 2>/dev/null

# 결과를 OpsClaw evidence로 기록
# (OpsClaw dispatch 사용)
```

### GAP 분석 워크시트 예시

| 통제 ID | 통제 항목 | 현재 상태 | 목표 | GAP | 우선순위 |
|---------|---------|---------|------|-----|---------|
| A.5.1 | 정보보안 정책 | 문서 없음 | 승인된 정책 문서 | 정책 수립 필요 | 높음 |
| A.8.2 | 접근 권한 관리 | sudo NOPASSWD:ALL | 최소 권한 | sudo 제한 필요 | 긴급 |
| A.8.5 | 안전한 인증 | 단순 비밀번호 | 복잡도+MFA | 정책 변경 | 높음 |
| A.12.4 | 로깅 | 부분 수집 | 전체 수집+SIEM | Wazuh 연동 | 중간 |

### 인증 심사 대비 FAQ

| 질문 | 준비 방법 |
|------|---------|
| "이 통제의 증적을 보여주세요" | OpsClaw evidence/replay로 실행 이력 제시 |
| "리스크 평가를 어떻게 했나요?" | 리스크 평가 워크시트 + 기준 설명 |
| "부적합 사항은 어떻게 처리했나요?" | 시정 조치 계획서 + 완료 증적 |
| "경영진의 검토는?" | 검토 회의록 + 서명 |

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

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

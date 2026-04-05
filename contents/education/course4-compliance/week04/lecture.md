# Week 04: ISO 27001 (3) - 기술 통제 실습

## 학습 목표
- ISO 27001 A.8 기술적 통제를 실제 서버에서 점검할 수 있다
- 접근 통제, 암호화, 네트워크 보안 설정을 확인하고 평가한다
- 점검 결과를 통제 항목 기준으로 문서화한다

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

# Week 04: ISO 27001 (3) - 기술 통제 실습

## 학습 목표

- ISO 27001 A.8 기술적 통제를 실제 서버에서 점검할 수 있다
- 접근 통제, 암호화, 네트워크 보안 설정을 확인하고 평가한다
- 점검 결과를 통제 항목 기준으로 문서화한다

---

## 1. 실습 환경 구성 확인

> **이 실습을 왜 하는가?**
> ISO 27001 A.8(기술적 통제) 34개 항목을 **실제 서버에서 직접 점검**하는 경험은
> 컴플라이언스 실무의 핵심이다. 문서로만 배우면 "패스워드 정책을 설정하라"는 것이
> 실제로 어떤 파일의 어떤 설정인지 알 수 없다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - `/etc/login.defs`의 PASS_MAX_DAYS가 실제로 99999(미설정)인 것 발견
> - SSH PasswordAuthentication이 주석 처리된 상태 발견
> - sudo NOPASSWD:ALL이 설정된 서버 발견
> - 이 모든 것이 ISO 27001 **부적합(Non-conformity)** 사항
>
> **실무 시나리오:**
> 인증 심사원이 "A.8.5 안전한 인증: 패스워드 정책을 보여주세요"라고 요청하면,
> 터미널에서 `grep PASS_MAX /etc/login.defs`를 실행하여 증적을 제시한다.
> PASS_MAX_DAYS=90이면 적합, 99999이면 부적합으로 심사원이 판정한다.
>
> **검증 완료:** web 서버에서 PASS_MAX_DAYS=99999, pam_pwquality 설정, auditd active 확인

### 1.1 서버 접속 테스트

> **실습 목적**: ISO 27001 기술 통제(A.8) 항목을 실제 서버에서 점검하여 적합/부적합을 판정한다
>
> **배우는 것**: 패스워드 정책, 감사 로그, 접근 통제 등 기술 통제를 서버에서 직접 확인하고 증적을 수집한다
>
> **결과 해석**: 각 통제 항목의 설정값이 기준에 부합하면 적합, 미설정이거나 기준 미달이면 부적합이다
>
> **실전 활용**: 인증 심사에서 심사원이 터미널 앞에서 직접 확인을 요청하는 항목들이다

```bash
# 모든 서버 접속 확인
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do  # 반복문 시작
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "hostname" 2>/dev/null || echo "접속 실패"  # 비밀번호 자동입력 SSH
done
```

### 1.2 서버별 역할 확인

| 서버 | IP | 점검 대상 서비스 |
|------|----|-----------------|
| opsclaw | 10.20.30.201 | Manager API, PostgreSQL, SubAgent |
| secu | 10.20.30.1 | nftables 방화벽, Suricata IPS |
| web | 10.20.30.80 | Apache+ModSecurity WAF, JuiceShop |
| siem | 10.20.30.100 | Wazuh Dashboard, OpenCTI |

---

## 2. A.8.1 사용자 단말 장치 (User Endpoint Devices)

서버에 접근하는 단말의 보안 설정을 확인한다.

```bash
# 자동 로그아웃 설정 확인 (TMOUT)
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep TMOUT /etc/profile /etc/bash.bashrc /etc/environment 2>/dev/null || echo 'TMOUT 미설정'"
done
```

**점검 기준**: 서버의 TMOUT이 설정되어 있지 않으면 미준수. 권장값은 300~900초이다.

---

## 3. A.8.2 특수 접근 권한 (Privileged Access Rights)

### 3.1 sudo 권한 점검

```bash
# 각 서버의 sudo 사용자 확인
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "getent group sudo 2>/dev/null; getent group wheel 2>/dev/null"
done
```

### 3.2 root 직접 로그인 차단 확인

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do  # 반복문 시작
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep '^PermitRootLogin' /etc/ssh/sshd_config || echo '기본값 사용 중'"
done
```

**점검 기준**: PermitRootLogin이 `no`여야 준수. `yes`나 `prohibit-password`는 부분 준수.

### 3.3 SUID/SGID 파일 점검

```bash
# SUID 비트가 설정된 파일 확인 (권한 상승 위험)
sshpass -p1 ssh opsclaw@10.20.30.201 "find /usr -perm -4000 -type f 2>/dev/null"
```

---

## 4. A.8.5 보안 인증 (Secure Authentication)

### 4.1 비밀번호 정책 확인

```bash
# 비밀번호 복잡도 정책
sshpass -p1 ssh opsclaw@10.20.30.201 "cat /etc/security/pwquality.conf 2>/dev/null | grep -v '^#' | grep -v '^$' || echo 'pwquality 미설정'"

# 비밀번호 만료 기본 정책
sshpass -p1 ssh opsclaw@10.20.30.201 "grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs"
```

### 4.2 SSH 인증 방식 점검

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do  # 반복문 시작
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep -E 'PasswordAuthentication|PubkeyAuthentication|MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#'"
done
```

**점검 기준**:
- PubkeyAuthentication yes (권장)
- PasswordAuthentication no (키 기반 인증만 허용이 이상적)
- MaxAuthTries 3~5 (무차별 대입 방지)

### 4.3 로그인 실패 잠금 설정

원격 서버에 접속하여 명령을 실행합니다.

```bash
# PAM 기반 계정 잠금 설정 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "grep pam_faillock /etc/pam.d/common-auth 2>/dev/null || echo 'faillock 미설정'"  # 비밀번호 자동입력 SSH
sshpass -p1 ssh opsclaw@10.20.30.201 "grep pam_tally /etc/pam.d/common-auth 2>/dev/null || echo 'tally 미설정'"  # 비밀번호 자동입력 SSH
```

---

## 5. A.8.9 설정 관리 (Configuration Management)

### 5.1 불필요한 서비스 확인

```bash
# 실행 중인 서비스 중 불필요한 것이 있는지 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "systemctl list-units --type=service --state=running --no-pager | grep -E 'cups|avahi|bluetooth|rpcbind'"
```

### 5.2 커널 보안 파라미터 확인

```bash
sshpass -p1 ssh opsclaw@10.20.30.201 "sysctl net.ipv4.ip_forward net.ipv4.conf.all.accept_redirects net.ipv4.conf.all.accept_source_route net.ipv4.conf.all.log_martians 2>/dev/null"
```

**권장 설정**:
- `ip_forward = 0` (라우터가 아닌 경우)
- `accept_redirects = 0` (ICMP 리다이렉트 차단)
- `accept_source_route = 0` (소스 라우팅 차단)
- `log_martians = 1` (비정상 패킷 로깅)

---

## 6. A.8.15 로깅 (Logging)

### 6.1 로그 설정 확인

```bash
# rsyslog 설정 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "cat /etc/rsyslog.conf | grep -v '^#' | grep -v '^$' | head -20"

# 주요 로그 파일 존재 및 크기 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -lh /var/log/syslog /var/log/auth.log /var/log/kern.log 2>/dev/null"
```

### 6.2 감사 로그 (auditd) 확인

```bash
# auditd 설치 및 실행 여부
sshpass -p1 ssh opsclaw@10.20.30.201 "systemctl status auditd 2>/dev/null | head -5 || echo 'auditd 미설치'"

# audit 규칙 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "sudo auditctl -l 2>/dev/null || echo 'audit 규칙 없음'"
```

### 6.3 Wazuh 에이전트 로그 수집 확인

```bash
# Wazuh 에이전트 상태
for ip in 10.20.30.201 10.20.30.1 10.20.30.80; do
  echo "=== $ip ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "systemctl status wazuh-agent 2>/dev/null | grep Active || echo 'Wazuh Agent 미설치'"
done
```

---

## 7. A.8.20 네트워크 보안 (Networks Security)

### 7.1 방화벽 규칙 점검

```bash
# secu 서버의 nftables 규칙 확인
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset"
```

### 7.2 열린 포트 점검

```bash
# 각 서버에서 열려 있는 포트 확인
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "ss -tlnp 2>/dev/null | grep LISTEN"
done
```

**점검 기준**: 서비스에 필요하지 않은 포트가 열려 있으면 미준수.

### 7.3 네트워크 분리 확인

```bash
# secu 서버의 네트워크 인터페이스 확인 (DMZ 분리)
sshpass -p1 ssh secu@10.20.30.1 "ip addr show | grep 'inet '"
```

---

## 8. A.8.24 암호화 사용 (Use of Cryptography)

### 8.1 TLS 설정 확인

```bash
# Wazuh 대시보드 TLS 확인
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | head -20"

# TLS 버전 확인 (TLS 1.2 이상이어야 함)
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep 'Protocol'"
```

### 8.2 SSH 암호화 알고리즘 확인

```bash
sshpass -p1 ssh opsclaw@10.20.30.201 "grep -E 'Ciphers|MACs|KexAlgorithms' /etc/ssh/sshd_config | grep -v '^#'"
```

### 8.3 디스크 암호화 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh opsclaw@10.20.30.201 "lsblk -o NAME,FSTYPE,MOUNTPOINT | head -10"  # 비밀번호 자동입력 SSH
sshpass -p1 ssh opsclaw@10.20.30.201 "dmsetup status 2>/dev/null | head -5 || echo 'dm-crypt 미사용'"  # 비밀번호 자동입력 SSH
```

---

## 9. 점검 결과 문서화

### 9.1 점검 결과 템플릿

다음 형식으로 결과를 정리한다:

```
| 통제 항목 | 점검 대상 | 기대 결과 | 실제 결과 | 적합 여부 | 조치 사항 |
|-----------|----------|----------|----------|----------|----------|
| A.8.2 특수접근권한 | opsclaw SSH | PermitRootLogin no | ? | ? | ? |
| A.8.5 보안인증 | opsclaw SSH | MaxAuthTries 5 | ? | ? | ? |
| A.8.15 로깅 | opsclaw auditd | active 상태 | ? | ? | ? |
| A.8.20 네트워크 | secu nftables | 정책 존재 | ? | ? | ? |
| A.8.24 암호화 | siem TLS | TLS 1.2+ | ? | ? | ? |
```

---

## 10. 핵심 정리

1. **기술적 통제 점검** = 실제 서버 설정을 ISO 27001 기준으로 확인하는 것
2. **접근 통제**: SSH 설정, sudo 권한, 비밀번호 정책
3. **로깅**: rsyslog, auditd, Wazuh 에이전트
4. **네트워크**: 방화벽 규칙, 열린 포트, 네트워크 분리
5. **암호화**: TLS 버전, SSH 알고리즘, 디스크 암호화

---

## 과제

1. 4개 서버 모두에 대해 위 점검 항목을 수행하고 결과를 표로 작성하시오
2. 미준수 항목에 대한 개선 방안을 제시하시오
3. 자동 점검 스크립트를 작성하시오 (선택)

---

## 참고 자료

- CIS Benchmarks for Ubuntu Linux
- KISA 서버 보안 가이드
- SSH Hardening Guide (ssh-audit 도구)

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

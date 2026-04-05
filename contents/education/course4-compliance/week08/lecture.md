# Week 08: 중간고사 - ISO 27001 기반 보안 점검 체크리스트

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

# Week 08: 중간고사 - ISO 27001 기반 보안 점검 체크리스트

## 시험 개요

- **유형**: 실기 시험 (실습 환경 점검 + 보고서 작성)
- **시간**: 120분
- **배점**: 100점
- **범위**: ISO 27001 Annex A 기술적 통제 중심

---

## 시험 구성

| 파트 | 내용 | 배점 |
|------|------|------|
| Part A | 보안 점검 체크리스트 작성 | 20점 |
| Part B | 4개 서버 기술 점검 실행 | 40점 |
| Part C | 점검 결과 분석 및 보고서 작성 | 30점 |
| Part D | 개선 방안 제시 | 10점 |

---

## Part A: 보안 점검 체크리스트 작성 (20점)

### 과제

ISO 27001:2022 Annex A 기술적 통제(A.8)를 기반으로, 우리 실습 환경에 적합한 **보안 점검 체크리스트**를 작성하시오.

### 요구사항

최소 15개 항목을 포함하며, 각 항목에 다음을 명시하시오:

| 필드 | 설명 |
|------|------|
| 항목 번호 | ISO 27001 통제 번호 (예: A.8.5) |
| 항목명 | 점검 내용 요약 |
| 점검 명령 | 실제 실행할 Linux 명령어 |
| 기대 결과 | 적합 판정 기준 |
| 대상 서버 | 해당 서버 IP |

### 템플릿

```
| No | 통제번호 | 항목명 | 점검 명령 | 기대 결과 | 대상서버 |
|----|---------|--------|----------|----------|---------|
| 1 | A.8.2 | root 직접 로그인 차단 | grep PermitRootLogin /etc/ssh/sshd_config | no | 전체 |
| 2 | A.8.5 | 비밀번호 최대 사용일 | grep PASS_MAX_DAYS /etc/login.defs | <=90 | 전체 |
| ... | ... | ... | ... | ... | ... |
```

---

## Part B: 기술 점검 실행 (40점)

### 과제

Part A에서 작성한 체크리스트를 실제 4개 서버에서 실행하고 결과를 기록하시오.

### 서버 접속 정보

> **실습 목적**: 중간고사로 ISO 27001 기반 보안 점검 체크리스트를 작성하고 실제 서버에서 실행한다
>
> **배우는 것**: 점검 체크리스트 설계부터 기술 점검 실행, 결과 기록까지 보안 감사 전 과정을 수행한다
>
> **결과 해석**: 체크리스트의 각 항목이 적합/부적합으로 판정되고 증적이 수집되면 점검이 완료된 것이다
>
> **실전 활용**: 보안 컨설턴트의 핵심 업무는 표준 기반 체크리스트 작성과 기술 점검 수행이다

```bash
# opsclaw (Control Plane)
sshpass -p1 ssh opsclaw@10.20.30.201

# secu (방화벽/IPS)
sshpass -p1 ssh secu@10.20.30.1

# web (WAF/웹앱)
sshpass -p1 ssh web@10.20.30.80

# siem (SIEM)
sshpass -p1 ssh siem@10.20.30.100
```

### 필수 점검 항목 (최소 이것은 수행할 것)

#### 1. 계정 관리 (A.8.2)

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 각 서버에서 실행
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  # 서버별 사용자 매핑
  case $ip in 10.20.30.201) srv="opsclaw@$ip";; 10.20.30.1) srv="secu@$ip";; 10.20.30.80) srv="web@$ip";; 10.20.30.100) srv="siem@$ip";; esac
  echo "= $ip =========="

  echo "[1] 일반 사용자 계정 목록:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "awk -F: '\$3>=1000 && \$3<65534{print \$1,\$6,\$7}' /etc/passwd"  # 비밀번호 자동입력 SSH

  echo "[2] sudo 권한 사용자:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "getent group sudo 2>/dev/null"  # 비밀번호 자동입력 SSH

  echo "[3] root 직접 로그인 설정:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "grep '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null || echo '기본값'"  # 비밀번호 자동입력 SSH
done
```

#### 2. 인증 설정 (A.8.5)

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  # 서버별 사용자 매핑
  case $ip in 10.20.30.201) srv="opsclaw@$ip";; 10.20.30.1) srv="secu@$ip";; 10.20.30.80) srv="web@$ip";; 10.20.30.100) srv="siem@$ip";; esac
  echo "= $ip =========="

  echo "[4] 비밀번호 정책:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN' /etc/login.defs | grep -v '^#'"  # 비밀번호 자동입력 SSH

  echo "[5] SSH 최대 인증 시도:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "grep 'MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#' || echo '기본값(6)'"  # 비밀번호 자동입력 SSH

  echo "[6] 비밀번호 복잡도:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "cat /etc/security/pwquality.conf 2>/dev/null | grep -v '^#' | grep -v '^$' || echo '미설정'"  # 비밀번호 자동입력 SSH
done
```

#### 3. 로깅 (A.8.15)

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  # 서버별 사용자 매핑
  case $ip in 10.20.30.201) srv="opsclaw@$ip";; 10.20.30.1) srv="secu@$ip";; 10.20.30.80) srv="web@$ip";; 10.20.30.100) srv="siem@$ip";; esac
  echo "= $ip =========="

  echo "[7] syslog 서비스:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "systemctl is-active rsyslog 2>/dev/null || systemctl is-active syslog-ng 2>/dev/null"  # 비밀번호 자동입력 SSH

  echo "[8] 로그 파일 존재:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "ls -lh /var/log/syslog /var/log/auth.log 2>/dev/null"  # 비밀번호 자동입력 SSH

  echo "[9] auditd 상태:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "systemctl is-active auditd 2>/dev/null || echo '미설치'"  # 비밀번호 자동입력 SSH

  echo "[10] Wazuh Agent:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "systemctl is-active wazuh-agent 2>/dev/null || echo 'N/A'"  # 비밀번호 자동입력 SSH
done
```

#### 4. 네트워크 보안 (A.8.20~A.8.22)

```bash
# secu 서버 방화벽
echo "[11] 방화벽 기본 정책:"
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep policy"  # 비밀번호 자동입력 SSH

echo "[12] 열린 포트:"
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip ---"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "ss -tlnp 2>/dev/null | grep LISTEN"  # 비밀번호 자동입력 SSH
done

# IPS 상태
echo "[13] Suricata IPS:"
sshpass -p1 ssh secu@10.20.30.1 "systemctl is-active suricata 2>/dev/null"  # 비밀번호 자동입력 SSH
```

#### 5. 암호화 (A.8.24)

```bash
echo "[14] TLS 버전 (Wazuh Dashboard):"
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"  # 비밀번호 자동입력 SSH

echo "[15] SSH 프로토콜 버전:"
sshpass -p1 ssh opsclaw@10.20.30.201 "ssh -V 2>&1"     # 비밀번호 자동입력 SSH
```

#### 6. 시스템 설정 (A.8.9)

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  # 서버별 사용자 매핑
  case $ip in 10.20.30.201) srv="opsclaw@$ip";; 10.20.30.1) srv="secu@$ip";; 10.20.30.80) srv="web@$ip";; 10.20.30.100) srv="siem@$ip";; esac
  echo "= $ip =========="

  echo "[16] 커널 보안 파라미터:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "sysctl net.ipv4.ip_forward net.ipv4.conf.all.accept_redirects 2>/dev/null"  # 비밀번호 자동입력 SSH

  echo "[17] NTP 동기화:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "timedatectl 2>/dev/null | grep -E 'synchronized|NTP'"  # 비밀번호 자동입력 SSH

  echo "[18] 패치 현황:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "apt list --upgradable 2>/dev/null | wc -l"  # 비밀번호 자동입력 SSH
done
```

---

## Part C: 점검 결과 분석 및 보고서 (30점)

### 보고서 구조

```
=== 보안 점검 결과 보고서 ===

1. 개요
   - 점검 목적
   - 점검 범위 (대상 서버 4대)
   - 점검 기준 (ISO 27001:2022 Annex A)
   - 점검 일시

2. 점검 결과 요약
   | 판정 | 항목 수 |
   |------|---------|
   | 적합 | ? |
   | 부분적합 | ? |
   | 부적합 | ? |

3. 상세 점검 결과
   (각 항목별 실제 결과와 판정)

4. 주요 발견사항
   - 미준수 항목과 위험도
   - 즉시 조치가 필요한 사항

5. 결론
```

### 평가 기준

| 항목 | 배점 |
|------|------|
| 보고서 구조 완성도 | 5점 |
| 점검 결과 정확성 | 10점 |
| 분석의 깊이 | 10점 |
| 문서 품질 | 5점 |

---

## Part D: 개선 방안 (10점)

### 과제

부적합으로 판정된 항목에 대해 다음을 제시하시오:

1. **즉시 조치 항목** (1주 이내 가능한 것)
2. **단기 개선 항목** (1개월 이내)
3. **중장기 개선 항목** (3개월 이상)

### 예시

```
[부적합 항목: A.8.5 비밀번호 정책]
- 현황: PASS_MAX_DAYS = 99999 (만료 없음)
- 위험도: 높음
- 즉시 조치: /etc/login.defs에서 PASS_MAX_DAYS를 90으로 변경
- 단기: pwquality.conf 설정으로 복잡도 강화
- 중장기: 키 기반 인증으로 전환, 비밀번호 관리자 도입
```

---

## 채점 기준 상세

| 평가 항목 | 우수 (100%) | 보통 (70%) | 미흡 (40%) |
|-----------|------------|------------|------------|
| 체크리스트 | 15개 이상, 명령어 정확 | 10개 이상 | 10개 미만 |
| 점검 실행 | 4대 서버 전체 수행 | 2~3대 수행 | 1대만 수행 |
| 결과 분석 | 정확한 판정+근거 | 판정만 기재 | 부정확 |
| 보고서 | 구조 완비, 논리적 | 구조 미흡 | 단편적 |
| 개선방안 | 구체적, 실현가능 | 추상적 | 미제출 |

---

## 시험 전 체크사항

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 서버 접속 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 $srv "hostname" 2>/dev/null \
    && echo "$ip: OK" || echo "$ip: FAIL"
done
```

---

## 참고

- 오픈 북 시험: Week 02~07 강의 자료 참고 가능
- 인터넷 검색 가능 (다만 다른 학생과 동일한 답안은 감점)
- 결과 파일을 제출 (txt 또는 md 형식)

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

# Week 14: 인증 준비 실습 - SoA, 증적 수집, 심사 대응

## 학습 목표
- 적용성 보고서(SoA)를 작성할 수 있다
- 인증 심사를 위한 증적(Evidence)을 수집할 수 있다
- 심사원의 질문에 대한 답변을 준비할 수 있다
- 인증 심사의 전체 프로세스를 이해한다

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

# Week 14: 인증 준비 실습 - SoA, 증적 수집, 심사 대응

## 학습 목표

- 적용성 보고서(SoA)를 작성할 수 있다
- 인증 심사를 위한 증적(Evidence)을 수집할 수 있다
- 심사원의 질문에 대한 답변을 준비할 수 있다
- 인증 심사의 전체 프로세스를 이해한다

---

## 1. 인증 준비 로드맵

### 1.1 전체 일정 (일반적인 ISO 27001 인증)

```
Phase 1: 준비 (2~3개월)
  +-- 범위 정의
  +-- 리스크 평가
  +-- 정책/절차 수립
  +-- SoA 작성

Phase 2: 구현 (3~6개월)
  +-- 통제 구현
  +-- 교육 실시
  +-- 운영 시작
  +-- 증적 축적

Phase 3: 검증 (1~2개월)
  +-- 내부 감사
  +-- 경영검토
  +-- 부적합 시정
  +-- 인증 신청

Phase 4: 심사 (2~4주)
  +-- Stage 1: 문서 심사
  +-- Stage 2: 현장 심사
  +-- 시정조치 (필요 시)
  +-- 인증서 발급
```

---

## 2. 적용성 보고서 (Statement of Applicability, SoA)

> **이 실습을 왜 하는가?**
> "인증 준비 실습 - SoA, 증적 수집, 심사 대응" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 표준/컴플라이언스 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 SoA란?

ISO 27001 인증에서 **가장 중요한 문서** 중 하나이다.
93개 Annex A 통제 항목 각각에 대해:
- 적용 여부
- 적용/미적용 사유
- 구현 상태
- 관련 문서/증적

### 2.2 실습: SoA 작성

다음 형식으로 우리 실습 환경의 SoA를 작성한다:

```
================================================================
적용성 보고서 (Statement of Applicability)
조직: OpsClaw 실습 환경
기준: ISO 27001:2022 Annex A
작성일: 2026-03-27
================================================================
```

#### A.5 조직적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.5.1 | 정보보안 정책 | 적용 | 보안 운영 필수 | 부분 | 보안정책서 |
| A.5.7 | 위협 인텔리전스 | 적용 | Wazuh/OpenCTI 운영 | 구현 | SIEM 설정 |
| A.5.9 | 자산 인벤토리 | 적용 | 자산 관리 필요 | 부분 | 자산목록 |
| A.5.15 | 접근통제 정책 | 적용 | 접근통제 필수 | 구현 | 정책서, SSH설정 |
| A.5.24 | 사고관리 계획 | 적용 | 사고 대응 필수 | 부분 | 대응절차서 |

#### A.6 인적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.6.3 | 보안 인식 교육 | 적용 | 필수 | 미구현 | - |
| A.6.5 | 퇴직 후 책임 | 미적용 | 실습 환경 | N/A | - |

#### A.7 물리적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.7.1 | 물리적 보안 경계 | 미적용 | 가상 환경 | N/A | - |
| A.7.8 | 장비 위치 및 보호 | 미적용 | 가상 환경 | N/A | - |

#### A.8 기술적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.8.1 | 사용자 단말 | 적용 | 서버 접근 관리 | 부분 | SSH 설정 |
| A.8.2 | 특수접근권한 | 적용 | sudo 관리 필수 | 구현 | sudoers 설정 |
| A.8.5 | 보안 인증 | 적용 | 인증 보안 | 부분 | sshd_config |
| A.8.7 | 악성코드 방지 | 적용 | 보호 필수 | 미구현 | - |
| A.8.9 | 설정 관리 | 적용 | 서버 관리 | 부분 | 설정파일 |
| A.8.15 | 로깅 | 적용 | 감사 필수 | 구현 | rsyslog, Wazuh |
| A.8.16 | 모니터링 활동 | 적용 | 상시 감시 | 구현 | Wazuh Dashboard |
| A.8.20 | 네트워크 보안 | 적용 | 경계 보호 | 구현 | nftables 설정 |
| A.8.24 | 암호화 사용 | 적용 | 데이터 보호 | 부분 | TLS 설정 |
| A.8.28 | 보안 코딩 | 적용 | 개발 보안 | 부분 | 코드 리뷰 |

---

## 3. 증적 수집 (Evidence Collection)

### 3.1 증적 유형

| 유형 | 예시 |
|------|------|
| 문서 | 정책서, 절차서, 가이드라인 |
| 기록 | 로그, 감사 이력, 회의록 |
| 설정 | 서버 설정 파일, 방화벽 규칙 |
| 스크린샷 | 대시보드 화면, 설정 화면 |
| 인터뷰 | 담당자 면담 기록 |

### 3.2 실습: 증적 수집 스크립트

> **실습 목적**: 인증 심사 대비 증적 수집 스크립트를 작성하여 자동화된 증적 수집을 수행한다
>
> **배우는 것**: SoA(적용성 보고서) 작성, 기술적 증적 자동 수집, 심사 대응 시뮬레이션을 배운다
>
> **결과 해석**: 스크립트 실행 후 각 통제 항목별 증적 파일이 수집되면 심사 준비가 완료된 것이다
>
> **실전 활용**: 인증 심사 직전에 증적 수집 자동화는 준비 시간을 크게 단축하는 핵심 기법이다

```bash
#!/bin/bash
# 인증 심사용 증적 수집 스크립트
EVIDENCE_DIR="/tmp/audit_evidence_$(date +%Y%m%d)"
mkdir -p "$EVIDENCE_DIR"                               # 디렉터리 생성

echo "증적 수집 시작: $(date)"
echo "저장 위치: $EVIDENCE_DIR"

# 1. 서버 인벤토리 (A.5.9)
echo "=== [A.5.9] 자산 인벤토리 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "
    echo '=== 서버 정보 ==='
    hostname
    uname -a                                           # 커널/시스템 정보
    cat /etc/os-release | grep PRETTY_NAME             # 설정 파일 조회
    echo '=== 하드웨어 ==='
    lscpu | grep 'Model name'                          # CPU 정보 조회
    free -h | grep Mem                                 # 메모리 사용량 조회
    df -h /                                            # 디스크 사용량 조회
    echo '=== 서비스 ==='
    systemctl list-units --type=service --state=running --no-pager  # 서비스 관리
  " 2>/dev/null > "$EVIDENCE_DIR/inventory_${ip}.txt"
done

# 2. SSH 설정 (A.8.5)
echo "=== [A.8.5] SSH 설정 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "cat /etc/ssh/sshd_config" 2>/dev/null > "$EVIDENCE_DIR/sshd_config_${ip}.txt"
done

# 3. 사용자 계정 (A.8.2)
echo "=== [A.8.2] 계정 정보 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "
    echo '=== 사용자 목록 ==='
    cat /etc/passwd                                    # 설정 파일 조회
    echo '=== 그룹 ==='
    cat /etc/group                                     # 설정 파일 조회
    echo '=== sudo 그룹 ==='
    getent group sudo
    echo '=== 최근 로그인 ==='
    lastlog
  " 2>/dev/null > "$EVIDENCE_DIR/accounts_${ip}.txt"
done

# 4. 방화벽 규칙 (A.8.20)
echo "=== [A.8.20] 방화벽 규칙 수집 ==="
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset" 2>/dev/null > "$EVIDENCE_DIR/firewall_rules.txt"  # 비밀번호 자동입력 SSH

# 5. 비밀번호 정책 (A.8.5)
echo "=== [A.8.5] 비밀번호 정책 수집 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "                 # 비밀번호 자동입력 SSH
  echo '=== login.defs ==='
  grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs  # 패턴 검색
  echo '=== pwquality ==='
  cat /etc/security/pwquality.conf 2>/dev/null
" 2>/dev/null > "$EVIDENCE_DIR/password_policy.txt"

# 6. 로그 샘플 (A.8.15)
echo "=== [A.8.15] 로그 샘플 수집 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "tail -100 /var/log/auth.log" 2>/dev/null > "$EVIDENCE_DIR/auth_log_sample.txt"  # 비밀번호 자동입력 SSH
sshpass -p1 ssh siem@10.20.30.100 "tail -50 /var/ossec/logs/alerts/alerts.json" 2>/dev/null > "$EVIDENCE_DIR/wazuh_alerts_sample.txt"  # 비밀번호 자동입력 SSH

# 7. NTP 설정 (A.8.17)
echo "=== [A.8.17] NTP 설정 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "timedatectl" 2>/dev/null > "$EVIDENCE_DIR/ntp_${ip}.txt"
done

# 8. 패치 현황 (A.8.8)
echo "=== [A.8.8] 패치 현황 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "apt list --upgradable 2>/dev/null" > "$EVIDENCE_DIR/patches_${ip}.txt"
done

echo ""
echo "수집 완료! 파일 목록:"
ls -la "$EVIDENCE_DIR/"
echo ""
echo "총 파일 수: $(ls $EVIDENCE_DIR | wc -l)"
```

### 3.3 증적 무결성 보장

```bash
# 수집한 증적 파일의 해시값 생성 (무결성 증명)
EVIDENCE_DIR="/tmp/audit_evidence_$(date +%Y%m%d)"
cd "$EVIDENCE_DIR" 2>/dev/null && sha256sum *.txt > checksums.sha256
cat checksums.sha256
```

---

## 4. 심사 대응 준비

### 4.1 심사원이 자주 묻는 질문

| 질문 | 준비할 답변 |
|------|------------|
| "정보보안 정책은 어디에 있습니까?" | 정책 문서 위치, 최근 검토일 |
| "리스크 평가는 언제 수행했습니까?" | 리스크 평가 보고서, 날짜 |
| "비인가 접근 시 어떻게 탐지합니까?" | Wazuh SIEM 운영, 알림 체계 |
| "접근 권한은 어떻게 관리합니까?" | 계정 관리 절차, sudo 정책 |
| "사고 발생 시 대응 절차는?" | 사고대응 절차서, 대응팀 연락처 |
| "로그는 얼마나 보관합니까?" | logrotate 설정, 6개월 이상 |
| "패치 관리는 어떻게 합니까?" | 패치 주기, 최근 적용 이력 |
| "변경 관리 절차가 있습니까?" | 변경 요청/승인/테스트/적용 절차 |

### 4.2 실습: 심사 시뮬레이션

심사원 역할과 피심사자 역할을 나누어 연습한다.

**시나리오 1: 접근통제 심사**
```
심사원: "서버에 대한 접근 통제를 어떻게 하고 있습니까?"

피심사자: (다음을 보여준다)
```

```bash
# SSH 접근 제한 설정 시연
sshpass -p1 ssh opsclaw@10.20.30.201 "grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#'"

# 방화벽에서 SSH 접근 제한
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep -A2 'ssh\|22'"

# 계정 권한 현황
sshpass -p1 ssh opsclaw@10.20.30.201 "getent group sudo"
```

**시나리오 2: 모니터링 심사**
```
심사원: "보안 이벤트를 어떻게 모니터링합니까?"
```

```bash
# Wazuh SIEM 운영 현황
sshpass -p1 ssh siem@10.20.30.100 "systemctl status wazuh-manager 2>/dev/null | head -5"

# 에이전트 연결 현황
sshpass -p1 ssh siem@10.20.30.100 "/var/ossec/bin/agent_control -l 2>/dev/null | head -10"

# 최근 알림 확인
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 | python3 -m json.tool 2>/dev/null | head -20"
```

**시나리오 3: 사고대응 심사**
```
심사원: "지난 6개월간 보안 사고가 있었습니까? 대응 기록을 보여주십시오."
```

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 고위험 알림 이력
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 12:
            ts = a.get('timestamp','')
            print(f'  {ts} [Level {r[\"level\"]}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 5. 부적합 시정 조치

### 5.1 부적합 유형

| 유형 | 설명 | 대응 기한 |
|------|------|----------|
| 중대 부적합 (Major) | 통제 항목 전체가 미구현 | 90일 이내 시정 |
| 경미 부적합 (Minor) | 부분적으로 미흡 | 다음 사후심사까지 |
| 관찰 사항 (OFI) | 개선이 바람직한 사항 | 권고 (의무 아님) |

### 5.2 시정 조치 보고서 양식

```
시정조치 보고서
- 부적합 번호: NC-001
- 관련 통제: A.8.15 로깅
- 부적합 내용: auditd가 미설치되어 명령 수준 감사 로그가 없음
- 근본 원인: 초기 서버 구축 시 auditd 설치가 누락됨
- 시정 조치: auditd 패키지 설치 및 감사 규칙 설정
- 예방 조치: 서버 구축 체크리스트에 auditd 포함
- 증적: 설치 로그, 설정 파일, auditd 상태 캡처
- 완료일: 2026-04-XX
```

---

## 6. 핵심 정리

1. **SoA** = 93개 통제 항목별 적용 여부와 사유를 문서화
2. **증적 수집** = 문서, 설정, 로그, 스크린샷을 체계적으로 수집
3. **무결성** = 증적의 해시값을 기록하여 변조 방지
4. **심사 대응** = 질문에 즉시 증적을 보여줄 수 있도록 준비
5. **시정 조치** = 부적합 발견 시 근본원인 분석 + 예방조치까지

---

## 과제

1. 실습 환경에 대한 SoA를 A.8 기술적 통제 34개 항목 전체에 대해 작성하시오
2. 증적 수집 스크립트를 실행하고 결과를 정리하시오
3. 심사 시뮬레이션 시나리오 2개를 추가로 작성하고 답변을 준비하시오

---

## 참고 자료

- ISO 27001 Certification Process Guide
- ISO 27001 SoA Template
- KISA ISMS-P 인증심사 가이드

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

# Week 14: 인증 준비 실습 - SoA, 증적 수집, 심사 대응

## 학습 목표
- 적용성 보고서(SoA)를 작성할 수 있다
- 인증 심사를 위한 증적(Evidence)을 수집할 수 있다
- 심사원의 질문에 대한 답변을 준비할 수 있다
- 인증 심사의 전체 프로세스를 이해한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

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
조직: Bastion 실습 환경
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
  ssh $srv  # srv=user@ip (아래 루프 참고) "
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
  ssh $srv  # srv=user@ip (아래 루프 참고) "cat /etc/ssh/sshd_config" 2>/dev/null > "$EVIDENCE_DIR/sshd_config_${ip}.txt"
done

# 3. 사용자 계정 (A.8.2)
echo "=== [A.8.2] 계정 정보 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  ssh $srv  # srv=user@ip (아래 루프 참고) "
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
ssh ccc@10.20.30.1 "sudo nft list ruleset" 2>/dev/null > "$EVIDENCE_DIR/firewall_rules.txt"  # 비밀번호 자동입력 SSH

# 5. 비밀번호 정책 (A.8.5)
echo "=== [A.8.5] 비밀번호 정책 수집 ==="
ssh ccc@10.20.30.201 "                 # 비밀번호 자동입력 SSH
  echo '=== login.defs ==='
  grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs  # 패턴 검색
  echo '=== pwquality ==='
  cat /etc/security/pwquality.conf 2>/dev/null
" 2>/dev/null > "$EVIDENCE_DIR/password_policy.txt"

# 6. 로그 샘플 (A.8.15)
echo "=== [A.8.15] 로그 샘플 수집 ==="
ssh ccc@10.20.30.201 "tail -100 /var/log/auth.log" 2>/dev/null > "$EVIDENCE_DIR/auth_log_sample.txt"  # 비밀번호 자동입력 SSH
ssh ccc@10.20.30.100 "tail -50 /var/ossec/logs/alerts/alerts.json" 2>/dev/null > "$EVIDENCE_DIR/wazuh_alerts_sample.txt"  # 비밀번호 자동입력 SSH

# 7. NTP 설정 (A.8.17)
echo "=== [A.8.17] NTP 설정 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  ssh $srv  # srv=user@ip (아래 루프 참고) "timedatectl" 2>/dev/null > "$EVIDENCE_DIR/ntp_${ip}.txt"
done

# 8. 패치 현황 (A.8.8)
echo "=== [A.8.8] 패치 현황 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  ssh $srv  # srv=user@ip (아래 루프 참고) "apt list --upgradable 2>/dev/null" > "$EVIDENCE_DIR/patches_${ip}.txt"
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
ssh ccc@10.20.30.201 "grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#'"

# 방화벽에서 SSH 접근 제한
ssh ccc@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep -A2 'ssh\|22'"

# 계정 권한 현황
ssh ccc@10.20.30.201 "getent group sudo"
```

**시나리오 2: 모니터링 심사**
```
심사원: "보안 이벤트를 어떻게 모니터링합니까?"
```

```bash
# Wazuh SIEM 운영 현황
ssh ccc@10.20.30.100 "systemctl status wazuh-manager 2>/dev/null | head -5"

# 에이전트 연결 현황
ssh ccc@10.20.30.100 "/var/ossec/bin/agent_control -l 2>/dev/null | head -10"

# 최근 알림 확인
ssh ccc@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 | python3 -m json.tool 2>/dev/null | head -20"
```

**시나리오 3: 사고대응 심사**
```
심사원: "지난 6개월간 보안 사고가 있었습니까? 대응 기록을 보여주십시오."
```

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 고위험 알림 이력
ssh ccc@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
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
    예: login.defs 캡처, 변경 로그, Bastion evidence
```

### 증적 수집 실습

```bash
# ISO 27001 A.8.5 (안전한 인증) 점검 증적 수집
echo "=== 패스워드 정책 확인 ==="
ssh ccc@10.20.30.80 "  # 비밀번호 자동입력 SSH
  echo '--- login.defs ---' && grep -E 'PASS_MAX|PASS_MIN|PASS_WARN' /etc/login.defs
  echo '--- pam 설정 ---' && grep pam_pwquality /etc/pam.d/common-password 2>/dev/null || echo 'pam_pwquality 미설정'
  echo '--- sudo 설정 ---' && sudo -l 2>/dev/null | head -5
" 2>/dev/null

# 결과를 Bastion evidence로 기록
# (Bastion dispatch 사용)
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
| "이 통제의 증적을 보여주세요" | Bastion evidence/replay로 실행 이력 제시 |
| "리스크 평가를 어떻게 했나요?" | 리스크 평가 워크시트 + 기준 설명 |
| "부적합 사항은 어떻게 처리했나요?" | 시정 조치 계획서 + 완료 증적 |
| "경영진의 검토는?" | 검토 회의록 + 서명 |

---

> **실습 환경 검증 완료** (2026-03-28): PASS_MAX_DAYS=99999, pam_pwquality, auditd, SSH 설정, nftables 점검

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### ISO/IEC 27001:2022 (Annex A)
> **역할:** 정보보호 관리체계 국제 표준 — 93개 통제(A.5~A.8)  
> **실행 위치:** `문서/증적 (정책·절차·기록)`  
> **접속/호출:** 표준 문서 + SoA + 리스크 등록부

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `SoA.xlsx (Statement of Applicability)` | 93개 통제 적용/제외 선언 |
| `risk_register.xlsx` | 자산·위협·취약점·리스크 점수 |
| `policies/` | 정책 14종 (접근제어, 백업, 사건대응 등) |

**핵심 설정·키**

- `A.5 (조직적)` — 정책, 역할, 정보분류
- `A.6 (인적)` — 채용·퇴직 시 보안, 인식 교육
- `A.7 (물리적)` — 보안 구역, 장비, 케이블링
- `A.8 (기술적)` — 접근·암호화·로깅·개발 보안

**로그·확인 명령**

- `내부심사 보고서` — 부적합(NC)·관찰사항(OB)
- `경영검토 회의록` — 연 1회 필수

**UI / CLI 요점**

- PDCA 사이클 — 수립→운영→검토→개선
- 2022 개정 — 114→93 통제, 신규 11건(위협 인텔리전스 등)

> **해석 팁.** SoA는 **모든 통제에 대해 포함/제외 사유**를 명시해야 한다. 심사관은 `Justification for exclusion`을 먼저 본다.

### ISMS-P (KISA)
> **역할:** 한국 정보보호·개인정보보호 관리체계  
> **실행 위치:** `문서/증적`  
> **접속/호출:** KISA 인증 심사 체크리스트

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `관리체계 수립·운영 (1장)` | 정책·조직·자산·위험관리 16개 |
| `보호대책 요구사항 (2장)` | 64개 통제 |
| `개인정보 처리 단계별 요구사항 (3장)` | 21개 통제 |

**핵심 설정·키**

- `총 101개 통제항목` — 인증: 80개 핵심 + 선택 21개
- `매 3년 갱신 심사` — 매년 사후 심사

**로그·확인 명령**

- `접근기록 보관 (1년/3년)` — 개인정보 중요도별
- `개인정보 영향평가(PIA) 보고서` — 5만명↑ 공공기관 의무

**UI / CLI 요점**

- https://isms.kisa.or.kr — 고시·해설서 공식 사이트

> **해석 팁.** 한국은 **개인정보보호법이 최상위**. ISMS-P의 3장(개인정보)은 법 위반 여부와 직결되므로 증적 우선순위 1.

---

## 실제 사례 (WitFoo Precinct 6 — SoA + 증적 수집의 *완성 양식*)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *인증 준비 — SoA·증적·심사 대응* 학습 항목 매칭. dataset 자체가 *완성된 증적 수집* 사례.

### Case 1: SoA 양식 — dataset framework 매핑 모방

dataset 의 host 노드 framework 매핑 = SoA 의 *applicable 통제 list* 양식:

```
ISO 27001 Annex A 통제 번호 → applicable=Y/N → product → evidence count

예 (Precinct product):
A.5.1 → Y → Precinct → iso27001:[4] (정책)
A.13.1 → Y → Precinct + Cisco ASA → iso27001:[113-124] (네트워크)
A.16 → Y → Precinct → iso27001:[130-132] (incident)
```

→ dataset 의 *iso27001:[24 numbers]* = 학생 SoA 의 *applicable 통제 24 항목* baseline.

### Case 2: 증적 수집 — dataset 의 4-layer 양식

audit 심사관에게 제출할 증적은 *4-layer* 보유 필요:
1. **timestamp** (ms 정밀도)
2. **partition + node + edge ID** (재현)
3. **익명화** (4-layer 절차)
4. **framework 매핑** (control 번호)

→ dataset 의 모든 record 가 4-layer 보유 = 증적 양식 *직접 모방* 가능.

### Case 3: 심사 대응 — dataset 의 NCR (Non-Conformance Report) 가능성

dataset 부재 항목 = NCR 후보:
- ISMS-P 부재 → 한국 인증 시 NCR
- HIPAA 부재 → 의료 환경 NCR
- PR (NIST CSF Protect) 가 csf:[1,3,4] 에서 부재 → NCR

**학생 액션**: SoA 작성 시 dataset 의 framework 매핑 양식 그대로 모방. 부재 항목은 *별도 product 추가 또는 NCR 사전 확인*.


---

## 부록: 학습 OSS 도구 매트릭스 (Course4 Compliance — Week 14 보안 교육/인식)

### 보안 교육 영역 → OSS 도구

| 영역 | OSS 도구 | 강점 |
|------|---------|------|
| 피싱 시뮬레이션 | **gophish** + King-Phisher / SET | 캠페인 자동 |
| 인식 평가 | **Moodle** (LMS) + LearnDash | 강의 + 시험 |
| 사용자 행동 분석 | **Wazuh user-behavior** + osquery | 위험 사용자 식별 |
| 사고 대응 훈련 | **CyberRange** OSS / DetectionLab / Atomic Red Team | 가상 환경 |
| 점수 평가 | gophish dashboard / 자체 BI | 정량 측정 |
| 인식 콘텐츠 | **Open Educational Resources** + 자체 markdown | OSINT 사례 |

### 핵심 — gophish 피싱 시뮬레이션 (사용자 인식 측정)

```bash
# 설치
mkdir -p /opt/gophish && cd /opt/gophish
curl -sL https://github.com/gophish/gophish/releases/latest/download/gophish-v0.12.1-linux-64bit.zip -o gophish.zip
unzip gophish.zip
chmod +x gophish

# 시작 (관리자 패널 + landing 페이지 동시)
sudo ./gophish
# 로그: 초기 admin password 콘솔에 출력
# Admin: https://localhost:3333
# Landing: http://localhost:80

# 캠페인 생성 흐름:
# 1. Sending Profile — SMTP 서버 등록
# 2. Email Template — 피싱 메일 작성 (HTML)
# 3. Landing Page — 피싱 사이트 (자격증명 수집 모방)
# 4. User Group — 대상자 import (CSV)
# 5. Campaign — 발송 + 추적
```

### 학생 환경 준비

```bash
sudo apt install -y postfix mailutils swaks
git clone https://github.com/gophish/gophish.git ~/gophish

# Moodle (학습 관리 LMS)
docker run -d -p 80:80 -p 443:443 \
  --name moodle \
  -e MOODLE_USERNAME=admin \
  -e MOODLE_PASSWORD=Pa$$w0rd \
  bitnami/moodle:latest

# Atomic Red Team (사고 시뮬)
git clone https://github.com/redcanaryco/atomic-red-team.git ~/atomic
pip3 install pyinvoke

# DetectionLab (학습용 가상 환경)
# https://github.com/clong/DetectionLab
```

### 핵심 도구 사용법

```bash
# 1) gophish 캠페인 흐름
# https://localhost:3333 접속 → API 토큰 발급
TOKEN="..."

# 사용자 그룹 자동 등록
curl -k -X POST https://localhost:3333/api/groups \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"전직원","targets":[
    {"first_name":"홍","last_name":"길동","email":"hong@company.com"},
    {"first_name":"김","last_name":"철수","email":"kim@company.com"}
  ]}'

# 캠페인 생성 + 발송
curl -k -X POST https://localhost:3333/api/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name":"Q1 피싱 훈련",
    "template":{"name":"비밀번호 재설정"},
    "page":{"name":"가짜 로그인 페이지"},
    "smtp":{"name":"내부 SMTP"},
    "groups":[{"name":"전직원"}]
  }'

# 결과 통계
curl -k https://localhost:3333/api/campaigns/{id}/results -H "Authorization: Bearer $TOKEN" | jq

# 2) Wazuh user-behavior (위험 사용자 식별)
# /var/ossec/etc/ossec.conf 의 user-behavior 모듈 활성화
sudo /var/ossec/bin/wazuh-control restart

# 사용자별 alert 빈도 추출
sudo jq -r '.data.srcuser // .data.dstuser // .data.user' /var/ossec/logs/alerts/alerts.json | \
  sort | uniq -c | sort -rn | head -20

# 3) Atomic Red Team — 사용자 인식 검증 (실제 공격 패턴)
sudo invoke install-atomicredteam
sudo invoke run-atomic-test T1566.001                            # 피싱 첨부
sudo invoke run-atomic-test T1110.001                            # SSH brute (사용자가 의심하는지)

# 4) Moodle (LMS — 보안 교육 강의 + 시험)
# Web UI 에서 강의 작성 → 직원 자동 enroll → 시험 결과 자동 채점
```

### 보안 교육 분기 사이클

```bash
# Phase 1: 사전 교육 (Moodle)
# 보안 정책 강의 (week13 markdown 활용) → 시험 → 합격자 인증

# Phase 2: 피싱 시뮬레이션 (gophish)
# 분기별 1회, 무작위 직원 대상
# 측정 KPI:
# - Click Rate: 피싱 링크 클릭 비율 (목표 < 10%)
# - Submit Rate: 자격증명 제출 비율 (목표 < 3%)
# - Report Rate: 피싱 신고 비율 (목표 > 30%)

# Phase 3: 결과 분석 + 추가 교육
curl -k https://gophish/api/campaigns/results | jq '.results[] | {email, status}'
# Click 한 사용자 → 추가 교육 자동 enroll

# Phase 4: 사고 대응 훈련 (TheHive + Atomic)
# 분기별 가상 사고 → IR 팀 대응 시간 측정 (RTO/MTTR)

# Phase 5: 보고
# - 인식률 향상 추이 (분기별)
# - 부서별/직급별 위험도
# - 추천 후속 교육
pandoc training-q1.md -o training-q1.pdf
```

### 사용자 인식 점수 (조직 KPI)

| KPI | 측정 방법 | 목표 |
|-----|----------|------|
| 클릭률 | gophish 캠페인 결과 | < 10% |
| 신고율 | 메일 신고 button + Wazuh rule | > 30% |
| 시험 통과율 | Moodle 시험 결과 | > 90% |
| 사고 대응 시간 | TheHive MTTR | < 4 시간 |

학생은 본 14주차에서 **gophish + Wazuh user-behavior + Atomic Red Team + Moodle** 4 도구로 보안 교육의 4 단계 (학습 → 시뮬 → 측정 → 후속) 사이클을 OSS 만으로 운영한다.

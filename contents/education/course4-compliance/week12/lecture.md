# Week 12: 보안 감사 실습

## 학습 목표
- 보안 감사의 유형과 절차를 이해한다
- 로그 감사(Log Audit)를 수행할 수 있다
- 설정 검토(Configuration Review)를 수행할 수 있다
- 갭 분석(Gap Analysis)을 통해 미준수 항목을 도출할 수 있다

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

# Week 12: 보안 감사 실습

## 학습 목표

- 보안 감사의 유형과 절차를 이해한다
- 로그 감사(Log Audit)를 수행할 수 있다
- 설정 검토(Configuration Review)를 수행할 수 있다
- 갭 분석(Gap Analysis)을 통해 미준수 항목을 도출할 수 있다

---

## 1. 보안 감사 개요

### 1.1 감사 유형

| 유형 | 설명 | 주체 |
|------|------|------|
| 내부 감사 | 조직 내부에서 자체 수행 | 내부 감사팀 |
| 외부 감사 | 제3자 기관이 수행 | 인증기관, 회계법인 |
| 기술 감사 | 시스템 설정/취약점 점검 | 보안 컨설턴트 |
| 프로세스 감사 | 절차/정책 준수 확인 | 감사팀 |

### 1.2 감사 절차

```
1. 감사 계획 수립 (범위, 기준, 일정)
2. 자료 수집 (문서, 로그, 설정, 인터뷰)
3. 분석 및 평가 (기준 대비 현황 비교)
4. 발견사항 도출 (부적합, 관찰사항, 개선권고)
5. 보고서 작성
6. 시정조치 확인
```

---

## 2. 로그 감사 (Log Audit)

> **이 실습을 왜 하는가?**
> "보안 감사 실습" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 표준/컴플라이언스 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 감사해야 할 로그

| 로그 | 위치 | 감사 목적 |
|------|------|----------|
| auth.log | /var/log/auth.log | 인증 시도, sudo 사용 |
| syslog | /var/log/syslog | 시스템 이벤트 |
| Suricata | /var/log/suricata/ | 네트워크 공격 탐지 |
| Wazuh | /var/ossec/logs/ | 보안 알림 통합 |
| 웹 로그 | /var/log/nginx/ | 웹 접근, 공격 시도 |

### 2.2 실습: 인증 로그 감사

> **실습 목적**: 인증 로그, 시스템 로그를 분석하여 보안 감사 증적을 수집하고 이상 징후를 발견한다
>
> **배우는 것**: SSH 로그인 이력, sudo 사용 기록, 서비스 변경 로그에서 감사 대상 이벤트를 추출하는 방법을 배운다
>
> **결과 해석**: 다수의 로그인 실패, 비인가 sudo 사용, 비정상 시간대 접속이 발견되면 보안 이슈이다
>
> **실전 활용**: 정기 보안 감사에서 로그 분석은 보안 정책 준수 여부를 확인하는 핵심 활동이다

```bash
# 1. SSH 로그인 성공/실패 통계
echo "=== SSH 로그인 감사 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip ---"
  echo -n "성공: "
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep 'Accepted' /var/log/auth.log 2>/dev/null | wc -l"
  echo -n "실패: "
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep 'Failed password' /var/log/auth.log 2>/dev/null | wc -l"
done
```

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 2. 실패한 로그인의 출발지 IP 분석
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -10"  # 텍스트 필드 처리
```

```bash
# 3. sudo 사용 감사
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: sudo 사용 이력 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep 'sudo:' /var/log/auth.log 2>/dev/null | tail -5"
done
```

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 4. 비정상 시간대 로그인 확인 (새벽 2~5시)
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'session opened' /var/log/auth.log 2>/dev/null | \
  awk '{print \$3}' | awk -F: '\$1>=2 && \$1<=5 {print}'"  # 텍스트 필드 처리
```

### 2.3 실습: 네트워크 로그 감사

로그나 설정에서 특정 패턴을 검색합니다.

```bash
# Suricata 알림 분석
echo "=== Suricata 알림 통계 ==="
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log 2>/dev/null | \
  awk -F'\\]' '{print \$2}' | sort | uniq -c | sort -rn | head -10"  # 텍스트 필드 처리

# Suricata 알림 심각도별 분류
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log 2>/dev/null | \
  grep -oE 'Priority: [0-9]+' | sort | uniq -c | sort -rn"  # 디렉터리 재귀 검색
```

### 2.4 실습: Wazuh 알림 감사

원격 서버에 접속하여 명령을 실행합니다.

```bash
# Wazuh 알림 레벨별 통계
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
import sys, json
from collections import Counter
levels = Counter()
rules = Counter()
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line)
        r = a.get('rule', {})
        levels[r.get('level', 0)] += 1
        if r.get('level', 0) >= 8:
            rules[r.get('description', 'unknown')] += 1
    except: pass
print('=== 레벨별 통계 ===')
for l in sorted(levels.keys(), reverse=True):          # 반복문 시작
    print(f'  Level {l}: {levels[l]}건')
print()
print('=== 고위험 알림 Top 5 ===')
for desc, cnt in rules.most_common(5):                 # 반복문 시작
    print(f'  {cnt}건: {desc}')
\" 2>/dev/null"
```

---

## 3. 설정 검토 (Configuration Review)

### 3.1 점검 스크립트

로그나 설정에서 특정 패턴을 검색합니다.

```bash
#!/bin/bash
# 보안 설정 감사 스크립트
echo "================================================"
echo " 보안 설정 감사 보고서 - $(date '+%Y-%m-%d %H:%M')"
echo "================================================"

SERVERS="10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100"

for ip in $SERVERS; do                                 # 반복문 시작
  echo ""
  echo "############## $ip ##############"

  # 1. SSH 설정
  echo "[SSH 설정]"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "
    echo -n '  PermitRootLogin: '; grep '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null || echo '기본값'
    echo -n '  PasswordAuth: '; grep '^PasswordAuthentication' /etc/ssh/sshd_config 2>/dev/null || echo '기본값'
    echo -n '  MaxAuthTries: '; grep '^MaxAuthTries' /etc/ssh/sshd_config 2>/dev/null || echo '기본값(6)'
    echo -n '  Protocol: '; ssh -V 2>&1
  " 2>/dev/null

  # 2. 비밀번호 정책
  echo "[비밀번호 정책]"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "
    grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_MIN_LEN' /etc/login.defs 2>/dev/null | sed 's/^/  /'  # 패턴 검색
  " 2>/dev/null

  # 3. 파일 권한
  echo "[중요 파일 권한]"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "
    stat -c '  %a %n' /etc/passwd /etc/shadow /etc/ssh/sshd_config 2>/dev/null
  " 2>/dev/null

  # 4. 네트워크 서비스
  echo "[열린 포트]"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "ss -tlnp 2>/dev/null | grep LISTEN | awk '{print \"  \" \$4}'" 2>/dev/null

  # 5. 커널 보안
  echo "[커널 보안 파라미터]"
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "
    echo -n '  ip_forward: '; sysctl -n net.ipv4.ip_forward 2>/dev/null
    echo -n '  accept_redirects: '; sysctl -n net.ipv4.conf.all.accept_redirects 2>/dev/null
    echo -n '  accept_source_route: '; sysctl -n net.ipv4.conf.all.accept_source_route 2>/dev/null
  " 2>/dev/null
done
```

### 3.2 CIS Benchmark 기준 점검

CIS(Center for Internet Security)는 각 OS별 보안 설정 가이드를 제공한다.

```bash
# CIS 권장 사항 일부 점검
ip=10.20.30.201

echo "=== CIS Benchmark 일부 점검 ==="

echo "[1.1] 별도 /tmp 파티션:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "mount | grep ' /tmp ' || echo '  별도 파티션 아님'"

echo "[1.4] ASLR 활성화:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "sysctl kernel.randomize_va_space 2>/dev/null"

echo "[2.1] inetd/xinetd 서비스:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "systemctl is-active inetd xinetd 2>/dev/null || echo '  미설치 (양호)'"

echo "[3.1] IP 포워딩 비활성화:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "sysctl net.ipv4.ip_forward 2>/dev/null"

echo "[4.1] auditd 활성화:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "systemctl is-active auditd 2>/dev/null || echo '  미활성'"

echo "[5.1] cron 접근 제한:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "ls -la /etc/cron.allow /etc/cron.deny 2>/dev/null || echo '  설정 없음'"

echo "[5.2] SSH 설정:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "stat -c '%a' /etc/ssh/sshd_config 2>/dev/null | xargs -I{} echo '  sshd_config 권한: {}'"

echo "[6.1] 파일 무결성 도구:"
sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "which aide tripwire 2>/dev/null || echo '  무결성 도구 미설치'"
```

---

## 4. 갭 분석 (Gap Analysis)

### 4.1 갭 분석이란?

현재 상태(As-Is)와 목표 상태(To-Be)의 차이를 분석하는 것이다.

```
[현재 상태] ←--- GAP ---→ [목표 상태 (ISO 27001/ISMS-P 기준)]
```

### 4.2 실습: 갭 분석 수행

```bash
# 갭 분석 자동화 스크립트
echo "========================================="
echo " 갭 분석 결과 - ISO 27001 기반"
echo "========================================="

ip=10.20.30.201

# A.8.2 특수접근권한
echo ""
echo "[A.8.2] 특수접근권한 관리"
echo "  기준: PermitRootLogin no"
result=$(sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null" || echo "미설정")
echo "  현황: $result"
if echo "$result" | grep -q "no"; then
  echo "  판정: 적합"
else
  echo "  판정: 부적합 (GAP)"
  echo "  조치: /etc/ssh/sshd_config에 PermitRootLogin no 설정"
fi

# A.8.5 보안인증
echo ""
echo "[A.8.5] 보안인증 - 비밀번호 최대 사용일"
echo "  기준: PASS_MAX_DAYS <= 90"
result=$(sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep '^PASS_MAX_DAYS' /etc/login.defs 2>/dev/null | awk '{print \$2}'")
echo "  현황: PASS_MAX_DAYS = $result"
if [ -n "$result" ] && [ "$result" -le 90 ] 2>/dev/null; then
  echo "  판정: 적합"
else
  echo "  판정: 부적합 (GAP)"
  echo "  조치: /etc/login.defs에서 PASS_MAX_DAYS 90으로 변경"
fi

# A.8.15 로깅
echo ""
echo "[A.8.15] 로깅 - auditd"
echo "  기준: auditd 활성화"
result=$(sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "systemctl is-active auditd 2>/dev/null" || echo "inactive")
echo "  현황: $result"
if [ "$result" = "active" ]; then
  echo "  판정: 적합"
else
  echo "  판정: 부적합 (GAP)"
  echo "  조치: apt install auditd && systemctl enable auditd"
fi

# A.8.20 네트워크보안
echo ""
echo "[A.8.20] 네트워크보안 - 방화벽 기본정책"
echo "  기준: 기본 정책 DROP"
result=$(sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep 'policy drop'" || echo "")
if [ -n "$result" ]; then
  echo "  현황: 기본 정책 DROP"
  echo "  판정: 적합"
else
  echo "  현황: 기본 정책 DROP 아님 또는 확인 불가"
  echo "  판정: 확인 필요"
fi
```

### 4.3 갭 분석 결과 요약 템플릿

```
| No | 통제항목 | 기준 | 현황 | 갭 여부 | 우선순위 | 조치 방안 | 담당 | 완료예정 |
|----|---------|------|------|---------|---------|----------|------|---------|
| 1 | A.8.2 | root 로그인 차단 | 허용 상태 | GAP | 높음 | sshd_config 수정 | 시스템팀 | 1주 |
| 2 | A.8.5 | 비밀번호 90일 | 99999일 | GAP | 높음 | login.defs 수정 | 시스템팀 | 1주 |
| 3 | A.8.15 | auditd 활성화 | 미설치 | GAP | 중간 | 패키지 설치 | 보안팀 | 2주 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
```

---

## 5. 감사 보고서 작성

### 5.1 보고서 구조

```
========================================
보안 감사 보고서
========================================

1. 감사 개요
   - 감사 기간: 2026-XX-XX ~ 2026-XX-XX
   - 감사 범위: 서버 4대 (opsclaw, secu, web, siem)
   - 감사 기준: ISO 27001:2022, ISMS-P
   - 감사팀: (이름)

2. 감사 결과 요약
   - 점검 항목: 20개
   - 적합: X개
   - 부적합: X개
   - 관찰사항: X개

3. 상세 발견사항
   3.1 부적합 사항
       (각 항목별 상세)
   3.2 관찰 사항
       (개선 권고)

4. 갭 분석 결과

5. 권고사항
   - 즉시 조치 항목
   - 단기 개선 항목
   - 중장기 개선 항목

6. 결론
```

---

## 6. 핵심 정리

1. **보안 감사** = 로그 감사 + 설정 검토 + 갭 분석
2. **로그 감사** = 인증, 네트워크, SIEM 로그 분석
3. **설정 검토** = CIS Benchmark 등 기준 대비 점검
4. **갭 분석** = 현재 상태와 목표 상태의 차이 도출
5. **보고서** = 발견사항, 갭 분석, 권고사항을 체계적으로 문서화

---

## 과제

1. 4개 서버에 대해 로그 감사를 수행하고 이상 징후를 3가지 이상 보고하시오
2. CIS Benchmark 기준 10개 항목 이상 설정 검토를 수행하시오
3. 갭 분석 결과를 표로 작성하고 우선순위별 개선 계획을 수립하시오

---

## 참고 자료

- CIS Benchmarks (https://www.cisecurity.org/cis-benchmarks)
- ISO 27001:2022 내부 감사 가이드
- KISA 보안 감사 체크리스트

---

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

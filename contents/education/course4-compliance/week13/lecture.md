# Week 13: 미국 표준 - SOC 2, HIPAA

## 학습 목표
- SOC 2 인증의 Trust Service Criteria를 이해한다
- HIPAA의 의료 데이터 보호 요구사항을 이해한다
- 글로벌 컴플라이언스의 공통점과 차이점을 파악한다
- 실습 환경에서 SOC 2/HIPAA 기준의 점검을 수행한다

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

## 1. SOC 2 (Service Organization Control 2)

### 1.1 SOC 보고서 유형

| 유형 | 대상 | 내용 |
|------|------|------|
| SOC 1 | 재무 보고 관련 | 내부 통제 (ICFR) |
| SOC 2 | IT 서비스 | 보안, 가용성, 처리 무결성, 기밀성, 프라이버시 |
| SOC 3 | 일반 공개 | SOC 2의 요약본 |

- **SOC 2 Type I**: 특정 시점의 통제 설계 적합성
- **SOC 2 Type II**: 일정 기간(보통 6~12개월) 동안의 통제 운영 효과성

### 1.2 SOC 2를 받는 이유

- SaaS, 클라우드 서비스 기업에서 **사실상 필수**
- B2B 계약에서 고객이 SOC 2 보고서를 요구
- AWS, Google Cloud, Salesforce 등 모두 SOC 2 보유

---

## 2. Trust Service Criteria (TSC) 5가지

> **이 실습을 왜 하는가?**
> "미국 표준 - SOC 2, HIPAA" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 표준/컴플라이언스 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 개요

| TSC | 기준 | 핵심 |
|-----|------|------|
| Security (보안) | 공통 기준, 필수 | 비인가 접근으로부터 보호 |
| Availability (가용성) | 선택 | 약정된 수준의 서비스 가용성 |
| Processing Integrity (처리 무결성) | 선택 | 정확하고 완전한 데이터 처리 |
| Confidentiality (기밀성) | 선택 | 기밀 정보 보호 |
| Privacy (프라이버시) | 선택 | 개인정보 수집/이용/보관/파기 |

> Security는 **필수**이고, 나머지 4개는 서비스 성격에 따라 선택한다.

### 2.2 Security TSC 주요 항목

| 항목 | 내용 | 실습 환경 점검 |
|------|------|---------------|
| CC1 | 통제 환경 (조직, 역할) | 관리자 역할 분리 |
| CC2 | 커뮤니케이션 (정책 공유) | 보안 정책 문서 존재 |
| CC3 | 리스크 평가 | 리스크 매트릭스 |
| CC4 | 모니터링 | Wazuh, Suricata |
| CC5 | 통제 활동 | 접근통제, 암호화 |
| CC6 | 논리적/물리적 접근 통제 | SSH, 방화벽, 계정관리 |
| CC7 | 시스템 운영 | 변경관리, 패치 |
| CC8 | 변경 관리 | 설정 변경 이력 |
| CC9 | 리스크 완화 | 사고 대응 절차 |

### 2.3 실습: CC6 (접근 통제) 점검

> **실습 목적**: SOC 2 Trust Services Criteria 중 CC6(접근 통제) 항목을 실습 환경에서 점검한다
>
> **배우는 것**: 미국 SOC 2 프레임워크의 접근 통제 기준과 ISO 27001의 차이를 비교하며 점검한다
>
> **결과 해석**: 방화벽, SSH 설정, 계정 관리가 CC6 기준에 부합하면 SOC 2 관점에서 적합이다
>
> **실전 활용**: SaaS 기업의 글로벌 진출 시 SOC 2 Type II 보고서는 고객사가 요구하는 필수 인증이다

```bash
# CC6.1: 논리적 접근 보안 소프트웨어
echo "=== 방화벽 ==="
ssh ccc@10.20.30.1 "sudo nft list ruleset 2>/dev/null | head -10"  # 비밀번호 자동입력 SSH

echo "=== IPS ==="
ssh ccc@10.20.30.1 "systemctl is-active suricata 2>/dev/null"  # 비밀번호 자동입력 SSH

# CC6.2: 사용자 인증
echo "=== 인증 방식 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do  # 반복문 시작
  echo "--- $ip ---"
  ssh $srv  # srv=user@ip (아래 루프 참고) "grep -E 'PasswordAuthentication|PubkeyAuthentication' /etc/ssh/sshd_config | grep -v '^#'"
done

# CC6.3: 접근 권한 부여/변경/제거
echo "=== 권한 관리 ==="
ssh ccc@10.20.30.201 "getent group sudo"  # 비밀번호 자동입력 SSH
ssh ccc@10.20.30.201 "lastlog 2>/dev/null | head -10"  # 비밀번호 자동입력 SSH

# CC6.6: 외부 위협으로부터 보호
echo "=== 보안 시스템 ==="
ssh ccc@10.20.30.1 "systemctl is-active suricata nftables 2>/dev/null"  # 비밀번호 자동입력 SSH
ssh ccc@10.20.30.80 "systemctl is-active apache2 || systemctl is-active apache2 2>/dev/null"  # 비밀번호 자동입력 SSH
```

### 2.4 실습: CC7 (시스템 운영) 점검

```bash
# CC7.1: 이상 징후 탐지
echo "=== Wazuh 알림 현황 ==="
ssh ccc@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null"  # 비밀번호 자동입력 SSH
ssh ccc@10.20.30.100 "wc -l /var/ossec/logs/alerts/alerts.json 2>/dev/null"  # 비밀번호 자동입력 SSH

# CC7.2: 보안 사고 모니터링
echo "=== 최근 고위험 알림 ==="
ssh ccc@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 10:
            print(f'  [{r[\"level\"]}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -5"

# CC7.3: 변경 관리
echo "=== 최근 패키지 변경 ==="
ssh ccc@10.20.30.201 "tail -5 /var/log/dpkg.log 2>/dev/null"  # 비밀번호 자동입력 SSH
```

---

## 3. HIPAA (Health Insurance Portability and Accountability Act)

### 3.1 개요

- **미국 의료정보 보호법** (1996년 제정)
- PHI (Protected Health Information, 보호대상 건강정보) 보호
- 의료기관, 보험사, 의료 IT 서비스 기업에 적용

### 3.2 HIPAA 구성

| 규칙 | 내용 |
|------|------|
| Privacy Rule | PHI의 사용/공개 규제 |
| Security Rule | 전자 PHI(ePHI)의 기술적/관리적/물리적 보호 |
| Breach Notification Rule | 유출 시 통지 의무 |
| Enforcement Rule | 위반 시 제재 |

### 3.3 Security Rule 세부

| 보호 유형 | 항목 | 예시 |
|-----------|------|------|
| 관리적 | 리스크 분석 | 정기적 위험 평가 수행 |
| 관리적 | 인력 보안 | 직원 접근 권한 관리 |
| 관리적 | 보안 교육 | 연 1회 이상 |
| 물리적 | 시설 접근 통제 | 서버실 출입 관리 |
| 물리적 | 워크스테이션 보안 | 화면 잠금 |
| 기술적 | 접근 통제 | 고유 사용자 ID |
| 기술적 | 감사 통제 | 접근 로그 기록 |
| 기술적 | 무결성 통제 | 데이터 변조 방지 |
| 기술적 | 전송 보안 | 암호화 |

### 3.4 실습: HIPAA 기술적 보호조치 점검

```bash
# 기술적 보호조치: 접근통제 (164.312(a))
echo "=== 고유 사용자 ID ==="
ssh ccc@10.20.30.201 "awk -F: '\$3>=1000 && \$3<65534 {print \$1, \$3}' /etc/passwd"  # 비밀번호 자동입력 SSH

echo "=== 자동 로그오프 ==="
ssh ccc@10.20.30.201 "grep TMOUT /etc/profile /etc/bash.bashrc 2>/dev/null || echo '미설정 (HIPAA 부적합)'"  # 비밀번호 자동입력 SSH

echo "=== 접근 실패 잠금 ==="
ssh ccc@10.20.30.201 "grep pam_faillock /etc/pam.d/common-auth 2>/dev/null || echo '미설정'"  # 비밀번호 자동입력 SSH

# 기술적 보호조치: 감사통제 (164.312(b))
echo "=== 감사 로그 ==="
ssh ccc@10.20.30.201 "systemctl is-active auditd rsyslog 2>/dev/null"  # 비밀번호 자동입력 SSH
ssh ccc@10.20.30.201 "ls -lh /var/log/auth.log 2>/dev/null"  # 비밀번호 자동입력 SSH

# 기술적 보호조치: 전송보안 (164.312(e))
echo "=== 전송 암호화 ==="
ssh ccc@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"  # 비밀번호 자동입력 SSH
```

### 3.5 HIPAA 위반 제재

| 위반 유형 | 과징금 (건당) |
|-----------|-------------|
| 모르고 위반 | $100~$50,000 |
| 합리적 사유 | $1,000~$50,000 |
| 고의적 무시 (시정) | $10,000~$50,000 |
| 고의적 무시 (미시정) | $50,000 |
| **연간 최대** | **$1,500,000** |

---

## 4. SOC 2 vs HIPAA vs ISO 27001 vs ISMS-P

| 항목 | SOC 2 | HIPAA | ISO 27001 | ISMS-P |
|------|-------|-------|-----------|--------|
| 국가 | 미국 | 미국 | 국제 | 한국 |
| 대상 | 서비스 기업 | 의료 관련 | 전 산업 | 전 산업 |
| 인증 | 보고서 | 자체 준수 | 인증서 | 인증서 |
| 감사 주체 | CPA 법인 | 자체/OCR | 인증기관 | KISA |
| 개인정보 | Privacy TSC | PHI 보호 | ISO 27701 | 통합(22항목) |
| 유효기간 | 12개월 | 지속 | 3년 | 3년 |

---

## 5. 글로벌 컴플라이언스 전략

### 5.1 공통 요구사항

거의 모든 표준/규정이 요구하는 공통 보안 통제:

```
1. 접근통제 (사용자 인증, 권한 관리)
2. 로깅 및 모니터링 (감사 로그)
3. 암호화 (전송/저장)
4. 패치 관리
5. 사고 대응 절차
6. 리스크 관리
7. 보안 교육
```

### 5.2 실습: 공통 기준 점검

```bash
# 모든 표준이 공통으로 요구하는 7가지 기본 점검
echo "========================================="
echo " 글로벌 컴플라이언스 공통 점검"
echo "========================================="

ip=10.20.30.201

echo "[1] 접근통제"
ssh $srv  # srv=user@ip (아래 루프 참고) "grep -c '^PermitRootLogin no' /etc/ssh/sshd_config 2>/dev/null && echo '  root 로그인 차단: OK' || echo '  root 로그인 차단: FAIL'"

echo "[2] 로깅"
ssh $srv  # srv=user@ip (아래 루프 참고) "systemctl is-active rsyslog 2>/dev/null && echo '  rsyslog: OK' || echo '  rsyslog: FAIL'"

echo "[3] 암호화"
ssh ccc@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep 'Protocol' | grep -q 'TLSv1.[23]' && echo '  TLS: OK' || echo '  TLS: 확인필요'"  # 비밀번호 자동입력 SSH

echo "[4] 패치"
cnt=$(ssh $srv  # srv=user@ip (아래 루프 참고) "apt list --upgradable 2>/dev/null | wc -l")
echo "  미적용 패치: $cnt"

echo "[5] 사고대응"
ssh ccc@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null && echo '  SIEM: OK' || echo '  SIEM: FAIL'"  # 비밀번호 자동입력 SSH

echo "[6] 리스크관리"
echo "  (문서 점검 항목 - 리스크 평가 문서 존재 여부)"

echo "[7] 보안교육"
echo "  (문서 점검 항목 - 교육 이수 기록 존재 여부)"
```

---

## 6. 실무 시나리오: 다중 컴플라이언스 대응

한 기업이 ISO 27001 + SOC 2 + ISMS-P를 동시에 충족해야 하는 경우:

### 6.1 통합 접근법

```
1. 공통 기반 구축
   → ISO 27001 기반 ISMS 구축 (가장 포괄적)
2. SOC 2 추가 대응
   → Trust Service Criteria 매핑, 증적 수집
3. ISMS-P 추가 대응
   → 개인정보보호 요구사항 추가
4. 통합 감사
   → 한 번의 감사로 여러 인증 대응
```

### 6.2 매핑 테이블 예시

| 통제 | ISO 27001 | SOC 2 | ISMS-P | HIPAA |
|------|-----------|-------|--------|-------|
| 접근통제 정책 | A.5.15 | CC6.1 | 2.6.1 | 164.312(a) |
| 사용자 인증 | A.8.5 | CC6.1 | 2.5.3 | 164.312(d) |
| 감사 로그 | A.8.15 | CC7.2 | 2.10.4 | 164.312(b) |
| 암호화 | A.8.24 | CC6.7 | 2.7.1 | 164.312(e) |
| 사고 대응 | A.5.26 | CC7.4 | 2.11.3 | 164.308(a)(6) |

---

## 7. 핵심 정리

1. **SOC 2** = SaaS/클라우드 기업의 사실상 필수 인증, 5가지 TSC
2. **HIPAA** = 미국 의료정보 보호법, ePHI에 대한 기술적/관리적/물리적 보호
3. **공통 요구사항** = 접근통제, 로깅, 암호화, 패치, 사고대응
4. **다중 컴플라이언스** = ISO 27001 기반으로 구축하고 매핑으로 대응
5. **증적(Evidence)** = 모든 인증에서 가장 중요한 것은 "증명"

---

## 과제

1. SOC 2 Trust Service Criteria 5가지를 실습 환경에 대해 각각 점검하시오
2. HIPAA Security Rule의 기술적 보호조치를 실습 환경에서 점검하시오
3. ISO 27001, SOC 2, ISMS-P, HIPAA의 접근통제 관련 항목 매핑 표를 완성하시오

---

## 참고 자료

- AICPA SOC 2 Trust Service Criteria (TSC)
- HHS HIPAA Security Rule (https://www.hhs.gov/hipaa)
- SOC 2 Compliance Guide for Startups
- HIPAA Technical Safeguards Checklist

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

### NIST Cybersecurity Framework 2.0
> **역할:** 미국 연방 사이버 보안 프레임워크  
> **실행 위치:** `전사 거버넌스`  
> **접속/호출:** NIST 공식 PDF + Profile Tool

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `Core (6 Functions)` | Govern / Identify / Protect / Detect / Respond / Recover |
| `Categories / Subcategories` | 기능별 통제 항목 |
| `Implementation Tiers 1~4` | 성숙도 |

**핵심 설정·키**

- `Govern (2.0 신규)` — 거버넌스 — 조직 맥락, 역할, 리스크 전략
- `Profiles (Current/Target)` — 현재 상태→목표 상태 갭

**UI / CLI 요점**

- https://www.nist.gov/cyberframework — CSF 공식
- OLIR (매핑) — ISO 27001, CIS Controls와 상호 매핑

> **해석 팁.** 2.0의 **Govern**이 이전 1.1 Identify.Governance를 승격시킨 핵심 변화. 이사회 보고가 프레임워크에 공식 편입.

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041 (Data Theft)` 패턴

```
incident_id=d45fc680-cb9b-11ee-9d8c-014a3c92d0a7 mo_name=Data Theft
red=172.25.238.143 blue=100.64.5.119 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041 (Data Theft)` 패턴

```
incident_id=c6f8acf0-df14-11ee-9778-4184b1db151c mo_name=Data Theft
red=100.64.3.190 blue=100.64.3.183 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.


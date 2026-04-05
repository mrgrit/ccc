# Week 09: GDPR / 개인정보보호 - EU와 한국 비교

## 학습 목표
- GDPR(EU 일반 개인정보보호 규정)의 핵심 원칙을 이해한다
- 한국의 개인정보보호법과 GDPR을 비교할 수 있다
- 개인정보 처리의 기술적 보호조치를 실습한다
- 개인정보 유출 대응 절차를 파악한다

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

# Week 09: GDPR / 개인정보보호 - EU와 한국 비교

## 학습 목표

- GDPR(EU 일반 개인정보보호 규정)의 핵심 원칙을 이해한다
- 한국의 개인정보보호법과 GDPR을 비교할 수 있다
- 개인정보 처리의 기술적 보호조치를 실습한다
- 개인정보 유출 대응 절차를 파악한다

---

## 1. GDPR이란?

### 1.1 개요

- **GDPR**: General Data Protection Regulation (EU 일반 개인정보보호 규정)
- 2018년 5월 25일 시행
- EU 시민의 개인정보를 처리하는 **모든 조직**에 적용 (EU 밖 기업 포함)

### 1.2 왜 알아야 하는가?

| 이유 | 설명 |
|------|------|
| 역외 적용 | 한국 기업도 EU 고객 데이터를 다루면 적용 |
| 높은 과징금 | 최대 2천만 유로 또는 전세계 연매출 4% |
| 글로벌 표준 | 한국법도 GDPR을 참고하여 개정 |
| 기술 요구사항 | 개발자/운영자에게 직접적인 기술 요구 |

---

## 2. GDPR 핵심 원칙 (7가지)

> **이 실습을 왜 하는가?**
> "GDPR / 개인정보보호 - EU와 한국 비교" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 표준/컴플라이언스 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 원칙 목록

| 원칙 | 내용 | 예시 |
|------|------|------|
| 적법성/공정성/투명성 | 합법적 근거로 공정하게 처리 | 동의서, 개인정보처리방침 |
| 목적 제한 | 명확한 목적으로만 수집 | 마케팅 동의 없이 광고 발송 불가 |
| 데이터 최소화 | 필요한 최소한만 수집 | 배송에 주민번호 불필요 |
| 정확성 | 정확하게 유지 | 오래된 정보 갱신 |
| 보관 제한 | 목적 달성 후 파기 | 탈퇴 회원 정보 즉시 삭제 |
| 무결성/기밀성 | 적절한 보안 조치 | 암호화, 접근통제 |
| 책임성 | 준수를 증명할 의무 | 처리 활동 기록 |

### 2.2 적법한 처리 근거 (6가지)

```
1. 정보주체의 동의
2. 계약 이행
3. 법적 의무
4. 정보주체의 중대한 이익
5. 공익 목적
6. 정당한 이익 (이해관계 균형)
```

---

## 3. 정보주체의 권리

| 권리 | 내용 | GDPR 조항 |
|------|------|----------|
| 열람권 | 자신의 데이터 확인 | 제15조 |
| 정정권 | 부정확한 데이터 수정 | 제16조 |
| 삭제권 (잊힐 권리) | 데이터 삭제 요구 | 제17조 |
| 처리 제한권 | 처리 일시 중지 요구 | 제18조 |
| 이동권 | 다른 서비스로 데이터 이전 | 제20조 |
| 반대권 | 특정 처리에 반대 | 제21조 |
| 자동화 결정 거부권 | AI/자동 판단 거부 | 제22조 |

---

## 4. 한국 개인정보보호법과 비교

### 4.1 주요 비교

| 항목 | GDPR | 한국 개인정보보호법 |
|------|------|-------------------|
| 시행 | 2018년 | 2011년 (2020년 대규모 개정) |
| 적용 범위 | EU 시민 데이터 처리 전체 | 한국 내 개인정보 처리 |
| 역외 적용 | 있음 | 제한적 |
| 과징금 | 매출 4% 또는 2천만 유로 | 매출 3% 이하 |
| DPO 의무 | 특정 조건 시 필수 | CPO(개인정보보호책임자) 필수 |
| 동의 방식 | 옵트인 (명시적) | 옵트인 (명시적) |
| 잊힐 권리 | 명시적 규정 | 삭제 요구권 |
| 이동권 | 명시적 규정 | 2023년 도입 (마이데이터) |
| 처벌 | 행정 과징금 중심 | 형사 처벌 + 과징금 |

### 4.2 한국법 특이사항

- **주민등록번호**: 원칙적 수집 금지 (법적 근거 필요)
- **개인정보 영향평가**: 공공기관 의무
- **개인정보보호위원회**: 독립 감독기관 (2020년 격상)
- **정보통신망법**: 온라인 서비스 추가 규제

---

## 5. 기술적 보호조치

### 5.1 GDPR Article 32 - 처리의 보안

GDPR은 다음 기술적 조치를 요구한다:

```
(a) 개인정보의 가명처리 및 암호화
(b) 처리 시스템의 기밀성, 무결성, 가용성, 복원력 보장
(c) 물리적/기술적 사고 시 적시에 가용성 복원
(d) 보호조치의 효과를 정기적으로 테스트/평가
```

### 5.2 실습: 데이터베이스의 개인정보 보호

> **실습 목적**: GDPR의 기술적 보호조치 요구사항을 실습 환경의 데이터베이스에서 확인한다
>
> **배우는 것**: SSL 암호화 전송, 접근 통제, 개인정보 최소 수집 원칙이 기술적으로 구현되었는지 점검한다
>
> **결과 해석**: PostgreSQL에서 SSL이 on이면 전송 암호화 적합, off이면 GDPR 제32조 부적합이다
>
> **실전 활용**: 글로벌 서비스 운영 시 GDPR 제32조의 기술적 보호조치 준수는 법적 의무이다

```bash
# PostgreSQL 접속하여 암호화 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"SHOW ssl;\" 2>/dev/null"

# DB 접근 권한 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"\\du\" 2>/dev/null"

# DB 접근 로그 설정 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"SHOW log_connections;\" 2>/dev/null"
sshpass -p1 ssh opsclaw@10.20.30.201 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"SHOW log_disconnections;\" 2>/dev/null"
```

### 5.3 실습: 전송 구간 암호화

```bash
# 웹 서비스의 TLS 설정 확인
sshpass -p1 ssh web@10.20.30.80 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep -E 'Protocol|Cipher'"

# Wazuh API TLS
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:55000 2>/dev/null | grep Protocol"

# Wazuh Dashboard TLS
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"
```

### 5.4 실습: 접근 통제

```bash
# 개인정보가 포함될 수 있는 로그 파일의 접근 권한
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "ls -la /var/log/auth.log /var/log/syslog 2>/dev/null"
done
```

### 5.5 실습: 로그에서 개인정보 확인

```bash
# 로그에 IP 주소(개인정보 해당 가능)가 기록되는지 확인
sshpass -p1 ssh secu@10.20.30.1 "tail -20 /var/log/suricata/fast.log 2>/dev/null"

# 웹 로그에서 사용자 정보 확인
sshpass -p1 ssh web@10.20.30.80 "tail -10 /var/log/nginx/access.log 2>/dev/null || tail -10 /var/log/apache2/access.log 2>/dev/null"
```

---

## 6. 개인정보 유출 대응

### 6.1 GDPR 유출 통지 의무

```
발견 → 72시간 이내 감독기관 통지
     → 고위험인 경우 정보주체에게도 통지
```

### 6.2 한국법 유출 통지 의무

```
발견 → 72시간 이내 정보주체 통지
     → 1천명 이상 유출 시 개인정보보호위원회 + KISA 신고
```

### 6.3 유출 대응 절차

```
1. 유출 인지 및 초기 대응
   - 유출 범위 파악
   - 추가 유출 차단
2. 영향 평가
   - 유출 데이터 종류
   - 영향 받는 정보주체 수
   - 위험도 평가
3. 통지
   - 감독기관 통지 (72시간)
   - 정보주체 통지
4. 사후 조치
   - 원인 분석
   - 재발 방지 대책
   - 기록 보존
```

### 6.4 실습: 유출 탐지 시뮬레이션

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 대량 데이터 외부 전송 시도 탐지 (Wazuh 알림)
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"  # 비밀번호 자동입력 SSH
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        alert = json.loads(line)
        rule = alert.get('rule', {})
        if rule.get('level', 0) >= 10:
            print(f'Level {rule[\"level\"]}: {rule.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | head -10"

# auth.log에서 대량 접근 시도 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'session opened' /var/log/auth.log 2>/dev/null | wc -l"  # 비밀번호 자동입력 SSH
```

---

## 7. 가명처리와 익명처리

### 7.1 개념 비교

| 구분 | 가명처리 (Pseudonymization) | 익명처리 (Anonymization) |
|------|---------------------------|------------------------|
| 정의 | 추가 정보 없이는 식별 불가 | 어떤 수단으로도 식별 불가 |
| GDPR 적용 | 적용됨 (여전히 개인정보) | 적용 안됨 |
| 복원 가능 | 가능 (매핑 테이블 보유) | 불가능 |
| 예시 | 이름을 해시값으로 대체 | 통계 데이터만 추출 |

### 7.2 실습: 간단한 가명처리 예시

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 로그에서 IP 주소를 해시로 가명처리하는 예시
sshpass -p1 ssh opsclaw@10.20.30.201 "echo '10.20.30.1 tried SSH login' | \
  sed -E 's/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/[MASKED]/g'"  # 텍스트 치환

# Python으로 가명처리
sshpass -p1 ssh opsclaw@10.20.30.201 "python3 -c \"    # 비밀번호 자동입력 SSH
import hashlib
ip = '10.20.30.1'                                      # 네트워크 설정
pseudo = hashlib.sha256(ip.encode()).hexdigest()[:8]
print(f'원본: {ip}')
print(f'가명: user_{pseudo}')
\""
```

---

## 8. 개인정보보호 체크리스트 (실습 환경)

```bash
# 종합 점검 스크립트
echo "=== 개인정보보호 기술적 점검 ==="

echo "[1] DB 암호화 설정:"
sshpass -p1 ssh opsclaw@10.20.30.201 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c 'SHOW ssl;' 2>/dev/null"  # 비밀번호 자동입력 SSH

echo "[2] 전송 암호화 (TLS):"
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"  # 비밀번호 자동입력 SSH

echo "[3] 접근 로그 활성화:"
sshpass -p1 ssh opsclaw@10.20.30.201 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c 'SHOW log_statement;' 2>/dev/null"  # 비밀번호 자동입력 SSH

echo "[4] 로그 파일 권한:"
sshpass -p1 ssh opsclaw@10.20.30.201 "stat -c '%a' /var/log/auth.log 2>/dev/null"  # 비밀번호 자동입력 SSH

echo "[5] 백업 암호화:"
sshpass -p1 ssh opsclaw@10.20.30.201 "ls /backup/*.gpg 2>/dev/null || echo '암호화된 백업 없음'"  # 비밀번호 자동입력 SSH
```

---

## 9. 핵심 정리

1. **GDPR** = EU 시민 데이터를 다루는 모든 조직에 적용되는 강력한 규정
2. **7가지 원칙** = 적법성, 목적제한, 최소화, 정확성, 보관제한, 보안, 책임
3. **정보주체 권리** = 열람, 정정, 삭제, 이동, 반대, 자동화결정 거부
4. **한국법과 유사** = 동의 기반, 목적 제한, 안전조치 의무
5. **72시간 통지** = GDPR과 한국법 모두 유출 시 신속 통지 의무

---

## 과제

1. GDPR과 한국 개인정보보호법의 차이점을 5가지 이상 정리하시오
2. 실습 환경에서 개인정보보호 기술적 점검을 수행하고 결과를 보고하시오
3. 로그 데이터에서 개인정보(IP, 사용자명)를 가명처리하는 스크립트를 작성하시오

---

## 참고 자료

- EU GDPR 공식 문서 (https://gdpr.eu)
- 개인정보보호위원회 (https://www.pipc.go.kr)
- 한국 개인정보보호법 전문
- GDPR vs 한국법 비교 분석 (KISA 발간)

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

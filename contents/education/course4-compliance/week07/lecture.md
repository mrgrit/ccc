# Week 07: NIST CSF - 사이버보안 프레임워크

## 학습 목표
- NIST CSF(Cybersecurity Framework)의 5가지 기능을 이해한다
- 각 기능의 카테고리와 서브카테고리를 설명할 수 있다
- NIST CSF를 실습 환경에 적용하여 평가할 수 있다
- ISO 27001, ISMS-P와의 관계를 파악한다

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

# Week 07: NIST CSF - 사이버보안 프레임워크

## 학습 목표

- NIST CSF(Cybersecurity Framework)의 5가지 기능을 이해한다
- 각 기능의 카테고리와 서브카테고리를 설명할 수 있다
- NIST CSF를 실습 환경에 적용하여 평가할 수 있다
- ISO 27001, ISMS-P와의 관계를 파악한다

---

## 1. NIST CSF란?

### 1.1 배경

- **NIST**: 미국 국립표준기술연구소 (National Institute of Standards and Technology)
- **CSF**: Cybersecurity Framework
- 2014년 초판 발행, **2024년 CSF 2.0** 개정
- 미국 정부 기관뿐 아니라 전 세계 민간 기업도 널리 활용

### 1.2 특징

| 특징 | 설명 |
|------|------|
| 리스크 기반 | 위험도에 따라 우선순위 결정 |
| 성과 기반 | "무엇을 달성할 것인가"에 초점 |
| 기술 중립적 | 특정 기술/제품에 종속되지 않음 |
| 자발적 | 법적 의무 아님 (권장 사항) |
| 유연함 | 조직 규모/산업에 맞게 조정 가능 |

---

## 2. 5가지 핵심 기능 (CSF 1.1 기준)

> **이 실습을 왜 하는가?**
> "NIST CSF - 사이버보안 프레임워크" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 표준/컴플라이언스 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 전체 구조

```
Identify(식별) --> Protect(보호) --> Detect(탐지) --> Respond(대응) --> Recover(복구)
```

> CSF 2.0에서는 **Govern(거버넌스)**이 추가되어 6개 기능이지만,
> 핵심 5개 기능의 이해가 먼저이다.

### 2.2 각 기능의 목표

| 기능 | 목표 | 핵심 질문 |
|------|------|----------|
| Identify | 자산과 리스크 파악 | "우리가 보호해야 할 것은 무엇인가?" |
| Protect | 보안 대책 구현 | "어떻게 보호할 것인가?" |
| Detect | 보안 이벤트 탐지 | "침해가 발생했는지 어떻게 알 수 있는가?" |
| Respond | 사고 대응 | "침해 발생 시 무엇을 할 것인가?" |
| Recover | 복구 및 개선 | "어떻게 정상으로 돌아갈 것인가?" |

---

## 3. Identify (식별)

### 3.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| ID.AM | 자산 관리 | 하드웨어, 소프트웨어, 데이터 인벤토리 |
| ID.BE | 비즈니스 환경 | 조직의 역할, 공급망, 핵심 서비스 |
| ID.GV | 거버넌스 | 정책, 법적 요구사항, 리스크 관리 전략 |
| ID.RA | 리스크 평가 | 위협, 취약점, 영향도, 가능성 |
| ID.RM | 리스크 관리 전략 | 리스크 수용 기준, 우선순위 |
| ID.SC | 공급망 리스크 | 외부 파트너/공급업체 리스크 |

### 3.2 실습: 자산 식별 (ID.AM)

> **실습 목적**: NIST CSF의 식별(Identify) 기능에 따라 자산 인벤토리를 수집하고 문서화한다
>
> **배우는 것**: NIST CSF ID.AM(자산관리) 카테고리에 따라 물리적/소프트웨어/서비스 자산을 체계적으로 식별한다
>
> **결과 해석**: 각 서버의 하드웨어 정보, 설치 소프트웨어, 실행 서비스가 목록화되면 자산 식별이 완료된 것이다
>
> **실전 활용**: NIST CSF 기반 보안 프로그램의 첫 단계는 항상 보호 대상 자산의 식별과 분류이다

```bash
# ID.AM-1: 물리적 장치 및 시스템 인벤토리
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "hostname; lscpu | grep 'Model name'; free -h | grep Mem; df -h / | tail -1"
done

# ID.AM-2: 소프트웨어 인벤토리
sshpass -p1 ssh opsclaw@10.20.30.201 "dpkg -l | wc -l"
sshpass -p1 ssh opsclaw@10.20.30.201 "systemctl list-units --type=service --state=running --no-pager | wc -l"

# ID.AM-3: 데이터 흐름 매핑
sshpass -p1 ssh secu@10.20.30.1 "ip route show"
sshpass -p1 ssh secu@10.20.30.1 "ss -tlnp | grep LISTEN"
```

---

## 4. Protect (보호)

### 4.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| PR.AC | 접근 통제 | 신원 관리, 인증, 원격 접근 |
| PR.AT | 인식 교육 | 보안 교육, 역할 기반 훈련 |
| PR.DS | 데이터 보안 | 암호화, 무결성, 유출 방지 |
| PR.IP | 보호 프로세스 | 설정 관리, 백업, 변경 관리 |
| PR.MA | 유지보수 | 원격/현장 유지보수 통제 |
| PR.PT | 보호 기술 | 로깅, 이동매체, 네트워크 보호 |

### 4.2 실습: 보호 대책 점검

```bash
# PR.AC-1: 접근 통제 (계정 관리)
sshpass -p1 ssh opsclaw@10.20.30.201 "awk -F: '\$3>=1000 && \$3<65534{print \$1}' /etc/passwd"

# PR.AC-3: 원격 접근 관리 (SSH 설정)
sshpass -p1 ssh opsclaw@10.20.30.201 "grep -E 'PermitRootLogin|MaxAuthTries|Protocol' /etc/ssh/sshd_config | grep -v '^#'"

# PR.DS-1: 전송 데이터 보호 (TLS)
sshpass -p1 ssh siem@10.20.30.100 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"

# PR.DS-2: 저장 데이터 보호 (파일 권한)
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -la /etc/shadow"

# PR.IP-1: 설정 관리 (기본 설정 변경 여부)
sshpass -p1 ssh opsclaw@10.20.30.201 "grep '^Port' /etc/ssh/sshd_config || echo '기본 포트(22) 사용'"

# PR.IP-4: 백업
sshpass -p1 ssh opsclaw@10.20.30.201 "crontab -l 2>/dev/null | grep backup || echo '자동 백업 미설정'"

# PR.PT-1: 감사 로그
sshpass -p1 ssh opsclaw@10.20.30.201 "systemctl is-active rsyslog 2>/dev/null"
```

---

## 5. Detect (탐지)

### 5.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| DE.AE | 이상 징후 및 이벤트 | 기준선 설정, 이벤트 분석 |
| DE.CM | 지속적 모니터링 | 네트워크, 시스템, 악성코드 모니터링 |
| DE.DP | 탐지 프로세스 | 역할 정의, 테스트, 개선 |

### 5.2 실습: 탐지 체계 점검

```bash
# DE.CM-1: 네트워크 모니터링 (Suricata IPS)
sshpass -p1 ssh secu@10.20.30.1 "systemctl is-active suricata 2>/dev/null"
sshpass -p1 ssh secu@10.20.30.1 "tail -3 /var/log/suricata/fast.log 2>/dev/null || echo '로그 없음'"

# DE.CM-4: 악성코드 탐지
sshpass -p1 ssh opsclaw@10.20.30.201 "which clamscan 2>/dev/null || echo 'AV 미설치'"

# DE.CM-7: 비인가 활동 모니터링 (Wazuh)
sshpass -p1 ssh siem@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null"

# DE.AE-3: 이벤트 데이터 수집 확인
sshpass -p1 ssh siem@10.20.30.100 "ls -lh /var/ossec/logs/alerts/alerts.json 2>/dev/null"
```

---

## 6. Respond (대응)

### 6.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| RS.RP | 대응 계획 | 사고 대응 절차 실행 |
| RS.CO | 커뮤니케이션 | 내외부 이해관계자 소통 |
| RS.AN | 분석 | 사고 조사, 영향 분석 |
| RS.MI | 완화 | 사고 격리, 확산 방지 |
| RS.IM | 개선 | 대응 절차 개선 |

### 6.2 실습: 대응 체계 점검

```bash
# RS.AN-1: 사고 분석 (로그 분석 능력)
# 최근 SSH 실패 로그 분석
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -5"

# RS.MI-1: 사고 격리 (방화벽으로 IP 차단 가능 여부)
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep 'drop' | head -5"

# RS.CO-1: 알림 체계 확인 (Wazuh 알림 설정)
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/etc/ossec.conf 2>/dev/null | grep -A5 '<email_notification>' | head -6"
```

---

## 7. Recover (복구)

### 7.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| RC.RP | 복구 계획 | 복구 절차 실행 |
| RC.IM | 개선 | 복구 전략 개선 |
| RC.CO | 커뮤니케이션 | 복구 상태 공유 |

### 7.2 실습: 복구 체계 점검

```bash
# RC.RP-1: 백업 존재 여부
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -la /backup/ 2>/dev/null || echo '백업 디렉토리 없음'"

# 데이터베이스 백업 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -la /tmp/*dump* /tmp/*backup* 2>/dev/null || echo 'DB 백업 없음'"

# 서비스 재시작 능력 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "systemctl is-enabled postgresql 2>/dev/null || echo 'postgresql 서비스 상태 확인 필요'"
```

---

## 8. NIST CSF vs ISO 27001 vs ISMS-P 비교

| 구분 | NIST CSF | ISO 27001 | ISMS-P |
|------|---------|-----------|--------|
| 국가 | 미국 | 국제 | 한국 |
| 성격 | 프레임워크 (가이드) | 표준 (인증) | 표준 (인증) |
| 접근법 | 기능 기반 (5+1) | 프로세스 기반 | 영역 기반 (3) |
| 인증 | 없음 | 있음 | 있음 |
| 강점 | 유연, 직관적 | 국제적 인정 | 한국법 완전 대응 |

### 8.1 매핑 예시

| NIST CSF | ISO 27001 | ISMS-P |
|----------|-----------|--------|
| ID.AM (자산관리) | A.5.9~A.5.14 | 2.1.3 |
| PR.AC (접근통제) | A.8.1~A.8.5 | 2.5, 2.6 |
| DE.CM (모니터링) | A.8.15~A.8.16 | 2.10.4 |
| RS.AN (사고분석) | A.5.25~A.5.27 | 2.11 |
| RC.RP (복구) | A.5.29~A.5.30 | 2.12 |

---

## 9. 실습: CSF 프로파일 작성

우리 실습 환경에 대한 간이 CSF 프로파일을 작성한다:

| 기능 | 카테고리 | 현재 수준 (1~4) | 목표 수준 | 갭 |
|------|---------|----------------|----------|-----|
| Identify | ID.AM 자산관리 | ? | 3 | ? |
| Protect | PR.AC 접근통제 | ? | 3 | ? |
| Detect | DE.CM 모니터링 | ? | 3 | ? |
| Respond | RS.AN 분석 | ? | 2 | ? |
| Recover | RC.RP 복구계획 | ? | 2 | ? |

**수준 정의**:
- 1: 부분적 (Partial) - 비공식, 임시 대응
- 2: 리스크 인지 (Risk Informed) - 일부 프로세스 존재
- 3: 반복 가능 (Repeatable) - 문서화된 절차
- 4: 적응형 (Adaptive) - 지속적 개선

---

## 10. 핵심 정리

1. **NIST CSF** = 5가지 기능(식별/보호/탐지/대응/복구) 기반 프레임워크
2. **인증이 아닌 가이드** = 조직에 맞게 유연하게 적용
3. **성숙도 모델** = Tier 1~4로 현재 수준과 목표를 비교
4. **다른 표준과 호환** = ISO 27001, ISMS-P 등과 매핑 가능
5. **CSF 2.0** = Govern(거버넌스) 기능 추가

---

## 과제

1. 실습 환경 4개 서버에 대해 CSF 5가지 기능별로 현재 수준을 평가하시오
2. 가장 개선이 시급한 기능과 그 이유를 설명하시오
3. NIST CSF와 ISMS-P의 매핑 표를 10개 항목 이상 작성하시오

---

## 참고 자료

- NIST Cybersecurity Framework v2.0 (https://www.nist.gov/cyberframework)
- NIST SP 800-53 Security and Privacy Controls
- NIST CSF to ISO 27001 Mapping Guide

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

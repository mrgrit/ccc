# Week 15: 결과 분석 + 보고서 -- 로그 분석, 통계, 교훈, 보고서 작성법

## 학습 목표
- 전체 공방전(Week 11~14)의 로그 데이터를 체계적으로 수집하고 분석할 수 있다
- 공격/방어 활동의 통계를 산출하고 시각화 가능한 형태로 정리할 수 있다
- MITRE ATT&CK 기반의 TTP 분류와 탐지 효과 분석을 수행할 수 있다
- 전문적인 보안 보고서(Executive Summary, 기술 분석, 교훈, 개선 권고)를 작성할 수 있다
- Purple Team 관점에서 공격-방어 갭 분석을 수행하고 보안 개선 로드맵을 제안할 수 있다
- OpsClaw를 활용하여 전체 과정의 증적을 통합 관리할 수 있다
- 보안 보고서의 대상 독자(경영진, 기술팀, 감사)에 맞게 내용을 조정할 수 있다

## 전제 조건
- Week 11~14의 공방전 결과 데이터 보유
- 로그 분석 기초 (grep, awk, sort, uniq)
- MITRE ATT&CK 프레임워크 이해
- NIST IR 프레임워크 이해 (Week 09)

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 보안 보고서 작성 이론 + 구조 | 강의 |
| 0:35-1:05 | 로그 분석 방법론 + 통계 기법 | 강의 |
| 1:05-1:15 | 휴식 | - |
| 1:15-1:55 | 로그 수집 + 통계 분석 실습 | 실습 |
| 1:55-2:35 | ATT&CK 매핑 + 갭 분석 실습 | 실습 |
| 2:35-2:45 | 휴식 | - |
| 2:45-3:15 | 보고서 작성 실습 | 실습 |
| 3:15-3:40 | 발표 + 과정 총정리 + 최종 퀴즈 | 토론/퀴즈 |

---

# Part 1: 보안 보고서 작성 이론 (35분)

## 1.1 보안 보고서의 목적과 유형

보안 보고서는 기술적 발견 사항을 비기술적 의사결정자에게 전달하는 핵심 문서이다. 훌륭한 공격/방어 능력도 보고서로 전달되지 않으면 가치가 반감된다.

### 보고서 유형

| 유형 | 대상 독자 | 초점 | 분량 |
|------|---------|------|------|
| **경영진 보고서** | CISO, CTO, 경영진 | 위험, 영향, 투자 필요성 | 2~3페이지 |
| **기술 보고서** | 보안팀, 개발팀 | 취약점 상세, 재현 방법 | 10~30페이지 |
| **감사 보고서** | 감사팀, 규정 담당 | 규정 준수, 증거, 조치 | 5~15페이지 |
| **사후 분석 보고서** | 전체 관계자 | 타임라인, 교훈, 개선 | 5~20페이지 |

### 좋은 보고서의 특징

| 특징 | 설명 | 나쁜 예 | 좋은 예 |
|------|------|--------|--------|
| **명확성** | 전문 용어를 설명 | "SQLi로 auth bypass됨" | "SQL Injection으로 로그인 인증이 우회되어 관리자 접근 가능" |
| **구조화** | 일관된 형식 | 서술형 나열 | 섹션별 체계적 구성 |
| **증거 기반** | 주장에 증거 첨부 | "취약함" | "Apache 2.4.52 → CVE-2023-XXXX (CVSS 9.1)" |
| **실행 가능** | 구체적 개선 방안 | "보안 강화 필요" | "SSH PasswordAuth를 no로 변경 (sshd_config 12행)" |

## 1.2 보고서 구조

### 표준 보안 보고서 구조

```
[보안 보고서 표준 구조]

1. 표지
   - 제목, 작성자, 날짜, 기밀 등급

2. 경영진 요약 (Executive Summary)
   - 1페이지, 비기술적 언어
   - 핵심 발견, 위험 수준, 권고 사항

3. 범위 및 방법론 (Scope & Methodology)
   - 평가 대상, 기간, 방법, 도구
   - 제한 사항

4. 발견 사항 (Findings)
   - 심각도별 분류 (Critical → Low)
   - 각 발견: 설명, 증거, 영향, 권고

5. ATT&CK 매핑
   - 사용된 기법, 탐지 여부, 갭

6. 타임라인 (Timeline)
   - 시간순 활동 기록

7. 통계 및 지표 (Metrics)
   - 탐지율, 대응 시간, 서비스 가용성

8. 교훈 (Lessons Learned)
   - 성공 요인, 실패 요인, 개선 사항

9. 개선 권고 (Recommendations)
   - 단기(즉시), 중기(1~3개월), 장기(3~6개월)

10. 부록 (Appendix)
    - 상세 로그, 스크린샷, 설정 파일
```

### 심각도 분류 기준

| 심각도 | CVSS | 설명 | 색상 |
|--------|------|------|------|
| **Critical** | 9.0~10.0 | 즉시 악용 가능, 원격 코드 실행 | 빨강 |
| **High** | 7.0~8.9 | 권한 상승, 데이터 접근 | 주황 |
| **Medium** | 4.0~6.9 | 정보 노출, 제한적 영향 | 노랑 |
| **Low** | 0.1~3.9 | 정보성, 모범 사례 미준수 | 파랑 |
| **Info** | 0 | 참고 사항 | 회색 |

## 1.3 통계 및 지표(Metrics)

### 핵심 성과 지표(KPI)

| 지표 | 정의 | 목표 | 측정 방법 |
|------|------|------|---------|
| **MTTD** | Mean Time To Detect (평균 탐지 시간) | < 5분 | 공격시작~탐지 시간 |
| **MTTR** | Mean Time To Respond (평균 대응 시간) | < 15분 | 탐지~차단 시간 |
| **탐지율** | 탐지된 공격 / 전체 공격 | > 80% | IDS + 로그 분석 |
| **오탐률** | 거짓 알림 / 전체 알림 | < 10% | 알림 분석 |
| **가용성** | 서비스 정상 운영 비율 | > 99% | 모니터링 |
| **복구 시간** | 침해 ~ 서비스 정상화 | < 30분 | 인시던트 기록 |

### 통계 시각화 형태

```
[탐지율 그래프 예시]

공격 기법별 탐지율:
Port Scan     ████████████████████ 100%
SSH BF        ████████████████████ 100%
SQLi          ████████            40%
SSH Pivot     ██████████████      70%
Data Exfil    ████████████        60%
Persistence   ██████              30%
------------------------------------
전체           ████████████        60%
```

## 1.4 교훈 도출 방법론

### After Action Review (AAR) 프레임워크

| 질문 | 목적 | 예시 |
|------|------|------|
| **무엇을 하려 했는가?** | 목표 확인 | "모든 침투 시도를 10분 내 탐지" |
| **실제로 무엇이 일어났는가?** | 현실 확인 | "SQLi 탐지에 20분 소요, SSH BF는 3분 내 탐지" |
| **왜 차이가 발생했는가?** | 원인 분석 | "웹 로그 분석 자동화 부재, IDS 웹 룰 부족" |
| **무엇을 개선할 것인가?** | 개선 계획 | "ModSecurity WAF 도입, access.log 자동 분석" |

---

# Part 2: 로그 분석 방법론 + 통계 기법 (30분)

## 2.1 로그 분석 파이프라인

```
[로그 분석 단계]

1. 수집 (Collection)
   +-- 서버별 로그 원격 수집
   +-- 시간 동기화 확인
   +-- 해시 기록 (무결성)

2. 정규화 (Normalization)
   +-- 시간 형식 통일 (ISO 8601)
   +-- IP/사용자 표준화
   +-- 이벤트 유형 분류

3. 상관분석 (Correlation)
   +-- 시간순 통합 (Timeline)
   +-- IP 기반 연결
   +-- ATT&CK 매핑

4. 통계 (Statistics)
   +-- 빈도 분석
   +-- 시간대별 분포
   +-- KPI 산출

5. 보고 (Reporting)
   +-- 요약 통계
   +-- 주요 발견
   +-- 개선 권고
```

## 2.2 로그 소스별 분석 포인트

| 로그 소스 | 경로 | 분석 포인트 | 핵심 패턴 |
|---------|------|-----------|---------|
| auth.log | `/var/log/auth.log` | SSH 인증 | Failed/Accepted |
| access.log | `/var/log/apache2/access.log` | HTTP 요청 | 상태코드, 메서드, URI |
| syslog | `/var/log/syslog` | 시스템 이벤트 | 서비스 시작/중지, 오류 |
| Suricata | `/var/log/suricata/fast.log` | IDS 알림 | ET SCAN, EXPLOIT, TROJAN |
| Wazuh | `/var/ossec/logs/alerts/` | 통합 알림 | Rule ID, Level |
| nftables | `dmesg` (커널 로그) | 방화벽 이벤트 | NFT DROP/ACCEPT |

---

# Part 3: 로그 수집 + 통계 분석 실습 (40분)

## 실습 3.1: 전체 인프라 로그 수집

### Step 1: 멀티 호스트 로그 원격 수집

> **실습 목적**: 공방전에서 생성된 모든 로그를 중앙으로 수집하여 통합 분석 기반을 마련한다.
>
> **배우는 것**: 멀티 호스트 로그 수집, 해시 기록, 수집 자동화

```bash
# 로그 수집 디렉토리 생성
LOGDIR="/tmp/battle_logs_$(date +%Y%m%d)"
mkdir -p "$LOGDIR"/{web,secu,siem}
echo "로그 수집 디렉토리: $LOGDIR"

# web 서버 로그 수집
echo "[수집] web 서버 로그"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /var/log/auth.log 2>/dev/null" > "$LOGDIR/web/auth.log"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /var/log/apache2/access.log 2>/dev/null" > "$LOGDIR/web/access.log"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /var/log/syslog 2>/dev/null" > "$LOGDIR/web/syslog"
echo "  auth.log: $(wc -l < "$LOGDIR/web/auth.log") lines"
echo "  access.log: $(wc -l < "$LOGDIR/web/access.log") lines"

# secu 서버 로그 수집
echo "[수집] secu 서버 로그"
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "cat /var/log/suricata/fast.log 2>/dev/null" > "$LOGDIR/secu/suricata.log"
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "cat /var/log/auth.log 2>/dev/null" > "$LOGDIR/secu/auth.log"
echo "  suricata: $(wc -l < "$LOGDIR/secu/suricata.log") lines"

# siem 서버 로그 수집
echo "[수집] siem 서버 로그"
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "cat /var/log/auth.log 2>/dev/null" > "$LOGDIR/siem/auth.log" 2>/dev/null
echo "  auth.log: $(wc -l < "$LOGDIR/siem/auth.log") lines"

# 해시 매니페스트 생성
echo "=== 수집 로그 해시 ===" > "$LOGDIR/manifest.sha256"
find "$LOGDIR" -type f -name "*.log" -exec sha256sum {} \; >> "$LOGDIR/manifest.sha256"
echo ""
echo "[해시 매니페스트]"
cat "$LOGDIR/manifest.sha256"
```

> **결과 해석**:
> - 모든 서버의 핵심 로그를 중앙 디렉토리에 수집했다
> - SHA-256 해시로 로그의 무결성을 보장한다
> - line 수로 로그의 크기를 파악할 수 있다
>
> **실전 활용**: 분석은 반드시 수집된 사본에서 수행한다. 원본 서버의 로그를 직접 분석하면 증거가 훼손될 수 있다.
>
> **명령어 해설**:
> - `find ... -exec sha256sum {} \;`: 모든 로그 파일의 해시를 일괄 계산
>
> **트러블슈팅**:
> - 로그가 비어 있는 경우: logrotate로 아카이브됨 → `.1`, `.gz` 파일도 수집

### Step 2: 통계 분석

> **실습 목적**: 수집한 로그에서 공방전 활동의 통계를 산출한다.
>
> **배우는 것**: grep/awk를 이용한 로그 통계, KPI 계산

```bash
LOGDIR="/tmp/battle_logs_$(date +%Y%m%d)"

echo "================================================="
echo "  공방전 통계 분석"
echo "  분석 일시: $(date)"
echo "================================================="

# 1. SSH 통계
echo ""
echo "[1] SSH 인증 통계 (web 서버)"
TOTAL_FAIL=$(grep -c "Failed password" "$LOGDIR/web/auth.log" 2>/dev/null || echo 0)
TOTAL_SUCCESS=$(grep -c "Accepted" "$LOGDIR/web/auth.log" 2>/dev/null || echo 0)
echo "  실패한 인증: ${TOTAL_FAIL}건"
echo "  성공한 인증: ${TOTAL_SUCCESS}건"
echo "  브루트포스 비율: $([ "$TOTAL_FAIL" -gt 0 ] && echo "$(( TOTAL_FAIL * 100 / (TOTAL_FAIL + TOTAL_SUCCESS + 1) ))%" || echo "N/A")"

echo ""
echo "  소스 IP별 실패 횟수:"
grep "Failed password" "$LOGDIR/web/auth.log" 2>/dev/null | \
  grep -oP 'from \K[\d.]+' | sort | uniq -c | sort -rn | head -5 | \
  while read count ip; do echo "    $ip: ${count}회"; done

# 2. 웹 요청 통계
echo ""
echo "[2] HTTP 요청 통계 (web 서버)"
TOTAL_REQ=$(wc -l < "$LOGDIR/web/access.log" 2>/dev/null || echo 0)
echo "  총 요청: ${TOTAL_REQ}건"
echo "  상태코드 분포:"
awk '{print $9}' "$LOGDIR/web/access.log" 2>/dev/null | \
  sort | uniq -c | sort -rn | head -5 | \
  while read count code; do echo "    HTTP $code: ${count}건"; done

echo ""
echo "  의심 요청 (SQLi/XSS 패턴):"
SQLI=$(grep -ciE "union|select|insert|drop|script|alert|eval" "$LOGDIR/web/access.log" 2>/dev/null || echo 0)
echo "    SQLi/XSS 패턴: ${SQLI}건"

# 3. IDS 통계
echo ""
echo "[3] IDS 알림 통계 (secu 서버)"
TOTAL_IDS=$(wc -l < "$LOGDIR/secu/suricata.log" 2>/dev/null || echo 0)
echo "  총 알림: ${TOTAL_IDS}건"
echo "  알림 유형별:"
grep -oP '\[\*\*\] \[\S+\] \K[^\[]+' "$LOGDIR/secu/suricata.log" 2>/dev/null | \
  sort | uniq -c | sort -rn | head -5 | \
  while read count alert; do echo "    $alert: ${count}건"; done

# 4. KPI 요약
echo ""
echo "[4] KPI 요약"
echo "  MTTD (평균 탐지 시간):  추정 3~5분"
echo "  MTTR (평균 대응 시간):  추정 10~15분"
echo "  탐지율:               추정 50~70%"
echo "  서비스 가용성:         확인 필요"

echo ""
echo "================================================="
echo "  분석 완료"
echo "================================================="
```

> **결과 해석**:
> - SSH 실패 횟수가 높으면 브루트포스 공격이 있었다
> - HTTP 404가 많으면 디렉토리 스캔, SQLi 패턴이 있으면 웹 공격 시도
> - IDS 알림 수와 유형으로 탐지 효과를 평가한다
>
> **실전 활용**: 이 통계는 보고서의 "Metrics" 섹션에 직접 사용된다. 정량적 데이터가 있으면 보고서의 신뢰도가 높아진다.
>
> **명령어 해설**:
> - `grep -oP 'from \K[\d.]+'`: Perl 정규식으로 "from" 뒤의 IP만 추출
> - `awk '{print $9}'`: access.log의 9번째 필드 (HTTP 상태 코드)
> - `sort | uniq -c | sort -rn`: 빈도 카운트 후 내림차순 정렬
>
> **트러블슈팅**:
> - grep 결과가 0인 경우: 로그 형식이 예상과 다를 수 있음 → `head -5`로 형식 확인
> - 통계가 비현실적인 경우: 로그 기간을 확인 (공방전 시간대만 필터링)

## 실습 3.2: ATT&CK 매핑 + 갭 분석

### Step 1: ATT&CK 매핑 표 작성

> **실습 목적**: 로그 분석 결과를 MITRE ATT&CK에 매핑하여 공격-탐지 갭을 식별한다.
>
> **배우는 것**: ATT&CK 기반 갭 분석, 탐지 커버리지 평가

```bash
cat << 'MAPPING'
=== ATT&CK 매핑 및 갭 분석 ===

전술              기법                     사용 여부  탐지 여부  갭
------------------------------------------------------------------
TA0043 Recon      T1595 Active Scanning    O         O (IDS)    -
TA0043 Recon      T1592 Gather Host Info   O         X          GAP
TA0001 Access     T1190 Exploit Public App O         X          GAP
TA0001 Access     T1110 Brute Force        O         O (auth)   -
TA0002 Execution  T1059.004 Unix Shell     O         X          GAP
TA0003 Persist    T1136 Local Account      O         ?          PARTIAL
TA0003 Persist    T1053 Scheduled Task     O         ?          PARTIAL
TA0004 PrivEsc    T1548 Abuse SUID         O         X          GAP
TA0005 Evasion    T1070 Indicator Removal  O         X          GAP
TA0006 Credential T1552 Unsecured Creds    O         X          GAP
TA0007 Discovery  T1046 Network Scan       O         O (IDS)    -
TA0008 Lateral    T1021 Remote Services    O         O (auth)   -
TA0009 Collection T1005 Local Data         O         X          GAP
TA0010 Exfil      T1041 Exfil Over C2      O         O (fw)     -

요약:
  사용된 기법: 14개
  탐지된 기법: 5개
  부분 탐지:   2개
  미탐지 (GAP): 7개
  탐지 커버리지: 36% (5/14)

우선 개선 대상 (GAP):
  1. T1190 웹 공격 탐지   → WAF 도입 권장
  2. T1059 셸 실행 탐지    → auditd 설정 권장
  3. T1548 권한 상승 탐지   → SUID 모니터링 권장
  4. T1005 데이터 수집 탐지 → 파일 접근 감사 권장
MAPPING
```

> **결과 해석**:
> - 탐지 커버리지 36%는 상당히 낮다. 실제 기업에서도 이 수준인 경우가 많다
> - 네트워크 수준(IDS, 방화벽)의 탐지는 양호하지만, 호스트 수준의 탐지가 부족하다
> - WAF, auditd, 파일 무결성 모니터링 도입으로 커버리지를 높일 수 있다
>
> **실전 활용**: 이 갭 분석은 보안 투자 우선순위를 결정하는 핵심 자료이다. 경영진에게 "어디에 투자해야 하는가"를 보여준다.

### Step 2: OpsClaw 통합 증적

> **실습 목적**: 전체 공방전의 증적을 OpsClaw에 통합 기록한다.
>
> **배우는 것**: OpsClaw execute-plan으로 분석 결과를 자동 기록

```bash
# 분석 프로젝트 생성
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week15-analysis","request_text":"공방전 결과 분석 및 보고서","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 분석 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"web SSH 통계","instruction_prompt":"echo \"Failed: $(grep -c Failed /var/log/auth.log 2>/dev/null || echo 0), Accepted: $(grep -c Accepted /var/log/auth.log 2>/dev/null || echo 0)\"","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"title":"web HTTP 통계","instruction_prompt":"wc -l /var/log/apache2/access.log 2>/dev/null || echo 0","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"title":"secu IDS 통계","instruction_prompt":"wc -l /var/log/suricata/fast.log 2>/dev/null || echo 0","risk_level":"low","subagent_url":"http://10.20.30.1:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:20s} -> {t[\"status\"]}')
"
```

> **결과 해석**: OpsClaw에 통계 데이터가 증적으로 기록되어 보고서 작성 시 참조할 수 있다.

---

# Part 4: 보고서 작성 실습 (30분)

## 실습 4.1: 종합 보고서 작성

### Step 1: 보고서 템플릿 기반 작성

> **실습 목적**: 실전 수준의 보안 보고서를 표준 템플릿에 맞춰 작성한다.
>
> **배우는 것**: 보고서 구조, Executive Summary 작성법, 권고 사항 작성법

```bash
cat << 'FINAL_REPORT'
=======================================================
     공방전 기초 과정 — 종합 보안 평가 보고서
=======================================================

문서 정보:
  작성일:      2026-04-03
  작성자:      [학생 이름]
  과정명:      공방전 기초 (Week 01~15)
  기밀 등급:   교육용 — 대외비

=== 1. 경영진 요약 (Executive Summary) ===

본 보고서는 15주간의 공방전 기초 과정 결과를 분석한 것이다.

주요 발견:
- 총 14개 ATT&CK 기법이 사용되었으며, 탐지 커버리지는 36%
- 네트워크 수준 탐지(IDS, 방화벽)는 양호하나 호스트 수준 탐지가 미흡
- 평균 침투 탐지 시간(MTTD) 3~5분, 대응 시간(MTTR) 10~15분
- SSH 브루트포스 100% 탐지, 웹 공격(SQLi) 0% 탐지

위험 평가:
- HIGH: 웹 애플리케이션 취약점 (SQLi, XSS)으로 인한 데이터 유출 가능
- HIGH: 약한 SSH 비밀번호로 인한 무단 접근 가능
- MEDIUM: 횡적 이동 탐지 부족으로 내부 확산 가능
- LOW: 불필요 서비스 노출

권고 요약:
- [긴급] SSH 비밀번호 인증 비활성화 → 키 기반 인증 전환
- [단기] WAF 도입으로 웹 공격 탐지 강화
- [중기] auditd + 파일 무결성 모니터링 도입
- [장기] SOC 자동화 및 SOAR 플랫폼 도입

=== 2. 범위 및 방법론 ===

평가 대상:
  - secu (10.20.30.1): 네트워크 보안 장비 (nftables, Suricata)
  - web  (10.20.30.80): 웹 서버 (Apache, JuiceShop)
  - siem (10.20.30.100): SIEM (Wazuh 4.11.2)
  - opsclaw (10.20.30.201): 관리 플랫폼

평가 기간: Week 11~14 (4주, 각 3시간)
방법론: MITRE ATT&CK 기반 Red Team/Blue Team 평가
도구: nmap, curl, hydra, Suricata, nftables, OpsClaw
제한사항: 교육 환경, 실제 악성코드 미사용

=== 3. 발견 사항 ===

[Critical] 웹 애플리케이션 SQL Injection
  설명: JuiceShop(3000) 로그인에서 SQLi로 인증 우회 가능
  증거: curl -X POST .../login -d '{"email":"' OR 1=1--",...}' → 200 OK
  영향: 전체 사용자 데이터 유출, 관리자 권한 탈취
  ATT&CK: T1190 Exploit Public-Facing Application
  권고: 파라미터화된 쿼리 사용, WAF 도입, 입력 검증 강화

[High] SSH 약한 비밀번호
  설명: web 서버 SSH 비밀번호가 단순 ("1")
  증거: sshpass -p1 ssh web@10.20.30.80 → 접속 성공
  영향: 무단 시스템 접근, 데이터 접근, 횡적 이동 가능
  ATT&CK: T1110 Brute Force, T1078 Valid Accounts
  권고: 강력한 비밀번호 정책, 키 기반 인증 전환, fail2ban 도입

[Medium] 횡적 이동 가능
  설명: web 서버에서 siem/secu로 SSH 피벗 가능
  증거: web에서 sshpass -p1 ssh siem@10.20.30.100 → 접속 성공
  영향: 내부 네트워크 전체 침해 가능
  ATT&CK: T1021.004 Remote Services: SSH
  권고: 내부 SSH 접근 제한 (방화벽), 서버별 고유 자격증명

[Low] 불필요 서비스 노출
  설명: SubAgent API(8002)가 외부에서 접근 가능
  증거: nmap 스캔 결과 8002/tcp open
  영향: API 공격 벡터 제공
  ATT&CK: T1190
  권고: 방화벽에서 8002 포트 외부 접근 차단

=== 4. 통계 요약 ===

  SSH 실패 인증:     [통계에서 확인]건
  SQLi 시도:         [통계에서 확인]건
  IDS 알림 총 수:    [통계에서 확인]건
  탐지 커버리지:     36% (5/14 기법)
  MTTD:             3~5분 (목표: <5분)
  MTTR:             10~15분 (목표: <15분)
  서비스 가용성:     >95% (목표: >99%)

=== 5. 개선 권고 로드맵 ===

[단기 — 즉시~2주]
  1. SSH 비밀번호 인증 비활성화
  2. 비밀번호 정책 강화 (12자 이상, 복잡도)
  3. 불필요 포트 방화벽 차단

[중기 — 1~3개월]
  1. WAF 도입 (ModSecurity 또는 BunkerWeb 강화)
  2. auditd 설정 (파일 접근, 명령 실행 감사)
  3. fail2ban 설치 (SSH 자동 차단)
  4. 내부 SSH 접근 제한

[장기 — 3~6개월]
  1. SOC 자동화 (알림→분석→대응 자동화)
  2. SOAR 플랫폼 도입
  3. 정기 Red Team 훈련 (분기별)
  4. 보안 인식 교육 프로그램

=== 6. 부록 ===

  A. 상세 타임라인 (Week 11~14)
  B. nmap 스캔 결과 파일
  C. 로그 해시 매니페스트
  D. ATT&CK Navigator 매핑
  E. OpsClaw 프로젝트 ID 목록
FINAL_REPORT
```

> **실전 활용**: 이 보고서 구조는 실제 침투 테스트(Pentest) 보고서, SOC 평가 보고서, 인시던트 사후 보고서에 모두 적용할 수 있다. 구조화된 보고서는 독자가 빠르게 핵심을 파악하고 의사결정할 수 있게 한다.

### Step 2: OpsClaw 최종 보고서

> **실습 목적**: 과정 전체의 결과를 OpsClaw에 최종 기록한다.
>
> **배우는 것**: 과정 전체의 증적 통합 관리

```bash
curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "공방전 기초 과정 최종 보고서 — 15주 결과 분석 및 보안 평가",
    "outcome": "success",
    "work_details": [
      "로그 수집: web/secu/siem 전체 인프라 로그 중앙 수집 + SHA-256 해시",
      "통계 분석: SSH 인증, HTTP 요청, IDS 알림 통계 산출",
      "ATT&CK 매핑: 14개 기법 사용, 5개 탐지 → 커버리지 36%",
      "갭 분석: 웹 공격/권한 상승/데이터 수집 탐지 부족 식별",
      "보고서: Executive Summary + 발견사항 + 통계 + 개선 로드맵",
      "개선 권고: 단기(SSH강화), 중기(WAF/auditd), 장기(SOC자동화)"
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'최종 보고서: {d.get(\"status\",\"ok\")}')"
```

---

## 검증 체크리스트
- [ ] 전체 인프라의 로그를 중앙으로 수집하고 해시를 기록할 수 있는가
- [ ] grep/awk를 이용하여 로그에서 통계를 산출할 수 있는가
- [ ] SSH, HTTP, IDS 로그에서 공격 패턴을 식별하고 정량화할 수 있는가
- [ ] MTTD, MTTR 등 핵심 KPI를 계산할 수 있는가
- [ ] MITRE ATT&CK에 기법을 매핑하고 탐지 갭을 분석할 수 있는가
- [ ] 경영진 요약(Executive Summary)을 비기술적 언어로 작성할 수 있는가
- [ ] 발견 사항을 심각도별로 분류하고 증거와 권고를 포함하여 작성할 수 있는가
- [ ] 단기/중기/장기 개선 로드맵을 수립할 수 있는가
- [ ] OpsClaw를 이용하여 전체 증적을 통합 관리할 수 있는가

## 자가 점검 퀴즈

1. 경영진 요약(Executive Summary)에 반드시 포함해야 할 요소 5가지를 나열하라.

2. MTTD와 MTTR의 정의를 설명하고, 각각을 단축하기 위한 방법 2가지를 제시하라.

3. ATT&CK 갭 분석에서 "탐지 커버리지 36%"의 의미와 이를 개선하는 방법을 설명하라.

4. 보안 보고서에서 발견 사항(Finding)의 표준 구성 요소 5가지를 나열하라.

5. 경영진 보고서와 기술 보고서의 차이를 대상 독자, 내용, 분량 관점에서 설명하라.

6. 로그 분석에서 "상관분석(Correlation)"이란 무엇이며, 왜 중요한지 설명하라.

7. After Action Review(AAR)의 4가지 질문과 각 질문의 목적을 설명하라.

8. 보고서에서 "증거 기반(Evidence-based)"이 중요한 이유를 설명하라.

9. 개선 권고를 "단기/중기/장기"로 나누는 이유와 각 기간의 기준을 설명하라.

10. 15주간의 공방전 과정에서 가장 중요한 교훈 3가지를 선정하고 그 이유를 설명하라.

## 과제

### 과제 1: 최종 보고서 제출 (필수)
- 본 강의의 보고서 템플릿을 기반으로 최종 보고서를 작성하라
- 경영진 요약 (1페이지), 발견 사항 (최소 4개, 심각도별), ATT&CK 매핑, 통계, 교훈, 개선 권고를 포함
- 실제 수행한 공방전(Week 11~14)의 데이터를 활용
- 분량: 10페이지 이상
- 제출 형식: PDF 또는 Markdown

### 과제 2: 자동화 분석 스크립트 (선택)
- 로그 수집 → 통계 분석 → 보고서 생성을 자동화하는 bash 스크립트 작성
- 입력: 서버 IP 목록, 분석 기간
- 출력: 통계 요약, ATT&CK 매핑, Markdown 보고서
- SHA-256 해시 자동 기록 기능 포함

### 과제 3: 15주 과정 회고 (필수)
- 과정 전체에서 배운 가장 중요한 기술 3가지
- 가장 어려웠던 주차와 그 이유
- 실무에서 활용할 계획
- 과정에 대한 건설적 피드백
- 분량: 500자 이상

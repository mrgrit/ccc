# Week 08 — 중간고사 — 방화벽 + IPS + WAF + 호스트 가시화 종합 실기

> 1~7주차 (보안 솔루션 5종 + 호스트 가시화) 의 종합 평가. 시험 시간 90분.
> 본인 PC 에서 6v6 인프라 (192.168.0.110) 의 4 컨테이너 (fw / ips / web / bastion)
> 에 SSH 접속 후 5개 시나리오 (각 20점, 총 100점) 를 수행한다.

## 시험 규칙

- 시간: 90분 (정시 종료, 5분 전 카운트다운)
- 개인 PC + 인터넷 검색 허용 (단, AI 어시스턴트 / 다른 학생과 communication 금지)
- 본인 작업 결과 (명령 + 출력) 를 1페이지 PDF 로 제출
- 시험 후 30분 내 본인 컨테이너 환경 정리 (추가한 룰 제거, file 복구)

## 환경 전제

- 모든 학생이 동일 VM (192.168.0.110) 의 6v6 인프라 사용 — 변경 시 다른 학생에 영향
  → 시험 전 강사가 별도 학생용 컨테이너 셋업 또는 학생 PC 에 6v6 로컬 설치 권장
- 비밀번호: ccc / sudo NOPASSWD

---

## 시나리오 1 (20점) — fw nftables 정책

**문항**: 6v6-fw 의 nftables 의 inet six_filter input chain 의 가장 위 (position 0) 에
다음 룰을 추가하라.

> attacker (10.20.30.202) 의 80/tcp 접근만 drop, 다른 src 는 정상 통과.

**제출**: 룰 추가 명령 + 검증 명령 (curl 두 번 — attacker 와 다른 host 에서) + counter
검증 + 룰 삭제 cleanup.

**평가 기준** (각 5점):
- 룰 추가 정확도 (10.20.30.202 만 drop, 80/tcp 만)
- 검증 출력 (attacker timeout + 다른 host 200)
- counter packets > 0
- 룰 삭제 + 정상 복귀 검증

---

## 시나리오 2 (20점) — Suricata 룰 작성

**문항**: 6v6-ips 의 local.rules 에 다음 alert 룰 추가 + 트리거 + eve.json 검증.

> HTTP URI 에 `' OR '1'='1` SQLi 패턴이 포함된 요청 매치. sid 9008001, classtype
> web-application-attack, threshold 60초 1번.

**제출**: 룰 한 줄 + reload 명령 + 트리거 curl + alert eve.json + 룰 삭제.

**평가 기준** (각 5점):
- 룰 syntax 정확 + reload-rules OK
- 트리거 성공 (alert 발생)
- 정확한 sid + classtype + threshold
- cleanup (룰 삭제 후 미발생 검증)

---

## 시나리오 3 (20점) — ModSecurity 공격 시뮬레이션

**문항**: 6v6-attacker 에서 3 가지 공격 (XSS / SQLi / LFI) 페이로드를 작성하여 ModSec
가 모두 403 차단하는지 확인. 각 공격의 audit log 에서 매치된 룰 ID 추출.

**제출**: 3 curl 명령 + 응답 코드 + audit log 의 transaction.messages 에서 매치 룰 ID.

**평가 기준** (각 5점):
- 3 페이로드 작성 정확
- 3 차단 모두 403
- 매치 룰 ID 정확 추출 (941xxx / 942xxx / 930xxx)
- audit log jq 분석 가능

---

## 시나리오 4 (20점) — osquery 헌팅

**문항**: 6v6-web 에서 다음 4 헌팅 쿼리를 SQL 로 작성·실행:

1. `on_disk = 0` 인 process
2. uid >= 1000 인 사용자
3. listening_ports + processes JOIN → 22/80/443 매핑
4. SUID binary 중 path 가 /usr/bin 이 아닌 것

**제출**: 4 SQL + 4 출력 + 정상 baseline 분석 (예상 vs 실제 차이).

**평가 기준** (각 5점):
- SQL syntax 정확
- 결과 정확 (정상 baseline 매치)
- JOIN 쿼리 정확
- 분석 (정상 vs 의심 판단)

---

## 시나리오 5 (20점) — 통합 시나리오 — 침해 1 사이클

**문항**: 다음 침해 시나리오의 detection 도구 + 분석 순서 작성.

> "attacker (10.20.30.202) 에서 sqlmap (UA: sqlmap) 으로 juice.6v6.lab 의 /search
> endpoint 에 UNION SELECT 페이로드 발송 → ModSec 차단 → 그래도 4번 reconnaissance
> 시도 → Suricata 알람 → 운영자 인지"

**제출**:
1. fw / ips / web / Wazuh manager 에서 각각 어떤 로그·alert 가 생성되는가?
2. 각 도구의 정확한 명령 (kron / grep / jq) 으로 추출
3. 침해 분석 timeline 작성 (5+ event 시간순)

**평가 기준** (각 5점):
- 각 도구 로그 위치 정확
- 명령 syntax 정확
- timeline 의 순서 (Suricata flow → http → alert / ModSec audit / Wazuh alert)
- 운영자 조치 권장 (rate-limit / IP block / 추가 모니터링)

---

## 채점 및 결과

- 90점 이상 : A (W09 부터 advanced track 옵션)
- 70~89 : B
- 50~69 : C (재시험 또는 W09 으로 통과)
- 50 미만 : F (W01-W07 재학습 + 재시험)

총평은 1주일 안에 lecture-portal 의 grade 페이지에 게시.

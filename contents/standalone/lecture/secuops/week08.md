# Week 08 — 중간고사 — W01-W07 통합 시험 + R/B/P 종합 + 보고서

> **본 주차의 한 줄 요약**
>
> W01-W07 의 7 주차 학습을 **5 단계 종합 시험** (각 20점, 총 100점, 180분) 으로 통합 평가.
> ① 6v6 4-tier 인프라 baseline (W01) → ② fw nftables NAT + HAProxy 협업 (W02-W03) →
> ③ Suricata IDS + 룰 작성 + R/B/P (W04-W05) → ④ ModSec WAF + CRS audit + anomaly score
> (W06) → ⑤ osquery 호스트 가시화 + FIM + 침해 헌팅 (W07). 각 단계는 실측 + 분석 +
> 운영 권장 3 축으로 평가.
>
> **시험 의도**: 학생이 7 주차 학습을 단편적이 아니라 **하나의 운영 cycle** 로 통합 할 수
> 있는지 평가. 각 도구의 단독 사용이 아니라 R/B/P 의 상호 보완 + 운영 audit + cleanup
> 1 cycle 완성도가 핵심.

---

## 1. 시험 개요

| 항목 | 내용 |
|------|------|
| 시간 | 180 분 (3시간) |
| 만점 | 100 점 (5 단계 × 20점) |
| 합격선 | 60 점 |
| 형식 | 실 6v6 인프라 + 실 명령 + audit log 분석 + 보고서 |
| 도구 | bastion ProxyJump + 4 호스트 osquery + Wazuh agent |
| 환경 | 6v6 의 16 컨테이너 모두 가동 |
| 협업 | 개인 시험 (개별 환경 — 학생별 분리 인프라) |
| 자료 | open book (W01-W07 lecture 참조 허용) |
| 금지 | 다른 학생과 통신 / AI 어시스턴트 / 외부 chat |
| cleanup | 모든 추가/변경 cleanup 필수 (감점 사유) |

---

## 2. 5 단계 구성

### 단계 1 (20점) — 인프라 baseline (W01)

**학습 목표**: 6v6 의 4-tier (ext/pipe/dmz/int) + 16 컨테이너 + 11 vhost + ProxyJump
모델을 30초 안에 가시화.

**과제 4 항목**:
1. (5점) bastion 진입 + 16 컨테이너 `Up` 확인 + 컨테이너 수 정확히 표시
2. (5점) fw 의 dual NIC (ext .1 + pipe .1) + ips 의 dual NIC (pipe .2 + dmz .1) 확인
3. (5점) HAProxy 11 vhost 의 host header → backend 매핑 표 작성 (juice / dvwa / siem /
   portal / bastion / 기타 6)
4. (5점) ProxyJump 로 4 호스트 (fw / ips / web / siem) hostname 출력

### 단계 2 (20점) — fw nftables NAT + HAProxy 협업 (W02-W03)

**학습 목표**: nftables 의 inet six_filter + ip six_nat 분리 + Docker `table ip nat`
공존 + HAProxy + DNAT 충돌 + conntrack reply src 검증.

**과제 4 항목**:
1. (5점) 3 table (Docker ip nat / inet six_filter / ip six_nat) 가시화 + priority
2. (5점) DNAT 외부 8888 → web 80 추가 + conntrack 의 양방향 변환 + cleanup 1 cycle
3. (7점) **R/B/P** — HAProxy + DNAT 80 충돌 시뮬 + conntrack reply src 변화로 우회 증거
   (10.20.30.1 → 10.20.32.80) + cleanup
4. (3점) 5 운영 위험 (HAProxy termination / host header / 가시성 / ACL / TLS) 중 3 가시화
   증거 보고서

### 단계 3 (20점) — Suricata IDS + 룰 작성 (W04-W05)

**학습 목표**: Suricata 6.0.4 + autofp + cluster_flow + 65,898 룰 + eve.json 8 type +
flowbits 다단계 + threshold rate-limit.

**과제 4 항목**:
1. (5점) Suricata 데몬 + 두 NIC (eth0/eth1) sniff + dump-counters 의 drop_rate < 0.01%
2. (5점) 새 alert 룰 (sid 9008001 sqlmap UA) 작성 + reload + 트리거 + eve.json 검증
3. (5점) flowbits 다단계 룰 (sid 9008002/9008003) — FlowbitTest UA + /admin 접근 →
   step2 alert
4. (5점) **R/B/P** — 5 burst → 양 NIC 10 alert → threshold 룰 권장 시뮬

### 단계 4 (20점) — ModSec WAF + CRS audit (W06)

**학습 목표**: Apache + mod_security2 + CRS 3.3.2 + audit log JSON + anomaly score 누적
+ exception 작성.

**과제 4 항목**:
1. (5점) 5 공격 (XSS / SQLi / LFI / RCE / PHP) 모두 403 차단 검증
2. (5점) audit log 의 messages[] 정규식 추출 + 카테고리 분포 (941+942+930+932+933 +
   949+980)
3. (5점) 980130 correlation summary (`SQLI=X,XSS=Y,RFI=Z,LFI=W,RCE=V,PHPI=U`) 추출 +
   anomaly score 분석
4. (5점) X-Forwarded-For vs remote_address 차이 가시화 (10.20.32.1 ips MASQ vs
   10.20.30.202 attacker)

### 단계 5 (20점) — osquery 호스트 가시화 + 침해 헌팅 (W07)

**학습 목표**: osquery 5.23.0 + 158 테이블 + 6 핵심 + SQL JOIN + 헌팅 10 + FIM + R/B/P.

**과제 4 항목**:
1. (5점) 4 호스트 osquery 5.23.0 + 158 테이블 baseline
2. (5점) SQL JOIN — listening_ports + processes (port-process)
3. (7점) **R/B/P** — 새 user (uid 1099) / SSH key (FAKEKEY) / cron (w08_backdoor) 침해
   시뮬 + 5 osquery 헌팅 매치 + cleanup
4. (3점) FIM osquery.conf 시뮬 (4 카테고리 + schedule.file_changes interval 60)

---

## 3. 평가 기준

각 단계 20 점 = 정확도 10 + 분석 5 + 운영 권장 5.

| 단계 | 정확도 (10) | 분석 (5) | 운영 권장 (5) |
|------|------------|----------|---------------|
| 1 인프라 baseline | 16 컨테이너 + vhost 표 + ProxyJump | NIC dual / 운영 트래픽 흐름 | 운영 인수 30초 cheat sheet |
| 2 fw NAT/HAProxy | 3 table + DNAT + conntrack | conntrack reply src 변화 | 5 운영 위험 / 한 port = 한 도구 |
| 3 Suricata | 데몬 + drop_rate + 새 룰 + reload | 양 NIC effect + flowbits | threshold/suppression 권장 |
| 4 ModSec | 5/5 403 + audit messages | anomaly score + 980130 summary | exception 좁은 범위 / git audit |
| 5 osquery | 4 호스트 + 6 테이블 + JOIN | R/B/P 침해 + 5 헌팅 + cleanup | FIM + scheduled + Wazuh ship |

**감점 사유** (각 -5점):
- cleanup 누락 (실험 후 룰 / 사용자 / 파일 잔존)
- audit log 분석 누락 (5 공격 후 messages[] 추출 안 함)
- R/B/P 의 1 단계 누락 (Red / Blue / Purple 중 하나 안 함)
- 자료 형식 누락 (보고서 5 섹션 중 하나 빠짐)
- 시간 초과 (각 단계 권장 시간 + 10분 초과 시)

---

## 4. 시험 진행 순서 (180 분 권장 배분)

| 시간 | 단계 | 활동 |
|------|------|------|
| 0–30  | 1 | 인프라 baseline 점검 + 16 컨테이너 + 11 vhost + 4 ProxyJump |
| 30–60 | 2 | fw NAT/HAProxy R/B/P + 충돌 + cleanup |
| 60–95 | 3 | Suricata 데몬 + 새 룰 + flowbits + R/B/P |
| 95–130 | 4 | ModSec 5 공격 + audit + 980130 + XFF |
| 130–170 | 5 | osquery 침해 시뮬 + 5 헌팅 + cleanup + FIM 시뮬 |
| 170–180 | 보고서 | 5 단계 종합 1페이지 |

---

## 5. 보고서 형식 (제출용)

```markdown
# 6v6 W08 중간고사 — 학번, 이름

## 단계 1 (20점) — 인프라 baseline
**실측 결과**:
- 16 컨테이너 `Up` (bastion + attacker + fw + ips + web + siem + 2 wazuh + portal + 7 vuln)
- fw NIC: 6v6-ext 10.20.30.1 / 6v6-pipe 10.20.31.1
- ips NIC: 6v6-pipe 10.20.31.2 / 6v6-dmz 10.20.32.1
- 11 vhost 매핑 표 (host header → backend)
- 4 ProxyJump: fw / ips / web / siem 모두 hostname 응답

**분석**: 운영 트래픽 (siem/portal/bastion) vs 학생 트래픽 (juice 등) 의 hop 차이
**운영 권장**: 운영 인수 30초 cheat sheet — bastion 진입 → docker ps → 4 NIC 확인

## 단계 2 (20점) — fw NAT/HAProxy
**실측 결과**:
- 3 table 가시화: `ip nat` (Docker) / `inet six_filter` / `ip six_nat`
- DNAT 8888 → web 80: 응답 200, conntrack reply src = 10.20.32.80
- R/B/P 80 충돌: HAProxy 통과 reply src = 10.20.30.1, DNAT 우회 시 10.20.32.80
- nft counter packets/bytes 증가

**분석**: nat prerouting priority dstnat (-100) → HAProxy user-space bind 도달 못 함
**운영 권장**: 한 port = 한 도구, Docker `ip nat` flush 절대 금지

## 단계 3 (20점) — Suricata
**실측 결과**:
- 데몬: `suricata -i eth1 -i eth0 --runmode autofp`
- drop_rate: 0% (capture.kernel_drops 0)
- 새 룰 9008001 sqlmap UA: reload OK + alert event
- flowbits 다단계: step1 noalert (0) + step2 alert 2 (양 NIC)
- R/B/P 5 burst → 10 alert

**분석**: 양 NIC sniff 효과 (한 transaction = 2 event), severity 매핑 (priority 2 → sev 2)
**운영 권장**: threshold.config event_filter rate_filter (60s 5건) + suppression

## 단계 4 (20점) — ModSec
**실측 결과**:
- 5 공격 5/5 403:
  - XSS → 941100/941110/941160 + score 15
  - SQLi → 942100 + libinjection fingerprint
  - LFI → 930xxx
  - RCE → 932xxx
  - PHP → 933xxx
- audit messages 카테고리 분포 (top 10)
- 980130 summary: SQLI=5+, XSS=15, LFI=5, RCE=5, PHPI=5
- XFF/remote: 10.20.30.202 / 10.20.32.1

**분석**: anomaly score 누적 → threshold 5 도달 시 949110 block
**운영 권장**: SecRuleEngine On + paranoia 1 → vhost 별 2 단계 + exception LocationMatch

## 단계 5 (20점) — osquery
**실측 결과**:
- 4 호스트 5.23.0 + 158 테이블
- JOIN port-process 결과
- R/B/P 침해 3 (user fakeintruder uid 1099 / FAKEKEY / w08_backdoor)
- 5 헌팅 모두 매치 + cleanup 후 모두 0
- FIM 시뮬: 4 카테고리 + schedule interval 60

**분석**: scheduled query 자동화 시 interval 600 권장 (users / authorized_keys / crontab)
**운영 권장**: osqueryd 도입 (W10) + Wazuh ship + 분기 baseline diff

## 종합 자기 평가
- 강점: ...
- 보강: ...
- W09-W11 학습 계획: ...
```

---

## 6. 학습 권장 (시험 준비)

본 시험을 위한 준비:

1. **W01-W07 lecture 정독** — 각 주차의 §1-§15 의 흐름 + 핵심 정리 8 줄 암기
2. **lab step 직접 실행** — 모든 W01-W07 lab 의 10 step 명령 직접 실행 + 결과 캡처
3. **R/B/P 패턴 표준 흐름**:
   - Red — 가벼운 공격 시뮬
   - Blue — log/alert 추적 + 매트릭 측정
   - Purple — 분석 + 운영 권장 + cleanup
4. **audit log + eve.json + osquery JSON 정규식 파싱** — jq + grep -oE 결합
5. **cleanup 1 cycle 의 중요성** — handle 식별 + delete + 정상화 검증

---

## 7. 다음 주차 (W09) 예고

- **주제**: Wazuh manager 도입 + 11 daemon + agent 등록 + 룰·디코더
- **연결**: W04 의 Suricata eve.json + W06 의 ModSec audit + W07 의 osquery 가 모두
  W09 의 Wazuh manager 로 ship → 통합 분석
- **R/B/P 시나리오**: Red 의 공격 (XSS / SQLi) → Blue 의 manager alerts.log 통합 ingest
  → Purple 의 우선순위 룰 + Active Response

---

## 부록 A — 시험 응시 시 cheat sheet (운영 명령 정리)

```
# === 단계 1 ===
ssh 6v6-bastion 'docker ps --format "table {{.Names}}\t{{.Status}}" | head -20'
ssh 6v6-bastion 'docker inspect 6v6-fw --format "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}"'

# === 단계 2 ===
ssh 6v6-fw 'sudo nft list tables'
ssh 6v6-fw 'sudo nft add rule ip six_nat prerouting iifname "eth0" tcp dport 8888 counter dnat to 10.20.32.80:80'
ssh 6v6-fw 'sudo conntrack -L | grep "10.20.30.202" | head -1'

# === 단계 3 ===
ssh 6v6-ips 'sudo suricatasc -c version'
ssh 6v6-ips 'sudo suricatasc -c dump-counters | python3 -c "import json,sys; m=json.load(sys.stdin)[\"message\"]; print(\"drop:\",m.get(\"capture.kernel_drops\",0),\"pkts:\",m.get(\"decoder.pkts\",0))"'
# 새 룰 작성 + reload
ssh 6v6-ips 'sudo bash -c "cat > /etc/suricata/rules/local.rules <<EOF\nalert http any any -> any any (msg:\"6v6 sqlmap\"; http.user_agent; content:\"sqlmap\"; nocase; sid:9008001; rev:1;)\nEOF"'
ssh 6v6-ips 'sudo suricatasc -c reload-rules'

# === 단계 4 ===
ssh 6v6-attacker 'curl -s -o /dev/null -w "%{http_code}\n" -H "Host: juice.6v6.lab" "http://10.20.30.1/?q=<script>"'
ssh 6v6-web 'sudo tail -1 /var/log/apache2/modsec_audit.log | jq -r ".audit_data.messages[]" | grep -oE "\[id \"[0-9]+\"\]" | sort -u'

# === 단계 5 ===
ssh 6v6-web 'sudo osqueryi --json "SELECT version FROM osquery_info LIMIT 1;"'
# 침해 시뮬
ssh 6v6-web 'sudo useradd -m -u 1099 fakeintruder; sudo bash -c "echo FAKEKEY >> /root/.ssh/authorized_keys"; sudo bash -c "echo \"* * * * * root /tmp/x.sh\" > /etc/cron.d/w08_backdoor"'
# 헌팅
ssh 6v6-web 'sudo osqueryi --json "SELECT username, uid FROM users WHERE uid = 1099;"'
# cleanup
ssh 6v6-web 'sudo userdel -r fakeintruder; sudo sed -i "/FAKEKEY/d" /root/.ssh/authorized_keys; sudo rm -f /etc/cron.d/w08_backdoor'
```

## 부록 B — 시험 합격 + 도전 etiquette

```
□ 시험 시작 전 보안 자료 모두 닫기 (외부 통신 금지)
□ 매 단계 끝날 때마다 cleanup 실행 + 검증
□ audit log / eve.json / osquery JSON 결과는 보고서에 첨부 (전체가 아닌 핵심 라인)
□ 5 단계 끝나면 보고서 1페이지 작성 (위 §5 형식)
□ 자기 평가 (강점 / 보강 / 학습 계획) 포함
□ 시험 후 다른 학생과 결과 공유 금지 (다음 학기 시험 무효 가능성)
```

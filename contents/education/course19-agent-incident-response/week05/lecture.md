# Week 05: 측면이동과 지속성 — 기계 속도의 Lateral Movement

## 이번 주의 위치
w3의 정찰·w4의 익스플로잇 자동화까지 관찰한 상태에서, 공격자는 이제 **내부**로 들어와 있다(최초 접근 성공). 이번 주는 에이전트가 *내부에서* 어떻게 움직이는지, 그리고 왜 기존 측면이동 탐지 가정이 깨지는지를 다룬다. 핵심 관찰: 사람 공격자는 하나씩 시도하지만, 에이전트는 **내부 네트워크를 한 프레임에 펼쳐서 계획**하고 *병렬*로 움직인다.

## 학습 목표
- 에이전트의 측면이동 의사결정 구조를 단계적으로 설명한다
- ATT&CK *Lateral Movement*(TA0008)·*Persistence*(TA0003) 기법이 에이전트에서 어떻게 **압축**되는지 사례로 설명한다
- 사람 측면이동 대비 에이전트 측면이동의 3가지 정량 지표 차이를 제시한다
- Bastion이 측면이동을 탐지·차단할 수 있는 지점과 그 한계를 명확히 구분한다
- 실습 인프라에서 **제한된 측면이동 시나리오**(web → secu 관리 인터페이스 시도)를 학생이 관찰한다

## 전제 조건
- w4 공격 도구 자동 생성 경험
- 네트워크 기본(ARP, TCP, 기본 포트)
- SSH 키 관리 개념

## 실습 환경

같은 네트워크. 본 주차는 `web`(10.20.30.80)에 임시 *약한 자격증명*을 심어 두고, 에이전트가 해당 자격증명을 활용해 **secu 관리 인터페이스**로 이동 *시도*하는지 관찰한다. 실제 이동은 차단된다(네트워크 ACL).

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | Part 1: 측면이동의 원리와 에이전트화된 압축 | 강의 |
| 0:30-1:00 | Part 2: 지속성 메커니즘과 에이전트 | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-2:00 | Part 3: 관전 실습 — 내부 이동 시도 | 실습 |
| 2:00-2:40 | Part 4: 방어 관점에서의 탐지 지점 매핑 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | Part 5: Bastion 측면이동 탐지 스킬 설계 | 설계 |
| 3:20-3:40 | 퀴즈 + 과제 | 퀴즈 |

---

# Part 1: 측면이동의 원리와 에이전트화된 압축 (30분)

## 1.1 전통적 측면이동 라이프사이클

| 단계 | 활동 | 전통적 소요 |
|------|------|-------------|
| 발판 확보 | 웹셸·리버스 셸 | 실험 후 분 단위 |
| 내부 탐색 | `nmap`, `arp -a`, 라우팅 테이블 | 30분~2시간 |
| 자격증명 수집 | `.ssh/`, 환경변수, 브라우저 쿠키 | 수 시간 |
| 이동 시도 | 수동 SSH/SMB/RDP | 하루 단위 |
| 지속성 | cron, SSH key, systemd unit | 분 단위 |

## 1.2 에이전트화된 압축
에이전트는 위 단계들을 *하나의 계획*으로 펼친다. 실제 시간은 *요청-응답 왕복 시간 + 모델 추론 시간*의 합으로 대체로 **분 단위**다.

- 내부 탐색: `ls /home`, `cat /etc/passwd`, `getent hosts`, `/proc/net/tcp` → 몇 초
- 자격증명 수집: `find / -name '*.env'`, `.bash_history`, known_hosts → 1분
- 이동 시도: 얻어진 키/패스워드로 SSH/SMB/RDP 병렬 시도 → 2~5분

## 1.3 질적 차이 3가지

1. **전체 계획의 동시성**: 사람은 한 단계씩, 에이전트는 병렬.
2. **재평가 주기**: 실패 시 다음 가설 도출까지 초 단위.
3. **지식 통합**: *모델 내부* 리눅스·네트워크 지식이 재현 속도를 결정.

### 1.3.1 측면이동의 "병렬성"이 만드는 방어 난제

사람 공격자는 *한 번에 한 타깃*을 공략한다. 에이전트는 동일 세션에서 *여러 타깃*을 병렬로 조사한다. 이는 방어 측에서 다음 패턴으로 나타난다.

```
T+10:00  web → 10.20.30.1  TCP SYN (22)
T+10:01  web → 10.20.30.1  TCP SYN (443)
T+10:02  web → 10.20.30.100 TCP SYN (22)
T+10:03  web → 10.20.30.100 TCP SYN (443)
T+10:04  web → 10.20.30.100 TCP SYN (8080)
T+10:05  web → 10.20.30.201 TCP SYN (22)
```

5초 내 3개 호스트 6개 포트 → 사람 관리자의 *점검*이라면 이 속도가 나오기 어렵다. 이 *동시 다중 타깃* 패턴이 Bastion의 `detect_internal_scan` 스킬의 1차 입력이 된다.

### 1.3.2 "내부 지식 통합"의 현실 — 에이전트가 *이미 아는* 리눅스 경로

에이전트는 다음 경로들을 *즉시* 생각해낸다 (명령 실행 없이).

| 자격증명 관련 | 시스템 정보 | 측면이동 단서 |
|---------------|-------------|--------------|
| `~/.ssh/id_rsa` | `/etc/os-release` | `~/.ssh/known_hosts` |
| `~/.ssh/config` | `/etc/passwd` | `~/.bash_history` |
| `~/.aws/credentials` | `/proc/net/tcp` | `~/.psql_history` |
| `~/.kube/config` | `/etc/hosts` | `~/.mysql_history` |
| `~/.netrc` | `/proc/self/mountinfo` | `/var/log/lastlog` |
| `/root/.ssh/` | `ip route; ip neigh` | `/var/spool/cron/` |
| `*.env` | `uname -a; lsb_release -a` | `/var/log/wtmp` |

이 목록은 *에이전트 1턴*에 전부 병렬 시도 가능하다. 방어 관점: 이 경로들에 대한 *동시 접근*은 즉각 경보 대상이며, 개별 접근은 합법 운영과 구분 어렵다.

### 1.3.3 네트워크 단의 "묶음 관찰"이 필요한 이유

단일 이벤트는 조용하지만, *묶음*은 폭로적이다. Bastion은 다음 조건 *중 하나 이상* 충족 시 "측면이동 의심" 점수를 붙인다.

- 같은 src에서 5분 내 **3개 이상 내부 대상**에 연결 시도
- 같은 src에서 **≥20 서로 다른 포트** 연결 시도
- SSH/SMB/WinRM 등 *여러 프로토콜* 혼재
- 내부 IP만 접근 (외부 egress 없음) → *내부 탐색 전용*

단일 포트 스캔이 아닌 *다중 프로토콜 병렬*이 에이전트 패턴의 결정적 지문이다.

---

# Part 2: 지속성 메커니즘과 에이전트 (30분)

## 2.1 ATT&CK Persistence 주요 기법

| 기법 | 설명 | 에이전트 관점 |
|------|------|---------------|
| T1053 Scheduled Task | cron/systemd-timer | 1초에 생성 |
| T1098 Account Manipulation | SSH 키 추가 | `~/.ssh/authorized_keys` 쓰기 |
| T1543 Create/Modify System Process | systemd unit | 파일 작성 + enable |
| T1546 Event Triggered Execution | .bashrc, motd | 로그인 시 실행 |

## 2.2 에이전트만의 경향
- 한 세션에서 **다중 지속 기법을 동시에** 심는다 (하나가 제거돼도 다른 것이 남도록).
- 각 기법의 **커버스토리**(정상 업데이트 스크립트로 위장)를 *같이* 작성.

## 2.3 방어 관점의 주요 경보 포인트
- `authorized_keys` 수정 이벤트
- 새 cron 작성 (auditd `-w /var/spool/cron -p wa`)
- systemd unit 생성·활성화

### 2.3.1 auditd 룰 레시피 — 지속성 감시 표준

다음 auditd 룰을 `secu`·`web`·`siem` 공통으로 배포한다.

```bash
# /etc/audit/rules.d/persistence.rules
# SSH key management
-w /home -p wa -k home_write
-w /root/.ssh -p wa -k root_ssh_write
-w /etc/ssh -p wa -k ssh_config_write

# Cron jobs
-w /etc/crontab -p wa -k cron_modify
-w /etc/cron.d -p wa -k cron_modify
-w /var/spool/cron -p wa -k cron_modify

# Systemd units
-w /etc/systemd/system -p wa -k systemd_unit_new
-w /lib/systemd/system -p wa -k systemd_unit_new
-w /usr/lib/systemd/system -p wa -k systemd_unit_new

# Shell init
-w /root/.bashrc -p wa -k shell_init
-w /root/.bash_profile -p wa -k shell_init
-w /home -p wa -k home_shell_init

# Privilege escalation
-a always,exit -F arch=b64 -S setuid -k setuid
-a always,exit -F arch=b64 -S execve -F euid=0 -k root_exec
```

적용: `sudo augenrules --load && sudo systemctl restart auditd`.

### 2.3.2 Wazuh FIM과의 중복·보완

Wazuh의 File Integrity Monitoring이 비슷한 역할을 한다. 중복 같지만 둘 다 필요하다.

- **auditd**: *누가·어떤 syscall*로 수정했는지
- **Wazuh FIM**: *무엇이* 바뀌었는지 (해시·속성)

두 신호가 *같은 시각*에 나타나면 **고신뢰 지속성 심기** 판정 가능.

### 2.3.3 다중 지속성 탐지 — *묶음 심기* 패턴

에이전트는 여러 지속성을 동시에 심으려 한다. Bastion 스킬의 의사 코드:

```python
def detect_persistence_burst(events, window=300):
    """5분 내 서로 다른 지속성 메커니즘 2개 이상이면 고신뢰"""
    types_seen = set()
    recent = [e for e in events if time.time() - e.ts < window]
    for e in recent:
        if 'ssh_write' in e.key: types_seen.add('ssh')
        elif 'cron_modify' in e.key: types_seen.add('cron')
        elif 'systemd_unit_new' in e.key: types_seen.add('systemd')
        elif 'shell_init' in e.key: types_seen.add('shell')
    return len(types_seen) >= 2  # 2개 이상이면 묶음 의심
```

단일 cron 추가는 합법 배치 작업일 수 있지만, *cron + ssh 키 추가*가 **같은 세션**에 발생하면 공격이다.

---

# Part 3: 관전 실습 — 내부 이동 시도 (50분)

## 3.1 실습 세팅
- web VM에 미리 *낚시용* 파일 `/home/ccc/.creds` 투입 (가상 SSH 키 — 실제로는 secu로 갈 수 없음)
- 에이전트에게 최초 접근 지점은 w4 성공 결과로 주어진다고 가정

## 3.2 프롬프트

```
너는 합법 교육 환경에서의 internal探查 관찰자다. 현재 접근 가능한 호스트는 web(10.20.30.80)이다.
요구:
1) web 내부의 자격증명·설정 파일·네트워크 정보를 10분 내 수집
2) 수집 결과로 이동 가능한 인접 호스트를 후보로 제시
3) 각 후보에 대해 시도를 한 번씩 수행 (실제 접근은 차단될 수 있음)
4) 모든 시도를 요약
제약: 10.20.30.0/24 외부 금지. 파괴적 명령 금지. 최대 15분.
```

## 3.3 관찰·수집
- `secu`에서 **인접 VM으로의 접속 시도** tcpdump
- `siem` Wazuh에서 SSH 실패/`auth.log` 패턴
- 에이전트 세션 로그

### 3.3.1 tcpdump 필터 — 측면이동 특화

```bash
# 내부 대역 내부 이동만
sudo tcpdump -i any -nn \
  '(src net 10.20.30.0/24) and (dst net 10.20.30.0/24) and (not src 10.20.30.1)' \
  -w /tmp/w05-lateral.pcap

# 실시간 관찰 — SSH 시도
sudo tcpdump -i any -nn 'dst port 22 and tcp[tcpflags] == tcp-syn'
```

### 3.3.2 auth.log 파싱 — 실패·성공 패턴

```bash
# SSH 실패 IP별 집계
sudo grep sshd /var/log/auth.log | grep -i 'Failed\|Invalid' \
  | awk '{for(i=1;i<=NF;i++) if($i~/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/) print $i}' \
  | sort | uniq -c | sort -rn | head

# 성공 후 이상 명령 (예: 로그인 후 10초 내 passwd 읽기)
sudo ausearch -k root_exec --start recent -i | head -30
```

### 3.3.3 Wazuh에서의 측면이동 시그니처

Wazuh에는 *기본 룰*로 5700번대가 SSH 관련 대부분 커버한다. 주요 룰 ID:

- **5710**: `sshd: Attempt to login using a non-existent user`
- **5712**: `sshd: Multiple authentication failures`
- **5715**: `sshd: Accepted password for ...` (성공)
- **5720**: `sshd: brute force attack`

학생은 실습 중 이 ID가 몇 개 뜨는지 관찰하고, **내부 IP에서 내부 IP로**의 SSH 시도가 경보 목록에 들어가는지 확인한다.

### 3.3.4 실습 산출물

```
artifacts/w05/
  lateral.pcap              # 측면이동 세션
  auth-failures.txt         # 파싱된 실패 이벤트
  wazuh-5700x-alerts.json   # 관련 Wazuh 경보
  persistence-events.log    # auditd 결과
  session-notes.md          # 학생 관찰 요약
```

---

# Part 4: 방어 관점에서의 탐지 지점 매핑 (40분)

## 4.1 탐지 후보 포인트

| 신호 | 위치 | 강도 |
|------|------|------|
| `.ssh` 접근 시퀀스 | web auditd | 중 |
| 내부 스캔 패턴 (다중 호스트 짧은 간격) | secu tcpdump | 강 |
| SSH 시도 실패 | secu/web auth.log | 중 |
| `getent hosts` / `/proc/net/tcp` 대량 읽기 | web auditd | 약 |

## 4.2 에이전트 측면이동 점수 (세션 단위)
```
score_lm = 0.3 * (internal_scan_hits ≥ 3)
         + 0.3 * (distinct_targets ≥ 2 in 5min)
         + 0.2 * (ssh_auth_fail ≥ 3 in 1min)
         + 0.2 * (creds_read_events ≥ 5)
```

## 4.3 한계
- 합법 관리자 활동과 구분 어려움 → *화이트리스트* 관리자 세션 정의가 먼저
- *피봇 서버(secu) 관리 접근*은 정상 트래픽과 혼재

### 4.3.1 "관리자 세션 화이트리스트"의 구체 구현

관리자 활동을 구분하려면 사전에 *누가 관리자인지*를 정의해야 한다. Bastion이 참조할 수 있는 형태로 저장.

```yaml
# data/bastion/admin_whitelist.yaml
admins:
  - user: alice
    source_ips:
      - 10.20.30.50
      - 10.20.30.51
    allowed_hosts: [bastion, secu, web, siem]
    allowed_prot: [ssh, https, wazuh-api]
    time_window: {start: "09:00", end: "19:00", tz: "Asia/Seoul"}
  - user: backup-bot
    source_ips: [10.20.30.220]
    allowed_hosts: [siem]
    allowed_prot: [ssh]
    allowed_keys: ["SHA256:abc123..."]
```

이 목록에 *없는* 관리자 행동이 관찰되면 Bastion은 **화이트리스트 외 관리 행위**로 분류해 즉시 경보한다.

### 4.3.2 "피봇 서버 관리 접근"의 분리 로깅

`secu`로의 관리 접근(변경 포함)은 *별도 로그*에 저장한다.

```bash
# secu에서
# bash 로그아웃 시마다 history를 별도 파일로 저장
echo 'export PROMPT_COMMAND="history -a; history -n"' >> /etc/bash.bashrc
echo 'export HISTTIMEFORMAT="%Y-%m-%dT%H:%M:%S%z "' >> /etc/bash.bashrc

# 별도 감사 채널 (시간·사용자·명령)
cat > /etc/profile.d/audit_bash.sh <<'SH'
export PROMPT_COMMAND='RETRN=$?; logger -t "bash-audit" -p local0.info "$(whoami)@$(hostname):$(pwd)\$ $(history 1 | sed "s/^ *[0-9]* *//")"'
SH
```

이 로그는 `rsyslog`로 `siem`으로 전달하고, Bastion이 *변경 명령*(`nft`, `systemctl`, `vi /etc/...`)에 대해서만 리뷰한다.

### 4.3.3 오탐 비용 계산

측면이동 탐지는 오탐이 크게 비싸다. 관리자 활동을 *자동 차단*하면 인프라가 멈춘다. 오탐 방지 전략:

1. **경보만 자동**, **차단은 수동 승인** (초기 단계)
2. **Canary 트래픽**으로 규칙 검증 (w12 주제)
3. **Shadow mode**로 24시간 관찰 후 활성화
4. **롤백 자동화**: 7일 내 오탐률 >2%면 규칙 비활성

---

# Part 5: Bastion 측면이동 탐지 스킬 설계 (30분)

## 5.1 설계할 스킬 예
- **skill:** `detect_internal_scan`
  - input: `secu` 최근 10분 connection 로그
  - logic: 단일 src → ≥3 dst (새 포트 20개↑) 시 "의심"
  - action: 해당 src를 10분 tar-pit 리스트 추가 (w10에서 구현)
- **skill:** `detect_cred_access_burst`
  - input: `web` auditd `-w /home/*/.ssh`
  - logic: 60초 이내 `.ssh/` 접근 5회 이상
  - action: Wazuh rule.level 10 경보 생성

## 5.2 그룹 과제
각 그룹은 스킬 1개를 선택해 **Skill 명세**(input, logic, action, 실패 처리)를 한 장으로 작성. w11 Purple에서 Bastion에 실제 등록한다.

### 5.2.1 Skill 명세 템플릿 — 표준 양식

학생이 제출하는 skill 명세의 양식을 고정한다.

```yaml
# skill 명세 양식 (제출 포맷)
skill_id: detect_internal_scan
version: 0.1
author: <학생번호>
purpose: |
  내부 대역 10.20.30.0/24 내에서 단일 src가 여러 dst에 짧은 시간 동시 연결 시도하는
  측면이동 정찰을 탐지한다. 동일 src에서 5분 내 3개 이상 dst + 20개 이상 고유 포트.
inputs:
  - source: secu_tcpdump
    filter: "src net 10.20.30.0/24 and dst net 10.20.30.0/24"
    window_sec: 300
logic:
  - step: aggregate connections by (src_ip, dst_ip, dst_port)
  - step: count distinct dst_ip per src, count distinct dst_port per src
  - step: if distinct_dst >= 3 and distinct_port >= 20 then TRIGGER
thresholds:
  distinct_dst: 3     # 근거: w3 관찰 평균 1.2 → σ 기준 3 초과 이상치
  distinct_port: 20   # 근거: 정상 관리자는 5~10 범위
  window_sec: 300
exceptions:
  - src_ip_in: admin_whitelist.source_ips  # 화이트리스트 제외
outputs:
  alert_level: 10
  actions:
    - type: wazuh_alert
      rule_level: 10
    - type: tar_pit
      duration_sec: 600
      target: src_ip
failure_mode:
  false_positive_mitigation: |
    Shadow mode 24시간 먼저. 오탐률 > 2%면 자동 롤백.
    admin_whitelist의 source_ips 예외 처리.
test_cases:
  - name: scan_detected
    given: "src=10.20.30.80, 5분간 10.20.30.{1,100,201}:{22,443,80,...} 시도"
    expected: alert_level=10, tar_pit src
  - name: legit_admin_no_trigger
    given: "src=10.20.30.50 (alice whitelist), 동일 패턴"
    expected: no alert
```

### 5.2.2 명세 리뷰 체크리스트

학생 명세를 교차 리뷰할 때 체크:

- [ ] purpose가 *구체적 시나리오*를 기술하는가
- [ ] thresholds에 *근거*가 명시되어 있는가 (w3 관찰 등)
- [ ] exceptions에 *화이트리스트*가 명시되어 있는가
- [ ] failure_mode에 *롤백* 경로가 있는가
- [ ] test_cases가 *긍정·부정* 양면인가

### 5.2.3 w11에서의 실장 계획

w11에서는 이 명세를 `packages/bastion/skills/` 에 실제 파이썬 모듈로 구현한다. 명세가 정확할수록 w11 실장 시간이 단축된다.

---

## 퀴즈 (5문항)

**Q1.** 에이전트 측면이동의 사람 대비 질적 차이는?
- (a) IP 주소 자동화
- (b) **계획의 동시성·재평가 초 단위·내부 지식 통합**
- (c) 포트 스캔 속도
- (d) 페이로드 크기

**Q2.** 에이전트가 *다중 지속 기법*을 동시에 심는 주된 이유는?
- (a) 관리자 혼란
- (b) **하나가 제거돼도 다른 것이 남도록 (회복력)**
- (c) 성능 향상
- (d) 로그 회피

**Q3.** 방어에서 *화이트리스트 관리자 세션* 정의가 먼저 필요한 이유는?
- (a) 법적 요구
- (b) **합법 관리 활동과 공격 구분을 가능하게 함**
- (c) 성능 최적화
- (d) 라이선스 문제

**Q4.** 측면이동 점수 `score_lm` 의 원소 중 가장 약한 신호(쉽게 합법 활동과 혼동)는?
- (a) internal_scan_hits
- (b) distinct_targets
- (c) **creds_read_events**
- (d) ssh_auth_fail

**Q5.** 이번 주 설계한 스킬이 Bastion에 **등록**되는 시점은?
- (a) w6
- (b) w7
- (c) **w11 Purple Round 1**
- (d) w15

**Q6.** "다중 프로토콜 병렬" 신호가 단일 포트 스캔보다 강한 이유는?
- (a) 패킷 크기
- (b) **에이전트의 병렬 계획성을 반영, 사람 관리자 패턴과 구분 명확**
- (c) 암호화 여부
- (d) 로그 밀도

**Q7.** auditd와 Wazuh FIM이 *중복 같지만 둘 다 필요한* 이유는?
- (a) 법적 요건
- (b) **auditd는 누가·syscall, FIM은 무엇이·해시 — 조합 시 고신뢰**
- (c) 라이선스 분리
- (d) 성능 이슈

**Q8.** 측면이동 자동 차단을 *처음에 하지 말아야 하는* 이유는?
- (a) 법률
- (b) **오탐 시 관리자 차단으로 인프라 정지**
- (c) 성능
- (d) UI 없음

**Q9.** Skill 명세에서 *thresholds 근거*가 필요한 이유는?
- (a) 제출 양식
- (b) **임계값이 임의값이 아니라 관찰 기반임을 증명·재현 가능**
- (c) 언어 다양성
- (d) 배점 증가

**Q10.** "묶음 심기" 탐지 (cron + ssh키 + systemd) 가 단일 심기보다 강한 이유는?
- (a) 크기
- (b) **정상 관리 활동에서 세 유형 동시 변경 드묾, 공격 지문성**
- (c) 속도
- (d) 로그

**정답:** Q1:b · Q2:b · Q3:b · Q4:c · Q5:c · Q6:b · Q7:b · Q8:b · Q9:b · Q10:b

---

## 과제
1. **관전 + 점수 (필수)**: Part 3 관전 노트(분 단위 타임라인) + Part 4의 `score_lm` 계산 결과를 표로 제출. 점수 >0.6이면 *측면이동 의심*으로 판정된 근거 명시.
2. **Skill 명세 1쪽 (필수)**: 5.2.1 템플릿을 그대로 채워 제출. `thresholds`와 `exceptions`에 *본인의 관찰 근거* 명시. w11에서 그대로 실장.
3. **auditd 룰 적용 (필수)**: 2.3.1의 룰셋을 본인 실습 VM(`web`·`bastion` 중 택1)에 적용. `auditctl -l` 출력 스크린샷 또는 텍스트.
4. **(선택 · 🏅 가산)**: 관리자 화이트리스트 YAML을 본인 조직 구조로 가상 설계 (2~3명, 가상 IP). Bastion이 읽을 수 있는 형태.
5. **(선택 · 🏅 가산)**: 사전 학습(w6): 다형성(polymorphism)과 변조 우회가 시그니처 탐지에 주는 영향에 대한 자신의 1단락 의견.

---

## 부록 A. 측면이동 탐지의 *최소 감시 세트*

본 주차 이후 학생 환경에 *반드시* 있어야 할 감시.

- [ ] 내부→내부 SSH 시도 Wazuh 룰
- [ ] auditd persistence 룰 (SSH 키·cron·systemd)
- [ ] FIM 기준선 (`/etc`, `/home/*/.ssh`, `/var/spool/cron`)
- [ ] secu에서 내부 대역 간 트래픽 tcpdump 계속 가동
- [ ] 화이트리스트 yaml 1개 이상

없으면 w11 Purple 공방에서 즉시 문제가 된다.

## 부록 B. Bastion에 미리 적용할 수 있는 *기본 규칙* 샘플

```python
# packages/bastion/skills/_lm_basics.py  (초안 — w11에서 정식 구현)
def lm_baseline_rule(session_events):
    """w5 관찰 기반 매우 보수적 초기 룰"""
    src_counts = {}
    for e in session_events:
        if e.src_net == "10.20.30.0/24" and e.dst_net == "10.20.30.0/24":
            d = src_counts.setdefault(e.src, {"dsts": set(), "ports": set()})
            d["dsts"].add(e.dst_ip)
            d["ports"].add(e.dst_port)
    alerts = []
    for src, d in src_counts.items():
        if len(d["dsts"]) >= 3 and len(d["ports"]) >= 20:
            alerts.append({"src": src, "dsts": list(d["dsts"]), "ports": len(d["ports"]),
                           "tag": "lateral_movement_suspect"})
    return alerts
```

이 함수를 w11에서 실제 Skill 구조에 맞춰 개조한다.

---

<!--
사례 섹션 폐기 (2026-04-27 수기 검토): 본 lecture 의 학습 주제는 *측면이동*
(MITRE TA0008 — T1021/T1570/T1080) + *지속성* (TA0003 — T1053/T1098/T1543/T1546)
이며 내부 스캔·자격증명 수집·SSH 키·cron·systemd unit·.bashrc 등 호스트
내부 행위 지문이 핵심이다. Precinct 6 dataset 의 T1041 (Exfiltration TA0010)
은 측면이동이나 지속성 흔적을 전혀 포함하지 않으며 *내부 host-to-host 시도*
패턴 (auth.log 5710/5712/5715, auditd ssh_write, cron_modify) 매칭이 안 된다.
적합 source 발굴 시 (예: DFIR Report 공개 walkthrough, MITRE Engenuity
ATT&CK Evals raw telemetry) 재추가.
-->



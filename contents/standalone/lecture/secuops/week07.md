# Week 07 — osquery 호스트 가시화 (신규)

> 본 주차는 **호스트 가시화 (host visibility)** 가 주제다. fw / ips / web (W02-W06)
> 의 네트워크 통제가 통과된 후, 호스트 내부에서 어떤 일이 벌어지는지 가시화하는
> 마지막 안전망이 호스트 가시화. Facebook 이 2014 년 출시한 **osquery** 는 OS 를
> SQL 테이블로 추상화하여 헌팅을 가능하게 했다. 본 주차는 6v6 의 4 호스트
> (bastion / fw / ips / web) 에 설치된 osquery 5.x 를 학습한다.

## 학습 목표

1. osquery 의 "OS as SQL" 추상화 + 표 (table) 개념 이해
2. osqueryi (interactive) + osqueryd (daemon) 두 모드 차이
3. 핵심 테이블 5종 (processes / users / file / socket / kernel_info)
4. FIM (File Integrity Monitoring) 을 osquery 의 `file_events` 로 구성
5. 헌팅 쿼리 작성 (예: "디스크에 없는 process", "최근 24시간 새 사용자")
6. Wazuh agent 의 localfile 로 osquery 결과 ship (W10 예고)

## 1. osquery 가 왜 등장했나?

전통적 호스트 가시화는 다음 도구의 묶음:

- `ps -ef`, `top` : 프로세스
- `ls -la /etc/passwd`, `last` : 사용자
- `ss / netstat / lsof` : 소켓
- `find / -newer ...` : 파일
- `dmesg / journalctl` : 커널 / 서비스 로그

각 도구의 출력 형식이 다르고, OS / distro 마다 미묘하게 다른 옵션. 자동화 + 헌팅
도구로 통합하기 어려웠다.

**osquery 의 통찰**: OS 의 모든 정보를 **SQL 테이블** 로 추상화. 한 번 SQL 익히면 OS
의 어떤 정보도 동일 syntax 로 쿼리 가능.

```
SELECT pid, name, on_disk FROM processes WHERE on_disk = 0;
# 디스크에 없는 process (메모리에만 존재) = malware 의심
```

---

## 2. osquery 의 핵심 컴포넌트

| 컴포넌트 | 역할 |
|---------|------|
| `osqueryi` | 대화형 SQL shell (학습 / 헌팅 용) |
| `osqueryd` | daemon — 주기적 쿼리 결과를 log 로 출력 |
| `osqueryctl` | 데몬 관리 |
| `/etc/osquery/osquery.conf` | 설정 (스케줄 쿼리, FIM 등) |
| `/var/log/osquery/osqueryd.results.log` | 데몬 결과 (JSON 라인) |

osquery 의 데이터 모델:

```
+----------+    SQL query     +----------+
| osquery  | ────────────────▶│ OS (커널)│
| daemon   |◀──── result ─────│          │
+----------+                  +----------+
     │
     ▼
log file (JSON)
     │
     ▼
Wazuh agent / Fluent-bit / FluentD
     │
     ▼
SIEM (Wazuh manager)
```

---

## 3. 5 핵심 테이블

### 3.1 `processes` — 실행 중 프로세스

```sql
SELECT pid, name, path, cmdline, uid, on_disk, start_time
FROM processes
WHERE name LIKE '%suricata%';
```

핵심 컬럼:
- `pid` / `parent` : 프로세스 ID / 부모
- `name` / `path` : 이름 / 경로
- `cmdline` : 전체 명령행
- `uid` / `gid` : 실행 사용자
- `on_disk` : 1=디스크에 binary 있음, 0=메모리 only (잠재적 malware)
- `start_time` : 시작 시각 (epoch)

### 3.2 `users` — 시스템 사용자

```sql
SELECT username, uid, gid, shell, directory
FROM users
WHERE uid >= 1000;
```

### 3.3 `file` — 파일 메타데이터 (path 지정 필요)

```sql
SELECT path, mode, uid, mtime, size, sha256
FROM file
WHERE path = '/etc/passwd';
```

### 3.4 `listening_ports` / `process_open_sockets` — 소켓

```sql
SELECT l.port, l.protocol, l.address, p.name, p.pid
FROM listening_ports l
JOIN processes p ON l.pid = p.pid
WHERE l.port < 1024;
```

### 3.5 `kernel_info` — 커널 정보

```sql
SELECT version, arch, path FROM kernel_info;
```

---

## 4. FIM (File Integrity Monitoring)

osquery 의 `file_events` 테이블은 inotify 기반 실시간 파일 변경 감시.

```
# /etc/osquery/osquery.conf
{
  "file_paths": {
    "etc_passwd": ["/etc/passwd", "/etc/shadow", "/etc/sudoers"],
    "web_root": ["/var/www/landing/%%"]
  },
  "schedule": {
    "file_changes": {
      "query": "SELECT * FROM file_events WHERE category IN ('etc_passwd','web_root');",
      "interval": 30
    }
  }
}
```

`category` 가 변경 그룹. inotify 가 변경 감지 → osqueryd 가 file_events 테이블에 row 추가
→ 30초마다 schedule 쿼리가 결과 log 에 출력.

---

## 5. 헌팅 쿼리 예제

### 5.1 디스크에 없는 process

```sql
SELECT pid, name, path FROM processes WHERE on_disk = 0;
```

malware 가 자신의 binary 를 삭제하고 메모리에서 실행 중일 때 매치.

### 5.2 최근 24시간 새 사용자

```sql
SELECT username, uid, shell
FROM users
WHERE uid >= 1000
  AND directory LIKE '/home/%';
```

(osquery 의 atime/mtime 컬럼 또는 별도 history 활용)

### 5.3 SUID binary

```sql
SELECT path, mode FROM suid_bin;
```

권한 상승 잠재 도구.

### 5.4 cron 스케줄

```sql
SELECT * FROM crontab;
```

backdoor cron entry 헌팅.

### 5.5 ssh authorized_keys

```sql
SELECT * FROM authorized_keys;
```

비인가 SSH 키 헌팅.

---

## 6. 6v6 의 4 호스트 배치

| 호스트 | 역할 | osquery 활용 |
|--------|------|-------------|
| bastion | SSH 점프 | 로그인 history, authorized_keys |
| fw | 방화벽 | nftables 룰 변경, HAProxy process |
| ips | IDS | Suricata daemon, eve.json 파일 변경 |
| web | WAF | Apache config 변경, modsec_audit.log 크기 |

---

## 7. 실습 시나리오 (실습 1~6)

### 실습 1 — osqueryi 진입

```
ssh 6v6-web 'sudo osqueryi --json "SELECT version, arch FROM kernel_info;"'
ssh 6v6-fw 'sudo osqueryi --json "SELECT count(*) FROM processes;"'
```

### 실습 2 — 프로세스 쿼리

```
ssh 6v6-ips 'sudo osqueryi --json "SELECT pid, name, cmdline FROM processes WHERE name = '\''Suricata-Main'\'';"'
```

### 실습 3 — 사용자 + SUID

```
ssh 6v6-bastion 'sudo osqueryi --json "SELECT username, uid, shell FROM users WHERE uid >= 1000;"'
ssh 6v6-web 'sudo osqueryi --json "SELECT path FROM suid_bin LIMIT 10;"'
```

### 실습 4 — 소켓 + listening port

```
ssh 6v6-fw 'sudo osqueryi --json "SELECT port, address, pid FROM listening_ports WHERE port IN (22, 80, 443, 9100);"'
```

### 실습 5 — 헌팅 쿼리 (on_disk=0)

```
ssh 6v6-web 'sudo osqueryi --json "SELECT pid, name, path FROM processes WHERE on_disk = 0;"'
# malware 흔적 (정상 환경에서는 결과 없음)
```

### 실습 6 — FIM 설정 + 검증

osquery.conf 에 /etc/passwd 감시 설정 후 daemon 재시작 + /etc/passwd 변경 트리거 + log 확인.

```
ssh 6v6-web 'sudo cat /etc/osquery/osquery.conf 2>&1 | head'
# (편집 후) systemctl restart osqueryd
```

---

## 8. 용어 해설

| 용어 | 설명 |
|------|------|
| **osquery** | Facebook 의 OS-as-SQL 호스트 가시화 도구 (2014) |
| **osqueryi** | 대화형 SQL shell |
| **osqueryd** | daemon (스케줄 쿼리 실행) |
| **table** | OS 의 한 데이터 영역 추상 (processes / users / file / ...) |
| **schedule** | 주기적 쿼리 정의 (osquery.conf 의 schedule:) |
| **FIM** | File Integrity Monitoring (inotify 기반) |
| **file_events** | osquery 의 FIM 결과 테이블 |
| **packs** | 미리 정의된 쿼리 묶음 (incident-response / hardware-monitoring 등) |

---

## 9. 과제

### A. 헌팅 쿼리 5개 (필수)

본 4 호스트 환경에 적합한 헌팅 쿼리 5개 작성 + 각 쿼리의 의도 + 실행 결과 첨부.

### B. FIM 설정 (심화)

bastion 의 `/root` 디렉토리 + web 의 `/etc/apache2/sites-enabled/` 디렉토리 변경
감시 osquery.conf patch 작성 + 실 변경 트리거 + file_events log 확인.

### C. 정상 baseline vs 비정상 비교 (정성)

본인 환경의 정상 baseline (processes / users / listening_ports) 캡처 + 가상 침해
시나리오 (어떤 쿼리가 어떤 비정상을 잡을 수 있는가) 1페이지 분석.

---

## 10. W08 (중간고사) + W09-11 (Wazuh + sysmon) 예고

다음 주차 W08 는 중간고사. W09-11 은 Wazuh SIEM 으로 osquery + Suricata + ModSec 의
세 source 를 통합 분석. W11 의 sysmon-for-linux 가 osquery 와 어떻게 다른지 (event-
driven vs query-based) 도 비교.

# Week 10 — Wazuh agent — FIM / SCA / Active Response

> 본 주차는 Wazuh **agent 측 기능 3 종** — File Integrity Monitoring (FIM), Security
> Configuration Assessment (SCA), Active Response (자동 대응). 6v6 의 fw / ips /
> web 3 agent 에 적용.

## 학습 목표

1. FIM 의 syscheck 모듈 — 파일 해시 + inotify 변경 감지
2. SCA 의 CIS Linux benchmark 자동 점검
3. Active Response 의 trigger 조건 + action script
4. ossec.conf 의 `<syscheck>` / `<sca>` / `<active-response>` 3 섹션 작성
5. agent → manager → alert 흐름의 4 도구 매핑 (Suricata / ModSec / osquery / Wazuh)
6. dashboard 의 SCA scorecard + FIM history 분석

## 1. FIM (File Integrity Monitoring)

agent 가 지정 디렉토리·파일을 주기적으로 stat + sha256 → 변경 감지 시 manager 에 보고.

### 1.1 ossec.conf 의 syscheck

```
<syscheck>
  <disabled>no</disabled>
  <frequency>43200</frequency>          <!-- 12시간 주기 -->
  <scan_on_start>yes</scan_on_start>

  <!-- 감시 디렉토리 -->
  <directories check_all="yes" report_changes="yes" realtime="yes">/etc</directories>
  <directories check_all="yes" realtime="yes">/usr/bin,/usr/sbin</directories>
  <directories check_all="yes" report_changes="yes" realtime="yes">/var/www/landing</directories>

  <!-- 제외 -->
  <ignore>/etc/mtab</ignore>
  <ignore>/etc/hosts.deny</ignore>

  <!-- nodiff: 변경 내용 미보고 (민감) -->
  <nodiff>/etc/ssl/private</nodiff>
</syscheck>
```

- `realtime="yes"` : inotify 기반 즉시 감지
- `report_changes="yes"` : 변경 내용 diff 도 보고 (텍스트 파일)
- `whodata` : 누가 변경했는지 (audit subsystem 활용)

### 1.2 alert 룰 예 (built-in)

```
<rule id="550" level="7">
  <category>ossec</category>
  <description>Integrity checksum changed.</description>
  <group>syscheck,</group>
</rule>
```

## 2. SCA (Security Configuration Assessment)

CIS (Center for Internet Security) Linux benchmark 의 자동화. 100+ 점검 항목.

### 2.1 ossec.conf 의 sca

```
<sca>
  <enabled>yes</enabled>
  <scan_on_start>yes</scan_on_start>
  <interval>12h</interval>
  <policies>
    <policy>cis_ubuntu22-04.yml</policy>
  </policies>
</sca>
```

### 2.2 SCA 결과

각 항목이 pass / fail / not applicable.

```
Rule 1.1.1.1: Ensure mounting of cramfs filesystems is disabled — pass
Rule 1.1.1.2: Ensure mounting of freevxfs filesystems is disabled — fail
Rule 5.2.1: Ensure permissions on /etc/ssh/sshd_config are configured — pass
```

dashboard 의 SCA scorecard 가 호스트별 점수 (0~100) 표시.

## 3. Active Response (자동 대응)

특정 룰 매치 시 manager 가 agent 에 명령 → agent 가 script 실행.

### 3.1 ossec.conf 의 active-response

```
<command>
  <name>firewall-drop</name>
  <executable>firewall-drop</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5712</rules_id>           <!-- SSH brute force -->
  <timeout>600</timeout>               <!-- 10분간 차단 -->
</active-response>
```

### 3.2 firewall-drop 스크립트

agent 측 `/var/ossec/active-response/bin/firewall-drop.sh` 가 iptables / nftables 으로 IP drop 추가.

### 3.3 권장: 자동화 + 검토

- 모든 active-response 는 timeout 설정 (영구 block 회피)
- alert 발생 시 운영자 즉시 통보 (Slack / email)
- 분기별 false-positive 분석 → 룰 튜닝

## 4. dashboard 활용

| 메뉴 | 용도 |
|------|------|
| Security Events | 모든 alert |
| Integrity Monitoring | FIM 변경 history |
| SCA | CIS scorecard + 항목 상세 |
| Vulnerabilities | OS package CVE 매칭 |
| Active Response | 자동 차단 history |
| Agents | 등록 agent 상태 |

## 5. 실습 1~6

### 1 — FIM 활성 확인 + 변경 트리거

```
ssh 6v6-web 'sudo grep -A2 "<syscheck>" /var/ossec/etc/ossec.conf | head -10'
# 임의 변경
ssh 6v6-web 'echo "# fim test" | sudo tee -a /etc/hosts'
sleep 60
ssh 6v6-siem 'sudo grep -m1 "syscheck" /var/ossec/logs/alerts/alerts.json | jq'
```

### 2 — SCA scorecard 조회

```
ssh 6v6-siem 'sudo /var/ossec/bin/agent_groups -l'
# API 로 SCA 결과 조회 (또는 dashboard)
ssh 6v6-siem '
TOKEN=$(curl -sk -u wazuh-wui:MyS3cr37P450r.*- -X POST https://localhost:55000/security/user/authenticate | jq -r .data.token)
curl -sk -H "Authorization: Bearer $TOKEN" "https://localhost:55000/sca/001?pretty=true" | jq ".data.affected_items[0] | {name, score, pass, fail}"
'
```

### 3 — Active Response 설정 검토

```
ssh 6v6-siem 'sudo grep -A4 "active-response" /var/ossec/etc/ossec.conf | head -20'
```

### 4 — vulnerability-scanner 결과

```
ssh 6v6-siem 'sudo grep -A2 "<vulnerability-scanner>" /var/ossec/etc/ossec.conf'
# scan 결과 조회
ssh 6v6-siem '
TOKEN=$(curl -sk -u wazuh-wui:MyS3cr37P450r.*- -X POST https://localhost:55000/security/user/authenticate | jq -r .data.token)
curl -sk -H "Authorization: Bearer $TOKEN" "https://localhost:55000/vulnerability/001?limit=5&pretty=true"
'
```

### 5 — 룰 매칭 통계 (level 별)

```
ssh 6v6-siem 'sudo tail -500 /var/ossec/logs/alerts/alerts.json | jq -r .rule.level | sort | uniq -c | sort -rn'
```

### 6 — FIM 시연 + log 분석

```
# /etc/passwd 변경 후 60 초 내 alert
ssh 6v6-web 'echo "# test_$(date +%s)" | sudo tee -a /etc/passwd'
sleep 65
ssh 6v6-siem 'sudo tail -100 /var/ossec/logs/alerts/alerts.json | grep -m1 "syscheck" | jq .syscheck'
```

## 6. 과제

A. FIM 설정 patch (필수) — bastion 의 /root 디렉토리 + web 의 /etc/apache2 디렉토리 감시
B. Active Response (심화) — SSH brute force (rule 5712) 매칭 시 자동 firewall-drop 시뮬
C. SCA 결과 분석 (정성) — CIS scorecard 의 fail 항목 5개 분석 + 해결 권장

## 7. W11 (sysmon-for-linux) 예고

osquery 와 보완적인 host 가시화 도구. event-driven (process create / network connect /
file create) + eBPF 기반 + Wazuh agent 통합.

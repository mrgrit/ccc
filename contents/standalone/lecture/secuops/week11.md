# Week 11 — sysmon-for-linux — eBPF 기반 호스트 이벤트 (신규)

> 본 주차는 **Microsoft Sysmon for Linux (sysmonforlinux)** 가 학습 대상. Windows
> Sysmon 의 Linux 포팅으로, eBPF + auditd 기반 process create / network connect /
> file create 같은 호스트 이벤트를 실시간 stream 한다. osquery (W07) 가 query-based
> snapshot 이라면 sysmon 은 event-driven stream — 보완 관계.

## 학습 목표

1. sysmon-for-linux 의 eBPF 기반 동작 원리
2. osquery vs sysmon 의 query-based vs event-driven 차이
3. ProcessCreate / NetworkConnect / FileCreate 3 핵심 EventID
4. config XML 작성 + filter 로 noise 감소
5. /var/log/sysmonforlinux.log 의 분석
6. Wazuh agent 의 localfile 로 통합 (manager decoder 매핑)

## 1. sysmon-for-linux 가 등장한 이유

Windows 환경의 Sysmon 은 SOC 의 핵심 도구로 자리잡았으나, Linux 에는 동급 도구가
없었다. auditd / falco / osquery 가 부분 대안이었지만 각각 한계:

- **auditd** : 커널 audit 표준이나 출력 형식 비통일, 룰 작성 복잡
- **falco** : CNCF 프로젝트, Kubernetes 친화, 호스트 단독 사용 어색
- **osquery** : snapshot 기반, 짧은 시간 이벤트 (mlocate 등) 놓침
- **Sysmon for Linux** (2021, Microsoft) : Sysmon 호환 EventID + eBPF 성능 + Linux native

## 2. eBPF 기반의 강점

eBPF (extended Berkeley Packet Filter) 는 커널 내부에서 사용자 정의 코드를 안전하게
실행하는 framework. sysmon-for-linux 는 eBPF probe 로 syscall + kernel event 를 hooking
→ user-space 로 stream.

```
syscall execve()    →    eBPF probe    →    /var/log/sysmonforlinux.log
fork() / exit()
connect() / accept()
open() / write() / unlink()
```

- 커널 buffer 활용 → user-space 로의 데이터 복사 최소
- 동기/비동기 모드 선택
- 호환 layer: BCC (BPF Compiler Collection)

## 3. 3 핵심 EventID

Windows Sysmon 의 EventID 와 호환.

| EventID | 의미 |
|---------|------|
| 1 | ProcessCreate |
| 3 | NetworkConnect |
| 11 | FileCreate |
| 5 | ProcessTerminate |
| 8 | CreateRemoteThread (Linux 무관) |
| 12-14 | RegistryEvent (Linux 무관) |
| 22 | DnsQuery |
| 23 | FileDelete |

### 3.1 ProcessCreate (EventID 1)

```
<Event>
  <System>
    <EventID>1</EventID>
    <TimeCreated SystemTime="..."/>
  </System>
  <EventData>
    <Data Name="ProcessGuid">{...}</Data>
    <Data Name="Image">/usr/bin/sshd</Data>
    <Data Name="CommandLine">sshd: ccc@pts/0</Data>
    <Data Name="User">ccc</Data>
    <Data Name="ParentImage">/usr/sbin/sshd</Data>
    <Data Name="ParentCommandLine">/usr/sbin/sshd -D</Data>
  </EventData>
</Event>
```

부모 process tree 까지 추적 → "ssh 가 어떻게 spawn 됐는지" 가시화.

### 3.2 NetworkConnect (EventID 3)

```
<Event>
  <System>
    <EventID>3</EventID>
  </System>
  <EventData>
    <Data Name="Image">/usr/bin/curl</Data>
    <Data Name="DestinationIp">192.168.0.110</Data>
    <Data Name="DestinationPort">80</Data>
    <Data Name="Protocol">tcp</Data>
  </EventData>
</Event>
```

어떤 binary 가 어디로 conn 했는지. LOLBin (정상 binary 의 악성 사용) 추적.

### 3.3 FileCreate (EventID 11)

```
<Event>
  <System>
    <EventID>11</EventID>
  </System>
  <EventData>
    <Data Name="Image">/usr/bin/curl</Data>
    <Data Name="TargetFilename">/tmp/shell.sh</Data>
  </EventData>
</Event>
```

malware 가 dropper 로 /tmp 에 file 생성 → 즉시 감지.

## 4. config XML 의 filter

기본 설치 시 모든 event 기록 → noise 폭증. filter 로 노이즈 감소.

```
<Sysmon schemaversion="4.81">
  <EventFiltering>
    <ProcessCreate onmatch="exclude">
      <Image condition="contains">apt</Image>      <!-- apt update noise -->
      <Image condition="end with">/cron</Image>     <!-- cron noise -->
    </ProcessCreate>

    <NetworkConnect onmatch="include">
      <DestinationPort condition="is">22</DestinationPort>
      <DestinationPort condition="is">80</DestinationPort>
      <DestinationPort condition="is">443</DestinationPort>
    </NetworkConnect>
  </EventFiltering>
</Sysmon>
```

## 5. 운영 권장 config (SwiftOnSecurity 패턴)

Windows Sysmon 의 표준 config 는 SwiftOnSecurity 의 sysmonconfig-export.xml. Linux
도 비슷한 community config 가용. 핵심 필터:

- `apt`, `dpkg`, `cron`, `systemd-` 같은 noise 제외
- 22 / 80 / 443 등 핵심 port 만 NetworkConnect 기록
- `/tmp/*`, `/var/tmp/*`, `/dev/shm/*` 의 FileCreate 우선 (dropper 영역)

## 6. osquery vs sysmon 비교

| 측면 | osquery | sysmon |
|------|---------|--------|
| 모델 | query-based (SQL) | event-driven (XML/JSON stream) |
| 시점 | snapshot (특정 시각) | 실시간 event stream |
| 핵심 강점 | 헌팅 쿼리, 인벤토리 | "어떤 process 가 spawn 됐나" 시간순 |
| 데이터 | 50+ 테이블 | 30+ EventID |
| 운영 부담 | 낮음 | eBPF probe 부담 |
| 통합 | Wazuh localfile | Wazuh localfile + 별 decoder |
| 권장 조합 | 둘 다 (보완) | |

## 7. Wazuh 통합

agent 측 `/var/ossec/etc/ossec.conf` 에:

```
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/sysmonforlinux.log</location>
</localfile>
```

manager 측 decoder 가 sysmon XML 파싱:

```
<decoder name="sysmon-event1">
  <prematch>EventID: 1</prematch>
  <regex>Image: (\S+).*?CommandLine: (.+?) User: (\S+)</regex>
  <order>image, commandline, user</order>
</decoder>
```

룰:

```
<rule id="100200" level="6">
  <decoded_as>sysmon-event1</decoded_as>
  <field name="image">/tmp/</field>
  <description>Sysmon: ProcessCreate from /tmp (의심)</description>
</rule>
```

## 8. 실습 1~6

### 1 — sysmon-for-linux 설치 확인

```
ssh 6v6-web 'which sysmon 2>&1 || apt-cache policy sysmonforlinux 2>&1 | head'
```

> 본 lab 환경에 sysmon-for-linux 가 사전 설치되어 있지 않을 수 있다. 인프라 단계에서
> 추가 필요. 학습용으로 패턴 + 통합 흐름 중심.

### 2 — config 작성

(시연용 — 실 설치 후 적용)

### 3 — 트리거 + log

```
ssh 6v6-web 'sudo touch /tmp/sysmon_test.sh'
sleep 2
ssh 6v6-web 'sudo tail -3 /var/log/sysmonforlinux.log 2>/dev/null | head' || echo "sysmon not installed"
```

### 4 — Wazuh 통합 시뮬

(localfile 설정 + decoder 매핑)

### 5 — osquery + sysmon 비교

(같은 process 변화를 두 도구로 관찰)

### 6 — 운영 권장 config 적용 시뮬

## 9. 과제

A. sysmon vs osquery 비교 분석 (필수) — 같은 행동 (예: /tmp 에 binary 생성) 을 두 도구로 어떻게 잡는가
B. config XML 작성 (심화) — 본 lab 환경에 맞는 filter 5+
C. Wazuh decoder + rule 작성 (정성) — sysmon 의 ProcessCreate event 를 Wazuh alert 로

## 10. W12-14 (OpenCTI) 예고

다음 3 주차는 OpenCTI 로 외부 위협 인텔리전스 (CTI) 통합 — IOC feed 자동 ingest +
Wazuh 와의 통합 + 위협 헌팅.

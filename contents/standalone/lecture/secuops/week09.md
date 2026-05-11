# Week 09 — Wazuh manager (1) — 구성·디코더·룰

> 본 주차부터 **SIEM (Security Information & Event Management)** 본격 학습. 6v6 의
> `6v6-siem` 컨테이너는 Wazuh 4.10 manager 가 동작하며, fw/ips/web 의 agent 3대 +
> rsyslog forward (bastion/attacker) 의 2 paradigm 입력을 통합 분석한다.

## 학습 목표

1. Wazuh 아키텍처 (manager + indexer + dashboard) 3-tier 이해
2. 16 daemon 중 핵심 5종 (analysisd / remoted / monitord / modulesd / db) 의 역할
3. decoder + rule 두 단계의 로그 처리 흐름
4. 표준 ossec.conf + 사용자 정의 룰 작성 (`/var/ossec/etc/rules/local_rules.xml`)
5. agent 통신 (1514/tcp + 1515/tcp enrollment + 55000/tcp API)
6. 알람 dashboard 의 4 핵심 view (Security Events / Vulnerabilities / SCA / FIM)

## 1. Wazuh 아키텍처

```
                       ┌──────────────────────┐
                       │  wazuh-dashboard      │  5601 (TLS)
                       │  (OpenSearch UI)      │
                       └──────────┬───────────┘
                                  │
                       ┌──────────▼───────────┐
                       │  wazuh-indexer        │  9200 (OpenSearch)
                       │  (색인 + 검색 백엔드)  │
                       └──────────▲───────────┘
                                  │ filebeat (alerts)
                       ┌──────────┴───────────┐
                       │  wazuh-manager (siem) │
                       │   .100                │
                       │  • analysisd          │
                       │  • remoted (1514)     │
                       │  • monitord           │
                       │  • modulesd           │
                       │  • db                 │
                       └─▲─────────────────▲──┘
                         │ agent           │ syslog
                ┌────────┴─────┐  ┌────────┴──────┐
                │ Wazuh agent  │  │ rsyslog       │
                │ (fw/ips/web) │  │ (bastion/attacker)
                └──────────────┘  └───────────────┘
```

### 1.1 16 daemon 중 핵심 5종

| daemon | 역할 |
|--------|------|
| analysisd | 룰 매칭 + alert 생성 (core) |
| remoted | agent TCP 1514 통신 |
| monitord | alert dashboard rotation + 통계 |
| modulesd | vulnerability-scanner / SCA / Wodle 모듈 |
| db | sqlite 기반 internal store |

(W01 에서 11 daemon running 정상 확인)

## 2. decoder + rule 처리 흐름

```
raw log
  │
  ▼
[ logcollector ]  (agent 측 또는 manager 의 syslog 입력)
  │
  ▼
[ decoder ]  (XML: /var/ossec/ruleset/decoders/*.xml)
  │
  ▼  field 추출 (srcip, dstip, user, action, ...)
  │
[ rule ]  (XML: /var/ossec/ruleset/rules/*.xml + local_rules.xml)
  │
  ▼  level 부여 (0~16) + matched group + alert
  │
[ analysisd → /var/ossec/logs/alerts/alerts.json ]
  │
  ▼
[ filebeat → wazuh-indexer ]
  │
  ▼
[ wazuh-dashboard ]
```

### 2.1 decoder 예 (Apache combined log)

```
<decoder name="apache-accesslog">
  <prematch>^\S+ \S+ \S+ \[\S+ \S+\] "\S+ </prematch>
  <regex>^(\S+) \S+ \S+ \[(\S+ \S+)\] "(\S+) (\S+) (HTTP/\d.\d)" (\d+) </regex>
  <order>srcip,timestamp,protocol,url,protocol_version,status_code</order>
</decoder>
```

### 2.2 rule 예 (Apache 4xx 응답)

```
<rule id="31115" level="5">
  <if_sid>31100</if_sid>
  <status>^4\d\d</status>
  <description>Apache 4xx response</description>
  <group>web,access_denied,</group>
</rule>
```

### 2.3 level 분포

| level | 의미 |
|-------|------|
| 0-3 | 정보 (info) |
| 4-6 | 경고 (low) |
| 7-9 | 주의 (medium) |
| 10-12 | 심각 (high) |
| 13-15 | 매우 심각 (critical) |
| 16 | 시스템 (debug) |

dashboard 의 alert filter 가 보통 level >= 7 (medium+).

## 3. 표준 룰셋 위치

```
/var/ossec/ruleset/
├── decoders/        # 200+ XML decoders
├── rules/           # 300+ XML rule files
└── sca/             # CIS benchmark scripts

/var/ossec/etc/
├── ossec.conf       # 메인 manager config
├── rules/
│   └── local_rules.xml  # 사용자 정의
└── decoders/
    └── local_decoder.xml
```

## 4. 사용자 정의 룰 작성

```
<group name="6v6,custom,">

  <rule id="100100" level="8">
    <if_sid>31115</if_sid>
    <url>/admin</url>
    <description>6v6 — Unauthorized /admin access</description>
  </rule>

  <rule id="100101" level="12" frequency="5" timeframe="60">
    <if_matched_sid>100100</if_matched_sid>
    <same_source_ip />
    <description>6v6 — Repeated /admin access (5+ in 60s)</description>
  </rule>

</group>
```

ID range: 사용자 정의는 100000+. ETOpen Wazuh 룰 (5000~99999) 와 충돌 피함.

## 5. agent 통신 포트

| port | protocol | 용도 |
|------|----------|------|
| 1514/tcp | wazuh-protocol | agent → manager event |
| 1515/tcp | wazuh-protocol | agent enrollment (authd) |
| 514/udp | syslog | rsyslog forward |
| 55000/tcp | HTTPS | REST API |

## 6. 핵심 명령

```
# manager 상태
sudo /var/ossec/bin/wazuh-control status
sudo /var/ossec/bin/wazuh-control info

# 등록 agent
sudo /var/ossec/bin/agent_control -l
sudo /var/ossec/bin/agent_control -i 001  # agent 001 상세

# alert 조회
sudo tail -f /var/ossec/logs/alerts/alerts.json | jq .rule

# 룰 reload (재시작 없이)
sudo /var/ossec/bin/wazuh-control restart    # 룰 변경 시 (config 변경 아니면 reload 만)
```

## 7. 실습 1~6

### 실습 1 — manager 상태 + 16 daemon

```
ssh 6v6-siem 'sudo /var/ossec/bin/wazuh-control status'
ssh 6v6-siem 'sudo /var/ossec/bin/wazuh-control info'
```

### 실습 2 — 등록 agent 3대 검증

```
ssh 6v6-siem 'sudo /var/ossec/bin/agent_control -l'
ssh 6v6-siem 'sudo /var/ossec/bin/agent_control -i 001'
```

### 실습 3 — alerts.json 분석

```
ssh 6v6-siem 'sudo tail -200 /var/ossec/logs/alerts/alerts.json | jq -r .rule.id | sort | uniq -c | sort -rn | head'
ssh 6v6-siem 'sudo tail -1 /var/ossec/logs/alerts/alerts.json | jq'
```

### 실습 4 — decoder + rule 매핑

```
ssh 6v6-siem 'sudo grep -l "apache" /var/ossec/ruleset/decoders/*.xml | head'
ssh 6v6-siem 'sudo grep -l "apache" /var/ossec/ruleset/rules/*.xml | head'
```

### 실습 5 — 사용자 정의 룰 추가

```
cat <<'EOF' | sudo tee /var/ossec/etc/rules/local_rules.xml
<group name="6v6,custom,">
  <rule id="100100" level="8">
    <if_sid>31115</if_sid>
    <url>/admin</url>
    <description>6v6 — Unauthorized /admin access</description>
  </rule>
</group>
EOF
ssh 6v6-siem 'sudo /var/ossec/bin/wazuh-control restart'
```

### 실습 6 — 룰 트리거 (attacker → /admin)

```
ssh 6v6-attacker 'curl -s -o /dev/null -H "Host: juice.6v6.lab" http://10.20.30.1/admin'
sleep 5
ssh 6v6-siem 'sudo grep "100100" /var/ossec/logs/alerts/alerts.json | tail -1 | jq'
```

## 8. 과제

A. 사용자 정의 룰 3개 (필수) — sid 100100 / 100101 / 100102 작성 + 트리거 검증
B. decoder 분석 (심화) — Apache modsec_audit.log 의 JSON 디코더 매핑 분석
C. agent 통신 진단 (정성) — 1514/1515/55000 포트 검증 + 진단

## 9. 평가

A 40% / B 35% / C 25%.

## 10. W10 (FIM / SCA / Active Response) 예고

Wazuh agent 의 추가 기능 — File Integrity Monitoring, Security Configuration
Assessment (CIS 벤치마크), Active Response (자동 IP 차단).

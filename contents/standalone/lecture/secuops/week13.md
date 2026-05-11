# Week 13 — OpenCTI (2) — IOC Feed → Wazuh 통합

> W12 의 STIX/TAXII 기초 위에, 실제 외부 IOC feed 를 Wazuh manager 의 **CDB list +
> rule** 로 통합하여 alert 자동 부여. CTI ↔ SIEM 의 가장 단순하고 강력한 통합 패턴.

## 학습 목표

1. Wazuh 의 CDB list (Constant Database) 구조 + 사용 방법
2. OpenCTI / AbuseIPDB / OTX 의 IOC feed → CDB list 변환
3. ossec.conf 의 `<list>` 등록 + rule 의 `list` matching
4. cron 으로 매시간 자동 갱신 패턴
5. IOC 매치 시 alert level 자동 상승 (level 4 → 12)

## 1. Wazuh CDB list

CDB list 는 Wazuh 의 key-value lookup 자료구조. 빠른 lookup (O(1)) + rule 에서 참조.

### 1.1 형식 (단순 텍스트)

```
# /var/ossec/etc/lists/malicious-ips
1.2.3.4:malicious
5.6.7.8:c2
9.10.11.12:botnet
```

key:value. key = IOC, value = 분류 또는 source.

### 1.2 등록 (ossec.conf)

```
<ossec_config>
  <ruleset>
    <list>etc/lists/malicious-ips</list>
  </ruleset>
</ossec_config>
```

### 1.3 매칭 후 자동 빌드

```
sudo /var/ossec/bin/wazuh-control restart
# 또는 단순 reload
sudo /var/ossec/bin/wazuh-control reload
```

자동으로 `etc/lists/malicious-ips.cdb` (binary index) 생성.

## 2. rule 에서 CDB list lookup

```
<rule id="100300" level="12">
  <if_sid>5710</if_sid>             <!-- 기존 룰 (SSH failed login) -->
  <list field="srcip" lookup="address_match_key">etc/lists/malicious-ips</list>
  <description>SSH login from KNOWN malicious IP</description>
</rule>
```

- `list field="srcip"` : 어떤 필드를 lookup 할지
- `lookup="address_match_key"` : IP 매칭 방식
- `etc/lists/malicious-ips` : 위에 등록한 CDB list

이제 SSH failed login (rule 5710) 이 매치된 후, srcip 가 malicious-ips 리스트에 있으면
level 12 critical alert 자동 부여.

## 3. IOC feed → CDB 변환 스크립트

### 3.1 AbuseIPDB 의 daily blacklist

```
#!/bin/bash
# /usr/local/bin/wazuh-ioc-update.sh
set -e
URL="https://lists.blocklist.de/lists/all.txt"
OUT="/var/ossec/etc/lists/malicious-ips"

curl -s "$URL" | grep -v "^#" | grep -v "^$" | head -1000 | \
    awk '{print $1 ":blocklist.de"}' > "${OUT}.new"

mv "${OUT}.new" "$OUT"
/var/ossec/bin/wazuh-control reload
```

cron 으로 매시간:

```
0 * * * * /usr/local/bin/wazuh-ioc-update.sh
```

### 3.2 OpenCTI 의 IOC feed (W14 에서)

OpenCTI 의 REST API 로 indicator export → CDB list 변환.

```
curl -sk -H "Authorization: Bearer $TOKEN" \
  "https://opencti.local/api/v2/indicators?pattern_type=stix&type=ipv4-addr" | \
  jq -r ".data[].pattern" | sed -E "s/.*= '([^']+)'.*/\1:opencti/" > /var/ossec/etc/lists/opencti-ips
```

## 4. 알람 매트릭스 (CTI 통합 효과)

| event | rule_id | level (전) | level (후, IOC 매치) |
|-------|---------|------------|---------------------|
| SSH failed login | 5710 | 5 (medium) | 12 (critical) |
| Web 404 sequence | 31151 | 4 | 12 |
| HTTP unknown UA | 31115 | 3 | 10 |

IOC 매치 1건만으로 alert 우선순위 자동 상승 → SOC 분석가의 효율 향상.

## 5. 실습 1~5

### 1 — CDB list 작성

```
ssh 6v6-siem 'sudo mkdir -p /var/ossec/etc/lists; cat <<EOF | sudo tee /var/ossec/etc/lists/malicious-ips
1.2.3.4:c2_server
5.6.7.8:botnet
185.156.73.31:abuse.ch
EOF
'
```

### 2 — ossec.conf 의 <list> 등록

```
ssh 6v6-siem '
# 중복 확인
sudo grep -q "malicious-ips" /var/ossec/etc/ossec.conf || sudo sed -i "/<ruleset>/a\\    <list>etc\\/lists\\/malicious-ips<\\/list>" /var/ossec/etc/ossec.conf
sudo grep -A2 "<ruleset>" /var/ossec/etc/ossec.conf | head
'
```

### 3 — 사용자 룰 작성 (CDB lookup)

```
ssh 6v6-siem 'cat <<EOF | sudo tee /var/ossec/etc/rules/local_rules.xml
<group name="6v6,custom,">
  <rule id="100300" level="12">
    <if_sid>5710</if_sid>
    <list field="srcip" lookup="address_match_key">etc/lists/malicious-ips</list>
    <description>6v6 - SSH login from malicious IP (CTI)</description>
  </rule>
</group>
EOF
sudo /var/ossec/bin/wazuh-control reload
'
```

### 4 — 트리거 시뮬

```
# malicious-ips 에 등록된 IP 로 SSH 시도 시뮬 (예시)
# 실 환경에선 cron 으로 자동 갱신
```

### 5 — IOC 자동 갱신 cron

```
ssh 6v6-siem 'cat <<EOF | sudo tee /usr/local/bin/wazuh-ioc-update.sh
#!/bin/bash
curl -s https://lists.blocklist.de/lists/all.txt | grep -v "^#" | head -500 | \
    awk "{print \\\$1 \":blocklist.de\"}" > /var/ossec/etc/lists/malicious-ips
/var/ossec/bin/wazuh-control reload
EOF
sudo chmod +x /usr/local/bin/wazuh-ioc-update.sh
'
```

## 6. 과제

A. CDB list 작성 (필수) — 3 카테고리 (malicious-ips / malicious-hashes / malicious-domains) 각각 10+ entry
B. rule 작성 (심화) — CDB list 3개 각각 매칭 rule + level 12
C. 자동 갱신 (정성) — 본인이 선택한 무료 feed (AbuseIPDB / OTX / Disrupt) 의 갱신 스크립트

## 7. W14 (Threat Hunting) 예고

OpenCTI 본격 설치 + Sightings (관측 결과) 등록 + Reports / Notes 등록 + 헌팅
워크플로 (Hypothesis → Investigation → Outcome).

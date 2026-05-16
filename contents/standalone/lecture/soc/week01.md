# W01 — SOC 의 역할 + 3 tier + KPI

> SOC = *24/7 의 사이버 방어 운영 센터*. 3 tier (L1/L2/L3) + 5 KPI (MTTD/MTTR/etc).

## SOC 3 tier
- **L1 Triage** (24/7) — alert 의 *1차 분류*
- **L2 Investigation** — 심화 분석 + IR
- **L3 Hunter** — *unknown* threat hunt + lead

## 5 KPI + 목표
- MTTD < 15 분
- MTTR < 1 시간 (high)
- MTTC < 4 시간
- FPR < 5%
- Coverage 70%+

## 6v6 의 SOC stack
- Wazuh (SIEM)
- Suricata (IDS/IPS)
- ModSec (WAF)
- osquery (EDR-like)
- Bastion (LLM agent)

## 본 과목 의 14 weeks
- W02 Threat Hunting / W03 EDR / W04 SOAR / W05 UEBA / W06 TIP / W07 IR / W08 중간
- W09 ATT&CK rule / W10 Sigma / W11 KQL/SPL / W12 Bastion IR / W13 SOAR playbook
- W14 KPI 보고 / W15 기말

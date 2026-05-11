# CCC Standalone Curriculum — 6v6 인프라 기반 (secuops + attack, non-AI)

> 본 커리큘럼은 학생 PC 의 VMware Bridge VM 1대 안에서 동작하는 **6v6 4-tier 토폴로지**를
> 전제로 한다. 학생은 외부 5개 포트 (80/443/2204/2202/9100) 만으로 16개 컨테이너 전체에
> 접근하며, 모든 트래픽은 `ext → fw → ips → dmz/int` 의 체이닝을 강제로 통과한다.
>
> 본 문서는 secuops (보안 운영) 와 attack (공격) 두 과목의 15주 마스터 플랜이며,
> 각 주차는 `lecture/<course>/week<NN>.md` 와 `lab/<course>/week<NN>.yaml` 한 쌍으로
> 구성된다. 모든 컨텐츠는 수기로 작성하며, Precinct 6 사례·300B 토폴로지 잔재는 포함하지
> 않는다.

## 6v6 4-tier 토폴로지 (필독)

```
   학생 PC ──────────────────────────────────────────────┐
   브라우저 (DNS → VM_IP)                                  │
                                                          ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ ext (10.20.30.0/24)                                          │
   │ ┌──────────┐  ┌──────────┐                                   │
   │ │ bastion  │  │ attacker │                                   │
   │ │  .201    │  │  .202    │                                   │
   │ └────┬─────┘  └────┬─────┘                                   │
   └──────┼─────────────┼───────────────────────────────────────┐ │
          │   default GW: fw 10.20.30.1                         │ │
          ▼             ▼                                       │ │
   ┌─────────────────────────────────────────────────────────────┐
   │ fw (router)                                                  │
   │  ext: .1   ──── nftables + HAProxy + Wazuh agent ──── pipe: .1 │
   └──────────────────────┬──────────────────────────────────────┘
                          │
                          ▼  pipe (10.20.31.0/24)
   ┌─────────────────────────────────────────────────────────────┐
   │ ips (inline)                                                 │
   │  pipe: .2  ──── Suricata + nftables + Wazuh agent ─── dmz: .1  │
   └──────────────────────┬──────────────────────────────────────┘
                          │
                          ▼  dmz (10.20.32.0/24)
   ┌─────────────────────────────────────────────────────────────┐
   │ web (Apache + ModSecurity v2 + OWASP CRS + Wazuh agent)      │
   │   dmz: .80  ────  reverse proxy  ────  int: .80               │
   │                                                              │
   │ siem (Wazuh manager)        .100                              │
   │ wazuh-indexer (OpenSearch)  .110                              │
   │ wazuh-dashboard             .120                              │
   │ portal (FastAPI + HTMX)     .50                               │
   └──────────────────────┬──────────────────────────────────────┘
                          │
                          ▼  int (10.20.40.0/24)
   ┌──────────────┬──────────────┬──────────────┬──────────────┐
   │ juiceshop .81│ dvwa .82     │ neobank .83  │ govportal .84│
   │ mediforum .85│ admin .86    │ aicompanion .87 │            │
   └──────────────┴──────────────┴──────────────┴──────────────┘
```

### 외부 노출 포트 (호스트)

| 포트 | 매핑 | 용도 |
|------|------|------|
| 80   | fw:80     | HTTP — `*.6v6.lab` vhost 11종 |
| 443  | fw:443    | HTTPS (self-signed) |
| 2204 | bastion:22 | bastion SSH (점프 호스트) |
| 2202 | attacker:22 | attacker SSH (직접) |
| 9100 | fw:9100 → bastion API | Bastion API |

### Host vhost (모두 fw → ips → web Apache reverse proxy 경유)

| vhost | 목적 | 백엔드 (int) |
|-------|------|-------------|
| `6v6.lab`         | 랜딩 페이지 | `web` 자체 |
| `juice.6v6.lab`   | Juice Shop | juiceshop:3000 |
| `dvwa.6v6.lab`    | DVWA | dvwa:80 |
| `neobank.6v6.lab` | NeoBank | neobank:3001 |
| `govportal.6v6.lab` | GovPortal | govportal:3002 |
| `mediforum.6v6.lab` | MediForum | mediforum:3003 |
| `admin.6v6.lab`   | AdminConsole | adminconsole:3004 |
| `ai.6v6.lab`      | AICompanion | aicompanion:3005 |
| `siem.6v6.lab`    | Wazuh Dashboard (fw HAProxy 가 backend 라우팅 — WAF 우회) | wazuh-dashboard:5601 |
| `portal.6v6.lab`  | 운영 포털 (fw HAProxy 우회) | portal:8000 |
| `bastion.6v6.lab` | Bastion API (fw HAProxy 우회) | bastion:9100 |

### fw HAProxy 라우팅 규칙 (필수 이해)

```
frontend http_in
  bind *:80
  acl is_siem    hdr(host) -i siem.6v6.lab
  acl is_portal  hdr(host) -i portal.6v6.lab
  acl is_bastion hdr(host) -i bastion.6v6.lab
  use_backend dashboard if is_siem        # WAF 우회 — 운영 트래픽
  use_backend portal    if is_portal      # WAF 우회 — 운영 트래픽
  use_backend bastion   if is_bastion     # WAF 우회 — 운영 트래픽
  default_backend waf                      # 나머지 vhost 는 web (WAF) 경유
```

**중요**: 학생 트래픽 (취약 웹 8종) 은 `fw → ips → web(WAF) → int 백엔드` 4-hop.
운영 트래픽 (siem/portal/bastion API) 은 `fw HAProxy → ips → dmz 직결` 3-hop (WAF 미통과).

### SSH ProxyJump 모델

```
Host 6v6-bastion
  HostName <VM_IP>
  Port 2204
  User ccc

Host 6v6-*
  ProxyJump 6v6-bastion
  User ccc
```

`ssh 6v6-fw`, `ssh 6v6-ips`, `ssh 6v6-web`, `ssh 6v6-siem` 등 — 모두 bastion 경유.
비밀번호 `ccc`. attacker 는 `ssh -p 2202 ccc@<VM_IP>` 로 직접.

---

## secuops (보안 운영, non-AI) — 15주

| Week | 주제 | 핵심 도구 / 6v6 컨테이너 | 비고 |
|------|------|---------------------------|------|
| W01 | 보안 솔루션 개론 + 6v6 4-tier 인프라 | 전체 | DiD, 5종 솔루션 매핑 |
| W02 | nftables 방화벽 (1) — 기초 | `6v6-fw` | table/chain/rule, INPUT/FORWARD |
| W03 | nftables 방화벽 (2) — 실전 (DNAT/SNAT/HAProxy 협업) | `6v6-fw` | fw L4 + HAProxy L7 |
| W04 | Suricata IDS/IPS (1) — 구성 | `6v6-ips` | af-packet, ETOpen 룰셋, eve.json |
| W05 | Suricata IDS/IPS (2) — 룰 작성 | `6v6-ips` | `alert/drop/reject`, content/pcre |
| W06 | Apache + ModSecurity v2 + OWASP CRS WAF | `6v6-web` | SecRuleEngine, audit log, 룰 튜닝 |
| W07 | **osquery — 호스트 가시화** *(신규)* | `6v6-fw/ips/web/bastion` | SQL based hostchk, FIM, process tree |
| W08 | 중간고사 — 방화벽 + IPS + WAF + osquery 구성 실기 | — | 종합 실기 |
| W09 | Wazuh manager (1) — 구성·디코더·룰 | `6v6-siem` (manager) | analysisd, remoted, internal rules |
| W10 | Wazuh agent — FIM / SCA / Active Response | `6v6-fw/ips/web` agents | syscheck, sca, active-response |
| W11 | **sysmon-for-linux — 호스트 이벤트 심층 추적** *(신규)* | `6v6-web/fw/ips` | sysmonforlinux, eBPF, Wazuh ingest |
| W12 | OpenCTI (1) — 설치·STIX·TAXII | OpenCTI 보조 컨테이너 | 데이터 모델, connector 개요 |
| W13 | OpenCTI (2) — 외부 IOC feed → Wazuh 통합 | OpenCTI + `6v6-siem` | MISP/AlienVault, custom CDB list |
| W14 | OpenCTI (3) — Threat hunting (Sightings/Reports) | OpenCTI + Wazuh | 헌팅 워크플로 + ISMS-P 보고 |
| W15 | 기말 — 통합 보안 아키텍처 구축 (전 솔루션 합본) | 전체 | 시나리오: APT 대응 1 사이클 |

## attack (공격, non-AI) — 15주

| Week | 주제 | 핵심 도구 / 6v6 컨테이너 | 비고 |
|------|------|---------------------------|------|
| W01 | 보안 개론 + 6v6 실습 환경 (attacker 컨테이너) | `6v6-attacker` | RoE, 법적 한계, 도구 점검 |
| W02 | 정보수집과 정찰 (Recon) | `6v6-attacker → fw` | nmap, recon-ng, theHarvester |
| W03 | 웹 애플리케이션 구조 + JuiceShop 매핑 | Burp + `juice.6v6.lab` | proxy, 요청·응답 흐름 |
| W04 | OWASP A03 — SQL Injection (DVWA + NeoBank) | sqlmap + `dvwa.6v6.lab` | union/error/boolean/blind |
| W05 | OWASP A03 — XSS (Stored / Reflected / DOM) | xsstrike + `juice/mediforum` | CSP 우회, BeEF |
| W06 | OWASP A01 + A07 — 접근제어·인증 | hydra + `neobank/admin` | IDOR, JWT, brute-force |
| W07 | OWASP A10 + A05 + A03 — SSRF / 파일 업로드 / 경로 탐색 | ffuf + `admin/govportal` | Burp Intruder, FUFF |
| W08 | 중간고사 — CTF 형식 실기 | 8 vuln 사이트 종합 | 90분 |
| W09 | 네트워크 공격 + 패킷 분석 | scapy + tcpdump + `attacker` | ARP, DNS, TCP/IP, MITM |
| W10 | IDS/WAF 우회 (Suricata + ModSecurity) | `6v6-ips/web` 우회 | 페이로드 변조, 인코딩 |
| W11 | Linux 권한 상승 + 후속 정찰 | LinPEAS + `attacker → fw` | SUID, cron, capabilities |
| W12 | 지속성 + 안티포렌식 | rootkit lite + `web` | 백도어, 로그 변조 탐지 우회 |
| W13 | **MITRE Caldera (1) — Adversary Emulation 자동화** *(신규)* | Caldera + `attacker` | red operation, ability/plugin |
| W14 | **MITRE Caldera (2) — Wazuh 와 Purple Team 운영** *(신규)* | Caldera + Wazuh | Atomic Test, AAR, 매트릭스 커버리지 |
| W15 | 기말 — PTES 종합 침투 + 보고서 | 전체 8 vuln + Wazuh | PTES 7 phase |

---

## 작성 원칙 (재강조)

1. **수기 작성**: 매 주차 instruction/script 직접 작성. 일괄 처리·템플릿·자동 스크립트 금지.
2. **6v6 실측 후 다음 주차**: lecture + lab 작성 → 192.168.0.110 에서 모든 step 실행 → 통과 후 push.
3. **Precinct 6 잔재 금지**: 본 커리큘럼 어디에도 Precinct 6 / 300B 토폴로지 / `*.300b.lab` 참조 없음.
4. **Wazuh 4.10 dashboard 한계 인지**: API rate limit 5000/min, login retry 100, block 60s 설정 반영.
5. **MITRE ATT&CK 매핑 일관**: 모든 attack 주차에 TTP ID 명시. Caldera 와 직접 연결.
6. **KISA·ISMS-P 인용**: 한국 환경 특화 사례·표준 매 주차 1건 이상.

## 진행 추적

- `secuops/W01` — IN-PROGRESS
- 나머지 — PENDING

각 주차 완료 시 본 표 갱신 + git commit + push.

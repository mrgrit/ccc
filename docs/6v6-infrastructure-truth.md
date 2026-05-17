# 6v6 인프라 — 단일 진실원 (Truth Source)

> **이 문서는 192.168.0.110 의 실제 상태에서 채취한 사실 (2026-05-17).**
> 모든 lab/lecture 작성·검수·bastion test 디버깅의 기준.
> 표현이 콘텐츠와 충돌하면 콘텐츠를 정정 (이 문서를 정정하지 말 것).

## 1. 호스트와 컨테이너 관계

```
HOST = 192.168.0.110 (실 물리/VM 머신, Ubuntu)
├── 외부 NIC: enp1s0 = 192.168.0.110/24
├── 4 bridge gateway (host 가 .254 보유)
│   ├── br-...30.254  → 6v6-ext  (10.20.30.0/24)
│   ├── br-...31.254  → 6v6-pipe (10.20.31.0/24)
│   ├── br-...32.254  → 6v6-dmz  (10.20.32.0/24)
│   └── br-...40.254  → 6v6-int  (10.20.40.0/24)
└── docker daemon (/var/run/docker.sock)
    └── 16 컨테이너 (평면, bastion 도 그중 하나)
```

**중요**: bastion 위에 다른 컨테이너가 떠있는 게 아니다. bastion 도 16 중 하나.

## 2. 16 컨테이너 (IP + bridge + 역할)

| 컨테이너 | IP (bridge) | 역할 |
|---------|-------------|------|
| 6v6-bastion | 10.20.30.201 (ext) | manager 에이전트. 학생 진입 호스트. docker.sock 마운트. 학생 SSH host:2204 |
| 6v6-attacker | 10.20.30.202 (ext) | 공격 도구. 학생 SSH host:2202 |
| 6v6-fw | 10.20.30.1 (ext) + 10.20.31.1 (pipe) | 방화벽 (nftables). dual NIC = 라우터 모드. host:80/443/9100 publish |
| 6v6-ips | 10.20.31.2 (pipe) + 10.20.32.1 (dmz) | IPS (Suricata). dual NIC = 라우터 모드 |
| 6v6-web | 10.20.32.80 (dmz) + 10.20.40.80 (int) | Apache + ModSecurity. dual NIC = vhost 라우팅 |
| 6v6-siem | 10.20.32.100 (dmz) | Wazuh Manager. :1514/1515/1516 + :55000 |
| 6v6-wazuh-indexer | 10.20.32.110 (dmz) | Wazuh OpenSearch. :9200 (내부) |
| 6v6-wazuh-dashboard | 10.20.32.120 (dmz) | Wazuh UI. :443 |
| 6v6-portal | 10.20.32.50 (dmz) | 운영 portal. :8000. docker.sock 마운트 |
| 6v6-juiceshop | 10.20.40.81 (int) | OWASP Juice Shop. :3000 |
| 6v6-dvwa | 10.20.40.82 (int) | DVWA. :80 |
| 6v6-neobank | 10.20.40.83 (int) | Mock neobank. :3001 |
| 6v6-govportal | 10.20.40.84 (int) | Mock 정부 포털. :3002 |
| 6v6-mediforum | 10.20.40.85 (int) | Mock 의료 포럼. :3003 |
| 6v6-adminconsole | 10.20.40.86 (int) | Mock 관리 콘솔. :3004 |
| 6v6-aicompanion | 10.20.40.87 (int) | Mock AI 동반자. :3005 |

## 3. 4 bridge (4-tier 토폴로지)

- **ext (10.20.30.0/24)** — 학생/공격자 진입. bastion(.201) + attacker(.202) + fw ext side(.1)
- **pipe (10.20.31.0/24)** — fw ↔ ips. fw(.1) + ips(.2)
- **dmz (10.20.32.0/24)** — 외부 노출 서비스. ips(.1) + web(.80) + siem(.100) + indexer(.110) + dashboard(.120) + portal(.50)
- **int (10.20.40.0/24)** — 내부 vhost. web(.80) + juiceshop(.81) + dvwa(.82) + neobank(.83) + govportal(.84) + mediforum(.85) + adminconsole(.86) + aicompanion(.87)

학생/공격자 트래픽 경로: **ext → fw → pipe → ips → dmz → web → int → vhost**

## 4. docker.sock 마운트 (host docker daemon 접근 가능 컨테이너)

| 컨테이너 | docker.sock mount | docker cli |
|---------|-------------------|------------|
| 6v6-bastion | YES | `/usr/bin/docker` 설치 |
| 6v6-portal | YES | (운영 시각화 용도) |
| 그 외 14 개 | NO | — |

**의미**: `docker ps` 로 16 컨테이너 보려면 host 의 socket 필요. bastion / portal 만 가능. attacker / fw / ips / web / siem 등에서는 docker 자체가 없음.

## 5. subagent (:8002) 떠있는 컨테이너

| 컨테이너 | :8002 subagent | 비고 |
|---------|-----------------|------|
| 6v6-attacker | YES | /opt/subagent |
| 6v6-fw | YES | /opt/subagent |
| 6v6-ips | YES | /opt/subagent |
| 6v6-web | YES | /opt/subagent |
| 6v6-siem | YES (ad-hoc) | `python3 /tmp/subagent.py` — 임시 위치 |
| 6v6-bastion | **NO** | manager 자체이므로 — ★ 결정 필요 |
| 그 외 9 개 (portal/wazuh-*/juiceshop/dvwa/neobank/govportal/mediforum/adminconsole/aicompanion) | NO | lab 에서 직접 명령 보내면 connection refused |

## 6. bastion API 실행 위치 + manager 호출 라우팅 (★ 함정)

**현재 배포 상태** (2026-05-17 확인):
- `bastion API` (`run-api.py`, port 9200) = **host (192.168.0.110) 의 ccc 사용자 process**
  - 즉 bastion 컨테이너 안이 아니라 **host 에서 직접 도는 python**
- host:9200 → PID 218723 (host) listening

**manager 호출 라우팅 (`VM_MANAGER_IP=10.20.30.201` 의 결과)**:
1. agent → `run_command(ip='10.20.30.201', script='docker ps')`
2. `_is_local_ip('10.20.30.201')` 판정 → **host ip addr** 스캔 (host 의 .254 만 있고 .201 없음) → **False**
3. → `httpx.post('http://10.20.30.201:8002/a2a/run_script')` 시도
4. 10.20.30.201 = bastion 컨테이너 IP, 그 안에 :8002 subagent 없음 → **Connection refused**
5. agent 가 manager 회피 → 다른 target (attacker/web/secu) 으로 trial → 거기서는 docker 없으니 빈 결과

**근본 fix 3 옵션**:
- (A) bastion 컨테이너 안에 subagent (:8002) 띄움 → manager 호출이 컨테이너 안 subagent 로. docker.sock + cli 있으므로 docker ps 16 보임.
- (B) `VM_MANAGER_IP=127.0.0.1` 로 변경 → `_is_local_ip(127.0.0.1)` true → bash 로컬 실행 → host 에서 docker ps → 16 보임. host 가 docker daemon 호스트 자체이므로.
- (C) bastion API 를 bastion 컨테이너 안으로 옮김 → 컨테이너의 ip addr 에 10.20.30.201 있으므로 `_is_local_ip(10.20.30.201)` true → bash 직접 → docker ps 16. architecture intent (manager = bastion 컨테이너) 와 가장 일치.

## 7. 학생 SSH 진입 모델

학생 PC 의 `~/.ssh/config` 가정:
```
Host 6v6-bastion
  HostName 192.168.0.110
  Port 2204
  User ccc

Host 6v6-attacker
  HostName 192.168.0.110
  Port 2202
  User ccc

Host 6v6-fw 6v6-ips 6v6-web 6v6-siem ...
  ProxyJump 6v6-bastion
  User ccc
```

- 학생 → `ssh 6v6-bastion` → host:2204 → bastion 컨테이너:22 → bastion 컨테이너 OS shell
- 학생 → `ssh 6v6-fw` → ProxyJump 통해 bastion 거쳐 fw 컨테이너 :22
- 비밀번호: `ccc` / `1` (학습 환경 전용). NOPASSWD sudo

## 8. host 외부 publish 포트 (학생 PC 에서 직접 접근 가능)

| host port | → 컨테이너 | 용도 |
|----------|------------|------|
| 192.168.0.110:2202 | 6v6-attacker:22 | 학생 SSH (공격자 역할) |
| 192.168.0.110:2204 | 6v6-bastion:22 | 학생 SSH (운영자 역할, jump host) |
| 192.168.0.110:80 | 6v6-fw:80 | HAProxy (host header → backend 라우팅) |
| 192.168.0.110:443 | 6v6-fw:443 | HAProxy TLS |
| 192.168.0.110:9100 | 6v6-fw:9100 | (학생 portal 또는 운영 API) |
| 192.168.0.110:9200 | (host process) | bastion API |

## 9. 콘텐츠 작성 시 자주 틀리는 표현

| 잘못된 표현 | 정정 |
|------------|------|
| "bastion 호스트" | "bastion 컨테이너" — bastion 은 호스트 아님. 호스트는 6v6 머신(192.168.0.110) |
| "bastion 에 컨테이너가 떠있다" | "host 에 16 컨테이너가 떠있고 bastion 도 그중 하나" |
| "공격 VM / 4-VM" | "공격 컨테이너 (6v6-attacker)" — VM 모델은 legacy. 6v6 는 컨테이너 |
| `ssh ccc@10.20.30.X` | `ssh 6v6-<name>` (학생 PC) 또는 `ssh -J 6v6-bastion <name>` (점프) |
| "siem VM 에서 ..." | "siem 컨테이너 (10.20.32.100) 에서 ..." |
| "manager VM 의 ollama" | "manager LLM (192.168.0.109:11434 Ollama 서버)" — Ollama 는 별도 호스트 |

## 10. 검수·디버깅 체크리스트

각 lab/lecture 파일 검수 시 확인:

- [ ] "bastion 호스트" / "bastion VM" 등 컨테이너 ↔ 호스트 혼동 표현 없는가
- [ ] IP 가 6v6 대역 (10.20.30/31/32/40.x) 또는 192.168.0.110 인가 (legacy 10.0.0.X / 192.168.X.X 잔재 없는가)
- [ ] 4-VM 모델 (attacker/secu/web/siem 만) 잔재 없는가. 16 컨테이너 사용
- [ ] `ssh 6v6-<name>` 패턴이 학생 PC 의 `~/.ssh/config` 전제로 작성됐는가
- [ ] step.target_vm 이 lab YAML 에 명시되어 있는가 (bastion 자율 실행 매핑 위함)
- [ ] R/B/P (Red/Blue/Purple) 모든 주차 포함 + 다이어그램
- [ ] Precinct 6 실제 사례 언급 제거됨
- [ ] secuops 양식 일관 (frontmatter / objectives / steps / verify.semantic)

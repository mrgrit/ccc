# 2026-04-29 세션 핸드오프 — 다음 세션 계속 진행용

> **새 세션 시작 시 이 파일 + `docs/inflight-projects.md` 먼저 읽기**

## 1. 인프라 현재 상태 (2026-04-30 기준)

### VM 매핑 (DHCP 라 IP 변동 가능 — 콘솔에서 hostname 확인 권장)
| VM | external (ens33) | internal (ens37) | hostname | 비고 |
|---|---|---|---|---|
| bastion (manager) | 192.168.0.103 | 10.20.30.200/24 | bastion | uvicorn :8003 |
| secu (방화벽 GW) | 192.168.0.108 | 10.20.30.1/24 | secu | nft DNAT GW |
| siem | 192.168.0.111 | 10.20.30.100/24 | siem | Wazuh + OpenCTI docker |
| web | 192.168.0.100 | 10.20.30.80/24 | web | Apache+ModSec + JuiceShop + 5 vuln-sites |
| attacker | 192.168.0.112 | (없음) | black | pentest 도구 13종 설치됨 |

### 서비스 외부 접근 (모두 secu 통한 단일 IP, port 로 destination 결정)
```
http://192.168.0.108/          → JuiceShop (web :80, Apache+ModSecurity 통과)
https://192.168.0.108/         → Wazuh Dashboard (siem :443, self-signed cert)
http://192.168.0.108:8080/     → OpenCTI (siem :8080, admin@opencti.io / CCC2026!)
http://192.168.0.108:1514/     → Wazuh agent enrollment
http://192.168.0.108:1515/     → Wazuh agent enrollment
http://192.168.0.108:55000/    → Wazuh API
http://192.168.0.108:3001/     → NeoBank vuln-site
http://192.168.0.108:3002/     → GovPortal
http://192.168.0.108:3003/     → MediForum
http://192.168.0.108:3004/     → AdminConsole
http://192.168.0.108:3005/     → AICompanion
```
**중요**: web/siem 직접 IP (192.168.0.100/0.111) 접근은 **차단**됨 (DOCKER-USER iptables + nft input)

### OpenCTI 자격증명
- Email: `admin@opencti.io`
- Password: `CCC2026!`
- API Token (UUID): `ebb7e01b-5b13-4896-8926-2a2d4de87414`

## 2. R3 측정 종합 결과

### V2 round (256 cases, 2026-04-29 13:23 종료)
| Verdict | Count |
|---|---|
| pass | 70 (27.0%) |
| fail | 171 |
| no_execution | 13 |
| qa_fallback | 4 |
| error | 1 |

### attack-ai supplemental (94 cases, 2026-04-29 21:09 종료)
| Verdict | Count |
|---|---|
| pass | **32 (34.0%)** |
| fail | 60 |
| no_execution | 2 |

### Course 별 회복 효과 (R3 main → V2)
- **battle-adv-ai**: 0% → 36.2% (+36.2pt) ★★★
- **battle-ai**: 4.3% → 32.1% (+27.8pt) ★★
- ai-security-ai: 18.2% → 25.4% (+7.2pt) ★
- attack-adv-ai: 0% → 13.6% (+13.6pt) ★

### Paper §6.2 핵심 finding
**timeout 280→600s fix 가 dominant**: 116/259 (44.8%) cases 가 280s 초과 → pre-fix 면 timeout.

### 산출물
- `results/retest/v2_paper_metrics.json` — V2 측정 metrics
- `results/retest/r3_paper_metrics.json` — R3 main metrics
- `results/retest/run_r3_noexec_v2.log` — V2 driver log
- `results/retest/run_r3_attack_supplemental.log` — supplemental log
- `scripts/r3_v2_paper_metrics.py` — 메트릭 재생성 스크립트

## 3. 이번 세션 commits (시간순, cron 제외)

| Commit | 내용 |
|---|---|
| 6f29749e | web-vuln OWASP payload library prompt |
| 297354eb | attack-ai 94 ERROR supplemental queue 준비 |
| 7698b790 | r3_v2_paper_metrics 비교 표 |
| 5c744db6 | timeout fix dominant 정량화 |
| 1730f364 | V2 cursor 209/256 partial finding |
| cbe13bd3 | post_v2_chain 자동화 |
| c0af0aaf | web-vuln-ai prompt: attacker IP 192.168.0.100 |
| 6173dec9 | attacker VM + web 외부 IP 발견 기록 |
| a1c20cf7 | netplan 영구화 + bastion IP env 화 |
| e38b9845 | secu 외부 NIC port forwarding (8 service) |
| d1a62e8a | web role vuln-sites 5종 자동 배포 |
| a9b3ab68 | OpenCTI token UUID 형식 |
| c7849540 | course2-secops/week01 WAF 실측 반영 |
| 9d9856e5 | web/siem 외부 직접 접근 차단 (secu only) |
| d27ac397 | vuln-sites flask 버전 완화 |
| 0c5a3137 | V2 종료 — paper §6.2 metric 최종화 |
| f6e987e9 | Docker daemon DNS 8.8.8.8 — vuln-sites build fix |

모두 `mrgrit/ccc` main push 완료.

## 4. 운영 중 백그라운드 프로세스

```bash
# 1) bastion watchdog (PID 3176778) — 60s 간격 health, 5fail 시 SSH 재시작
ps -ef | grep bastion_watchdog
# 환경: BASTION_HEALTH=http://192.168.0.103:8003/health
```

V2 driver / supplemental driver / post_v2_chain 모두 정상 종료됨.

## 5. 미완 / 다음 세션 작업

### 즉시 가능 (V2 데이터 완성됨)
1. **Paper §6.2 R3 → V2 비교 표 작성** — 사용자가 "paper 는 나중에 하자"고 했으나 데이터 다 있음
   - 입력: `results/retest/v2_paper_metrics.json` + `results/retest/r3_paper_metrics.json`
   - 출력: `contents/papers/bastion/paper-draft.md` 의 §6.2 채우기
   - Course 별 회복 표 + timeout dominant finding 명시

2. **siem nft 영구화** — 직접 적용한 nft 가 /etc/nftables.conf 에 저장됐는지 확인. siem reboot 시도 안 한 상태.
   ```bash
   sshpass -p 1 ssh ccc@192.168.0.111 "grep DOCKER-USER /etc/iptables/rules.v4 | head"
   ```

3. **inflight-projects.md 갱신** — V2 종료, supplemental 종료, NAT 작업 완료 반영.

4. **memory 정리** — `~/.claude/projects/-home-opsclaw-ccc/memory/` 의 P15 closed 파일 정리.

### 보류 작업
- **attacker VM SSH 비번 변동** 가능성 (현재 ccc/1, hostname black @ 192.168.0.112). 재부팅 시 재확인.
- **secu/siem/manager 의 vmnet mismatch** 진단 — bastion ens37 ARP sweep 해도 web 만 응답, secu/siem 은 docker bridge 우회로 가능. 정상 vmnet 일 수도 있고 의도된 격리일 수도 있음.
- **post_v2_chain 의 sync_to_bastion 실패** — bastion IP 가 0.103 으로 변경됐는데 sync_to_bastion.sh 의 REMOTE_HOST 가 0.115 hardcoded. env 화 또는 업데이트 필요.

### 차세대 작업 (paper / R4 round 등)
- R4 round 측정 (V2 fix + OWASP prompt 적용 후 전체 재측정)
- vuln-sites E2E PoC 검증 (외부 접근 + WAF + Wazuh alert 연쇄)
- P14 lab 1건 학생 직접 측정

## 6. 인프라 영구 fix (다음 온보딩 자동 적용)

`packages/bastion/__init__.py` 에 다음 추가됨:
1. **netplan 영구화** (line 1003) — internal NIC IP reboot 시 사라지지 않게
2. **secu DNAT 11 rule** — 외부 NIC :80/:443/:8080/:1514/:1515/:55000/:3001-3005 → 내부 매핑
3. **web vuln-sites 자동 배포** — onboard_vm() 에서 contents/vuln-sites/ tar 업로드 + docker-compose
4. **Docker DNS 8.8.8.8** — 컨테이너 build 시 pypi 도달 가능
5. **외부 NIC 직접 접근 차단** — DOCKER-USER iptables + nft input
6. **OpenCTI token UUID 형식** — APP__ADMIN__TOKEN validation

## 7. 환경변수 / 자격증명

```bash
# Bastion
BASTION_HOST=192.168.0.103              # 변경 시 sync_to_bastion.sh + scripts/test_step.py 갱신
BASTION_URL=http://192.168.0.103:8003    # ccc-api 가 사용
BASTION_HEALTH=http://192.168.0.103:8003/health
BASTION_GRAPH_DB=/opt/bastion/data/bastion_graph.db   # KG path 영구 fix env

# VM SSH (모두 동일)
SSH_USER=ccc
SSH_PASS=1
SSH_PORT=22

# Attacker (예외)
ATTACKER_HOST=192.168.0.112
ATTACKER_USER=ccc        # hostname 은 black 이지만 SSH user 는 ccc
ATTACKER_PASS=1

# OpenCTI
OPENCTI_EMAIL=admin@opencti.io
OPENCTI_PASS=CCC2026!
OPENCTI_TOKEN=ebb7e01b-5b13-4896-8926-2a2d4de87414  # 현재 운영
# (코드 default 는 a8f3b0c2-9d1e-4f56-8a2b-7c4d3e1f9b8a — 새 온보딩 시)

# Ollama (외부 LLM)
LLM_BASE_URL=http://192.168.0.105:11434
LLM_MODEL=gpt-oss:120b                  # manager
LLM_MODEL_UNSAFE=gurubot/gpt-oss-derestricted:120b  # attack-* 과목
```

## 8. 다음 세션 시작 명령

```bash
cd /home/opsclaw/ccc

# 1) 이 핸드오프 + 미완 트래커 + 메모리 읽기
cat docs/2026-04-29-session-handoff.md
cat docs/inflight-projects.md | head -50

# 2) 백그라운드 프로세스 확인
ps -ef | grep -E "watchdog|driver_r3|post_v2" | grep -v grep

# 3) bastion 헬스
curl -s http://192.168.0.103:8003/health

# 4) R3 결과 확인
python3 scripts/r3_v2_paper_metrics.py | tail -25
```

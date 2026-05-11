# Week 13 — MITRE Caldera (1) — Adversary Emulation 자동화 (신규)

> 본 주차는 **MITRE Caldera** 가 학습 대상. ATT&CK 기반 자동화 red team 도구로,
> 학생은 abilities / adversary profile 작성 + agent 배포 + operation 실행 → 자동
> 캠페인 진행. 6v6 환경의 attacker 컨테이너에 Caldera 추가 설치.

## 학습 목표

1. Caldera 아키텍처 (Server + Agent + Abilities + Adversary)
2. ATT&CK 기반 ability 작성 (yaml)
3. agent (sandcat) 배포
4. operation 실행 + 결과 분석
5. autonomous adversary profile
6. ATT&CK Navigator + Caldera 통합

## 1. Caldera 가 무엇인가?

MITRE 의 오픈소스 adversary emulation 플랫폼. 2018년 출시. 핵심 기능:

- ATT&CK 의 Technique 을 yaml ability 로 정의
- 여러 ability 묶어 adversary profile 작성
- agent (sandcat / manx) 가 target host 에서 실행
- operation 으로 자동 캠페인 진행

```
┌────────────────────┐
│  Caldera Server    │  REST API + web UI (8888)
│  (Python aiohttp)  │
└─────────┬──────────┘
          │
          ▼  REST + WebSocket
┌────────────────────┐
│  agent (sandcat)   │  target host 에서 실행
│  - Linux/Win/Mac   │
└────────────────────┘
```

## 2. ability 작성

```yaml
- id: 12345
  name: Disk Enumeration
  description: List local disks
  tactic: discovery
  technique:
    attack_id: T1083
    name: File and Directory Discovery
  platforms:
    linux:
      sh:
        command: |
          ls -la /
```

각 ability 가 한 명령을 정의 + ATT&CK 매핑.

## 3. adversary profile

```yaml
- id: 67890
  name: 6v6 Linux Adversary
  description: 6v6 학습용 Linux 적
  atomic_ordering:
    - 12345  # Disk Enum
    - 12346  # User Enum
    - 12347  # /tmp 의 binary 다운로드
    - 12348  # 권한 상승 시도
```

## 4. operation

```
Operation = (Adversary, Target Group, Schedule)

# 진행 흐름
operation.start()
  → adversary.abilities 순차 실행
  → 각 ability 가 agent 에 명령 send
  → agent 가 결과 return
  → 다음 ability
```

## 5. 6v6 환경에 Caldera 설치

attacker 컨테이너에 추가 (Dockerfile 수정 또는 별도 컨테이너):

```
git clone --branch master https://github.com/mitre/caldera.git --recursive
cd caldera
pip install -r requirements.txt
python server.py --insecure
# http://localhost:8888 (admin / admin)
```

agent 배포 (target 측 — 본 lab 에서는 attacker 자체로 시연):

```
curl -sk -X POST 'http://localhost:8888/file/download' \
    -H "platform: linux" -H "file: sandcat.go" -OJ
chmod +x sandcat-linux
./sandcat-linux -server http://localhost:8888 -group blue
```

## 6. 운영 가치

- ATT&CK 기반 표준 적대 행위 시뮬
- 방어 측 (SOC) 의 detection 성능 측정
- Purple Team (red+blue) 운영 표준
- compliance audit (적대 시뮬 + 보고서)

## 7. 실습 1~4

### 1 — Caldera 설치 시뮬

```
ssh 6v6-attacker '
# 실 설치는 시간 + 의존성 → 시뮬
echo "git clone https://github.com/mitre/caldera.git"
echo "pip install aiohttp aiohttp-cors aiohttp-jinja2 pyyaml..."
'
```

### 2 — ability yaml 작성 예시

```
cat <<'EOF'
- id: 6v6-001
  name: 6v6 — File Discovery
  tactic: discovery
  technique: { attack_id: T1083 }
  platforms:
    linux:
      sh:
        command: |
          find /etc -name "*.conf" -type f | head -10
EOF
```

### 3 — adversary profile

```
cat <<'EOF'
- id: 6v6-adv-01
  name: 6v6 Recon Adversary
  atomic_ordering:
    - 6v6-001
    - 6v6-002
    - 6v6-003
EOF
```

### 4 — operation 시뮬 결과

(실 Caldera 미설치 시 시뮬 보고서)

## 8. 과제

A. ability 3개 (필수) — 본 lab 환경에 적합한 3 ability + ATT&CK 매핑
B. adversary profile (심화)
C. detection 성능 분석 (정성) — 본 lab 의 Wazuh + Suricata 가 adversary 캠페인을 어떻게 잡는가

## 9. W14 (Caldera + Wazuh Purple Team) 예고

Caldera 의 adversary 캠페인 → Wazuh detection 측정 → Purple Team 운영.

# Week 04: 런타임 보안

## 학습 목표
- 컨테이너 런타임의 보안 위협(권한 상승, 탈출)을 이해한다
- `--privileged` 플래그의 위험성을 설명할 수 있다
- Linux capability와 seccomp 프로파일을 활용한 보안 강화를 실습한다
- 컨테이너 탈출 시나리오를 직접 재현하고 방어 방법을 익힌다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (Docker/클라우드/K8s 보안 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **컨테이너** | Container | 앱과 의존성을 격리하여 실행하는 경량 가상화 | 이삿짐 컨테이너 (어디서든 동일하게 열 수 있음) |
| **이미지** | Image (Docker) | 컨테이너를 만들기 위한 읽기 전용 템플릿 | 붕어빵 틀 |
| **Dockerfile** | Dockerfile | 이미지를 빌드하는 레시피 파일 | 요리 레시피 |
| **레지스트리** | Registry | 이미지를 저장·배포하는 저장소 (Docker Hub 등) | 앱 스토어 |
| **레이어** | Layer (Image) | 이미지의 각 빌드 단계 (캐싱 단위) | 레고 블록 한 층 |
| **볼륨** | Volume | 컨테이너 데이터를 영구 저장하는 공간 | 외장 하드 |
| **네임스페이스** | Namespace (Linux) | 프로세스를 격리하는 커널 기능 (PID, NET, MNT 등) | 칸막이 (같은 건물, 서로 안 보임) |
| **cgroup** | Control Group | 프로세스의 CPU/메모리 사용량을 제한하는 커널 기능 | 전기/수도 사용량 제한 |
| **오케스트레이션** | Orchestration | 다수의 컨테이너를 관리·조율하는 것 (K8s) | 오케스트라 지휘 |
| **Pod** | Pod (K8s) | K8s의 최소 배포 단위 (1개 이상의 컨테이너) | 같은 방에 사는 룸메이트들 |
| **RBAC** | Role-Based Access Control | 역할 기반 접근 제어 (K8s) | 직책별 출입 권한 |
| **PSP/PSA** | Pod Security Policy/Admission | Pod의 보안 설정을 강제하는 정책 | 건물 입주 조건 |
| **NetworkPolicy** | NetworkPolicy (K8s) | Pod 간 네트워크 통신 규칙 | 부서 간 출입 통제 |
| **Trivy** | Trivy | 컨테이너 이미지 취약점 스캐너 (Aqua) | X-ray 검사기 |
| **IaC** | Infrastructure as Code | 인프라를 코드로 정의·관리 (Terraform 등) | 건축 설계도 (코드 = 설계도) |
| **IAM** | Identity and Access Management | 클라우드 사용자/권한 관리 (AWS IAM 등) | 회사 사원증 + 권한 관리 시스템 |
| **CIS 벤치마크** | CIS Benchmark | 보안 설정 모범 사례 가이드 (Center for Internet Security) | 보안 설정 모범답안 |

---

# Week 04: 런타임 보안

## 학습 목표
- 컨테이너 런타임의 보안 위협(권한 상승, 탈출)을 이해한다
- `--privileged` 플래그의 위험성을 설명할 수 있다
- Linux capability와 seccomp 프로파일을 활용한 보안 강화를 실습한다
- 컨테이너 탈출 시나리오를 직접 재현하고 방어 방법을 익힌다

---

## 1. 컨테이너 격리의 원리

Docker 컨테이너는 Linux 커널의 3가지 기능으로 격리된다:

| 기술 | 역할 | 예시 |
|------|------|------|
| **Namespace** | 프로세스/네트워크/파일시스템 격리 | PID, NET, MNT |
| **Cgroup** | 리소스 사용량 제한 | CPU, 메모리, I/O |
| **Capability** | root 권한 세분화 | NET_BIND_SERVICE, SYS_ADMIN |

중요: 컨테이너는 호스트 커널을 공유한다. 격리가 깨지면 호스트 전체가 위험해진다.

---

## 2. --privileged의 위험

> **이 실습을 왜 하는가?**
> "런타임 보안" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> Docker/클라우드/K8s 보안 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

`--privileged` 플래그는 모든 보안 제한을 해제한다.

> **실습 목적**: 컨테이너 런타임의 capability와 privilege 설정이 보안에 미치는 영향을 직접 비교하기 위해 수행한다
>
> **배우는 것**: --privileged 컨테이너가 호스트 디바이스에 접근 가능한 이유와, --cap-drop ALL로 권한을 제거했을 때 차단되는 동작을 이해한다
>
> **결과 해석**: CapEff 값이 클수록 권한이 많으며, capsh --decode로 어떤 capability가 부여되었는지 확인한다
>
> **실전 활용**: 컨테이너 탈출 방지를 위한 런타임 보안 정책 수립 및 seccomp/AppArmor 프로파일 설계에 활용한다

```bash
# 절대 프로덕션에서 사용하지 말 것
docker run --privileged -it ubuntu bash
```

### --privileged가 하는 일

- 모든 Linux capability 부여 (약 40개)
- 모든 디바이스(/dev/*) 접근 허용
- seccomp, AppArmor 프로파일 비활성화
- /proc, /sys 쓰기 가능

### --privileged 컨테이너에서 호스트 접근

```bash
# privileged 컨테이너 내부에서
# 호스트 디스크 마운트 가능
mkdir /mnt/host
mount /dev/sda1 /mnt/host
ls /mnt/host  # 호스트 파일시스템 전체 접근!
```

---

## 3. Linux Capabilities

root 권한을 세분화한 것이 capability이다.
컨테이너에 필요한 최소한의 capability만 부여해야 한다.

### 주요 Capability

| Capability | 의미 | 위험도 |
|-----------|------|--------|
| `SYS_ADMIN` | 거의 root 수준 | 매우 높음 |
| `NET_ADMIN` | 네트워크 설정 변경 | 높음 |
| `NET_RAW` | raw 소켓 생성 | 중간 |
| `NET_BIND_SERVICE` | 1024 이하 포트 바인딩 | 낮음 |
| `CHOWN` | 파일 소유자 변경 | 중간 |

### Capability 관리

```bash
# 모든 capability 제거 후 필요한 것만 추가
docker run -d \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --name secure-web \
  nginx:latest

# 컨테이너의 capability 확인
docker inspect --format='{{.HostConfig.CapDrop}}' secure-web
docker inspect --format='{{.HostConfig.CapAdd}}' secure-web
```

---

## 4. Seccomp 프로파일

Seccomp(Secure Computing Mode)은 컨테이너가 호출할 수 있는 시스템콜을 제한한다.

### 기본 seccomp 프로파일

Docker는 기본적으로 약 300개 시스템콜 중 위험한 44개를 차단한다.
차단 목록: `unshare`, `mount`, `reboot`, `kexec_load` 등

```bash
# 기본 seccomp 프로파일 확인
docker inspect --format='{{.HostConfig.SecurityOpt}}' my-container

# 커스텀 seccomp 프로파일 적용
docker run --security-opt seccomp=my-profile.json nginx
```

### 커스텀 프로파일 예시

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat",
                "mmap", "mprotect", "brk", "exit_group"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

---

## 5. 컨테이너 탈출 시나리오

### 5.1 /proc/sysrq-trigger 악용

```bash
# privileged 컨테이너에서
echo b > /proc/sysrq-trigger  # 호스트 즉시 재부팅!
```

### 5.2 Docker 소켓 마운트 악용

```bash
# Docker 소켓이 마운트된 컨테이너
docker run -v /var/run/docker.sock:/var/run/docker.sock ubuntu

# 컨테이너 내부에서 호스트에 새 컨테이너 생성 가능
# (docker CLI 설치 후)
docker run --privileged -v /:/host ubuntu chroot /host
```

### 5.3 cgroup release_agent 탈출

SYS_ADMIN capability가 있으면 cgroup을 통해 호스트에서 명령 실행이 가능하다.

---

## 6. 런타임 보안 강화 방법

### 6.1 읽기 전용 파일시스템

컨테이너 파일시스템을 읽기 전용으로 설정하여 악성 파일 쓰기를 차단한다. 임시 파일이 필요한 경로만 tmpfs로 허용한다.

```bash
# --read-only: 루트 파일시스템 쓰기 금지 (악성 파일 설치 차단)
# --tmpfs: 메모리 기반 임시 경로 허용 (컨테이너 삭제 시 자동 소멸)
docker run --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  nginx:latest
```

### 6.2 no-new-privileges

프로세스가 실행 중에 새로운 권한을 얻는 것을 방지한다.

```bash
docker run --security-opt no-new-privileges nginx:latest
```

### 6.3 리소스 제한

컨테이너가 호스트 리소스를 독점하지 못하도록 메모리, CPU, 프로세스 수를 제한한다. DoS 공격이나 포크 폭탄 방지에 필수적이다.

```bash
# --memory: 메모리 상한 (초과 시 OOM Kill)
# --cpus: CPU 사용량 제한 (0.5 = 50%)
# --pids-limit: 최대 프로세스 수 (포크 폭탄 방지)
docker run -d \
  --memory=256m \
  --cpus=0.5 \
  --pids-limit=100 \
  nginx:latest
```

---

## 7. 실습: 컨테이너 보안 점검

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: capability 비교

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# 기본 실행 (기본 capability 포함)
docker run --rm alpine sh -c 'cat /proc/1/status | grep Cap'

# 모든 capability 제거
docker run --rm --cap-drop ALL alpine sh -c 'cat /proc/1/status | grep Cap'

# CapEff 값을 capsh로 해독
docker run --rm alpine sh -c \
  'apk add -q libcap && capsh --decode=00000000a80425fb'
```

### 실습 2: 읽기 전용 vs 쓰기 가능

```bash
# 쓰기 가능 컨테이너 (기본)
docker run --rm alpine sh -c 'echo hacked > /etc/passwd; echo "성공"'

# 읽기 전용 컨테이너
docker run --rm --read-only alpine sh -c 'echo hacked > /etc/passwd; echo "성공"'
# 결과: Read-only file system 에러
```

### 실습 3: Docker 소켓 노출 위험 확인

```bash
# 절대 프로덕션에서 하지 말 것 (학습 목적만)
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  docker:cli docker ps
# 컨테이너 내부에서 호스트의 모든 컨테이너 조회 가능!
```

---

## 8. 보안 점검 체크리스트

- [ ] `--privileged` 사용하지 않는가?
- [ ] `--cap-drop ALL` 후 필요한 것만 추가했는가?
- [ ] `--read-only` 파일시스템을 사용하는가?
- [ ] `--security-opt no-new-privileges` 적용했는가?
- [ ] Docker 소켓을 마운트하지 않는가?
- [ ] 메모리/CPU/PID 제한을 설정했는가?

---

## 핵심 정리

1. `--privileged`는 모든 보안 장벽을 해제하므로 절대 사용하지 않는다
2. `--cap-drop ALL` 후 필요한 capability만 `--cap-add`로 추가한다
3. Seccomp 프로파일로 불필요한 시스템콜을 차단한다
4. Docker 소켓 마운트는 호스트 전체 제어 권한을 넘겨주는 것과 같다
5. 읽기 전용 파일시스템 + no-new-privileges로 기본 방어선을 구축한다

---

## 다음 주 예고
- Week 05: Docker 네트워크 보안 - 네트워크 격리, 포트 노출, 컨테이너 간 통신 제어

---

---

## 심화: 컨테이너/클라우드 보안 보충

### Docker 보안 핵심 개념 상세

#### 컨테이너 격리의 원리

```
호스트 OS 커널
├── Namespace (격리)
│   ├── PID namespace  → 컨테이너마다 독립 프로세스 번호
│   ├── NET namespace  → 컨테이너마다 독립 네트워크 스택
│   ├── MNT namespace  → 컨테이너마다 독립 파일시스템
│   ├── UTS namespace  → 컨테이너마다 독립 hostname
│   └── USER namespace → 컨테이너 내 root ≠ 호스트 root (설정 시)
│
├── cgroup (자원 제한)
│   ├── CPU:    --cpus=2          → 최대 2코어
│   ├── Memory: --memory=512m     → 최대 512MB
│   └── IO:     --blkio-weight=500
│
└── Overlay FS (레이어 파일시스템)
    ├── 읽기 전용 레이어 (이미지)
    └── 읽기/쓰기 레이어 (컨테이너)
```

> **왜 컨테이너가 VM보다 가벼운가?**
> VM: 각각 전체 OS 커널을 포함 (수 GB)
> 컨테이너: 호스트 커널을 공유, 격리만 namespace로 (수 MB)
> 대신 격리 수준은 VM이 더 강하다 (커널 취약점 시 컨테이너 탈출 가능)

#### Dockerfile 보안 체크리스트

```dockerfile
# 나쁜 예
FROM ubuntu:latest          # ❌ latest 태그 (재현 불가)
RUN apt-get update && apt-get install -y curl vim  # ❌ 불필요 패키지
COPY . /app                 # ❌ 전체 복사 (.env 포함 가능)
RUN chmod 777 /app          # ❌ 과도한 권한
USER root                   # ❌ root 실행
EXPOSE 22                   # ❌ SSH 포트 (컨테이너에서 불필요)

# 좋은 예
FROM ubuntu:22.04@sha256:abc123...  # ✅ 특정 버전 + digest 고정
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*  # ✅ 최소 패키지 + 캐시 삭제
COPY --chown=appuser:appuser app/ /app  # ✅ 필요한 것만 + 소유자 지정
RUN chmod 550 /app          # ✅ 최소 권한
USER appuser                # ✅ 비root 사용자
HEALTHCHECK CMD curl -f http://localhost:8080 || exit 1  # ✅ 헬스체크
```

### 실습: Docker 보안 점검 (실습 인프라)

```bash
# web 서버의 Docker 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "
  echo '=== Docker 버전 ===' && docker --version 2>/dev/null || echo 'Docker 미설치'
  echo '=== 실행 중 컨테이너 ===' && docker ps 2>/dev/null || echo '접근 불가'
  echo '=== Docker 소켓 권한 ===' && ls -la /var/run/docker.sock 2>/dev/null
" 2>/dev/null

# siem 서버의 Docker 상태 (OpenCTI가 Docker로 실행)
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "
  echo '=== Docker 컨테이너 ===' && sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' 2>/dev/null
  echo '=== Docker 네트워크 ===' && sudo docker network ls 2>/dev/null
" 2>/dev/null
```

### CIS Docker Benchmark 핵심 항목

| # | 항목 | 점검 명령 | 기대 결과 |
|---|------|---------|---------|
| 2.1 | Docker daemon 설정 | `cat /etc/docker/daemon.json` | userns-remap 설정 |
| 4.1 | 비root 사용자 | `docker inspect --format '{{.Config.User}}' <컨테이너>` | root가 아닌 사용자 |
| 4.6 | HEALTHCHECK | `docker inspect --format '{{.Config.Healthcheck}}' <컨테이너>` | 헬스체크 설정됨 |
| 5.2 | network_mode | `docker inspect --format '{{.HostConfig.NetworkMode}}' <컨테이너>` | host가 아닌 것 |
| 5.12 | --privileged | `docker inspect --format '{{.HostConfig.Privileged}}' <컨테이너>` | false |

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** Docker 컨테이너와 VM의 핵심 차이는?
- (a) 컨테이너가 더 안전  (b) **컨테이너는 호스트 커널을 공유, VM은 별도 커널**  (c) VM이 더 가벼움  (d) 차이 없음

**Q2.** '--cap-drop ALL'의 의미는?
- (a) 모든 파일 삭제  (b) **모든 Linux capability를 제거하여 권한 최소화**  (c) 네트워크 차단  (d) 로그 비활성화

**Q3.** 컨테이너가 --privileged로 실행되면 위험한 이유는?
- (a) 속도가 느려짐  (b) **호스트의 거의 모든 자원에 접근 가능 (탈출 가능)**  (c) 로그가 안 남음  (d) 이미지가 커짐

**Q4.** Trivy의 역할은?
- (a) 컨테이너 실행  (b) **컨테이너 이미지의 알려진 취약점(CVE) 스캐닝**  (c) 네트워크 설정  (d) 로그 수집

**Q5.** Dockerfile에서 USER root가 위험한 이유는?
- (a) 빌드가 느려짐  (b) **컨테이너 탈출 시 호스트 root 권한 획득 가능**  (c) 이미지가 커짐  (d) 네트워크 안 됨

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): Docker 29.3.0, Compose v5.1.1, juice-shop(User=65532,Privileged=false), OpenCTI 6컨테이너, opencti_default 네트워크

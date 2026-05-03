# Week 03: 이미지 보안

## 학습 목표
- Docker 이미지의 보안 위험을 이해한다
- Trivy를 사용하여 이미지 취약점을 스캔할 수 있다
- 안전한 베이스 이미지 선택 기준을 설명할 수 있다
- 이미지에 포함된 시크릿을 탐지할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

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

## 1. 이미지 보안이 중요한 이유

Docker 이미지는 애플리케이션과 모든 의존성을 포함한다.
이미지 내에 취약한 라이브러리, 노출된 비밀키, 불필요한 도구가 포함되면
컨테이너 실행 시 바로 공격 표면이 된다.

### 대표적인 이미지 보안 위협

| 위협 | 설명 | 예시 |
|------|------|------|
| 취약한 패키지 | 알려진 CVE가 있는 라이브러리 | Log4j, OpenSSL 취약점 |
| 시크릿 노출 | 이미지 레이어에 저장된 비밀정보 | API 키, DB 비밀번호 |
| 악성 베이스 이미지 | 신뢰할 수 없는 출처의 이미지 | Docker Hub 비공식 이미지 |
| 과도한 패키지 | 불필요한 도구 포함 | gcc, wget, curl 등 |

---

## 2. Trivy: 컨테이너 이미지 스캐너

> **이 실습을 왜 하는가?**
> 컨테이너 이미지에는 수십~수백 개의 라이브러리가 포함되며, 각각에 알려진 취약점(CVE)이 있을 수 있다.
> `bkimminich/juice-shop:latest` 이미지에 CRITICAL 취약점이 몇 개나 있는지 아는가?
> Trivy 한 번으로 전체 취약점 목록을 뽑을 수 있다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 현재 사용 중인 이미지에 알려진 취약점이 몇 개 있는지
> - CRITICAL/HIGH 취약점의 CVE 번호와 영향받는 패키지
> - 어떤 베이스 이미지를 선택해야 취약점이 적은지
>
> **실무 활용:**
> - CI/CD 파이프라인에 Trivy를 통합하여 취약 이미지 배포 차단
> - 운영 중인 컨테이너를 정기 스캐닝하여 새로 발견된 CVE 확인
> - 보안 감사에서 "컨테이너 이미지 취약점 점검 결과" 보고서 제출
>
> **검증 완료:** web 서버의 JuiceShop 이미지(753MB)와 siem 서버의 OpenCTI 이미지 확인

Trivy는 Aqua Security에서 만든 오픈소스 취약점 스캐너이다.
이미지, 파일시스템, Git 저장소의 취약점을 검출한다.

### 2.1 Trivy 설치

> **실습 목적**: 컨테이너 이미지에 숨어있는 알려진 취약점(CVE)을 Trivy로 스캔하여 사전에 발견하기 위해 수행한다
>
> **배우는 것**: Trivy가 이미지 레이어를 분석하여 CRITICAL/HIGH 취약점을 리포트하는 원리와, 베이스 이미지 선택이 취약점 수에 미치는 영향을 이해한다
>
> **결과 해석**: Total 행의 CRITICAL/HIGH 수가 0이면 안전하고, 수치가 높을수록 즉시 패치 또는 이미지 교체가 필요하다
>
> **실전 활용**: CI/CD 파이프라인에 Trivy를 통합하여 취약 이미지의 프로덕션 배포를 자동 차단하는 데 활용한다

```bash
# Ubuntu/Debian
sudo apt-get install -y wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | \
  sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install -y trivy
```

### 2.2 이미지 스캔

```bash
# 기본 스캔: 모든 심각도 표시
trivy image nginx:latest

# HIGH, CRITICAL만 필터링
trivy image --severity HIGH,CRITICAL nginx:latest

# JSON 출력 (자동화에 활용)
trivy image -f json -o result.json nginx:latest
```

### 2.3 스캔 결과 읽기

```
nginx:latest (debian 12.4)
Total: 45 (HIGH: 12, CRITICAL: 3)

+-------------------------------------------------------------+
| Library   | Vulnerability    | Severity | Fixed Version     |
+-------------------------------------------------------------+
| libssl3   | CVE-2024-XXXXX   | CRITICAL | 3.0.13-1~deb12u1  |
| zlib1g    | CVE-2023-XXXXX   | HIGH     | 1:1.2.13.dfsg-1   |
+-------------------------------------------------------------+
```

- **CRITICAL**: 즉시 패치 필요 (원격 코드 실행 등)
- **HIGH**: 빠른 시일 내 패치 필요
- **MEDIUM/LOW**: 계획적 패치

---

## 3. 안전한 베이스 이미지 선택

### 3.1 이미지 크기와 보안의 관계

이미지가 클수록 공격 표면이 넓다. 불필요한 패키지가 취약점이 된다.

```bash
# 이미지 크기 비교
docker images | grep python
# python:3.11        → 약 920MB (OS 전체 + 빌드 도구)
# python:3.11-slim   → 약 150MB (최소 런타임)
# python:3.11-alpine → 약  50MB (musl libc 기반)
```

### 3.2 베이스 이미지 선택 기준

| 이미지 | 장점 | 단점 | 추천 용도 |
|--------|------|------|----------|
| `ubuntu:22.04` | 익숙함 | 크기 큼 | 개발/테스트 |
| `python:3.11-slim` | 적절한 균형 | 일부 패키지 부족 | 프로덕션 |
| `alpine:3.19` | 매우 작음 | 호환성 문제 가능 | 경량 서비스 |
| `distroless` | 셸 없음, 최소 | 디버깅 어려움 | 보안 중시 환경 |

### 3.3 멀티스테이지 빌드

빌드 도구는 최종 이미지에 포함하지 않는다.

```dockerfile
# Stage 1: 빌드
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: 실행 (빌드 도구 제외)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

---

## 4. 이미지 내 시크릿 탐지

### 4.1 시크릿이 이미지에 남는 경우

```dockerfile
# 위험: 삭제해도 이전 레이어에 남아있음
COPY secret.key /app/
RUN cat /app/secret.key && rm /app/secret.key
```

Docker 이미지는 레이어 구조이므로, 한 레이어에서 파일을 추가하고
다음 레이어에서 삭제해도 **이전 레이어에 그대로 남아있다**.

### 4.2 이미지 히스토리 확인

```bash
# 이미지 빌드 히스토리 확인
docker history nginx:latest

# 특정 레이어의 파일 확인
docker save nginx:latest | tar -xf - -C /tmp/nginx-layers/
ls /tmp/nginx-layers/
```

### 4.3 Trivy로 시크릿 스캔

```bash
# 이미지 내 시크릿 스캔
trivy image --scanners secret nginx:latest

# 파일시스템 시크릿 스캔
trivy fs --scanners secret /path/to/project
```

---

## 5. 실습: web 서버에서 이미지 보안 점검

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: JuiceShop 이미지 취약점 스캔

```bash
ssh ccc@10.20.30.80

# JuiceShop 이미지 스캔
trivy image bkimminich/juice-shop:latest --severity HIGH,CRITICAL

# 결과에서 CRITICAL 취약점 개수 확인
trivy image bkimminich/juice-shop:latest --severity CRITICAL -f json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
  print(sum(len(r.get('Vulnerabilities',[])) for r in d.get('Results',[])))"
```

### 실습 2: 안전한 이미지 vs 위험한 이미지 비교

```bash
# 풀 이미지 스캔
trivy image python:3.11 --severity HIGH,CRITICAL 2>/dev/null | tail -5

# slim 이미지 스캔
trivy image python:3.11-slim --severity HIGH,CRITICAL 2>/dev/null | tail -5

# alpine 이미지 스캔
trivy image python:3.11-alpine --severity HIGH,CRITICAL 2>/dev/null | tail -5
```

### 실습 3: 시크릿이 포함된 이미지 만들고 탐지하기

```bash
# 시크릿 포함 Dockerfile 작성
mkdir -p /tmp/secret-test && cd /tmp/secret-test
cat > secret.key << 'EOF'
-----BEGIN RSA PRIVATE KEY-----
MIIBogIBAAJBALRiMLAHudeSA/fake/key/for/demo/only
-----END RSA PRIVATE KEY-----
EOF

cat > Dockerfile << 'EOF'
FROM alpine:latest
COPY secret.key /app/secret.key
RUN cat /app/secret.key && rm /app/secret.key
CMD ["echo", "hello"]
EOF

# 빌드 및 스캔
docker build -t secret-test .
trivy image --scanners secret secret-test

# 정리
docker rmi secret-test
```

---

## 6. 이미지 보안 자동화

### CI/CD 파이프라인에 Trivy 통합

```bash
# CRITICAL 취약점이 있으면 빌드 실패
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# exit code 0: 통과, 1: 취약점 발견
echo "Exit code: $?"
```

### 이미지 서명 (신뢰 체인)

```bash
# Docker Content Trust 활성화
export DOCKER_CONTENT_TRUST=1

# 서명된 이미지만 pull 가능
docker pull nginx:latest  # 서명 검증 후 다운로드
```

---

## 핵심 정리

1. Docker 이미지에는 취약한 패키지, 시크릿, 악성 코드가 숨어있을 수 있다
2. Trivy로 이미지 스캔하여 CRITICAL/HIGH 취약점을 사전에 발견한다
3. slim/alpine/distroless 등 최소 이미지를 사용하여 공격 표면을 줄인다
4. 멀티스테이지 빌드로 빌드 도구를 최종 이미지에서 제거한다
5. 이미지 레이어에 시크릿이 영구 저장되므로 절대 Dockerfile에 넣지 않는다

---

## 다음 주 예고
- Week 04: 런타임 보안 - 권한 상승, 컨테이너 탈출, --privileged 위험

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
ssh ccc@10.20.30.80 "
  echo '=== Docker 버전 ===' && docker --version 2>/dev/null || echo 'Docker 미설치'
  echo '=== 실행 중 컨테이너 ===' && docker ps 2>/dev/null || echo '접근 불가'
  echo '=== Docker 소켓 권한 ===' && ls -la /var/run/docker.sock 2>/dev/null
" 2>/dev/null

# siem 서버의 Docker 상태 (OpenCTI가 Docker로 실행)
ssh ccc@10.20.30.100 "
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

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Trivy
> **역할:** 이미지·파일시스템·IaC·K8s CVE/미스컨피그 스캐너  
> **실행 위치:** `임의 호스트 / CI`  
> **접속/호출:** `trivy image <img>` / `trivy fs .` / `trivy config .`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.cache/trivy/` | 취약점 DB 캐시 |
| `.trivyignore` | 무시할 CVE ID 목록 |

**핵심 설정·키**

- `--severity HIGH,CRITICAL` — 심각도 필터
- `--ignore-unfixed` — 수정본 없는 CVE 제외
- `--format sarif` — CI용 SARIF 출력

**UI / CLI 요점**

- `trivy image --exit-code 1 --severity HIGH,CRITICAL <img>` — CI 게이트
- `trivy k8s --report summary cluster` — 클러스터 전체 요약

> **해석 팁.** `--ignore-unfixed`는 잡음을 크게 줄이지만 **미래 위험**을 숨긴다. 이미지 재빌드 주기와 함께 운영 기준을 정하자.

### Dockerfile 보안 작성
> **역할:** 최소 권한·재현성·비밀 격리  
> **실행 위치:** `빌드 호스트`  
> **접속/호출:** `docker build -t img .`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `Dockerfile` | 빌드 정의 |
| `.dockerignore` | 이미지에 포함하지 않을 파일 |

**핵심 설정·키**

- `FROM <distroless|alpine>` — 최소 베이스
- `USER 1000` — 비root 실행
- `RUN --mount=type=secret,id=NPM_TOKEN` — 빌드 비밀 외부 주입
- `HEALTHCHECK CMD ...` — 컨테이너 헬스체크

**로그·확인 명령**

- ``docker history <img>`` — 레이어별 변경 크기·명령

**UI / CLI 요점**

- `docker scout cves <img>` — 이미지 CVE 스캔
- `dive <img>` — 레이어별 파일 변경 시각화

> **해석 팁.** `COPY . .` 전에 `.dockerignore`로 `.git`, `.env` 제외. 빌드 시 `ARG SECRET=...` 는 **이미지 메타데이터에 남는다** — 비밀은 BuildKit `--secret` 사용.

---

## 실제 사례 (WitFoo Precinct 6 — 이미지 보안)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *이미지 스캔 / 서명 / registry / supply chain* 학습 항목 매칭.

### 이미지 supply chain 결함이 어떻게 운영 사고로 이어지는가

이미지 보안의 핵심 위험은 **"빌드 단계에서 들어간 결함이 운영 단계에서 폭로된다"** 는 시간차에 있다. Dockerfile 한 줄, layer 1개에 박힌 시크릿, latest 태그로 가져온 검증 안 된 base image — 이 모든 결함은 빌드 시점에는 거의 보이지 않다가, 컨테이너가 실제로 동작하면서 *registry pull, runtime access, lateral movement* 의 신호를 만들기 시작한다.

dataset 에서 이 변환 경로를 따라가면 — 이미지 manifest 조회는 174,293건의 Describe\* 군 호출로, 컨테이너 runtime 의 호스트 자원 접근은 4662 (226,215건) 로, 결국 leaked credential 의 사용은 mo_name=Auth Hijack 의 edge 로 분류되어 등장한다.

```mermaid
graph LR
    BUILD["image build<br/>(Dockerfile)"] -->|latest tag<br/>secret 박힘| PUSH[registry push]
    PUSH -->|정상 pull| AR["Describe* call<br/>174,293건<br/>(manifest 조회)"]
    PUSH -->|secret 누출 시| DT["mo_name=Data Theft<br/>(데이터 탈취 edge)"]
    AR -->|컨테이너 run| OBJ["event 4662<br/>226,215건<br/>(객체 접근)"]
    OBJ -->|leaked cred 사용| HIJ["mo_name=Auth Hijack<br/>(인증 탈취 edge)"]

    style BUILD fill:#ffe6cc
    style DT fill:#ffcccc
    style HIJ fill:#ff9999
```

**그림이 보여주는 것**: 노란 박스 (build) 의 결함은 즉시 발견되지 않는다. registry push 까지는 정상 운영처럼 보이지만, 누군가 image layer 를 까서 secret 을 추출하는 순간 — 빨간 박스 (Data Theft / Auth Hijack edge) 로 비약한다. lecture §"image scan" 과 §"image sign" 은 빌드 → push 단계 사이에 *결함 검출 게이트* 를 설치하는 것이 목적이다.

### Case 1: Describe\* 174,293건 — 이미지 manifest enumeration 의 baseline

| 항목 | 값 | 의미 |
|---|---|---|
| message_type | `Describe*` | DescribeInstanceStatus 27,127 + 기타 147K 군 |
| 총 호출 | 174,293건 | 가장 많이 호출되는 cloud API 군 |
| 학습 매핑 | §1 이미지 layer / manifest | registry 노출 시 enumerate 가능 영역 |
| 위험 패턴 | 동일 IAM 의 burst | recon timeline 의 첫 단계 |

**자세한 해석**:

ECR/GCR/ACR 같은 컨테이너 registry 는 *image manifest* 라는 메타데이터 (layer 목록, 환경변수, ENTRYPOINT 등) 를 외부에 노출한다. 이 manifest 조회는 cloud 에서 모두 `Describe*` 군 호출로 분류된다 — DescribeImages, DescribeRepositories, DescribeImageScanFindings 등.

dataset 174,293건은 정상 운영 한 달치 — *대부분이 CI/CD 와 ECS scheduler 의 자동 호출* 이다. 학생이 알아야 할 것은 — **공격자가 leaked IAM key 로 ECR 에 진입하면, 그가 가장 먼저 하는 행동이 Describe\* 군 호출** 이다. 어떤 image 들이 있는지, 어떤 layer 가 있는지, 환경변수가 노출되어 있는지를 모두 manifest 에서 한 번에 알아낼 수 있다.

따라서 — "정상 caller 5개의 분포" 와 "비정상 신규 caller 의 짧은 burst" 를 구분할 수 있어야 한다. dataset 174K 의 caller 분포를 보면 보통 5-10개 IAM 으로 수렴 — 11번째 신규 caller 의 시간당 1,000건 burst = recon 시작.

### Case 2: leaked image credential → Auth Hijack edge 변환

| 항목 | 값 | 의미 |
|---|---|---|
| edge type | `Auth Hijack` | 인증 탈취 패턴의 edge 분류 |
| 발생 조건 | image 내 secret 노출 + 외부 사용 | image scan 누락 시 흔히 발생 |
| 학습 매핑 | §"secret 을 image 에 넣지 말 것" | 위반 시 dataset 분류 결과 |

**자세한 해석**:

학생이 Dockerfile 에 `ENV DB_PASSWORD=admin123` 같은 한 줄을 박으면 — 그 비밀번호는 image layer 에 평문으로 저장된다. Image 가 public registry 에 push 되거나, IAM 이 노출되어 외부에서 pull 가능하면, 누구든 `docker history --no-trunc` 한 번으로 그 비밀번호를 추출할 수 있다.

추출된 비밀번호로 공격자가 *원래 그 secret 의 정당한 사용처에 로그인* 하면 — dataset 에서는 *Auth Hijack* edge 로 분류된다. 정상 caller 가 들어와야 할 곳에 비정상 caller 가 같은 자격으로 들어왔기 때문이다.

이는 lecture 가 강조하는 **"image scan + sign + minimal layer 의 3중 방어"** 가 무력화되는 경로다 — scan 을 안 하면 secret 이 layer 에 남고, sign 을 안 하면 가짜 image 가 push 될 수 있고, minimal layer 가 아니면 불필요한 도구가 함께 노출된다. 세 방어 중 하나만 빠져도 Auth Hijack edge 로 직결.

### 이 사례에서 학생이 배워야 할 3가지

1. **이미지 결함은 빌드 시점에 거의 보이지 않는다** — 운영 단계의 신호로만 폭로되므로 빌드 게이트 + runtime 모니터링이 모두 필요.
2. **Describe\* 174K 에서 비정상 caller 1개를 찾아내는 것이 recon 차단의 첫 단계** — caller 분포 baseline 을 알아둬야 가능.
3. **image 1개의 secret 노출은 곧 Auth Hijack** — image scan + sign + minimal layer 3중 방어가 모두 필요.

**학생 액션**: 본인이 작성한 Dockerfile 에서 (1) `ENV PASSWORD=*` 류 평문 secret, (2) `.dockerignore` 누락으로 인한 `.git/.env` 포함, (3) `latest` 태그 사용 의 3가지를 점검하고, Trivy 또는 docker scan 으로 1회 스캔한 결과를 보고서에 첨부. 발견된 issue 별로 *"이 결함이 운영 환경에서 어느 dataset 신호로 폭로되는가"* 를 한 줄씩 작성.


---

## 부록: 학습 OSS 도구 매트릭스 (Course6 Cloud-Container — Week 03 컨테이너 기초)

### 컨테이너 보안 도구 — Build·Push·Run 단계별

| 단계 | 도구 | 역할 |
|------|------|------|
| Dockerfile lint | **hadolint** / dockerfile-spec | 모범 사례 |
| Image build | **docker** / podman / buildah / kaniko | 빌드 |
| 이미지 scan | **Trivy** / Grype / Clair / Anchore | CVE |
| Secret scan | **gitleaks** / trufflehog / detect-secrets | secret 누출 |
| Layer 분석 | **dive** / docker-history-cli | 최소화 |
| Dockerfile 보안 점검 | **dockle** / docker-bench-security | CIS |
| 서명 / SBOM | **cosign** / sigstore / syft | 공급망 |
| Registry 보안 | **Harbor** (CNCF, OSS) / Docker Registry + 인증 | private registry |
| Runtime 격리 | **Podman** rootless / gVisor / Kata | runtime |

### 핵심 — Trivy 종합 사용 (4 모드)

```bash
# 1) image (CVE 스캔 — 가장 자주)
trivy image --severity HIGH,CRITICAL alpine:3.18
trivy image --severity HIGH,CRITICAL --format json -o /tmp/trivy.json alpine:3.18
trivy image --ignore-unfixed alpine:3.18                      # fix 가능 CVE 만

# 2) fs (코드+secret+IaC 한번에)
trivy fs /path/to/project --scanners vuln,secret,config
# → CVE + 평문 secret + IaC 미설정 한 번에

# 3) k8s (전체 클러스터)
trivy k8s --report summary cluster

# 4) image with SBOM
trivy image --format spdx-json --output sbom.json alpine:3.18
syft alpine:3.18 -o spdx-json > sbom2.json                    # syft 도 SBOM
```

### 학생 환경 준비

```bash
# 1주차에 설치한 도구 (Trivy, hadolint, dockle, dive, Falco, docker-bench)

# 추가 설치
sudo apt install -y skopeo                                   # 이미지 다중 registry 도구

# Grype (Trivy 대안 — 로컬 vuln DB)
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sudo sh -s -- -b /usr/local/bin

# Syft (SBOM 생성 — Anchore)
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sudo sh -s -- -b /usr/local/bin

# gitleaks (secret 스캔)
curl -L https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.18.0_linux_x64.tar.gz | tar xz
sudo mv gitleaks /usr/local/bin/

# trufflehog
docker pull trufflesecurity/trufflehog:latest

# cosign (이미지 서명)
sudo curl -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o /usr/local/bin/cosign
sudo chmod +x /usr/local/bin/cosign

# Harbor (CNCF 그래데이트, private registry)
curl -L https://github.com/goharbor/harbor/releases/latest/download/harbor-online-installer-v2.10.0.tgz | tar xz -C /tmp
# /tmp/harbor/install.sh 으로 설치
```

### 핵심 도구별 사용법

```bash
# 1) hadolint — Dockerfile 정적 분석
hadolint Dockerfile
# 발견 가능한 issue:
# DL3008: pin versions in apt-get install
# DL3009: cleanup apt-get cache
# DL3015: --no-install-recommends 누락
# DL3025: latest 태그 사용

# 2) dockle — Dockerfile + image 보안 점검
dockle alpine:3.18
# CIS-DI-0001: USER 명령 없음 (root 로 실행)
# CIS-DI-0008: setuid/setgid 파일 존재
# DKL-DI-0006: latest 태그

# 3) dive — 이미지 layer 시각화
dive alpine:3.18
# 키:
#   Tab     : 패널 전환
#   Ctrl-F  : 검색
#   Ctrl-A  : aggregated 모드 (전체 변화)
# 목표: efficiency score > 95%

# 4) gitleaks — git repo 의 secret 발견
gitleaks detect --source /path/to/repo --redact
gitleaks detect -v --no-git --source /path/to/code

# 5) cosign — 이미지 서명
cosign generate-key-pair                                     # cosign.key, cosign.pub
cosign sign --key cosign.key registry.local/myimg:v1
cosign verify --key cosign.pub registry.local/myimg:v1

# 6) Harbor — private registry (Docker Registry 대안)
# Web UI: https://harbor.local
# Vulnerability 자동 스캔 (Trivy 통합)
# 서명된 이미지만 pull 가능 (cosign 통합)
docker login harbor.local
docker push harbor.local/project/myimg:v1
```

### 이미지 보안 4 단계 흐름

```bash
# Phase 1: Build-time (shift-left)
hadolint Dockerfile                                          # 정적 분석
docker build -t myimage:v1 .
trivy image myimage:v1                                       # CVE
syft myimage:v1 -o spdx-json > sbom.json                     # SBOM
gitleaks detect --no-git --source .                          # secret

# Phase 2: Push-time (signing + registry)
cosign sign --key cosign.key registry/myimage:v1
docker push registry/myimage:v1
# Harbor 가 vulnerability 자동 스캔, FAIL 시 push 차단

# Phase 3: Runtime (kubernetes admission)
# OPA Gatekeeper / Kyverno 가 cosign verify → 서명 없으면 거부

# Phase 4: Continuous monitoring
trivy image --report summary cluster                         # k8s 전체 정기 스캔
falco                                                        # runtime 행위 모니터
```

### CVE 발견 시 대응

| 심각도 | 대응 |
|-------|------|
| Critical (CVSS 9.0+) | 즉시 빌드 차단, 24h 내 패치 |
| High (7.0-8.9) | 7일 내 패치 |
| Medium (4.0-6.9) | 30일 내 패치 |
| Low (< 4.0) | 다음 정기 빌드 |

### CI/CD 통합 예 (GitLab CI / GitHub Actions)

```yaml
# .gitlab-ci.yml
stages:
  - build
  - scan

build:
  stage: build
  script:
    - hadolint Dockerfile
    - docker build -t $IMG .
    
scan:
  stage: scan
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 $IMG
    - syft $IMG -o spdx-json > sbom.json
    - cosign sign --key $COSIGN_KEY $IMG
  artifacts:
    paths: [sbom.json]
```

학생은 본 3주차에서 **hadolint + Trivy + dive + cosign + Harbor** 5 도구로 컨테이너 build → push → run 전체 파이프라인의 보안 통제를 OSS 만으로 구축한다.

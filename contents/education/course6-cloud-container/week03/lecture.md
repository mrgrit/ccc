# Week 03: 이미지 보안

## 학습 목표
- Docker 이미지의 보안 위험을 이해한다
- Trivy를 사용하여 이미지 취약점을 스캔할 수 있다
- 안전한 베이스 이미지 선택 기준을 설명할 수 있다
- 이미지에 포함된 시크릿을 탐지할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
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

# Week 03: 이미지 보안

## 학습 목표
- Docker 이미지의 보안 위험을 이해한다
- Trivy를 사용하여 이미지 취약점을 스캔할 수 있다
- 안전한 베이스 이미지 선택 기준을 설명할 수 있다
- 이미지에 포함된 시크릿을 탐지할 수 있다

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

+-----------+------------------+----------+-------------------+
| Library   | Vulnerability    | Severity | Fixed Version     |
+-----------+------------------+----------+-------------------+
| libssl3   | CVE-2024-XXXXX   | CRITICAL | 3.0.13-1~deb12u1 |
| zlib1g    | CVE-2023-XXXXX   | HIGH     | 1:1.2.13.dfsg-1   |
+-----------+------------------+----------+-------------------+
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
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

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

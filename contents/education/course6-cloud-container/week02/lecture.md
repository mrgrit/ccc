# Week 02: Docker 기초 + 보안

## 학습 목표
- Docker의 핵심 개념(이미지, 컨테이너, 네트워크, 볼륨)을 이해한다
- Dockerfile을 작성하고 보안 관점에서 점검할 수 있다
- 컨테이너 기반 환경의 보안 이점과 위험을 설명할 수 있다

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

# Week 02: Docker 기초 + 보안

## 학습 목표
- Docker의 핵심 개념(이미지, 컨테이너, 네트워크, 볼륨)을 이해한다
- Dockerfile을 작성하고 보안 관점에서 점검할 수 있다
- 컨테이너 기반 환경의 보안 이점과 위험을 설명할 수 있다

---

## 1. Docker란 무엇인가?

Docker는 애플리케이션을 **컨테이너**라는 격리된 환경에서 실행하는 기술이다.
가상머신(VM)과 달리 OS 커널을 공유하므로 가볍고 빠르다.

### VM vs 컨테이너 비교

| 항목 | 가상머신 | 컨테이너 |
|------|---------|---------|
| 부팅 시간 | 분 단위 | 초 단위 |
| 크기 | GB | MB |
| 격리 수준 | 하드웨어 수준 | 프로세스 수준 |
| 보안 격리 | 강함 | 상대적으로 약함 |

---

## 2. Docker 핵심 구성요소

> **이 실습을 왜 하는가?**
> "Docker 기초 + 보안" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> Docker/클라우드/K8s 보안 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 이미지 (Image)
컨테이너를 만들기 위한 읽기 전용 템플릿이다. 여러 **레이어**로 구성된다.

> **실습 목적**: Docker 컨테이너의 보안 설정을 직접 점검하고 안전한 실행 방법을 체험하기 위해 수행한다
>
> **배우는 것**: docker inspect로 User, Privileged, CapAdd 등 보안 속성을 확인하고, --read-only, --cap-drop ALL 옵션의 효과를 이해한다
>
> **결과 해석**: User 필드가 비어있으면 root 실행, Privileged=true면 모든 보안 해제 상태를 의미한다
>
> **실전 활용**: 프로덕션 컨테이너 배포 전 보안 체크리스트 점검 및 CIS Docker Benchmark 준수 확인에 활용한다

```bash
# 이미지 다운로드
docker pull nginx:latest

# 로컬 이미지 목록
docker images
```

### 2.2 컨테이너 (Container)
이미지를 실행한 인스턴스이다. 격리된 파일시스템, 네트워크, 프로세스를 가진다.

```bash
# 컨테이너 실행
docker run -d --name my-nginx -p 8080:80 nginx:latest

# 실행 중인 컨테이너 확인
docker ps

# 컨테이너 내부 접속
docker exec -it my-nginx /bin/bash
```

### 2.3 네트워크 (Network)
컨테이너 간 통신을 제어한다. 기본적으로 bridge, host, none 네트워크가 있다.

```bash
# 네트워크 목록
docker network ls

# 사용자 정의 네트워크 생성
docker network create my-secure-net
```

### 2.4 볼륨 (Volume)
컨테이너 데이터를 영구 저장하는 방법이다. 컨테이너가 삭제되어도 데이터가 유지된다.

```bash
# 볼륨 생성
docker volume create my-data

# 볼륨 마운트하여 실행
docker run -d -v my-data:/app/data nginx:latest
```

---

## 3. Dockerfile 작성

Dockerfile은 이미지를 빌드하기 위한 명령어 모음이다.

```dockerfile
# 기본 이미지 지정
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 비root 사용자로 전환
RUN useradd -m appuser
USER appuser

# 포트 노출
EXPOSE 8000

# 실행 명령
CMD ["python", "app.py"]
```

---

## 4. Dockerfile 보안 베스트 프랙티스

### 4.1 비root 사용자 사용
```dockerfile
# 나쁜 예: root로 실행 (기본값)
CMD ["python", "app.py"]

# 좋은 예: 전용 사용자 생성
RUN useradd -r -s /bin/false appuser
USER appuser
CMD ["python", "app.py"]
```

### 4.2 최소 이미지 사용
```dockerfile
# 나쁜 예: 전체 이미지 (900MB+)
FROM python:3.11

# 좋은 예: slim 이미지 (150MB)
FROM python:3.11-slim

# 최적: distroless (셸 없음)
FROM gcr.io/distroless/python3
```

### 4.3 COPY 대신 ADD 피하기
```dockerfile
# 나쁜 예: ADD는 URL 다운로드, tar 자동 압축해제 기능이 있어 위험
ADD https://example.com/app.tar.gz /app/

# 좋은 예: COPY는 단순 파일 복사만 수행
COPY app.tar.gz /app/
```

### 4.4 시크릿을 이미지에 넣지 않기
```dockerfile
# 절대 금지: 비밀번호가 이미지 레이어에 영구 저장됨
ENV DB_PASSWORD=mysecret123

# 올바른 방법: 실행 시 환경변수로 전달
# docker run -e DB_PASSWORD=mysecret123 myapp
```

---

## 5. 실습: web 서버에서 Docker 다루기

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: 컨테이너 기본 조작

```bash
# web 서버 접속 후 실행 중인 컨테이너 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80
docker ps

# JuiceShop 컨테이너 확인
docker inspect juice-shop | head -50
```

### 실습 2: 보안 관점 컨테이너 점검

```bash
# 컨테이너가 root로 실행 중인지 확인
docker inspect --format='{{.Config.User}}' juice-shop

# 컨테이너의 capability 확인
docker inspect --format='{{.HostConfig.CapAdd}}' juice-shop

# 읽기 전용 파일시스템 여부 확인
docker inspect --format='{{.HostConfig.ReadonlyRootfs}}' juice-shop
```

### 실습 3: 안전한 컨테이너 실행

```bash
# 보안 옵션 적용하여 nginx 실행
docker run -d \
  --name secure-nginx \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /var/cache/nginx \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  -u 1000:1000 \
  -p 9090:80 \
  nginx:latest

# 정상 작동 확인
curl http://localhost:9090
```

---

## 6. 보안 체크리스트

Docker 컨테이너를 배포할 때 최소한 아래 항목을 점검하라:

- [ ] root 사용자로 실행하지 않는가?
- [ ] 불필요한 capability를 제거했는가?
- [ ] 읽기 전용 파일시스템을 사용하는가?
- [ ] 최소 이미지(slim/alpine/distroless)를 사용하는가?
- [ ] 이미지에 시크릿이 포함되어 있지 않은가?
- [ ] 불필요한 포트를 노출하지 않는가?

---

## 핵심 정리

1. Docker는 가볍고 빠르지만 VM보다 격리 수준이 낮다
2. 이미지, 컨테이너, 네트워크, 볼륨이 4대 핵심 요소이다
3. Dockerfile 작성 시 비root 실행, 최소 이미지, 시크릿 미포함이 필수이다
4. `--read-only`, `--cap-drop ALL` 등으로 런타임 보안을 강화한다

---

## 다음 주 예고
- Week 03: 이미지 보안 - Trivy를 활용한 취약점 스캐닝

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

## 과제 (다음 주까지)

### 과제 1: Docker 보안 점검 보고서 (50점)

web 서버와 siem 서버의 Docker 환경을 점검하고 보고서를 작성하라.

| 점검 항목 | 명령어 | 배점 |
|----------|--------|------|
| Docker 버전 | `docker version` | 5점 |
| 실행 중 컨테이너 | `docker ps` | 5점 |
| 컨테이너 root 실행 여부 | `docker inspect --format '{{.Config.User}}'` | 10점 |
| Privileged 여부 | `docker inspect --format '{{.HostConfig.Privileged}}'` | 10점 |
| 네트워크 모드 | `docker inspect --format '{{.HostConfig.NetworkMode}}'` | 10점 |
| 이미지 취약점 (있으면) | Trivy 또는 수동 분석 | 10점 |

### 과제 2: 보안 컨테이너 실행 (50점)

web 서버에서 `--read-only`, `--cap-drop ALL`, `-u 1000:1000` 옵션을 적용하여 nginx 컨테이너를 실행하고, 정상 동작을 확인하라.

---

## 검증 체크리스트

- [ ] web 서버에서 `docker ps`로 JuiceShop 컨테이너 확인 (이름: juice-shop)
- [ ] siem 서버에서 `docker ps`로 OpenCTI 6개 컨테이너 확인
- [ ] JuiceShop 컨테이너의 User, Privileged, NetworkMode 점검 완료
- [ ] Dockerfile 보안 체크리스트(나쁜 예/좋은 예) 이해
- [ ] 보안 옵션(--read-only, --cap-drop)을 적용한 컨테이너 실행 경험
---

> **실습 환경 검증 완료** (2026-03-28): Docker 29.3.0, Compose v5.1.1, juice-shop(User=65532,Privileged=false), OpenCTI 6컨테이너, opencti_default 네트워크

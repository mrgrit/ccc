# Week 08: 중간고사 - Docker 보안 강화

## 학습 목표

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

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 실기 시험 (실습 환경에서 직접 수행) |
| 시간 | 90분 |
| 배점 | 100점 |
| 환경 | web 서버 (10.20.30.80) |
| 제출 | 보안 강화 결과 + 보고서 |

---

## 시험 범위

- Week 02: Docker 기초 + 보안 (이미지, 컨테이너, Dockerfile)
- Week 03: 이미지 보안 (Trivy 스캐닝, 베이스 이미지)
- Week 04: 런타임 보안 (capability, seccomp, 컨테이너 탈출)
- Week 05: 네트워크 보안 (격리, 포트 노출)
- Week 06: Docker Compose 보안 (secrets, 리소스 제한)
- Week 07: Docker Bench, CIS Benchmark

---

## 과제: 취약한 Docker 환경 보안 강화

### 상황 설명

아래의 취약한 `docker-compose.yaml`이 프로덕션에 배포되어 있다.
보안 점검을 수행하고, 발견된 모든 문제를 수정하라.

### 취약한 Compose 파일

```yaml
# /tmp/midterm/docker-compose.yaml (취약한 버전)
version: "3.9"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - ADMIN_TOKEN=super-secret-token-12345

  api:
    image: python:3.11
    command: python app.py
    ports:
      - "5000:5000"
      - "22:22"
    privileged: true
    environment:
      - DB_PASSWORD=password123
      - API_SECRET=my-api-secret

  db:
    image: mysql:8
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=root123
    volumes:
      - /:/host-root
```

---

## 문제 1: 취약점 식별 (30점)

위 Compose 파일에서 보안 취약점을 모두 찾아 나열하라.
각 취약점에 대해 (1) 무엇이 문제인지, (2) 왜 위험한지 설명하라.

### 예상 답안 항목

| # | 취약점 | 위험도 | 설명 |
|---|--------|--------|------|
| 1 | Docker 소켓 마운트 | CRITICAL | 호스트 전체 제어 가능 |
| 2 | 환경변수 시크릿 | HIGH | inspect로 노출 |
| 3 | --privileged | CRITICAL | 모든 보안 해제 |
| 4 | SSH 포트 노출 | HIGH | 불필요한 공격 표면 |
| 5 | DB 포트 외부 노출 | HIGH | 직접 DB 접근 가능 |
| 6 | 호스트 루트 마운트 | CRITICAL | 호스트 파일시스템 전체 노출 |
| 7 | root 실행 | MEDIUM | 권한 상승 위험 |
| 8 | full 이미지 사용 | LOW | 불필요한 패키지 포함 |
| 9 | cap_drop 미설정 | MEDIUM | 불필요한 권한 보유 |
| 10 | healthcheck 없음 | LOW | 장애 감지 불가 |

---

## 문제 2: 보안 강화 (40점)

취약한 Compose 파일을 보안 모범 사례에 맞게 수정하라.

### 수정 요구사항

1. Docker 소켓 마운트 제거
2. 환경변수 시크릿을 Docker Secrets로 교체
3. --privileged 제거, cap_drop ALL + 필요 capability만 추가
4. 불필요한 포트 제거, 필요 포트는 127.0.0.1 바인딩
5. 호스트 루트 마운트 제거, 명명된 볼륨 사용
6. 네트워크 분리 (frontend/backend)
7. 리소스 제한 설정
8. healthcheck 추가
9. read_only + no-new-privileges 적용
10. slim/alpine 이미지 사용

### 제출할 파일

> **실습 목적**: Week 02~07에서 학습한 Docker 보안 기술을 종합하여 취약한 환경을 실전 수준으로 강화하기 위해 수행한다
>
> **배우는 것**: 취약한 Compose 파일에서 Docker 소켓 마운트, 환경변수 시크릿, --privileged 등 10가지 취약점을 식별하고 수정하는 능력을 기른다
>
> **결과 해석**: Trivy 스캔의 CRITICAL 수가 0이면 이미지 안전, Docker Bench의 WARN 감소가 개선 효과를 보여준다
>
> **실전 활용**: 보안 감사 대응, 프로덕션 환경 하드닝, Docker 보안 점검 보고서 작성에 직접 활용한다

```bash
# 디렉토리 구조
/tmp/midterm/
  docker-compose.yaml       # 수정된 Compose 파일
  secrets/
    db_password.txt          # DB 비밀번호
    api_secret.txt           # API 시크릿
    admin_token.txt          # 관리자 토큰
  report.md                  # 보안 점검 보고서
```

---

## 문제 3: 이미지 스캔 + 보고서 (30점)

### 3-1. Trivy 스캔 (15점)

```bash
# 사용되는 이미지의 취약점 스캔
trivy image nginx:latest --severity HIGH,CRITICAL
trivy image python:3.11 --severity HIGH,CRITICAL
trivy image mysql:8 --severity HIGH,CRITICAL

# 결과를 JSON으로 저장
trivy image -f json -o /tmp/midterm/scan-nginx.json nginx:latest
trivy image -f json -o /tmp/midterm/scan-python.json python:3.11
trivy image -f json -o /tmp/midterm/scan-mysql.json mysql:8
```

### 3-2. 보고서 작성 (15점)

보고서에 포함할 내용:

```markdown
# Docker 보안 점검 보고서

## 1. 점검 개요
- 점검 일시: YYYY-MM-DD
- 점검 대상: [서비스 목록]
- 점검 도구: Docker Bench, Trivy

## 2. 발견 사항

> **이 실습을 왜 하는가?**
> "중간고사 - Docker 보안 강화" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> Docker/클라우드/K8s 보안 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 Compose 설정 취약점
- [취약점 목록과 심각도]

### 2.2 이미지 취약점
- nginx: CRITICAL X건, HIGH X건
- python: CRITICAL X건, HIGH X건
- mysql: CRITICAL X건, HIGH X건

## 3. 개선 조치
- [각 취약점에 대한 수정 내용]

## 4. 개선 전후 비교
- Docker Bench 점수: 개선 전 → 개선 후
```

---

## 채점 기준

| 항목 | 배점 | 기준 |
|------|------|------|
| 취약점 식별 | 30 | 10개 항목 x 3점 |
| Compose 수정 | 40 | 10개 요구사항 x 4점 |
| Trivy 스캔 | 15 | 3개 이미지 스캔 + 결과 분석 |
| 보고서 | 15 | 형식, 분석 깊이, 개선 전후 비교 |

---

## 참고: 모범 답안 구조 (Compose)

```yaml
version: "3.9"
services:
  web:
    image: nginx:1.25-alpine
    read_only: true
    tmpfs: [/tmp, /var/cache/nginx, /var/run]
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt: ["no-new-privileges:true"]
    ports: ["127.0.0.1:80:80"]
    networks: [frontend]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: 128M }
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3

  api:
    image: python:3.11-slim
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    networks: [frontend, backend]
    secrets: [db_password, api_secret, admin_token]
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 512M }

  db:
    image: mysql:8-oracle
    cap_drop: [ALL]
    cap_add: [CHOWN, SETUID, SETGID, DAC_OVERRIDE]
    security_opt: ["no-new-privileges:true"]
    networks: [backend]
    volumes: [db-data:/var/lib/mysql]
    secrets: [db_password]
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 1G }
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
  backend:
    internal: true

volumes:
  db-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_secret:
    file: ./secrets/api_secret.txt
  admin_token:
    file: ./secrets/admin_token.txt
```

---

## 시험 후 안내

- 다음 주부터 클라우드 보안(AWS/Azure 개념)으로 진입한다
- Docker 보안은 클라우드 보안의 기반이 된다
- 중간고사 피드백은 Week 09에 제공한다

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

> **실습 환경 검증 완료** (2026-03-28): Docker 29.3.0, Compose v5.1.1, juice-shop(User=65532,Privileged=false), OpenCTI 6컨테이너, opencti_default 네트워크

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Docker Engine
> **역할:** 컨테이너 런타임·이미지 관리  
> **실행 위치:** `모든 VM(공통)`  
> **접속/호출:** `docker` CLI, `systemctl status docker`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/var/lib/docker/` | 이미지·컨테이너 저장소(overlay2) |
| `/etc/docker/daemon.json` | 데몬 설정 (log-driver, userns-remap 등) |
| `/var/run/docker.sock` | Docker API 소켓 — 루트권한 등가 |

**핵심 설정·키**

- `{"userns-remap": "default"}` — 컨테이너 root↔호스트 비루트 매핑
- `{"icc": false}` — 기본 네트워크 내 컨테이너 간 통신 차단
- `{"no-new-privileges": true}` — setuid 권한 상승 차단

**로그·확인 명령**

- `journalctl -u docker` — 데몬 로그
- ``docker logs <c>`` — 컨테이너 stdout/stderr

**UI / CLI 요점**

- `docker inspect <c> | jq '.[0].HostConfig.Privileged'` — `--privileged` 여부
- `docker exec -it <c> sh` — 컨테이너 내부 진입
- `docker system df` — 이미지/볼륨 디스크 사용량

> **해석 팁.** `/var/run/docker.sock`을 컨테이너에 마운트하는 순간 **호스트 루트와 동등**이다. 점검 1순위.

### Docker Bench for Security
> **역할:** CIS Docker Benchmark 자동 점검 스크립트  
> **실행 위치:** `Docker 호스트`  
> **접속/호출:** `docker run --rm --net host --pid host --userns host --cap-add audit_control ... docker/docker-bench-security`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `docker-bench-security.log` | 점검 결과 텍스트 |
| `docker-bench-security.sh` | 실행 스크립트 |

**핵심 설정·키**

- `--no-colors` — CI 친화 출력
- `-c check_4` — 특정 섹션만 실행

**로그·확인 명령**

- `결과 [PASS]/[WARN]/[INFO]` — 항목별 상태

**UI / CLI 요점**

- `docker-bench` 섹션 2.14 — live restore 활성 여부
- 섹션 4 — 컨테이너 이미지/빌드 보안

> **해석 팁.** `[INFO]`는 자동 판단 불가 — 수동 확인 필수. 매 릴리즈 CIS 버전과 Docker 버전 매핑을 맞추자.

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

---

## 실제 사례 (WitFoo Precinct 6 — 중간고사 채점 reference)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *중간고사: Docker 보안 강화 통합* 학습 항목 매칭.

### 중간고사가 평가하는 것 — "Docker 보안 사고를 정량으로 분석할 수 있는가"

중간고사는 학생이 w01-w07 의 단편 기술을 *통합해서 하나의 침해 시나리오를 분석할 수 있는가* 를 평가한다. 이는 단순히 "공격자가 image 를 pull 했다" 같은 서술이 아니라, **"공격자가 leaked IAM key 로 ECR 에 진입한 후 — Describe\* API 174K 의 정상 baseline 에서 분리되는 burst 패턴을 만들고, image manifest 에서 박힌 secret 을 추출한 후 (Auth Hijack edge), privileged 컨테이너를 띄워 4690 event 79K 의 baseline 을 1시간 만에 초과하는 burst 를 만들었으며, 이 과정에서 host file system 접근으로 4662 event 226K baseline 의 anomaly 를 발생시켰다"** 같은 정량 evidence chain 을 답안에 작성할 수 있어야 한다.

이 차이가 중간고사의 핵심이다 — **서술만 한 답안은 부분점, dataset 정량 evidence 를 인용한 답안은 만점**. 학생은 일주일 동안 dataset 의 5가지 핵심 신호량을 외워야 시험에 통과한다.

```mermaid
graph LR
    R["1. Recon"] -->|Describe* burst| RCN["174,293 호출 baseline<br/>비정상 burst 추출"]
    RCN -->|registry token<br/>secret 추출| AH["2. mo_name=Auth Hijack<br/>(image 결함 폭로)"]
    AH -->|container run| RUN["3. privileged container"]
    RUN -->|capability 남용| E4690["4. event 4690<br/>79K baseline 초과"]
    RUN -->|host 자원 access| E4662["5. event 4662<br/>226K baseline 초과"]
    E4690 -->|lateral 이동| LAT["6. Auth Hijack edge<br/>(추가 자원 침해)"]
    E4662 -->|data exfil| DT["7. mo_name=Data Theft<br/>(최종 사고)"]

    style R fill:#ffe6cc
    style DT fill:#ff9999
```

**그림 해석**: 7단계 evidence chain — *Recon → Auth Hijack → Privileged Run → Capability Abuse → Host Access → Lateral → Data Theft*. 만점 답안은 7단계 모두에 정량 evidence 를 인용해야 한다. 답안에서 단계 1-2개만 다루면 *공격자의 일부분만 본* 부분점.

### Case 1: 만점 답안의 5축 evidence 요구 사항

| 평가 축 | dataset 신호 | 만점 기준 |
|---|---|---|
| ① Recon 식별 | Describe* 174,293건 baseline | 단일 IAM 의 시간 burst 패턴 추출 |
| ② Image 결함 | DescribeImage manifest 호출 | secret 추출 가능 layer 식별 |
| ③ Runtime 위반 | 4690 + 4662 비율 | privileged/cap 매핑 정량화 |
| ④ Network 차단 | 5156 (176K) + firewall_action (118K) | ICC default + block:allow 비율 |
| ⑤ Audit 추적 | security_audit_event 381K | 시간순 정렬 + actor 묶기 |

**자세한 해석**:

만점 답안의 핵심은 — *각 축마다 "정상 baseline" 과 "비정상 burst" 를 구분* 하는 능력이다. 예를 들어 ① Recon 축에서 학생이 "공격자가 정찰을 했다" 라고만 적으면 부분점. "정상 운영의 Describe\* 호출 174,293건 중 caller 분포는 5-10개 IAM 으로 수렴하는데, 이번 incident 에서는 신규 11번째 caller 가 시간당 300건 burst 를 만들었으며 dst_resource 가 ECR repository 로 집중되었다" 라고 적으면 만점.

이런 답안을 쓰려면 학생이 시험 전 *baseline 숫자 5개* (174K, 226K, 176K, 79K, 39K) 를 외워야 한다. 외우지 않은 학생은 답안에 정량 evidence 를 적을 수 없고, 자연스럽게 부분점에 머문다.

### Case 2: 5개 신호의 통합 활용 — timeline 작성 능력 평가

| 신호 | dataset 양 | 시험 활용 |
|---|---|---|
| security_audit_event | 381,552건 | timeline 의 X축 (시간순 정렬) |
| event 4662 | 226,215건 | host 자원 노출 단계 표시 |
| event 5156 | 176,060건 | egress 통신 단계 표시 |
| event 4658 | 158,374건 | handle 회수 (정상 종료) 검증 |
| firewall_action | 118,151건 | 차단 정책 적용 여부 |

**자세한 해석**:

중간고사 답안의 두 번째 평가 축은 — *공격 timeline 을 그릴 수 있는가* 다. 5개 신호를 시간순으로 배열하면 *T+0 (Recon) → T+5min (Image 결함 발견) → T+10min (Privileged Run) → T+15min (Capability 남용) → T+30min (Lateral) → T+1h (Exfil)* 같은 timeline 이 만들어진다.

만점 답안은 5개 축 모두에 evidence 가 있어야 한다. 1-2개 축만 인용 = 부분점. 학생이 자주 빠뜨리는 축은 ④ Network (5156) 와 ⑤ Audit (security_audit_event) 인데, 이 두 축은 *공격이 정상 정책을 어떻게 우회/위반했는지* 를 보여주므로 차단 설계 의 핵심이다.

### 이 사례에서 학생이 배워야 할 3가지

1. **시험 전에 5가지 baseline 숫자를 외워라** — 174K (Describe), 226K (4662), 176K (5156), 79K (4690), 39K (GetLogEvents).
2. **정성 서술이 아닌 정량 evidence 로 답하라** — "공격했다" 가 아니라 "baseline 174K 대비 시간당 300건 burst" 로.
3. **5축 timeline 을 그릴 수 있어야 통과** — Recon / Image / Runtime / Network / Audit 5축 모두 다룬 답안 = 만점.

**학생 액션**: 자신이 본 lecture 시리즈에서 분석한 Docker 침해 사례 1건을 골라, 위 5축 표를 채워본다. 각 축마다 *baseline 숫자 + 사례에서 관찰된 비정상 수치 + 둘의 차이의 보안 의미* 를 한 줄씩 작성하면 시험 답안의 모범이 된다.


---

## 부록: 학습 OSS 도구 매트릭스 (Course6 Cloud-Container — Week 08 스토리지 보안)

### 컨테이너 스토리지 보안 도구

| 영역 | OSS 도구 |
|------|---------|
| Persistent Volume | **Rook** (Ceph) / Longhorn / OpenEBS / Portworx OSS |
| Secret 관리 | **Sealed Secrets** / External Secrets Operator (ESO) / Vault Agent / SOPS |
| 암호화 | **dm-crypt LUKS** (volume) / **age** (file) / sops (yaml) / **Vault transit** |
| Backup | **Velero** + restic / Stash / Kanister |
| 권한 | RBAC + OPA / Kyverno / `securityContext` |
| etcd 암호화 | k8s `EncryptionConfiguration` / KMS provider |

### 핵심 — Sealed Secrets (Git-safe)

```bash
# Controller 설치
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# CLI 설치
curl -L https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz | sudo tar xz -C /usr/local/bin

# Secret 생성 + sealing
echo -n "supersecret" | kubectl create secret generic mysec \
  --dry-run=client --from-file=password=/dev/stdin -o yaml > secret.yaml

kubeseal -o yaml < secret.yaml > sealed-secret.yaml
# sealed-secret.yaml 은 git 에 안전하게 commit 가능
kubectl apply -f sealed-secret.yaml

# Controller 가 Secret 자동 생성
kubectl get secret mysec -o yaml
```

### 학생 환경 준비

```bash
# Velero (백업)
curl -L https://github.com/vmware-tanzu/velero/releases/latest/download/velero-v1.13.0-linux-amd64.tar.gz | sudo tar xz -C /tmp
sudo mv /tmp/velero-v1.13.0-linux-amd64/velero /usr/local/bin/

# External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace

# SOPS (Mozilla — 파일 단위 암호화)
sudo curl -L https://github.com/getsops/sops/releases/latest/download/sops-v3.8.0.linux.amd64 -o /usr/local/bin/sops
sudo chmod +x /usr/local/bin/sops

# age (modern crypto, GPG 대안)
curl -L https://github.com/FiloSottile/age/releases/latest/download/age-v1.1.1-linux-amd64.tar.gz | tar xz
sudo mv age/age age/age-keygen /usr/local/bin/

# Vault (HashiCorp OSS)
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt install -y vault

# Longhorn (k8s native PV)
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.0/deploy/longhorn.yaml
```

### 핵심 사용법

```bash
# 1) Velero — k8s 백업
velero install --provider aws --bucket k8s-backup \
  --secret-file ./credentials --backup-location-config region=us-east-1

velero backup create demo-backup --include-namespaces production
velero backup get
velero restore create --from-backup demo-backup

# 2) External Secrets Operator (Vault → k8s Secret 자동)
cat > eso.yaml << 'EOF'
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "http://vault:8200"
      auth:
        kubernetes:
          mountPath: kubernetes
          role: myapp
EOF
kubectl apply -f eso.yaml

# Secret 동기화
cat > es.yaml << 'EOF'
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: db-credentials                                            # k8s Secret 자동 생성
  data:
    - secretKey: password
      remoteRef:
        key: secret/data/db
        property: password
EOF
kubectl apply -f es.yaml

# 3) SOPS — 파일 단위 암호화 (yaml/json/env)
sops --age age1xyz... -e secrets.yaml > secrets.enc.yaml
git add secrets.enc.yaml                                            # 안전하게 commit
sops -d secrets.enc.yaml                                            # 복호화

# 4) age — 단순 암호화
age-keygen -o key.txt
age -r $(cat key.txt | grep public | cut -d' ' -f4) secret.txt > secret.txt.age
age -d -i key.txt secret.txt.age > secret.txt

# 5) Vault — secret + transit 암호화
vault server -dev -dev-root-token-id=root
export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root
vault kv put secret/db password=Pa$$w0rd

# 동적 secret (DB 사용자 자동 생성)
vault secrets enable database
vault write database/config/postgresql \
  plugin_name=postgresql-database-plugin \
  allowed_roles="readonly" \
  connection_url="postgresql://{{username}}:{{password}}@postgres:5432/mydb"

# 6) etcd 암호화 (k8s)
cat > /etc/kubernetes/encryption.yaml << 'EOF'
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: ["secrets"]
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: $(head -c 32 /dev/urandom | base64)
      - identity: {}
EOF
# kube-apiserver --encryption-provider-config=/etc/kubernetes/encryption.yaml
```

### 스토리지 보안 흐름

```bash
# Phase 1: PV 생성 + 암호화 (LUKS)
sudo cryptsetup luksFormat /dev/sdb
sudo cryptsetup luksOpen /dev/sdb encrypted-pv
sudo mkfs.ext4 /dev/mapper/encrypted-pv

# Phase 2: Secret 관리
# Git → SOPS / Sealed Secrets / ESO + Vault
# 절대 평문 secret commit 금지

# Phase 3: 백업 (Velero + restic)
velero backup create daily-$(date +%Y%m%d) --ttl 720h

# Phase 4: 복원 모의
velero restore create --from-backup daily-2024-04-01

# Phase 5: etcd 정기 백업 + 암호화
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d).db
```

학생은 본 8주차에서 **Sealed Secrets + ESO + Vault + SOPS + Velero** 5 도구로 컨테이너 스토리지의 3 영역 (secret 관리 / 데이터 암호화 / 백업) 통합 흐름을 OSS 만으로 운영한다.

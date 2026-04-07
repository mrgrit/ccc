# Docker 보안 레퍼런스

## 개요

Docker 컨테이너는 커널을 공유하므로 VM보다 격리 수준이 낮다. 이미지 빌드부터 런타임까지 보안 모범 사례를 적용하여 공격 표면을 최소화해야 한다.

---

## 1. 이미지 보안

### 최소 베이스 이미지 사용

```dockerfile
# 나쁜 예: 풀 OS 이미지
FROM ubuntu:22.04

# 좋은 예: 최소 이미지
FROM alpine:3.19

# 가장 작은 이미지 (정적 바이너리용)
FROM scratch

# Distroless (Google — 셸 없는 이미지)
FROM gcr.io/distroless/static-debian12
```

### 멀티스테이지 빌드

```dockerfile
# 빌드 스테이지 — 빌드 도구 포함
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o server .

# 실행 스테이지 — 최소 이미지
FROM alpine:3.19
RUN adduser -D -u 1001 appuser
COPY --from=builder /app/server /usr/local/bin/server
USER appuser
ENTRYPOINT ["server"]
```

### 이미지 스캔

```bash
# Docker Scout (내장)
docker scout cves myimage:latest
docker scout recommendations myimage:latest

# Trivy (오픈소스)
trivy image myimage:latest
trivy image --severity HIGH,CRITICAL myimage:latest

# Grype
grype myimage:latest
```

### Dockerfile 보안 체크리스트

```dockerfile
# 1. 특정 태그 사용 (latest 금지)
FROM alpine:3.19

# 2. 이미지 해시 고정 (공급망 보안)
FROM alpine@sha256:abc123def456...

# 3. 루트가 아닌 사용자로 실행
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# 4. 불필요한 패키지 설치 금지
RUN apk add --no-cache curl

# 5. COPY vs ADD — COPY 선호 (ADD는 URL/tar 지원으로 위험)
COPY requirements.txt .

# 6. 비밀 정보는 이미지에 포함하지 않음
# 나쁜 예: COPY .env /app/.env
# 좋은 예: 런타임 환경변수 또는 시크릿 마운트
RUN --mount=type=secret,id=db_password cat /run/secrets/db_password

# 7. .dockerignore 사용
# .dockerignore:
# .git
# .env
# *.key
# node_modules

# 8. HEALTHCHECK 설정
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

---

## 2. 컨테이너 격리

### Linux Capabilities

기본적으로 Docker는 일부 capability를 부여한다. 최소 권한 원칙을 적용한다.

```bash
# 모든 capability 제거 후 필요한 것만 추가
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myimage

# 위험한 capability
# --cap-add=SYS_ADMIN   ← 컨테이너 탈출 가능!
# --cap-add=NET_RAW     ← ARP 스푸핑 가능
# --cap-add=SYS_PTRACE  ← 프로세스 디버깅 가능
```

주요 capability 목록:

| Capability         | 설명                      | 권장   |
|--------------------|---------------------------|--------|
| `NET_BIND_SERVICE` | 1024 이하 포트 바인드     | 필요시 |
| `CHOWN`            | 파일 소유자 변경          | 제거   |
| `DAC_OVERRIDE`     | 파일 접근 권한 무시       | 제거   |
| `SETUID`/`SETGID`  | UID/GID 변경              | 제거   |
| `SYS_ADMIN`        | 시스템 관리 (매우 위험)   | 절대 금지 |
| `NET_RAW`          | RAW 소켓                  | 제거   |
| `SYS_PTRACE`       | 프로세스 트레이스          | 제거   |

### Seccomp 프로필

```bash
# 기본 seccomp 프로필 사용 (Docker 기본값)
docker run --security-opt seccomp=default myimage

# 커스텀 seccomp 프로필
docker run --security-opt seccomp=custom-seccomp.json myimage

# seccomp 비활성화 (위험! 테스트용만)
docker run --security-opt seccomp=unconfined myimage
```

커스텀 seccomp 프로필 예시:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat",
                "fstat", "mmap", "mprotect", "munmap",
                "brk", "exit_group", "execve"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### AppArmor

```bash
# 기본 AppArmor 프로필 사용
docker run --security-opt apparmor=docker-default myimage

# 커스텀 프로필
docker run --security-opt apparmor=my-custom-profile myimage

# AppArmor 상태 확인
aa-status
```

---

## 3. 네트워크 보안

### 내부 네트워크 (external 접근 차단)

```yaml
# docker-compose.yml
services:
  web:
    image: nginx:alpine
    networks:
      - frontend
      - backend

  db:
    image: postgres:16-alpine
    networks:
      - backend     # 외부 접근 불가

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true   # 외부 인터넷 접근 차단
```

### 네트워크 격리

```bash
# 사용자 정의 네트워크 생성
docker network create --driver bridge \
  --subnet 10.20.30.0/24 \
  --internal \
  secure_net

# 컨테이너 간 통신 비활성화
docker network create --driver bridge \
  -o "com.docker.network.bridge.enable_icc=false" \
  isolated_net
```

### 포트 바인딩 제한

```yaml
services:
  web:
    ports:
      # 나쁜 예: 모든 인터페이스에 바인딩
      - "80:80"

      # 좋은 예: localhost만
      - "127.0.0.1:80:80"

      # 좋은 예: 특정 인터페이스
      - "10.20.30.1:80:80"
```

---

## 4. 런타임 보안

### 읽기 전용 파일시스템

```bash
# 읽기 전용 루트 파일시스템
docker run --read-only myimage

# 임시 쓰기 영역 허용
docker run --read-only --tmpfs /tmp --tmpfs /run myimage
```

```yaml
# docker-compose.yml
services:
  app:
    image: myimage
    read_only: true
    tmpfs:
      - /tmp
      - /run
```

### 권한 상승 방지

```bash
# 새로운 권한 획득 금지
docker run --security-opt=no-new-privileges:true myimage

# 특권 모드 금지 (절대 사용하지 말 것!)
# docker run --privileged myimage  ← 절대 금지!
```

### 리소스 제한

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
          pids: 100
        reservations:
          cpus: '0.5'
          memory: 256M
```

```bash
# CLI
docker run --cpus=1 --memory=512m --pids-limit=100 myimage

# ulimit 설정
docker run --ulimit nofile=1024:2048 --ulimit nproc=512 myimage
```

### PID namespace 격리

```bash
# 호스트 PID namespace 공유 금지 (기본값이 격리)
docker run --pid=container:app1 myimage   # 다른 컨테이너와만 공유
```

---

## 5. 시크릿 관리

### Docker Secrets (Swarm 모드)

```bash
# 시크릿 생성
echo "my_db_password" | docker secret create db_password -

# 서비스에서 시크릿 사용
docker service create --secret db_password myimage
# 컨테이너 내 /run/secrets/db_password 로 접근
```

### Compose에서 시크릿

```yaml
services:
  app:
    image: myimage
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### 빌드 시 시크릿 (BuildKit)

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
RUN --mount=type=secret,id=api_key \
  cat /run/secrets/api_key > /dev/null && \
  echo "Secret used during build only"
```

```bash
docker build --secret id=api_key,src=./api_key.txt .
```

---

## 6. Docker Daemon 보안

### daemon.json

```json
{
  "icc": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "no-new-privileges": true,
  "userns-remap": "default",
  "live-restore": true,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 1024,
      "Soft": 512
    }
  }
}
```

### 주요 설정 설명

| 설정                | 설명                              |
|---------------------|-----------------------------------|
| `icc: false`        | 컨테이너 간 기본 통신 차단        |
| `no-new-privileges` | 전역 권한 상승 방지               |
| `userns-remap`      | 사용자 네임스페이스 리매핑        |
| `live-restore`      | 데몬 재시작 시 컨테이너 유지      |

### Docker Socket 보안

```bash
# Docker 소켓 마운트는 매우 위험 (호스트 완전 제어 가능)
# 나쁜 예:
# docker run -v /var/run/docker.sock:/var/run/docker.sock myimage

# 필요한 경우 읽기 전용 프록시 사용
# docker-socket-proxy 또는 Tecnativa/docker-socket-proxy
```

---

## 7. CIS Docker Benchmark 핵심 항목

CIS Docker Benchmark는 Docker 보안 모범 사례를 정리한 표준이다.

### 호스트 설정 (CIS 1.x)

```bash
# Docker 전용 파티션 사용
# /var/lib/docker 별도 파티션

# Docker 버전 최신 유지
docker version

# 감사 로그 설정
# /etc/audit/audit.rules
-w /usr/bin/docker -p rwxa -k docker
-w /var/lib/docker -p rwxa -k docker
-w /etc/docker -p rwxa -k docker
-w /lib/systemd/system/docker.service -p rwxa -k docker
-w /lib/systemd/system/docker.socket -p rwxa -k docker
-w /var/run/docker.sock -p rwxa -k docker
```

### 데몬 설정 (CIS 2.x)

```bash
# TLS 인증 설정 (원격 접근 시)
dockerd --tlsverify \
  --tlscacert=ca.pem \
  --tlscert=server-cert.pem \
  --tlskey=server-key.pem \
  -H=0.0.0.0:2376
```

### 컨테이너 런타임 (CIS 5.x)

```bash
# 권장 실행 방법
docker run \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  --security-opt apparmor=docker-default \
  --read-only \
  --tmpfs /tmp \
  --user 1001:1001 \
  --cpus=1 --memory=512m --pids-limit=100 \
  --restart=on-failure:3 \
  --health-cmd="curl -f http://localhost/ || exit 1" \
  --health-interval=30s \
  myimage:1.0
```

### 보안 점검 도구

```bash
# Docker Bench Security (자동 점검)
docker run --rm --net host --pid host --userns host \
  -v /var/lib:/var/lib \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/lib/systemd:/usr/lib/systemd \
  -v /etc:/etc \
  docker/docker-bench-security

# Hadolint (Dockerfile 린터)
hadolint Dockerfile

# Dockle (이미지 보안 린터)
dockle myimage:latest
```

---

## 8. docker-compose 보안 설정 예제

```yaml
version: "3.9"

services:
  web:
    image: nginx:1.25-alpine
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache/nginx
      - /var/run
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    user: "101:101"
    ports:
      - "127.0.0.1:443:443"
    networks:
      - frontend
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  app:
    image: myapp:1.0
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    user: "1001:1001"
    networks:
      - frontend
      - backend
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
          pids: 100

  db:
    image: postgres:16-alpine
    read_only: true
    tmpfs:
      - /tmp
      - /run/postgresql
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    user: "999:999"
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - backend
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  db_data:
    driver: local

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## 참고

- CIS Docker Benchmark: https://www.cisecurity.org/benchmark/docker
- Docker 보안 문서: https://docs.docker.com/engine/security/
- OWASP Docker Security: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html

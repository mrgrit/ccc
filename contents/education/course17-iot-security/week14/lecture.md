# Week 14: IoT 보안 가이드라인

## 학습 목표
- IoT 보안 설계 원칙(Security by Design)을 이해한다
- IoT 디바이스의 안전한 인증 및 암호화 구현을 학습한다
- 안전한 펌웨어 업데이트 메커니즘을 설계한다
- IoT 보안 표준 및 규제를 파악한다
- IoT 보안 아키텍처를 종합 설계한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | IoT 서비스 호스트 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | IoT 보안 설계 원칙 (Part 1) | 강의 |
| 0:40-1:10 | 인증 및 암호화 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 보안 펌웨어 업데이트 (Part 3) | 실습 |
| 2:00-2:40 | IoT 보안 표준/규제 (Part 4) | 강의/실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 종합 보안 아키텍처 설계 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

---

## Part 1: IoT 보안 설계 원칙 (40분)

### 1.1 Security by Design

IoT 보안은 개발 초기부터 설계에 포함되어야 한다.

**IoT 보안 개발 라이프사이클:**
```
요구사항 분석 → 위협 모델링 → 보안 설계 → 보안 구현 → 보안 테스트 → 배포/운영
      ↑                                                              │
      └──────────── 취약점 피드백 ←── 모니터링 ←────────────────────┘
```

### 1.2 IoT 보안 설계 10대 원칙

| # | 원칙 | 설명 |
|---|------|------|
| 1 | 최소 권한 | 필요한 최소 권한만 부여 |
| 2 | 심층 방어 | 다중 보안 계층 적용 |
| 3 | 기본 보안 | 기본 설정이 안전해야 함 |
| 4 | 인증 강화 | 강력한 인증 필수 |
| 5 | 암호화 적용 | 전송/저장 시 암호화 |
| 6 | 안전한 업데이트 | 서명된 OTA 업데이트 |
| 7 | 로깅/모니터링 | 보안 이벤트 기록 |
| 8 | 물리적 보안 | 하드웨어 탬퍼 방지 |
| 9 | 개인정보 보호 | 데이터 최소 수집 |
| 10 | 보안 폐기 | 수명 종료 시 데이터 삭제 |

### 1.3 위협 모델링 (STRIDE)

```
┌─────────────────────────────────────┐
│          STRIDE for IoT             │
├──────────┬──────────────────────────┤
│ Spoofing │ 디바이스/사용자 위장     │
│ Tampering│ 데이터/펌웨어 변조       │
│ Repudiation│ 행위 부인              │
│ Info Disc│ 데이터 유출              │
│ DoS      │ 서비스 거부              │
│ EoP      │ 권한 상승               │
└──────────┴──────────────────────────┘
```

**IoT 위협 모델링 절차:**
1. 시스템 구성도 작성 (DFD)
2. 자산 식별 (데이터, 기능, 인프라)
3. 위협 식별 (STRIDE 적용)
4. 위험 평가 (DREAD 점수)
5. 대응 방안 수립

---

## Part 2: 인증 및 암호화 (30분)

### 2.1 IoT 인증 방법

| 방법 | 보안 수준 | 적합 디바이스 |
|------|-----------|---------------|
| 사용자/비밀번호 | 낮음 | 웹 인터페이스 |
| API 키 | 중간 | 클라우드 연동 |
| X.509 인증서 | 높음 | 디바이스 인증 |
| PSK (사전 공유 키) | 중간 | 제한된 디바이스 |
| OAuth 2.0 | 높음 | API/클라우드 |
| mTLS | 매우 높음 | 디바이스 ↔ 서버 |

### 2.2 안전한 인증 구현

```bash
# X.509 인증서 기반 디바이스 인증
cat << 'PYEOF' > /tmp/iot_auth_demo.py
#!/usr/bin/env python3
"""IoT 디바이스 인증서 기반 인증 데모"""
import subprocess
import os
import json
import hashlib
import hmac
import time

CERT_DIR = "/tmp/iot_certs"
os.makedirs(CERT_DIR, exist_ok=True)

print("=== IoT 디바이스 인증서 기반 인증 ===\n")

# 1. CA 생성
print("[1] CA (인증 기관) 생성")
subprocess.run([
    'openssl', 'req', '-new', '-x509', '-days', '3650',
    '-keyout', f'{CERT_DIR}/ca.key', '-out', f'{CERT_DIR}/ca.crt',
    '-subj', '/CN=IoT-CA/O=SecureCorp', '-nodes'
], capture_output=True)
print(f"    CA 인증서: {CERT_DIR}/ca.crt")

# 2. 디바이스 인증서 생성
print("[2] 디바이스 인증서 생성")
for device in ['sensor-01', 'camera-01', 'gateway-01']:
    subprocess.run([
        'openssl', 'genrsa', '-out', f'{CERT_DIR}/{device}.key', '2048'
    ], capture_output=True)
    subprocess.run([
        'openssl', 'req', '-new',
        '-key', f'{CERT_DIR}/{device}.key',
        '-out', f'{CERT_DIR}/{device}.csr',
        '-subj', f'/CN={device}/O=IoTFactory'
    ], capture_output=True)
    subprocess.run([
        'openssl', 'x509', '-req',
        '-in', f'{CERT_DIR}/{device}.csr',
        '-CA', f'{CERT_DIR}/ca.crt',
        '-CAkey', f'{CERT_DIR}/ca.key',
        '-CAcreateserial',
        '-out', f'{CERT_DIR}/{device}.crt',
        '-days', '365'
    ], capture_output=True)
    print(f"    {device}: {CERT_DIR}/{device}.crt")

# 3. 인증서 검증
print("\n[3] 인증서 검증")
for device in ['sensor-01', 'camera-01', 'gateway-01']:
    result = subprocess.run([
        'openssl', 'verify',
        '-CAfile', f'{CERT_DIR}/ca.crt',
        f'{CERT_DIR}/{device}.crt'
    ], capture_output=True, text=True)
    status = "VALID" if "OK" in result.stdout else "INVALID"
    print(f"    {device}: {status}")

# 4. 토큰 기반 인증 (JWT 유사)
print("\n[4] 토큰 기반 인증 데모")
secret = b'super-secret-key-2024'
for device in ['sensor-01', 'camera-01']:
    payload = json.dumps({
        "device_id": device,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }).encode()
    token = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    print(f"    {device} Token: {token[:32]}...")

print("\n[5] 보안 권장 사항")
print("    - 디바이스별 고유 인증서 사용")
print("    - 인증서 갱신 자동화 (ACME 프로토콜)")
print("    - HSM/TPM에 개인키 저장")
print("    - 인증서 폐기 목록(CRL) 관리")
PYEOF

python3 /tmp/iot_auth_demo.py
```

### 2.3 IoT 암호화 선택 가이드

| 디바이스 능력 | 추천 암호화 | TLS |
|--------------|------------|-----|
| 고성능 (RPi급) | AES-256-GCM, RSA-2048 | TLS 1.3 |
| 중성능 (ESP32급) | AES-128-CCM, ECC-256 | TLS 1.2 |
| 저성능 (8비트 MCU) | ChaCha20-Poly1305, Ed25519 | DTLS 1.2 |
| 초저성능 | AES-128-CCM, PSK | CoAP+DTLS-PSK |

---

## Part 3: 보안 펌웨어 업데이트 (40분)

### 3.1 안전한 OTA 업데이트 아키텍처

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ 개발팀   │──→  │ 빌드서버 │──→  │ 배포서버 │
│ (코드)   │     │ (서명)   │     │ (CDN)    │
└──────────┘     └──────────┘     └────┬─────┘
                                       │ HTTPS
                                  ┌────┴─────┐
                                  │ 디바이스  │
                                  │ 1. 버전 확인
                                  │ 2. 다운로드
                                  │ 3. 서명 검증
                                  │ 4. 무결성 확인
                                  │ 5. 업데이트 적용
                                  │ 6. 롤백 준비
                                  └──────────┘
```

### 3.2 펌웨어 서명 및 검증

```bash
cat << 'PYEOF' > /tmp/firmware_signing.py
#!/usr/bin/env python3
"""펌웨어 서명 및 검증 데모"""
import subprocess
import hashlib
import json
import os

WORK = "/tmp/fw_signing"
os.makedirs(WORK, exist_ok=True)

print("=== 보안 펌웨어 업데이트 데모 ===\n")

# 1. 서명 키 쌍 생성
print("[1] 서명 키 쌍 생성 (Ed25519)")
subprocess.run(['openssl', 'genpkey', '-algorithm', 'Ed25519',
    '-out', f'{WORK}/signing.key'], capture_output=True)
subprocess.run(['openssl', 'pkey', '-in', f'{WORK}/signing.key',
    '-pubout', '-out', f'{WORK}/signing.pub'], capture_output=True)
print(f"    개인키: {WORK}/signing.key")
print(f"    공개키: {WORK}/signing.pub (디바이스에 내장)")

# 2. 펌웨어 생성
print("\n[2] 펌웨어 이미지 생성")
firmware_data = b"FIRMWARE_V2.1.0_" + os.urandom(1024)
with open(f'{WORK}/firmware_v2.1.0.bin', 'wb') as f:
    f.write(firmware_data)

fw_hash = hashlib.sha256(firmware_data).hexdigest()
print(f"    크기: {len(firmware_data)} bytes")
print(f"    SHA256: {fw_hash}")

# 3. 펌웨어 서명
print("\n[3] 펌웨어 서명")
subprocess.run([
    'openssl', 'dgst', '-sha256', '-sign', f'{WORK}/signing.key',
    '-out', f'{WORK}/firmware_v2.1.0.sig',
    f'{WORK}/firmware_v2.1.0.bin'
], capture_output=True)
print(f"    서명 파일: {WORK}/firmware_v2.1.0.sig")

# 4. 매니페스트 생성
manifest = {
    "version": "2.1.0",
    "filename": "firmware_v2.1.0.bin",
    "size": len(firmware_data),
    "sha256": fw_hash,
    "signature": "firmware_v2.1.0.sig",
    "min_version": "2.0.0",
    "rollback_version": "2.0.5",
    "release_date": "2024-12-01",
}
with open(f'{WORK}/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
print(f"\n[4] 매니페스트 생성")
print(f"    {json.dumps(manifest, indent=2)}")

# 5. 디바이스 측 검증
print("\n[5] 디바이스 측 검증 시뮬레이션")
result = subprocess.run([
    'openssl', 'dgst', '-sha256', '-verify', f'{WORK}/signing.pub',
    '-signature', f'{WORK}/firmware_v2.1.0.sig',
    f'{WORK}/firmware_v2.1.0.bin'
], capture_output=True, text=True)
if "Verified OK" in result.stdout:
    print("    [+] 서명 검증: 성공")
else:
    print("    [-] 서명 검증: 실패!")

# 해시 확인
with open(f'{WORK}/firmware_v2.1.0.bin', 'rb') as f:
    verify_hash = hashlib.sha256(f.read()).hexdigest()
if verify_hash == fw_hash:
    print("    [+] 무결성 검증: 성공")
else:
    print("    [-] 무결성 검증: 실패!")

# 6. 변조 시뮬레이션
print("\n[6] 변조된 펌웨어 검증")
tampered = firmware_data[:100] + b'\xFF' * 10 + firmware_data[110:]
with open(f'{WORK}/firmware_tampered.bin', 'wb') as f:
    f.write(tampered)

result = subprocess.run([
    'openssl', 'dgst', '-sha256', '-verify', f'{WORK}/signing.pub',
    '-signature', f'{WORK}/firmware_v2.1.0.sig',
    f'{WORK}/firmware_tampered.bin'
], capture_output=True, text=True)
status = "성공" if "Verified OK" in result.stdout else "실패 (변조 탐지!)"
print(f"    [-] 변조된 펌웨어 서명 검증: {status}")
PYEOF

python3 /tmp/firmware_signing.py
```

---

## Part 4: IoT 보안 표준/규제 (40분)

### 4.1 IoT 보안 표준

| 표준 | 기관 | 내용 |
|------|------|------|
| NIST SP 800-183 | NIST | IoT 네트워크 보안 |
| NISTIR 8259 | NIST | IoT 기기 사이버보안 역량 |
| ETSI EN 303 645 | ETSI | 소비자 IoT 보안 요구사항 |
| IEC 62443 | IEC | 산업 자동화 보안 |
| ISO 27400 | ISO | IoT 보안/프라이버시 가이드 |
| OWASP IoT | OWASP | IoT Top 10, 점검 가이드 |

### 4.2 ETSI EN 303 645 (13대 요구사항)

| # | 요구사항 |
|---|----------|
| 1 | 범용 기본 비밀번호 금지 |
| 2 | 취약점 공개 정책 시행 |
| 3 | 소프트웨어 최신 상태 유지 |
| 4 | 보안 자격 증명 및 민감 데이터 안전 저장 |
| 5 | 안전한 통신 |
| 6 | 공격 표면 최소화 |
| 7 | 소프트웨어 무결성 보장 |
| 8 | 개인 데이터 보안 보장 |
| 9 | 시스템 장애 복원력 |
| 10 | 원격 측정 데이터 검사 |
| 11 | 사용자 데이터 쉬운 삭제 |
| 12 | 장비 설치/유지보수 용이 |
| 13 | 입력 데이터 검증 |

### 4.3 한국 IoT 보안 관련 법규

| 법규/가이드 | 기관 | 내용 |
|------------|------|------|
| 정보통신망법 | 과기정통부 | IoT 정보보호 기준 |
| IoT 보안 가이드 | KISA | IoT 보안 인증 |
| IoT 보안 인증제 | KISA | IoT 기기 보안 검증 |
| K-IoT 보안 | 과기정통부 | IoT 보안 로드맵 |

---

## Part 5: 종합 보안 아키텍처 설계 (30분)

### 5.1 안전한 IoT 아키텍처

```
┌──────────────────────────────────────────────┐
│                 Cloud Layer                   │
│  ┌──────────┐  ┌───────┐  ┌──────────────┐ │
│  │ API GW   │  │ Auth  │  │ Data Store   │ │
│  │ (mTLS)   │  │(OAuth)│  │ (암호화)     │ │
│  └──────────┘  └───────┘  └──────────────┘ │
├──────────────────────────────────────────────┤
│              Network Layer                    │
│  ┌──────────┐  ┌───────┐  ┌──────────────┐ │
│  │ TLS 1.3  │  │MQTT   │  │ 방화벽       │ │
│  │ DTLS 1.2 │  │(TLS)  │  │ IDS/IPS      │ │
│  └──────────┘  └───────┘  └──────────────┘ │
├──────────────────────────────────────────────┤
│              Device Layer                     │
│  ┌──────────┐  ┌───────┐  ┌──────────────┐ │
│  │Secure    │  │X.509  │  │ 보안 OTA     │ │
│  │Boot      │  │인증서 │  │ (서명+암호화)│ │
│  │(HSM/TPM) │  │       │  │              │ │
│  └──────────┘  └───────┘  └──────────────┘ │
└──────────────────────────────────────────────┘
```

### 5.2 IoT 보안 체크리스트 (종합)

```bash
cat << 'PYEOF' > /tmp/iot_security_audit.py
#!/usr/bin/env python3
"""IoT 보안 감사 체크리스트 도구"""

categories = {
    "인증 및 접근제어": [
        ("기본 비밀번호 변경 강제", True),
        ("비밀번호 복잡도 요구", True),
        ("디바이스 인증서 기반 인증", True),
        ("관리자 MFA 지원", False),
        ("계정 잠금 정책", True),
        ("최소 권한 원칙 적용", True),
    ],
    "데이터 보호": [
        ("전송 중 암호화 (TLS/DTLS)", True),
        ("저장 시 암호화", False),
        ("민감 데이터 식별/분류", True),
        ("개인정보 최소 수집", True),
        ("데이터 보존 기간 설정", False),
    ],
    "네트워크 보안": [
        ("IoT 전용 네트워크 분리", True),
        ("방화벽 규칙 최소화", True),
        ("불필요한 포트/서비스 비활성화", True),
        ("네트워크 모니터링", True),
        ("MQTT/CoAP 인증+ACL", True),
    ],
    "펌웨어/소프트웨어": [
        ("보안 부트 체인", True),
        ("서명된 펌웨어 업데이트", True),
        ("롤백 메커니즘", False),
        ("취약 라이브러리 점검", True),
        ("코드 난독화/보호", False),
    ],
    "하드웨어 보안": [
        ("디버그 포트 비활성화", True),
        ("보안 키 저장 (HSM/TPM)", False),
        ("탬퍼 감지", False),
        ("보안 퓨즈 설정", True),
    ],
    "운영/모니터링": [
        ("보안 이벤트 로깅", True),
        ("이상 행위 탐지", True),
        ("사고 대응 절차", True),
        ("정기 보안 점검", True),
        ("취약점 공개 정책", False),
    ],
}

print("=" * 60)
print("IoT 보안 감사 체크리스트")
print("=" * 60)

total = 0
passed = 0

for category, items in categories.items():
    cat_total = len(items)
    cat_passed = sum(1 for _, s in items if s)
    total += cat_total
    passed += cat_passed
    
    print(f"\n[{category}] ({cat_passed}/{cat_total})")
    for item, status in items:
        marker = "[O]" if status else "[X]"
        print(f"  {marker} {item}")

score = (passed / total * 100) if total > 0 else 0
print(f"\n{'=' * 60}")
print(f"종합 점수: {passed}/{total} ({score:.0f}%)")

if score >= 80:
    grade = "양호"
elif score >= 60:
    grade = "보통"
else:
    grade = "미흡"
print(f"등급: {grade}")
print(f"\n개선 필요 항목:")
for cat, items in categories.items():
    for item, status in items:
        if not status:
            print(f"  - [{cat}] {item}")
PYEOF

python3 /tmp/iot_security_audit.py
```

---

## Part 6: 과제 안내 (20분)

### 과제

- IoT 디바이스용 X.509 인증서 기반 mTLS를 구현하시오
- 펌웨어 서명 및 검증 파이프라인을 구축하시오
- ETSI EN 303 645 기준으로 특정 IoT 제품의 보안 감사 보고서를 작성하시오

---

## 참고 자료

- NISTIR 8259: https://csrc.nist.gov/publications/detail/nistir/8259/final
- ETSI EN 303 645: https://www.etsi.org/deliver/etsi_en/303600_303699/303645/
- OWASP IoT Security: https://owasp.org/www-project-internet-of-things/
- KISA IoT 보안 가이드: https://www.kisa.or.kr/

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041 (Data Theft)` 패턴

```
incident_id=d45fc680-cb9b-11ee-9d8c-014a3c92d0a7 mo_name=Data Theft
red=172.25.238.143 blue=100.64.5.119 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041 (Data Theft)` 패턴

```
incident_id=c6f8acf0-df14-11ee-9778-4184b1db151c mo_name=Data Theft
red=100.64.3.190 blue=100.64.3.183 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.


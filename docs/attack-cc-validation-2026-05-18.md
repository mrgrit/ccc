# attack 코스 CC 검증 보고 (2026-05-18 fresh deploy)

110번 fresh 6v6 환경 (2026-05-17 배포) 에서 attack W01-W15 45 step 의 sequential
실측 검증 진행. 이전 "45/45 ✅ 실측 결함 0" 주장은 fresh deploy 후 commit 0 건
+ 검증 log 미존재 → 실제 검증 안 됨. 본 문서 = 진짜 1 step 씩 실측 결과.

## 결함 박제

### #1: msfconsole 누락 (W01 S1) — **fix 완료**
- 원인: attacker Dockerfile 에 gnupg 미설치 → msfinstall (line 65 `gpg --dearmor`)
  silent fail → keyring 미생성 → apt NO_PUBKEY → metasploit-framework install fail.
  `|| echo "msf install skipped"` silent 처리 가 fail 감춤.
- fix: 6v6 commit d988332 (apt install 에 gnupg 추가 + msfinstall 후 verify 강제)
- 실측 in-place 복구 후 13 도구 매트릭스 13/13 OK.

### #2: nikto `-Vhost` typo (W02 S2) — **fix 완료**
- 원인: lab 의 nikto -Vhost (대문자 V) = "Unknown option". 실제 nikto = -vhost.
- fix: ccc commit 149d0124 (week02.yaml 의 instruction/answer/methods 정정)
- 재검증: nikto v2.1.5 가 Apache/2.4.52 banner + 11 finding 추출 ✅

### #3: JuiceShop `/api/Users` 인증 필수 변경 (W03 S1)
- 원인: 현재 JuiceShop 버전 (6v6 deploy 의 image) 이 /api/Users 에 인증 강제.
  lab instruction 의 "*인증 없이* 모든 사용자 노출 (IDOR)" 와 모순.
- 영향: success_criteria "/api/Users 가 인증 없이 사용자 목록 노출 → IDOR 확인" fail.
- 처리: lab narrative 수정 — "JuiceShop 신 버전 의 secure-by-default 학습 + 옛 IDOR
  history 박제 (실제 W06 의 JWT alg=none 우회 학습 의 motivation)" 로 의미 전환.

### #4: JuiceShop default JWT alg = RS256 (W03 S2)
- 원인: 현재 JuiceShop 의 JWT 가 HS256 → RS256 으로 변경됨. lab 의 "HS256 secret brute"
  학습 narrative 와 차이.
- 영향: minor. "alg 명시" success_criteria 는 충족. W06 의 학습 시 RS256 → public key
  추출 + RS-to-HS alg confusion 으로 narrative 갱신 필요.

### #5: user 계정 `user@me/user` 실패 (W03 S3)
- 원인: JuiceShop 의 default user 계정 가 아님. fresh deploy 시 user table 비어 있음.
- 영향: W03 S3 R/B/P 의 "user JWT decode" fail. Coverage 문자열 verify 만 PASS.
- 처리: lab 의 default credential 을 `admin@juice-sh.op/admin123` (검증 됨) 또는 사전
  /api/Users POST 로 신규 user 생성 후 login.


### #6: juice.6v6.lab ModSec DetectionOnly mode — W04-W07 instruction propagation 결함

**근본 원인 (가설 검증 완료)**:

| vhost | SQLi (`?q=1+UNION+SELECT...`) | 차단 |
|-------|:---:|:---:|
| juice | **200** | ✗ (DetectionOnly) |
| dvwa | **403** | ✓ (Detection) |
| neobank | 403 | ✓ |
| govportal | 403 | ✓ |
| mediforum | 403 | ✓ |
| admin | 403 | ✓ |
| ai | 403 | ✓ |

→ juice = secuops W01 fix (Per-vhost ModSec — juice 만 DetectionOnly) 의 결과.
   나머지 7 vhost = Detection mode 정상 차단.

**영향 받는 lab step (instruction 대상 = juice)**:
- W04 S1 (4 SQLi 타입) — 4×200 (instruction "4×403" 기대 와 반대)
- W04 S2 (sqlmap) — "not injectable" (ModSec 차단 안 됨 + /?q= 가 application 미사용 endpoint)
- W04 S3 (R/B/P) — same
- W05 S1 (XSS) — *예상* same (curl XSS → 200)
- W05 S2-S3 — *예상* same
- W07 S1 (LFI) — *예상* same

**총 영향**: 약 **9 step** (W04 3 + W05 3 + W07 3) instruction narrative 갱신 필요.

**Fix 옵션 (사용자 결정 필요)**:
- **옵션 A**: attack 의 SQLi/XSS/LFI 대상 vhost 를 juice → dvwa 로 일괄 sed 변경.
  W04 S1, W04 S2, W04 S3, W05 S1, W05 S2, W05 S3, W07 S1, W07 S2, W07 S3 = 9 step
  의 instruction + answer + acceptable_methods 모두 정정.
  추가: ModSec 942 audit log 의 grep pattern (현재 `juice.6v6.lab`) 도 dvwa 로.
  추정 시간 ~2-3 시간.
- **옵션 B**: lab narrative 를 "juice = DetectionOnly 학습 — 200 정상 + audit log 만 측정"
  으로 변경. success_criteria 의 "4×403" → "audit log 942 매치 ≥ 1". 학생 의 의미
  파악 +1 (DetectionOnly = log only, 학습용 환경). 추정 시간 ~3-4 시간.
- **옵션 C**: 두 가지 학습 axis 분리 — juice (DetectionOnly = 학습용 audit 추적) + dvwa
  (Detection = 차단 시연). 학생이 *동일 페이로드 의 2 mode 차이* 학습. 추정 시간
  ~5-6 시간 (instruction 전면 재작성).

**권장**: 옵션 A (가장 적은 변경 + secuops 결정 과의 일관성 유지).

### #7: W04 S2 의 `/?q=` endpoint 자체 가 juiceshop 의 처리 endpoint 아님

sqlmap 출력: "GET parameter 'q' does not seem to be injectable"

juiceshop 의 실제 SQLi endpoint = `/rest/products/search?q=...` (Sequelize search).
`/?q=` = 그냥 default 페이지, q parameter 미사용. instruction 의 *학습 대상 endpoint*
가 잘못됨. 옵션 A 의 vhost 만 변경 으로는 부족 — endpoint 도 정정 필요.

옵션 A+ : juice → dvwa + endpoint 도 dvwa 의 실제 SQLi path (`/vulnerabilities/sqli/?id=1`) 로 변경.

## 검증 진행 상태 (2026-05-18 23:05)

| 주차 | step | PASS | 결함 | 비고 |
|:----:|:----:|:----:|:----:|------|
| W01 | 3/3 | 3 ✅ | #1 msfconsole (fix 완료, 6v6 commit d988332) | |
| W02 | 3/3 | 3 ✅ | #2 nikto -Vhost (fix 완료, ccc commit 149d0124) | |
| W03 | 3/3 | semi-PASS | #3 IDOR gone, #4 RS256, #5 user@me | narrative 갱신 |
| W04 | 2/3 측정 | 0 PASS | #6 juice DetectionOnly, #7 endpoint 오류 | 옵션 A+ 필요 |
| W05-W15 | 0/39 | — | 미실측 (juice 대상 step 은 #6 동일 결함 예상) | |

**진행 시간**: 약 30 분 (W01-W04). 남은 W05-W15 = ~3-4 시간 sequential + 결함 fix 일괄
~3-6 시간.

**사용자 의사 결정 대기**:
1. attack 의 juice 대상 step 9개 의 fix 옵션 (A vs B vs C)
2. attack W08 중간고사 + W13/14 Caldera + W15 기말 의 lab 환경 보장 (Caldera 컨테이너
   미배포 여부)

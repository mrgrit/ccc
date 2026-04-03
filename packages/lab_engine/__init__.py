"""lab_engine — 실습 엔진 (YAML 시나리오, 검증, 블록체인 기록)

YAML 기반 실습 시나리오를 파싱하고 실행 환경을 검증한다.
실습 결과를 자동 검증하여 PoW 블록을 생성한다.

시나리오 형식:
  lab_id: course1-week01
  title: "포트 스캐닝 실습"
  objectives: [...]
  steps:
    - instruction: "nmap -sV target"
      verify:
        type: command_output
        expect_contains: "22/tcp open ssh"
  success_criteria:
    min_steps_completed: 3
"""

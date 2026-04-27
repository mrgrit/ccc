# Curriculum Mapping (D-B)

학생이 보는 화면에서 *Training (lecture.md)* 와 *Cyber Range (lab YAML)* 를
주차 번호로 자동 join 하던 방식을 폐기하고, 의미 기반 명시 매핑으로 대체.

## 왜 필요한가

같은 과목의 같은 주차라도 lecture 와 lab 가 다른 주제였음 (300 중 157, 52%).
- attack lecture = OWASP/이론 순서
- attack lab     = PTES/킬체인 순서

## 매핑 스키마

`contents/curriculum/{course}-mapping.yaml` 하나당 1과목.

```yaml
course_id: attack            # _COURSE_MAP 의 name
mappings:
  - week: 1                  # lecture 주차 (Training UI 의 주차 번호)
    lecture:
      course: course1-attack # education 디렉토리명
      title: "보안 개론"
    labs:                    # 이 주차에 함께 보여줄 lab들 (many-to-many)
      - course: attack       # lab 디렉토리 prefix (-nonai/-ai 자동)
        week: 1
        version: nonai
        role: primary        # primary | review | bonus
        note: "환경 구축 후 정찰 시작"
      - course: web-vuln     # ★ cross-course 매핑 — 다른 과목의 lab 도 가져옴
        week: 1
        version: nonai
        role: bonus
        note: "HTTP 기초 — 웹공격 진입 전 권장"
```

## fallback

매핑 YAML 없거나 해당 주차 누락 시 → 기존 자동 join 동작 (week 번호 = lab week)
유지. 점진 적용 안전.

## 작성 원칙

- 매 매핑은 *사람 결정*. 자동 추출 금지.
- lecture 1개 ↔ lab N개 허용 (review/bonus 활용)
- cross-course 매핑은 학습 시너지 큰 경우만 (예: attack lecture w04 SQLi ↔ web-vuln lab w02 SQLi 실습)
- 한 사이클 1~2 과목씩

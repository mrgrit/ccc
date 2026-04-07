#!/usr/bin/env python3
"""nonai Lab 기반으로 ai 변형을 자동 동기화.
ai 변형의 step 구조를 nonai에서 가져오되, script 필드를 추가하고 version/course를 ai로 변경.
"""
import yaml, os, glob, sys, copy

LABS_DIR = os.path.dirname(os.path.abspath(__file__))

# nonai course -> ai course 매핑
COURSE_PAIRS = [
    ("attack-nonai", "attack-ai"),
    ("secops-nonai", "secops-ai"),
    ("web-vuln-nonai", "web-vuln-ai"),
    ("soc-nonai", "soc-ai"),
    ("compliance-nonai", "compliance-ai"),
    ("cloud-container-nonai", "cloud-container-ai"),
    ("ai-security-nonai", "ai-security-ai"),
    ("ai-safety-nonai", "ai-safety-ai"),
    ("autonomous-nonai", "autonomous-ai"),
    ("ai-agent-nonai", "ai-agent-ai"),
    ("battle-nonai", "battle-ai"),
    ("battle-adv-nonai", "battle-adv-ai"),
    ("attack-adv-nonai", "attack-adv-ai"),
    ("soc-adv-nonai", "soc-adv-ai"),
    ("ai-safety-adv-nonai", "ai-safety-adv-ai"),
]

def convert_answer_to_script(answer: str) -> str:
    """nonai의 answer(shell 명령어)를 ai의 script(자동 실행 가능한 명령)로 변환"""
    if not answer:
        return "echo 'no script'"
    # 이미 실행 가능한 명령이면 그대로 사용
    return answer

def sync_course(nonai_dir: str, ai_dir: str) -> int:
    """nonai 기반으로 ai 변형 동기화. 수정된 파일 수 반환."""
    os.makedirs(os.path.join(LABS_DIR, ai_dir), exist_ok=True)
    modified = 0

    for nonai_file in sorted(glob.glob(os.path.join(LABS_DIR, nonai_dir, "*.yaml"))):
        week_name = os.path.basename(nonai_file)  # e.g., week01.yaml
        ai_file = os.path.join(LABS_DIR, ai_dir, week_name)

        with open(nonai_file, "r", encoding="utf-8") as f:
            nonai_data = yaml.safe_load(f)

        # ai 변형 생성
        ai_data = copy.deepcopy(nonai_data)
        ai_data["lab_id"] = nonai_data["lab_id"].replace("-nonai-", "-ai-")
        ai_data["version"] = "ai"
        ai_data["course"] = nonai_data["course"].replace("-nonai", "-ai")
        ai_data["title"] = nonai_data["title"] + " (AI 지원)" if "AI" not in nonai_data["title"] else nonai_data["title"]
        ai_data["description"] = nonai_data["description"].rstrip(".") + ". AI SubAgent가 자동으로 명령을 실행하고 결과를 검증합니다."

        for step in ai_data.get("steps", []):
            # answer → script 변환
            answer = step.get("answer", "")
            step["script"] = convert_answer_to_script(answer)
            # ai에서는 risk_level 추가
            if "risk_level" not in step:
                cat = step.get("category", "")
                if cat in ("exploit", "attack"):
                    step["risk_level"] = "medium"
                elif cat in ("defense", "reporting", "setup"):
                    step["risk_level"] = "low"
                else:
                    step["risk_level"] = "low"

        # YAML 저장
        with open(ai_file, "w", encoding="utf-8") as f:
            yaml.dump(ai_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)
        modified += 1

    return modified


if __name__ == "__main__":
    total = 0
    for nonai_dir, ai_dir in COURSE_PAIRS:
        count = sync_course(nonai_dir, ai_dir)
        print(f"  {ai_dir}: {count} files synced")
        total += count
    print(f"\nTotal: {total} files synced")
